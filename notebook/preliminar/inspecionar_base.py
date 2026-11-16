# Inspeção preliminar de uma base de imagens (REQ-VCIA-08, 11).
# Uso: python -I inspecionar_base.py <pasta_extraida> <saida.json>
# - estrutura de pastas e contagens por pasta-folha
# - extensões, resoluções (amostra), arquivos ilegíveis
# - padrões de nome que indicam aumento de dados
# - quase-duplicatas por dHash 64 bits (original e espelhada), distância de Hamming <= LIMIAR
import sys, os, json, re, collections
from PIL import Image

RAIZ, SAIDA = sys.argv[1], sys.argv[2]
LIMIAR = 6
EXT = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}

def dhash(img, n=8):
    g = img.convert('L').resize((n + 1, n), Image.BILINEAR)
    px = list(g.getdata())
    bits = 0
    for y in range(n):
        for x in range(n):
            bits = (bits << 1) | (px[y * (n + 1) + x] > px[y * (n + 1) + x + 1])
    return bits

arquivos, ilegiveis = [], []
por_pasta = collections.Counter()
exts = collections.Counter()
tamanhos = collections.Counter()
for dp, _, fs in os.walk(RAIZ):
    for f in fs:
        e = os.path.splitext(f)[1].lower()
        exts[e] += 1
        if e in EXT:
            rel = os.path.relpath(os.path.join(dp, f), RAIZ)
            arquivos.append(rel)
            por_pasta[os.path.relpath(dp, RAIZ)] += 1

hashes = {}
for i, rel in enumerate(arquivos):
    try:
        with Image.open(os.path.join(RAIZ, rel)) as im:
            if i % 25 == 0:
                tamanhos[f'{im.width}x{im.height}'] += 1
            hashes[rel] = (dhash(im), dhash(im.transpose(Image.FLIP_LEFT_RIGHT)))
    except Exception as ex:
        ilegiveis.append([rel, str(ex)[:80]])

# padrões de nome sugestivos de aumento
pad = re.compile(r'(aug|augment|rot|flip|bright|zoom|shear|noise|blur|copy|\(\d+\)|_\d+_\d+)', re.I)
nomes_suspeitos = collections.Counter()
for rel in arquivos:
    for m in pad.findall(os.path.basename(rel)):
        nomes_suspeitos[m.lower() if not m.startswith('(') else '(n)'] += 1

# quase-duplicatas: índice por 4 blocos de 16 bits (garante achar pares com Hamming <= 3; acha muitos até 6)
idx = collections.defaultdict(list)
itens = list(hashes.items())
for k, (rel, (h, hf)) in enumerate(itens):
    for b in range(4):
        idx[(b, (h >> (16 * b)) & 0xFFFF)].append(k)
pai = list(range(len(itens)))
def acha(a):
    while pai[a] != a:
        pai[a] = pai[pai[a]]; a = pai[a]
    return a
pares = 0
def compara(k, h):
    global pares
    for b in range(4):
        for j in idx[(b, (h >> (16 * b)) & 0xFFFF)]:
            if j <= k:
                continue
            if bin(h ^ itens[j][1][0]).count('1') <= LIMIAR:
                ra, rb = acha(k), acha(j)
                if ra != rb:
                    pai[ra] = rb; pares += 1
for k, (rel, (h, hf)) in enumerate(itens):
    compara(k, h)
    compara(k, hf)   # espelhada x original
grupos = collections.defaultdict(list)
for k in range(len(itens)):
    grupos[acha(k)].append(itens[k][0])
multi = sorted([g for g in grupos.values() if len(g) > 1], key=len, reverse=True)
# grupos que atravessam pastas-folha diferentes (possível rótulo inconsistente)
cruzados = [g for g in multi if len({os.path.dirname(x) for x in g}) > 1]

res = {
    'raiz': RAIZ, 'total_imagens': len(arquivos), 'extensoes': dict(exts),
    'por_pasta_folha': dict(sorted(por_pasta.items())),
    'resolucoes_amostra_1_em_25': dict(tamanhos.most_common(15)),
    'ilegiveis': ilegiveis[:50], 'n_ilegiveis': len(ilegiveis),
    'padroes_de_nome_sugestivos': dict(nomes_suspeitos.most_common(20)),
    'exemplos_nomes': arquivos[:15],
    'dhash_limiar_hamming': LIMIAR,
    'grupos_quase_duplicatas': len(multi),
    'imagens_em_grupos': sum(len(g) for g in multi),
    'maiores_grupos': [g[:8] + ([f'... +{len(g)-8}'] if len(g) > 8 else []) for g in multi[:10]],
    'grupos_que_cruzam_pastas': len(cruzados),
    'exemplos_cruzados': [g[:6] for g in cruzados[:10]],
}
with open(SAIDA, 'w', encoding='utf-8') as fo:
    json.dump(res, fo, ensure_ascii=False, indent=1)
print(json.dumps({k: res[k] for k in ['total_imagens', 'extensoes', 'n_ilegiveis', 'resolucoes_amostra_1_em_25', 'padroes_de_nome_sugestivos', 'grupos_quase_duplicatas', 'imagens_em_grupos', 'grupos_que_cruzam_pastas']}, ensure_ascii=False, indent=1))
