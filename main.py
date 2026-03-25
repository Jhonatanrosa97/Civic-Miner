from scripts.ipm_scraper import Scraper
import os

def get_chrome_version():
    """
    Tenta obter a versão do Chrome instalado.
    Se não conseguir, apenas retorna None sem quebrar o programa.
    """
    try:
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        
        if not os.path.exists(chrome_path):
            return None
        
        # Tenta usar win32api se disponível
        try:
            import win32api
            info = win32api.GetFileVersionInfo(chrome_path, '\\')
            ms = info['FileVersionMS']
            ls = info['FileVersionLS']
            version = f"{ms >> 16}.{ms & 0xffff}.{ls >> 16}.{ls & 0xffff}"
            print(f"Versão do Chrome: {version}")
            return version
        except:
            # Se win32api não está disponível, apenas retorna None silenciosamente
            return None
            
    except Exception as e:
        # Silenciosamente ignora erros de versão
        return None

def main():
    import sys
    
    # Verifica se foi passado um parâmetro de config
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
        # Se o caminho for relativo, converte para absoluto
        if not os.path.isabs(config_path):
            config_path = os.path.join(os.path.dirname(__file__), config_path)
    else:
        # Usa o config.json padrão
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
    
    # Verifica se o arquivo de configuração existe
    if not os.path.exists(config_path):
        print(f"ERRO: Arquivo de configuração não encontrado: {config_path}")
        return
    
    # Verifica versão do Chrome (informativo apenas)
    chrome_version = get_chrome_version()
    
    try:
        scraper = Scraper(config_path)
        scraper.run()
        # Se chegou aqui, sucesso!
        sys.exit(0)
    except FileNotFoundError as e:
        print(f"ERRO - Arquivo não encontrado: {e}")
        sys.exit(1)
    except Exception as e:
        # Salva mensagem de erro para o Flask capturar
        error_type = "ERRO_GENERICO"
        
        if "Aba 'Anexos' não está disponível" in str(e):
            error_type = "ABA_ANEXOS_NAO_DISPONIVEL"
        
        error_file = os.path.join(os.path.dirname(__file__), ".scraper_error")
        try:
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(error_type)
            print(f"✓ Arquivo de erro criado: {error_file}")
        except Exception as write_err:
            print(f"⚠ Erro ao criar arquivo de erro: {write_err}")
        
        print(f"Erro no main: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()