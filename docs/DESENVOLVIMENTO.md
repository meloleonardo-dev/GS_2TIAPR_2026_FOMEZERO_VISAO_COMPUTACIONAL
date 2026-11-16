# DESENVOLVIMENTO — VCIA (FOMEZERO · triagem visual de hortifrúti)

> Arquitetura, decisões locais de implementação e diário. O nicho, as classes e as salvaguardas vêm da **DEC-023 do CENTRAL** (adotada na DEC-006 local). A versão anterior (nicho 2) está em `06_ARQUIVO/2026-11-16_DESENVOLVIMENTO_pre_DEC-023.md`.

## 1. Nicho (fixo) [§1.b] — REQ-VCIA-03, 58
**"Triagem visual de hortifrúti excedente antes do cadastro do lote de doação"** — nicho de interesse social proposto pela equipe. Aparece igual no título da tela, no README, no notebook/scripts e no relatório.
Fora do escopo: pratos prontos, carnes, caixas com vários itens.

## 2. Design (proposta para o checkpoint de 16/11)
| Item | Decisão proposta | Justificativa (qualidade × velocidade × prazo) | REQs |
|---|---|---|---|
| (a) Tarefa | **Classificação** de imagem [§2.2] | DEC-023; uma foto = um item; métricas de classificação [§2.3] | 12, 17–20, 27 |
| (b) Base | **AgriFreshNET** (F-010, CC BY 4.0), já inspecionada | única com 3 estágios; origem rastreável; ver `PESQUISA_BASES.md` | 59, 08 |
| (c1) Saída do modelo | **Uma cabeça de 24 classes** (produto × estágio). Condição = soma das probabilidades por estágio; produto = soma por produto | um só modelo dá as duas saídas exigidas pela DEC-023 (condição e produto) sem treinar dois modelos | 27, 29 |
| (c2) Arquitetura | **EfficientNet-B0** pré-treinada no ImageNet (torchvision), ajuste fino de todas as camadas; **comparação com MobileNetV3-Large** (mais leve) para a análise qualidade × velocidade | arquiteturas leves treinam em minutos numa GPU de 6 GB; a comparação dá base real ao §2.5 | 14, 16, 35, 38 |
| (c3) Pré-processamento | redimensionar para **224×224**, normalização ImageNet (média/desvio); treino com flip horizontal, rotação ±15°, variação de brilho/contraste; as `aug_` da base só no treino | o padrão dos pesos pré-treinados; aumento leve compensa a pouca variedade de fundo | 09, 36 |
| (c4) Limiar | **τ sobre a maior probabilidade de condição**; abaixo de τ → "inconclusivo — avaliar pessoalmente". τ escolhido na **validação** pela curva cobertura × acurácia (registrar a curva e o ponto escolhido) | calibra o "inconclusivo" sem olhar o teste; o relatório diz que τ **não** protege contra fotos fora do domínio | 37, 38 |
| (c5) Divisão | por **grupo de origem** (sessão por minuto; senão nome original sem `aug_<n>_`), `StratifiedGroupKFold` estratificado por produto×estágio, **70/15/15**; validação e teste **só originais**; as 16 fotos conflitantes excluídas | atende [§2.1] de forma verificável (script mostra 0 grupos compartilhados entre conjuntos) | 10, 11, 15 |
| (c6) Hardware | **local**: Python 3.13 em `.venv` (fora do git), PyTorch com CUDA, RTX 3050 6 GB Laptop (driver 621.01), i5-13420H, 15,7 GB RAM. Reserva: Colab T4 gratuito | gratuito; latência/FPS medidos no mesmo equipamento, em GPU e em CPU | 31–34 |
| (c7) Interferências | no **teste**: perturbações sintéticas controladas (brilho −40/+40%, sombra sintética, oclusão parcial de 25%, desfoque); + fotos próprias **identificadas** (fora das métricas oficiais) | a base não tem sombra/obstrução reais; mede o efeito de cada interferência do §2.3 | 24, 25, 51 |
| (c8) Sequência/vídeo | sequência de N fotos de teste (vários produtos) simulando a **bancada** do doador; gera um vídeo MP4 com rótulo, produto e confiança sobrepostos; mede latência média e FPS | atende [§2.4]/[§4.b] sem precisar de câmera | 30, 46, 55 |
| (d) Onde vive | **App Gradio próprio** "FOMEZERO · VCIA — Triagem visual antes do cadastro" (aba Imagem, aba Sequência, endpoint `/triagem`) + **CT-08** para a FEMD: T2 (iframe do link Gradio) preferencial, T1 (`@gradio/client`) opcional, **T3** (`respostas_SIMULADO.json`, com faixa "SIMULADO") sempre entregue | o link Gradio é temporário; T3 garante a tela na FEMD sem servidor | 01, 26, 54 |
| (e) Resultado visual | rótulo, produto, barra de confiança, aviso fixo e texto sugerido para `condicao_informada`; **Grad-CAM** opcional (se sobrar tempo no dia 17) | [§1.c] pede resultado visual; Grad-CAM mostra onde o modelo olhou | 05, 06 |
| (f) Entrega de código | scripts Python **comentados e numerados** em `05_ENTREGAVEIS/VCIA/notebook/` (`01_preparar_dados.py`, `02_treinar.py`, `03_avaliar.py`, `04_interferencias.py`, `05_desempenho.py`) + `app/app.py`; README com como rodar | "notebook **ou** código executável" [§4.a]; scripts são mais fáceis de rodar e revisar | 40–43, 60, 61 |

