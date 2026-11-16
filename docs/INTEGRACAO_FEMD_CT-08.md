# Para o Erick — integrar a triagem visual (VCIA) na tela de cadastro da FEMD

> **CT-08 (VCIA → FEMD), versão `ct08-v1`** · grupo FOMEZERO — matéria VCIA · 16/11/2026
> **Nicho: Triagem visual de hortifrúti excedente antes do cadastro do lote de doação** (DEC-023 do CENTRAL)
> Este documento é uma proposta: **quem decide como ligar é você.** Nada aqui muda o desenho da FEMD.

---

## 1. Em 30 segundos
- Na tela `/doador/cadastro-lote` (`CadastroLote.jsx`), entra **um botão "Sugerir condição pela foto"** ao lado do campo **"Condição informada pelo doador"**.
- O doador escolhe a foto de **um item** de hortifrúti. A VCIA devolve um texto pronto, que **pré-preenche** `condicaoInformada`, e o doador pode editar antes de salvar.
- **Nenhum campo novo no lote**, nenhuma mudança no `lotesService.js` nem no `localStorage` dos lotes. **Nada é bloqueado.**
- O padrão é o mesmo da GENAI (`assistenteService.js`): **modo simulado** com um JSON gravado (funciona offline) e **modo integrado** com `@gradio/client` e o link `gradio.live`.

## 2. Três jeitos de ligar (escolha um)
| Opção | Esforço na FEMD | Funciona sem o PC da VCIA ligado? | Quando usar |
|---|---|---|---|
| **T3 — simulado** | baixo: ler um JSON | **sim** | garantia para a apresentação e o vídeo |
| **T1 — integrado** (`@gradio/client`) | médio: igual ao `consultarIntegrado` da GENAI | não (link temporário) | demonstração ao vivo |
| **T2 — iframe** | mínimo | não | se não der tempo de codar; o doador copia o texto à mão |

Sugestão da VCIA: **T3 + T1 juntos**, como a GENAI fez (simulado por padrão e integrado quando houver link). Se o integrado falhar, a tela volta ao simulado com um aviso.

## 3. Regras de tela (vêm da DEC-023, não negociáveis)
1. **Aviso fixo** sempre visível junto do resultado (use o campo `aviso` do JSON, sem reescrever):
   > Apoio à triagem visual. A imagem não atesta que o alimento é seguro para consumo; a decisão é do doador e da vigilância sanitária.
2. O texto que vai para o campo é **sempre** o `texto_sugerido`, no formato `Sugestão da triagem visual (confiança 89%): <classe>`. **Nunca** use "confirmado", "apto", "seguro" ou "próprio para consumo".
3. Quando `pede_confirmacao_humana` for `true` (sugestão de compostagem ou "inconclusivo"), mostre: **"Confirmação humana necessária. Avalie o item pessoalmente antes de cadastrar. Nada foi bloqueado: a decisão é sua."**
4. Quando `nitidez.borrada` for `true`, mostre a `nitidez.mensagem` (pede outra foto).
5. **Não sobrescreva** o que o doador já escreveu. Se o campo não estiver vazio, pergunte antes ou acrescente a sugestão numa linha nova. O campo tem `maxLength={1000}`, e o texto sugerido tem cerca de 110 caracteres.
6. Mostre o **produto reconhecido** (`produto.rotulo`), porque ele ajuda o doador a perceber um erro do modelo.
7. No modo simulado: faixa **"SIMULADO"** visível, igual à da GENAI.
8. Junto do botão, a instrução: **"Fotografe um item por vez, de cima, sobre fundo claro. Produtos: banana, melão-de-são-caetano, pepino, berinjela, laranja, mamão, abacaxi, tomate."**

