# -*- coding: utf-8 -*-
"""
02_treinar.py — FOMEZERO · VCIA
Nicho: Triagem visual de hortifrúti excedente antes do cadastro do lote de doação

Ajuste fino (transfer learning) de uma CNN pré-treinada no ImageNet [§2.2; REQ-VCIA-12, 14, 16, 61]:
- entrada 224x224, normalização ImageNet; aumento leve só no treino (ver comum.py);
- 24 classes (produto x estágio); a escolha da melhor época usa o F1 macro da CONDIÇÃO (3 classes)
  no conjunto de VALIDAÇÃO — o teste não é usado aqui;
- AdamW + cosseno, suavização de rótulo 0,1, precisão mista (AMP) na GPU;
- grava os pesos da melhor época e o histórico em JSON.

Uso: python 02_treinar.py --modelo efficientnet_b0 --dados <Processed Data> --divisao <evidencias> --saida <modelo>
"""
import argparse, json, os, time
import torch
import torch.nn as nn
from sklearn.metrics import f1_score
import comum as C


def avaliar(modelo, carregador, disp):
    """Probabilidades no conjunto; devolve (F1 macro condição, acurácia 24 classes, perda média)."""
    modelo.eval()
    y, p_cond, acertos24, perda, n = [], [], 0, 0.0, 0
    crit = nn.CrossEntropyLoss()
    with torch.no_grad(), torch.autocast('cuda', enabled=disp.type == 'cuda'):
        for x, t in carregador:
            x, t = x.to(disp, non_blocking=True), t.to(disp)
            s = modelo(x)
            perda += crit(s.float(), t).item() * len(t)
            pr = s.float().softmax(1)
            acertos24 += (pr.argmax(1) == t).sum().item()
            cond, _ = C.agregar(pr)
            p_cond += cond.argmax(1).tolist()
            y += [C.ESTAGIOS.index(C.CLASSES[i].split('|')[1]) for i in t.tolist()]
            n += len(t)
    return f1_score(y, p_cond, average='macro'), acertos24 / n, perda / n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--modelo', default='efficientnet_b0')
    ap.add_argument('--dados', required=True)
    ap.add_argument('--divisao', required=True)
    ap.add_argument('--saida', required=True)
    ap.add_argument('--epocas', type=int, default=10)
    ap.add_argument('--lote', type=int, default=32)
    ap.add_argument('--lr', type=float, default=3e-4)
    ap.add_argument('--paciencia', type=int, default=3)
    a = ap.parse_args()
    torch.manual_seed(42)
    os.makedirs(a.saida, exist_ok=True)
    disp = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    treino = C.ler_divisao(os.path.join(a.divisao, 'divisao_treino.csv'))
    valid = C.ler_divisao(os.path.join(a.divisao, 'divisao_validacao.csv'))
    dl_t = torch.utils.data.DataLoader(C.BaseHortifruti(a.dados, treino, C.TF_TREINO), batch_size=a.lote,
                                       shuffle=True, num_workers=6, pin_memory=True, persistent_workers=True)
    dl_v = torch.utils.data.DataLoader(C.BaseHortifruti(a.dados, valid, C.TF_AVAL), batch_size=64,
                                       num_workers=4, pin_memory=True, persistent_workers=True)

    modelo = C.criar_modelo(a.modelo).to(disp)
    opt = torch.optim.AdamW(modelo.parameters(), lr=a.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=a.epocas)
    crit = nn.CrossEntropyLoss(label_smoothing=0.1)
    scaler = torch.amp.GradScaler('cuda', enabled=disp.type == 'cuda')

    hist, melhor, sem_melhora = [], -1.0, 0
    pesos = os.path.join(a.saida, f'{a.modelo}.pt')
    t0 = time.time()
    for ep in range(1, a.epocas + 1):
        modelo.train()
        te, perda, n = time.time(), 0.0, 0
        for x, t in dl_t:
            x, t = x.to(disp, non_blocking=True), t.to(disp, non_blocking=True)
            opt.zero_grad(set_to_none=True)
            with torch.autocast('cuda', enabled=disp.type == 'cuda'):
                perda_lote = crit(modelo(x), t)
            scaler.scale(perda_lote).backward()
            scaler.step(opt)
            scaler.update()
            perda += perda_lote.item() * len(t)
            n += len(t)
        sched.step()
        f1v, acc24v, perdav = avaliar(modelo, dl_v, disp)
        reg = dict(epoca=ep, perda_treino=round(perda / n, 4), perda_val=round(perdav, 4),
                   f1_macro_condicao_val=round(f1v, 4), acuracia_24_val=round(acc24v, 4),
                   segundos=round(time.time() - te, 1))
        hist.append(reg)
        print(reg, flush=True)
        if f1v > melhor:
            melhor, sem_melhora = f1v, 0
            torch.save(modelo.state_dict(), pesos)
            reg['salvo'] = True
        else:
            sem_melhora += 1
            if sem_melhora >= a.paciencia:
                print('parada antecipada', flush=True)
                break

    info = dict(modelo=a.modelo, classes=C.CLASSES, tamanho=C.TAMANHO, media=C.MEDIA, desvio=C.DESVIO,
                n_treino=len(treino), n_validacao=len(valid), epocas_max=a.epocas, lote=a.lote, lr=a.lr,
                criterio='F1 macro da condição na validação', melhor_f1_val=round(melhor, 4),
                melhor_epoca=max((h for h in hist if h.get('salvo')), key=lambda h: h['f1_macro_condicao_val'])['epoca'],
                tempo_total_s=round(time.time() - t0, 1), dispositivo=str(disp),
                gpu=torch.cuda.get_device_name(0) if disp.type == 'cuda' else None,
                torch=torch.__version__, historico=hist)
    with open(os.path.join(a.divisao, f'treino_{a.modelo}.json'), 'w', encoding='utf-8') as f:
        json.dump(info, f, ensure_ascii=False, indent=1)
    print('melhor F1 macro (condição, validação):', round(melhor, 4), '| pesos:', pesos)


if __name__ == '__main__':
    main()
