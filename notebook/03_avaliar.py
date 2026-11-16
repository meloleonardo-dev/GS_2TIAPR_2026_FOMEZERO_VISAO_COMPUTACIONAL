# -*- coding: utf-8 -*-
"""
03_avaliar.py — FOMEZERO · VCIA
Nicho: Triagem visual de hortifrúti excedente antes do cadastro do lote de doação

Avaliação métrica [§2.3, §2.5; REQ-VCIA-17, 18, 19, 20, 24, 37]:
1. Calibra o limiar τ do "inconclusivo" SÓ na VALIDAÇÃO.
   Regra fixada ANTES de ver o teste: τ = menor valor (passo 0,01) em que a acurácia da condição
   nas imagens aceitas (confiança >= τ) chega a 95% mantendo cobertura >= 70%; se nenhum τ atingir,
   usa o τ de maior acurácia aceita com cobertura >= 70%.
2. No TESTE (só originais, nunca vistos): precisão, recall, F1 (por classe e macro), matriz de confusão
   para a CONDIÇÃO (3 classes) e para o PRODUTO (8 classes), sempre com n (suporte).
3. Efeito de τ no teste: cobertura, inconclusivos por classe verdadeira, métricas nas aceitas.
4. Galeria de acertos e erros (erros mais confiantes primeiro) para a análise qualitativa.

Uso: python 03_avaliar.py --modelo efficientnet_b0 --dados <Processed Data> --divisao <evidencias> --pesos <.pt>
"""
import argparse, json, os
import numpy as np
import torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
from sklearn.metrics import precision_recall_fscore_support, confusion_matrix, accuracy_score
import comum as C


def probabilidades(modelo, linhas, raiz, disp):
    dl = torch.utils.data.DataLoader(C.BaseHortifruti(raiz, linhas, C.TF_AVAL), batch_size=64, num_workers=4)
    ps, ts = [], []
    with torch.no_grad():
        for x, t in dl:
            ps.append(modelo(x.to(disp)).float().softmax(1).cpu())
            ts.append(t)
    return torch.cat(ps), torch.cat(ts)


def metricas(y, p, nomes):
    pr, rc, f1, sup = precision_recall_fscore_support(y, p, labels=list(range(len(nomes))), zero_division=0)
    prm, rcm, f1m, _ = precision_recall_fscore_support(y, p, average='macro', zero_division=0)
    return {'por_classe': {n: dict(precisao=round(float(pr[i]), 4), recall=round(float(rc[i]), 4),
                                   f1=round(float(f1[i]), 4), n=int(sup[i])) for i, n in enumerate(nomes)},
            'macro': dict(precisao=round(float(prm), 4), recall=round(float(rcm), 4), f1=round(float(f1m), 4)),
            'acuracia': round(float(accuracy_score(y, p)), 4), 'n': int(len(y)),
            'matriz_confusao': confusion_matrix(y, p, labels=list(range(len(nomes)))).tolist(),
            'matriz_linhas_verdadeiro_colunas_previsto': nomes}


