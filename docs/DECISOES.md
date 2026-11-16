# DECISÕES locais (DEC-NNN) — só acréscimos

> Decisões **locais** sobre como implementar a VCIA. Tema, ideia, nicho, termos e campos do lote são do CENTRAL (DEC-021, DEC-022 do CENTRAL) e não são redecididos aqui.

## DEC-001 — Estrutura AI-DLC local e espelho somente leitura do CENTRAL
- Data: 2026-11-15 · Fase: Discovery · Status: APROVADA (instrução do usuário no prompt inicial)
- Decisão: pastas 00 a 06, `CLAUDE.md` local prevalecendo sobre os superiores, espelho em `01_CENTRAL_ESPELHO/` com SHA-256 (`LEIAME.md`), cópias de `ENUNCIADO.md` (v2) e `RASTREABILIDADE.md` em `02_MATERIA_VCIA/`.
- Consequência: o espelho é atualizado só por `/sincronizar-central`.

## DEC-002 — Proteção de escrita por hook PreToolUse
- Data: 2026-11-15 · Fase: Discovery · Status: APROVADA (instrução do usuário)
- Decisão: `.claude/hooks/guarda-escrita.ps1` (UTF-8 com BOM), registrado em `.claude/settings.json` para `Write|Edit|MultiEdit|NotebookEdit`. Bloqueia pastas externas (CENTRAL, projeto PLN/GENAI/AIPA, clone da FEMD) para qualquer agente; restringe `disc-vcia` a `02_MATERIA_VCIA/` e `05_ENTREGAVEIS/VCIA/`, sem `ENUNCIADO.md`; registra em log. Escritas via PowerShell ficam fora do hook e são revisadas por data (`/checar-entrega`).
- Evidência: testes T1–T8 em `STATUS.md` (§ Teste do hook).

## DEC-003 — Conferência dos REQs sem reextração
- Data: 2026-11-15 · Fase: Discovery · Status: APROVADA (instrução do usuário)
- Decisão: os 61 REQs ativos foram conferidos por script: cada trecho entre "…" da coluna *Requisito original* precisa existir literalmente no texto bruto v2 **e** na linha da âncora `[§n]` do `ENUNCIADO.md`. Resultado: 61/61 OK, 0 divergências (TAR-001).

## DEC-004 — Checkpoint do Discovery aprovado; direção do Design
- Data: 2026-11-15 · Fase: Discovery → Design · Status: APROVADA
- Aprovada por: usuário ("Aprovar e seguir", em resposta a "Aprova o Discovery e as três recomendações de Design?")
- Decisão:
  - (a) **Tarefa: detecção de objetos com caixas delimitadoras** [§2.2], ajustando um detector YOLO pequeno pré-treinado (n ou s). Métricas: precisão, recall e mAP [§2.3]. Condicionais ativos: REQ-VCIA-13, 21, 22, 23, 28. Condicionais de classificação (12, 17–20, 27) ficam **NÃO APLICÁVEL (tarefa = detecção, DEC-004)**.
  - (b) **Base: pública, de detecção de lixo/descarte em via pública**, escolhida na TAR-002 entre candidatas abertas; critério decisivo = rastrear a imagem de origem (REQ-VCIA-11). Fotos próprias só como teste qualitativo, com rostos e placas borrados.
  - (c) **Hospedagem: app Gradio próprio "FOMEZERO · VCIA — Reportar descarte irregular" como entrega garantida**; ao Erick, CT-08 com **T2 (iframe) preferencial**, T1 opcional e T3 (SIMULADO) só para demonstração offline.
- Consequência: TAR-002 (bases) e TAR-003 (Design) iniciadas.

## DEC-005 — Usuário escolhe levar a Opção C (triagem visual de alimentos) ao CENTRAL; VCIA segue parada
- Data: 2026-11-15 · Fase: Design · Status: APROVADA (escolha do usuário: "Opção C (triagem)")
- Decisão: preparar o pacote para o CENTRAL (`03_INTEGRACAO/PACOTE_CENTRAL_OPCAO_C.md`, PC-005). **Não** implementar nada até a DEC nova existir no CENTRAL (regra do prompt inicial; PEN-012).
- Efeito sobre a DEC-004: os itens (a) tarefa e (b) base ficam **suspensos** até a decisão do CENTRAL; (c) hospedagem (Gradio próprio + CT-08) continua válida, com outro conteúdo.

