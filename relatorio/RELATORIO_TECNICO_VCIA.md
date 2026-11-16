# Relatório técnico breve — Visão Computacional (VCIA)

**FOMEZERO · Protótipo Integrado CitizenTech com IA para Apoiar o Cidadão**
FIAP · Global Solution 2026.2 · Tecnólogo em IA · turma 2TIAPR-2026
Integrantes: Erick Miguel (RM 564896) · Leonardo Melo (RM 567097) · Luna Oliveira (RM 564215)

**Nicho [§1.b, interesse social]: Triagem visual de hortifrúti excedente antes do cadastro do lote de doação**

> **Apoio à triagem visual. A imagem não atesta que o alimento é seguro para consumo; a decisão é do doador e da vigilância sanitária.**

Versão: 2026-11-16 · Todas as métricas indicam o conjunto e o tamanho da amostra (n). Caminhos relativos à raiz do repositório (`05_ENTREGAVEIS/VCIA/` no projeto de trabalho). Os documentos de apoio citados com `02_MATERIA_VCIA/`, `03_INTEGRACAO/` ou `04_REFERENCIAS/` estão em `docs/`.

---

## 1. Problema, nicho e papel no FOMEZERO

O FOMEZERO conecta doadores de alimentos excedentes a beneficiários por meio do **lote de doação**. Na tela de cadastro, o doador descreve o estado do alimento no campo de texto livre **"Condição informada pelo doador"** (`condicao_informada`). O módulo de visão computacional ajuda nesse momento. O doador fotografa **um item de hortifrúti por vez, de cima, sobre fundo claro**, e o modelo **sugere** a condição visual. O texto da sugestão pré-preenche o campo, e o doador pode editá-lo.

| Classe sugerida | Origem na base |
|---|---|
| "sem sinais visuais de deterioração" | Fresh |
| "sinais visuais leves — priorizar uso rápido e avaliar pessoalmente" | Semi-Fresh |
| "sinais visuais de deterioração — sugestão: compostagem" | Rotten |
| "inconclusivo — avaliar pessoalmente" | confiança abaixo do limiar τ **ou** foto borrada (§5) |

O módulo também mostra o **produto reconhecido**, um dos 8 da base: banana, melão-de-são-caetano, pepino, berinjela, laranja, mamão, abacaxi e tomate. Quando o produto reconhecido está errado, o doador percebe que a sugestão não vale para aquela foto.

**Salvaguardas** (decisão DEC-023 do grupo):
- O texto é sempre "Sugestão da triagem visual (confiança X%): <classe>" e nunca "confirmado".
- Nada é barrado.
- A classe de deterioração e o "inconclusivo" pedem confirmação humana.
- Nenhum campo novo é criado no lote.
- Ficam fora do escopo: pratos prontos, carnes e caixas com vários itens.

**Releitura do enunciado `[HIPÓTESE]`:**
- [§1.c] pede "sinalizar possíveis necessidades de intervenção ou inspeção". Aqui, a **inspeção** é a avaliação humana do doador ou da ONG antes do cadastro, pedida nas classes 2, 3 e no inconclusivo. A **intervenção** é a sugestão de compostagem.
- [§5.b] fala em "otimizar rotas de inspeção das equipes municipais". Lemos isso como **priorizar o que precisa ser olhado** pela pessoa responsável.
- Essa releitura e a aceitação do nicho de interesse social (P-VCIA-14) estão em consulta ao professor.
- Coerente com [§5.b], a saída não substitui a avaliação presencial nem atesta risco.

## 2. Dados

**Base: AgriFreshNET Freshness and Shelf-Life Image Dataset**
- Autores: Risdin, Salauddin, Tufa e Hossain, 2026. Mendeley Data, v1, DOI 10.17632/42m5tb7yv9.1.
- Licença: **CC BY 4.0**.
- Foi escolhida entre 4 bases abertas por ser a única com **três estágios** compatíveis com as três classes. O comparativo está em `02_MATERIA_VCIA/PESQUISA_BASES.md`.

