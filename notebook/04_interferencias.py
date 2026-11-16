# -*- coding: utf-8 -*-
"""
04_interferencias.py — FOMEZERO · VCIA
Nicho: Triagem visual de hortifrúti excedente antes do cadastro do lote de doação

Interferências [§2.3; REQ-VCIA-25]: a base AgriFreshNET não traz sombras fortes nem obstruções reais
(um item, de cima, sobre pano claro). Para medir a robustez, aplicamos PERTURBAÇÕES SINTÉTICAS
controladas às imagens do TESTE e comparamos com o teste original:
  - iluminação: escurecer (brilho x0,6) e clarear (brilho x1,4);
  - sombra sintética: metade da imagem escurecida em 50%, com borda inclinada;
  - obstrução parcial: retângulo cinza cobrindo 25% da área, sobre a região central;
  - desfoque gaussiano (raio 3), simulando foto tremida.
Cada perturbação usa semente fixa por imagem (reprodutível).
Opcional: --fotos_proprias <pasta> classifica fotos tiradas pela equipe; elas ficam MARCADAS como
fotos próprias e NUNCA entram nas métricas oficiais.

Uso: python 04_interferencias.py --modelo efficientnet_b0 --dados <Processed Data> --divisao <evidencias> --pesos <.pt>
"""
import argparse, json, os, random, zlib
import numpy as np
import torch
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw
from sklearn.metrics import f1_score, accuracy_score
import comum as C


def escurecer(img, rng): return ImageEnhance.Brightness(img).enhance(0.6)
def clarear(img, rng): return ImageEnhance.Brightness(img).enhance(1.4)
def desfocar(img, rng): return img.filter(ImageFilter.GaussianBlur(3))


def sombra(img, rng):
    w, h = img.size
    m = Image.new('L', (w, h), 0)
    x1, x2 = rng.randint(0, w), rng.randint(0, w)
    lado = rng.choice([0, 1])
    poly = [(x1, 0), (x2, h), (w if lado else 0, h), (w if lado else 0, 0)]
    ImageDraw.Draw(m).polygon(poly, fill=255)
    escura = ImageEnhance.Brightness(img).enhance(0.5)
    return Image.composite(escura, img, m.filter(ImageFilter.GaussianBlur(8)))


def obstruir(img, rng):
    w, h = img.size
    ow, oh = int(w * 0.5), int(h * 0.5)             # 25% da área
    x0 = rng.randint(int(w * 0.15), int(w * 0.35)); y0 = rng.randint(int(h * 0.15), int(h * 0.35))
    img = img.copy()
    ImageDraw.Draw(img).rectangle([x0, y0, x0 + ow, y0 + oh], fill=(128, 128, 128))
    return img


PERTURBACOES = {'original': None, 'escurecer_x0.6': escurecer, 'clarear_x1.4': clarear,
                'sombra_sintetica': sombra, 'obstrucao_25pct': obstruir, 'desfoque_r3': desfocar}


def prever(modelo, imgs, disp):
    with torch.no_grad():
        x = torch.stack([C.TF_AVAL(i) for i in imgs]).to(disp)
        p = modelo(x).float().softmax(1).cpu()
    return C.agregar(p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--modelo', default='efficientnet_b0')
    ap.add_argument('--dados', required=True)
    ap.add_argument('--divisao', required=True)
    ap.add_argument('--pesos', required=True)
    ap.add_argument('--fotos_proprias', default=None)
    a = ap.parse_args()
    disp = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    modelo = C.carregar_modelo(a.pesos, a.modelo, disp)
    tau = json.load(open(os.path.join(a.divisao, f'metricas_teste_{a.modelo}.json'), encoding='utf-8'))['calibracao']['tau']
    teste = C.ler_divisao(os.path.join(a.divisao, 'divisao_teste.csv'))
    y = np.array([C.ESTAGIOS.index(l['estagio']) for l in teste])

    res = {}
    for nome, f in PERTURBACOES.items():
        preds, confs = [], []
        for k in range(0, len(teste), 64):
            lote = []
            for l in teste[k:k + 64]:
                img = Image.open(os.path.join(a.dados, l['caminho'])).convert('RGB')
                rng = random.Random(zlib.crc32(l['caminho'].encode('utf-8')))   # semente fixa por imagem
                lote.append(f(img, rng) if f else img)
            cond, _ = prever(modelo, lote, disp)
            c, p = cond.max(1)
            preds += p.tolist(); confs += c.tolist()
        preds, confs = np.array(preds), np.array(confs)
        aceita = confs >= tau
        res[nome] = dict(n=int(len(y)), acuracia=round(float(accuracy_score(y, preds)), 4),
                         f1_macro=round(float(f1_score(y, preds, average='macro')), 4),
                         cobertura_tau=round(float(aceita.mean()), 4),
                         rotten_previsto_fresh=int(((y == 2) & (preds == 0)).sum()))
        print(nome, res[nome], flush=True)
    base = res['original']
    for k, v in res.items():
        v['delta_f1_vs_original'] = round(v['f1_macro'] - base['f1_macro'], 4)

    # exemplo visual das perturbações (primeira imagem Rotten do teste)
    ex = next(l for l in teste if l['estagio'] == 'Rotten')
    img0 = Image.open(os.path.join(a.dados, ex['caminho'])).convert('RGB').resize((256, 256))
    painel = Image.new('RGB', (256 * len(PERTURBACOES), 280), 'white')
    d = ImageDraw.Draw(painel)
    for j, (nome, f) in enumerate(PERTURBACOES.items()):
        im = f(img0, random.Random(1)) if f else img0
        painel.paste(im, (256 * j, 0)); d.text((256 * j + 4, 260), nome, fill='black')
    painel.save(os.path.join(a.divisao, f'exemplo_perturbacoes_{a.modelo}.png'))

    proprias = None
    if a.fotos_proprias and os.path.isdir(a.fotos_proprias):
        proprias = []
        for arq in sorted(os.listdir(a.fotos_proprias)):
            try:
                img = Image.open(os.path.join(a.fotos_proprias, arq)).convert('RGB')
            except Exception:
                continue
            cond, prod = prever(modelo, [img], disp)
            c, p = cond[0].max(0); cp, pp = prod[0].max(0)
            classe = C.CONDICAO_PT[C.ESTAGIOS[int(p)]] if float(c) >= tau else C.INCONCLUSIVO
            proprias.append(dict(arquivo=arq, classe=classe, confianca=round(float(c), 4),
                                 produto=C.PRODUTO_PT[C.PRODUTOS[int(pp)]], conf_produto=round(float(cp), 4)))
    out = dict(modelo=a.modelo, conjunto='teste (só originais) com perturbações sintéticas', tau=tau,
               resultados=res, fotos_proprias_FORA_DAS_METRICAS_OFICIAIS=proprias)
    with open(os.path.join(a.divisao, f'interferencias_{a.modelo}.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
