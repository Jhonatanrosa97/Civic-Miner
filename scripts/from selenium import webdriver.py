from selenium import webdriver
from selenium.webdriver.common.by import By

# Inicializa o driver do navegador (exemplo com Chrome)
driver = webdriver.Chrome()

# Exemplo de definição do elemento botao_visualizar
botao_visualizar_xpath = ".//span[contains(@class, 'fa-eye')]"
botao_visualizar = driver.find_element(By.XPATH, botao_visualizar_xpath)  # Certifique-se de que 'driver' está definido

# Verifica se o botão está visível
if botao_visualizar.is_displayed():
    print("Botão 'Visualizar' está visível!")
else:
    print("Botão 'Visualizar' não está visível. Tentando via JavaScript...")