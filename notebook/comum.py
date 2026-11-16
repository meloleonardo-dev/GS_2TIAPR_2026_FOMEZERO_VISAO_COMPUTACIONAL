# -*- coding: utf-8 -*-
"""
comum.py — FOMEZERO · VCIA (definições compartilhadas por treino, avaliação, desempenho e app)
Nicho: Triagem visual de hortifrúti excedente antes do cadastro do lote de doação

- 24 classes = 8 produtos x 3 estágios (Fresh, Semi-Fresh, Rotten) da base AgriFreshNET.
- O modelo dá uma probabilidade para cada uma das 24 classes. A partir delas:
    condição (3)  = soma das probabilidades de cada estágio sobre os 8 produtos;
    produto  (8)  = soma das probabilidades de cada produto sobre os 3 estágios.
- Textos de tela fixados pela DEC-023 do CENTRAL (não alterar sem nova decisão).
"""
import csv, os
import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms

NICHO = 'Triagem visual de hortifrúti excedente antes do cadastro do lote de doação'
AVISO = ('Apoio à triagem visual. A imagem não atesta que o alimento é seguro para consumo; '
         'a decisão é do doador e da vigilância sanitária.')

PRODUTOS = ['banana', 'bittermelon', 'cucumber', 'eggplant', 'orange', 'papaya', 'pineapple', 'tomato']
PRODUTO_PT = {'banana': 'banana', 'bittermelon': 'melão-de-são-caetano', 'cucumber': 'pepino',
              'eggplant': 'berinjela', 'orange': 'laranja', 'papaya': 'mamão',
              'pineapple': 'abacaxi', 'tomato': 'tomate'}
ESTAGIOS = ['Fresh', 'Semi-Fresh', 'Rotten']
CONDICAO_PT = {'Fresh': 'sem sinais visuais de deterioração',
               'Semi-Fresh': 'sinais visuais leves — priorizar uso rápido e avaliar pessoalmente',
               'Rotten': 'sinais visuais de deterioração — sugestão: compostagem'}
INCONCLUSIVO = 'inconclusivo — avaliar pessoalmente'
CLASSES = [f'{p}|{e}' for p in PRODUTOS for e in ESTAGIOS]          # índice 0..23
IDX = {c: i for i, c in enumerate(CLASSES)}

TAMANHO = 224                                    # entrada do modelo (a base vem em 512x512)
MEDIA, DESVIO = [0.485, 0.456, 0.406], [0.229, 0.224, 0.225]   # normalização ImageNet

# matrizes de agregação 24 -> 3 (condição) e 24 -> 8 (produto)
AGG_COND = torch.zeros(len(CLASSES), len(ESTAGIOS))
AGG_PROD = torch.zeros(len(CLASSES), len(PRODUTOS))
for i, c in enumerate(CLASSES):
    p, e = c.split('|')
    AGG_COND[i, ESTAGIOS.index(e)] = 1
    AGG_PROD[i, PRODUTOS.index(p)] = 1

TF_TREINO = transforms.Compose([
    transforms.RandomResizedCrop(TAMANHO, scale=(0.7, 1.0)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(15),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.1),
    transforms.ToTensor(), transforms.Normalize(MEDIA, DESVIO)])
TF_AVAL = transforms.Compose([
    transforms.Resize((TAMANHO, TAMANHO)),
    transforms.ToTensor(), transforms.Normalize(MEDIA, DESVIO)])


def criar_modelo(nome, pretreinado=True):
    """CNN pré-treinada no ImageNet (torchvision) com a última camada trocada para 24 classes."""
    if nome == 'efficientnet_b0':
        m = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.IMAGENET1K_V1 if pretreinado else None)
        m.classifier[1] = nn.Linear(m.classifier[1].in_features, len(CLASSES))
    elif nome == 'mobilenet_v3_large':
        m = models.mobilenet_v3_large(weights=models.MobileNet_V3_Large_Weights.IMAGENET1K_V2 if pretreinado else None)
        m.classifier[3] = nn.Linear(m.classifier[3].in_features, len(CLASSES))
    else:
        raise ValueError(nome)
    return m


def carregar_modelo(caminho_pesos, nome, dispositivo):
    m = criar_modelo(nome, pretreinado=False)
    m.load_state_dict(torch.load(caminho_pesos, map_location=dispositivo, weights_only=True))
    return m.to(dispositivo).eval()


def ler_divisao(caminho_csv):
    with open(caminho_csv, encoding='utf-8') as f:
        return list(csv.DictReader(f))


class BaseHortifruti(torch.utils.data.Dataset):
    """Lê as linhas de divisao_<conjunto>.csv; devolve (tensor, índice 0..23)."""
    def __init__(self, raiz, linhas, transformacao):
        self.raiz, self.linhas, self.tf = raiz, linhas, transformacao

    def __len__(self):
        return len(self.linhas)

    def __getitem__(self, i):
        l = self.linhas[i]
        img = Image.open(os.path.join(self.raiz, l['caminho'])).convert('RGB')
        return self.tf(img), IDX[l['rotulo']]


def agregar(probs24):
    """probs24: tensor [N,24] -> (probs de condição [N,3], probs de produto [N,8])."""
    return probs24 @ AGG_COND.to(probs24.device), probs24 @ AGG_PROD.to(probs24.device)


def nitidez(img):
    """Variância do laplaciano (4-vizinhos) dividida pelo brilho médio ao quadrado, em tons de cinza 224x224.
    Valor baixo = foto borrada. Calculada no mesmo tamanho da entrada do modelo, para não depender
    da resolução da câmera, e normalizada pelo brilho, para foto escura não parecer borrada.
    Variante escolhida na VALIDAÇÃO entre 4 (bruta, ÷variância, ÷brilho², ÷amplitude²): a bruta recusava
    19% das escurecidas e a ÷variância 20% das com sombra; a ÷brilho² recusa 0,4% e 1,5% (DEC-010).
    Salvaguarda de nitidez (DEC-010): abaixo do limiar, a resposta vira 'inconclusivo' e o app pede outra foto."""
    import numpy as np
    g = np.asarray(img.convert('L').resize((TAMANHO, TAMANHO)), dtype=np.float32)
    lap = 4 * g[1:-1, 1:-1] - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:]
    return float(lap.var() / (g.mean() ** 2 + 1e-6))


MSG_NITIDEZ = ('A foto parece borrada; a triagem visual não sugere condição para ela. '
               'Tire outra foto, com o celular parado e o item em foco.')


def texto_sugerido(classe_pt, confianca):
    """Texto que pré-preenche 'Condição informada pelo doador' (DEC-023: nunca 'confirmado')."""
    return f'Sugestão da triagem visual (confiança {confianca * 100:.0f}%): {classe_pt}'
