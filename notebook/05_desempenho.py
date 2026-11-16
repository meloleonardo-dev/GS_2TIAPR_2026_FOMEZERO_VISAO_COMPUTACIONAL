# -*- coding: utf-8 -*-
"""
05_desempenho.py — FOMEZERO · VCIA
Nicho: Triagem visual de hortifrúti excedente antes do cadastro do lote de doação

Desempenho computacional [§2.4, §2.5; REQ-VCIA-30 a 34, 55]:
1. Latência média por imagem (lote = 1), medida em GPU e em CPU, separando:
   - pré-processamento (abrir JPEG 512x512, redimensionar para 224x224, normalizar);
   - inferência do modelo (com aquecimento antes de medir; cuda.synchronize na GPU).
2. "Bancada" simulada (monitoramento contínuo): sequência de N fotos do TESTE, de vários produtos,
   processadas uma a uma de ponta a ponta (ler + pré-processar + inferir + desenhar o resultado).
   Mede o FPS e grava um vídeo MP4 com o rótulo, o produto, a confiança e o aviso em cada quadro.
   O vídeo é exibido a 1 quadro/s para ser legível; o FPS medido é o do processamento.
3. Registra o hardware e as versões de software em detalhe.

Uso: python 05_desempenho.py --modelo efficientnet_b0 --dados <Processed Data> --divisao <evidencias> --pesos <.pt>
     [--video <saída.mp4>] [--n_seq 40]
"""
import argparse, ctypes, json, os, platform, subprocess, time, unicodedata
import numpy as np
import torch, torchvision, cv2
from PIL import Image
import comum as C


def hardware():
    def ps(cmd):
        try:
            return subprocess.run(['powershell', '-NoProfile', '-Command', cmd], capture_output=True, text=True, timeout=30).stdout.strip()
        except Exception:
            return None

    class MEM(ctypes.Structure):
        _fields_ = [('dwLength', ctypes.c_ulong), ('dwMemoryLoad', ctypes.c_ulong), ('ullTotalPhys', ctypes.c_ulonglong),
                    ('ullAvailPhys', ctypes.c_ulonglong), ('a', ctypes.c_ulonglong), ('b', ctypes.c_ulonglong),
                    ('c', ctypes.c_ulonglong), ('d', ctypes.c_ulonglong), ('e', ctypes.c_ulonglong)]
    m = MEM(); m.dwLength = ctypes.sizeof(MEM)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return dict(cpu=ps('(Get-CimInstance Win32_Processor).Name'),
                cpu_nucleos_logicos=os.cpu_count(),
                ram_gb=round(m.ullTotalPhys / 2**30, 1),
                gpu=torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
                gpu_memoria_gb=round(torch.cuda.get_device_properties(0).total_memory / 2**30, 1) if torch.cuda.is_available() else None,
                driver_nvidia=ps('(nvidia-smi --query-gpu=driver_version --format=csv,noheader)'),
                so=platform.platform(), python=platform.python_version(), torch=torch.__version__,
                torchvision=torchvision.__version__, cuda=torch.version.cuda, opencv=cv2.__version__,
                observacao='notebook em tomada; outros programas abertos podem variar os tempos')


def latencias(modelo, caminhos, disp, n, aquecer=20):
    tf = C.TF_AVAL
    t_pre, t_inf = [], []
    with torch.no_grad():
        for k in range(aquecer + n):
            p = caminhos[k % len(caminhos)]
            t0 = time.perf_counter()
            x = tf(Image.open(p).convert('RGB')).unsqueeze(0).to(disp)
            if disp.type == 'cuda': torch.cuda.synchronize()
            t1 = time.perf_counter()
            modelo(x)
            if disp.type == 'cuda': torch.cuda.synchronize()
            t2 = time.perf_counter()
            if k >= aquecer:
                t_pre.append((t1 - t0) * 1000); t_inf.append((t2 - t1) * 1000)
    a, b = np.array(t_pre), np.array(t_inf)
    return dict(n=n, aquecimento=aquecer,
                preproc_ms_media=round(a.mean(), 2), inferencia_ms_media=round(b.mean(), 2),
                inferencia_ms_p50=round(float(np.percentile(b, 50)), 2), inferencia_ms_p95=round(float(np.percentile(b, 95)), 2),
                total_ms_media=round((a + b).mean(), 2), fps_equivalente=round(1000 / (a + b).mean(), 1))


