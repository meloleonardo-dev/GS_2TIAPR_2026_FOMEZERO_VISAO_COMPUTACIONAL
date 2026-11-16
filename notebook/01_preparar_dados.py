# -*- coding: utf-8 -*-
"""
01_preparar_dados.py — FOMEZERO · VCIA
Nicho: Triagem visual de hortifrúti excedente antes do cadastro do lote de doação

Prepara a base AgriFreshNET (Mendeley Data, DOI 10.17632/42m5tb7yv9.1, CC BY 4.0) e faz a
divisão treino / validação / teste SEM VAZAMENTO [§2.1; REQ-VCIA-08, 10, 11, 15]:

1. Lê as 24 pastas (8 produtos x 3 estágios: Fresh, Semi-Fresh, Rotten).
2. Separa as fotos ORIGINAIS das variações geradas pelos autores ("aug_<n>_<original>").
3. Define o GRUPO DE ORIGEM de cada arquivo:
   - nomes com data/hora (IMG_AAAAMMDD_HHMMSS...) -> sessão = data + hora + minuto
     (rajadas do mesmo item ou da mesma bancada ficam juntas);
   - outros nomes -> pasta + nome original;
   - fotos originais IDÊNTICAS (dHash igual) em qualquer lugar -> mesmo grupo.
4. Exclui as fotos com RÓTULO CONFLITANTE (a mesma foto em duas pastas de estágio) e as aug_ delas.
5. Divide POR GRUPO com StratifiedGroupKFold (20 dobras: 3 teste, 3 validação, 14 treino ~ 70/15/15),
   estratificando por produto x estágio.
6. Validação e teste recebem SÓ originais; as aug_ entram só no treino, e só as dos grupos de treino.
7. Verifica automaticamente que nenhum grupo aparece em dois conjuntos e grava as evidências.

Uso: python 01_preparar_dados.py <pasta "Processed Data"> <pasta de saída das evidências>
"""
import sys, os, re, json, csv, collections
from PIL import Image
from sklearn.model_selection import StratifiedGroupKFold

RAIZ, SAIDA = sys.argv[1], sys.argv[2]
SEMENTE = 42
os.makedirs(SAIDA, exist_ok=True)

# Nomes internos (sem acento) e nomes de exibição dos produtos
PRODUTOS = {'banana': 'banana', 'bittermelon': 'melão-de-são-caetano', 'cucumber': 'pepino',
            'eggplant': 'berinjela', 'orange': 'laranja', 'papaya': 'mamão',
            'pineapple': 'abacaxi', 'tomato': 'tomate'}
ESTAGIOS = ['Fresh', 'Semi-Fresh', 'Rotten']   # ordem fixa das classes de condição


def estagio_da_pasta(p):
    p = p.lower()
    if 'semi' in p:
        return 'Semi-Fresh'
    return 'Rotten' if 'rotten' in p else 'Fresh'


def produto_da_pasta(p):
    for k in PRODUTOS:
        if k in p.lower():
            return k
    raise ValueError(f'produto não reconhecido: {p}')


def dhash(caminho, n=8):
    """Hash de diferença (64 bits): só para achar fotos IDÊNTICAS, não para agrupar parecidas."""
    g = Image.open(caminho).convert('L').resize((n + 1, n))
    px = g.tobytes()
    bits = 0
    for y in range(n):
        for x in range(n):
            bits = (bits << 1) | (px[y * (n + 1) + x] > px[y * (n + 1) + x + 1])
    return bits


RE_SESSAO = re.compile(r'(\d{8})_(\d{4})\d{2}')   # IMG_20251104_131910090 -> 20251104_1319

