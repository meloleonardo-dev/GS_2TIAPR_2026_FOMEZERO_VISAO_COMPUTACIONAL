# -*- coding: utf-8 -*-
"""
gerar_respostas_simulado.py — FOMEZERO · VCIA (CT-08, opção T3)
Grava em respostas_SIMULADO.json as respostas REAIS do modelo para as fotos de exemplo do app.
A FEMD usa este arquivo sem servidor nem GPU; por isso cada resposta sai com "simulado": true
(não é IA ao vivo) e a FEMD deve mostrar a faixa "SIMULADO".
Uso: python gerar_respostas_simulado.py
"""
import json, os, sys
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..', 'app'))
import app   # carrega o modelo e a função triagem() (não abre o servidor)

saida = []
for caminho in app.EXEMPLOS:
    r = app.triagem(Image.open(caminho))
    r['simulado'] = True
    r['arquivo_exemplo'] = os.path.basename(caminho)
    saida.append(r)
with open(os.path.join(AQUI, 'respostas_SIMULADO.json'), 'w', encoding='utf-8') as f:
    json.dump({'esquema': 'fomezero.vcia.v1', 'versao': 'ct08-v1', 'SIMULADO': True,
               'nota': 'Respostas reais do modelo gravadas para as fotos de exemplo; não é IA ao vivo.',
               'respostas': saida}, f, ensure_ascii=False, indent=1)
for r in saida:
    print(r['arquivo_exemplo'], '->', r['condicao']['classe'], r['condicao']['confianca'], '|', r['produto']['rotulo'])
