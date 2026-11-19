#!/usr/bin/env python3
"""MagicToilet serial diagnostics and physical framebuffer capture."""
import argparse,sys,time,pathlib
import serial
from device import save_png

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--port',required=True)
    p.add_argument('--command',action='append',default=[])
    p.add_argument('--seconds',type=float,default=3)
    p.add_argument('--frame',type=pathlib.Path)
    p.add_argument('--delay',type=float,default=0)
    p.add_argument('--after-delay',action='append',default=[])
    p.add_argument('--log',type=pathlib.Path)
    a=p.parse_args()
    allowed={'STATUS','PERF','ASK','FLUSH','RESET','MUTE','CAL','SOUND 1','SOUND 2','SOUND 3','SOUND 4'}
    assert all(c in allowed for c in a.command+a.after_delay)
    port=serial.Serial();port.port=a.port;port.baudrate=115200;port.timeout=.2;port.dtr=False;port.rts=False
    lines=[]
    with port:
        if sys.platform=='darwin':
            import termios
            attributes=termios.tcgetattr(port.fileno());attributes[2]&=~termios.HUPCL;termios.tcsetattr(port.fileno(),termios.TCSANOW,attributes)
        time.sleep(1.5);port.reset_input_buffer()
        for command in a.command or ['STATUS']:
            port.write((command+'\n').encode());time.sleep(.12)
        time.sleep(a.delay)
        for command in a.after_delay:
            port.write((command+'\n').encode());time.sleep(.12)
        if a.frame:
            port.write(b'FRAME\n')
        deadline=time.monotonic()+(25 if a.frame else a.seconds)
        while time.monotonic()<deadline:
            line=port.readline()
            if line.startswith(b'PET_FRAME '):
                _,w,h,n=line.decode().split();w,h,n=int(w),int(h),int(n)
                assert (w,h,n)==(466,466,466*466*2)
                data=bytearray()
                while len(data)<n and time.monotonic()<deadline:data.extend(port.read(min(16384,n-len(data))))
                assert len(data)==n,'Incomplete frame'
                assert b'PET_FRAME_END' in port.read_until(b'PET_FRAME_END\r\n'),'Missing terminator'
                save_png(a.frame,w,h,data);print('Saved device framebuffer:',a.frame);break
            if line:
                text=line.decode(errors='replace').rstrip();lines.append(text);print(text,flush=True)
        if a.log:a.log.parent.mkdir(parents=True,exist_ok=True);a.log.write_text('\n'.join(lines)+'\n')
        if not a.frame and not lines:raise RuntimeError('No serial response')

if __name__=='__main__':main()