# ---------------------------------------------------------------- 1-3. inventário e grupos
itens = []
for pasta in sorted(os.listdir(RAIZ)):
    est, prod = estagio_da_pasta(pasta), produto_da_pasta(pasta)
    for arq in sorted(os.listdir(os.path.join(RAIZ, pasta))):
        orig = re.sub(r'^aug_\d+_', '', arq)
        m = RE_SESSAO.search(orig)
        grupo = f'S:{m.group(1)}_{m.group(2)}' if m else f'N:{pasta}/{orig}'
        itens.append(dict(caminho=f'{pasta}/{arq}', pasta=pasta, original=orig, aug=arq.startswith('aug_'),
                          estagio=est, produto=prod, rotulo=f'{prod}|{est}', grupo=grupo))

# hash das ORIGINAIS (as aug_ herdam o grupo da original pelo nome)
hash_orig = {}
for it in itens:
    if not it['aug']:
        hash_orig[(it['pasta'], it['original'])] = dhash(os.path.join(RAIZ, it['caminho']))

# ---------------------------------------------------------------- 4. rótulo conflitante
# mesma foto (dHash IDÊNTICO, distância 0) em pastas de ESTÁGIO diferente do mesmo produto
# -> a foto tem dois rótulos: excluir as duas cópias e as aug_ delas.
# Distância 0 e não <= 2: na conferência visual de 16/11, os pares com distância 2 eram fotos
# DIFERENTES (melão-de-são-caetano, tomate) sobre o mesmo pano branco; os de distância 0 eram iguais.
LIMIAR_IDENTICA = 0
por_hash = collections.defaultdict(list)
for (pasta, orig), h in hash_orig.items():
    por_hash[h].append((pasta, orig))
conflitos = set()
por_produto = collections.defaultdict(list)
for (pasta, orig), h in hash_orig.items():
    por_produto[produto_da_pasta(pasta)].append((pasta, orig, h))
for prod, lst in por_produto.items():
    for i in range(len(lst)):
        for j in range(i + 1, len(lst)):
            (pa, oa, ha), (pb, ob, hb) = lst[i], lst[j]
            if estagio_da_pasta(pa) != estagio_da_pasta(pb) and bin(ha ^ hb).count('1') <= LIMIAR_IDENTICA:
                conflitos.update([(pa, oa), (pb, ob)])
excluidos = [it for it in itens if (it['pasta'], it['original']) in conflitos]
itens = [it for it in itens if (it['pasta'], it['original']) not in conflitos]

# fotos idênticas restantes (mesmo estágio, nomes diferentes) -> unir grupos (union-find)
pai = {}
def acha(g):
    pai.setdefault(g, g)
    while pai[g] != g:
        pai[g] = pai[pai[g]]
        g = pai[g]
    return g
grupo_de = {(it['pasta'], it['original']): it['grupo'] for it in itens}
uniões = 0
for h, lst in por_hash.items():
    gs = [grupo_de[k] for k in lst if k in grupo_de]
    for g in gs[1:]:
        a, b = acha(gs[0]), acha(g)
        if a != b:
            pai[a] = b
            uniões += 1
for it in itens:
    it['grupo'] = acha(it['grupo'])

# ---------------------------------------------------------------- 5. divisão por grupo
originais = [it for it in itens if not it['aug']]
X = list(range(len(originais)))
y = [it['rotulo'] for it in originais]
g = [it['grupo'] for it in originais]
skf = StratifiedGroupKFold(n_splits=20, shuffle=True, random_state=SEMENTE)
conjunto_do_grupo = {}
for k, (_, idx) in enumerate(skf.split(X, y, g)):
    nome = 'teste' if k < 3 else ('validacao' if k < 6 else 'treino')
    for i in idx:
        conjunto_do_grupo[g[i]] = nome

# ---------------------------------------------------------------- 6. montagem dos conjuntos
conjuntos = {'treino': [], 'validacao': [], 'teste': []}
aug_descartadas = 0
for it in itens:
    c = conjunto_do_grupo.get(it['grupo'])
    if c is None:                 # aug_ cuja original não existe (não deve ocorrer)
        aug_descartadas += 1
        continue
    if it['aug'] and c != 'treino':
        continue                  # validação e teste só com originais
    conjuntos[c].append(it)