**Inspeção da base** [§2.1, REQ-VCIA-08] (`evidencias/inspecao_*`, `mosaico_*`):
- O arquivo baixado é o `Processed Data.zip`, com SHA-256 igual ao publicado.
- São 14.160 arquivos JPEG de 512×512 em 24 pastas (8 produtos × 3 estágios).
- A base já vem com **aumento de dados embutido**: cada pasta foi completada até 590 arquivos com cópias `aug_<n>_<original>`. Isso dá **5.217 originais** e **8.943 aumentadas**.
- O cenário é sempre um item por foto, visto de cima, sobre pano claro.
- O nome de cada pasta traz uma faixa de vida útil (ex.: "Fresh Banana(1-4)"). Essa faixa **não** é usada como afirmação sobre validade.

**Tratamentos:**
1. **Exclusão por rótulo conflitante:** 34 fotos originais (68 arquivos, com as `aug_`) aparecem idênticas em dois estágios (dHash com distância 0) e foram excluídas. A conferência visual está em `evidencias/conferencia_pares_conflitantes_dist0_e_dist2.jpg`. Os pares com distância 2 eram fotos diferentes e ficaram na base (DEC-008).
2. **Divisão sem vazamento** [§2.1, REQ-VCIA-10/11]:
   - Cada foto pertence a um **grupo de origem**. O grupo é a sessão de captura (data e hora até o minuto no nome do arquivo) ou, sem isso, o nome da original sem o prefixo `aug_<n>_`. Fotos idênticas ficam no mesmo grupo.
   - A divisão usa `StratifiedGroupKFold` (20 dobras, semente 42), estratificada por produto × estágio: 3 dobras para o teste, 3 para a validação e 14 para o treino.
   - **Validação e teste usam só originais.** As `aug_` entram só no treino, e só as dos grupos de treino.
   - O script confere e grava: **0 grupos e 0 originais compartilhados** entre os conjuntos (`evidencias/divisao.json`).

| Conjunto | Grupos | Originais | Arquivos | Fresh / Semi-Fresh / Rotten (originais) |
|---|---|---|---|---|
| Treino | 1.125 | 3.615 | 9.788 (6.173 `aug_`) | 1.371 / 1.114 / 1.130 |
| Validação | 244 | 782 | 782 | 281 / 288 / 213 |
| Teste | 247 | 786 | 786 | 265 / 241 / 280 |

**Amostra representativa** [REQ-VCIA-15]: usamos todas as originais válidas. O treino completo levou de 4,5 a 6 minutos por modelo na GPU (274 s e 355 s), então não foi preciso subamostrar.

## 3. Arquitetura e treinamento (justificativa)

**Uma CNN com 24 saídas (produto × estágio).**
- A **condição** é a soma das probabilidades de cada estágio sobre os 8 produtos. O **produto** é a soma de cada produto sobre os 3 estágios.
- Um único modelo entrega as duas informações que a tela precisa, sem treinar dois modelos.
- Separar por produto ajuda porque "sinal leve" é visualmente diferente numa banana e num tomate.

**Transferência de aprendizado** [§2.2, REQ-VCIA-14/16]: comparamos duas CNNs leves pré-treinadas no ImageNet (torchvision). Em ambas, a última camada foi trocada por uma de 24 saídas e todas as camadas foram ajustadas.

| | EfficientNet-B0 (`IMAGENET1K_V1`) | MobileNetV3-Large (`IMAGENET1K_V2`) |
|---|---|---|
| Parâmetros (modelo original) | 5,29 M | 5,48 M |
| Por que entrou | bom equilíbrio entre acurácia e custo; modelo principal | pensada para celular e CPU; serve de comparação de velocidade |
| Melhor época (critério: F1 macro da condição na validação) | 4 de 7 (parada antecipada) — F1 val 0,944 | 3 de 6 — F1 val 0,935 |
| Tempo total de treino (RTX 3050) | 355 s | 274 s |

**Configuração comum** (`notebook/02_treinar.py`):
- otimizador AdamW (lr 3e-4, decaimento de pesos 1e-4) com taxa de aprendizado em cosseno;
- suavização de rótulo 0,1, para reduzir o excesso de confiança diante do ruído de rótulo;
- precisão mista na GPU e lote 32;
- até 10 épocas, com paciência 3.

