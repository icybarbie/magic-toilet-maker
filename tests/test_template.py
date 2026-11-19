"""Portable skill checks using synthetic fixtures, never a real person's photo or board."""
import importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
SKILL=ROOT
class SkillTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name)
        self.input=self.base/'inputs';self.input.mkdir()
        self.pngs=[]
        for i in range(5):
            im=Image.new('RGBA',(150,160));d=ImageDraw.Draw(im)
            d.polygon([(20+i*3,20),(125,35+i*4),(80,140)],fill=(20+i*40,170,220-i*25,255))
            p=self.input/f'{i}.png';im.save(p);self.pngs.append(p)
    def tearDown(self):self.temp.cleanup()
    def create(self,name,names):
        p=self.base/name
        subprocess.run([sys.executable,str(SKILL/'scripts/new_project.py'),str(p),'--items',*names,
          '--portrait',str(self.pngs[4]),'--item-images',*[str(x) for x in self.pngs[:4]]],check=True,capture_output=True)
        return p
    def bake(self,p):return subprocess.run([sys.executable,str(p/'scripts/bake_assets.py')],capture_output=True,text=True)
    def test_personalization_and_validation(self):
        a=self.create('first',['草莓','钥匙','星星','唱片'])
        b=self.create('second',['猫咪','苹果','月亮','蛋糕'])
        im=Image.open(self.pngs[4]);im.transpose(Image.Transpose.FLIP_LEFT_RIGHT).save(b/'assets/input/portrait.png')
        for i in range(4):
            im=Image.open(self.pngs[i]);im.transpose(Image.Transpose.FLIP_TOP_BOTTOM).save(b/f'assets/input/item{i}.png')
        for p in (a,b):
            result=self.bake(p);self.assertEqual(result.returncode,0,result.stderr)
        self.assertNotEqual((a/'firmware/MagicToilet/MagicAssets.cpp').read_bytes(),(b/'firmware/MagicToilet/MagicAssets.cpp').read_bytes())
        for name in ('item0','item1','item2','item3','face'):
            self.assertNotEqual((a/f'build/asset-preview/{name}.png').read_bytes(),(b/f'build/asset-preview/{name}.png').read_bytes())
        self.assertEqual((a/'build/asset-preview/mic.png').read_bytes(),(b/'build/asset-preview/mic.png').read_bytes())
        prior=(a/'firmware/MagicToilet/MagicAssets.cpp').read_bytes()
        cfg=json.loads((a/'magic-toilet.json').read_text());cfg['items'].pop()
        (a/'magic-toilet.json').write_text(json.dumps(cfg))
        self.assertNotEqual(self.bake(a).returncode,0)
        self.assertEqual(prior,(a/'firmware/MagicToilet/MagicAssets.cpp').read_bytes())
        cfg['items'].append({'name':'花','png':'../outside.png'});(a/'magic-toilet.json').write_text(json.dumps(cfg))
        self.assertNotEqual(self.bake(a).returncode,0)
        cfg['items'][-1]['png']='assets/input/item3.png';(a/'magic-toilet.json').write_text(json.dumps(cfg))
        Image.new('RGB',(50,50),'red').save(a/'assets/input/item3.png')
        self.assertNotEqual(self.bake(a).returncode,0)
    def test_backup_guard(self):
        path=SKILL/'assets/template/scripts/board.py';spec=importlib.util.spec_from_file_location('board_guard',path)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        folder=self.base/'backup';folder.mkdir();(folder/'flash.bin').write_bytes(b'fixture')
        device={'mac':'00:11:22:33:44:55','flash_bytes':7,'chip':'esp32s3'}
        (folder/'backup.json').write_text(json.dumps(dict(device,sha256=m.digest(folder/'flash.bin'),verified=True)))
        self.assertEqual(m.validate_backup(folder,device),folder/'flash.bin')
        with self.assertRaises(ValueError):m.validate_backup(folder,dict(device,mac='11:11:22:33:44:55'))
        (folder/'flash.bin').write_bytes(b'changed')
        with self.assertRaises(ValueError):m.validate_backup(folder,device)
if __name__=='__main__':unittest.main()
