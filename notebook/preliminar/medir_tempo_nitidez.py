# -*- coding: utf-8 -*-
"""
medir_tempo_nitidez.py — FOMEZERO · VCIA (DEC-010)
Mede o custo da salvaguarda de nitidez (comum.nitidez) na CPU, em fotos do TESTE (512x512):
20 fotos de aquecimento + 100 medidas. Grava evidencias/tempo_nitidez.json.
Uso: python medir_tempo_nitidez.py <pasta "Processed Data"> <pasta evidencias>
"""
import json, os, statistics, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from PIL import Image
import comum as C

dados, evid = sys.argv[1], sys.argv[2]
linhas = C.ler_divisao(os.path.join(evid, 'divisao_teste.csv'))[:120]
imgs = [Image.open(os.path.join(dados, l['caminho'])).convert('RGB') for l in linhas]
for i in imgs[:20]:
    C.nitidez(i)                                   # aquecimento
t = []
for i in imgs[20:]:
    a = time.perf_counter(); C.nitidez(i); t.append((time.perf_counter() - a) * 1000)
t.sort()
r = dict(funcao='comum.nitidez', dispositivo='CPU (i5-13420H)', entrada='512x512 da base -> cinza 224x224',
         n=len(t), aquecimento=20, media_ms=round(statistics.mean(t), 3), p50_ms=round(t[len(t) // 2], 3),
         p95_ms=round(t[int(0.95 * len(t)) - 1], 3))
json.dump(r, open(os.path.join(evid, 'tempo_nitidez.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(r)