## 4. Pré-processamento (justificativa) [§2.1, §2.5]

- **Redimensionar 512→224 e normalizar com a média e o desvio do ImageNet.** É o formato em que os pesos foram pré-treinados. Também reduz em cerca de 5× o número de pixels, o que baixa a latência.
- **Aumento leve só no treino:** recorte aleatório (70–100% da área), espelhamento, rotação de ±15° e variação de brilho e contraste de ±20%. Ele compensa a pouca variedade de fundo e de luz da base, sem mudar a cor do alimento (saturação só ±10%), já que a cor é pista de deterioração.
- **Validação e teste sem aumento**, para medir o modelo na foto como ela é.

## 5. Limiar de confiança e salvaguarda de nitidez (justificativa) [§2.5]

**Limiar τ do "inconclusivo".**
- Regra fixada antes de olhar o teste: o menor τ, aplicado à maior probabilidade de condição, que dê **acurácia ≥ 95% nas sugestões aceitas** com **cobertura ≥ 70%**.
- A calibração foi feita **só na validação** (n = 782). A curva está em `evidencias/curva_tau_*.png`.

| Modelo | τ | Validação: cobertura / acurácia nas aceitas | Teste (n = 786): cobertura / acurácia nas aceitas |
|---|---|---|---|
| EfficientNet-B0 | **0,50** | 99,1% / 95,1% | 98,98% (778) / 94,47% |
| MobileNetV3-Large | 0,56 | 95,8% / 95,1% | 97,96% (770) / 93,90% |

O τ é baixo porque o modelo raramente fica em dúvida. Como os erros também vêm com confiança alta (§8), **o τ sozinho não protege**. Por isso existe a segunda salvaguarda.

**Salvaguarda de nitidez** (DEC-010, trabalho extra aprovado; `notebook/06_nitidez.py`).
- O que mede: a variância do laplaciano dividida pelo brilho médio ao quadrado, na foto em tons de cinza de 224×224.
- Limiar: o percentil 2 das originais da **validação** (0,000945).
- Escolha da medida: comparamos 4 variantes, também só na validação (`evidencias/nitidez_variantes_validacao.json`). A versão sem normalizar recusava 18,9% das fotos escurecidas, e a que divide pela variância recusava 19,8% das fotos com sombra. A variante escolhida recusa 0,4% e 1,5%, respectivamente.
- Abaixo do limiar, a resposta vira "inconclusivo" e o app pede outra foto.
- Custo: 1,05 ms por foto na CPU, em média (n = 100; p50 0,95 ms; p95 1,66 ms; `evidencias/tempo_nitidez.json`).

## 6. Métricas de desempenho [§2.3, REQ-VCIA-17 a 20]

**Condição** (teste, n = 786, só originais; sem limiar; `evidencias/metricas_teste_*.json`):

| Classe (n) | EfficientNet-B0: precisão / recall / F1 | MobileNetV3-Large: precisão / recall / F1 |
|---|---|---|
| Fresh (265) | 0,931 / 0,966 / 0,948 | 0,893 / 0,977 / 0,933 |
| Semi-Fresh (241) | 0,915 / 0,892 / 0,903 | 0,921 / 0,867 / 0,893 |
| Rotten (280) | 0,975 / 0,961 / 0,968 | 0,996 / 0,957 / 0,976 |
| **Macro** | **0,940 / 0,940 / 0,940** | 0,937 / 0,934 / 0,934 |
| Acurácia | 94,2% (740/786) | 93,6% (736/786) |

**Matriz de confusão da condição — EfficientNet-B0** (linhas = verdadeiro, colunas = previsto; `evidencias/matriz_condicao_efficientnet_b0.png`):

| | Fresh | Semi-Fresh | Rotten |
|---|---|---|---|
| **Fresh** (265) | **256** | 9 | 0 |
| **Semi-Fresh** (241) | 19 | **215** | 7 |
| **Rotten** (280) | 0 | 11 | **269** |