## DEC-006 — Adoção local da DEC-023 do CENTRAL
- Data: 2026-11-16 · Fase: Design · Status: APROVADA (DEC-023 do CENTRAL, aprovada pelo usuário; espelho sincronizado e conferido em 16/11)
- Decisão: o projeto local passa a seguir a DEC-023: nicho "Triagem visual de hortifrúti excedente antes do cadastro do lote de doação"; classificação CNN + transfer learning na AgriFreshNET; 3 classes de aparência + "inconclusivo"; produto reconhecido; salvaguardas 1–4 e ajustes (a)–(d); CT-08.
- **Substitui** a DEC-004 (a) e (b): a tarefa passa a ser **classificação**. Condicionais ativos: REQ-VCIA-12, 17, 18, 19, 20, 27. Condicionais de detecção (13, 21, 22, 23, 28): **NÃO APLICÁVEL (tarefa = classificação, DEC-006)**. A DEC-004 (c) continua (app próprio garantido + CT-08 com T2 preferencial).
- Documentos atualizados: `CLAUDE.md` e `.claude/agents/disc-vcia.md` (versões anteriores em `06_ARQUIVO/2026-11-16_*_pre_DEC-023.md`); espelho do CENTRAL (7 arquivos).
- PEN-012 resolvida; PEN-002 (CT-08) e PEN-003 (PROMPT_VCIA) resolvidas pela DEC-023.

## DEC-007 — Design aprovado; início do Development
- Data: 2026-11-16 · Fase: Design → Development · Status: APROVADA (usuário: "Aprovar e treinar")
- Decisão: vale o `02_MATERIA_VCIA/DESENVOLVIMENTO.md` §2 (24 classes produto×estágio; EfficientNet-B0 principal e MobileNetV3-Large para comparação; 224×224 + normalização ImageNet; τ na validação; divisão 70/15/15 por grupo de origem, validação/teste só originais; treino local na RTX 3050 em `.venv` Python 3.13; app Gradio + CT-08). Instalação de PyTorch, torchvision, scikit-learn, Gradio e OpenCV (gratuitos) no `.venv` do projeto, fora do git.
- Execução: pelo ORQUESTRADOR, para não perder o contexto da inspeção da base no prazo; revisão por data após cada etapa (`/checar-entrega`).

## DEC-008 — Regra de exclusão por rótulo conflitante: só fotos idênticas (dHash distância 0)
- Data: 2026-11-16 · Fase: Development · Status: APROVADA (detalhe de implementação; ORQUESTRADOR)
- Contexto: a inspeção de 15/11 achou 16 conflitos olhando só **nomes repetidos**. O `01_preparar_dados.py` compara todos os pares entre estágios do mesmo produto. Com distância ≤ 2 bits ele marcou 44 fotos; a conferência visual (`05_ENTREGAVEIS/VCIA/evidencias/conferencia_pares_conflitantes_dist0_e_dist2.jpg`) mostrou que os pares com distância 2 eram fotos **diferentes** (melão-de-são-caetano, tomate) e os de distância 0 eram idênticos (laranjas em Fresh e Semi-Fresh).
- Decisão: excluir só fotos com dHash idêntico em estágios diferentes → **34 fotos originais, 68 arquivos** (com as `aug_`). Fotos idênticas no mesmo estágio são unidas no mesmo grupo. Resultado: 1.616 grupos de origem; treino 3.615 originais (9.788 arquivos), validação 782, teste 786; 0 grupos e 0 originais compartilhados (`evidencias/divisao.json`).
- Consequência: o número "16" da DEC-023 do CENTRAL fica desatualizado → PC-006.

