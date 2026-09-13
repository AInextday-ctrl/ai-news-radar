# 🤖 AI 资讯雷达 (AI Radar)

零成本（$0/月）全自动 AI 资讯情报站，支持多源抓取、Google Gemini AI 智能翻译与提炼一句话看点、深色极客风四分栏实时看板，并一键部署到 Google Firebase Hosting。

---

## 🌟 核心特色

1. **四分栏全景视野**：
   - ⚡ **突发·行业快讯**：TechCrunch AI、The Verge AI、Hacker News AI 热榜
   - 🐦 **名人·大V观点**：马斯克、奥特曼、LeCun 等行业领袖最新发声与专访
   - 🛠️ **爆款·新AI工具**：Hugging Face 趋势模型与 GitHub AI 热门开源项目
   - 💡 **实操·前沿精选**：Reddit LocalLLaMA 避坑心得、ArXiv CS.AI 预印论文
2. **零服务器成本**：
   - 采用 Serverless 纯静态架构，托管在 Google Firebase Hosting CDN。
   - 利用 GitHub Actions 定时任务每 30 分钟在云端自动运行爬虫并发布，电脑关机也能 7×24 小时自动更新。
3. **AI 智能提炼看点**：
   - 对接 Google Gemini 2.5 Flash 免费接口，自动将外文资讯转为中文，并提炼 30~50 字的一句话核心价值看点。
4. **前端自动无感刷新**：
   - 看板每 30 秒自动检测本地/云端最新数据，有新内容即刻平滑更新。

---

## 📂 项目结构

```text
├── .github/workflows/
│   └── update_and_deploy.yml   # GitHub Actions 云端 7x24 小时定时抓取与部署脚本
├── data/
│   └── latest_news.json        # 本地抓取并生成的结构化资讯数据
├── public/                     # 发布到 Firebase Hosting 的静态站点目录
│   ├── index.html              # 极客风四分栏前端看板 (Tailwind CSS)
│   └── data/latest_news.json   # 供前端实时轮询的线上数据源
├── config.py                   # 抓取源与分类规则配置
├── fetcher.py                  # 多平台免 Key 资讯抓取引擎
├── processor.py                # Gemini AI 翻译、摘要与打标签中枢
├── main.py                     # 全流程调度主入口
├── firebase.json               # Firebase Hosting 配置文件
└── requirements.txt            # Python 依赖清单
```

---

## 🚀 本地运行与调试

### 1. 安装依赖
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Mac / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. 配置 Gemini API Key
复制 `.env.example` 为 `.env`：
```env
GEMINI_API_KEY=你的Gemini_API_Key
GEMINI_MODEL=gemini-2.5-flash
```
> 可前往 [Google AI Studio](https://aistudio.google.com/) 免费创建 API Key。

### 3. 执行抓取与整理
```bash
python main.py
```

### 4. 预览看板
打开浏览器访问：
```text
http://localhost:8080/public/index.html
```

---

## 🌐 部署上线到 Google 免费网址 (Firebase Hosting)

1. **登录 Firebase**：
   ```bash
   npx firebase login
   ```
2. **关联项目**：
   ```bash
   npx firebase use --add
   ```
3. **一键部署**：
   ```bash
   npx firebase deploy --only hosting
   ```
   部署完成后即可获得官方免费网址：`https://<你的项目名>.web.app`！
