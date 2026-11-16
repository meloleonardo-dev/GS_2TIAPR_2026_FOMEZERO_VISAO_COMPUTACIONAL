# FOMEZERO · VCIA — Módulo de Visão Computacional do CitizenTech

**Nicho [§1.b, interesse social]: Triagem visual de hortifrúti excedente antes do cadastro do lote de doação**

> Apoio à triagem visual. A imagem não atesta que o alimento é seguro para consumo; a decisão é do doador e da vigilância sanitária.

FIAP · Global Solution 2026.2 · Tecnólogo em IA · turma 2TIAPR-2026 · matéria Visão Computacional.

| Integrante | RM |
|---|---|
| Erick Miguel | 564896 |
| Leonardo Melo | 567097 |
| Luna Oliveira | 564215 |

Parte do FOMEZERO ("Protótipo Integrado CitizenTech com IA para Apoiar o Cidadão"). O doador fotografa **um item de hortifrúti por vez, de cima, sobre fundo claro**. Uma CNN (EfficientNet-B0, transferência de aprendizado) **sugere** a condição visual e o produto, com a confiança. O texto pré-preenche o campo "Condição informada pelo doador" do lote de doação, e o doador pode editá-lo. Nada é bloqueado.

| Resultado (teste, n = 786 fotos originais) | EfficientNet-B0 |
|---|---|
| F1 macro da condição (3 classes) | 0,940 |
| F1 macro do produto (8 classes) | 0,993 |
| Inferência por imagem, 224×224 (RTX 3050 6 GB Laptop / i5-13420H) | 17,1 ms GPU · 44,1 ms CPU |

Detalhes, limitações e análise de erros: **[relatório técnico](relatorio/RELATORIO_TECNICO_VCIA.md)**.

## Entregas ([§4] do enunciado)
| Entrega | Onde |
|---|---|
| (a) Código executável comentado | [`notebook/`](notebook/) (scripts `01_` a `07_` + `comum.py`) e [`app/app.py`](app/app.py) |
| (b) Vídeo de demonstração | `video/` (roteiro em [`video/ROTEIRO_VIDEO.md`](video/ROTEIRO_VIDEO.md)) |
| (c) Relatório técnico breve | [`relatorio/RELATORIO_TECNICO_VCIA.md`](relatorio/RELATORIO_TECNICO_VCIA.md) |

## Pastas
| Pasta | Conteúdo |
|---|---|
| `notebook/` | preparação dos dados, treino, avaliação, interferências, desempenho, nitidez, Grad-CAM; `preliminar/` = inspeção da base |
| `modelo/` | `efficientnet_b0.pt`, o modelo do app (15,7 MB). O MobileNetV3-Large (comparação) não está no repositório; ele é retreinado pelo passo 2 |
| `app/` | app Gradio "FOMEZERO · VCIA — Triagem visual antes do cadastro" (abas Imagem e Sequência; endpoint `/triagem`) e 13 fotos de exemplo |
| `contrato/` | `respostas_SIMULADO.json` (CT-08, opção T3) e o script que o gera |
| `evidencias/` | divisão, métricas, desempenho, interferências, nitidez, Grad-CAM (JSON e figuras) |
| `prints/` | capturas de tela do app |
| `video/` | vídeo da bancada (sequência) e vídeo de demonstração |
| `docs/` | rastreabilidade dos requisitos, contrato CT-08, guia de integração com a FEMD, fontes e licenças, decisões. São cópias dos documentos de trabalho; os caminhos citados neles seguem a pasta do projeto (ex.: `05_ENTREGAVEIS/VCIA/evidencias/` = `evidencias/` aqui) |

## Como executar (Windows, Python 3.13; só ferramentas gratuitas)
```
python -m venv .venv
.venv\Scripts\pip install torch torchvision --index-url https://download.pytorch.org/whl/cu130
.venv\Scripts\pip install scikit-learn gradio opencv-python-headless matplotlib
```
**Só o app** (usa `modelo/efficientnet_b0.pt` e os JSON de `evidencias/`; não precisa da base):
```
.venv\Scripts\python app\app.py
```
Abre em http://127.0.0.1:7860. Com `--share`, gera um link público temporário do Gradio. Sem GPU, roda na CPU (cerca de 44 ms por imagem).

**Refazer tudo:** baixe a AgriFreshNET (DOI abaixo) e extraia `Processed Data`. Dentro de `notebook/`, rode nesta ordem (`D` = pasta `Processed Data`, `E` = `../evidencias`, `M` = `../modelo`):
| # | Comando | Gera |
|---|---|---|
| 1 | `python 01_preparar_dados.py D E` | divisão por grupo de origem sem vazamento (`divisao*.{json,csv}`) |
| 2 | `python 02_treinar.py --modelo efficientnet_b0 --dados D --divisao E --saida M` (repetir com `mobilenet_v3_large`) | pesos `M/*.pt`, `treino_*.json` |
| 3 | `python 03_avaliar.py --modelo efficientnet_b0 --dados D --divisao E --pesos M/efficientnet_b0.pt` | métricas do teste, τ, matrizes, galeria |
| 4 | `python 04_interferencias.py …` (mesmos argumentos do passo 3) | interferências sintéticas |
| 5 | `python 05_desempenho.py … --video ../video/bancada_sequencia_efficientnet_b0.mp4` (`--so_video` refaz só o vídeo) | latência, FPS, hardware, vídeo da sequência |
| 6 | `python 06_nitidez.py …` | limiar de nitidez (validação) e efeito no teste |
| 7 | `python 07_gradcam.py …` | Grad-CAM de acertos e erros (qualitativo) |
| 8 | `python ../app/app.py` | app |
| 9 | `python ../contrato/gerar_respostas_simulado.py` | `respostas_SIMULADO.json` (CT-08, T3) |

## Fontes e licenças
- **Base:** AgriFreshNET Freshness and Shelf-Life Image Dataset — Risdin, F.; Salauddin, H.; Tufa, T. A.; Hossain, M. J. (2026). Mendeley Data, v1. DOI 10.17632/42m5tb7yv9.1. **CC BY 4.0**. As fotos em `app/exemplos/` e nas figuras são dessa base (atribuição em `app/exemplos/LEIAME.md`). A base em si não está no repositório.
- **Modelos e bibliotecas:**
  - pesos ImageNet da torchvision (EfficientNet-B0, MobileNetV3-Large), que podem ter termos próprios (uso acadêmico);
  - PyTorch (licença estilo BSD), torchvision e scikit-learn (BSD-3-Clause), Gradio e OpenCV (Apache-2.0);
  - NumPy, Pillow e Matplotlib.
  - Lista completa em [`docs/FONTES.md`](docs/FONTES.md).