**Nenhum item "Rotten" foi sugerido como "sem sinais visuais de deterioração"**, e nenhum "Fresh" como deterioração, nos dois modelos (n = 786 no teste original).

**Produto** (teste, n = 786):
- EfficientNet-B0: F1 macro 0,993. São 4 erros: 2 mamões vistos como pepino, 1 mamão como laranja e 1 melão-de-são-caetano como berinjela (`matriz_produto_*.png`).
- MobileNetV3-Large: acertou o produto nas 786 fotos do teste. Isso vale para este teste, nesta base de fundo claro, e não deve ser lido como garantia fora dela.

**Acurácia da condição por produto — EfficientNet-B0** (teste):

| Produto | Acurácia |
|---|---|
| laranja | 112/112 |
| abacaxi | 81/81 |
| pepino | 37/37 |
| banana | 98,0% (n = 102) |
| tomate | 94,6% (n = 167) |
| melão-de-são-caetano | 90,9% (n = 77) |
| mamão | 87,3% (n = 110) |
| berinjela | 86,0% (n = 100) |

O pepino tem a menor amostra de teste, por isso o resultado dele merece cautela.

## 7. Latência, FPS e equipamento [§2.5, REQ-VCIA-31 a 34]

**Equipamento** (`evidencias/desempenho_*.json`):
- notebook com Intel Core i5-13420H (12 núcleos lógicos), 15,7 GB de RAM e NVIDIA GeForce RTX 3050 6 GB Laptop (driver 621.01);
- Windows 11 (10.0.26200), Python 3.13.5, PyTorch 2.14.1+cu130 (CUDA 13.0), torchvision 0.29.1, OpenCV 5.0.0;
- ligado na tomada; outros programas abertos podem variar os tempos.

**Como medimos:**
- imagem de entrada da base em 512×512, entrada do modelo em 224×224;
- lote de 1 imagem, precisão FP32;
- 20 execuções de aquecimento antes de medir, com `cuda.synchronize` na GPU;
- n = 200 imagens na GPU e n = 100 na CPU.

| Modelo | Dispositivo | Pré-processamento (ms) | Inferência média (p50 / p95), ms | Total por imagem (ms) | FPS equivalente |
|---|---|---|---|---|---|
| EfficientNet-B0 | GPU | 5,11 | **17,13** (16,98 / 19,17) | 22,24 | 45,0 |
| EfficientNet-B0 | CPU | 4,71 | **44,08** (43,79 / 46,44) | 48,79 | 20,5 |
| MobileNetV3-L | GPU | 5,09 | 13,50 (13,46 / 14,48) | 18,59 | 53,8 |
| MobileNetV3-L | CPU | 4,84 | 30,06 (30,02 / 37,39) | 34,90 | 28,7 |

**Processamento contínuo** [§2.4, REQ-VCIA-30]: simulamos a **bancada de doação** com uma sequência de 40 fotos do teste, de vários produtos (`notebook/05_desempenho.py`).
- A medição de ponta a ponta (ler a foto, pré-processar, inferir e desenhar o rótulo) usou 37 quadros, depois do aquecimento.
- EfficientNet-B0: **24,6 ms por quadro = 40,7 FPS** na GPU. MobileNetV3-L: 19,2 ms = 52,0 FPS.
- O vídeo `video/bancada_sequencia_efficientnet_b0.mp4` mostra cada quadro com o nicho, a sugestão, a confiança, o produto e o aviso fixo. Ele é exibido a 1 quadro por segundo para dar tempo de leitura.
- Depois da revisão dos rótulos (§10), o vídeo foi regravado com texto acentuado e completo e com a salvaguarda de nitidez. Na regravação, a sequência ficou em 46,9 ms por quadro = 21,3 FPS (`evidencias/sequencia_video_efficientnet_b0.json`). A queda vem do desenho da faixa com fonte TrueType, não do modelo.
- O valor de 40,7 FPS acima mede o fluxo com uma faixa simples, mais próxima do processamento real.
- No app, a aba "Sequência" processou as 13 fotos de exemplo a 16 ms por foto = 64,3 FPS (GPU; `prints/02_app_sequencia_tabela.jpg`). É a medição do próprio app e variou entre 37 e 71 FPS nas execuções de 16/11. Abaixo da galeria, uma tabela mostra o texto completo de cada sugestão, porque a galeria corta legendas longas.
- A verificação de nitidez acrescenta cerca de 1 ms por foto, medido na CPU. Os tempos da tabela foram medidos antes de ela existir.

