import os, random, sys
from PIL import Image, ImageDraw
R = sys.argv[1]; random.seed(7)
pastas = sorted(os.listdir(R)); W = 128
linhas = []
for prod in ['banana', 'tomato', 'papaya', 'cucumber']:
    for p in pastas:
        if prod in p.lower():
            fs = [f for f in os.listdir(os.path.join(R, p)) if not f.startswith('aug_')]
            linhas.append((p, [os.path.join(R, p, f) for f in random.sample(fs, 5)]))
img = Image.new('RGB', (180 + 5 * W, len(linhas) * W), 'white'); d = ImageDraw.Draw(img)
for i, (p, fs) in enumerate(linhas):
    d.text((4, i * W + 55), p[:26], fill='black')
    for j, f in enumerate(fs):
        img.paste(Image.open(f).convert('RGB').resize((W, W)), (180 + j * W, i * W))
img.save(sys.argv[2])
