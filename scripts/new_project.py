#!/usr/bin/env python3
"""Create a fresh, private customization project; never overwrite an existing one."""
import argparse,json,shutil
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument('output',type=Path)
    p.add_argument('--items',nargs=4,required=True,metavar='NAME')
    p.add_argument('--portrait',type=Path)
    p.add_argument('--item-images',nargs=4,type=Path,metavar='PNG')
    p.add_argument('--cjk-font',type=Path)
    a=p.parse_args()
    if len(set(a.items))!=4 or any(not n.strip() for n in a.items):p.error('Four distinct names are required.')
    sources=([a.portrait] if a.portrait else [])+(a.item_images or [])
    if any(not f.is_file() for f in sources):p.error('An input file does not exist.')
    if a.output.exists():p.error('Output already exists; use another folder or edit the existing project.')
    skill=Path(__file__).resolve().parents[1]
    shutil.copytree(skill/'assets/template',a.output)
    config=json.loads((a.output/'magic-toilet.json').read_text())
    for item,name in zip(config['items'],a.items):item['name']=name
    if a.cjk_font:config['cjk_font']=str(a.cjk_font.resolve())
    inputs=a.output/'assets/input';inputs.mkdir(parents=True)
    if a.portrait:shutil.copy2(a.portrait,inputs/'portrait.png')
    if a.item_images:
        for i,path in enumerate(a.item_images):shutil.copy2(path,inputs/f'item{i}.png')
    (a.output/'magic-toilet.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n')
    print('Created:',a.output.resolve())
    print('Next: supply four transparent object PNGs and a transparent portrait, then run scripts/bake_assets.py.')
if __name__=='__main__':main()
