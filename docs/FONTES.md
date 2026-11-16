# FONTES (F-NNN)

> Só entra aqui o que foi **aberto**. Toda base de dados e todo modelo pré-treinado com licença. Data de acesso obrigatória.

| ID | Tipo | Título | Autoria | URL | Licença | Acesso | Uso / adequação |
|---|---|---|---|---|---|---|---|
| F-001 | enunciado | Enunciado VCIA v2 (texto colado) | professor(a) da VCIA, FIAP | `CENTRAL/02_DISCIPLINAS/VCIA/enunciado_original/2026-11-08_enunciado_v2_colado_pelo_usuario.md` | uso acadêmico | 2026-11-15 | contrato |
| F-002 | repositório | FomeZero_FrontEnd (FEMD) | Erick Miguel | https://github.com/lostgear84/FomeZero_FrontEnd | `[PENDENTE: conferir]` | 2026-11-15 | só leitura (rotas, README) |
| F-003 | contrato | CT-02_PROPOSTA (GENAI → FEMD) | grupo FOMEZERO (GENAI) | `GS_2TIAPR_2026_ERICK_LEO_LUNA/05_ENTREGAVEIS/GENAI/contrato/CT-02_PROPOSTA.md` | uso acadêmico | 2026-11-15 | padrão do CT-08 |

## Bases candidatas — triagem visual de alimentos (Opção C; detalhes em `02_MATERIA_VCIA/PESQUISA_BASES.md`)
| ID | Base | URL aberta | Licença | Nº de imagens | Rótulos | Cena | Origem rastreável p/ divisão? | Acesso |
|---|---|---|---|---|---|---|---|---|
| F-010 | AgriFreshNET Freshness and Shelf-Life Image Dataset — Risdin, F.; Salauddin, H.; Tufa, T. A.; Hossain, M. J. (2026), Mendeley Data, v1, DOI 10.17632/42m5tb7yv9.1 | https://data.mendeley.com/datasets/42m5tb7yv9/1 | CC BY 4.0 | 14.500 (página) / **14.160 no zip: 5.217 originais + 8.943 `aug_`** | Fresh / Semi-Fresh / Rotten × 8 produtos | um item, de cima, pano branco, 512×512 | **Sim, pelo nome** (`aug_<n>_<original>`; 1.632 grupos por sessão) | 2026-11-15 (baixado; SHA-256 conferido) |
| F-011 | Fresh and Rotten Fruits Dataset for Machine-Based Evaluation of Fruit Quality — Sultana, N.; Jahan, M.; Uddin, M. S. (2022), Mendeley Data, v1, DOI 10.17632/bdd69gyhv8.1 | https://data.mendeley.com/datasets/bdd69gyhv8/1 | CC BY 4.0 | 3.200 originais (+12.335 aumentadas) | fresh / rotten × 8 frutas | lojas e campo | Sim (originais separados) | 2026-11-15 |
| F-012 | Spoiled and fresh fruit inspection dataset — Pachon Suescun, C. G.; Pinzón Arenas, J. O.; Jiménez-Moreno, R. (2020), Mendeley Data, v1, DOI 10.17632/6ps7gtp2wg.1 | https://data.mendeley.com/datasets/6ps7gtp2wg/1 | CC BY 4.0 | 16.000 | fresh / spoiled × 8 frutas | fundos, ângulos e luz variados | risco (mesma fruta em vários ângulos) | 2026-11-15 |
| F-013 | FruitVision — Bijoy, M. H. I.; Tasnim, S. Z.; Awsaf, S. A.; Hasan, M. Z. (2025), Mendeley Data, v2, DOI 10.17632/xkbjx8959c.2 | https://data.mendeley.com/datasets/xkbjx8959c/2 | CC BY-NC-ND 4.0 | 10.154 originais (>81.000 aumentadas) | fresh / rotten / formalin-mixed × 5 frutas | não visível | Sim (originais separados) | 2026-11-15 |

