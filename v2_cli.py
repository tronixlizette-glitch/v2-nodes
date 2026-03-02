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

def safe_base64_decode(s):
    if not s: return ""
    s = s.strip()
    missing = 4 - len(s) % 4
    if missing: s += "=" * missing
    try:
        return base64.urlsafe_b64decode(s).decode("utf-8", errors="ignore")
    except: return ""

def get_node_name(link):
    try:
        if link.startswith("vmess://"):
            data = safe_base64_decode(link.replace("vmess://", ""))
            if data: return json.loads(data).get("ps", "")
        elif "://" in link:
            return urllib.parse.unquote(urllib.parse.urlparse(link).fragment)
    except: pass
    return ""

def is_target_country(name):
    if not name: return False
    keywords = ["美国", "united states", " us ", "(us)", "[us]", "🇺🇸", "英国", "united kingdom", " uk ", "(uk)", "[uk]", "🇬🇧", "法国", "france", " fr ", "(fr)", "[fr]", "🇫🇷", "德国", "germany", " de ", "(de)", "[de]", "🇩🇪"]
    name_l = name.lower()
    return any(k in name_l for k in keywords)

def run_scraper():
    url = "https://v2raya.net/free-nodes/free-v2ray-node-subscriptions.html"
    print(f"Starting scraping: {url}")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    final_node_list = []
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        driver.get(url)
        time.sleep(15) # 增加等待时间
        html = driver.page_source
        print(f"Page loaded, HTML length: {len(html)}")
        driver.quit()
    except Exception as e:
        print(f"Selenium Error: {e}")
        # 如果 Selenium 失败，尝试直接 Requests (备用方案)
        try:
            print("Trying requests as fallback...")
            html = requests.get(url, timeout=20).text
        except: return

    subs = list(set(re.findall(r"https://fn12[^\s\"'<]+", html)))
    print(f"Found {len(subs)} sources")

    for i, sub in enumerate(subs):
        try:
            r = requests.get(sub, timeout=15)
            text = safe_base64_decode(r.text.strip()) or r.text
            for line in text.splitlines():
                if is_target_country(get_node_name(line)):
                    final_node_list.append(line)
        except: pass

    final_node_list = list(set(final_node_list))
    print(f"Total filtered nodes: {len(final_node_list)}")

    # 无论是否找到节点，都创建一个文件，防止报错
    with open("nodes.txt", "w", encoding="utf-8") as f:
        if final_node_list:
            f.write("\n".join(final_node_list))
            print("Saved nodes to nodes.txt")
        else:
            f.write("No nodes found at " + time.strftime("%Y-%m-%d %H:%M:%S"))
            print("No nodes found, created empty nodes.txt")

if __name__ == "__main__":
    run_scraper()
