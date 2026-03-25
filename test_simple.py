#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script simples para testar a conexão e download
Pede a cidade antes de executar
"""

import sys
import os
import unicodedata
import re

# Adiciona o projeto ao path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from scripts.ipm_scraper import Scraper
import json

def formatar_cidade(cidade):
    """Formata o nome da cidade para URL"""
    nfd = unicodedata.normalize('NFD', cidade)
    sem_acentos = ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')
    formatada = re.sub(r'[^a-z0-9]', '', sem_acentos.lower())
    return formatada

def main():
    print("\n" + "="*60)
    print("TESTE SIMPLES DO SCRAPER")
    print("="*60)
    
    # Pede a cidade
    print("\nQual cidade deseja usar?")
    print("Exemplos: São José, Palhoça, Brusque, etc.")
    cidade = input("\nDigite a cidade: ").strip()
    
    if not cidade:
        print("\n❌ Erro: Cidade não informada")
        return
    
    CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.json")
    DOWNLOADS_FOLDER = os.path.join(PROJECT_ROOT, "Downloads_PDFs")
    
    print(f"\n[1] Verificando arquivos...")
    print(f"  - Config: {CONFIG_PATH}")
    print(f"  - Existe? {os.path.exists(CONFIG_PATH)}")
    print(f"  - Download folder: {DOWNLOADS_FOLDER}")
    
    print(f"\n[2] Criando pasta de downloads...")
    os.makedirs(DOWNLOADS_FOLDER, exist_ok=True)
    print(f"  ✓ Pasta criada/verificada")
    
    print(f"\n[3] Lendo config.json...")
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"  ✓ Config lido com sucesso")
    except Exception as e:
        print(f"  ✗ Erro ao ler config: {e}")
        return
    
    print(f"\n[4] Formatando cidade...")
    cidade_formatada = formatar_cidade(cidade)
    url_nova = f"https://{cidade_formatada}.atende.net/transparencia/item/contratos-gerais"
    config['url'] = url_nova
    print(f"  - Cidade original: {cidade}")
    print(f"  - Cidade formatada: {cidade_formatada}")
    print(f"  - URL nova: {url_nova}")
    
    print(f"\n[5] Salvando config temporário...")
    temp_config = os.path.join(PROJECT_ROOT, "config_temp_test.json")
    try:
        with open(temp_config, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        print(f"  ✓ Config temporário salvo")
    except Exception as e:
        print(f"  ✗ Erro ao salvar: {e}")
        return
    
    print(f"\n[6] Contando arquivos antes...")
    arquivos_antes = len(os.listdir(DOWNLOADS_FOLDER))
    print(f"  - Arquivos antes: {arquivos_antes}")
    
    print(f"\n[7] Inicializando Scraper...")
    try:
        scraper = Scraper(temp_config)
        print(f"  ✓ Scraper inicializado")
    except Exception as e:
        print(f"  ✗ Erro ao inicializar: {e}")
        import traceback
        traceback.print_exc()
        try:
            os.remove(temp_config)
        except:
            pass
        return
    
    print(f"\n[8] Executando scraper.run()...")
    print(f"  (Aguarde... o navegador vai abrir)")
    try:
        scraper.run()
        print(f"  ✓ Run concluído")
    except Exception as e:
        print(f"  ✗ Erro durante run: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n[9] Contando arquivos depois...")
    arquivos_depois = len(os.listdir(DOWNLOADS_FOLDER))
    print(f"  - Arquivos depois: {arquivos_depois}")
    print(f"  - Novos arquivos: {arquivos_depois - arquivos_antes}")
    
    if arquivos_depois > arquivos_antes:
        print(f"\n✅ SUCESSO! PDF foi baixado para {cidade}!")
        arquivos = os.listdir(DOWNLOADS_FOLDER)
        for arq in sorted(arquivos)[-3:]:  # Mostra últimos 3
            caminho = os.path.join(DOWNLOADS_FOLDER, arq)
            tamanho = os.path.getsize(caminho)
            print(f"  - {arq} ({tamanho / 1024:.2f} KB)")
    else:
        print(f"\n❌ FALHA! Nenhum PDF foi baixado para {cidade}")
    
    print(f"\n[10] Limpando config temporário...")
    try:
        os.remove(temp_config)
        print(f"  ✓ Config temporário removido")
    except:
        pass
    
    print("\n" + "="*60)
    print("FIM DO TESTE")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
