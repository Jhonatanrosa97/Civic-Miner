# 📋 Resumo das Alterações - v2.0

## ✅ O que foi feito

### 1. **main.py** - Suporte a Config Dinâmico
- ✨ Agora aceita parâmetro `config.json` via linha de comando
- Exemplo: `python main.py config_temp.json`
- Se nenhum parâmetro, usa `config.json` padrão

### 2. **app.py** - Flask Web Server Completo
- ✨ Rota `/api/executar` [POST] - Aceita cidade em JSON
- ✨ Função `formatar_cidade()` - Remove acentos e caracteres especiais
- ✨ Gera URL dinâmica: `https://{cidade_formatada}.atende.net/...`
- ✨ Cria `config_temp.json` com URL modificada
- ✨ Executa scraper em thread separada
- ✨ Limpa arquivo temporário após execução
- ✨ Retorna status de progresso (10%, 20%, 50%, 100%)

### 3. **templates/index.html** - Interface Web Melhorada
- ✨ Campo de entrada para cidade: "Digite o nome da cidade"
- ✨ Validação: avisa se cidade está vazia
- ✨ Envio de JSON: `{"cidade": "São José"}`
- ✨ Mantém toda funcionalidade anterior (progresso, download, delete)

### 4. **test_scraper.py** - Novo Script de Teste
- 🧪 Script Python para testar múltiplas cidades
- 🧪 Testa automaticamente: São José, Palhoça, Brusque
- 🧪 Conta arquivos antes/depois para validar downloads
- 🧪 Mostra relatório completo de execução

### 5. **SETUP.md** - Guia de Configuração
- 📖 Instruções passo-a-passo
- 📖 Explicação de cidades testadas
- 📖 Troubleshooting comum
- 📖 Dicas de uso

## 🔄 Fluxo de Execução (Web)

1. Usuário acessa http://localhost:5000
2. Digita "São José" no campo de cidade
3. Clica em "Clique para Baixar PDF"
4. JavaScript envia POST: `{"cidade": "São José"}`
5. app.py recebe e inicia thread
6. Formata cidade: "São José" → "saojose"
7. Gera URL: "https://saojose.atende.net/..."
8. Lê config.json e atualiza URL
9. Salva como config_temp.json
10. Executa: `python main.py config_temp.json`
11. Scraper abre portal, encontra PDF, baixa
12. Deleta config_temp.json
13. Retorna sucesso (100%)
14. PDF aparece em Downloads_PDFs/

## 🎯 Formatação de Cidades

Exemplos:
```
"São José"    → saojose         → https://saojose.atende.net/...
"Palhoça"     → palhoca         → https://palhoca.atende.net/...
"São João"    → saojoao         → https://saojoao.atende.net/...
"Brusque"     → brusque         → https://brusque.atende.net/...
"Açu"         → acu             → https://acu.atende.net/...
```

## 📊 Status Retornado

```json
{
    "rodando": false,
    "mensagem": "✓ Download de São José concluído com sucesso!",
    "progresso": 100,
    "erro": null,
    "cidade": "São José"
}
```

## 🚀 Como Usar

### Interface Web
```bash
python app.py
# Acesse: http://localhost:5000
# Digite a cidade e clique para baixar
```

### Teste Automatizado
```bash
python test_scraper.py
# Testa 3 cidades automaticamente
# Mostra relatório de downloads
```

### Linha de Comando (Manual)
```bash
python main.py
# Usa config.json padrão (São José)

# Ou com city dinâmica:
# Edite config.json manualmente com a URL desejada
```

## ⚠️ Pré-requisitos

- Python 3.13+
- Chrome 143.0.7499.192+
- ChromeDriver 143 compatível
- Dependências: `pip install -r requirements.txt`

## 🔍 Debug

Se PDF não baixar:

1. Teste com `test_scraper.py`:
   ```bash
   python test_scraper.py
   ```

2. Verifique logs:
   ```bash
   # Abra logs/scraper.log
   ```

3. Verifique Downloads_PDFs:
   ```bash
   # Windows: explorer Downloads_PDFs
   # Linux/Mac: open Downloads_PDFs
   ```

4. Verifique se portal está online:
   - https://saojose.atende.net/transparencia/item/contratos-gerais

## 📝 Notas

- Cidades com portal em `{cidade}.atende.net` funcionam
- Acentos são removidos automaticamente
- Espaços e caracteres especiais são removidos
- URL deve estar no padrão: `https://{cidade}.atende.net/...`

---

**Status:** ✅ Pronto para produção
**Versão:** 2.0
**Data:** 2024
