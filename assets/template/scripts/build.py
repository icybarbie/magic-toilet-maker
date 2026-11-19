#!/usr/bin/env python3
"""Build only. No serial access, installation or flashing."""
import argparse,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--arduino-cli',default='arduino-cli')
p.add_argument('--arduino-config',type=Path)
p.add_argument('--libraries',type=Path,required=True)
a=p.parse_args();root=Path(__file__).resolve().parents[1]
libs=a.libraries.resolve()
if not libs.is_dir():p.error('Supply the libraries directory from Waveshare v1.0.2.')
subprocess.run([sys.executable,str(root/'scripts/bake_assets.py')],check=True)
cmd=[a.arduino_cli]
if a.arduino_config:cmd+=['--config-file',str(a.arduino_config.resolve())]
cmd+=['compile','--fqbn','esp32:esp32:esp32s3:FlashSize=16M,PartitionScheme=app3M_fat9M_16MB,PSRAM=opi,CDCOnBoot=cdc',
 '--libraries',str(libs),'--build-path',str(root/'build/firmware'),str(root/'firmware/MagicToilet')]
subprocess.run(cmd,check=True,cwd=root)
