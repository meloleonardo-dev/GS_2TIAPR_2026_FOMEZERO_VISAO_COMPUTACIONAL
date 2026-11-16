# -*- coding: utf-8 -*-
"""
app.py — FOMEZERO · VCIA — Triagem visual antes do cadastro (módulo do protótipo CitizenTech)
Nicho: Triagem visual de hortifrúti excedente antes do cadastro do lote de doação

Funcionalidade do protótipo [§2.4; REQ-VCIA-01, 04, 05, 06, 26, 27, 29, 30, 54, 57, 58]:
- Aba "Imagem": recebe UMA foto e mostra a condição visual SUGERIDA, o produto reconhecido, a confiança,
  o texto pronto para o campo "Condição informada pelo doador" e o aviso fixo (DEC-023).
- Aba "Sequência (bancada)": processa várias fotos em sequência (monitoramento contínuo) e mede o FPS.
- Endpoint "/triagem" (CT-08, opção T1): devolve o JSON no esquema fomezero.vcia.v1.
Salvaguardas: é SUGESTÃO; nada é barrado; a classe 3 e o "inconclusivo" pedem confirmação humana;
nenhum texto diz "apto", "seguro" ou "próprio para consumo".

Uso: python app.py            (abre em http://127.0.0.1:7860)
     python app.py --share    (gera um link público temporário do Gradio, para T1/T2 do CT-08)
"""
import json, os, sys, time
import gradio as gr
import torch
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..', 'notebook'))
import comum as C   # noqa: E402

MODELO = 'efficientnet_b0'
PESOS = os.path.join(AQUI, '..', 'modelo', f'{MODELO}.pt')
METRICAS = os.path.join(AQUI, '..', 'evidencias', f'metricas_teste_{MODELO}.json')
DISP = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
REDE = C.carregar_modelo(PESOS, MODELO, DISP)
TAU = json.load(open(METRICAS, encoding='utf-8'))['calibracao']['tau']
# salvaguarda de nitidez (DEC-010): limiar calibrado na validação por notebook/06_nitidez.py
LIMIAR_NITIDEZ = json.load(open(os.path.join(AQUI, '..', 'evidencias', f'nitidez_{MODELO}.json'),
                                encoding='utf-8'))['calibracao']['limiar_nitidez']
PRODUTOS_ACEITOS = ', '.join(C.PRODUTO_PT[p] for p in C.PRODUTOS)


def triagem(img):
    """Classifica uma foto e devolve o dicionário do contrato CT-08 (fomezero.vcia.v1)."""
    if img is None:
        return {'status': 'erro', 'erro': {'codigo': 'IMAGEM_INVALIDA', 'mensagem': 'Envie uma foto.'}, 'aviso': C.AVISO}
    t0 = time.perf_counter()
    img = img.convert('RGB')
    nit = C.nitidez(img)
    borrada = nit < LIMIAR_NITIDEZ
    with torch.no_grad():
        p = REDE(C.TF_AVAL(img).unsqueeze(0).to(DISP)).float().softmax(1).cpu()
    cond, prod = C.agregar(p)
    c, k = cond[0].max(0)
    cp, kp = prod[0].max(0)
    inconc = float(c) < TAU or borrada
    classe = C.INCONCLUSIVO if inconc else C.CONDICAO_PT[C.ESTAGIOS[int(k)]]
    motivo = 'foto_borrada' if borrada else ('confianca_abaixo_do_limiar' if inconc else None)
    return {'esquema': 'fomezero.vcia.v1', 'versao': 'ct08-v1', 'nicho': C.NICHO,
            'motivo_inconclusivo': motivo,
            'nitidez': {'valor': float(f'{nit:.4g}'), 'limiar': LIMIAR_NITIDEZ, 'borrada': borrada,
                        'mensagem': C.MSG_NITIDEZ if borrada else None},
            'produto': {'rotulo': C.PRODUTO_PT[C.PRODUTOS[int(kp)]], 'confianca': round(float(cp), 4)},
            'condicao': {'classe': classe, 'confianca': round(float(c), 4)},
            'probabilidades_condicao': {C.CONDICAO_PT[e]: round(float(cond[0][i]), 4) for i, e in enumerate(C.ESTAGIOS)},
            'limiar': TAU, 'inconclusivo': inconc,
            'texto_sugerido': C.texto_sugerido(classe, float(c)),
            'pede_confirmacao_humana': inconc or C.ESTAGIOS[int(k)] == 'Rotten',
            'modelo': f'{MODELO} (ajuste fino, AgriFreshNET)', 'tempo_ms': round((time.perf_counter() - t0) * 1000, 1),
            'simulado': False, 'aviso': C.AVISO}


def tela_imagem(img):
    r = triagem(img)
    if r.get('status') == 'erro':
        return r['erro']['mensagem'], {}, '', r
    c = r['condicao']
    alerta = ''
    if r['nitidez']['borrada']:
        alerta += f"\n\n> 📷 **{r['nitidez']['mensagem']}**"
    if r['pede_confirmacao_humana']:
        alerta += ('\n\n> ⚠️ **Confirmação humana necessária.** Avalie o item pessoalmente antes de cadastrar. '
                  'Nada foi bloqueado: a decisão é sua.')
    if r['motivo_inconclusivo'] == 'foto_borrada':
        conf = f"{c['confianca'] * 100:.0f}% (não usada: foto borrada)"
    elif r['inconclusivo']:
        conf = f"{c['confianca'] * 100:.0f}% (abaixo do limiar de {r['limiar'] * 100:.0f}%)"
    else:
        conf = f"{c['confianca'] * 100:.0f}%"
    card = (f"**Sugestão da triagem visual:**\n### {c['classe']}\n**Confiança:** {conf}  \n"
            f"**Produto reconhecido:** {r['produto']['rotulo']} ({r['produto']['confianca'] * 100:.0f}%)  \n"
            f"<small>Se o produto reconhecido estiver errado, a sugestão não vale para esta foto.</small>{alerta}")
    # no "inconclusivo" o gráfico some: o destaque da classe mais provável pareceria uma sugestão
    barras = None if r['inconclusivo'] else r['probabilidades_condicao']
    return card, barras, r['texto_sugerido'], r


