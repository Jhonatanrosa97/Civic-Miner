#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TESTE SUPER SIMPLES - Com input forçado
"""

import sys
import os

print("\n" + "="*60)
print("QUAL CIDADE?")
print("="*60)
print("\nOpções: São José, Palhoça, Brusque, etc.")
print("\nDIGITE AGORA:")

cidade = input("> ").strip()

if not cidade:
    print("\n❌ ERRO: Você não digitou nada!")
    sys.exit(1)

print(f"\n✓ Você escolheu: {cidade}")
print("Aguarde... o navegador vai abrir")
print("="*60 + "\n")

# Agora executa o scraper
import unicodedata
import re
import json
from scripts.ipm_scraper import Scraper

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_FOLDER = os.path.join(PROJECT_ROOT, "Downloads_PDFs")

def formatar_cidade(cidade):
    """Formata o nome da cidade para URL"""
    nfd = unicodedata.normalize('NFD', cidade)
    sem_acentos = ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')
    formatada = re.sub(r'[^a-z0-9]', '', sem_acentos.lower())
    return formatada

# Formata cidade
cidade_formatada = formatar_cidade(cidade)
print(f"Cidade formatada: {cidade_formatada}")

# Lê config original
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.json")
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = json.load(f)

# Modifica URL
config['url'] = f"https://{cidade_formatada}.atende.net/transparencia/item/contratos-gerais"
print(f"URL: {config['url']}\n")

# Salva temp
temp_config = os.path.join(PROJECT_ROOT, "config_temp.json")
with open(temp_config, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=4)

# Conta antes
arquivos_antes = len(os.listdir(DOWNLOADS_FOLDER))

try:
    # Executa
    scraper = Scraper(temp_config)
    scraper.run()
except Exception as e:
    print(f"Erro: {e}")
finally:
    # Remove temp
    try:
        os.remove(temp_config)
    except:
        pass

# Conta depois
arquivos_depois = len(os.listdir(DOWNLOADS_FOLDER))

print("\n" + "="*60)
if arquivos_depois > arquivos_antes:
    print(f"✅ SUCESSO! {arquivos_depois - arquivos_antes} PDF(s) baixado(s)")
else:
    print(f"❌ FALHA! Nenhum PDF foi baixado")
print("="*60 + "\n")
