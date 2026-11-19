#!/usr/bin/env python3
"""Explicit-port inspection, full backup, and guarded application-only flashing.
A different partition layout is intentionally not initialized by this helper.
"""
import argparse,hashlib,json,re,subprocess,sys
from pathlib import Path

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(base,*args,capture=False):
    return subprocess.run(base+list(args),check=True,text=True,capture_output=capture)
def identity(base):
    text=run(base,'read_mac',capture=True).stdout
    mac=re.search(r'MAC:\s*([0-9a-fA-F:]{17})',text)
    size=run(base,'flash_id',capture=True).stdout
    mb=re.search(r'Detected flash size:\s*(\d+)MB',size)
    if not mac or not mb:raise RuntimeError('Cannot establish MAC/flash capacity; no writes performed.')
    return {'mac':mac[1].lower(),'flash_bytes':int(mb[1])*1024*1024,'chip':'esp32s3'}
def validate_backup(folder,device):
    meta=json.loads((folder/'backup.json').read_text());data=folder/'flash.bin'
    if any(meta.get(k)!=v for k,v in device.items()):raise ValueError('Backup belongs to a different device/capacity.')
    if not meta.get('verified') or data.stat().st_size!=device['flash_bytes'] or digest(data)!=meta['sha256']:
        raise ValueError('Backup is incomplete, altered or unverified.')
    return data

def main():
    p=argparse.ArgumentParser()
    p.add_argument('action',choices=['inspect','backup','flash'])
    p.add_argument('--port',required=True)
    p.add_argument('--backup',type=Path)
    p.add_argument('--board',choices=['waveshare-1.75c-toilet-180'])
    p.add_argument('--build',type=Path,default=Path(__file__).resolve().parents[1]/'build/firmware')
    a=p.parse_args()
    if a.action!='inspect' and a.backup is None:p.error('--backup is required')
    if a.action=='flash' and not a.board:p.error('Confirm the exact board using --board')
    base=[sys.executable,'-m','esptool','--chip','esp32s3','--port',a.port]
    device=identity(base);print(json.dumps(device,indent=2),flush=True)
    if a.action=='inspect':return
    if a.action=='backup':
        a.backup.mkdir(parents=True,exist_ok=False)
        dump=a.backup/'flash.bin'
        run(base,'read_flash','0',str(device['flash_bytes']),str(dump))
        if dump.stat().st_size!=device['flash_bytes']:raise ValueError('Truncated backup')
        run(base,'verify_flash','0',str(dump))
        (a.backup/'backup.json').write_text(json.dumps(dict(device,sha256=digest(dump),verified=True),indent=2)+'\n')
        return
    backup=validate_backup(a.backup,device)
    if device['flash_bytes']<16*1024*1024:raise ValueError('This profile requires at least 16MB flash.')
    part=a.build/'MagicToilet.ino.partitions.bin';app=a.build/'MagicToilet.ino.bin'
    data=part.read_bytes()
    if not 0<len(data)<=4096 or not 0<app.stat().st_size<0x300000:raise ValueError('Invalid partition/app size')
    # Verify this build really puts the application at our sole permitted address.
    entries=[data[i:i+32] for i in range(0,len(data),32)]
    import struct
    apps=[struct.unpack_from('<II',e,4) for e in entries if len(e)==32 and e[:2]==b'\xaa\x50' and e[2]==0]
    if not apps or apps[0]!=(0x10000,0x300000):raise ValueError('Unexpected build partition layout')
    current=a.backup/'current-partitions.bin'
    run(base,'read_flash','0x8000',str(len(data)),str(current))
    if current.read_bytes()!=data or backup.read_bytes()[0x8000:0x8000+len(data)]!=data:
        raise ValueError('Partition layout differs. No write performed. Follow the hardware reference for first-time setup; never force app-only flashing.')
    run(base,'--baud','921600','write_flash','--flash_size','keep','0x10000',str(app))
    (a.build/'deployment.json').write_text(json.dumps(dict(device,app_sha256=digest(app),app_bytes=app.stat().st_size,offset='0x10000',backup=str(a.backup.resolve())),indent=2)+'\n')
if __name__=='__main__':main()