def tela_sequencia(arquivos):
    if not arquivos:
        return [], 'Envie várias fotos (ou use as fotos de exemplo).'
    galeria, tempos, linhas = [], [], []
    for n, a in enumerate(arquivos, 1):
        caminho = a if isinstance(a, str) else a.name
        t0 = time.perf_counter()
        img = Image.open(caminho).convert('RGB')
        r = triagem(img)
        tempos.append(time.perf_counter() - t0)
        conf = 'foto borrada' if r['nitidez']['borrada'] else f"confiança {r['condicao']['confianca'] * 100:.0f}%"
        galeria.append((img, f"{n}. {r['condicao']['classe']} · {conf} · {r['produto']['rotulo']}"))
        # a galeria corta legendas longas: a tabela abaixo mostra o texto completo de cada foto
        linhas.append(f"| {n} | {r['condicao']['classe']} | {conf} | {r['produto']['rotulo']} |")
    med = sum(tempos[1:] or tempos) / len(tempos[1:] or tempos)
    fps = f'{1 / med:.1f}'.replace('.', ',')          # vírgula decimal (tela em português)
    resumo = (f'**{len(arquivos)} fotos processadas em sequência** · {med * 1000:.0f} ms por foto (ponta a ponta) · '
              f'**{fps} FPS** · dispositivo: {"GPU" if DISP.type == "cuda" else "CPU"}\n\n'
              '| Foto | Sugestão da triagem visual | Confiança | Produto reconhecido |\n|---|---|---|---|\n'
              + '\n'.join(linhas))
    return galeria, resumo


PASTA_EX = os.path.join(AQUI, 'exemplos')
EXEMPLOS = sorted(os.path.join(PASTA_EX, f) for f in os.listdir(PASTA_EX) if f.lower().endswith(('.jpg', '.jpeg', '.png'))) \
    if os.path.isdir(PASTA_EX) else []

with gr.Blocks(title='FOMEZERO · VCIA — Triagem visual antes do cadastro') as demo:
    gr.Markdown(f'# FOMEZERO · VCIA — Triagem visual antes do cadastro\n'
                f'**{C.NICHO}** · módulo de visão computacional do protótipo CitizenTech\n\n'
                f'Fotografe **um item por vez, de cima, sobre fundo claro**. Produtos aceitos: {PRODUTOS_ACEITOS}. '
                f'Pratos prontos, carnes e caixas com vários itens estão fora do escopo.')
    gr.Markdown(f'> **{C.AVISO}**')
    with gr.Tab('Imagem'):
        with gr.Row():
            entrada = gr.Image(type='pil', label='Foto do item')
            with gr.Column():
                card = gr.Markdown()
                barras = gr.Label(label='Confiança por condição', num_top_classes=3)
                texto = gr.Textbox(label='Sugestão para "Condição informada pelo doador" (edite antes de salvar)',
                                   interactive=True)
        botao = gr.Button('Sugerir condição pela foto', variant='primary')
        with gr.Accordion('Resposta no contrato CT-08 (fomezero.vcia.v1)', open=False):
            js = gr.JSON()
        if EXEMPLOS:
            gr.Examples([[e] for e in EXEMPLOS], inputs=entrada, examples_per_page=len(EXEMPLOS),
                        label='Fotos de exemplo (conjunto de teste da AgriFreshNET, CC BY 4.0; '
                              'a última foi borrada por nós, de propósito, para mostrar a salvaguarda de nitidez)')
        botao.click(tela_imagem, entrada, [card, barras, texto, js])
        gr.Button('Só API', visible=False).click(triagem, entrada, gr.JSON(visible=False), api_name='triagem')
    with gr.Tab('Sequência (bancada)'):
        gr.Markdown('Simula a triagem visual contínua de uma bancada de doação: várias fotos processadas em sequência. '
                    'Cada resultado é uma sugestão; o doador avalia cada item.')
        arqs = gr.File(file_count='multiple', file_types=['image'], label='Fotos da bancada',
                       value=EXEMPLOS or None)
        rodar = gr.Button('Processar sequência', variant='primary')
        resumo = gr.Markdown()
        gal = gr.Gallery(label='Resultado da sequência', columns=4, height='auto')
        rodar.click(tela_sequencia, arqs, [gal, resumo])
    gr.Markdown(f'<small>Modelo: {MODELO} ajustado na AgriFreshNET (Risdin et al., 2026, Mendeley Data, '
                f'DOI 10.17632/42m5tb7yv9.1, CC BY 4.0). Limiar do "inconclusivo": confiança abaixo de {TAU * 100:.0f}%. '
                'Fotos borradas (nitidez abaixo do limiar calibrado na validação) também viram "inconclusivo". '
                'FIAP · Global Solution 2026.2 · 2TIAPR-2026 · Grupo: Erick Miguel (RM 564896), '
                'Leonardo Melo (RM 567097), Luna Oliveira (RM 564215).</small>')

if __name__ == '__main__':
    demo.launch(share='--share' in sys.argv)
