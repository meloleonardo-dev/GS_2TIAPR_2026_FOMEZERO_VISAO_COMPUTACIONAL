# -*- coding: utf-8 -*-
"""
nitidez_variantes_validacao.py — FOMEZERO · VCIA (DEC-010)
Compara 4 variantes da medida de nitidez SÓ na VALIDAÇÃO (originais e perturbações sintéticas);
limiar = percentil 2 das originais. Grava <evidencias>/nitidez_variantes_validacao.json.
Uso: python nitidez_variantes_validacao.py <pasta "Processed Data"> <pasta evidencias>
"""
import os, sys, random, zlib, importlib.util, json
import numpy as np
from PIL import Image, ImageFilter

NB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')     # pasta notebook/
sys.path.insert(0, NB)
import comum as C
s = importlib.util.spec_from_file_location('i', os.path.join(NB, '04_interferencias.py')); I = importlib.util.module_from_spec(s); s.loader.exec_module(I)
DADOS, EVID = sys.argv[1], sys.argv[2]
val = C.ler_divisao(os.path.join(EVID, 'divisao_validacao.csv'))


def lapg(img):
    g = np.asarray(img.convert('L').resize((224, 224)), dtype=np.float32)
    return g, 4 * g[1:-1, 1:-1] - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:]


# variantes: laplaciano bruto, ÷ variância, ÷ brilho médio² (escolhida), ÷ amplitude² (p95 - p5)
M = {'bruta': lambda g, l: l.var(), 'div_var': lambda g, l: l.var() / (g.var() + 1e-6),
     'div_media2': lambda g, l: l.var() / (g.mean() ** 2 + 1e-6),
     'div_p95p5_2': lambda g, l: l.var() / ((np.percentile(g, 95) - np.percentile(g, 5)) ** 2 + 1e-6)}
P = {'original': None, 'escurecer': I.escurecer, 'clarear': I.clarear, 'sombra': I.sombra,
     'desfoque_r2': lambda im, r: im.filter(ImageFilter.GaussianBlur(2)), 'desfoque_r3': I.desfocar}
v = {m: {p: [] for p in P} for m in M}
for l in val:
    img = Image.open(os.path.join(DADOS, l['caminho'])).convert('RGB')
    for p, f in P.items():
        im = f(img, random.Random(zlib.crc32(l['caminho'].encode()))) if f else img
        g, lap = lapg(im)
        for m, fn in M.items():
            v[m][p].append(fn(g, lap))
out = {}
for m in M:
    lim = np.percentile(v[m]['original'], 2)
    out[m] = {p: round(float((np.array(x) < lim).mean()), 4) for p, x in v[m].items()}
    print(m, out[m])
json.dump(dict(conjunto='validação (só originais + perturbações sintéticas)', n=len(val), percentil=2, taxa_recusada=out, escolhida='div_media2'),
          open(os.path.join(EVID, 'nitidez_variantes_validacao.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