## Modelos pré-treinados e bibliotecas (páginas abertas em 2026-11-16)
| ID | Item | URL aberta | Licença / nota (literal ou resumo fiel) | Uso |
|---|---|---|---|---|
| F-020 | EfficientNet-B0, pesos `EfficientNet_B0_Weights.IMAGENET1K_V1` (torchvision) | https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.efficientnet_b0.html | ImageNet acc@1 77,692; 5.288.548 parâmetros; "These weights are ported from the original paper." Licença própria dos pesos: não visível na página (ver F-024) | modelo principal |
| F-021 | MobileNetV3-Large, pesos `MobileNet_V3_Large_Weights.IMAGENET1K_V2` (torchvision) | https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.mobilenet_v3_large.html | ImageNet acc@1 75,274; 5.483.032 parâmetros; licença dos pesos não visível (ver F-024) | modelo de comparação |
| F-022 | torchvision (código) | https://github.com/pytorch/vision/blob/main/LICENSE | BSD 3-Clause License | modelos, transformações |
| F-023 | PyTorch 2.14.1 (cu130) | https://download.pytorch.org/whl/cu130 · arquivo aberto em 2026-11-16: `.venv/Lib/site-packages/torch-2.14.1+cu130.dist-info/licenses/LICENSE` | licença estilo BSD de 3 cláusulas (redistribuição com aviso de copyright; cláusula 3: proíbe usar os nomes de Facebook, Deepmind, NYU, NEC e IDIAP para promover derivados). METADATA: `Apache-2.0 AND … BSD-3-Clause AND BSL-1.0 AND MIT` (inclui componentes de terceiros) | treino e inferência |
| F-024 | Nota da torchvision sobre pesos pré-treinados | https://docs.pytorch.org/vision/stable/models.html | os modelos pré-treinados "may have their own licenses or terms and conditions derived from the dataset used for training" (uso acadêmico, sem fins comerciais) | justificativa de uso |
| F-025 | Gradio 6.32.0 | https://github.com/gradio-app/gradio/blob/main/LICENSE | Apache License, Version 2.0 | app de demonstração |
| F-026 | OpenCV 5.0.0 (opencv-python-headless) | https://github.com/opencv/opencv/blob/4.x/LICENSE | Apache License, Version 2.0 (arquivo do ramo 4.x) | vídeo da sequência |
| F-027 | scikit-learn 1.9.1 | arquivo aberto em 2026-11-16: `.venv/Lib/site-packages/scikit_learn-1.9.1.dist-info/licenses/COPYING` | "BSD 3-Clause License", Copyright (c) 2007-2026 The scikit-learn developers | divisão estratificada por grupo, métricas |
| F-029 | Grad-CAM (método) | https://arxiv.org/abs/1610.02391 (aberta em 2026-11-16) | Selvaraju, Cogswell, Das, Vedantam, Parikh, Batra. "Grad-CAM: Visual Explanations from Deep Networks via Gradient-based Localization", arXiv:1610.02391 v4; comentário da página: publicada no IJCV (2019), versão anterior no ICCV'17. Implementação própria (sem código de terceiros) | análise de erros (`07_gradcam.py`) |
| F-028 | NumPy 2.5.4 · Pillow 13.0.0 · Matplotlib 3.11.2 | METADATA/LICENSE dos pacotes no `.venv` (abertos em 2026-11-16) | NumPy: `BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0`; Pillow: `MIT-CMU`; Matplotlib: "License agreement for matplotlib versions 1.3.0 and later" (licença não exclusiva, sem royalties) | cálculo, imagens, gráficos |

## Bases abertas na pesquisa anterior (descarte irregular; suspensa por PEN-012)
Registro resumido no diário de `02_MATERIA_VCIA/DESENVOLVIMENTO.md` (2026-11-15): IWWD-Dumping Detection (MIT), prometheusCCTV, Bill, Mahimanvitha, Street trash, Project Elevate, MySpace, DATA 298 (Roboflow, CC BY 4.0) e pLitterStreet (Zenodo, CC BY 4.0).