LARGURA, ALT_TOPO, ALT_FAIXA = 640, 64, 196


import functools


@functools.lru_cache(maxsize=None)          # carrega cada fonte uma vez só (desenhar não pode pesar no FPS)
def _fonte(tam, negrito=False):
    from PIL import ImageFont
    for nome in (('arialbd.ttf' if negrito else 'arial.ttf'), 'DejaVuSans.ttf'):
        try:
            return ImageFont.truetype(nome, tam)
        except OSError:
            continue
    return ImageFont.load_default()


def _quebrar(d, texto, fonte, largura):
    """Quebra o texto em linhas que cabem na largura (nada é cortado)."""
    linhas, atual = [], ''
    for p in texto.split(' '):
        teste = (atual + ' ' + p).strip()
        if d.textlength(teste, font=fonte) <= largura:
            atual = teste
        else:
            linhas.append(atual); atual = p
    return linhas + [atual]


@functools.lru_cache(maxsize=None)
def _moldura(texto_cls):
    """Partes fixas do quadro (topo com o nicho completo, bloco da sugestão, aviso), desenhadas uma vez por classe.
    Devolve (moldura RGB, y da linha de confiança)."""
    from PIL import ImageDraw
    q = Image.new('RGB', (LARGURA, ALT_TOPO + LARGURA + ALT_FAIXA), 'white')
    d = ImageDraw.Draw(q)
    d.text((10, 6), 'FOMEZERO · VCIA — bancada simulada (fotos do teste da AgriFreshNET)', fill=(0, 0, 0), font=_fonte(16, True))
    for i, l in enumerate(_quebrar(d, C.NICHO, _fonte(14), LARGURA - 20)):
        d.text((10, 28 + 17 * i), l, fill=(40, 40, 40), font=_fonte(14))
    y = ALT_TOPO + LARGURA + 6
    cor = (200, 0, 0) if texto_cls == C.CONDICAO_PT['Rotten'] else \
        ((230, 120, 0) if texto_cls in (C.INCONCLUSIVO, C.CONDICAO_PT['Semi-Fresh']) else (0, 130, 0))
    d.text((10, y), 'Sugestão da triagem visual:', fill=(0, 0, 0), font=_fonte(14)); y += 18
    for l in _quebrar(d, texto_cls, _fonte(17, True), LARGURA - 20):
        d.text((10, y), l, fill=cor, font=_fonte(17, True)); y += 21
    y_det = y + 2; y += 26
    for l in _quebrar(d, C.AVISO, _fonte(13), LARGURA - 20):
        d.text((10, y), l, fill=(70, 70, 70), font=_fonte(13)); y += 16
    return q, y_det


