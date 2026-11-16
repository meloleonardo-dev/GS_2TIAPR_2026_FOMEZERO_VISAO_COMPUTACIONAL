# -*- coding: utf-8 -*-
"""
06_nitidez.py — FOMEZERO · VCIA
Nicho: Triagem visual de hortifrúti excedente antes do cadastro do lote de doação

Salvaguarda de nitidez (DEC-010, EXTRA aprovado pelo usuário em 16/11; apoia REQ-VCIA-25 e as salvaguardas da DEC-023).
O 04_interferencias.py mostrou que fotos borradas levam o modelo a sugerir "sem sinais visuais de deterioração"
para itens "Rotten" com confiança alta, e o limiar τ não pega esses casos. Aqui:
  1. CALIBRAÇÃO (só VALIDAÇÃO): mede a nitidez (comum.nitidez) das fotos originais e das mesmas fotos com
     desfoque gaussiano; o limiar é o percentil 2 das originais (no máximo ~2% das fotos boas são recusadas).
  2. MEDIÇÃO (TESTE, sem tocar no limiar): aplica a salvaguarda ao teste original e às perturbações do
     04_interferencias.py e compara com o resultado sem salvaguarda.
Fotos recusadas pela nitidez contam como "inconclusivo" (não sugerem condição).

Uso: python 06_nitidez.py --modelo efficientnet_b0 --dados <Processed Data> --divisao <evidencias> --pesos <.pt>
"""
import argparse, json, os, random, zlib, importlib.util
import numpy as np
import torch
from PIL import Image, ImageFilter
from sklearn.metrics import f1_score, accuracy_score
import comum as C

AQUI = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('interf', os.path.join(AQUI, '04_interferencias.py'))
I = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(I)

PERCENTIL = 2
RAIOS_CALIB = [2, 3]          # desfoques usados só para mostrar a separação na validação


def carregar(raiz, l):
    return Image.open(os.path.join(raiz, l['caminho'])).convert('RGB')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--modelo', default='efficientnet_b0')
    ap.add_argument('--dados', required=True)
    ap.add_argument('--divisao', required=True)
    ap.add_argument('--pesos', required=True)
    a = ap.parse_args()
    disp = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    modelo = C.carregar_modelo(a.pesos, a.modelo, disp)
    tau = json.load(open(os.path.join(a.divisao, f'metricas_teste_{a.modelo}.json'), encoding='utf-8'))['calibracao']['tau']

    # 1. calibração na validação
    val = C.ler_divisao(os.path.join(a.divisao, 'divisao_validacao.csv'))
    n_val = {'original': []}
    n_val.update({f'desfoque_r{r}': [] for r in RAIOS_CALIB})
    for l in val:
        img = carregar(a.dados, l)
        n_val['original'].append(C.nitidez(img))
        for r in RAIOS_CALIB:
            n_val[f'desfoque_r{r}'].append(C.nitidez(img.filter(ImageFilter.GaussianBlur(r))))
    n_val = {k: np.array(v) for k, v in n_val.items()}
    limiar = float(np.percentile(n_val['original'], PERCENTIL))
    est_val = np.array([l['estagio'] for l in val])
    calib = dict(conjunto='validação (só originais)', n=len(val), percentil=PERCENTIL, limiar_nitidez=float(f'{limiar:.4g}'),
                 recusadas_por_conjunto={k: round(float((v < limiar).mean()), 4) for k, v in n_val.items()},
                 recusadas_originais_por_estagio={e: dict(n=int((est_val == e).sum()),
                                                          taxa=round(float((n_val['original'][est_val == e] < limiar).mean()), 4))
                                                  for e in C.ESTAGIOS},
                 mediana={k: float(f'{np.median(v):.4g}') for k, v in n_val.items()})
    print('calibração', calib, flush=True)

    # 2. medição no teste
    teste = C.ler_divisao(os.path.join(a.divisao, 'divisao_teste.csv'))
    y = np.array([C.ESTAGIOS.index(l['estagio']) for l in teste])
    res = {}
    for nome, f in I.PERTURBACOES.items():
        preds, confs, nits = [], [], []
        for k in range(0, len(teste), 64):
            lote = []
            for l in teste[k:k + 64]:
                img = carregar(a.dados, l)
                rng = random.Random(zlib.crc32(l['caminho'].encode('utf-8')))   # mesma semente do 04
                im = f(img, rng) if f else img
                lote.append(im); nits.append(C.nitidez(im))
            cond, _ = I.prever(modelo, lote, disp)
            c, p = cond.max(1)
            preds += p.tolist(); confs += c.tolist()
        preds, confs, nits = np.array(preds), np.array(confs), np.array(nits)
        nitida = nits >= limiar
        sem = confs >= tau                     # sugestão sem a salvaguarda (só τ)
        com = sem & nitida                     # sugestão com a salvaguarda
        rf = (y == 2) & (preds == 0)           # "Rotten" sugerido como "sem sinais"
        res[nome] = dict(
            n=int(len(y)), f1_macro_todas=round(float(f1_score(y, preds, average='macro')), 4),
            recusadas_nitidez=int((~nitida).sum()),
            recusadas_nitidez_por_estagio={e: int((~nitida & (y == i)).sum()) for i, e in enumerate(C.ESTAGIOS)},
            sem_salvaguarda=dict(cobertura=round(float(sem.mean()), 4),
                                 acuracia_sugeridas=round(float(accuracy_score(y[sem], preds[sem])), 4) if sem.any() else None,
                                 rotten_sugerido_sem_sinais=int((rf & sem).sum())),
            com_salvaguarda=dict(cobertura=round(float(com.mean()), 4),
                                 acuracia_sugeridas=round(float(accuracy_score(y[com], preds[com])), 4) if com.any() else None,
                                 f1_macro_sugeridas=round(float(f1_score(y[com], preds[com], average='macro')), 4) if com.any() else None,
                                 rotten_sugerido_sem_sinais=int((rf & com).sum())))
        print(nome, res[nome], flush=True)

    out = dict(modelo=a.modelo, tau=tau, metrica='variância do laplaciano 4-vizinhos ÷ brilho médio², cinza 224x224 (comum.nitidez)', variantes_descartadas_na_validacao='nitidez_variantes_validacao.json',
               calibracao=calib, teste=res,
               nota=('"cobertura" = fração das fotos que recebem sugestão de condição; as demais viram "inconclusivo". '
                     'Perturbações sintéticas; fora das métricas oficiais do teste original.'))
    with open(os.path.join(a.divisao, f'nitidez_{a.modelo}.json'), 'w', encoding='utf-8') as fo:
        json.dump(out, fo, ensure_ascii=False, indent=1)

    # histograma da calibração
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 4))
    bins = np.logspace(np.log10(max(1e-6, min(v.min() for v in n_val.values()))), np.log10(max(v.max() for v in n_val.values())), 60)
    for k, v in n_val.items():
        ax.hist(v, bins=bins, alpha=0.55, label=f'{k} (n={len(v)})')
    ax.axvline(limiar, color='k', ls='--', label=f'limiar = {limiar:.4g} (percentil {PERCENTIL} das originais)')
    ax.set_xscale('log'); ax.set_xlabel('nitidez (variância do laplaciano, escala log)'); ax.set_ylabel('fotos')
    ax.set_title('Calibração da salvaguarda de nitidez — validação'); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(a.divisao, f'nitidez_calibracao_{a.modelo}.png'), dpi=120)


if __name__ == '__main__':
    main()
