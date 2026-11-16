# -*- coding: utf-8 -*-
"""
07_gradcam.py — FOMEZERO · VCIA
Nicho: Triagem visual de hortifrúti excedente antes do cadastro do lote de doação

Grad-CAM (Selvaraju et al., 2017) para a ANÁLISE DE ERROS [REQ-VCIA-24, 51] e o resultado visual [REQ-VCIA-05]:
mostra em quais regiões da foto a CNN se apoiou para a classe prevista (24 classes produto x estágio).
Uso QUALITATIVO: o mapa não é prova de causa e não entra em nenhuma métrica.

Seleção dos exemplos (todos do TESTE, só originais), determinística:
  - acertos: o acerto de maior confiança de cada condição (Fresh, Semi-Fresh, Rotten);
  - erros: os erros de maior confiança, até 2 por tipo de troca (verdadeiro -> previsto).
Implementação manual com ganchos do PyTorch na última camada convolucional (features[-1] da EfficientNet-B0).

Uso: python 07_gradcam.py --modelo efficientnet_b0 --dados <Processed Data> --divisao <evidencias> --pesos <.pt>
"""
import argparse, json, os
import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont
import matplotlib; matplotlib.use('Agg')
from matplotlib import cm
import comum as C


class GradCAM:
    def __init__(self, modelo, camada):
        self.m, self.a, self.g = modelo, None, None
        camada.register_forward_hook(lambda mod, i, o: setattr(self, 'a', o))
        camada.register_full_backward_hook(lambda mod, gi, go: setattr(self, 'g', go[0]))

    def __call__(self, x, classe):
        self.m.zero_grad()
        saida = self.m(x)
        saida[0, classe].backward()
        pesos = self.g.mean(dim=(2, 3), keepdim=True)              # média dos gradientes por canal
        mapa = torch.relu((pesos * self.a).sum(1))[0].detach()     # combinação ponderada + ReLU
        mapa = mapa / (mapa.max() + 1e-8)
        return mapa.cpu().numpy()


def sobrepor(img, mapa, alfa=0.45):
    img = img.resize((C.TAMANHO, C.TAMANHO))
    calor = Image.fromarray((cm.jet(np.array(Image.fromarray((mapa * 255).astype(np.uint8)).resize(img.size, Image.BILINEAR)) / 255.0)[..., :3] * 255).astype(np.uint8))
    return Image.blend(img, calor, alfa)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--modelo', default='efficientnet_b0')
    ap.add_argument('--dados', required=True)
    ap.add_argument('--divisao', required=True)
    ap.add_argument('--pesos', required=True)
    a = ap.parse_args()
    disp = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    modelo = C.carregar_modelo(a.pesos, a.modelo, disp)
    teste = C.ler_divisao(os.path.join(a.divisao, 'divisao_teste.csv'))

    # 1. previsões no teste (para escolher os exemplos)
    prev = []
    with torch.no_grad():
        for k in range(0, len(teste), 64):
            ls = teste[k:k + 64]
            x = torch.stack([C.TF_AVAL(Image.open(os.path.join(a.dados, l['caminho'])).convert('RGB')) for l in ls]).to(disp)
            p = modelo(x).float().softmax(1).cpu()
            cond, _ = C.agregar(p)
            for l, pi, ci in zip(ls, p, cond):
                c, kc = ci.max(0)
                prev.append(dict(l=l, top24=int(pi.argmax()), cond_prev=C.ESTAGIOS[int(kc)], conf=float(c)))
    acertos = []
    for e in C.ESTAGIOS:
        cand = [r for r in prev if r['l']['estagio'] == e and r['cond_prev'] == e]
        acertos.append(max(cand, key=lambda r: r['conf']))
    erros, por_tipo = [], {}
    for r in sorted([r for r in prev if r['cond_prev'] != r['l']['estagio']], key=lambda r: -r['conf']):
        t = (r['l']['estagio'], r['cond_prev'])
        if por_tipo.get(t, 0) < 2:
            por_tipo[t] = por_tipo.get(t, 0) + 1; erros.append(r)

    # 2. Grad-CAM (precisa de gradiente: modo avaliação, mas sem no_grad)
    gc = GradCAM(modelo, modelo.features[-1])
    itens = [('ACERTO', r) for r in acertos] + [('ERRO', r) for r in erros]
    try:
        fonte = ImageFont.truetype('arial.ttf', 12)
    except OSError:
        fonte = ImageFont.load_default()
    L, H, col = C.TAMANHO, C.TAMANHO + 52, 4
    linhas = (len(itens) + col - 1) // col
    painel = Image.new('RGB', (col * 2 * L, linhas * H), 'white')
    d = ImageDraw.Draw(painel)
    registro = []
    for i, (tipo, r) in enumerate(itens):
        img = Image.open(os.path.join(a.dados, r['l']['caminho'])).convert('RGB')
        x = C.TF_AVAL(img).unsqueeze(0).to(disp).requires_grad_(True)
        mapa = gc(x, r['top24'])
        x0, y0 = (i % col) * 2 * L, (i // col) * H
        painel.paste(img.resize((L, L)), (x0, y0)); painel.paste(sobrepor(img, mapa), (x0 + L, y0))
        prod = C.PRODUTO_PT[r['l']['produto']]
        d.text((x0 + 4, y0 + L + 3), f"{tipo} · {prod} · verdadeiro: {r['l']['estagio']}", fill='green' if tipo == 'ACERTO' else 'red', font=fonte)
        d.text((x0 + 4, y0 + L + 19), f"previsto: {r['cond_prev']} ({r['conf'] * 100:.0f}%)", fill='black', font=fonte)
        d.text((x0 + 4, y0 + L + 35), r['l']['caminho'][:60], fill='gray', font=fonte)
        registro.append(dict(tipo=tipo, caminho=r['l']['caminho'], produto=prod, verdadeiro=r['l']['estagio'],
                             previsto=r['cond_prev'], confianca=round(r['conf'], 4), classe_24_explicada=C.CLASSES[r['top24']]))
    painel.save(os.path.join(a.divisao, f'gradcam_{a.modelo}.png'))
    with open(os.path.join(a.divisao, f'gradcam_{a.modelo}.json'), 'w', encoding='utf-8') as f:
        json.dump(dict(modelo=a.modelo, conjunto='teste (só originais)', n_teste=len(teste), camada='features[-1]',
                       uso='qualitativo; não é métrica', exemplos=registro), f, ensure_ascii=False, indent=1)
    for r in registro:
        print(r)


if __name__ == '__main__':
    main()
