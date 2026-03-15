import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType # Import this!
import time
import os

logger = logging.getLogger("exam_reader")

# Uses Chromium
def href_link_scraper(URL, port, text, chromium_path):
    """Gets link from given text in URL"""

    logger.log(1, f"Configuring Chrome for URL: {URL}")
    options = webdriver.ChromeOptions()

    options.add_argument("--headless")
    options.add_argument("--no-sandbox") # Bypass OS security model
    options.add_argument("--disable-dev-shm-usage") # Overcome limited resource problems
    options.add_argument("--disable-gpu") # Applicable to windows os only but good practice
    options.add_argument(f"--remote-debugging-port={port}") # Helps with the port error
    options.binary_location = chromium_path

    service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())

    try:
        logger.log(1, "Starting Chrome driver instance...")
        driver = webdriver.Chrome(service=service, options=options)

        logger.log(1, f"Accessing URL: {URL}")
        driver.get(URL)

        logger.log(1, "Waiting for JS rendering (1s)...")
        time.sleep(1) # Wait for JS to render

        # Find the link containing the text
        logger.log(1, f"Finding element by XPath: {text}")
        element = driver.find_element(By.XPATH, text)
        href_link = element.get_attribute('href')
        logger.log(30, f"Successfully scraped target link: {href_link}")

    except Exception as e:
        logger.log(50, f"Error in href_link_scraper: {e}")
        raise e

    finally:
        # Check if driver was actually created before quitting
        if 'driver' in locals():
            logger.log(1, "Quitting Chrome driver.")
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
