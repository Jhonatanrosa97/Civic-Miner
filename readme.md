# CivicMiner

> Automação inteligente para coleta e download de contratos públicos em portais de transparência municipal.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com)
[![Selenium](https://img.shields.io/badge/Selenium-4.x-orange.svg)](https://selenium.dev)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## O que é

**CivicMiner** é uma ferramenta web construída em Python que automatiza a busca, filtragem e download de PDFs de contratos públicos em portais de transparência municipal do Brasil. Com uma interface simples, é possível consultar qualquer município e obter o contrato mais recente disponível no portal.

## Funcionalidades

- 🌐 **Interface Web** — Dashboard moderno com autenticação, histórico e gerenciamento de arquivos
- 🔍 **Busca por cidade** — Suporte a qualquer município com portal de transparência compatível
- 📄 **Download automático de PDF** — Detecta e baixa o arquivo de contrato mais recente
- ⏹️ **Cancelamento em tempo real** — Interrompe o scraper e fecha o navegador com um clique
- ⚠️ **Avisos inteligentes** — Informa quando um contrato não possui anexos disponíveis
- 🗂️ **Gerenciamento de arquivos** — Lista, baixa e exclui contratos direto pela interface
- 🌙 **Modo escuro** — Tema alternativo persistente

## Tecnologias

| Camada | Tecnologia |
|--------|------------|
| Backend web | Flask (Python) |
| Automação de browser | Selenium 4 + ChromeDriver |
| Frontend | HTML/CSS/JS (sem frameworks) |
| Execução paralela | Threading (subprocess) |

## Instalação rápida

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/civicminer.git
cd civicminer

# 2. Crie e ative o ambiente virtual
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 3. Instale as dependências
pip install -r requirements.txt
```

> **Requisito:** Google Chrome instalado e ChromeDriver 143 no PATH ou na raiz do projeto.  
> Download: https://googlechromelabs.github.io/chrome-for-testing/

## Como usar

### Interface Web (recomendado)

```bash
python app.py
```

Acesse `http://localhost:5000`, faça login, digite o nome da cidade e clique em **"Clique para Baixar PDF"**.

### Linha de comando

```bash
python main.py
```

Edite `config.json` com a URL do município desejado antes de executar.

## Estrutura do projeto

```
civicminer/
├── app.py               # Servidor Flask + API
├── main.py              # Entrada do scraper (CLI)
├── config.json          # Configuração padrão
├── requirements.txt     # Dependências
├── scripts/
│   └── ipm_scraper.py   # Engine de automação (Selenium)
├── templates/
│   └── index.html       # Interface web (CivicMiner)
├── Downloads_PDFs/      # Contratos baixados
└── logs/                # Logs de execução
```

## Configuração (`config.json`)

```json
{
    "url": "https://CIDADE.atende.net/transparencia/item/contratos-gerais",
    "driver_path": "chromedriver",
    "search_filters": {
        "tipo_pessoa": "Fornecedor - Nome Razão",
        "anos": ["2022", "2023", "2024", "2025"]
    }
}
```

## API REST

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/api/executar` | Inicia o scraper para uma cidade |
| `GET` | `/api/status` | Retorna progresso e mensagem atual |
| `POST` | `/api/cancelar` | Cancela e fecha o navegador |
| `GET` | `/api/arquivos` | Lista contratos baixados |
| `GET` | `/api/download/<nome>` | Faz download de um arquivo |
| `DELETE` | `/api/arquivos/<nome>` | Remove um arquivo |

## Contribuindo

Pull requests são bem-vindos! Abra uma issue primeiro para discutir mudanças maiores.

## Licença

MIT — veja o arquivo [LICENSE](LICENSE) para detalhes.

## Como usar

1. Instale as dependências:
