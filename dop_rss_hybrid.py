import hashlib
import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

# === Step 1: Launch Selenium to fetch live page ===
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920x1080")
options.add_argument("--log-level=3")
options.add_experimental_option('excludeSwitches', ['enable-logging'])

driver = webdriver.Chrome(options=options)
driver.get("https://dop.rajasthan.gov.in/Content/news.aspx")
time.sleep(3)  # let it load

html = driver.page_source
driver.quit()

# === Step 2: Parse table and hash it ===
soup = BeautifulSoup(html, "html.parser")
table = soup.find("table", id="cpMain_grdNews")
if not table:
    raise RuntimeError("❌ Table not found in the page.")

table_html = str(table)
table_hash = hashlib.sha256(table_html.encode()).hexdigest()

# === Step 3: Check for changes using hash file ===
HASH_FILE = "last_hash.txt"
if os.path.exists(HASH_FILE):
    with open(HASH_FILE, "r") as f:
        last_hash = f.read().strip()
    if table_hash == last_hash:
        print("✅ No change detected. Skipping RSS generation.")
        exit()

# Save new hash
with open(HASH_FILE, "w") as f:
    f.write(table_hash)

# === Step 4: Extract data from table ===
rows = table.find_all("tr")[1:]
base_url = "https://dop.rajasthan.gov.in/"

rss = ET.Element("rss", version="2.0")
channel = ET.SubElement(rss, "channel")
ET.SubElement(channel, "title").text = "Rajasthan DOP News Feed"
ET.SubElement(channel, "link").text = "https://dop.rajasthan.gov.in/Content/news.aspx"
ET.SubElement(channel, "description").text = "Live DOP news updates from the Rajasthan government."

for row in rows:
    cells = row.find_all("td")
    if len(cells) != 3:
        continue
    a = cells[1].find("a")
    if not a:
        continue

    title = a.text.strip()
    link = base_url + a['href'].lstrip("..")
    date_raw = cells[2].text.strip()

    try:
        pub_date = datetime.strptime(date_raw, "%d/%m/%Y").strftime("%a, %d %b %Y 10:00:00 +0530")
    except ValueError:
        pub_date = datetime.now().strftime("%a, %d %b %Y 10:00:00 +0530")

    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = title
    ET.SubElement(item, "link").text = link
    ET.SubElement(item, "guid").text = link
    ET.SubElement(item, "pubDate").text = pub_date

# === Step 5: Write RSS file ===
tree = ET.ElementTree(rss)
tree.write("dop_live_feed.xml", encoding="utf-8", xml_declaration=True)
print("✅ New RSS feed written to dop_live_feed.xml")
