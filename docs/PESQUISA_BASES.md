# PESQUISA DE BASES — triagem visual de alimentos (Opção C)

> **Pesquisa preparatória, feita em 2026-11-15 a pedido do usuário, ANTES da decisão do CENTRAL (PEN-012, PC-005).** Nada foi baixado. Só está registrado o que estava escrito nas páginas abertas (Mendeley Data, pelo navegador embutido). Se o CENTRAL mantiver a DEC-022, esta pesquisa vai para `06_ARQUIVO/`.
> REQs ligados: REQ-VCIA-59 (base pública compatível), 08 (examinar imagens e rótulos), 11 (não espalhar variações da mesma imagem), 15 (amostra representativa).

## Escopo realista
Não encontrei base pública de **pratos prontos** com rótulo de deterioração. As bases abertas são de **hortifrúti** (frutas e verduras), o que combina com os doadores do FOMEZERO (feiras, mercados, sacolões). Proposta: o nicho declara "hortifrúti excedente" e o relatório diz que pratos prontos ficam fora `[HIPÓTESE: a confirmar no CENTRAL]`.

## Comparação (páginas abertas em 2026-11-15)
| # | Base | URL aberta | Licença (literal) | Imagens | Rótulos | Cena | Origem rastreável (REQ-11) | Download |
|---|---|---|---|---|---|---|---|---|
| 1 | **AgriFreshNET Freshness and Shelf-Life Image Dataset** (Risdin, Salauddin, Tufa, Hossain — East West University), v1, 30/07/2026, DOI 10.17632/42m5tb7yv9.1 | https://data.mendeley.com/datasets/42m5tb7yv9/1 | CC BY 4.0 | 14.500 RGB; "24 classes of fruits and vegetables"; média de 569 por classe | **Fresh, Semi-Fresh, Rotten** + vida útil aproximada | celular, "local markets, supermarkets, households, farms, and storage facilities", luz e fundos variados | `[PENDENTE]` só há "Processed Data.zip" (332 MB); o "Raw Data.zip" citado nos passos **não aparece** na lista de arquivos; a página não diz se o processado tem aumento de dados | direto, sem conta |
| 2 | **Fresh and Rotten Fruits Dataset for Machine-Based Evaluation of Fruit Quality** (Sultana, Jahan, Uddin — Jahangirnagar University), v1, 08/04/2022, DOI 10.17632/bdd69gyhv8.1 | https://data.mendeley.com/datasets/bdd69gyhv8/1 | CC BY 4.0 | 3.200 originais + 12.335 aumentadas (zips separados) | 16 classes: fresh/rotten × maçã, banana, laranja, uva, goiaba, jujuba, romã, morango | "different fruit shops and real fields" | **Sim**: "Original Image.zip" (2,6 GB) separado do "Augmented Image.zip" (766 MB) | direto, sem conta |
| 3 | **Spoiled and fresh fruit inspection dataset** (Pachon Suescun, Pinzón Arenas, Jiménez-Moreno), v1, 01/11/2020, DOI 10.17632/6ps7gtp2wg.1 | https://data.mendeley.com/datasets/6ps7gtp2wg/1 | CC BY 4.0 | 16.000 (2.000 por fruta; metade fresca, metade estragada); 95,3 MB | fresh × spoiled em 8 frutas (banana, limão, lulo, manga, laranja, morango, tamarillo, tomate) | fundos trocados, "rotation of the fruits", distância e luz variadas | **Risco**: várias fotos da mesma fruta física, sem ID de origem declarado | direto, sem conta |
| 4 | **FruitVision** (Bijoy, Tasnim, Awsaf, Hasan), v2, 15/01/2025, DOI 10.17632/xkbjx8959c.2 | https://data.mendeley.com/datasets/xkbjx8959c/2 | **CC BY-NC-ND 4.0** | 10.154 originais → >81.000 aumentadas | fresh / rotten / formalin-mixed × 5 frutas | não visível | Sim ("Original Image.zip" 857 MB separado) | direto |
Não avaliadas (não abertas): bases de carne (fresh/half-fresh/spoiled) — fora do escopo por risco sanitário maior; bases só de Kaggle (exigem conta para baixar).

## Avaliação
- **#1 AgriFreshNET** é a única com **3 estágios** que casam com as 3 classes da Opção C, tem fotos de celular em mercados (cenário do doador), licença aberta e tamanho viável (332 MB). Riscos: publicada há 4 meses (pouco uso independente); conteúdo do zip e presença de aumento de dados não verificados.
- **#2** é a mais segura para o REQ-VCIA-11 (originais separados), mas é **binária** (fresh/rotten) e pesada (2,6 GB).
- **#3** tem risco alto de vazamento (mesma fruta fotografada de vários ângulos, sem ID).
- **#4** descartada como principal: "ND" (sem derivados) complica publicar amostras/modelo no repositório; a classe "formalin" não serve ao FOMEZERO.

