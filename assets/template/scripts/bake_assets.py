#!/usr/bin/env python3
"""Validate four user sprites + a portrait, then encode the proven firmware assets."""
from pathlib import Path
import json,struct,wave,argparse,os
from PIL import Image,ImageDraw,ImageFont,ImageOps
parser=argparse.ArgumentParser()
parser.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[1])
args=parser.parse_args();ROOT=args.project.resolve()
config=json.loads((ROOT/'magic-toilet.json').read_text())
if config.get('schema_version')!=1 or config.get('board_profile')!='waveshare-1.75c-toilet-180':
    raise SystemExit('Unsupported configuration/board profile. Porting requires hardware review.')
items=config.get('items',[])
if len(items)!=4 or any(not isinstance(i.get('name'),str) or not i['name'].strip() for i in items):
    raise SystemExit('Choose exactly four named objects.')
if len(set(i['name'] for i in items))!=4:
    raise SystemExit('Choose four distinct object names.')
OUT=ROOT/'firmware/MagicToilet';PREVIEW=ROOT/'build/asset-preview'
sprites={}
def load_png(relative,size):
    p=Path(relative)
    if p.is_absolute() or not (ROOT/p).resolve().is_relative_to(ROOT):
        raise ValueError('Image paths must stay inside the generated project.')
    with Image.open(ROOT/p) as source:
        im=ImageOps.exif_transpose(source).convert('RGBA')
    alpha=im.getchannel('A')
    if alpha.getbbox() is None or alpha.getextrema()[0]==255:
        raise ValueError(f'{relative}: supply a nonempty transparent PNG cutout.')
    im=im.crop(alpha.getbbox());im.thumbnail(size,Image.Resampling.LANCZOS)
    return im
for i,item in enumerate(items):
    im=load_png(item['png'],(128,112));slot=Image.new('RGBA',(128,112))
    slot.paste(im,((128-im.width)//2,(112-im.height)//2))
    sprites['item'+str(i)]=slot
sprites['face']=load_png(config['portrait'],(126,148))
logo=Image.open(ROOT/'assets/ui/logo.png').convert('RGBA');sprites['logo']=logo
mic=Image.open(ROOT/'assets/ui/mic.png').convert('RGBA');sprites['mic']=mic
phrases=['魔桶魔桶，\n告诉我今天的\n幸运之物。','魔桶魔桶，\n谁是这个世界上\n最好看的人？']
labels=[i['name'] for i in items]+['当然是你']
characters=list(dict.fromkeys(''.join(phrases+labels).replace('\n','')))
if len(characters)>=254:raise ValueError('Too many distinct glyphs for this renderer.')
fontpaths=[config.get('cjk_font'),os.environ.get('MAGIC_CJK_FONT'),
 '/System/Library/Fonts/STHeiti Medium.ttc',
 '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
 str(Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts/msyh.ttc')]
fontpath=next((p for p in fontpaths if p and Path(p).is_file()),None)
if not fontpath:raise SystemExit('Set cjk_font or MAGIC_CJK_FONT to a Chinese-capable TTF/TTC; do not bundle a system font.')
cn=ImageFont.truetype(fontpath,17);glyphs=[]
missing=cn.getmask(chr(0x10ffff))
for ch in characters:
    candidate=cn.getmask(ch)
    if candidate.size==missing.size and bytes(candidate)==bytes(missing):
        raise ValueError(f'The selected font cannot render {ch!r}.')
    im=Image.new('L',(19,21));g=ImageDraw.Draw(im);bb=g.textbbox((0,0),ch,font=cn)
    g.text(((19-(bb[2]-bb[0]))/2,2-bb[1]),ch,font=cn,fill=255);glyphs.extend(im.getdata())
# Check audio before producing any outputs; fixed cue timing expects these durations.
for name,duration in [('magic',1.15),('water',.95),('fart',.47),('flush',2.35)]:
    with wave.open(str(ROOT/'assets/audio'/f'{name}.wav')) as w:
        if (w.getframerate(),w.getnchannels(),w.getsampwidth())!=(22050,1,2):
            raise ValueError(f'{name}: expected 22050 Hz mono PCM16 WAV.')
        if abs(w.getnframes()/22050-duration)>.02:raise ValueError(f'{name}: cue duration mismatch.')
OUT.mkdir(parents=True,exist_ok=True);PREVIEW.mkdir(parents=True,exist_ok=True)
for name,im in sprites.items():im.save(PREVIEW/(name+'.png'))
def array(name,ctype,values,per=24):
    return 'const '+ctype+' '+name+'[] = {\n'+''.join(','.join(str(x) for x in values[i:i+per])+',\n' for i in range(0,len(values),per))+'};\n'

header=['#pragma once\n#include <stdint.h>\n#include <stddef.h>\nnamespace MagicAssets {\nstruct Sprite {int w,h;const uint16_t* rgb;const uint8_t* alpha;};\nstruct Sound {const int16_t* samples;size_t count;};\n']
cpp=['#include "MagicAssets.h"\nnamespace MagicAssets {\n']
for name,im in sprites.items():
    rgba=list(im.getdata());rgb=[((r>>3)<<11)|((g>>2)<<5)|(b>>3) for r,g,b,a in rgba];alpha=[a for r,g,b,a in rgba]
    cpp+=[array(name+'RGB','uint16_t',rgb),array(name+'A','uint8_t',alpha),f'const Sprite {name}={{{im.width},{im.height},{name}RGB,{name}A}};\n']
    header.append(f'extern const Sprite {name};\n')
cpp.append(array('glyphAlpha','uint8_t',glyphs));header.append('extern const uint8_t glyphAlpha[];\n')
for i,text in enumerate(phrases+labels):
    values=[255 if ch=='\n' else characters.index(ch) for ch in text]+[254]
    cpp.append(array('text'+str(i),'uint8_t',values));header.append(f'extern const uint8_t text{i}[];\n')
header.append('extern const Sprite* const items[4];\nextern const uint8_t* const labels[5];\n')
cpp.append('const Sprite* const items[4]={&item0,&item1,&item2,&item3};\nconst uint8_t* const labels[5]={text2,text3,text4,text5,text6};\n')
for name in ['magic','water','fart','flush']:
    with wave.open(str(ROOT/'assets/audio'/f'{name}.wav')) as w:
        assert (w.getframerate(),w.getnchannels(),w.getsampwidth())==(22050,1,2)
        samples=struct.unpack('<'+'h'*w.getnframes(),w.readframes(w.getnframes()))
    cpp.append(array(name+'PCM','int16_t',samples));cpp.append(f'const Sound {name}Sound={{{name}PCM,{len(samples)}}};\n');header.append(f'extern const Sound {name}Sound;\n')
header.append('}\n');cpp.append('}\n');(OUT/'MagicAssets.h').write_text(''.join(header));(OUT/'MagicAssets.cpp').write_text(''.join(cpp))
sheet=Image.new('RGB',(512,290),'#61bec6')
for i in range(4):sheet.paste(sprites['item'+str(i)],(i*128,0),sprites['item'+str(i)])
sheet.paste(logo,(20,145),logo);sheet.paste(sprites['face'],(210,130),sprites['face']);sheet.paste(mic,(390,160),mic);sheet.save(PREVIEW/'contact-sheet.png')
print('Generated',len(sprites),'sprites,',len(characters),'Chinese glyphs and four PCM cues.')
