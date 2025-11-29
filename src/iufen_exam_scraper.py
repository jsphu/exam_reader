from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType # Import this!
import time
import os
# Uses Chromium
def href_link_scraper(URL, port, text, chromium_path):
    """Gets link from given text in URL"""

    options = webdriver.ChromeOptions()

    options.add_argument("--headless")
    options.add_argument("--no-sandbox") # Bypass OS security model
    options.add_argument("--disable-dev-shm-usage") # Overcome limited resource problems
    options.add_argument("--disable-gpu") # Applicable to windows os only but good practice
    options.add_argument(f"--remote-debugging-port={port}") # Helps with the port error
    options.binary_location = chromium_path

    service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())

    try:
        driver = webdriver.Chrome(service=service, options=options)

        driver.get(URL)

        time.sleep(1) # Wait for JS to render

        # Find the link containing the text
        element = driver.find_element(By.XPATH, text)
        href_link = element.get_attribute('href')

    except Exception as e:
        print(f"Error: {e}")
        href_link = None

    finally:
        # Check if driver was actually created before quitting
        if 'driver' in locals():
            driver.quit()

    return href_link

if __name__ == "__main__":
    from config import CONFIG as cfg

    CONFIG = cfg() # initiation
    URL = CONFIG.URL
    port = CONFIG.port
    text = CONFIG.text
    chromium_path = CONFIG.chromium_path

    print(href_link_scraper(URL, port, text, chromium_path))
