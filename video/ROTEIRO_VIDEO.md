# Roteiro do vídeo de demonstração — VCIA (E-b)

**Nicho: Triagem visual de hortifrúti excedente antes do cadastro do lote de doação**

| Item | Valor |
|---|---|
| Atende | [§4.b] "Gravação curta mostrando a funcionalidade integrada ao CitizenTech, exibindo testes com imagens estáticas e o processamento dinâmico de vídeo ou sequência de quadros." (REQ-VCIA-44, 45, 46, 62) e [§2.4] (REQ-VCIA-26 a 30) |
| Duração-alvo | **cerca de 3 min** `[HIPÓTESE: a duração máxima não foi informada — PEN-007 / P-VCIA-03]` |
| Grupo | Erick Miguel (RM 564896) · Leonardo Melo (RM 567097) · Luna Oliveira (RM 564215). Mostrar os nomes e RMs na abertura (cena 1) ou num cartão final |
| Quem grava | o grupo (voz e tela). Ferramentas gratuitas: OBS Studio ou a Barra de Jogo do Windows (Win+Alt+R) |
| Saída | `video/demo_vcia.mp4` (1920×1080 ou 1280×720). O link fica no README e na entrega |

## Antes de gravar (checklist)
- [ ] App rodando com o código revisado em 16/11 (`python app/app.py`), aberto em http://127.0.0.1:7860, zoom do navegador em 100–110%.
- [ ] Rótulos conferidos (TAR-009): o cartão diz "Sugestão da triagem visual", o aviso fixo aparece no topo e a aba Sequência mostra a tabela.
- [ ] Tela limpa, sem dados pessoais: feche e-mail, WhatsApp e outras abas, e desligue as notificações (Windows: "Não incomodar").
- [ ] Deixe o vídeo `video/bancada_sequencia_efficientnet_b0.mp4` aberto num player.
- [ ] **Integração com a FEMD:** se o Erick já tiver posto o CT-08 na tela de cadastro, grave a cena 2A. Se não, grave a cena 2B. Nunca mostre uma tela que finja estar integrada.
- [ ] Ensaie as falas uma vez. Elas cabem em cerca de 3 min falando sem pressa.

## Cenas

