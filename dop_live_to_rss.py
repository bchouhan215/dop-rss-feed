from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from datetime import datetime
import time
import xml.etree.ElementTree as ET

# Step 1: Use Selenium to fetch live HTML
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920x1080")
options.add_argument("--log-level=3")
options.add_experimental_option('excludeSwitches', ['enable-logging'])

driver = webdriver.Chrome(options=options)
driver.get("https://dop.rajasthan.gov.in/Content/news.aspx")
time.sleep(3)  # allow page to load

html = driver.page_source
driver.quit()

# Step 2: Parse with BeautifulSoup
soup = BeautifulSoup(html, "html.parser")
table = soup.find("table", id="cpMain_grdNews")
rows = table.find_all("tr")[1:]

base_url = "https://dop.rajasthan.gov.in/"

# Step 3: Build RSS structure
rss = ET.Element("rss", version="2.0")
channel = ET.SubElement(rss, "channel")

ET.SubElement(channel, "title").text = "Rajasthan DOP News Feed"
ET.SubElement(channel, "link").text = "https://dop.rajasthan.gov.in/Content/news.aspx"
ET.SubElement(channel, "description").text = "Live orders and news updates from Department of Personnel, Rajasthan."

# Step 4: Add items
for row in rows:
    cells = row.find_all("td")
    if len(cells) != 3:
        continue

    a_tag = cells[1].find("a")
    if not a_tag:
        continue

    title = a_tag.text.strip()
    href = base_url + a_tag["href"].lstrip("..")
    date_str = cells[2].text.strip()

    try:
        pub_date = datetime.strptime(date_str, "%d/%m/%Y").strftime("%a, %d %b %Y 10:00:00 +0530")
    except:
        pub_date = datetime.now().strftime("%a, %d %b %Y 10:00:00 +0530")

    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = title
    ET.SubElement(item, "link").text = href
    ET.SubElement(item, "guid").text = href
    ET.SubElement(item, "pubDate").text = pub_date

# Step 5: Save the RSS feed
tree = ET.ElementTree(rss)
tree.write("dop_live_feed.xml", encoding="utf-8", xml_declaration=True)

print("✅ RSS feed generated: dop_live_feed.xml")
