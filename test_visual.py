#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

# Force UTF-8
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(__file__))

import scripts.ipm_scraper as scraper

print("=" * 70)
print("IPM SCRAPER - TESTE DE SELECAO DE UNIDADE GESTORA")
print("=" * 70)
print("\nFUNCIONAMENTO:")
print("1. O navegador abrira o site IPM SISTEMAS")
print("2. Quando aparecer o CAPTCHA, resolva manualmente")
print("3. Apos resolver, o scraper continuara automaticamente")
print("4. O scraper testara a selecao de MUNICIPIO/PREFEITURA")
print("\n" + "=" * 70 + "\n")

try:
    s = scraper.Scraper('config.json')
    print("[*] Iniciando acesso ao portal...")
    s.acessar_portal()
    print("\n[OK] Script executado com sucesso!")
except KeyboardInterrupt:
    print("\n\n[INFO] Interrompido pelo usuario")
    s.driver.quit()
except Exception as e:
    print(f"\n[ERRO] {e}")
    import traceback
    traceback.print_exc()
    try:
        s.driver.quit()
    except:
        pass