## 8. Qualidade × velocidade: escolha do modelo [§2.5, REQ-VCIA-35/38]

| Critério | EfficientNet-B0 | MobileNetV3-Large |
|---|---|---|
| F1 macro da condição (teste, n = 786) | **0,940** | 0,934 |
| Recall de Semi-Fresh (o estágio que pede atenção) | **0,892** | 0,867 |
| Semi-Fresh sugerido como "sem sinais" | **19** | 31 |
| Inferência GPU / CPU | 17,1 / 44,1 ms | **13,5 / 30,1 ms** |
| F1 com foto desfocada / "Rotten" → "sem sinais" | **0,852 / 35** | 0,785 / 53 |
| F1 com 25% obstruído / "Rotten" → "sem sinais" | 0,722 / 25 | **0,739 / 15** |

**Escolha: EfficientNet-B0** (DEC-009).
- Para o doador, o erro que mais pesa é um item com sinais de deterioração sair como "sem sinais". A EfficientNet-B0 comete menos esse erro com Semi-Fresh (19 contra 31) e com fotos desfocadas.
- As duas atendem com folga a um uso interativo (uma foto por vez): mais de 20 FPS até na CPU.
- A MobileNetV3-Large fica registrada como alternativa para rodar só em CPU, por exemplo num servidor sem GPU. A diferença de qualidade entre elas é pequena.

## 9. Análise detalhada dos erros [§2.3, REQ-VCIA-24/25/51]

**9.1 Onde o modelo erra** (EfficientNet-B0, teste, 46 erros em 786):
- **Todos** os erros são entre **estágios vizinhos**. O maior grupo é Semi-Fresh → Fresh: 19 erros, 41% do total. Depois vêm Rotten → Semi-Fresh (11), Fresh → Semi-Fresh (9) e Semi-Fresh → Rotten (7).
- Os produtos mais difíceis são a berinjela (86,0%) e o mamão (87,3%). Laranja, abacaxi e pepino não tiveram erro de condição.
- O limiar τ separou 8 fotos como inconclusivas (7 Semi-Fresh e 1 Rotten). Ele pega poucos erros porque **os erros vêm com confiança alta**: os 8 erros de maior confiança ficaram entre 78% e 98% (`evidencias/gradcam_efficientnet_b0.json`).

**9.2 Exemplos práticos** (`evidencias/galeria_acertos_erros_efficientnet_b0.png` e Grad-CAM em `evidencias/gradcam_efficientnet_b0.png`):
- **O que o Grad-CAM mostra:** em todos os 11 exemplos (3 acertos e 8 erros), a região que pesou na decisão é o **próprio item**, e não o pano do fundo nem a borda da foto. Não aparece sinal de "atalho" pelo fundo. Isso é uma leitura qualitativa, não uma prova.
- **Acertos de alta confiança:** laranja "Fresh" (99%), pepino "Semi-Fresh" (99%) e banana "Rotten" (99%), esta com a casca escura e o mapa concentrado nas manchas.
- **Erros de tomate Semi-Fresh → Fresh** (98% e 98%): os tomates não mostram mancha visível na foto. A pasta da base se chama "Semi fresh Tomato(10-24)" (faixa de dias).
- **Erros de berinjela, nos dois sentidos** (Fresh → Semi-Fresh, 97% e 89%; Rotten → Semi-Fresh, 94% e 92%): a aparência de casca mais clara ou levemente manchada aparece nos três estágios.
- **Erro de banana Semi-Fresh → Rotten** (83%): a casca está muito escurecida na foto.

