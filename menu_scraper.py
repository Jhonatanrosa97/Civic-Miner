#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SCRIPT SUPER SIMPLES COM MENU
"""

import sys
import os
import json
import unicodedata
import re

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from scripts.ipm_scraper import Scraper

DOWNLOADS_FOLDER = os.path.join(PROJECT_ROOT, "Downloads_PDFs")
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.json")

def formatar_cidade(cidade):
    nfd = unicodedata.normalize('NFD', cidade)
    sem_acentos = ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')
    return re.sub(r'[^a-z0-9]', '', sem_acentos.lower())

print("\n" + "="*70)
print(" "*20 + "SCRAPER DE CONTRATOS IPM")
print("="*70)

print("\nEscolha uma cidade:")
print("\n  1 = São José")
print("  2 = Palhoça")
print("  3 = Brusque")
print("  4 = Outra (digitar manualmente)")

print("\n" + "-"*70)
escolha = input("Escolha (1, 2, 3 ou 4): ").strip()
print("-"*70)

cidades_predefinidas = {
    "1": "São José",
    "2": "Palhoça",
    "3": "Brusque"
}

if escolha in cidades_predefinidas:
    cidade = cidades_predefinidas[escolha]
    print(f"\n✓ Você escolheu: {cidade}")
elif escolha == "4":
    print("\nDigite o nome da cidade:")
    cidade = input("Cidade: ").strip()
    if not cidade:
        print("❌ Erro: Cidade vazia!")
        sys.exit(1)
    print(f"✓ Você escolheu: {cidade}")
else:
    print(f"❌ Erro: Opção inválida '{escolha}'")
    sys.exit(1)

# Formata
cidade_formatada = formatar_cidade(cidade)
print(f"Formatada: {cidade_formatada}")

# Config
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = json.load(f)

config['url'] = f"https://{cidade_formatada}.atende.net/transparencia/item/contratos-gerais"
print(f"URL: {config['url']}")

# Temp config
temp_config = os.path.join(PROJECT_ROOT, "config_temp.json")
with open(temp_config, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=4)

# Conta
os.makedirs(DOWNLOADS_FOLDER, exist_ok=True)
arquivos_antes = len(os.listdir(DOWNLOADS_FOLDER))

print("\n" + "="*70)
print("Aguarde... O NAVEGADOR VAI ABRIR EM ALGUNS SEGUNDOS...")
print("="*70 + "\n")

try:
    scraper = Scraper(temp_config)
    scraper.run()
except Exception as e:
    print(f"❌ Erro: {e}")
finally:
    try:
        os.remove(temp_config)
    except:
        pass

# Resultado
arquivos_depois = len(os.listdir(DOWNLOADS_FOLDER))
novos = arquivos_depois - arquivos_antes

print("\n" + "="*70)
if novos > 0:
    print(f"✅ SUCESSO! {novos} PDF(s) baixado(s) para {cidade}")
    arquivos = sorted(os.listdir(DOWNLOADS_FOLDER))[-novos:]
    for arq in arquivos:
        tamanho = os.path.getsize(os.path.join(DOWNLOADS_FOLDER, arq))
        print(f"   📄 {arq} ({tamanho/1024:.1f} KB)")
else:
    print(f"❌ FALHA! Nenhum PDF foi baixado para {cidade}")
    print("\nVerifique:")
    print("  - O site abriu?")
    print("  - Clicou no botão 'Baixar'?")
    print("  - O PDF apareceu na tela?")
print("="*70 + "\n")
