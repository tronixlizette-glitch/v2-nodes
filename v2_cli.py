import re
import requests
import base64
import json
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import os
from webdriver_manager.chrome import ChromeDriverManager

def safe_base64_decode(s):
    if not s:
        return ""
    s = s.strip()
    missing = 4 - len(s) % 4
    if missing:
        s += "=" * missing
    try:
        return base64.urlsafe_b64decode(s).decode("utf-8", errors="ignore")
    except:
        return ""

def get_node_name(link):
    try:
        if link.startswith("vmess://"):
            data = safe_base64_decode(link.replace("vmess://", ""))
            if data:
                return json.loads(data).get("ps", "")
        elif "://" in link:
            return urllib.parse.unquote(urllib.parse.urlparse(link).fragment)
    except:
        pass
    return ""

def is_target_country(name):
    if not name:
        return False
    keywords = [
        "美国", "united states", " us ", "(us)", "[us]", "🇺🇸",
        "英国", "united kingdom", " uk ", "(uk)", "[uk]", "🇬🇧",
        "法国", "france", " fr ", "(fr)", "[fr]", "🇫🇷",
        "德国", "germany", " de ", "(de)", "[de]", "🇩🇪"
    ]
    name_l = name.lower()
    return any(k in name_l for k in keywords)

def run_scraper():
    url = "https://v2raya.net/free-nodes/free-v2ray-node-subscriptions.html"
    print(f"Starting scraping: {url}")

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    final_node_list = []

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)
        time.sleep(10) 
        html = driver.page_source
        driver.quit()
    except Exception as e:
        print(f"Selenium Error: {e}")
        return

    subs = list(set(re.findall(r"https://fn12[^\s\"'<]+", html)))
    if not subs:
        print("No subscription links found")
        return

    print(f"Found {len(subs)} sources")

    for i, sub in enumerate(subs):
        print(f"[{i+1}/{len(subs)}] Parsing {sub}")
        try:
            r = requests.get(sub, timeout=20)
            text = safe_base64_decode(r.text.strip()) or r.text
            count = 0
            for line in text.splitlines():
                name = get_node_name(line)
                if is_target_country(name):
                    final_node_list.append(line)
                    count += 1
            print(f"   -> Hit {count} nodes")
        except Exception as e:
            print(f"   -> Error: {e}")

    final_node_list = list(set(final_node_list))
    print(f"Done, filtered {len(final_node_list)} nodes total")

    if final_node_list:
        with open("nodes.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(final_node_list))
        print("Saved to nodes.txt")
        
        try:
            nodes_text = "\n".join(final_node_list)
            b64 = base64.b64encode(nodes_text.encode()).decode()
            r = requests.post("https://dpaste.com/api/", data={"content": b64, "expiry_days": 1}, timeout=10)
            if r.status_code in (200, 201):
                print(f"Dpaste Link: {r.text.strip()}.txt")
        except:
            pass

if __name__ == "__main__":
    run_scraper()