## DEC-009 — EfficientNet-B0 é o modelo do app; MobileNetV3-Large fica como comparação
- Data: 2026-11-16 · Fase: Development · Status: APROVADA (critério fixado no Design: qualidade da condição × velocidade; ORQUESTRADOR)
- Dados (teste, n=786 originais; latência lote 1, 224×224, RTX 3050 6 GB Laptop / i5-13420H; `evidencias/metricas_teste_*.json`, `desempenho_*.json`, `interferencias_*.json`):
| | EfficientNet-B0 | MobileNetV3-Large |
|---|---|---|
| F1 macro condição / acurácia | **0,940** / 94,2% | 0,934 / 93,6% |
| F1 macro produto | 0,993 | 1,000 |
| Rotten → "sem sinais" (teste original) | 0 | 0 |
| Inferência GPU / CPU (ms, média) | 17,1 / 44,1 | **13,5 / 30,1** |
| Sequência ponta a ponta GPU | 40,7 FPS | 52,0 FPS |
| F1 com desfoque r3 / Rotten → "sem sinais" | **0,852 / 35** | 0,785 / 53 |
| F1 com obstrução 25% / Rotten → "sem sinais" | 0,722 / 25 | **0,739 / 15** |
- Decisão: **EfficientNet-B0** no app e no CT-08: melhor F1 de condição e mais robusta ao desfoque (o caso mais perigoso), e as duas passam folgado do tempo real (> 20 FPS até na CPU). A MobileNetV3-Large fica no relatório como alternativa mais rápida, para CPU.

## DEC-010 — Salvaguarda de nitidez: foto borrada vira "inconclusivo" (EXTRA aprovado)
- Data: 2026-11-16 · Fase: Development · Status: APROVADA (usuário: "Sim, adicionar", em resposta a "Adiciono o aviso de nitidez (foto borrada vira "inconclusivo") ao app?")
- Contexto: no teste com desfoque r3, 29 fotos "Rotten" (de 280) passavam do τ como "sem sinais visuais de deterioração" — o modelo erra com confiança alta e o τ não protege. É **EXTRA** (não há REQ que peça); apoia REQ-VCIA-25 (interferências) e as salvaguardas da DEC-023; não substitui nenhum REQ.
- Decisão: medir a nitidez antes de sugerir (`comum.nitidez`: variância do laplaciano ÷ brilho médio², cinza 224×224). Abaixo do limiar → "inconclusivo — avaliar pessoalmente", mensagem pedindo outra foto, confirmação humana; nada é barrado. No inconclusivo, o gráfico de probabilidades some da tela (o destaque da classe mais provável parecia sugestão).
- Calibração **só na validação** (n=782 originais): limiar = percentil 2 das originais = **0,0009446**. Variante escolhida entre 4 também na validação (`evidencias/nitidez_variantes_validacao.json`): a bruta recusava 18,9% das escurecidas e a ÷variância 19,8% das com sombra; a ÷brilho² recusa 0,4% e 1,5%. A 1ª medição no teste com a bruta está guardada (`nitidez_efficientnet_b0_v1_sem_normalizar.json`).
- Resultado no teste (n=786, `evidencias/nitidez_efficientnet_b0.json`; perturbações sintéticas, fora das métricas oficiais):
| Conjunto | Recusadas por nitidez | Cobertura sem → com | "Rotten" → "sem sinais" sem → com |
|---|---|---|---|
| original | 9 (4 Fresh, 5 Semi, 0 Rotten) | 98,98% → 97,84% | 0 → 0 |
| escurecer ×0,6 | 6 | 98,35% → 97,58% | 0 → 0 |
| clarear ×1,4 | 22 | 98,09% → 95,29% | 0 → 0 |
| sombra sintética | 11 | 98,60% → 97,20% | 0 → 0 |
| obstrução 25% | 4 | 77,48% → 77,23% | **11 → 11** |
| desfoque r3 | 709 | 96,31% → 9,03% | **29 → 0** |
- Limitação mantida: a obstrução parcial não é detectada (11 casos); vai para o relatório e para os Limites do CT-08. CT-08 ganhou campos opcionais `motivo_inconclusivo`, `nitidez` e `probabilidades_condicao` (compatível com `ct08-v1`). Exemplo sintético `app/exemplos/tomate_3rotten_BORRADA_sintetica.jpg`: sem a salvaguarda o modelo diria "sem sinais" com 79,5%; com ela, "inconclusivo" (print `prints/03_app_salvaguarda_nitidez_tomate_borrado.jpg`).
