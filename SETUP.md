# 🚀 CivicMiner - Guia de Uso

## Instalação

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Verificar ChromeDriver
- Certifique-se de que o ChromeDriver versão 143 está no PATH ou em `scripts/`
- Baixe em: https://googlechromelabs.github.io/chrome-for-testing/

## Uso

### Opção 1: Interface Web (Recomendado) ✨

```bash
python app.py
```

- Acesse: http://localhost:5000
- Digite o nome da cidade (ex: São José, Palhoça, Brusque)
- Clique em "Clique para Baixar PDF"
- Os arquivos serão salvos em `Downloads_PDFs/`

### Opção 2: Linha de Comando

```bash
# Com cidade São José (padrão)
python main.py

# Com outra cidade
# (Primeiro edite o config.json com a URL desejada)
python main.py config.json
```

### Opção 3: Teste Automatizado

```bash
python test_scraper.py
```

Testa automaticamente com múltiplas cidades (São José, Palhoça, Brusque).

## Estrutura de Arquivos

```
civicminer/
├── app.py                    # Servidor Flask (web)
├── main.py                   # Entrada principal
├── config.json               # Configuração de cidade/filtros
├── test_scraper.py           # Script de teste automatizado
├── requirements.txt          # Dependências Python
├── scripts/
│   ├── ipm_scraper.py        # Engine de automação (Selenium)
│   └── __pycache__/
├── templates/
│   └── index.html            # Interface web (CivicMiner)
├── Downloads_PDFs/           # Pasta de downloads
├── logs/                     # Logs de execução
└── README.md                 # Este arquivo
```

## Configuração

### config.json
```json
{
    "url": "https://saojose.atende.net/transparencia/item/contratos-gerais",
    "driver_path": "scripts/chromedriver",
    "search_filters": {
        "tipo_pessoa": "Fornecedor - Nome Razão",
        "anos": ["2020", "2021", "2022", "2023", "2024", "2025"]
    },
    "chrome_binary": "chrome"
}
```

## Formatação de Cidades

A aplicação automaticamente:
- Remove acentos: "São José" → "saojose"
- Converte para lowercase
- Remove espaços e caracteres especiais
- Gera URL: `https://{cidade}.atende.net/transparencia/item/contratos-gerais`

## Possíveis Erros

### ChromeDriver não encontrado
```
FileNotFoundError: chromedriver
```
**Solução:** Baixe o ChromeDriver 143 correspondente ao seu SO

### Versão do Chrome não compatível
```
Message: session not created: Chrome version must be between X and Y
```
**Solução:** Atualize o Chrome ou baixe ChromeDriver compatível

### Portal não responde
```
TimeoutException
```
**Solução:** Verifique sua conexão e se a URL é válida

### PDF não baixa
1. Verifique se a pasta `Downloads_PDFs/` tem permissão de escrita
2. Teste com `test_scraper.py`
3. Verifique os logs em `logs/`

## Dicas

✅ A interface web (`app.py`) é mais fácil e não requer terminal
✅ Use `test_scraper.py` para diagnosticar problemas
✅ Os PDFs são salvos automaticamente em `Downloads_PDFs/`
✅ Você pode deletar e fazer download via interface web
✅ Chrome deve estar atualizado (versão 143+)

## Cidades Testadas

- São José
- Palhoça  
- Brusque

(Outras cidades podem funcionar se tiverem o portal no formato `https://{cidade}.atende.net/...`)

---

**Última atualização:** 2024
**Versão:** 2.0 (com suporte a múltiplas cidades)