## 4. A resposta (esquema `fomezero.vcia.v1`)
Exemplo real, copiado de `respostas_SIMULADO.json` (banana do conjunto de teste; por isso `simulado` vale `true`; no modo integrado ele vem `false`):
```json
{
  "esquema": "fomezero.vcia.v1", "versao": "ct08-v1",
  "nicho": "Triagem visual de hortifrúti excedente antes do cadastro do lote de doação",
  "motivo_inconclusivo": null,
  "nitidez": {"valor": 0.01174, "limiar": 0.0009446, "borrada": false, "mensagem": null},
  "produto": {"rotulo": "banana", "confianca": 0.8586},
  "condicao": {"classe": "sinais visuais de deterioração — sugestão: compostagem", "confianca": 0.8894},
  "probabilidades_condicao": {"...": 0.0},
  "limiar": 0.5, "inconclusivo": false,
  "texto_sugerido": "Sugestão da triagem visual (confiança 89%): sinais visuais de deterioração — sugestão: compostagem",
  "pede_confirmacao_humana": true,
  "modelo": "efficientnet_b0 (ajuste fino, AgriFreshNET)", "tempo_ms": 13.0, "simulado": true,
  "aviso": "Apoio à triagem visual. A imagem não atesta que o alimento é seguro para consumo; a decisão é do doador e da vigilância sanitária."
}
```
**Campos que a FEMD usa:** `texto_sugerido`, `aviso`, `pede_confirmacao_humana`, `produto.rotulo`, `nitidez.borrada` e `nitidez.mensagem`, além de `simulado` (faixa). O resto é informativo. **Não** destaque `probabilidades_condicao` quando `inconclusivo` for `true`.
Classes possíveis em `condicao.classe`:
- "sem sinais visuais de deterioração"
- "sinais visuais leves — priorizar uso rápido e avaliar pessoalmente"
- "sinais visuais de deterioração — sugestão: compostagem"
- "inconclusivo — avaliar pessoalmente"

Erro: `{"status": "erro", "erro": {"codigo": "IMAGEM_INVALIDA", "mensagem": "..."}, "aviso": "..."}`.

## 5. Arquivos enviados pela VCIA
| Arquivo (repositório da VCIA) | Onde pôr na FEMD (sugestão) |
|---|---|
| `contrato/respostas_SIMULADO.json` (13 respostas reais gravadas; tem a chave `respostas`, e cada item tem `arquivo_exemplo`) | `frontend/src/data/vcia_respostas_SIMULADO.json` |
| `app/exemplos/*.jpg` (13 fotos do teste da AgriFreshNET, CC BY 4.0; a `tomate_3rotten_BORRADA_sintetica.jpg` foi borrada de propósito) | `frontend/public/vcia_exemplos/` |
| `app/exemplos/LEIAME.md` (atribuição da base) | junto das fotos |

