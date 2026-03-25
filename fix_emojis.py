# -*- coding: utf-8 -*-
import sys

# Read the file in binary mode and decode
with open('scripts/ipm_scraper.py', 'rb') as f:
    content = f.read().decode('utf-8')

# Replace emojis with text equivalents
replacements = [
    (u'\u2713', '[OK]'),         # ✓
    (u'\u274C', '[ERRO]'),        # ❌
    (u'\u26A0\uFE0F', '[AVISO]'), # ⚠️
    (u'\u26A0', '[AVISO]'),       # ⚠
    (u'\U0001F3AF', '>>'),        # 🎯
]

for emoji, text in replacements:
    content = content.replace(emoji, text)

# Write back in binary mode
with open('scripts/ipm_scraper.py', 'wb') as f:
    f.write(content.encode('utf-8'))

print("Done")
