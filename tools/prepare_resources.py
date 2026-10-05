from pathlib import Path
import random
import shutil
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / 'Practical Task'

def encrypt(raw):
    values = [ord(raw[0])+2, ord(raw[0])-2, ord(raw[0])+1,
              ord(raw[1])+3, ord(raw[1])-3, ord(raw[1])-1,
              ord(raw[2])+2, ord(raw[2])-2, ord(raw[3])+4, ord(raw[3])-4]
    for i, value in enumerate(values):
        lo, hi = (97, 122) if i < 6 else (48, 57)
        if value > hi: values[i] = value - hi + lo
        elif value < lo: values[i] = lo - value + lo
    return ''.join(map(chr, values))

password_dir = TASKS / 'Task 03'
rng = random.Random(6005)
raw = ['aa00', 'zz99', 'az09', 'za90', 'ab12', 'mn56', 'xy87', 'bb11']
raw += [''.join([chr(97+rng.randrange(26)), chr(97+rng.randrange(26)),
                 str(rng.randrange(10)), str(rng.randrange(10))]) for _ in range(10000-len(raw))]
(password_dir / 'passwords.txt').write_text('\n'.join(map(encrypt, raw))+'\n', encoding='ascii')
(password_dir / 'expected_passwords.txt').write_text('\n'.join(raw)+'\n', encoding='ascii')

images = TASKS / 'Task 04' / 'images'
images.mkdir(parents=True, exist_ok=True)
image = Image.new('RGBA', (512, 384), (18, 30, 42, 255))
draw = ImageDraw.Draw(image)
draw.rectangle((48, 48, 240, 240), fill=(235, 235, 235, 255))
draw.ellipse((290, 90, 460, 260), fill=(225, 65, 40, 255))
draw.polygon([(90, 300), (230, 260), (350, 345)], fill=(30, 200, 100, 255))
image.save(images / 'shapes.png')

image = Image.new('RGBA', (640, 480))
image.putdata([(x*255//639, y*255//479, (x+y)*255//1118, 255)
               for y in range(480) for x in range(640)])
draw = ImageDraw.Draw(image)
for x in range(60, 640, 100): draw.line((x, 20, x, 460), fill=(255, 255, 255, 255), width=4)
image.save(images / 'gradient.png')

image = Image.new('RGBA', (257, 193))
image.putdata([((255 if (x//24+y//24)%2 else 0), x%256, y%256, (x*5+y*3)%256)
               for y in range(193) for x in range(257)])
image.save(images / 'checkerboard.png')

(ROOT / 'evidence').mkdir(exist_ok=True)
print('Prepared 10,000 repeatable encrypted passwords and three original PNG inputs.')