## Recomendação `[HIPÓTESE até o download]`
- **Principal: AgriFreshNET (#1)**, classificação em 3 classes com transfer learning (ex.: CNN leve pré-treinada no ImageNet).
- **Reserva: Fresh and Rotten Fruits (#2), só "Original Image.zip"**, se o zip da #1 tiver aumento de dados não separável ou rótulos ruins. Com a #2 o problema vira binário + classe "inconclusivo" pelo limiar.

### Mapeamento das classes para a tela (proposta; ajusta o pacote PC-005)
| Classe da base | Rótulo na tela (FOMEZERO) | Sugestão ao doador |
|---|---|---|
| Fresh | "sem sinais visuais de deterioração" | segue para o cadastro; o doador confirma |
| Semi-Fresh | "sinais visuais leves — priorizar uso rápido e avaliar pessoalmente" | o doador avalia antes de cadastrar |
| Rotten | "sinais visuais de deterioração — sugestão: compostagem" | alerta; não cadastrar sem avaliação humana |
| confiança < limiar | "inconclusivo — avaliar pessoalmente" | — |
Nenhum rótulo usa "apto", "seguro" ou "próprio para consumo".

### Divisão sem vazamento (REQ-VCIA-11) — plano
1. Baixar e **examinar** a estrutura (pastas, nomes, resoluções, duplicatas) antes de qualquer treino (REQ-08).
2. Agrupar quase-duplicatas por **hash perceptual** (pHash/dHash, inclusive das versões espelhada e girada) e por padrão de nome; cada grupo vai inteiro para um só conjunto.
3. Divisão estratificada por classe e por tipo de produto, 70/15/15, **por grupo**; registrar n por conjunto e classe.
4. Amostra representativa (REQ-15): se o tempo de treino apertar, subamostrar por grupo mantendo a proporção de classes e produtos.

## Inspeção da AgriFreshNET (2026-11-15, download autorizado pelo usuário)
Arquivo: `Processed Data.zip`, 347.828.971 bytes, baixado pela API pública do Mendeley; **SHA-256 `6607a48b…fcac53f11` igual ao publicado** pelo Mendeley. Extraído em `dados_brutos/agrifreshnet/` (fora do git). Zip sem caminhos perigosos.
Evidências: `05_ENTREGAVEIS/VCIA/evidencias/inspecao_agrifreshnet_PRELIMINAR.json`, `agrupamento_origem_agrifreshnet_PRELIMINAR.json`, `mosaico_amostra_agrifreshnet_PRELIMINAR.jpg`; scripts em `05_ENTREGAVEIS/VCIA/notebook/preliminar/`.

| Item | Achado `[CONFIRMADO pela inspeção]` |
|---|---|
| Total | **14.160** arquivos (a página diz 14.500), 0 ilegíveis, .jpg/.jpeg, **512×512** (amostra de 1 em 25) |
| Estrutura | 24 pastas = **8 produtos** (banana, melão-de-são-caetano, pepino, berinjela, laranja, mamão, abacaxi, tomate) × **3 estágios**; o nome da pasta traz a faixa de vida útil (ex.: "Fresh Banana(1-4)") |
| Aumento de dados | **Sim, embutido**: cada pasta foi completada até exatamente 590 arquivos com `aug_<n>_<foto original>.jpg`. **5.217 originais** + **8.943 aumentadas**. Originais por estágio: Fresh 1.934 · Semi-Fresh 1.660 · Rotten 1.623 |
| Origem rastreável (REQ-11) | **Sim, pelo nome**: o prefixo `aug_<n>_` some e sobra o nome da original. A maioria dos nomes traz data e hora (`IMG_AAAAMMDD_HHMMSS`); fotos tiradas no mesmo minuto foram tratadas como uma **sessão** (mesmo item ou mesma bancada) → **1.632 grupos de origem** (maior: 38 originais; 947 grupos com 1 original) |
| Rótulo conflitante | **16 fotos idênticas em duas pastas de estágio** (ex.: `IMG-20251122-WA0000.jpg` em Fresh Orange e em Semi fresh Orange; conferido por dHash ≤ 2). 12 outras colisões de nome são fotos diferentes. 98 sessões têm fotos em mais de uma pasta (fotos diferentes do mesmo minuto) |
| dHash global | com limiar 6 e fusão transitiva, formou um "grupão" de 5.261 imagens (fundos muito parecidos): **não serve sozinho** para agrupar; fica só como checagem de duplicata exata |
| Cenário (mosaico) | **um item por foto, visto de cima, sobre pano branco** (às vezes fundo azul). Não é foto de caixa nem de prato com vários itens |
| Qualidade dos rótulos | Fresh × Semi-Fresh às vezes quase indistinguíveis (tomate); alguns "Rotten Cucumber" parecem pepinos íntegros e algum "Semi Fresh Cucumber" parece estragado → **ruído de rótulo** esperado |

### Consequências para o Design (se a Opção C for aprovada)
1. **Divisão por grupo de origem** (sessão por minuto; senão, nome original), estratificada por estágio e produto, 70/15/15. **Validação e teste só com originais**; as `aug_` da base só entram no treino, e só as dos grupos de treino. Isso atende ao REQ-VCIA-11 de forma verificável.
2. **Excluir as 16 fotos com rótulo conflitante** (e as `aug_` delas) e registrar a exclusão.
3. **Escopo honesto da tela:** "fotografe **um item por vez**, de cima, sobre fundo claro" — é o domínio da base. Caixa ou prato com vários itens fica fora (limitação no relatório; teste qualitativo com fotos próprias, marcado como tal).
4. Esperar confusão Fresh × Semi-Fresh; analisar na matriz de confusão (REQ-20, 24) e calibrar o limiar para "inconclusivo".
5. As fotos são de Bangladesh, mas 7 dos 8 produtos (banana, pepino, berinjela, laranja, mamão, abacaxi, tomate) são comuns em feiras brasileiras; o melão-de-são-caetano é o menos comum.
**Conclusão:** a AgriFreshNET **continua recomendada**; os riscos acima são tratáveis e ficam documentados. A reserva (Fresh and Rotten Fruits) só entra se o CENTRAL quiser frutas diferentes ou se o ruído de rótulo inviabilizar o treino.

## Pendências desta pesquisa
- ~~conteúdo do zip da #1~~ → resolvido na inspeção acima (2026-11-15).
- `[PENDENTE]` decisão do CENTRAL (PC-005). Nenhum treino antes dela.