def figura_matriz(m, nomes, titulo, arq):
    m = np.array(m)
    fig, ax = plt.subplots(figsize=(1.1 * len(nomes) + 2, 1.0 * len(nomes) + 1.5))
    ax.imshow(m, cmap='Blues')
    for i in range(len(nomes)):
        for j in range(len(nomes)):
            ax.text(j, i, m[i, j], ha='center', va='center', color='white' if m[i, j] > m.max() / 2 else 'black')
    ax.set_xticks(range(len(nomes)), nomes, rotation=35, ha='right')
    ax.set_yticks(range(len(nomes)), nomes)
    ax.set_xlabel('previsto'); ax.set_ylabel('verdadeiro'); ax.set_title(titulo)
    fig.tight_layout(); fig.savefig(arq, dpi=130); plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--modelo', default='efficientnet_b0')
    ap.add_argument('--dados', required=True)
    ap.add_argument('--divisao', required=True)
    ap.add_argument('--pesos', required=True)
    a = ap.parse_args()
    disp = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    modelo = C.carregar_modelo(a.pesos, a.modelo, disp)
    saida = a.divisao
    rotulo_curto = ['Fresh', 'Semi-Fresh', 'Rotten']
    prod_pt = [C.PRODUTO_PT[p] for p in C.PRODUTOS]

    # ------------------------------------------------ 1. calibração de τ na VALIDAÇÃO
    val = C.ler_divisao(os.path.join(a.divisao, 'divisao_validacao.csv'))
    pv, tv = probabilidades(modelo, val, a.dados, disp)
    cv, _ = C.agregar(pv)
    yv = np.array([C.ESTAGIOS.index(C.CLASSES[i].split('|')[1]) for i in tv.tolist()])
    confv, predv = cv.max(1)
    confv, predv = confv.numpy(), predv.numpy()
    curva = []
    for tau in np.round(np.arange(0.34, 1.0, 0.01), 2):
        aceita = confv >= tau
        cob = float(aceita.mean())
        acc = float((predv[aceita] == yv[aceita]).mean()) if aceita.any() else float('nan')
        curva.append(dict(tau=float(tau), cobertura=round(cob, 4), acuracia_aceitas=round(acc, 4)))
    validos = [c for c in curva if c['cobertura'] >= 0.70]
    alvo = [c for c in validos if c['acuracia_aceitas'] >= 0.95]
    escolha = alvo[0] if alvo else max(validos, key=lambda c: c['acuracia_aceitas'])
    tau = escolha['tau']
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot([c['tau'] for c in curva], [c['cobertura'] for c in curva], label='cobertura')
    ax.plot([c['tau'] for c in curva], [c['acuracia_aceitas'] for c in curva], label='acurácia nas aceitas')
    ax.axvline(tau, color='gray', ls='--', label=f'τ escolhido = {tau:.2f}')
    ax.set_xlabel('limiar τ (confiança da condição)'); ax.set_title(f'Validação (n={len(yv)}) — {a.modelo}')
    ax.legend(); fig.tight_layout(); fig.savefig(os.path.join(saida, f'curva_tau_{a.modelo}.png'), dpi=130); plt.close(fig)

    # ------------------------------------------------ 2. TESTE
    teste = C.ler_divisao(os.path.join(a.divisao, 'divisao_teste.csv'))
    pt, tt = probabilidades(modelo, teste, a.dados, disp)
    ct, prt = C.agregar(pt)
    y_c = np.array([C.ESTAGIOS.index(C.CLASSES[i].split('|')[1]) for i in tt.tolist()])
    y_p = np.array([C.PRODUTOS.index(C.CLASSES[i].split('|')[0]) for i in tt.tolist()])
    conf_c, p_c = [v.numpy() for v in ct.max(1)]
    conf_p, p_p = [v.numpy() for v in prt.max(1)]
    m_cond = metricas(y_c, p_c, rotulo_curto)
    m_prod = metricas(y_p, p_p, prod_pt)
    acc24 = float((pt.argmax(1) == tt).float().mean())
    figura_matriz(m_cond['matriz_confusao'], rotulo_curto, f'Condição — teste (n={len(y_c)})',
                  os.path.join(saida, f'matriz_condicao_{a.modelo}.png'))
    figura_matriz(m_prod['matriz_confusao'], prod_pt, f'Produto — teste (n={len(y_p)})',
                  os.path.join(saida, f'matriz_produto_{a.modelo}.png'))

    # ------------------------------------------------ 3. efeito de τ no TESTE
    aceita = conf_c >= tau
    inconc = {rotulo_curto[k]: int(((~aceita) & (y_c == k)).sum()) for k in range(3)}
    m_aceitas = metricas(y_c[aceita], p_c[aceita], rotulo_curto) if aceita.any() else None
    rotten_como_fresh = int(((y_c == 2) & (p_c == 0)).sum())
    rotten_como_fresh_aceitas = int(((y_c == 2) & (p_c == 0) & aceita).sum())

    # ------------------------------------------------ 4. por produto (acurácia da condição)
    por_produto = {}
    for k, nome in enumerate(prod_pt):
        s = y_p == k
        por_produto[nome] = dict(n=int(s.sum()), acuracia_condicao=round(float((p_c[s] == y_c[s]).mean()), 4))

    # ------------------------------------------------ 5. galeria de acertos e erros
    erros = np.where(p_c != y_c)[0]
    erros = erros[np.argsort(-conf_c[erros])][:12]
    acertos = np.where(p_c == y_c)[0]
    rng = np.random.default_rng(0)
    acertos = rng.choice(acertos, size=min(6, len(acertos)), replace=False)
    W = 200
    sel = list(acertos) + list(erros)
    img = Image.new('RGB', (W * 6, (W + 46) * ((len(sel) + 5) // 6)), 'white')
    d = ImageDraw.Draw(img)
    try:   # fonte com acentos (a fonte padrão do Pillow não desenha "ã")
        fonte = ImageFont.truetype('arial.ttf', 12)
    except OSError:
        fonte = ImageFont.load_default()
    galeria = []
    for k, i in enumerate(sel):
        l = teste[i]
        x0, y0 = (k % 6) * W, (k // 6) * (W + 46)
        img.paste(Image.open(os.path.join(a.dados, l['caminho'])).convert('RGB').resize((W, W)), (x0, y0))
        ok = p_c[i] == y_c[i]
        d.text((x0 + 3, y0 + W + 2), f"{'ACERTO' if ok else 'ERRO'} | real: {rotulo_curto[y_c[i]]}", fill='green' if ok else 'red', font=fonte)
        d.text((x0 + 3, y0 + W + 16), f'prev: {rotulo_curto[p_c[i]]} ({conf_c[i] * 100:.0f}%)', fill='black', font=fonte)
        d.text((x0 + 3, y0 + W + 30), f'produto prev: {prod_pt[p_p[i]]}', fill='black', font=fonte)
        galeria.append(dict(arquivo=l['caminho'], acerto=bool(ok), real=rotulo_curto[y_c[i]],
                            previsto=rotulo_curto[p_c[i]], confianca=round(float(conf_c[i]), 4),
                            produto_real=prod_pt[y_p[i]], produto_previsto=prod_pt[p_p[i]]))
    img.save(os.path.join(saida, f'galeria_acertos_erros_{a.modelo}.png'))

    res = dict(modelo=a.modelo, pesos=os.path.basename(a.pesos), conjunto='teste (só originais)',
               calibracao=dict(conjunto='validação (só originais)', n=int(len(yv)),
                               regra='menor τ com acurácia nas aceitas >= 95% e cobertura >= 70%; senão maior acurácia com cobertura >= 70%',
                               tau=tau, ponto_escolhido=escolha, curva=curva),
               condicao=m_cond, produto=m_prod, acuracia_24_classes=round(acc24, 4),
               com_limiar=dict(tau=tau, cobertura=round(float(aceita.mean()), 4), n_aceitas=int(aceita.sum()),
                               inconclusivos_por_classe_real=inconc, metricas_nas_aceitas=m_aceitas),
               rotten_previsto_como_fresh=dict(total=rotten_como_fresh, entre_aceitas=rotten_como_fresh_aceitas),
               acuracia_condicao_por_produto=por_produto, galeria=galeria)
    with open(os.path.join(saida, f'metricas_teste_{a.modelo}.json'), 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print(json.dumps(dict(tau=tau, ponto=escolha, condicao_macro=m_cond['macro'], condicao_acc=m_cond['acuracia'],
                          produto_macro=m_prod['macro'], acc24=round(acc24, 4), n_teste=len(y_c),
                          cobertura_teste=res['com_limiar']['cobertura'], inconclusivos=inconc,
                          rotten_como_fresh=res['rotten_previsto_como_fresh']), ensure_ascii=False, indent=1))
    for n, v in m_cond['por_classe'].items():
        print(n, v)


if __name__ == '__main__':
    main()