| # | Tempo | O que aparece na tela | Fala (narração) |
|---|---|---|---|
| 1 | 0:00–0:15 | Cartão de 2 s com "FOMEZERO · VCIA" e os integrantes (Erick Miguel 564896 · Leonardo Melo 567097 · Luna Oliveira 564215); depois, o topo do app com o título, o nicho e o aviso em destaque | "Este é o módulo de visão computacional do FOMEZERO, o nosso protótipo CitizenTech. O nicho é a triagem visual de hortifrúti excedente antes do cadastro do lote de doação. É um apoio: a imagem não atesta que o alimento é seguro para consumo; a decisão é do doador e da vigilância sanitária." |
| 2A | 0:15–0:40 | *(se integrado)* FEMD, tela `/doador/cadastro-lote`, botão "Sugerir condição pela foto" e o campo "Condição informada pelo doador" sendo pré-preenchido | "No cadastro do lote de doação, o doador tira a foto de um item e recebe uma sugestão que pré-preenche o campo 'Condição informada pelo doador'. Ele pode editar o texto, e nada é bloqueado." |
| 2B | 0:15–0:40 | *(se não integrado)* App da VCIA; abra o acordeão "Resposta no contrato CT-08" depois da cena 3 ou mostre `03_INTEGRACAO/CONTRATOS.md` §2 | "A integração com a tela de cadastro da FEMD segue o contrato CT-08: a FEMD recebe este JSON e pré-preenche o campo 'Condição informada pelo doador' com a sugestão, que o doador pode editar. Aqui mostramos o módulo funcionando no app da VCIA." |
| 3 | 0:40–1:00 | Instrução da tela ("um item por vez, de cima, sobre fundo claro"), lista dos 8 produtos | "O modelo foi treinado para oito produtos e para fotos de um item por vez, de cima, sobre fundo claro. Pratos prontos, carnes e caixas com vários itens estão fora do escopo." |
| 4 | 1:00–1:20 | **Imagem estática 1:** exemplo `banana_1fresh` → "Sugerir condição pela foto" → cartão "sem sinais visuais de deterioração", confiança 92%, produto banana | "Primeiro teste com imagem estática: a banana recebe a sugestão 'sem sinais visuais de deterioração', com 92% de confiança, e o produto reconhecido aparece junto para o doador conferir." |
| 5 | 1:20–1:40 | **Imagem estática 2:** `laranja_2semi` → "sinais visuais leves — priorizar uso rápido e avaliar pessoalmente", 85% | "Esta laranja tem sinais leves: a sugestão é priorizar o uso rápido e avaliar pessoalmente." |
| 6 | 1:40–2:00 | **Imagem estática 3:** `banana_3rotten` → "sinais visuais de deterioração — sugestão: compostagem", 89%, alerta "Confirmação humana necessária". Clique na caixa de texto e edite uma palavra | "Aqui a sugestão é compostagem. Nesse caso, o app pede confirmação humana e não bloqueia nada. O texto vai para o cadastro como sugestão, e o doador pode editar antes de salvar." |
| 7 | 2:00–2:15 | `tomate_3rotten_BORRADA_sintetica` → "inconclusivo — avaliar pessoalmente" + "A foto parece borrada… tire outra foto" | "Esta foto foi borrada de propósito. Sem a nossa salvaguarda de nitidez, o modelo diria que o tomate não tinha sinais de deterioração. Com ela, o resultado vira 'inconclusivo' e o app pede outra foto." |
| 8 | 2:15–2:40 | **Processamento dinâmico:** aba "Sequência (bancada)" → "Processar sequência" → FPS + tabela; depois, 3–4 s do vídeo `bancada_sequencia_efficientnet_b0.mp4` | "Para simular o monitoramento contínuo de uma bancada de doação, processamos uma sequência de fotos. Cada foto leva poucos milissegundos na GPU. A tabela mostra a sugestão completa de cada item, e este vídeo mostra a mesma bancada quadro a quadro." |
| 9 | 2:40–3:00 | Tela de resumo (pode ser o `relatorio/RELATORIO_TECNICO_VCIA.md` §6–§8 ou um slide simples) | "No teste com 786 fotos que o modelo nunca viu, a EfficientNet-B0 teve F1 macro de 0,94 na condição, com 17 milissegundos por imagem numa RTX 3050. Ela erra mais entre estágios vizinhos, como 'leve' e 'sem sinais', e não detecta obstrução parcial. Por isso a decisão continua sendo do doador." |
| 10 | 3:00–3:10 | Aviso fixo em tela cheia | "Apoio à triagem visual. A imagem não atesta que o alimento é seguro para consumo; a decisão é do doador e da vigilância sanitária." |

## Regras das falas
- Use "sugestão", "triagem visual", "confiança" e "inconclusivo". Nunca diga "apto", "seguro" ou "próprio para consumo", exceto na frase do aviso fixo, e nunca "confirmado".
- Os números citados vêm do relatório: F1 0,94 com n = 786 no teste e 17 ms por imagem na RTX 3050. Não arredonde para "acerta tudo" nem diga "100%".
- A cena 7 usa uma foto sintética: diga que ela foi "borrada de propósito".
- Se a confiança mostrada na gravação for diferente da fala (por exemplo, por uma foto trocada), diga o número que aparece na tela.
- Opcional, para mostrar honestidade: o exemplo `mamao_2semi` sai como "sem sinais" (85%), mas na base ele é Semi-Fresh. É um erro real, que pode ser citado na cena 9.

## Depois de gravar
- [ ] Assistir inteiro e conferir: o texto aparece completo, não há dado pessoal visível, o aviso aparece no início e no fim, e a duração ficou dentro do limite (PEN-007).
- [ ] Salvar em `video/demo_vcia.mp4` e registrar a duração e o tamanho no STATUS.
- [ ] Atualizar REQ-VCIA-44, 45, 46 e 62 na RASTREABILIDADE com o arquivo e o minuto de cada trecho.
