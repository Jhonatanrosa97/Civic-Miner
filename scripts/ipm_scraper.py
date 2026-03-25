import json
import traceback
import re
import unicodedata
import signal
import sys
import atexit
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
import os

def remove_acentos(text):
    """Remove acentos de um texto para comparação"""
    if not text:
        return ""
    nfd = unicodedata.normalize('NFD', text)
    return ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')

def sleep_interruptible(seconds):
    """Sleep que pode ser interrompido por KeyboardInterrupt"""
    try:
        time.sleep(seconds)
    except KeyboardInterrupt:
        raise

class Scraper:
    def __init__(self, config_path):
        self.driver = None  # Inicializa como None
        self.cancel_flag_file = os.path.join(
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
            ".cancel_scraper"
        )
        try:
            print("Carregando configurações do config.json...")
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Arquivo de configuração não encontrado: {config_path}")
            
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            except json.JSONDecodeError as je:
                print(f"ERRO no arquivo JSON: {je}")
                print(f"Verifique o arquivo {config_path}")
                raise
            except Exception as e:
                print(f"Erro ao ler o arquivo de configuração: {e}")
                raise

            print("Inicializando o ChromeDriver...")
            
            # Define a pasta de downloads
            downloads_folder = os.path.join(
                os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
                "Downloads_PDFs"
            )
            os.makedirs(downloads_folder, exist_ok=True)
            print(f"Pasta de downloads: {downloads_folder}")
            
            driver_path = self.config["driver_path"]
            if not os.path.exists(driver_path):
                raise FileNotFoundError(f"ChromeDriver não encontrado em: {driver_path}")
            
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            
            # Configura o download para ir direto para a pasta Downloads_PDFs
            prefs = {
                "download.default_directory": downloads_folder,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
            }
            chrome_options.add_experimental_option("prefs", prefs)

            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            print("ChromeDriver iniciado com sucesso!")
            
            # Registra função para SEMPRE fechar o navegador quando o script terminar
            atexit.register(self._fechar_navegador_atexit)
            
            # Registra manipulador para fechar navegador quando script for interrompido
            signal.signal(signal.SIGINT, self._fechar_navegador_signal)
            signal.signal(signal.SIGTERM, self._fechar_navegador_signal)

        except Exception as e:
            print("Erro ao iniciar o Scraper:", e)
            traceback.print_exc()
            raise

    def _fechar_navegador_signal(self, sig, frame):
        """Fecha o navegador quando o script é interrompido (Ctrl+C ou cancelamento)"""
        print("\n\n⚠ Script interrompido! Fechando navegador...")
        try:
            if self.driver:
                self.driver.quit()
                print("✓ Navegador fechado!")
        except:
            pass
        sys.exit(0)
    
    def _fechar_navegador_atexit(self):
        """Fecha o navegador quando o script termina (qualquer motivo)"""
        try:
            if self.driver:
                self.driver.quit()
        except:
            pass
    
    def _verificar_cancelamento(self):
        """Verifica se o usuário cancelou a operação"""
        if os.path.exists(self.cancel_flag_file):
            print("\n\n⚠ OPERAÇÃO CANCELADA PELO USUÁRIO!")
            try:
                os.remove(self.cancel_flag_file)
            except:
                pass
            
            # FECHA O NAVEGADOR ANTES DE LEVANTAR A EXCEÇÃO
            print("🔴 Fechando navegador...")
            try:
                if self.driver:
                    self.driver.quit()
                    self.driver = None
                    print("✓ Navegador fechado com sucesso!")
            except Exception as e:
                print(f"⚠ Erro ao fechar navegador: {e}")
            
            raise KeyboardInterrupt("Operação cancelada pelo usuário")

    def acessar_portal(self):
        try:
            self._verificar_cancelamento()  # Verifica cancelamento
            url = self.config["url"]
            print(f"Acessando o site: {url}")
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.driver.get(url)
                    print("Página carregada com sucesso!")
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"Tentativa {attempt + 1} falhou: {e}")
                        print(f"Tentando novamente em 2 segundos...")
                        time.sleep(2)
                    else:
                        raise

            # Aguarda a página carregar completamente
            time.sleep(2)

            wait = WebDriverWait(self.driver, 120)

            # Aguarda o CAPTCHA ser resolvido detectando quando o iframe aparece
            print("\n" + "="*60)
            print("⚠️  AGUARDANDO RESOLUÇÃO DO CAPTCHA")
            print("   Se aparecer um CAPTCHA na tela:")
            print("   1. Resolva-o manualmente")
            print("   2. O scraper continuará automaticamente")
            print("="*60 + "\n")
            
            # Tenta aguardar o iframe aparecer (significa CAPTCHA resolvido)
            captcha_timeout = 180  # 3 minutos de timeout
            try:
                print("Aguardando iframe aparecer (CAPTCHA ser resolvido)...")
                iframe = wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")), timeout=captcha_timeout)
                print("✓ CAPTCHA resolvido! Continuando...\n")
            except Exception as e:
                print(f"Timeout aguardando iframe. Tentando continuar mesmo assim...")
                # Continua mesmo se não encontrar iframe
                time.sleep(2)

            wait = WebDriverWait(self.driver, 120)
            try:
                print("Verificando se o popup de cookies está presente...")
                btn_aceitar = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Aceitar')]"))
                )
                btn_aceitar.click()
                print("Popup de cookies aceito!")
                time.sleep(1)
            except Exception:
                print("Popup de cookies não encontrado ou já aceito.")

            # Trata banners/notificações
            print("Tratando banners/notificações...")
            time.sleep(0.3)
            try:
                try:
                    botao_fechar = self.driver.find_element(By.XPATH, "//div[contains(@class, 'wrapper-aviso')]//button | //div[contains(@class, 'wrapper-aviso')]//*[@role='button']")
                    print("  Botão de fechar encontrado, clicando...")
                    self.driver.execute_script("arguments[0].style.visibility='visible'; arguments[0].click();", botao_fechar)
                    print("  ✓ Banner fechado")
                    time.sleep(0.5)
                except Exception as e:
                    print(f"  Botão não encontrado: {str(e)[:50]}")
                    try:
                        self.driver.execute_script("""
                            var wrapper = document.querySelector('.wrapper-aviso');
                            if (wrapper) {
                                wrapper.style.display = 'none';
                                console.log('Wrapper escondido');
                            }
                        """)
                        print("  ✓ Wrapper escondido via CSS")
                        time.sleep(0.3)
                    except Exception as e2:
                        print(f"  Erro ao esconder: {e2}")
            except Exception as e:
                print(f"  Erro ao tratar banner: {e}")

            # Trocando para o iframe
            try:
                print("Trocando para o iframe...")
                iframe = self.driver.find_element(By.TAG_NAME, "iframe")
                self.driver.switch_to.frame(iframe)
                print("✓ Dentro do iframe!")
            except Exception as e:
                print(f"Erro ao encontrar iframe: {e}")
                raise

            # Seleciona o filtro "Fornecedor - Nome Razão"
            print("Aguardando o filtro aparecer...")
            filtro_select = wait.until(EC.visibility_of_element_located((By.NAME, "filtro")))
            select = Select(filtro_select)
            select.select_by_value("uninomerazao")
            print('Filtro alterado para "Fornecedor - Nome Razão".')

            # Seleciona a Unidade Gestora ANTES do ano
            print("\n" + "="*60)
            print("SELECIONANDO UNIDADE GESTORA...")
            print("="*60)
            
            try:
                print("\n1. Procurando o campo de Unidade Gestora...")
                
                # Encontra e clica no campo para abrir o dropdown
                campo_unidade = self.driver.execute_script("""
                    var campo = document.querySelector('input[name="clicodigo"]');
                    if(campo) {
                        console.log('Campo encontrado: ' + campo.className);
                        return campo;
                    }
                    return null;
                """)
                
                if not campo_unidade:
                    print("[AVISO] Campo Unidade Gestora não encontrado! Pulando...")
                    raise Exception("Campo não encontrado")
                
                print("[OK] Campo encontrado! Abrindo dropdown...")
                self.driver.execute_script("arguments[0].click();", campo_unidade)
                time.sleep(1.5)  # Aguarda dropdown abrir e checkboxes aparecerem
                
                print("\n2. Procurando checkbox do MUNICIPIO nos itens do dropdown...")
                
                # Aguarda mais um pouco para garantir que dropdown está totalmente carregado
                time.sleep(1)
                
                # Primeiro: DESMARCA explicitamente tudo que NÃO é município
                print("Desmarcando tudo que NÃO é MUNICIPIO/PREFEITURA...")
                self.driver.execute_script("""
                    var todosCheckboxes = document.querySelectorAll('input[type="checkbox"][data-valor-lista]');
                    console.log('=== LIMPEZA: Total checkboxes: ' + todosCheckboxes.length);
                    
                    for(var i = 0; i < todosCheckboxes.length; i++) {
                        var cb = todosCheckboxes[i];
                        var ariaLabel = cb.getAttribute('aria-label') || '';
                        var label_upper = ariaLabel.toUpperCase();
                        
                        // Remove acentos
                        var labelSemAcentos = label_upper
                            .replace(/[ÀÁÂÃÄÅ]/g, 'A')
                            .replace(/[ÈÉÊË]/g, 'E')
                            .replace(/[ÌÍÎÏ]/g, 'I')
                            .replace(/[ÒÓÔÕÖ]/g, 'O')
                            .replace(/[ÙÚÛÜ]/g, 'U')
                            .replace(/[Ç]/g, 'C');
                        
                        // Se TEM qualquer palavra ruim OU NÃO começa com MUNICIPIO/PREFEITURA
                        var temRuim = labelSemAcentos.indexOf('ANTI') >= 0 || 
                                      labelSemAcentos.indexOf('FUNDO') >= 0 || 
                                      labelSemAcentos.indexOf('FUNDACAO') >= 0 || 
                                      labelSemAcentos.indexOf('SECRETARIA') >= 0;
                        
                        var comecaBom = labelSemAcentos.indexOf('MUNICIPIO') === 0 || 
                                       labelSemAcentos.indexOf('PREFEITURA') === 0;
                        
                        // Se NÃO é bom OU tem palavra ruim, DESMARCA
                        if(!comecaBom || temRuim) {
                            if(cb.checked) {
                                console.log('DESMARCANDO: ' + ariaLabel);
                                cb.checked = false;
                                cb.click(); // Força evento
                            }
                        }
                    }
                """)
                
                time.sleep(0.5)
                
                # Segundo: Marca APENAS o município/prefeitura
                print("Marcando APENAS MUNICIPIO/PREFEITURA...")
                resultado = self.driver.execute_script("""
                    var todosCheckboxes = document.querySelectorAll('input[type="checkbox"][data-valor-lista]');
                    console.log('=== MARCACAO: Procurando MUNICIPIO...');
                    
                    var municipio_checkbox = null;
                    var municipio_label = null;
                    var municipio_index = -1;
                    var municipio_li = null;
                    
                    for(var i = 0; i < todosCheckboxes.length; i++) {
                        var cb = todosCheckboxes[i];
                        var ariaLabel = cb.getAttribute('aria-label') || '';
                        var label_upper = ariaLabel.toUpperCase();
                        
                        // Remove acentos
                        var labelSemAcentos = label_upper
                            .replace(/[ÀÁÂÃÄÅ]/g, 'A')
                            .replace(/[ÈÉÊË]/g, 'E')
                            .replace(/[ÌÍÎÏ]/g, 'I')
                            .replace(/[ÒÓÔÕÖ]/g, 'O')
                            .replace(/[ÙÚÛÜ]/g, 'U')
                            .replace(/[Ç]/g, 'C');
                        
                        // Verifica se TEM as palavras ruins
                        var temAnti = labelSemAcentos.indexOf('ANTI') >= 0;
                        var temFundo = labelSemAcentos.indexOf('FUNDO') >= 0;
                        var temFundacao = labelSemAcentos.indexOf('FUNDACAO') >= 0;
                        var temSecretaria = labelSemAcentos.indexOf('SECRETARIA') >= 0;
                        
                        // Verifica se COMEÇA com MUNICIPIO ou PREFEITURA
                        var comecaMunicipio = labelSemAcentos.indexOf('MUNICIPIO') === 0;
                        var comecaPrefeitura = labelSemAcentos.indexOf('PREFEITURA') === 0;
                        
                        // Se começa com MUNICIPIO ou PREFEITURA E NÃO tem palavras ruins
                        if((comecaMunicipio || comecaPrefeitura) && !temAnti && !temFundo && !temFundacao && !temSecretaria) {
                            console.log('>>> ENCONTROU MUNICIPIO VALIDO [' + i + ']: ' + ariaLabel);
                            municipio_checkbox = cb;
                            municipio_label = ariaLabel;
                            municipio_index = i;
                            
                            // Encontra o LI parent
                            municipio_li = cb.closest('li');
                            break;
                        }
                    }
                    
                    if(!municipio_checkbox) {
                        return 'ERRO: Municipio nao encontrado';
                    }
                    
                    // LIMPA TUDO primeiro
                    console.log('=== Limpando todas as seleções...');
                    for(var j = 0; j < todosCheckboxes.length; j++) {
                        if(todosCheckboxes[j].checked) {
                            todosCheckboxes[j].checked = false;
                        }
                    }
                    
                    // Clica no LI do município (simula clique de usuário real)
                    console.log('=== Clicando no LI do municipio [' + municipio_index + ']: ' + municipio_label);
                    if(municipio_li) {
                        municipio_li.click();
                    } else {
                        // Fallback: clica no checkbox
                        municipio_checkbox.click();
                    }
                    
                    return 'OK: [' + municipio_index + '] ' + municipio_label;
                """)
                
                print(f"[OK] {resultado}")
                time.sleep(0.3)
                
                # FECHA O DROPDOWN IMEDIATAMENTE (antes do site marcar ANTI DROGAS)
                print("\n3. Fechando dropdown IMEDIATAMENTE...")
                self.driver.find_element(By.TAG_NAME, "body").click()
                time.sleep(0.3)
                
                # Verifica se município ficou selecionado no campo
                valor_selecionado = self.driver.execute_script("""
                    var campo = document.querySelector('input[name="clicodigo"]');
                    return campo ? campo.value : 'N/A';
                """)
                print("\nFechando dropdown (clicando fora)...")
                try:
                    self.driver.find_element(By.TAG_NAME, "body").click()
                except:
                    pass
                time.sleep(0.5)
                
                print("[OK] Unidade Gestora selecionada com sucesso!")
                    
            except Exception as e:
                print(f"\n[ERRO] Erro ao selecionar Unidade Gestora: {e}")
                import traceback
                traceback.print_exc()
                print("\n[AVISO] Continuando sem Unidade Gestora...")
            
            print("="*60 + "\n")

            # Seleciona todos os anos
            print("Aguardando o campo de ano do contrato aparecer...")
            campo_ano_contrato = wait.until(EC.element_to_be_clickable((By.NAME, "ano_contrato_superior")))
            campo_ano_contrato.click()
            print("Campo de ano clicado.")

            time.sleep(1)

            for ano in range(2020, 2026):
                print(f"Selecionando o ano {ano}...")
                
                try:
                    avisos = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'wrapper-aviso') or contains(@class, 'aviso')]")
                    for aviso in avisos:
                        try:
                            botao_fechar = aviso.find_element(By.XPATH, ".//button | .//a[contains(@class, 'close')]")
                            self.driver.execute_script("arguments[0].click();", botao_fechar)
                            print("  Aviso fechado.")
                        except:
                            self.driver.execute_script("arguments[0].remove();", aviso)
                            print("  Aviso removido via JavaScript.")
                except:
                    pass
                
                time.sleep(0.3)
                
                checkbox_xpath = f"//input[@type='checkbox' and @data-valor-lista='{ano}']"
                checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, checkbox_xpath)))
                
                self.driver.execute_script("arguments[0].click();", checkbox)
                print(f"Ano {ano} selecionado.")
                time.sleep(0.2)

            # Fecha o dropdown clicando fora
            self.driver.find_element(By.TAG_NAME, "body").click()
            time.sleep(0.5)
            print("Dropdown fechado.")

            # Preenche a caixa de busca com "IPM Sistemas"
            print("Aguardando o campo de busca aparecer...")
            campo_busca = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@name='campo01' and @type='text']")))
            campo_busca.click()
            time.sleep(0.2)
            try:
                campo_busca.clear()
                campo_busca.send_keys("IPM Sistemas")
                print('Texto "IPM Sistemas" inserido no campo de busca (via send_keys).')
            except Exception:
                print("Falha ao usar send_keys, tentando via JavaScript...")
                self.driver.execute_script("arguments[0].value = 'IPM Sistemas';", campo_busca)
                print('Texto "IPM Sistemas" inserido no campo de busca (via JS).')

            # Clica no botão "Consultar"
            print('Aguardando o botão "Consultar" aparecer...')
            btn_consultar = wait.until(EC.element_to_be_clickable((
                By.XPATH, "//span[contains(@class, 'botao-label') and text()='Consultar']/ancestor::*[self::button or self::div][1]"
            )))
            btn_consultar.click()
            print('Consulta realizada!')

            # Aguarda o carregamento "Aguarde" desaparecer
            print('Aguardando o carregamento "Aguarde" desaparecer...')
            wait.until(EC.invisibility_of_element_located((By.XPATH, "//*[contains(text(), 'Aguarde')]")))
            print('Carregamento finalizado!')

            # Força o desfoco do campo de busca
            print('Removendo o foco do campo de busca...')
            self.driver.execute_script("arguments[0].blur();", campo_busca)
            time.sleep(0.2)
            self.driver.find_element(By.TAG_NAME, "body").click()
            time.sleep(0.5)

            # Localiza e expande QUALQUER contrato (pega o primeiro disponível)
            print("\nLocalizando e expandindo PRIMEIRO CONTRATO disponível...")
            try:
                # Aguarda a tabela carregar
                time.sleep(2)
                
                # Busca a linha de CONTRATO MAIS RECENTE e clica na seta
                resultado = self.driver.execute_script("""
                    var linhas = document.querySelectorAll('tr');
                    console.log('Total de TRs encontradas: ' + linhas.length);
                    
                    var linhas_contratos = [];
                    
                    // PROCURA todas as TRs que contêm "Contrato:"
                    for(var i = 0; i < linhas.length; i++) {
                        if(linhas[i].textContent.indexOf('Contrato:') >= 0) {
                            console.log('>>> Encontrada TR com "Contrato:" no índice ' + i);
                            
                            // Extrai o ano do contrato (formato: "Contrato: XXX/YYYY")
                            var texto = linhas[i].textContent;
                            var match = texto.match(/Contrato:\\s*(\\d+)\\/(\\d{4})/);
                            var ano = match ? parseInt(match[2]) : 0;
                            
                            linhas_contratos.push({
                                linha: linhas[i],
                                indice: i,
                                texto: texto.substring(0, 100),
                                ano: ano
                            });
                        }
                    }
                    
                    if(linhas_contratos.length === 0) {
                        return {erro: 'Nenhuma linha com "Contrato:" encontrada'};
                    }
                    
                    // Ordena por ano (decrescente) para pegar o mais recente
                    linhas_contratos.sort(function(a, b) {
                        return b.ano - a.ano;
                    });
                    
                    console.log('Total de contratos encontrados: ' + linhas_contratos.length);
                    console.log('Contratos encontrados:', linhas_contratos.map(function(c) { return c.ano; }));
                    
                    var primeira_linha_contrato = linhas_contratos[0].linha;
                    var ano_selecionado = linhas_contratos[0].ano;
                    
                    console.log('>>> SELECIONANDO CONTRATO MAIS RECENTE (ANO: ' + ano_selecionado + ')');
                    
                    // Busca o número do contrato
                    var spans = primeira_linha_contrato.querySelectorAll('span.coluna_agrupador_valor');
                    var numero_contrato = spans.length > 0 ? spans[0].textContent.trim() : 'N/A';
                    console.log('Contrato selecionado: ' + numero_contrato + ' (' + ano_selecionado + ')');
                    
                    // PROCURA O TD COM CLASSE "acao_consulta_agrupamento" (SETA ESPECÍFICA DO CONTRATO)
                    var td_seta = primeira_linha_contrato.querySelector('td.acao_consulta_agrupamento');
                    
                    if(!td_seta) {
                        console.log('TD com acao_consulta_agrupamento NÃO encontrado');
                        // Tenta alternativa: qualquer acao_consulta
                        td_seta = primeira_linha_contrato.querySelector('td.acao_consulta');
                        console.log('Tentando acao_consulta genérico: ' + (td_seta ? 'SIM' : 'NAO'));
                    }
                    
                    if(!td_seta) {
                        return {erro: 'Seta do contrato não encontrada', contrato: numero_contrato};
                    }
                    
                    // Procura o INPUT ou SPAN clicável dentro do TD
                    var elemento = td_seta.querySelector('input[type="button"], span[class*="fa-chevron"]');
                    if(!elemento) {
                        elemento = td_seta.querySelector('input, span, a');
                    }
                    if(!elemento) {
                        elemento = td_seta;
                    }
                    
                    console.log('Clicando no elemento: ' + elemento.tagName + ' / ' + (elemento.className || ''));
                    elemento.click();
                    
                    return {ok: true, contrato: numero_contrato};
                """)
                
                if 'erro' in resultado:
                    print(f"[ERRO] {resultado['erro']}")
                    raise Exception(resultado['erro'])
                
                print(f"✓ [OK] Contrato MAIS RECENTE expandido: {resultado['contrato']}")
                time.sleep(2)
                
                # VERIFICAÇÃO: Confirma que a linha foi realmente expandida
                print("\nVerificando se linha foi expandida...")
                linhas_visiveis = self.driver.execute_script("""
                    var trs = document.querySelectorAll('tr');
                    var count = 0;
                    for(var i = 0; i < trs.length; i++) {
                        if(trs[i].offsetHeight > 0 && trs[i].offsetWidth > 0) {
                            count++;
                        }
                    }
                    return count;
                """)
                print(f"   Total de linhas visíveis: {linhas_visiveis}")
                
                if linhas_visiveis < 2:
                    print("[AVISO] Parece que a linha não expandiu (poucas linhas visíveis)")
                    print("   Tentando expandir novamente com método alternativo...")
                    
                    # Tenta clicar em qualquer lugar da linha como fallback
                    self.driver.execute_script("""
                        var linhas = document.querySelectorAll('tr');
                        for(var i = 0; i < linhas.length; i++) {
                            if(linhas[i].textContent.indexOf('Contrato:') >= 0) {
                                console.log('Clicando na linha inteira como fallback...');
                                linhas[i].click();
                                break;
                            }
                        }
                    """)
                    time.sleep(2)
                else:
                    print("[OK] Linha expandida com sucesso!")
                
            except Exception as e:
                print(f"[ERRO] Falha ao expandir contrato: {e}")
                print("   Tentando continuar mesmo assim...")
                time.sleep(1)

        except Exception as e:
            print(f"Erro ao acessar o portal: {e}")

    def clicar_linha_visualizacao(self, timeout=20):
        """
        Após a linha do contrato ser expandida, localiza a linha de detalhe correta e clica no ícone de visualização (olho).
        """
        wait = WebDriverWait(self.driver, timeout)

        print("\n" + "="*60)
        print("INICIANDO: clicar_linha_visualizacao")
        print("="*60)

        time.sleep(1)

        try:
            html_debug = os.path.join(
                os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
                "debug_linhas_expandidas.html"
            )
            with open(html_debug, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print(f"HTML de debug salvo: {html_debug}")
        except Exception as e:
            print(f"Erro ao salvar HTML debug: {e}")

        print("\nProcurando por ícones de visualização (fa-eye)...")
        try:
            eye_icons = self.driver.find_elements(By.XPATH, "//i[contains(@class, 'fa-eye')] | //span[contains(@class, 'fa-eye')]")
            print(f"  ✓ Encontrados {len(eye_icons)} ícones de olho na página")
            
            if len(eye_icons) > 0:
                for i, eye in enumerate(eye_icons[:5]):
                    try:
                        parent_row = eye.find_element(By.XPATH, "ancestor::tr")
                        texto_linha = parent_row.text[:100]
                        print(f"    [{i}] Linha: {texto_linha}")
                    except:
                        pass
        except Exception as e:
            print(f"  Erro ao listar ícones: {e}")

        rows = []
        print("\nBuscando linhas de detalhe...")
        
        try:
            rows = self.driver.find_elements(By.XPATH, "//tr[.//i[contains(@class, 'fa-eye')] or .//span[contains(@class, 'fa-eye')]]")
            print(f"  ✓ {len(rows)} linhas encontradas com ícone de olho")
        except Exception as e:
            print(f"  ✗ Erro ao encontrar linhas: {e}")
            return False

        if not rows:
            print("  ✗ Nenhuma linha de detalhe encontrada!")
            return False

        print(f"\nEscolhendo primeira linha de {len(rows)} disponíveis...")
        chosen_row = rows[0]
        
        try:
            texto = chosen_row.text
            print(f"  Texto da linha: {texto[:150]}")
        except:
            pass

        print("\nFazendo scroll para linha...")
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", chosen_row)
        time.sleep(0.5)

        print("Procurando ícone de olho dentro da linha...")
        eye_icon = None
        try:
            eye_xpaths = [
                ".//i[contains(@class, 'fa-eye')]",
                ".//span[contains(@class, 'fa-eye')]",
                ".//button[.//i[contains(@class, 'fa-eye')]]",
                ".//a[.//i[contains(@class, 'fa-eye')]]",
            ]
            
            for xpath in eye_xpaths:
                try:
                    elements = chosen_row.find_elements(By.XPATH, xpath)
                    if elements:
                        eye_icon = elements[0]
                        print(f"  ✓ Ícone encontrado com: {xpath}")
                        break
                except:
                    pass
        except Exception as e:
            print(f"  Erro ao procurar ícone: {e}")

        if not eye_icon:
            print("  ✗ Ícone de olho não encontrado!")
            return False

        print("\nTentando clicar no ícone de visualizar...")
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                print(f"  Tentativa {attempt + 1}/{max_attempts}...")
                
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", eye_icon)
                time.sleep(0.2)
                
                try:
                    WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, ".//i[contains(@class, 'fa-eye')]")))
                except Exception:
                    pass

                try:
                    ActionChains(self.driver).move_to_element(eye_icon).pause(0.35).click().perform()
                    print(f"  ✓ Clicado via ActionChains!")
                    time.sleep(1)
                    return True
                except Exception as e1:
                    print(f"    ActionChains falhou: {str(e1)[:50]}")
                    
                    try:
                        self.driver.execute_script("arguments[0].click();", eye_icon)
                        print("  ✓ Clicado via JavaScript!")
                        time.sleep(1)
                        return True
                    except Exception as e2:
                        print(f"    JavaScript falhou: {str(e2)[:50]}")
                
                # Verifica se município ficou selecionado no campo
                valor_selecionado = self.driver.execute_script("""
                    var campo = document.querySelector('input[name="clicodigo"]');
                    return campo ? campo.value : 'N/A';
                """)
                print(f"   Valor final do campo clicodigo: {valor_selecionado}")
                
                if not valor_selecionado or valor_selecionado == 'N/A':
                    print("\n[ERRO] Unidade Gestora não foi selecionada após fechar dropdown!")
                    return False
                    
                print("\n[SUCESSO] Unidade Gestora selecionada com sucesso!")
            
            except Exception as e:
                print(f"  Erro na tentativa {attempt + 1}: {e}")

        print("✗ Falha ao clicar no ícone após todas as tentativas")
        return False

    def clicar_aba_anexos(self, timeout=15):
        """
        Clica na aba "Anexos" dentro do diálogo de visualização do contrato.
        """
        self._verificar_cancelamento()  # Verifica cancelamento
        wait = WebDriverWait(self.driver, timeout)
        try:
            print("\n" + "="*60)
            print("INICIANDO: clicar_aba_anexos")
            print("="*60)
            
            print("Aguardando o diálogo carregar completamente...")
            time.sleep(3)  # Aguarda mais tempo para a página carregar
            
            # Tenta aguardar elementos de carregamento desaparecerem
            print("Verificando se há elementos de carregamento...")
            try:
                loading_elements = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'loading') or contains(@class, 'spinner') or contains(@class, 'aguarde')]")
                if loading_elements:
                    print(f"  Encontrados {len(loading_elements)} elementos de carregamento, aguardando desaparecerem...")
                    for elem in loading_elements:
                        try:
                            wait.until(EC.invisibility_of_element_located((By.XPATH, f"//*[contains(@class, '{elem.get_attribute('class')}')]")))
                        except:
                            pass
                    print("  ✓ Elementos de carregamento desapareceram")
            except:
                pass
            
            time.sleep(1.5)  # Aguarda mais um pouco após o carregamento
            
            print("\nProcurando pela aba 'Anexos'...")
            
            # XPaths para encontrar a aba Anexos
            anexos_xpaths = [
                "//a[contains(., 'Anexos')]",
                "//span[contains(., 'Anexos')]",
                "//*[contains(text(), 'Anexos')]",
                "//li[contains(., 'Anexos')]",
                "//*[@title='Anexos']",
            ]
            
            aba_anexos = None
            for xpath in anexos_xpaths:
                try:
                    elementos = self.driver.find_elements(By.XPATH, xpath)
                    for elem in elementos:
                        try:
                            if elem.is_displayed():
                                aba_anexos = elem
                                print(f"  ✓ Aba 'Anexos' encontrada com: {xpath}")
                                break
                        except:
                            pass
                    if aba_anexos:
                        break
                except Exception as e:
                    pass
            
            if not aba_anexos:
                print("  ✗ Aba 'Anexos' não encontrada!")
                print("  Tentando wait até que apareça...")
                try:
                    aba_anexos = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Anexos')]")))
                    print("  ✓ Aba 'Anexos' encontrada após esperar!")
                except:
                    print("  ✗ Timeout aguardando aba 'Anexos'")
                    return "NAO_DISPONIVEL"
            
            print("  Fazendo scroll para aba...")
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", aba_anexos)
            time.sleep(0.3)
            
            print("  Clicando na aba 'Anexos'...")
            try:
                ActionChains(self.driver).move_to_element(aba_anexos).pause(0.3).click().perform()
                print("  ✓ Clicado via ActionChains!")
            except Exception as e1:
                print(f"    ActionChains falhou: {str(e1)[:50]}")
                try:
                    self.driver.execute_script("arguments[0].click();", aba_anexos)
                    print("  ✓ Clicado via JavaScript!")
                except Exception as e2:
                    print(f"    JavaScript falhou: {str(e2)[:50]}")
                    return False
            
            print("  Aguardando aba 'Anexos' carregar conteúdo...")
            time.sleep(3)
            
            # Verifica se a aba está realmente ativa e com conteúdo
            print("  Verificando se aba 'Anexos' está ativa...")
            anexo_ativo = self.driver.execute_script("""
                // Procura pela aba Anexos ativa
                var abaAnexos = document.querySelector('article[aria-label*="Anexos"]');
                if (!abaAnexos) {
                    return 'Aba Anexos não encontrada no DOM';
                }
                
                // Verifica se está visível
                var style = window.getComputedStyle(abaAnexos);
                if (style.display === 'none' || !abaAnexos.offsetParent) {
                    return 'Aba Anexos não está visível (display:none)';
                }
                
                // Procura pela tabela de dados dentro da aba Anexos
                var tabela = abaAnexos.querySelector('table.dados_consulta tbody');
                if (!tabela) {
                    return 'Tabela de anexos não encontrada';
                }
                
                var linhas = tabela.querySelectorAll('tr.registro-linha, tr.linha_dados');
                return 'Aba ativa com ' + linhas.length + ' linhas de dados';
            """)
            print(f"    Status da aba: {anexo_ativo}")
            
            if 'não' in str(anexo_ativo).lower() or 'display:none' in str(anexo_ativo):
                print("  ✗ Aba 'Anexos' não está carregada corretamente!")
                return "NAO_DISPONIVEL"
            
            print("✓ Aba 'Anexos' clicada e carregada com sucesso!")
            time.sleep(1)
            return True
            
        except Exception as e:
            print(f"Erro em clicar_aba_anexos: {e}")
            import traceback
            traceback.print_exc()
            return False

    def baixar_pdf_impressao(self, timeout=15):
        """
        Encontra a linha com tipo 'Impressão', clica nos 3 pontos e depois em 'Baixar'.
        """
        self._verificar_cancelamento()  # Verifica cancelamento
        wait = WebDriverWait(self.driver, timeout)
        try:
            print("\n" + "="*60)
            print("INICIANDO: baixar_pdf_impressao")
            print("="*60)
            
            print("Aguardando a tabela de Anexos carregar completamente...")
            time.sleep(3)
            
            # Salva screenshot antes de tudo
            try:
                screenshot_path = os.path.join(
                    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
                    "debug_antes_clique_3pontos.png"
                )
                self.driver.save_screenshot(screenshot_path)
                print(f"Screenshot salvo: {screenshot_path}")
            except:
                pass
            
            # Tenta aguardar elementos de carregamento desaparecerem
            print("Verificando se há elementos de carregamento...")
            try:
                loading_elements = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'loading') or contains(@class, 'spinner') or contains(@class, 'aguarde')]")
                if loading_elements:
                    print(f"  Encontrados {len(loading_elements)} elementos de carregamento, aguardando desaparecerem...")
            except:
                pass
            
            time.sleep(1)
            
            print("\nProcurando pela linha com tipo 'Impressão' ou 'Outros' dentro da aba Anexos...")
            
            # Usa JavaScript para buscar a linha "Impressão" OU "Outros" especificamente dentro da aba Anexos ativa
            impressao_info = self.driver.execute_script("""
                // Encontra a aba Anexos ativa
                var abaAnexos = document.querySelector('article[aria-label*="Anexos"]');
                if (!abaAnexos) {
                    return {erro: 'Aba Anexos não encontrada'};
                }
                
                // Procura a tabela de dados dentro da aba Anexos
                var tabela = abaAnexos.querySelector('table.dados_consulta tbody');
                if (!tabela) {
                    return {erro: 'Tabela de anexos não encontrada'};
                }
                
                // Procura todas as linhas de dados
                var linhas = tabela.querySelectorAll('tr.registro-linha, tr.linha_dados');
                console.log('Total de linhas encontradas:', linhas.length);
                
                var linhaImpressao = null;
                var linhaOutros = null;
                
                // Primeira passagem: procura por "Impressão" e marca "Outros" se encontrar
                for (var i = 0; i < linhas.length; i++) {
                    var texto = linhas[i].textContent || linhas[i].innerText;
                    console.log('Linha ' + i + ':', texto.substring(0, 100));
                    
                    // Prioridade 1: Procura por "Impressão" (com ou sem acento)
                    if (texto.indexOf('Impressão') >= 0 || texto.indexOf('Impressao') >= 0) {
                        linhaImpressao = {
                            encontrada: true,
                            tipo: 'Impressão',
                            indice: i,
                            texto: texto.substring(0, 200)
                        };
                        break;  // Encontrou Impressão, para de procurar
                    }
                    
                    // Prioridade 2: Marca linha "Outros" caso não encontre Impressão
                    if (texto.indexOf('Outros') >= 0 || texto.indexOf('OUTROS') >= 0) {
                        linhaOutros = {
                            encontrada: true,
                            tipo: 'Outros',
                            indice: i,
                            texto: texto.substring(0, 200)
                        };
                    }
                }
                
                // Retorna Impressão se encontrou, senão retorna Outros, senão erro
                if (linhaImpressao) {
                    return linhaImpressao;
                } else if (linhaOutros) {
                    return linhaOutros;
                }
                
                // Se não encontrou nenhuma, retorna todas as linhas para debug
                var todosTextos = [];
                for (var i = 0; i < linhas.length; i++) {
                    todosTextos.push(linhas[i].textContent.substring(0, 100));
                }
                
                return {
                    erro: 'Nenhuma linha Impressão ou Outros encontrada',
                    totalLinhas: linhas.length,
                    amostras: todosTextos
                };
            """)
            
            print(f"  Resultado da busca JavaScript: {str(impressao_info)[:300]}")
            
            if 'erro' in impressao_info:
                print(f"  ✗ {impressao_info['erro']}")
                if 'amostras' in impressao_info:
                    print(f"  Total de linhas na tabela: {impressao_info.get('totalLinhas', 0)}")
                    print(f"  Amostras de linhas encontradas:")
                    for i, amostra in enumerate(impressao_info.get('amostras', [])[:5]):
                        print(f"    Linha {i}: {amostra}")
                
                print("  Salvando HTML para debug...")
                try:
                    html_debug = os.path.join(
                        os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
                        "debug_html_sem_impressao.html"
                    )
                    with open(html_debug, "w", encoding="utf-8") as f:
                        f.write(self.driver.page_source)
                    print(f"  HTML salvo: {html_debug}")
                except:
                    pass
                return False
            
            print(f"✓ Linha '{impressao_info['tipo']}' encontrada (índice {impressao_info['indice']})!")
            print(f"  Texto da linha: {impressao_info['texto']}")
            
            # Agora busca o elemento real da linha usando o índice
            print("\n  Obtendo elemento real da linha via JavaScript...")
            impressao_row = self.driver.execute_script("""
                var abaAnexos = document.querySelector('article[aria-label*="Anexos"]');
                if (!abaAnexos) return null;
                
                var tabela = abaAnexos.querySelector('table.dados_consulta tbody');
                if (!tabela) return null;
                
                var linhas = tabela.querySelectorAll('tr.registro-linha, tr.linha_dados');
                return linhas[arguments[0]];
            """, impressao_info['indice'])
            
            if not impressao_row:
                print("  ✗ Não conseguiu obter o elemento da linha!")
                return False
            
            print("  ✓ Elemento da linha obtido!")
            
            # Faz scroll para garantir visibilidade
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", impressao_row)
            time.sleep(0.5)
            
            print("\nProcurando pelos 3 pontos (menu) na linha...")
            
            # Debug: lista todos os elementos clicáveis na linha
            print("  Debug: Procurando todos os botões/spans da linha...")
            try:
                todos_botoes = impressao_row.find_elements(By.XPATH, ".//*[self::button or self::i or self::span or self::a]")
                print(f"  Encontrados {len(todos_botoes)} elementos clicáveis")
                for i, btn in enumerate(todos_botoes[-5:]):  # Mostra os últimos 5
                    try:
                        tag = btn.tag_name
                        classe = btn.get_attribute("class") or ""
                        texto = btn.text or ""
                        print(f"    [{i}] <{tag}> class='{classe}' text='{texto[:30]}'")
                    except:
                        pass
            except:
                pass
            
            # Procura pelos 3 pontos - tenta especificamente na última coluna
            menu_button_xpaths = [
                ".//td[last()]//button",  # Botão na última coluna
                ".//td[last()]//i",  # Ícone na última coluna
                ".//td[last()]//span",  # Span na última coluna
                ".//button[contains(@class, 'menu') or contains(@class, 'action') or contains(@class, 'dropdown')]",
                ".//i[contains(@class, 'fa-ellipsis') or contains(@class, 'fa-bars') or contains(@class, 'fa-dots')]",
                ".//button",  # Fallback: último botão
            ]
            
            menu_button = None
            for xpath in menu_button_xpaths:
                try:
                    elementos = impressao_row.find_elements(By.XPATH, xpath)
                    if elementos:
                        # Prefere o último elemento (deve estar no final da linha)
                        menu_button = elementos[-1]
                        print(f"  ✓ Possível menu encontrado com: {xpath}")
                        break
                except:
                    pass
            
            if not menu_button:
                print("  ✗ Menu button não encontrado!")
                return False
            
            print("✓ Menu button encontrado! Clicando...")
            
            # Tenta clicar de várias formas
            click_success = False
            
            # Tentativa 1: ActionChains
            try:
                print("  Tentativa 1: ActionChains...")
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", menu_button)
                time.sleep(0.3)
                ActionChains(self.driver).move_to_element(menu_button).pause(0.3).click().perform()
                print("  ✓ Clicado via ActionChains!")
                click_success = True
            except Exception as e1:
                print(f"  ✗ ActionChains falhou: {str(e1)[:50]}")
            
            # Tentativa 2: JavaScript direto
            if not click_success:
                try:
                    print("  Tentativa 2: JavaScript click...")
                    self.driver.execute_script("arguments[0].click();", menu_button)
                    print("  ✓ Clicado via JavaScript!")
                    click_success = True
                except Exception as e2:
                    print(f"  ✗ JavaScript falhou: {str(e2)[:50]}")
            
            # Tentativa 3: Focus + Enter
            if not click_success:
                try:
                    print("  Tentativa 3: Focus + Enter...")
                    self.driver.execute_script("arguments[0].focus();", menu_button)
                    menu_button.send_keys(Keys.RETURN)
                    print("  ✓ Ativado via Focus + Enter!")
                    click_success = True
                except Exception as e3:
                    print(f"  ✗ Focus + Enter falhou: {str(e3)[:50]}")
            
            if not click_success:
                print("  ✗ Nenhum método de clique funcionou!")
                return False
            
            print("✓ Menu clicado! Aguardando menu abrir...")
            time.sleep(1.5)
            
            # Salva screenshot do menu aberto
            try:
                screenshot_path = os.path.join(
                    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
                    "debug_menu_aberto.png"
                )
                self.driver.save_screenshot(screenshot_path)
                print(f"Screenshot do menu salvo: {screenshot_path}")
            except:
                pass
            
            # Procura pelo botão "Baixar"
            print("\nProcurando pelo botão 'Baixar'...")
            
            baixar_xpaths = [
                "//*[contains(text(), 'Baixar')]",
                "//*[normalize-space()='Baixar']",
                "//a[contains(., 'Baixar')]",
                "//button[contains(., 'Baixar')]",
                "//li[contains(., 'Baixar')]",
                "//*[contains(text(), 'Download')]",
            ]
            
            baixar_button = None
            for xpath in baixar_xpaths:
                try:
                    elementos = self.driver.find_elements(By.XPATH, xpath)
                    if elementos:
                        for elem in elementos:
                            try:
                                if elem.is_displayed():
                                    baixar_button = elem
                                    print(f"  ✓ Botão 'Baixar' encontrado com: {xpath}")
                                    print(f"    Texto: '{elem.text}'")
                                    break
                            except:
                                pass
                        if baixar_button:
                            break
                except:
                    pass
            
            if not baixar_button:
                print("  ✗ Botão 'Baixar' não encontrado!")
                print("  Salvando HTML com menu aberto...")
                try:
                    html_debug = os.path.join(
                        os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
                        "debug_html_menu_aberto.html"
                    )
                    with open(html_debug, "w", encoding="utf-8") as f:
                        f.write(self.driver.page_source)
                    print(f"  HTML salvo: {html_debug}")
                except:
                    pass
                return False
            
            print("✓ Botão 'Baixar' encontrado! Clicando...")
            
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", baixar_button)
            time.sleep(0.3)
            
            try:
                ActionChains(self.driver).move_to_element(baixar_button).pause(0.3).click().perform()
                print("  ✓ Clicado via ActionChains!")
            except Exception as e1:
                print(f"  ✗ ActionChains falhou: {str(e1)[:50]}")
                try:
                    self.driver.execute_script("arguments[0].click();", baixar_button)
                    print("  ✓ Clicado via JavaScript!")
                except Exception as e2:
                    print(f"  ✗ JavaScript falhou: {str(e2)[:50]}")
                    return False
            
            print("\n✓ Botão 'Baixar' clicado! Download iniciado...")
            
            # Monitora a pasta para detectar novo arquivo
            downloads_folder = os.path.join(
                os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
                "Downloads_PDFs"
            )
            
            print(f"\nAguardando download completar em: {downloads_folder}")
            
            # Lista arquivos antes
            arquivos_antes = set(os.listdir(downloads_folder))
            
            # Primeiro aguarda o arquivo .crdownload aparecer (download começou)
            print("  Aguardando download iniciar...")
            download_iniciado = False
            for tentativa in range(10):
                time.sleep(1)
                arquivos_agora = os.listdir(downloads_folder)
                
                # Verifica se tem arquivo .crdownload (download em andamento)
                tem_crdownload = any(f.endswith('.crdownload') for f in arquivos_agora)
                
                if tem_crdownload:
                    print(f"  ✓ Download iniciado! Aguardando conclusão...")
                    download_iniciado = True
                    break
                
                # Ou verifica se já apareceu arquivo novo completo (download muito rápido)
                novos_arquivos = set(arquivos_agora) - arquivos_antes
                if novos_arquivos:
                    arquivos_completos = [f for f in novos_arquivos if not f.endswith('.crdownload')]
                    if arquivos_completos:
                        print(f"  ✓ Download concluído rapidamente!")
                        download_iniciado = True
                        break
                
                print(f"  Aguardando iniciar... ({tentativa + 1}/10)")
            
            if not download_iniciado:
                print("  ⚠ Download não iniciou no tempo esperado")
            
            # Agora aguarda o arquivo .crdownload desaparecer (download completo)
            print("\n  Aguardando download finalizar (arquivo .crdownload desaparecer)...")
            download_completo = False
            
            for tentativa in range(10):  # Até 10 segundos para download completar
                time.sleep(1)
                arquivos_agora = os.listdir(downloads_folder)
                
                # Verifica se ainda tem .crdownload
                tem_crdownload = any(f.endswith('.crdownload') for f in arquivos_agora)
                
                if not tem_crdownload:
                    # Não tem mais .crdownload, verifica se tem arquivo novo
                    novos_arquivos = set(arquivos_agora) - arquivos_antes
                    arquivos_completos = [f for f in novos_arquivos if not f.endswith('.crdownload')]
                    
                    if arquivos_completos:
                        print(f"\n✓ Download concluído!")
                        for arquivo in arquivos_completos:
                            caminho_completo = os.path.join(downloads_folder, arquivo)
                            tamanho = os.path.getsize(caminho_completo)
                            print(f"  📄 {arquivo}")
                            print(f"  📊 Tamanho: {tamanho:,} bytes ({tamanho/1024:.1f} KB)")
                            print(f"  📍 Caminho: {caminho_completo}")
                        download_completo = True
                        break
                else:
                    if tentativa % 3 == 0:  # Mostra progresso a cada 3 segundos
                        print(f"  Download em andamento... ({tentativa + 1}s)")
            
            if not download_completo:
                print("  ⚠ Download não completou no tempo esperado (10s)")
                print("  O arquivo pode estar sendo baixado ainda...")
            
            # Aguarda mais 2 segundos de segurança
            print("\n  Aguardando 2 segundos adicionais para garantir...")
            time.sleep(2)
            
            print("\n" + "="*60)
            print("SUCESSO! PDF baixado com sucesso!")
            print("="*60)
            
            return True
            
        except Exception as e:
            print(f"Erro em baixar_pdf_impressao: {e}")
            import traceback
            traceback.print_exc()
            return False


    def run(self):
        try:
            self._verificar_cancelamento()
            self.acessar_portal()
            self._verificar_cancelamento()
            ok = self.clicar_linha_visualizacao()
            if ok:
                print("\nVisualização aberta!")
                time.sleep(1)
                
                self._verificar_cancelamento()
                print("\n" + "="*60)
                print("Clicando na aba 'Anexos'...")
                print("="*60)
                
                ok_anexos = self.clicar_aba_anexos()
                if ok_anexos == "NAO_DISPONIVEL":
                    raise Exception("ABA_ANEXOS_NAO_DISPONIVEL")
                if ok_anexos:
                    print("\n" + "="*60)
                    print("SUCESSO! Aba 'Anexos' aberta!")
                    print("="*60)
                    
                    # SALVA SCREENSHOT DA ABA ANEXOS
                    time.sleep(2)
                    try:
                        screenshot_path = os.path.join(
                            os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
                            "debug_aba_anexos.html"
                        )
                        with open(screenshot_path, "w", encoding="utf-8") as f:
                            f.write(self.driver.page_source)
                        print(f"\nHTML da aba Anexos salvo: {screenshot_path}")
                    except Exception as e:
                        print(f"Erro ao salvar HTML: {e}")
                    
                    # Tenta baixar o PDF da linha Impressão
                    print("\nAgora vamos baixar o PDF...")
                    ok_download = self.baixar_pdf_impressao()
                    
                    if ok_download:
                        print("\n" + "="*60)
                        print("Download finalizado! Fechando navegador em 2 segundos...")
                        print("="*60)
                        time.sleep(2)
                    else:
                        print("\n✗ Falha no download.")
                        raise Exception("DOWNLOAD_FALHOU")
                else:
                    raise Exception("FALHA_ABRIR_ANEXOS")
            else:
                print("✗ Falha ao localizar/clicar a linha de visualização.")
                raise Exception("FALHA_VISUALIZACAO")
        
        except KeyboardInterrupt:
            print("\n\n⚠ Script cancelado pelo usuário!")
        
        except Exception as e:
            # Verifica se é erro de aba Anexos não disponível
            if "ABA_ANEXOS_NAO_DISPONIVEL" in str(e):
                print("\n" + "="*60)
                print("⚠️ ABA 'ANEXOS' NÃO DISPONÍVEL")
                print("="*60)
                print("\nEste contrato não possui a aba 'Anexos' no portal.")
                print("Não é possível baixar o PDF pois o arquivo não está")
                print("disponível no site de transparência.")
                raise Exception("Aba 'Anexos' não está disponível neste contrato. O PDF não pode ser baixado pois não existe no portal de transparência.")
            else:
                print(f"Erro no run: {e}")
                import traceback
                traceback.print_exc()
        finally:
            try:
                # Fecha apenas a janela do Selenium (não afeta outras abas do Chrome do usuário)
                print("\nFechando navegador do scraper...")
                if self.driver:
                    self.driver.quit()
                    print("✓ Navegador fechado com sucesso!")
            except Exception as e:
                print(f"Erro ao fechar navegador: {e}")