`[HIPÓTESE]` Parte desses erros vem de **rótulos atribuídos por tempo de armazenamento** (os dias no nome da pasta), e não por sinais visíveis. Nesse caso, a foto não tem a informação que separa os estágios. A inspeção de 15/11 já tinha encontrado pepinos "Rotten" com aparência íntegra. Isso é coerente com a decisão de chamar a classe 2 de "sinais visuais leves — priorizar uso rápido e **avaliar pessoalmente**" e de nunca tirar conclusões sobre validade.

**9.3 Interferências** [§2.3]. A base não tem sombras fortes, variação severa de luz nem obstruções reais. Por isso aplicamos **perturbações sintéticas controladas** às 786 fotos do teste, com semente fixa por imagem (`notebook/04_interferencias.py`). Esses resultados ficam **fora das métricas oficiais**.

| Perturbação | F1 macro EffNet-B0 (Δ) | "Rotten" → "sem sinais" (todas / acima do τ) | Recusadas pela nitidez | "Rotten" → "sem sinais" com a nitidez |
|---|---|---|---|---|
| Original | 0,940 | 0 / 0 | 9 | 0 |
| Escurecer (brilho ×0,6) | 0,934 (−0,6 p.p.) | 0 / 0 | 6 | 0 |
| Clarear (brilho ×1,4) | 0,920 (−1,9 p.p.) | 1 / 0 | 22 | 0 |
| Sombra sintética (metade da foto 50% mais escura) | 0,924 (−1,6 p.p.) | 0 / 0 | 11 | 0 |
| Obstrução parcial (25% da área coberta) | 0,722 (−21,8 p.p.) | 25 / 11 | 4 | **11** |
| Desfoque gaussiano (raio 3) | 0,852 (−8,8 p.p.) | 35 / 29 | 709 | **0** |

O que a tabela mostra:
- **Luz e sombra afetam pouco**, menos de 2 pontos de F1. O aumento de brilho e contraste no treino provavelmente contribui.
- **O desfoque é o caso perigoso:** sem nenhuma proteção, 29 itens "Rotten" passariam do τ como "sem sinais". Com a salvaguarda de nitidez, nenhum passa. Em troca, a foto borrada recebe "inconclusivo" e um pedido de nova foto.
- No teste original, a salvaguarda recusa 9 fotos nítidas (4 Fresh e 5 Semi-Fresh), e a cobertura cai de 98,98% para 97,84%.
- **A obstrução parcial continua sem defesa:** 11 de 280 itens "Rotten" com 25% da área coberta ainda saem como "sem sinais". É a principal limitação técnica (§11). A tela mitiga isso pedindo "um item por vez, de cima, sobre fundo claro", e a sugestão sempre passa pelo doador.
- **Texturas complexas** (fundos estampados, bancadas) não foram testadas: a base só tem pano liso e não criamos perturbação para isso.

**9.4 Fora do domínio.** Pratos prontos, carnes, caixas com vários itens e produtos fora dos 8 da base recebem uma resposta mesmo assim, e o modelo pode errar com confiança alta. Nem o τ nem a nitidez detectam isso. Por isso a tela lista os 8 produtos e mostra o produto reconhecido. Não fizemos teste com fotos próprias; se houver, ficará marcado e fora das métricas.

## 10. Integração ao CitizenTech e escolhas de engenharia [§2.4, §5.a]

**App "FOMEZERO · VCIA — Triagem visual antes do cadastro"** (Gradio, `app/app.py`):
- **Aba Imagem:** mostra a sugestão, o produto, a confiança, o gráfico de probabilidades e o texto editável para "Condição informada pelo doador", sempre com o aviso fixo. No "inconclusivo", o gráfico some, para que a classe mais provável não pareça uma sugestão.
- **Aba Sequência:** processa a bancada de fotos e mede o FPS.
- **Endpoint `/triagem`:** devolve o JSON do contrato.
- Prints: `prints/` (refeitos depois da revisão dos rótulos de 16/11; os anteriores estão arquivados).
- **Revisão dos rótulos** (16/11, antes do vídeo):
  - Conferência automática dos 13 exemplos: classe igual ao texto fixo, formato da sugestão, aviso idêntico, pedido de confirmação humana e ausência de palavras proibidas.
  - Correções na tela: o cartão passou a dizer "Sugestão da triagem visual"; a legenda da sequência indica "foto borrada"; a sequência ganhou uma tabela com o texto completo de cada sugestão; os números usam vírgula decimal.
  - Correções no vídeo: o texto de Semi-Fresh era cortado; acentos, nicho completo e aviso idêntico foram restaurados.

