"""
节点验证脚本
用于验证爬取到的节点链接的有效性
"""

import re
import requests
import json
import base64
import urllib.parse
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('validate.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def safe_base64_decode(s):
    """安全的Base64解码"""
    if not s:
        return ""
    s = s.strip()
    missing = 4 - len(s) % 4
    if missing:
        s += "=" * missing
    try:
        return base64.urlsafe_b64decode(s).decode("utf-8", errors="ignore")
    except Exception as e:
        logger.debug(f"Base64解码失败: {e}")
        return ""

def validate_trojan_link(link):
    """验证Trojan链接"""
    try:
        # Trojan格式: trojan://password@hostname:port?query#fragment
        parsed = urllib.parse.urlparse(link)
        
        # 检查必要部分
        if not parsed.netloc or "@" not in parsed.netloc:
            return False
            
        # 提取密码和主机信息
        auth_host = parsed.netloc.split("@")
        if len(auth_host) != 2:
            return False
            
        password, host_port = auth_host
        if not password or not host_port:
            return False
            
        # 检查主机和端口
        if ":" not in host_port:
            return False
            
        host, port_str = host_port.split(":", 1)
        if not host or not port_str:
            return False
            
        # 检查端口号
        try:
            port = int(port_str)
            if port < 1 or port > 65535:
                return False
        except ValueError:
            return False
            
        return True
        
    except Exception as e:
        logger.debug(f"Trojan链接验证失败: {e}")
        return False

def validate_hysteria2_link(link):
    """验证Hysteria2链接"""
    try:
        # Hysteria2格式: hysteria2://password@hostname:port?query#fragment
        parsed = urllib.parse.urlparse(link)
        
        # 检查必要部分
        if not parsed.netloc or "@" not in parsed.netloc:
            return False
            
        # 提取密码和主机信息
        auth_host = parsed.netloc.split("@")
        if len(auth_host) != 2:
            return False
            
        password, host_port = auth_host
        if not password or not host_port:
            return False
            
        # 检查主机和端口
        if ":" not in host_port:
            return False
            
        host, port_str = host_port.split(":", 1)
        if not host or not port_str:
            return False
            
        # 检查端口号
        try:
            port = int(port_str)
            if port < 1 or port > 65535:
                return False
        except ValueError:
            return False
            
        # 检查查询参数（可选）
        if parsed.query:
            params = urllib.parse.parse_qs(parsed.query)
            # 可以添加更多参数验证
            
        return True
        
    except Exception as e:
        logger.debug(f"Hysteria2链接验证失败: {e}")
        return False

def validate_vmess_link(link):
    """验证VMess链接"""
    try:
        if not link.startswith("vmess://"):
            return False
            
        # 解码Base64
        encoded = link.replace("vmess://", "")
        decoded = safe_base64_decode(encoded)
        
        if not decoded:
            return False
            
        # 解析JSON
        config = json.loads(decoded)
        
        # 检查必要字段
        required_fields = ["add", "port", "id", "aid", "net", "type", "host", "tls"]
        for field in required_fields:
            if field not in config:
                return False
                
        # 检查端口
        port = config.get("port")
        if not isinstance(port, int) or port < 1 or port > 65535:
            return False
            
        # 检查UUID格式
        uuid = config.get("id", "")
        if not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', uuid, re.I):
            return False
            
        return True
        
    except Exception as e:
        logger.debug(f"VMess链接验证失败: {e}")
        return False

def validate_node_link(link):
    """通用节点链接验证"""
    if not link or not isinstance(link, str):
        return False
    
    # 检查链接长度
    if len(link) < 20 or len(link) > 1000:
        return False
    
    # 根据协议类型调用相应的验证函数
    if link.startswith("trojan://"):
        return validate_trojan_link(link)
    elif link.startswith("hysteria2://"):
        return validate_hysteria2_link(link)
    elif link.startswith("vmess://"):
        return validate_vmess_link(link)
    elif link.startswith("vless://"):
        # VLESS验证（简化版）
        return ":" in link and "@" in link
    elif link.startswith("ss://") or link.startswith("ssr://"):
        # Shadowsocks验证（简化版）
        return ":" in link and "@" in link
    else:
        return False

def check_node_connectivity(link, timeout=5):
    """检查节点连通性（可选，可能较慢）"""
    try:
        # 这里可以添加实际的连通性测试
        # 注意：实际测试可能会消耗较长时间
        return True
    except Exception as e:
        logger.debug(f"连通性检查失败: {e}")
        return False

def validate_nodes_file(filename="nodes.txt"):
    """验证节点文件"""
    logger.info(f"开始验证节点文件: {filename}")
    print(f"[CHECK] 开始验证节点文件: {filename}")
    
    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        logger.error(f"文件不存在: {filename}")
        print(f"[ERROR] 文件不存在: {filename}")
        return False
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        print(f"[ERROR] 读取文件失败: {e}")
        return False
    
    total_nodes = len(lines)
    valid_nodes = []
    invalid_nodes = []
    stats = {
        'trojan': 0,
        'hysteria2': 0,
        'vmess': 0,
        'vless': 0,
        'ss': 0,
        'ssr': 0,
        'other': 0
    }
    
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        # 验证链接
        is_valid = validate_node_link(line)
        
        if is_valid:
            valid_nodes.append(line)
            # 统计协议类型
            if line.startswith("trojan://"):
                stats['trojan'] += 1
            elif line.startswith("hysteria2://"):
                stats['hysteria2'] += 1
            elif line.startswith("vmess://"):
                stats['vmess'] += 1
            elif line.startswith("vless://"):
                stats['vless'] += 1
            elif line.startswith("ss://"):
                stats['ss'] += 1
            elif line.startswith("ssr://"):
                stats['ssr'] += 1
            else:
                stats['other'] += 1
        else:
            invalid_nodes.append(line)
            
        # 进度显示
        if i % 50 == 0 or i == total_nodes:
            print(f"  已验证 {i}/{total_nodes} 个节点")
    
    # 输出结果
    logger.info(f"验证完成:")
    logger.info(f"  总节点数: {total_nodes}")
    logger.info(f"  有效节点: {len(valid_nodes)}")
    logger.info(f"  无效节点: {len(invalid_nodes)}")
    logger.info(f"  有效率: {len(valid_nodes)/total_nodes*100:.2f}%" if total_nodes > 0 else "  有效率: N/A")
    
    print(f"\n[STATS] 验证结果:")
    print(f"  总节点数: {total_nodes}")
    print(f"  有效节点: {len(valid_nodes)}")
    print(f"  无效节点: {len(invalid_nodes)}")
    print(f"  有效率: {len(valid_nodes)/total_nodes*100:.2f}%" if total_nodes > 0 else "  有效率: N/A")
    
    print(f"\n[LIST] 协议分布:")
    for protocol, count in stats.items():
        if count > 0:
            percentage = count/len(valid_nodes)*100 if valid_nodes else 0
            print(f"  {protocol}: {count} 个 ({percentage:.1f}%)")
    
    # 保存有效节点
    if valid_nodes:
        valid_filename = "nodes_validated.txt"
        with open(valid_filename, "w", encoding="utf-8") as f:
            f.write("\n".join(valid_nodes))
        
        logger.info(f"有效节点已保存到: {valid_filename}")
        print(f"\n[OK] 有效节点已保存到: {valid_filename}")
        
        # 保存无效节点（用于调试）
        if invalid_nodes:
            invalid_filename = "nodes_invalid.txt"
            with open(invalid_filename, "w", encoding="utf-8") as f:
                f.write("\n".join(invalid_nodes))
            logger.info(f"无效节点已保存到: {invalid_filename}")
            print(f"[WARN] 无效节点已保存到: {invalid_filename}")
        
        return True
    else:
        logger.warning("未找到有效节点")
        print("[ERROR] 未找到有效节点")
        return False

def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("节点验证脚本开始运行")
    logger.info("=" * 50)
    
    print("[START] 节点验证脚本")
    print("=" * 50)
    
    # 验证节点文件
    success = validate_nodes_file("nodes.txt")
    
    if success:
        logger.info("验证完成，存在有效节点")
        print("\n[OK] 验证完成，存在有效节点")
        return 0
    else:
        logger.error("验证完成，未找到有效节点")
        print("\n[ERROR] 验证完成，未找到有效节点")
        return 1

if __name__ == "__main__":
    exit(main())