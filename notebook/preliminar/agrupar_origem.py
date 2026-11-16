# Agrupamento por origem para a divisão sem vazamento (REQ-VCIA-11) — análise preliminar.
# Regra: (1) tira o prefixo aug_<n>_ -> nome da foto original;
# (2) se o nome tem data/hora IMG_AAAAMMDD_HHMMSS..., a chave é a SESSÃO = data + hora + minuto (global, entre pastas);
# (3) senão, a chave é pasta + nome original; (4) nomes genéricos repetidos entre pastas são checados por dHash exato (<=2).
import sys, os, re, json, collections
from PIL import Image
RAIZ, SAIDA = sys.argv[1], sys.argv[2]
ts = re.compile(r'(\d{8})_(\d{4})\d{2}')
def estagio(p):
    p = p.lower()
    return 'Semi-Fresh' if 'semi' in p else ('Rotten' if 'rotten' in p else 'Fresh')
def produto(p):
    return re.sub(r'(?i)^(fresh|rotten|semi[ _]?fresh)\s*', '', p).split('(')[0].strip().lower()
def dhash(path, n=8):
    g = Image.open(path).convert('L').resize((n + 1, n))
    px = g.tobytes()
    return sum(1 << i for i, (y, x) in enumerate((y, x) for y in range(n) for x in range(n)) if px[y*(n+1)+x] > px[y*(n+1)+x+1])
itens = []
for pasta in sorted(os.listdir(RAIZ)):
    for f in os.listdir(os.path.join(RAIZ, pasta)):
        orig = re.sub(r'^aug_\d+_', '', f)
        m = ts.search(orig)
        chave = f'S:{m.group(1)}_{m.group(2)}' if m else f'N:{pasta}/{orig}'
        itens.append(dict(pasta=pasta, arq=f, orig=orig, chave=chave, aug=f.startswith('aug_'),
                          estagio=estagio(pasta), produto=produto(pasta)))
# nomes genéricos iguais em pastas diferentes: mesma foto?
gen = collections.defaultdict(set)
for it in itens:
    if it['chave'].startswith('N:') and not it['aug']:
        gen[it['orig']].add(it['pasta'])
colisoes = {o: sorted(ps) for o, ps in gen.items() if len(ps) > 1}
iguais = []
for o, ps in colisoes.items():
    hs = [dhash(os.path.join(RAIZ, p, o)) for p in ps if os.path.exists(os.path.join(RAIZ, p, o))]
    if len(hs) > 1 and bin(hs[0] ^ hs[1]).count('1') <= 2:
        iguais.append([o, ps])
for o, ps in iguais:   # funde as chaves
    for it in itens:
        if it['orig'] == o and it['pasta'] in ps:
            it['chave'] = f'N:*/{o}'
grupos = collections.defaultdict(list)
for it in itens:
    grupos[it['chave']].append(it)
orig_por_grupo = [len({(i['pasta'], i['orig']) for i in g}) for g in grupos.values()]
multi_rotulo = [k for k, g in grupos.items() if len({i['pasta'] for i in g}) > 1]
dist = collections.Counter((i['estagio']) for i in itens if not i['aug'])
grupos_por_estagio = collections.Counter()
for g in grupos.values():
    for e in {i['estagio'] for i in g}:
        grupos_por_estagio[e] += 1
res = dict(total=len(itens), originais=sum(1 for i in itens if not i['aug']), aumentadas=sum(1 for i in itens if i['aug']),
           originais_por_estagio=dict(dist), produtos=sorted({i['produto'] for i in itens}),
           grupos_origem=len(grupos), grupos_por_estagio=dict(grupos_por_estagio),
           maior_grupo_originais=max(orig_por_grupo), grupos_com_1_original=sum(1 for x in orig_por_grupo if x == 1),
           grupos_com_mais_de_um_rotulo=len(multi_rotulo), exemplos_mais_de_um_rotulo=multi_rotulo[:10],
           colisoes_de_nome_entre_pastas=len(colisoes), colisoes_que_sao_a_mesma_foto=len(iguais), exemplos_mesma_foto=iguais[:5])
json.dump(res, open(SAIDA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
