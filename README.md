"# V2Ray 节点自动爬取与更新系统

这是一个自动爬取、验证和更新V2Ray节点的系统，通过GitHub Actions定时运行。

## 🚀 主要功能

1. **自动爬取**：从指定网站爬取免费V2Ray节点
2. **智能过滤**：只保留特定国家（美、英、法、德）的节点
3. **验证机制**：验证节点链接的有效性
4. **自动更新**：通过GitHub Actions定时更新
5. **多重备份**：GitHub Raw + JsDelivr CDN + Dpaste镜像

## 📁 文件结构

```
.
├── .github/workflows/update.yml      # GitHub Actions 配置文件
├── v2_cli.py                         # 主爬虫脚本
├── validate_nodes.py                 # 节点验证脚本
├── requirements.txt                  # Python依赖包
├── nodes.txt                         # 生成的节点文件
├── v2_scraper.log                    # 爬虫日志文件
└── README.md                         # 本文件
```

## 🔧 更新内容

### 1. 优化GitHub Actions配置
- **重试机制**：爬虫失败时自动重试3次
- **超时设置**：增加超时时间到30分钟
- **文件检查**：检查生成的节点文件是否有效
- **推送重试**：Git推送失败时重试3次
- **详细日志**：输出详细的执行状态和统计信息

### 2. 增加日志记录
- **结构化日志**：使用Python logging模块
- **文件日志**：日志同时输出到控制台和文件
- **详细统计**：记录爬取过程的详细统计信息
- **错误追踪**：记录所有错误和异常

### 3. 添加验证机制
- **链接验证**：验证节点链接的格式和有效性
- **协议验证**：支持Trojan、Hysteria2、VMess等协议
- **去重处理**：自动过滤重复节点
- **有效性检查**：检查节点链接的基本格式

## 🚀 使用方法

### 本地运行
```bash
# 安装依赖
pip install -r requirements.txt

# 运行爬虫
python v2_cli.py

# 验证节点
python validate_nodes.py
```

### GitHub Actions

系统会自动在以下时间运行：
- 北京时间：00:00, 06:00, 12:00, 18:00
- UTC时间：16:00, 22:00, 04:00, 10:00

也可以手动触发：
1. 进入GitHub仓库的Actions页面
2. 选择"Update V2Ray Nodes"工作流
3. 点击"Run workflow"

## 🔗 访问链接

- **JsDelivr CDN (推荐)**: https://cdn.jsdelivr.net/gh/tronixlizette-glitch/v2-nodes@main/nodes.txt
- **GitHub Raw**: https://raw.githubusercontent.com/tronixlizette-glitch/v2-nodes/main/nodes.txt
- **Dpaste Mirror**: 每次运行后生成新的链接

## 📊 监控与调试

### 日志文件
- `v2_scraper.log` - 爬虫执行日志
- `validate.log` - 验证脚本日志

### 验证结果
- `nodes_validated.txt` - 验证通过的有效节点
- `nodes_invalid.txt` - 验证失败的无效节点

### GitHub Actions日志
- 在Actions页面查看详细执行日志
- 查看Step Summary获取执行统计

## 🔄 更新频率

- **定时运行**：每天4次（每6小时一次）
- **手动触发**：随时可以手动运行
- **条件提交**：只有节点发生变化时才提交

## ⚠️ 注意事项

1. **Chrome依赖**：需要系统中安装Chrome浏览器
2. **网络环境**：GitHub Actions服务器可能受网络限制
3. **目标网站**：如果目标网站结构变化，可能需要更新爬虫
4. **节点有效期**：免费节点通常有效期较短

## 📝 许可证

本项目仅供学习和研究使用，请遵守相关法律法规。"