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
import logging
from datetime import datetime
from webdriver_manager.chrome import ChromeDriverManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('v2_scraper.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def safe_base64_decode(s):
    if not s:
        return ""
    s = s.strip()
    missing = 4 - len(s) % 4
    if missing:
        s += "=" * missing
    try:
        return base64.urlsafe_b64decode(s).decode("utf-8", errors="ignore")
    except Exception as e:
        logger.warning(f"Base64解码失败: {e}")
        return ""

def get_node_name(link):
    try:
        if link.startswith("vmess://"):
            data = safe_base64_decode(link.replace("vmess://", ""))
            if data:
                return json.loads(data).get("ps", "")
        elif "://" in link:
            return urllib.parse.unquote(urllib.parse.urlparse(link).fragment)
    except Exception as e:
        logger.debug(f"获取节点名称失败: {e}")
    return ""

def is_target_country(name):
    if not name:
        return False
    keywords = [
        "美国", "united states", " us ", "(us)", "[us]",
        "英国", "united kingdom", " uk ", "(uk)", "[uk]",
        "法国", "france", " fr ", "(fr)", "[fr]",
        "德国", "germany", " de ", "(de)", "[de]"
    ]
    name_l = name.lower()
    return any(k in name_l for k in keywords)

def validate_node_link(link):
    """验证节点链接的有效性"""
    if not link or not isinstance(link, str):
        return False
    
    # 检查链接格式
    valid_protocols = ["trojan://", "hysteria2://", "vmess://", "vless://", "ss://", "ssr://"]
    if not any(link.startswith(proto) for proto in valid_protocols):
        logger.debug(f"无效协议: {link[:50]}...")
        return False
    
    # 检查链接长度
    if len(link) < 20 or len(link) > 1000:
        logger.debug(f"链接长度异常: {len(link)} 字符")
        return False
    
    # 检查是否包含必要部分
    if "@" not in link or ":" not in link:
        logger.debug(f"链接格式不完整: {link[:50]}...")
        return False
    
    return True

def filter_duplicate_nodes(node_list):
    """过滤重复节点"""
    unique_nodes = []
    seen = set()
    
    for node in node_list:
        # 提取节点特征用于去重
        node_hash = hash(node.strip())
        if node_hash not in seen:
            seen.add(node_hash)
            unique_nodes.append(node)
    
    logger.info(f"去重前: {len(node_list)} 个节点, 去重后: {len(unique_nodes)} 个节点")
    return unique_nodes

def run_scraper():
    """主爬虫函数"""
    start_time = datetime.now()
    url = "https://v2raya.net/free-nodes/free-v2ray-node-subscriptions.html"
    logger.info(f"开始爬取: {url}")
    print(f"[START] 开始爬取: {url}")

    # Chrome 配置
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    final_node_list = []
    stats = {
        'total_sources': 0,
        'successful_sources': 0,
        'failed_sources': 0,
        'total_nodes_found': 0,
        'valid_nodes': 0
    }

    try:
        logger.info("正在初始化Chrome浏览器...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        logger.info(f"正在访问页面: {url}")
        driver.get(url)
        time.sleep(15)  # 增加等待时间确保页面加载完成
        
        # 检查页面是否加载成功
        if "404" in driver.title or "Not Found" in driver.page_source:
            logger.error("页面未找到或加载失败")
            driver.quit()
            return False
            
        html = driver.page_source
        driver.quit()
        logger.info("页面抓取成功")
        
    except Exception as e:
        logger.error(f"Selenium 错误: {e}")
        print(f"[ERROR] Selenium 错误: {e}")
        return False

    # 提取订阅链接
    subs = list(set(re.findall(r"https://fn12[^\s\"'<]+", html)))
    stats['total_sources'] = len(subs)
    
    if not subs:
        logger.warning("未找到订阅链接")
        print("[WARN] 未找到订阅链接")
        return False

    logger.info(f"找到 {len(subs)} 个订阅源")
    print(f"[STATS] 找到 {len(subs)} 个订阅源")

    # 处理每个订阅源
    for i, sub in enumerate(subs):
        logger.info(f"[{i+1}/{len(subs)}] 正在解析: {sub}")
        print(f"[{i+1}/{len(subs)}] 正在解析: {sub[:50]}...")
        
        try:
            r = requests.get(sub, timeout=25, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if r.status_code != 200:
                logger.warning(f"   HTTP {r.status_code}: {sub}")
                stats['failed_sources'] += 1
                continue
                
            text = safe_base64_decode(r.text.strip()) or r.text
            
            if not text:
                logger.warning(f"   内容为空: {sub}")
                stats['failed_sources'] += 1
                continue
                
            count = 0
            lines = text.splitlines()
            stats['total_nodes_found'] += len(lines)
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # 验证节点链接
                if validate_node_link(line):
                    name = get_node_name(line)
                    if is_target_country(name):
                        final_node_list.append(line)
                        count += 1
                        stats['valid_nodes'] += 1
            
            logger.info(f"   成功获取 {count} 个节点")
            stats['successful_sources'] += 1
            
        except requests.exceptions.Timeout:
            logger.warning(f"   请求超时: {sub}")
            stats['failed_sources'] += 1
        except requests.exceptions.RequestException as e:
            logger.warning(f"   请求错误: {e}")
            stats['failed_sources'] += 1
        except Exception as e:
            logger.error(f"   解析错误: {e}")
            stats['failed_sources'] += 1

    # 去重处理
    final_node_list = filter_duplicate_nodes(final_node_list)
    
    # 统计信息
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info(f"\n[STATS] 爬取统计:")
    logger.info(f"   总订阅源: {stats['total_sources']}")
    logger.info(f"   成功订阅源: {stats['successful_sources']}")
    logger.info(f"   失败订阅源: {stats['failed_sources']}")
    logger.info(f"   发现总节点: {stats['total_nodes_found']}")
    logger.info(f"   有效节点: {stats['valid_nodes']}")
    logger.info(f"   最终节点(去重后): {len(final_node_list)}")
    logger.info(f"   耗时: {duration:.2f} 秒")
    
    print(f"\n[STATS] 爬取统计:")
    print(f"   总订阅源: {stats['total_sources']}")
    print(f"   成功订阅源: {stats['successful_sources']}")
    print(f"   失败订阅源: {stats['failed_sources']}")
    print(f"   发现总节点: {stats['total_nodes_found']}")
    print(f"   有效节点: {stats['valid_nodes']}")
    print(f"   最终节点(去重后): {len(final_node_list)}")
    print(f"   耗时: {duration:.2f} 秒")

    # 保存结果
    if final_node_list:
        content = "\n".join(final_node_list)
        with open("nodes.txt", "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.info(f"已保存到 nodes.txt (共 {len(final_node_list)} 个节点)")
        print(f"[OK] 已保存到 nodes.txt (共 {len(final_node_list)} 个节点)")
        
        # 输出访问链接
        print("\n--- 访问链接 ---")
        print("GitHub Raw: https://raw.githubusercontent.com/tronixlizette-glitch/v2-nodes/main/nodes.txt")
        print("JsDelivr CDN: https://cdn.jsdelivr.net/gh/tronixlizette-glitch/v2-nodes@main/nodes.txt")
        
        try:
            # 上传到 dpaste.com 作为备份
            r = requests.post("https://dpaste.com/api/", 
                            data={"content": content, "expiry_days": 1}, 
                            timeout=15)
            if r.status_code in (200, 201):
                dpaste_url = r.text.strip() + ".txt"
                print(f"Dpaste Mirror: {dpaste_url}")
                logger.info(f"Dpaste 镜像: {dpaste_url}")
        except Exception as e:
            logger.warning(f"Dpaste 上传失败: {e}")
        
        print("--------------------\n")
        return True
    else:
        logger.warning("未找到有效节点")
        print("[WARN] 未找到有效节点")
        return False

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("V2Ray 节点爬虫开始运行")
    logger.info("=" * 50)
    
    success = run_scraper()
    
    if success:
        logger.info("爬虫执行成功")
        exit(0)
    else:
        logger.error("爬虫执行失败")
        exit(1)