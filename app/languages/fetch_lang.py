# Requires: pip install selenium and ChromeDriver installed in PATH
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import os
import requests
from bs4 import BeautifulSoup

BASE_PAGE = "https://www.argosopentech.com/argospm/index/"
BASE_DIR = "lang_models"
os.makedirs(BASE_DIR, exist_ok=True)

print("🌐 Launching headless browser to fetch JavaScript-rendered page...")
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=chrome_options)
driver.get(BASE_PAGE)
time.sleep(5)  # Wait for JavaScript to render
html = driver.page_source
driver.quit()

soup = BeautifulSoup(html, "html.parser")

rows = soup.find_all("tr")
download_count = 0

print("📥 Scanning for English → X model download links...")

for row in rows:
    cols = row.find_all("td")
    if len(cols) >= 3:
        source_lang = cols[0].get_text(strip=True)
        if source_lang.lower() == "english":
            print(f"🔎 Found row: {row}")
            print(f"🔗 Link column: {cols[2]}")
            download_link = cols[2].find("a", href=True)
            if download_link:
                href = download_link["href"]
                if not href.startswith("http"):
                    href = f"https://www.argosopentech.com{href}"
                if href.endswith(".argosmodel"):
                    url = href
                    filename = url.split("/")[-1]
                    dest_path = os.path.join(BASE_DIR, filename)

                    if os.path.exists(dest_path):
                        print(f"⚠️ Skipping (already downloaded): {filename}")
                        continue

                    print(f"⬇️ Downloading: {filename}")
                    try:
                        file_data = requests.get(url)
                        file_data.raise_for_status()
                        with open(dest_path, "wb") as f:
                            f.write(file_data.content)
                        print(f"✅ Saved: {filename}")
                        download_count += 1
                    except Exception as e:
                        print(f"❌ Error downloading {filename}: {e}")
            else:
                print(f"🚫 No valid link found in: {cols[2]}")

print(f"\n📊 Download summary: {download_count} new models saved to '{BASE_DIR}'.")