# ---------------------------------------------------------------- 7. verificações e evidências
grupos_por_conj = {c: {it['grupo'] for it in v} for c, v in conjuntos.items()}
compartilhados = {
    'treino∩validacao': len(grupos_por_conj['treino'] & grupos_por_conj['validacao']),
    'treino∩teste': len(grupos_por_conj['treino'] & grupos_por_conj['teste']),
    'validacao∩teste': len(grupos_por_conj['validacao'] & grupos_por_conj['teste'])}
orig_por_conj = {c: {(it['pasta'], it['original']) for it in v} for c, v in conjuntos.items()}
originais_compartilhadas = len(orig_por_conj['treino'] & orig_por_conj['teste']) + \
    len(orig_por_conj['treino'] & orig_por_conj['validacao']) + len(orig_por_conj['validacao'] & orig_por_conj['teste'])
assert sum(compartilhados.values()) == 0 and originais_compartilhadas == 0, 'VAZAMENTO entre conjuntos!'
assert all(not it['aug'] for c in ('validacao', 'teste') for it in conjuntos[c]), 'aug_ fora do treino!'

def contagem(lst, chave):
    return dict(sorted(collections.Counter(it[chave] for it in lst).items()))

resumo = {
    'base': 'AgriFreshNET (Mendeley Data, DOI 10.17632/42m5tb7yv9.1, CC BY 4.0)',
    'semente': SEMENTE, 'metodo': 'StratifiedGroupKFold(n_splits=20): dobras 0-2 teste, 3-5 validação, 6-19 treino',
    'arquivos_lidos': len(itens) + len(excluidos),
    'excluidos_rotulo_conflitante': {'arquivos': len(excluidos),
                                     'fotos_originais': sorted({f'{p}/{o}' for p, o in conflitos})},
    'unioes_por_foto_identica': uniões,
    'grupos_de_origem': len(set(conjunto_do_grupo)),
    'grupos_por_conjunto': {c: len(v) for c, v in grupos_por_conj.items()},
    'grupos_compartilhados_entre_conjuntos': compartilhados,
    'originais_compartilhadas_entre_conjuntos': originais_compartilhadas,
    'conjuntos': {c: {'n_arquivos': len(v), 'n_originais': sum(not i['aug'] for i in v),
                      'n_aug': sum(i['aug'] for i in v),
                      'por_estagio_originais': contagem([i for i in v if not i['aug']], 'estagio'),
                      'por_produto_originais': contagem([i for i in v if not i['aug']], 'produto')}
                  for c, v in conjuntos.items()},
    'aug_sem_original': aug_descartadas,
}
with open(os.path.join(SAIDA, 'divisao.json'), 'w', encoding='utf-8') as f:
    json.dump(resumo, f, ensure_ascii=False, indent=1)
for c, v in conjuntos.items():
    with open(os.path.join(SAIDA, f'divisao_{c}.csv'), 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['caminho', 'produto', 'estagio', 'rotulo', 'grupo', 'aug'])
        for it in v:
            w.writerow([it['caminho'], it['produto'], it['estagio'], it['rotulo'], it['grupo'], int(it['aug'])])
print(json.dumps({k: resumo[k] for k in ('arquivos_lidos', 'grupos_de_origem', 'grupos_por_conjunto',
                                         'grupos_compartilhados_entre_conjuntos', 'originais_compartilhadas_entre_conjuntos')},
                 ensure_ascii=False, indent=1))
print('excluídos (rótulo conflitante):', resumo['excluidos_rotulo_conflitante']['arquivos'], 'arquivos de',
      len(conflitos), 'fotos originais')
for c, v in resumo['conjuntos'].items():
    print(c, v['n_arquivos'], 'arquivos |', v['n_originais'], 'originais |', v['por_estagio_originais'])
