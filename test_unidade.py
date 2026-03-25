#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

# Força UTF-8
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Adiciona scripts ao path
sys.path.insert(0, os.path.dirname(__file__))

import scripts.ipm_scraper as scraper
import time

# Cria o scraper
s = scraper.Scraper('config.json')

# Acessa o portal
try:
    s.acessar_portal()
except KeyboardInterrupt:
    print("\n[INFO] Interrompido pelo usuário")
    s.driver.quit()
except Exception as e:
    print(f"[ERRO] {e}")
    import traceback
    traceback.print_exc()
    s.driver.quit()
