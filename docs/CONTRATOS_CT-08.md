# CONTRATOS — VCIA

> Versão anterior (CT-08 para descarte irregular): `06_ARQUIVO/2026-11-16_CONTRATOS_pre_DEC-023.md`.

## 1. Informações recebidas do grupo em 15/11/2026 (registro)
Fonte: Erick Miguel (FEMD), repassado pelo usuário no prompt inicial em 2026-11-15; conferido com o README da FEMD (GitHub `lostgear84/FomeZero_FrontEnd`, `master` `6eb1b2e`, 14/11) e com o `MAPA_INTEGRACAO.md` do CENTRAL.
| Integração | Status (Erick, 15/11) | Observação |
|---|---|---|
| IOT → FEMD (alerta térmico do lote) | **OK** — campos e unidades batem com a mensagem MQTT | esquemas `fomezero.telemetria.v1` e `fomezero.alerta.v1`; tópicos `fomezero/gs2026/rm564896/lote/<lote_id>/...`. A VCIA não toca nesses dados |
| AIPA → FEMD (pontos e Selo Verde ESG) | PENDENTE | no clone local, branch `integracao-genai-aipa` (`9b5a9d8`, 15/11) já tem `aipaService.js` |
| GENAI → FEMD (assistente para doadores) | em andamento | padrão CT-02 (T1/T2/T3); tela `AssistenteConsulta.jsx` + `genai_respostas_SIMULADO.json` no branch `integracao-genai-aipa` |
| **FEMD hospeda a função da VCIA** | **PENDENTE: a equipe decide** | README da FEMD: "VCIA \| Pendente \| Decisão da equipe sobre onde será hospedada a funcionalidade de imagem" |

Fatos da FEMD `[CONFIRMADO: clone local + GitHub]`: SPA React + Vite **sem backend**; dados no `localStorage` (`fomezero.lotes.v1`); rotas `/doador/cadastro-lote` e outras. A tela de cadastro tem o campo de texto livre **"Condição informada pelo doador"** (`condicao_informada`, até 1000 caracteres), com a ajuda "Descrição declarada pelo doador. Não representa validação sanitária nem garantia de segurança para consumo." (`frontend/src/pages/CadastroLote.jsx`).
Campos do lote são do grupo. **A VCIA não cria nem renomeia campos**; ela só sugere um texto para `condicao_informada`, que o doador edita (DEC-023).

Numeração em uso: CT-01 (PLN→GENAI), CT-02 (GENAI→FEMD), CT-03 (FEMD→AIPA), CT-04 (AIPA→FEMD), CT-05 (AIPA→GABA/CQIA), CT-06 (IA→AIPA, não usado), CT-07 (PLN→IOT/CCNS), **CT-08 (VCIA→FEMD)** — DEC-023.

## 2. CT-08 (VCIA → FEMD) — PROPOSTA `ct08-v1`
**Status: PROPOSTA (DEC-023 do CENTRAL).** A decisão de como ligar é do Erick (PEN-001, PEN-015). Nada aqui obriga a FEMD a mudar o desenho. Padrão do CT-02 da GENAI.

### Onde aparece na FEMD (sugestão)
Na tela `/doador/cadastro-lote`, um botão **"Sugerir condição pela foto"** ao lado do campo "Condição informada pelo doador". Ao receber a resposta, a FEMD **pré-preenche** o campo com `texto_sugerido` e mostra o `aviso`. O doador edita e salva. Nenhum campo novo no lote; nada é barrado.

### Formas de ligar (a FEMD escolhe)
| Opção | Como | Prós | Contras |
|---|---|---|---|
| T2 (preferencial) | `iframe` com a interface Gradio da VCIA; o doador copia o texto sugerido | menor esforço para a FEMD; IA ao vivo | link `gradio.live` temporário; a FEMD não controla o layout |
| T1 | a FEMD chama o endpoint Gradio `/triagem` com `@gradio/client` (`Client.connect(URL)`, `predict("/triagem", [imagem])`) e preenche o campo sozinha | integração real | mesmo link temporário; mais código na FEMD |
| T3 (sempre entregue) | a FEMD lê `respostas_SIMULADO.json` (saídas **reais** do modelo para imagens de exemplo, gravadas) e mostra a faixa **"SIMULADO"** | funciona sem internet nem GPU | não é IA ao vivo |