Dependências gratuitas (a registrar em FONTES com licença ao instalar): PyTorch/torchvision, scikit-learn, Pillow, OpenCV (vídeo), Gradio.

## 3. Termos da VCIA (fixos)
| Termo | Definição |
|---|---|
| triagem visual | avaliação da **aparência** do item na foto; não é avaliação sanitária |
| sugestão | saída do modelo; o doador confirma ou edita |
| confiança | probabilidade do modelo para a classe exibida (0–100%); não é probabilidade de segurança |
| inconclusivo | confiança abaixo de τ → "inconclusivo — avaliar pessoalmente" |
Texto pré-preenchido em `condicao_informada`: **"Sugestão da triagem visual (confiança X%): <classe>"** (nunca "confirmado").

## 4. Diário
| Data | Registro |
|---|---|
| 2026-11-15 | Discovery: estrutura criada, espelho do CENTRAL com hash, 61 REQs ativos conferidos (TAR-001). |
| 2026-11-15 | TAR-002 (nicho 2) suspensa por PEN-012; 9 bases de descarte abertas (registro na versão arquivada deste arquivo). |
| 2026-11-15 | TAR-004: bases de alimentos (`PESQUISA_BASES.md`); AgriFreshNET baixada (SHA-256 conferido) e inspecionada. |
| 2026-11-16 | DEC-023 do CENTRAL registrada e sincronizada; DEC-006 local. Design proposto (§2). |
| 2026-11-16 | Development (TAR-005): divisão sem vazamento, 2 CNNs treinadas, teste n=786 (F1 macro condição 0,940 / 0,934), desempenho, interferências, app Gradio, T3. DEC-008, DEC-009. |
| 2026-11-16 | TAR-006 (EXTRA, DEC-010): salvaguarda de nitidez; desfoque r3: "Rotten" → "sem sinais" de 29 para 0 (n=786). Obstrução continua sem defesa (11). |
| 2026-11-16 | TAR-007: Grad-CAM (`evidencias/gradcam_efficientnet_b0.png`): nos 11 exemplos o mapa cobre o item, não o fundo. Os 8 erros de maior confiança (78–98%) são trocas entre estágios vizinhos (Semi→Fresh, Fresh→Semi, Rotten→Semi, Semi→Rotten); vários parecem rótulo ambíguo [HIPÓTESE, para a análise de erros do relatório]: tomates "Semi-Fresh" sem sinal visível e uma banana "Semi-Fresh" bem escurecida. Licenças do PyTorch e do scikit-learn abertas (F-023, F-027, F-028). Evidência e status dos 61 REQs preenchidos. README com ordem de execução. Mensagem do CT-08 para o Erick em `03_INTEGRACAO/MENSAGEM_CT08_ERICK.md`. |
| 2026-11-16 | TAR-008: relatório técnico breve (`05_ENTREGAVEIS/VCIA/relatorio/RELATORIO_TECNICO_VCIA.md`), conferido por script contra os JSON (métricas por classe, tabela de nitidez, nicho, aviso, caminhos). Tempo da nitidez gravado (`tempo_nitidez.json`: 1,05 ms média, n=100, CPU). Referência do Grad-CAM conferida no arXiv (F-029). |
| 2026-11-16 | TAR-009 (revisão dos rótulos antes do vídeo): a faixa do vídeo cortava o texto de Semi-Fresh em 60 caracteres e não tinha acentos (o aviso não saía idêntico). Ela passou a ser desenhada com PIL e fonte TrueType, com o nicho completo, "Sugestão da triagem visual", o aviso exato e a nitidez. Na tela: cartão com "Sugestão da triagem visual", legenda "foto borrada", vírgula decimal. Conferência automática: 13/13 exemplos sem problema. Vídeo antigo e prints antigos em `06_ARQUIVO`. |
