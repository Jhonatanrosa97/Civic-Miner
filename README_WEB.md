# 📄 CivicMiner - Aplicação Web

Uma aplicação web para baixar contratos automaticamente do portal de transparência de São José/SC.

## 🚀 Instalação

### 1. Instale as dependências:
```bash
pip install -r requirements.txt
```

### 2. Configure o `config.json`:
```json
{
  "url": "https://saojose.atende.net/...",
  "driver_path": "C:\\path\\to\\chromedriver.exe",
  "search_filters": {
    "fornecedor": "IPM",
    "anos": [2020, 2021, 2022, 2023, 2024, 2025]
  },
  "chrome_binary": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
}
```

## 🏃 Como Usar

### Option 1: Interface Web (Recomendado)
```bash
python app.py
```

Abra no navegador: **http://localhost:5000**

- Clique em "Clique para Baixar PDF"
- Aguarde o download completar
- Os PDFs aparecem em "Arquivos Baixados"
- Você pode fazer download ou deletar os arquivos

### Option 2: Linha de Comando
```bash
python main.py
```

## 📁 Estrutura de Pastas

```
ipm-sistemas-scraper/
├── app.py                 # Aplicação Flask
├── main.py               # Entry point do scraper
├── config.json           # Configurações
├── requirements.txt      # Dependências Python
├── templates/
│   └── index.html        # Interface web
├── scripts/
│   └── ipm_scraper.py    # Lógica do scraper
└── Downloads_PDFs/       # PDFs baixados
```

## ⚙️ Configuração

### ChromeDriver
1. Baixe em: https://chromedriver.chromium.org/
2. Extraia para uma pasta conhecida
3. Atualize o `config.json` com o caminho

### Arquivo config.json Exemplo:
```json
{
  "url": "https://saojose.atende.net/cidadao/portal/...",
  "driver_path": "C:\\Users\\seu_usuario\\Documents\\chromedriver.exe",
  "search_filters": {
    "fornecedor": "IPM",
    "anos": [2020, 2021, 2022, 2023, 2024, 2025]
  },
  "chrome_binary": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
}
```

## 🎯 Funcionalidades

✅ Interface web intuitiva  
✅ Execução em background  
✅ Monitoramento de progresso  
✅ Download automático para Downloads_PDFs  
✅ Gerenciamento de arquivos (download/deletar)  
✅ Sem necessidade de VS Code  

## 🛠️ Troubleshooting

### Erro: "Chrome process exited unexpectedly"
- Verifique se o ChromeDriver versão corresponde ao Chrome
- Adicione a flag `--disable-gpu` nas opções do Chrome

### Erro: "Arquivo config.json não encontrado"
- Certifique-se de criar o `config.json` na pasta raiz
- Use o exemplo acima como referência

### Porta 5000 já está em uso
- Modifique em `app.py`: `app.run(debug=True, port=5001)`

## 📝 Notas

- O scraper busca automaticamente o contrato **89/2022**
- Fornecedor: **[nome do fornecedor configurado]**
- Anos: **2020-2025**
- Baixa apenas PDFs do tipo **Impressão**

Para modificar esses parâmetros, edite `scripts/ipm_scraper.py`

## 📞 Suporte

Se encontrar problemas:
1. Verifique o arquivo `debug_*.html` para ver o estado da página
2. Verifique o arquivo `debug_*.png` para screenshots
3. Veja os logs no terminal/console web

---

**Desenvolvido com ❤️**
