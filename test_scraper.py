#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para testar o scraper com cidades diferentes
"""

import subprocess
import os
import json
import time
from pathlib import Path
import unicodedata
import re

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_FOLDER = os.path.join(PROJECT_ROOT, "Downloads_PDFs")
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.json")

def formatar_cidade(cidade):
    """Formata o nome da cidade para URL"""
    nfd = unicodedata.normalize('NFD', cidade)
    sem_acentos = ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')
    formatada = re.sub(r'[^a-z0-9]', '', sem_acentos.lower())
    return formatada

def testar_cidade(cidade):
    """Testa o download para uma cidade específica"""
    print(f"\n{'='*60}")
    print(f"Testando: {cidade}")
    print(f"{'='*60}")
    
    try:
        # Formata a cidade
        cidade_formatada = formatar_cidade(cidade)
        url_base = f"https://{cidade_formatada}.atende.net/transparencia/item/contratos-gerais"
        
        print(f"Cidade original: {cidade}")
        print(f"Cidade formatada: {cidade_formatada}")
        print(f"URL: {url_base}")
        
        # Lê o config.json
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Atualiza a URL
        config['url'] = url_base
        
        # Salva o config temporário
        temp_config_path = os.path.join(PROJECT_ROOT, 'config_temp.json')
        with open(temp_config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        
        # Conta arquivos antes
        arquivos_antes = len(os.listdir(DOWNLOADS_FOLDER)) if os.path.exists(DOWNLOADS_FOLDER) else 0
        
        print(f"\nArquivos antes: {arquivos_antes}")
        print("Executando scraper...")
        
        # Executa o scraper
        processo = subprocess.Popen(
            ["python", "main.py", temp_config_path],
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = processo.communicate()
        
        # Limpa o config temporário
        try:
            os.remove(temp_config_path)
        except:
            pass
        
        # Conta arquivos depois
        arquivos_depois = len(os.listdir(DOWNLOADS_FOLDER)) if os.path.exists(DOWNLOADS_FOLDER) else 0
        
        print(f"Arquivos depois: {arquivos_depois}")
        
        if processo.returncode == 0:
            print(f"✅ Sucesso! Novos arquivos: {arquivos_depois - arquivos_antes}")
            if arquivos_depois > arquivos_antes:
                # Lista os novos arquivos
                arquivos = os.listdir(DOWNLOADS_FOLDER)
                print(f"Arquivos: {arquivos[-1] if arquivos else 'Nenhum'}")
        else:
            print(f"❌ Falha no scraper")
            print(f"STDERR:\n{stderr}")
        
        print(f"Retorno: {processo.returncode}")
        
    except Exception as e:
        print(f"❌ Erro ao testar: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Cria a pasta de downloads se não existir
    os.makedirs(DOWNLOADS_FOLDER, exist_ok=True)
    
    # Testa com algumas cidades
    cidades = [
        "São José",
        "Palhoça",
        "Brusque"
    ]
    
    for cidade in cidades:
        testar_cidade(cidade)
        time.sleep(2)  # Aguarda 2 segundos entre testes
    
    print(f"\n{'='*60}")
    print("Testes concluídos!")
    print(f"{'='*60}")
    print(f"\nArquivos no Downloads_PDFs:")
    if os.path.exists(DOWNLOADS_FOLDER):
        arquivos = os.listdir(DOWNLOADS_FOLDER)
        if arquivos:
            for arquivo in arquivos:
                caminho = os.path.join(DOWNLOADS_FOLDER, arquivo)
                tamanho = os.path.getsize(caminho)
                print(f"  - {arquivo} ({tamanho / 1024:.2f} KB)")
        else:
            print("  (vazio)")
    else:
        print("  (pasta não existe)")