### Entrada
Uma imagem JPEG/PNG de **um item de hortifrúti**, de cima, sobre fundo claro. Produtos aceitos: banana, melão-de-são-caetano, pepino, berinjela, laranja, mamão, abacaxi, tomate.

### Saída (esquema `fomezero.vcia.v1` `[HIPÓTESE: a equipe confirma]`)
```json
{"esquema": "fomezero.vcia.v1", "versao": "ct08-v1",
 "nicho": "Triagem visual de hortifrúti excedente antes do cadastro do lote de doação",
 "produto": {"rotulo": "tomate", "confianca": 0.0},
 "condicao": {"classe": "sem sinais visuais de deterioração", "confianca": 0.0},
 "limiar": 0.0, "inconclusivo": false,
 "texto_sugerido": "Sugestão da triagem visual (confiança 0%): sem sinais visuais de deterioração",
 "pede_confirmacao_humana": false,
 "modelo": "<arquitetura e versão>", "tempo_ms": 0, "simulado": false,
 "aviso": "Apoio à triagem visual. A imagem não atesta que o alimento é seguro para consumo; a decisão é do doador e da vigilância sanitária."}
```
O exemplo mostra só o formato; números são ilustrativos.
| Campo | O que é |
|---|---|
| `produto` | produto reconhecido (um dos 8) e confiança 0–1; ajuda o doador a perceber erro do modelo |
| `condicao.classe` | "sem sinais visuais de deterioração" · "sinais visuais leves — priorizar uso rápido e avaliar pessoalmente" · "sinais visuais de deterioração — sugestão: compostagem" · "inconclusivo — avaliar pessoalmente" |
| `limiar`, `inconclusivo` | τ calibrado na validação; `inconclusivo=true` quando a confiança de condição < τ |
| `texto_sugerido` | o que vai para `condicao_informada`; **nunca** contém "confirmado" |
| `pede_confirmacao_humana` | `true` na classe 3 e no inconclusivo |
| `simulado` | `true` no modo T3 |
| `aviso` | **sempre presente**; a FEMD exibe junto do resultado |
| `motivo_inconclusivo` | *(acréscimo 16/11, DEC-010)* `null`, `"confianca_abaixo_do_limiar"` ou `"foto_borrada"` |
| `nitidez` | *(acréscimo 16/11, DEC-010)* `{"valor", "limiar", "borrada", "mensagem"}`; com `borrada=true` a resposta é "inconclusivo" e `mensagem` pede outra foto — a FEMD exibe essa mensagem |
| `probabilidades_condicao` | *(acréscimo 16/11)* probabilidade de cada uma das 3 condições; informativo, a FEMD **não** deve destacá-las quando `inconclusivo=true` |
Os acréscimos não mudam nenhum campo existente (compatível com `ct08-v1`); a FEMD pode ignorá-los, exceto a `nitidez.mensagem`, que é recomendável exibir.
Erros: `{"status":"erro","erro":{"codigo":"IMAGEM_INVALIDA|SERVICO_INDISPONIVEL|TEMPO_ESGOTADO|ERRO_INTERNO","mensagem":"..."},"aviso":"..."}`.

### Limites
- Não diz que o alimento é "apto", "seguro" ou "próprio para consumo"; não informa validade nem vida útil; não barra o cadastro.
- AIPA, GABA e indicadores tratam o texto de `condicao_informada` como **informado pelo doador**, nunca como validação (DEC-023 ajuste c).
- Fora do domínio (prato pronto, carne, caixa com vários itens): o modelo pode errar com confiança alta; o limiar não protege contra isso.
- Foto borrada: a salvaguarda de nitidez (DEC-010) devolve "inconclusivo" e pede outra foto. Obstrução parcial (mão, outro objeto na frente) **não** é detectada: no teste sintético, 11 de 280 "Rotten" com 25% da área coberta ainda saem como "sem sinais visuais de deterioração".
- O link Gradio não é produção.