## 6. Sugestão de código (siga o padrão da GENAI; **não testado na FEMD**)
`frontend/src/services/vciaService.js`:
```js
// Triagem visual da VCIA. Contrato CT-08 (ct08-v1). Simulado por padrão; integrado se houver link Gradio.
import respostasSimuladas from "../data/vcia_respostas_SIMULADO.json";

const STORAGE_URL = "fomezero.vcia.url.v1";
const TEMPO_LIMITE_MS = 60000;

export const EXEMPLOS = respostasSimuladas.respostas.map((r) => r.arquivo_exemplo);

export function lerUrlVcia() { return localStorage.getItem(STORAGE_URL) || ""; }
export function salvarUrlVcia(url) {
  const limpa = url.trim();
  if (limpa && !/^https:\/\/[\w.-]+\.gradio\.live\/?$|^https?:\/\/(127\.0\.0\.1|localhost):\d+\/?$/.test(limpa)) {
    throw new Error("Informe o link do Gradio da VCIA (ex.: https://xxxx.gradio.live).");
  }
  limpa ? localStorage.setItem(STORAGE_URL, limpa) : localStorage.removeItem(STORAGE_URL);
  return limpa;
}

// T3: o doador escolhe uma das fotos de exemplo; devolve a resposta gravada (sem IA ao vivo).
export function triagemSimulada(arquivoExemplo) {
  const r = respostasSimuladas.respostas.find((x) => x.arquivo_exemplo === arquivoExemplo);
  if (!r) throw new Error("No modo simulado, escolha uma das fotos de exemplo.");
  return { modo: "simulado", resposta: r };
}

// T1: envia a foto ao endpoint /triagem do app Gradio da VCIA.
export async function triagemIntegrada(arquivoImagem, url) {
  const { Client, handle_file } = await import("@gradio/client");
  const limite = (p) => Promise.race([p, new Promise((_, rej) =>
    setTimeout(() => rej(new Error("A triagem visual demorou mais de 60 s.")), TEMPO_LIMITE_MS))]);
  const app = await limite(Client.connect(url));
  const retorno = await limite(app.predict("/triagem", [handle_file(arquivoImagem)]));
  const resposta = Array.isArray(retorno?.data) ? retorno.data[0] : null;
  if (!resposta || !resposta.aviso) throw new Error("Resposta fora do formato fomezero.vcia.v1.");
  if (resposta.status === "erro") throw new Error(resposta.erro?.mensagem || "Erro na triagem visual.");
  return { modo: "integrado", resposta };
}
```
No `CadastroLote.jsx`, um esboço logo abaixo da `<textarea id="condicao-informada">`:
```jsx
// estado: const [triagem, setTriagem] = useState(null);
function aplicarSugestao({ resposta }) {
  setTriagem(resposta);
  setCondicaoInformada((atual) =>
    atual.trim() ? `${atual.trim()}\n${resposta.texto_sugerido}` : resposta.texto_sugerido);  // regra 5
}
// ...
{triagem && (
  <div className="resultado-triagem" role="status">
    {triagem.simulado && <strong className="faixa-simulado">SIMULADO</strong>}
    <p>Produto reconhecido: {triagem.produto.rotulo}</p>
    {triagem.nitidez?.borrada && <p>{triagem.nitidez.mensagem}</p>}
    {triagem.pede_confirmacao_humana && (
      <p><strong>Confirmação humana necessária.</strong> Avalie o item pessoalmente antes de cadastrar. Nada foi bloqueado: a decisão é sua.</p>)}
    <small>{triagem.aviso}</small>
  </div>
)}
```
`[HIPÓTESE]` O uso do `handle_file` com um `File` do `<input type="file" accept="image/*">` segue a documentação do `@gradio/client`. O endpoint `/triagem` foi testado pelo cliente Python, não pelo JS. Se der erro, testamos juntos.

**T2 (iframe), se preferir:**
```jsx
<iframe src={lerUrlVcia()} title="Triagem visual (VCIA)" width="100%" height="900" />
```

## 7. Como o link funciona (T1/T2)
- O app roda com `python app/app.py --share` num PC com GPU, que gera o link `https://xxxx.gradio.live`.
- O link é temporário: só vale enquanto o app estiver rodando nesse PC (e expira depois de um tempo). Combinamos o horário da gravação ou da apresentação.
- Fora desse horário, use o T3 (simulado).

## 8. O que a integração precisa
1. **Qual opção:** T3, T1, T2 ou T3 + T1.
2. **Até quando dá:** a entrega é **19/11**. Se não couber, tudo bem: a demonstração usa o app próprio da VCIA e cito o CT-08 no vídeo, sem mostrar integração que não existe.
3. Quando estiver pronto: **branch e commit** para conferir a tela (só leitura) e gravar o trecho do vídeo.

## 9. Checklist de aceite (a gente confere junto)
- [ ] Botão "Sugerir condição pela foto" na tela de cadastro, com a instrução de foto e os 8 produtos.
- [ ] O texto entra no campo "Condição informada pelo doador" como `texto_sugerido`, editável; nada é bloqueado.
- [ ] O aviso fixo aparece sempre junto do resultado.
- [ ] Faixa "SIMULADO" no modo T3.
- [ ] Mensagem de confirmação humana quando `pede_confirmacao_humana` for `true`.
- [ ] A mensagem de foto borrada aparece com `tomate_3rotten_BORRADA_sintetica.jpg`.
- [ ] Nenhum campo novo no lote; o `lotesService.js` não muda.

Detalhes completos: `03_INTEGRACAO/CONTRATOS.md` §2 (CT-08) e relatório técnico da VCIA §10.
