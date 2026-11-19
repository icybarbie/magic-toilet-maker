#!/usr/bin/env python3
"""Exercise one real-device round; capture frames without reconnecting USB."""
from pathlib import Path
import sys,time,json
import serial
from device import save_png
root=Path(__file__).resolve().parents[1]
out=root/'build/magic-device-test';out.mkdir(parents=True,exist_ok=True)
port=serial.Serial();port.port=sys.argv[1];port.baudrate=115200;port.timeout=.15;port.dtr=False;port.rts=False
log=[]
def command(text):port.write((text+'\n').encode())
def status():
    command('STATUS');deadline=time.monotonic()+4
    while time.monotonic()<deadline:
        line=port.readline().decode(errors='replace').strip()
        if line:log.append(line)
        if line.startswith('MT_STATUS '):
            values=dict(item.split('=',1) for item in line.split()[1:]);return values
    raise RuntimeError('No MagicToilet status')
def await_phase(phase,timeout=12):
    until=time.monotonic()+timeout
    while time.monotonic()<until:
        s=status()
        assert s['touch']=='1' and s['audio']=='1',s
        assert s['audio_errors']=='0',s
        if int(s['phase'])==phase:return s
        time.sleep(.25)
    raise RuntimeError(f'Phase {phase} timed out')
def frame(name):
    command('FRAME');deadline=time.monotonic()+22
    while time.monotonic()<deadline:
        line=port.readline()
        if line.startswith(b'PET_FRAME '):
            _,w,h,n=line.decode().split();w,h,n=map(int,(w,h,n));assert (w,h,n)==(466,466,434312)
            data=bytearray()
            while len(data)<n and time.monotonic()<deadline:data.extend(port.read(min(16384,n-len(data))))
            assert len(data)==n
            assert b'PET_FRAME_END' in port.read_until(b'PET_FRAME_END\r\n')
            save_png(out/(name+'-physical.png'),w,h,data)
            # Derived diagnostic view in installed orientation, not a screen photograph.
            from PIL import Image
            Image.open(out/(name+'-physical.png')).transpose(Image.Transpose.ROTATE_180).save(out/(name+'-installed.png'))
            return
    raise RuntimeError('Frame timeout')
with port:
    if sys.platform=='darwin':
        import termios
        attrs=termios.tcgetattr(port.fileno());attrs[2]&=~termios.HUPCL;termios.tcsetattr(port.fileno(),termios.TCSANOW,attrs)
    time.sleep(2);port.reset_input_buffer();command('RESET');initial=await_phase(0);frame('idle')
    command('ASK');await_phase(2);time.sleep(1.6);frame('question-one')
    fortune=await_phase(4);frame('fortune');command('ASK');await_phase(2);time.sleep(1.6);frame('question-two')
    face=await_phase(6);frame('face');command('FLUSH');final=await_phase(0);frame('reset')
    assert int(final['cues'])-int(initial['cues'])>=6,(initial,final)
    command('PERF');time.sleep(.25)
    while port.in_waiting:
        line=port.readline().decode(errors='replace').strip()
        if line:log.append(line)
    result={'initial':initial,'fortune':fortune,'face':face,'final':final,'passed':True,'note':'Serial-driven flow and framebuffer; not a physical touch or acoustic test.'}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    (out/'serial.log').write_text('\n'.join(log)+'\n')
    print(json.dumps(result,indent=2))