def quadro(img_rgb, texto_cls, texto_prod, conf, inconc, borrada=False):
    """Quadro do vídeo: topo (nicho completo) + foto + faixa (sugestão, confiança, produto, aviso fixo).
    Desenhado com PIL (fonte TrueType) para manter acentos e o texto exato da DEC-023."""
    from PIL import ImageDraw
    base, y_det = _moldura(texto_cls)
    q = base.copy()
    q.paste(img_rgb.resize((LARGURA, LARGURA)), (0, ALT_TOPO))
    detalhe = ('foto borrada — tire outra foto' if borrada else f'confiança {conf * 100:.0f}%') + f' · produto reconhecido: {texto_prod}'
    ImageDraw.Draw(q).text((10, y_det), detalhe, fill=(0, 0, 0), font=_fonte(15))
    return cv2.cvtColor(np.array(q), cv2.COLOR_RGB2BGR)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--modelo', default='efficientnet_b0')
    ap.add_argument('--dados', required=True)
    ap.add_argument('--divisao', required=True)
    ap.add_argument('--pesos', required=True)
    ap.add_argument('--video', default=None)
    ap.add_argument('--n_seq', type=int, default=40)
    ap.add_argument('--so_video', action='store_true',
                    help='não mede latência: só refaz a sequência/vídeo e grava sequencia_video_<modelo>.json')
    a = ap.parse_args()
    tau = json.load(open(os.path.join(a.divisao, f'metricas_teste_{a.modelo}.json'), encoding='utf-8'))['calibracao']['tau']
    arq_nit = os.path.join(a.divisao, f'nitidez_{a.modelo}.json')       # salvaguarda de nitidez (DEC-010), se existir
    lim_nit = json.load(open(arq_nit, encoding='utf-8'))['calibracao']['limiar_nitidez'] if os.path.exists(arq_nit) else None
    teste = C.ler_divisao(os.path.join(a.divisao, 'divisao_teste.csv'))
    caminhos = [os.path.join(a.dados, l['caminho']) for l in teste]
    res = dict(modelo=a.modelo, resolucao_base='512x512', resolucao_modelo=f'{C.TAMANHO}x{C.TAMANHO}', lote=1,
               hardware=hardware(), latencia={})

    for nome_disp, n in (() if a.so_video else (('cuda', 200), ('cpu', 100))):
        if nome_disp == 'cuda' and not torch.cuda.is_available():
            continue
        disp = torch.device(nome_disp)
        modelo = C.carregar_modelo(a.pesos, a.modelo, disp)
        res['latencia'][nome_disp] = latencias(modelo, caminhos, disp, n)
        print(nome_disp, res['latencia'][nome_disp], flush=True)

    # bancada simulada: N fotos do teste, embaralhadas com semente fixa (vários produtos e estágios)
    disp = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    modelo = C.carregar_modelo(a.pesos, a.modelo, disp)
    rng = np.random.default_rng(7)
    seq = [teste[i] for i in rng.choice(len(teste), size=min(a.n_seq, len(teste)), replace=False)]
    escritor = None
    if a.video:
        escritor = cv2.VideoWriter(a.video, cv2.VideoWriter_fourcc(*'mp4v'), 1, (LARGURA, ALT_TOPO + LARGURA + ALT_FAIXA))
    tempos, registros = [], []
    with torch.no_grad():
        for l in seq:
            t0 = time.perf_counter()
            img = Image.open(os.path.join(a.dados, l['caminho'])).convert('RGB')
            borrada = lim_nit is not None and C.nitidez(img) < lim_nit
            p = modelo(C.TF_AVAL(img).unsqueeze(0).to(disp)).float().softmax(1).cpu()
            cond, prod = C.agregar(p)
            c, k = cond[0].max(0); cp, kp = prod[0].max(0)
            inconc = float(c) < tau or borrada
            cls = C.INCONCLUSIVO if inconc else C.CONDICAO_PT[C.ESTAGIOS[int(k)]]
            fr = quadro(img, cls, C.PRODUTO_PT[C.PRODUTOS[int(kp)]], float(c), inconc, borrada)
            tempos.append(time.perf_counter() - t0)
            if escritor is not None:
                escritor.write(fr)
            registros.append(dict(arquivo=l['caminho'], real=l['estagio'], sugestao=cls, confianca=round(float(c), 4)))
    if escritor is not None:
        escritor.release()
    t = np.array(tempos[3:])          # descarta os 3 primeiros quadros (aquecimento)
    res['sequencia'] = dict(n_quadros=len(seq), quadros_medidos=len(t), dispositivo=str(disp),
                            ms_por_quadro_ponta_a_ponta=round(t.mean() * 1000, 2), fps_ponta_a_ponta=round(1 / t.mean(), 1),
                            video=os.path.basename(a.video) if a.video else None, video_fps_exibicao=1,
                            acertos_condicao=sum(1 for r in registros if C.CONDICAO_PT.get(r['real']) == r['sugestao']),
                            inconclusivos=sum(1 for r in registros if r['sugestao'] == C.INCONCLUSIVO), quadros=registros)
    res['sequencia']['salvaguarda_nitidez'] = lim_nit is not None
    print('sequencia', {k: v for k, v in res['sequencia'].items() if k != 'quadros'})
    if a.so_video:   # não sobrescreve as latências já medidas
        saida = dict(modelo=a.modelo, nota='refeito só o vídeo/sequência (rótulos revisados, nitidez); latências em desempenho_<modelo>.json',
                     hardware=res['hardware'], sequencia=res['sequencia'])
        with open(os.path.join(a.divisao, f'sequencia_video_{a.modelo}.json'), 'w', encoding='utf-8') as f:
            json.dump(saida, f, ensure_ascii=False, indent=1)
        return
    with open(os.path.join(a.divisao, f'desempenho_{a.modelo}.json'), 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