**Contrato CT-08 (VCIA → interface FEMD do grupo):**
- esquema `fomezero.vcia.v1`, versão `ct08-v1` (`03_INTEGRACAO/CONTRATOS.md`);
- três formas de ligar: iframe do app (T2), chamada ao endpoint com `@gradio/client` (T1), ou um arquivo `respostas_SIMULADO.json` com respostas reais gravadas, exibido com a faixa "SIMULADO" (T3, funciona sem servidor);
- a interface só pré-preenche `condicao_informada`, sem campo novo no lote.

**Escolhas de engenharia de software:**
- **Scripts numerados e comentados** (01 preparar → 07 Grad-CAM), em vez de um notebook único: são fáceis de rodar e revisar.
- **`comum.py` como fonte única** das classes, dos textos de tela, do pré-processamento e do aviso. O treino, a avaliação, o vídeo e o app não podem divergir.
- **Evidências em JSON** geradas pelos próprios scripts. Nenhum número deste relatório foi digitado à mão sem um arquivo de origem.
- **Sementes fixas e verificação automática** de vazamento.
- **Limiares lidos dos arquivos de calibração:** o app nunca usa número fixo no código.
- **Pesos fora do repositório:** os arquivos `.pt` estão no `.gitignore`.
- **Só ferramentas gratuitas.**

## 11. Limitações

1. **Uma só base**, coletada por outra equipe, com um só cenário (pano claro, item isolado). O desempenho em fotos reais de doadores do FOMEZERO **não foi medido**.
2. **Ruído de rótulo** provável entre estágios vizinhos (§9.2). As métricas medem a concordância com o rótulo da base, que nem sempre é visível.
3. **Erros confiantes:** o τ quase não filtra. A proteção do fluxo vem da revisão humana obrigatória, não do modelo.
4. **Obstrução parcial** sem defesa automática (11/280 "Rotten" → "sem sinais" no teste sintético).
5. **Perturbações sintéticas** aproximam, mas não reproduzem, as sombras e obstruções reais.
6. **O link Gradio é temporário:** não há hospedagem permanente. A integração com a FEMD depende da escolha da equipe (T1, T2 ou T3).
7. A imagem não informa validade, vida útil nem condições sanitárias. A faixa de dias da base não é convertida em afirmação.

## 12. Reprodutibilidade e fontes

- **Execução:** a ordem dos comandos está em `README.md`, na seção "Como executar". Base em `dados_brutos/`, fora do git. Pesos em `modelo/`, fora do git.
- **Evidências:** `evidencias/` (`divisao.json`, `treino_*.json`, `metricas_teste_*.json`, `desempenho_*.json`, `interferencias_*.json`, `nitidez_*.json`, `gradcam_*.json` e figuras).
- **Fontes e licenças** (`04_REFERENCIAS/FONTES.md`):
  - AgriFreshNET (CC BY 4.0);
  - pesos EfficientNet-B0 e MobileNetV3-Large da torchvision, cuja nota diz que os pesos podem ter termos próprios (uso acadêmico);
  - PyTorch (BSD de 3 cláusulas), torchvision e scikit-learn (BSD-3-Clause), Gradio e OpenCV (Apache-2.0), NumPy, Pillow e Matplotlib.
- **Grad-CAM:** Selvaraju, R. R.; Cogswell, M.; Das, A.; Vedantam, R.; Parikh, D.; Batra, D. "Grad-CAM: Visual Explanations from Deep Networks via Gradient-based Localization". arXiv:1610.02391 (v4). A versão final saiu no IJCV (2019), e uma versão anterior no ICCV 2017. Implementação própria, em `notebook/07_gradcam.py`.

> **Apoio à triagem visual. A imagem não atesta que o alimento é seguro para consumo; a decisão é do doador e da vigilância sanitária.**
