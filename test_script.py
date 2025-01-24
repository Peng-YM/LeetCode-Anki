from selenium.webdriver.chrome.service import Service
from selenium import webdriver

service = Service(r"C:\Users\blau2\workspace\LeetCode-Anki\vendor\chromedriver.exe")
driver = webdriver.Chrome(service=service)
driver.get("https://www.google.com")
print("Browser launched successfully!")
driver.quit()