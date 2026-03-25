from flask import Flask, render_template, jsonify, send_file, request
import os
import json
import subprocess
import threading
from pathlib import Path
import unicodedata
import re

app = Flask(__name__)

# Configurações
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_FOLDER = os.path.join(PROJECT_ROOT, "Downloads_PDFs")
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.json")
CANCEL_FLAG_FILE = os.path.join(PROJECT_ROOT, ".cancel_scraper")

# Variável global para armazenar o status
status_execucao = {
    "rodando": False,
    "mensagem": "",
    "progresso": 0,
    "erro": None,
    "cidade": ""
}

# Variável para armazenar o processo em execução
processo_atual = None

def formatar_cidade(cidade):
    """Formata o nome da cidade para URL"""
    # Remove acentos
    nfd = unicodedata.normalize('NFD', cidade)
    sem_acentos = ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')
    
    # Converte para lowercase, remove espaços e caracteres especiais
    formatada = re.sub(r'[^a-z0-9]', '', sem_acentos.lower())
    
    return formatada

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Retorna o status atual da execução"""
    return jsonify(status_execucao)

@app.route('/api/cancelar', methods=['POST'])
def cancelar_scraper():
    """Cancela a execução do scraper"""
    global status_execucao, processo_atual
    
    try:
        if not status_execucao["rodando"]:
            return jsonify({"mensagem": "Nenhum scraper está rodando"}), 400
        
        # Cria arquivo flag para o scraper detectar
        with open(CANCEL_FLAG_FILE, 'w') as f:
            f.write('CANCEL')
        
        # Mata o processo se ainda estiver rodando
        if processo_atual:
            try:
                processo_atual.terminate()  # Tenta terminar graciosamente
                import time
                time.sleep(1)
                if processo_atual.poll() is None:  # Se ainda está rodando
                    processo_atual.kill()  # Força o encerramento
            except:
                pass
        
        status_execucao["rodando"] = False
        status_execucao["mensagem"] = "✗ Operação cancelada pelo usuário"
        status_execucao["erro"] = "Cancelado"
        
        return jsonify({"mensagem": "Scraper cancelado com sucesso"})
    
    except Exception as e:
        print(f"Erro ao cancelar: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route('/api/arquivos')
def get_arquivos():
    """Lista os arquivos baixados"""
    os.makedirs(DOWNLOADS_FOLDER, exist_ok=True)
    
    arquivos = []
    try:
        for arquivo in os.listdir(DOWNLOADS_FOLDER):
            caminho = os.path.join(DOWNLOADS_FOLDER, arquivo)
            if os.path.isfile(caminho):
                tamanho = os.path.getsize(caminho)
                data_mod = os.path.getmtime(caminho)
                arquivos.append({
                    "nome": arquivo,
                    "tamanho": tamanho,
                    "tamanho_formatado": f"{tamanho / (1024*1024):.2f} MB" if tamanho > 1024*1024 else f"{tamanho / 1024:.2f} KB",
                    "data_modificacao": data_mod
                })
    except Exception as e:
        print(f"Erro ao listar arquivos: {e}")
    
    return jsonify(sorted(arquivos, key=lambda x: x['data_modificacao'], reverse=True))

@app.route('/api/executar', methods=['POST'])
def executar_scraper():
    """Executa o scraper em uma thread separada"""
    global status_execucao
    
    try:
        # Obtém a cidade do POST
        data = request.get_json()
        if data is None:
            return jsonify({"erro": "Erro: Não foi enviado JSON válido"}), 400
            
        cidade = data.get('cidade', '').strip() if data else ''
        
        if not cidade:
            return jsonify({"erro": "Cidade não informada"}), 400
        
        if status_execucao["rodando"]:
            return jsonify({"erro": "Scraper já está rodando"}), 400
        
        def rodar_scraper():
            global status_execucao, processo_atual
            try:
                # Remove flag de cancelamento anterior se existir
                if os.path.exists(CANCEL_FLAG_FILE):
                    os.remove(CANCEL_FLAG_FILE)
                # Remove arquivo de erro anterior se existir
                error_file = os.path.join(PROJECT_ROOT, ".scraper_error")
                if os.path.exists(error_file):
                    os.remove(error_file)
                
                status_execucao["rodando"] = True
                status_execucao["cidade"] = cidade
                status_execucao["mensagem"] = f"Iniciando scraper para {cidade}..."
                status_execucao["progresso"] = 10
                status_execucao["erro"] = None
                
                # Formata a cidade
                cidade_formatada = formatar_cidade(cidade)
                url_base = f"https://{cidade_formatada}.atende.net/transparencia/item/contratos-gerais"
                
                print(f"Cidade: {cidade}")
                print(f"Cidade formatada: {cidade_formatada}")
                print(f"URL: {url_base}")
                
                # Lê o config.json
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Atualiza a URL com a cidade
                config['url'] = url_base
                
                # Salva o config temporário
                temp_config_path = os.path.join(PROJECT_ROOT, 'config_temp.json')
                with open(temp_config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4)
                
                status_execucao["mensagem"] = f"Conectando a {cidade}..."
                status_execucao["progresso"] = 20
                
                # Executa o main.py com o config temporário
                print(f"Iniciando processo: python main.py {temp_config_path}")
                processo = subprocess.Popen(
                    ["python", "main.py", temp_config_path],
                    cwd=PROJECT_ROOT,
                    stdout=None,
                    stderr=None,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
                )
                
                processo_atual = processo  # Guarda referência do processo
                print(f"Processo iniciado com PID: {processo.pid}")
                
                # Monitora o progresso
                status_execucao["progresso"] = 50
                status_execucao["mensagem"] = "Acessando portal..."
                
                # Aguarda o processo em background SEM bloquear
                import time
                timeout = 300  # 5 minutos
                start_time = time.time()
                processo_finalizado = False
                
                while time.time() - start_time < timeout:
                    return_code = processo.poll()
                    
                    if return_code is not None:
                        # Processo finalizou
                        processo_finalizado = True
                        print(f"Return code: {return_code}")
                        
                        # SEMPRE verifica se existe arquivo de erro PRIMEIRO
                        error_file = os.path.join(PROJECT_ROOT, ".scraper_error")
                        print(f"Verificando arquivo de erro: {error_file}")
                        print(f"Arquivo existe: {os.path.exists(error_file)}")
                        
                        if os.path.exists(error_file):
                            try:
                                with open(error_file, 'r', encoding='utf-8') as f:
                                    error_msg = f.read().strip()
                                print(f"Conteúdo do arquivo de erro: '{error_msg}'")
                                os.remove(error_file)
                                
                                if error_msg == "ABA_ANEXOS_NAO_DISPONIVEL":
                                    status_execucao["erro"] = "⚠️ Aba 'Anexos' não está disponível neste contrato. O PDF não pode ser baixado pois não existe no portal de transparência."
                                    status_execucao["mensagem"] = f"⚠️ Aba 'Anexos' não disponível em {cidade}"
                                    print("✓ Erro específico de Aba Anexos detectado")
                                else:
                                    status_execucao["erro"] = f"Erro ao executar scraper"
                                    status_execucao["mensagem"] = f"✗ Falha ao processar {cidade}"
                            except Exception as e:
                                print(f"Erro ao ler arquivo de erro: {e}")
                                status_execucao["erro"] = f"Erro ao executar scraper"
                                status_execucao["mensagem"] = f"✗ Falha ao processar {cidade}"
                        elif return_code == 0:
                            # Sucesso apenas se return_code == 0 E não houver arquivo de erro
                            status_execucao["mensagem"] = f"✓ Download de {cidade} concluído com sucesso!"
                            status_execucao["progresso"] = 100
                        else:
                            # Erro genérico
                            status_execucao["erro"] = f"Erro ao executar scraper (código: {return_code})"
                            status_execucao["mensagem"] = f"✗ Falha ao processar {cidade}"
                        break
                    
                    # Incrementa progresso simulado
                    if status_execucao["progresso"] < 95:
                        status_execucao["progresso"] += 1
                    
                    time.sleep(1)
                
                # Limpa o config temporário
                try:
                    os.remove(temp_config_path)
                except:
                    pass
                
                if not processo_finalizado:
                    # Timeout - mata o processo
                    processo.kill()
                    status_execucao["erro"] = "Timeout: processo excedeu o limite de 5 minutos"
                    status_execucao["mensagem"] = "✗ Timeout ao processar"
                    
            except Exception as e:
                status_execucao["erro"] = str(e)
                print(f"ERRO: {str(e)}")
                status_execucao["mensagem"] = "✗ Erro ao iniciar scraper"
                print(f"Erro: {e}")
                import traceback
                traceback.print_exc()
            finally:
                status_execucao["rodando"] = False
        
        # Inicia a thread
        thread = threading.Thread(target=rodar_scraper)
        thread.daemon = True
        thread.start()
        
        return jsonify({"mensagem": f"Scraper iniciado para {cidade}"})
    
    except Exception as e:
        print(f"Erro em /api/executar: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"erro": f"Erro: {str(e)}"}), 500


@app.route('/api/download/<nome_arquivo>')
def download_arquivo(nome_arquivo):
    """Faz download de um arquivo"""
    try:
        caminho_arquivo = os.path.join(DOWNLOADS_FOLDER, nome_arquivo)
        
        # Validação de segurança
        if not os.path.isfile(caminho_arquivo):
            return jsonify({"erro": "Arquivo não encontrado"}), 404
        
        if not os.path.abspath(caminho_arquivo).startswith(os.path.abspath(DOWNLOADS_FOLDER)):
            return jsonify({"erro": "Acesso negado"}), 403
        
        return send_file(
            caminho_arquivo,
            as_attachment=True,
            download_name=nome_arquivo
        )
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/deletar/<nome_arquivo>', methods=['DELETE'])
def deletar_arquivo(nome_arquivo):
    """Deleta um arquivo"""
    try:
        caminho_arquivo = os.path.join(DOWNLOADS_FOLDER, nome_arquivo)
        
        # Validação de segurança
        if not os.path.isfile(caminho_arquivo):
            return jsonify({"erro": "Arquivo não encontrado"}), 404
        
        if not os.path.abspath(caminho_arquivo).startswith(os.path.abspath(DOWNLOADS_FOLDER)):
            return jsonify({"erro": "Acesso negado"}), 403
        
        os.remove(caminho_arquivo)
        return jsonify({"mensagem": "Arquivo deletado com sucesso"})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/limpar', methods=['POST'])
def limpar_pasta():
    """Limpa todos os arquivos da pasta de downloads"""
    try:
        os.makedirs(DOWNLOADS_FOLDER, exist_ok=True)
        
        deletados = 0
        for arquivo in os.listdir(DOWNLOADS_FOLDER):
            caminho = os.path.join(DOWNLOADS_FOLDER, arquivo)
            if os.path.isfile(caminho):
                os.remove(caminho)
                deletados += 1
        
        return jsonify({"mensagem": f"{deletados} arquivo(s) deletado(s)"})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/config')
def get_config():
    """Retorna as configurações"""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return jsonify({
            "url": config.get("url", "N/A"),
            "fornecedor": "IPM",  # Hardcoded no scraper
            "anos": "2020-2025"  # Hardcoded no scraper
        })
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    # Cria a pasta de downloads se não existir
    os.makedirs(DOWNLOADS_FOLDER, exist_ok=True)
    
    print("\n" + "="*60)
    print("Aplicação Web IPM Scraper iniciada!")
    print("="*60)
    print(f"Acesse: http://localhost:5000")
    print(f"Pasta de downloads: {DOWNLOADS_FOLDER}")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5000)
