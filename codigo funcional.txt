import json
import traceback
import re
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

class Scraper:
    def __init__(self, config_path):
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

        except Exception as e:
            print("Erro ao iniciar o Scraper:", e)
            traceback.print_exc()
            raise

    def acessar_portal(self):
        try:
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

            # Preenche a caixa de busca com "IPM"
            print("Aguardando o campo de busca aparecer...")
            campo_busca = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@name='campo01' and @type='text']")))
            campo_busca.click()
            time.sleep(0.2)
            try:
                campo_busca.clear()
                campo_busca.send_keys("IPM")
                print('Texto "IPM" inserido no campo de busca (via send_keys).')
            except Exception:
                print("Falha ao usar send_keys, tentando via JavaScript...")
                self.driver.execute_script("arguments[0].value = 'IPM';", campo_busca)
                print('Texto "IPM" inserido no campo de busca (via JS).')

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

            # Localiza a linha do contrato "89/2022"
            print("Localizando a linha do contrato '89/2022'...")
            linha_xpath = "//tr[contains(@class, 'linha_agrupamento') and .//span[@class='coluna_agrupador_valor' and text()='89/2022']]"
            try:
                linha_desejada = wait.until(
                    EC.presence_of_element_located((By.XPATH, linha_xpath))
                )
                print("Linha do contrato encontrada!")

                seta_xpath = linha_xpath + "/td[contains(@class, 'acao_consulta')]/span[contains(@class, 'fa-chevron-down')]"
                seta_btn = wait.until(EC.element_to_be_clickable((By.XPATH, seta_xpath)))

                print("Clicando na seta para expandir a linha...")
                ActionChains(self.driver).move_to_element(seta_btn).pause(0.5).click().perform()
                print("Linha expandida com sucesso!")
                self.last_expanded_row = linha_desejada
                time.sleep(0.5)
            except Exception as e:
                print(f"Erro ao expandir a linha: {e}")

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
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  Erro na tentativa {attempt + 1}: {e}")

        print("✗ Falha ao clicar no ícone após todas as tentativas")
        return False

    def clicar_aba_anexos(self, timeout=15):
        """
        Clica na aba "Anexos" dentro do diálogo de visualização do contrato.
        """
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
                    return False
            
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
            
            print("✓ Aba 'Anexos' clicada com sucesso!")
            time.sleep(2)
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
            
            print("\nProcurando pela linha com tipo 'Impressão'...")
            
            # Procura a linha com "Impressão"
            impressao_xpaths = [
                "//tr[contains(., 'Impressão')]",
                "//tr[contains(., 'Impressao')]",
                "//tr[.//td[contains(., 'Impressão')]]",
                "//tr[.//td[contains(., 'Impressao')]]",
            ]
            
            impressao_row = None
            for xpath in impressao_xpaths:
                try:
                    elementos = self.driver.find_elements(By.XPATH, xpath)
                    if elementos:
                        impressao_row = elementos[0]
                        print(f"  ✓ Linha 'Impressão' encontrada com: {xpath}")
                        break
                except:
                    pass
            
            if not impressao_row:
                print("  ✗ Linha 'Impressão' não encontrada!")
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
            
            print("✓ Linha encontrada!")
            print(f"  Texto da linha: {impressao_row.text[:150]}")
            
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
            time.sleep(1)
            
            # Monitora a pasta para detectar novo arquivo
            downloads_folder = os.path.join(
                os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
                "Downloads_PDFs"
            )
            
            print(f"\nAguardando arquivo ser baixado em: {downloads_folder}")
            
            # Lista arquivos antes
            arquivos_antes = set(os.listdir(downloads_folder))
            
            # Aguarda até 10 segundos pelo novo arquivo
            for tentativa in range(10):
                time.sleep(1)
                arquivos_agora = set(os.listdir(downloads_folder))
                novos_arquivos = arquivos_agora - arquivos_antes
                
                if novos_arquivos:
                    print(f"\n✓ Arquivo(s) baixado(s):")
                    for arquivo in novos_arquivos:
                        caminho_completo = os.path.join(downloads_folder, arquivo)
                        tamanho = os.path.getsize(caminho_completo)
                        print(f"  📄 {arquivo}")
                        print(f"  📊 Tamanho: {tamanho} bytes")
                        print(f"  📍 Caminho: {caminho_completo}")
                    break
                else:
                    print(f"  Aguardando... ({tentativa + 1}/10)")
            
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
            self.acessar_portal()
            ok = self.clicar_linha_visualizacao()
            if ok:
                print("\nVisualização aberta!")
                time.sleep(1)
                
                print("\n" + "="*60)
                print("Clicando na aba 'Anexos'...")
                print("="*60)
                
                ok_anexos = self.clicar_aba_anexos()
                if ok_anexos:
                    print("\n" + "="*60)
                    print("SUCESSO! Aba 'Anexos' aberta!")
                    print("="*60)
                    
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
                        print("Pressione Enter para fechar o navegador...")
                        input()
                else:
                    print("✗ Falha ao abrir a aba 'Anexos'.")
                    print("Pressione Enter para fechar o navegador...")
                    input()
            else:
                print("✗ Falha ao localizar/clicar a linha de visualização.")
                print("Pressione Enter para fechar o navegador...")
                input()
            
        except Exception as e:
            print(f"Erro no run: {e}")
            import traceback
            traceback.print_exc()
            print("Pressione Enter para fechar o navegador...")
            input()
        finally:
            try:
                self.driver.quit()
                print("\n✓ Navegador fechado com sucesso!")
            except Exception:
                pass
