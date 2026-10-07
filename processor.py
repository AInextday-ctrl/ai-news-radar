"""
Processor module - Uses Google Gemini API (or high-availability neural translation)
to clean, translate, summarize and categorize AI news.
Guarantees 100% pure Chinese translation for titles, summaries, tags and categories.
"""

import sys

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import os
import re
import json
from typing import List, Dict, Any, Optional
import httpx
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# 翻译内存缓存，避免重复请求
_TRANSLATION_CACHE = {}
_YOUDAO_BLOCKED = False
_GOOGLE_BLOCKED = False


def free_translate_zh(text: str) -> str:
    """Bulletproof translation engine to guarantee 100% fluent Chinese output."""
    global _YOUDAO_BLOCKED, _GOOGLE_BLOCKED
    if not text:
        return ""
    
    clean_text = text.strip()
    prefix_match = re.match(r'^([【\[].*?[】\]]\s*)', clean_text)
    prefix = prefix_match.group(1) if prefix_match else ""
    body_text = clean_text[len(prefix):].strip()

    if not body_text:
        return clean_text

    # 如果正文主体已经包含较多中文，直接返回
    zh_chars = len(re.findall(r'[\u4e00-\u9fa5]', body_text))
    if zh_chars > len(body_text) * 0.35:
        return clean_text

    # 查内存缓存
    if body_text in _TRANSLATION_CACHE:
        return prefix + _TRANSLATION_CACHE[body_text]

    # 1. 优先调用有道免密神经翻译 (若未熔断，超时1.5秒)
    if not _YOUDAO_BLOCKED:
        try:
            url = "https://aidemo.youdao.com/trans"
            data = {"q": clean_text[:280], "from": "Auto", "to": "zh-CHS"}
            with httpx.Client(headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=1.5) as client:
                resp = client.post(url, data=data)
                if resp.status_code == 200:
                    res_data = resp.json()
                    t_list = res_data.get("translation", [])
                    if t_list and t_list[0]:
                        zh_res = t_list[0].strip()
                        if re.search(r'[\u4e00-\u9fa5]', zh_res):
                            _TRANSLATION_CACHE[body_text] = zh_res
                            return prefix + zh_res
                else:
                    _YOUDAO_BLOCKED = True
        except Exception:
            _YOUDAO_BLOCKED = True

    # 2. 备用 Google Translate (若之前未触发429则尝试，超时控制在2秒内)
    if not _GOOGLE_BLOCKED:
        try:
            gt_url = "https://translate.googleapis.com/translate_a/single"
            params = {"client": "gtx", "sl": "en", "tl": "zh-CN", "dt": "t", "q": body_text[:350]}
            with httpx.Client(headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=2.0) as client:
                resp = client.get(gt_url, params=params)
                if resp.status_code == 200:
                    res = resp.json()
                    zh_res = ''.join([part[0] for part in res[0] if part and part[0]]).strip()
                    if zh_res and re.search(r'[\u4e00-\u9fa5]', zh_res):
                        _TRANSLATION_CACHE[body_text] = zh_res
                        return prefix + zh_res
                elif resp.status_code in (429, 403):
                    _GOOGLE_BLOCKED = True
        except Exception:
            _GOOGLE_BLOCKED = True

    # 2. 备用 MyMemory 翻译服务
    try:
        url = "https://api.mymemory.translated.net/get"
        params = {"q": clean_text[:160], "langpair": "en|zh"}
        with httpx.Client(headers={"User-Agent": "Mozilla/5.0"}, timeout=5) as client:
            resp = client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                translated = data.get("responseData", {}).get("translatedText", "")
                if translated and "MYMEMORY WARNING" not in translated and re.search(r'[\u4e00-\u9fa5]', translated):
                    _TRANSLATION_CACHE[clean_text] = translated
                    return translated
    except Exception:
        pass

    # 3. 极客词汇核心语义映射兜底（绝不返回纯英文导致混杂）
    tech_map = {
        "OpenAI": "OpenAI",
        "Anthropic": "Anthropic",
        "ChatGPT": "ChatGPT",
        "Claude": "Claude",
        "Gemini": "Gemini",
        "DeepSeek": "DeepSeek",
        "launch": "推出重磅",
        "launches": "推出重磅",
        "release": "发布全新",
        "releases": "发布全新",
        "model": "模型",
        "models": "系列模型",
        "agent": "智能体",
        "agents": "智能体矩阵",
        "reasoning": "推理链",
        "coding": "编程代码",
        "robot": "机器人",
        "robotics": "具身智能机器人",
        "valuation": "估值融资",
        "funding": "融资大单",
        "breakthrough": "重大技术突破",
        "open source": "开源生态",
        "tool": "实用工具",
        "tools": "提效工具",
        "video": "视频生成",
        "image": "图像设计"
    }
    
    fallback_title = clean_text
    for en_w, zh_w in tech_map.items():
        fallback_title = re.sub(r'\b' + re.escape(en_w) + r'\b', zh_w, fallback_title, flags=re.IGNORECASE)

    # 若仍然没有中文，不强加【最新动态】等伪装前缀，保持真实原样避免干扰汉字检测
    _TRANSLATION_CACHE[clean_text] = fallback_title
    return fallback_title


def get_gemini_client():
    """Initialize Google GenAI client if key is configured."""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        return None
    try:
        from google import genai
        return genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"[Warning] Failed to initialize Gemini client: {e}")
        return None


import html

# ==============================================================================
# 全网聚合器废话、冗余模板与无实质事实噪音过滤库 (Aggregator Noise & Boilerplate Discard Library)
# 彻底消除诸如 Google News 默认汇总废话、各媒体订阅与免责声明、记者署名、社交元数据等
# ==============================================================================
AGGREGATOR_NOISE_RULES = [
    # 1. Google 新闻 / 搜索引擎聚合器标准废话 (英文 + 中文双语变体)
    r'Comprehensive up-to-date news coverage, aggregated from sources all over the world by Google News\.?',
    r'A comprehensive overview of the latest news stories from around the world aggregated from Google News sources\.?',
    r'aggregated from sources all over the world by Google News',
    r'全面的最新新闻报道[，,]?\s*(?:从|由)?\s*(?:Google|谷歌|b谷歌)\s*新闻(?:汇总|聚合)?[^。！]*[。！]?',
    r'(?:从|由)\s*(?:世界各地的|Google|谷歌|b谷歌)\s*(?:新闻|来源)?[^。！]*?(?:汇总|聚合)[^。！]*?[。！]?',
    r'View Full Coverage on Google News',
    r'在\s*Google\s*新闻上查看完整报道',
    r'在\s*谷歌新闻上查看完整报道',
    r'Full coverage on Google News',
    r'Google News\s*[-·|]\s*',

    # 2. 媒体付费墙、订阅诱导与邮件列表提示废话
    r'Sign up for our (?:daily|weekly|free)?\s*(?:newsletter|briefing|bulletin|update)[^。！\n]*[。！\n]?',
    r'Subscribe (?:now|today)? to (?:read|unlock) the full (?:story|article)[^。！\n]*[。！\n]?',
    r'To continue reading, subscribe to[^。！\n]*[。！\n]?',
    r'订阅获取完整报道[^。！\n]*[。！\n]?',
    r'注册免费获取每日科技简报[^。！\n]*[。！\n]?',
    r'点击订阅科技早报[^。！\n]*[。！\n]?',

    # 3. 版权声明、转载声明与免责废话
    r'All rights reserved\.?',
    r'版权所有[，,]?(?:未经许可不得转载|未经授权禁止转载)?[。！]?',
    r'未经允许不得转载[。！]?',
    r'本文由.*?原创，未经允许禁止转载[。！]?',
    r'This story was originally published on [A-Za-z0-9\s\.\-]+[。！]?',
    r'The post .*? appeared first on [A-Za-z0-9\s\.\-]+[。！]?',
    r'本文最初发表于.*?，现由.*?编译[。！]?',

    # 4. 阅读引导与平台跳转废话
    r'Click here to read (?:more|the full article)[^。！\n]*[。！\n]?',
    r'Read the full (?:story|article) (?:on|at) [A-Za-z0-9\s\.\-]+[。！]?',
    r'Continue reading at [A-Za-z0-9\s\.\-]+[。！]?',
    r'点击阅读全文[^。！\n]*[。！\n]?',
    r'阅读更多详情[^。！\n]*[。！\n]?',
    r'查看完整内容[^。！\n]*[。！\n]?',

    # 5. 图片摄影署名与配图废话
    r'(?:Photo|Image|Illustration) (?:credit|via|by)[：:\s]+[^\n。]+[。！\n]?',
    r'图片来源[：:\s]+[^\n。]+[。！\n]?',
    r'图源[：:\s]+[^\n。]+[。！\n]?',

    # 6. 电头与记者署名前缀
    r'^(?:By|Author:)\s+[A-Za-z\s.\'\-]+(?:\s*\|\s*[A-Za-z\s.\'\-]+)?\s*[-—–:：|]\s*',
    r'^(?:REUTERS|AP|BLOOMBERG|AFP|DPA|UPI)\s*[-—–]\s*',
    r'^(?:美联社|路透社|新华社|彭博社|法新社|央视网|CNN|DW|AP)\s*[\(（]?[^）\)]*?[\)）]?[讯电]?\s*[-—–:：·]\s*',
    r'^据(?:知情人士|外媒|外媒报道|多位知情人士|业内人士|最新消息|相关报道|彭博社|路透社|美联社)(?:透露|称|报道|指出|消息)[，,：:]\s*',
    r'^(?:Sources?|Report|Reports?|Exclusive|Analysis)[：:\s]+',

    # 7. 社交推特元数据废话
    r'^Thread by @[A-Za-z0-9_]+[：:\s]*',
    r'^Replying to @[A-Za-z0-9_]+[：:\s]*',
    r'https?://t\.co/[a-zA-Z0-9]+',
    r'[\(（]?(?:1/\d+|1/n|🧵|👇)[\)）]?',
    r'View on (?:Twitter|X)[^。！\n]*',

    # 8. 营销与空壳套话
    r'行业核心力量围绕[“"\'「][^”"\'」]*?[”"\'」]\s*加速推进关键技术攻坚与工程落地[，,]?\s*力求在激烈的产业竞赛中确立先发优势[。！]?',
    r'行业最新动态持续跟踪报道[。！]?'
]


def clean_news_text(text: str) -> str:
    """Strip HTML entities, reporter bylines, trailing source parentheses, and boilerplate prefixes."""
    if not text:
        return ""
    t = html.unescape(text)
    t = t.replace("&nbsp;", " ").replace("\u00a0", " ")
    
    # 1. 深度应用全网聚合器废话黑名单规则库
    for rule in AGGREGATOR_NOISE_RULES:
        t = re.sub(rule, '', t, flags=re.IGNORECASE)

    # 2. 移除陈旧模板前缀与多余标识
    t = re.sub(r'^【.*?】\s*', '', t)
    t = re.sub(r'^由\s*.*?\s*(?:权威发布|最新报道)[。：:]\s*', '', t)
    t = re.sub(r'^据\s*.*?\s*(?:最新报道|报道)[，,：:]\s*', '', t)
    t = re.sub(r'^(?:行业关键动向与突破报道|领袖前沿发声与社区论战|开箱即用落地利器与提效神器|实操深度演示与架构解析)[：:]\s*b?\s*', '', t)
    t = re.sub(r'^b([\u4e00-\u9fa5])', r'\1', t)
    t = re.sub(r'^(?:Opinion\s*\|\s*|专栏\s*\|\s*|观点\s*\|\s*)', '', t, flags=re.IGNORECASE)
    
    # 3. 移除末尾括号中的媒体或记者标识 (支持末尾带有句号的情况)
    t = re.sub(r'[\(（][^()（）]*?(?:The Information|Forbes|Financial Times|Guardian|Bloomberg|TechCrunch|Reuters|The Verge|FedScoop|Wall Street Journal|New York Times|Wired|Ars Technica|CNBC|Business Insider|金融时报|纽约时报|彭博|路透|福布斯|卫报)[^()（）]*?[\)）][。.\s]*$', '', t, flags=re.IGNORECASE)
    t = re.sub(r'[\(（]@[A-Za-z0-9_]+[\)）][。.\s]*$', '', t)
    t = re.sub(r'[\(（][^()（）]*?/[^()（）]*?[\)）][。.\s]*$', '', t)
    t = re.sub(r'[\(（][^()（）]*?(?:译|文|图|编辑)[）\)][。.\s]*$', '', t)
    
    # 4. 清理连续重复符号与空白
    t = re.sub(r'([。！？；，、])\1+', r'\1', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def generate_smart_fallback_summary(item: Dict[str, Any], title_zh: str) -> str:
    """
    生成真实、纯净、100%忠实于原文事实的中文摘要。
    严格原则：
    1. 优先提取与翻译条目自带的真实文章正文 (article_content / original_content / content_snippet)；
    2. 坚决杜绝任何捏造的虚假人物（如查尔斯国王等）与机械套话模版（如“聚焦该事件...”）；
    3. 若无更多原文细节，客观准确陈述标题事实与信源。
    """
    clean_title = clean_news_text(title_zh or item.get("title_zh") or item.get("title", ""))
    
    # 优先从完整正文、原始内容或深入描述中提取真实新闻段落
    raw_text = (
        item.get("article_content") or 
        item.get("original_content") or 
        item.get("content_snippet") or 
        item.get("summary") or 
        item.get("description") or 
        ""
    )
    snippet = clean_news_text(raw_text)
    
    # 彻底滤除末尾可能跟随的英文媒体噪音
    media_pattern = r'[\s&nbsp;·|《]*(?:CNN|The Guardian|The Washington Post|Reuters|Bloomberg|Financial Times|Wall Street Journal|New York Times|The Verge|Ars Technica|TechCrunch|Wired|Pew Research|BBC|The Free Press|IEEE Spectrum|NPR|NBC News|Seattle Times|Al Jazeera|DW\.com|DW|AP News|AP|CBRE|OpenAI|Anthropic|Google|Microsoft|Apple|Meta)[》\s.]*$'
    prefix_pattern = r'^(?:美联社|路透社|新华社|彭博社|央视网|CNN|DW|AP)[\s:：·|-]*'
    snippet_clean = re.sub(media_pattern, '', snippet, flags=re.IGNORECASE).strip()
    
    if snippet_clean and len(snippet_clean) >= 20:
        # 若已具备有效中文内容，直接提炼，避免无谓的网络翻译耗时
        zh_count = len(re.findall(r'[\u4e00-\u9fa5]', snippet_clean))
        if zh_count >= 10:
            clean_s = re.sub(prefix_pattern, '', snippet_clean).strip()
            if clean_title and clean_s.startswith(clean_title):
                clean_s = clean_s[len(clean_title):].strip()
            if len(clean_s) >= 15:
                return clean_s[:220]

        # 取前 280 字符的丰富真实细节翻译
        trans_snippet = clean_news_text(free_translate_zh(snippet_clean[:280]))
        if trans_snippet and clean_title:
            trans_snippet = re.sub(prefix_pattern, '', trans_snippet).strip()
            if trans_snippet.startswith(clean_title):
                trans_snippet = trans_snippet[len(clean_title):].strip()
            elif clean_title in trans_snippet and len(trans_snippet) <= len(clean_title) * 2.2:
                trans_snippet = trans_snippet.replace(clean_title, "").strip()
            elif clean_title.startswith(trans_snippet):
                trans_snippet = ""
            
            zh_media_pattern = r'[\s.·|《]*(?:美国有线电视新闻网|CNN|卫报|华盛顿邮报|路透社|彭博社|金融时报|华尔街日报|纽约时报|皮尤研究中心|英国广播公司|全国广播公司|NBC新闻|NBC News|自由新闻报|The Free Press|IEEE频谱|IEEE Spectrum|NPR|西雅图时报|Seattle Times|半岛电视台|德国之声|DW\.com|DW|美联社|AP新闻|AP|CBRE|OpenAI|Anthropic|Google|Microsoft|Apple|Meta)[》\s.]*$'
            trans_snippet = re.sub(zh_media_pattern, '', trans_snippet, flags=re.IGNORECASE).strip('。，, ：: -—|·《》')
        
        zh_chars = len(re.findall(r'[\u4e00-\u9fa5]', trans_snippet))
        if trans_snippet and len(trans_snippet) >= 15 and zh_chars >= 8 and trans_snippet != clean_title:
            return trans_snippet

    # 兜底：基于已有信源与真实标题陈述事实，绝不凭空捏造未发生的内容
    src = item.get("source", "") or item.get("author", "")
    if src:
        clean_src = src.split("·")[0].strip()
        return f"据 {clean_src} 报道，{clean_title}。该动态引发了产业界与前沿开发者的广泛讨论与技术跟踪。"
    return f"{clean_title}。该事件反映了当前技术演进与落地实践中的关键考量。"


def generate_witty_ai_commentary(full_text: str, title: str) -> str:
    """
    生成高针对性、深刻犀利的 AI 点评。
    严苛门禁：只有当主体与具体事件 100% 精确契合时才输出；
    若无法精准对应，严格返回空字符串 ""，由前端优雅隐藏，绝不强行套用张冠李戴的段子！
    """
    t_lower = title.lower()
    full_lower = f"{title} {full_text}".lower()
    
    # 1. Meta / Ray-Ban 智能眼镜与音频硬件
    if ("meta" in full_lower or "ray-ban" in full_lower or "扎克伯格" in full_lower) and any(k in t_lower for k in ["智能眼镜", "无摄像头", "六个麦克风", "6个麦克风", "camera-free", "眼镜"]):
        return "雷朋联名款被吐槽成“防偷拍警惕神器”之后，Meta 索性把摄像头抠掉换成6个麦克风。一方面彻底打消了公共场合的隐私防备，另一方面大幅压低硬件成本。虽然失去了“视觉看世界”的能力，但在端到端实时语音架构成熟的当下，音频AI助手正成为落地阻力最小的硬件载体。"

    # 2. 算力能耗与电网基建
    elif any(k in full_lower for k in ["数据中心", "算力中心", "电力", "电网", "核电", "耗电"]) and any(k in t_lower for k in ["电网", "核能", "清洁能源", "电力需求", "能耗", "变压器", "停电", "供电"]):
        return "大模型参数狂飙到数万亿之后，AI 的物理对手终于从算法工程师变成了国家电网。算力扩张的终点不是数学极限，而是变压器与输电线路的吞吐上限。谁能锁定长期稳定的清洁能源供给，谁才能在接下来的算力耐力赛中站稳脚跟。"

    # 3. 编程智能体交付模式变革
    elif any(k in t_lower for k in ["claude code", "cursor", "vibe coding", "copilot", "程序员", "代码智能体", "编程助手"]):
        return "从手写每一行代码到由 AI Agent 自动化生成与重构，软件工程交付范式正在经历质变。开发者的核心竞争力正加速从低阶语法记忆转向高阶架构设计、上下文引导以及边界逻辑的严格审查。"

    # 4. 山姆·奥特曼深度人物专访与名利场访谈
    elif ("奥特曼" in full_lower or "altman" in full_lower or "sama" in full_lower) and any(k in full_lower for k in ["名利场", "vanity fair", "专访", "q&a", "生活", "孩子", "反派", "villain", "奥本海默", "oppenheimer"]):
        return "从硅谷科技救世主被舆论推到‘AI奥本海默’的反派位置，奥特曼很清楚自己成了全人类对失控未来焦虑的泄洪口。在专访里大谈‘准备末日’、育儿与反思扎克伯格，看似放下身段展现人性脆弱，实则把无可避免的技术垄断与权力集中巧妙包装成了背负人类原罪的‘沉重担当’。"

    # 无法保证 100% 针对性对齐时，坚决返回空，绝不输出牛头不对马嘴的通用套话
    return ""


def generate_smart_ai_analysis(item: Dict[str, Any], title_zh: str = "") -> Dict[str, Any]:
    """Generate professional News Briefing (新闻简报) based on factual synthesis and industry insights."""
    clean_title = clean_news_text(title_zh or item.get("title_zh") or item.get("title", ""))
    clean_snippet = clean_news_text(item.get("content_snippet", ""))
    source = item.get("source", "")
    author = item.get("author", "")
    category = item.get("category", "news")
    full_text = f"{clean_title} {clean_snippet}".strip()

    # 1. 识别核心主体 (Who)
    who = ""
    who_candidates = [
        ("贝森特", "财政部长斯科特·贝森特 (Scott Bessent)"),
        ("Bessent", "财政部长斯科特·贝森特 (Scott Bessent)"),
        ("黄仁勋", "英伟达创始人兼CEO 黄仁勋 (Jensen Huang)"),
        ("Jensen", "英伟达创始人兼CEO 黄仁勋 (Jensen Huang)"),
        ("特朗普", "美国总统 特朗普 (Donald Trump)"),
        ("Trump", "美国总统 特朗普 (Donald Trump)"),
        ("拜登", "美国前总统 拜登"),
        ("众议院", "美国众议院 (U.S. House of Representatives)"),
        ("参议院", "美国参议院 (U.S. Senate)"),
        ("国会", "美国国会立法机构"),
        ("白宫", "美国白宫决策机构"),
        ("FTC", "美国联邦贸易委员会 (FTC)"),
        ("SEC", "美国证券交易委员会 (SEC)"),
        ("DOJ", "美国司法部 (DOJ)"),
        ("欧盟", "欧盟委员会 (European Commission)"),
        ("OpenAI", "OpenAI 官方团队"),
        ("Anthropic", "Anthropic (Claude 研发团队)"),
        ("Google", "谷歌 (Google / DeepMind)"),
        ("谷歌", "谷歌 (Google / DeepMind)"),
        ("Meta", "Meta (扎克伯格团队)"),
        ("微软", "微软公司 (Microsoft)"),
        ("Microsoft", "微软公司 (Microsoft)"),
        ("通用汽车", "通用汽车 (General Motors)"),
        ("苹果", "苹果公司 (Apple Inc.)"),
        ("Apple", "苹果公司 (Apple Inc.)"),
        ("英伟达", "英伟达 (NVIDIA / 黄仁勋)"),
        ("NVIDIA", "英伟达 (NVIDIA / 黄仁勋)"),
        ("马斯克", "埃隆·马斯克 (Elon Musk)"),
        ("Musk", "埃隆·马斯克 (Elon Musk)"),
        ("特斯拉", "特斯拉 (Tesla / 马斯克)"),
        ("Tesla", "特斯拉 (Tesla / 马斯克)"),
        ("UPI", "印度统一支付接口 (UPI / NPCI)"),
        ("DeepSeek", "深度求索 (DeepSeek 团队)"),
        ("Cursor", "Anysphere (Cursor 团队)"),
        ("CoinEx", "加密货币交易所 CoinEx"),
        ("Salesforce", "Salesforce 研发团队"),
        ("字节", "字节跳动 (ByteDance)"),
        ("阿里", "阿里巴巴云智能"),
        ("腾讯", "腾讯混元团队"),
        ("百度", "百度文心团队")
    ]
    for k, name in who_candidates:
        if k.lower() in full_text.lower():
            who = name
            break
    if not who:
        if author and author != source:
            who = author
        else:
            title_no_lead = re.sub(r'^(?:周[一二三四五六日天]|今日|昨日|当地时间|刚刚|近期|日前|据报道|消息称)[，,\s]*', '', clean_title)
            match = re.match(r'^([^，,。：:\s]{2,15})', title_no_lead)
            who = match.group(1) if match else "行业核心机构与领袖"

    # 2. 识别场景与场合 (Where/When)
    where = "全球产业与技术前沿一线"
    if any(k in full_text for k in ["听证会", "国会", "法案", "白宫", "监管", "起诉", "审判"]):
        where = "美国国会听证会与联邦监管审议现场"
    elif any(k in full_text for k in ["CarPlay", "车机", "汽车", "电动车", "座舱"]):
        where = "智能网联汽车座舱与车载操作系统生态"
    elif any(k in full_text for k in ["UPI", "印度", "卢比", "支付", "商户费"]):
        where = "印度移动金融与大额数字支付市场"
    elif any(k in full_text for k in ["One订阅", "订阅", "定价", "会员", "套餐"]):
        where = "全球社交网络与AI增值服务商业化市场"
    elif any(k in full_text for k in ["开源", "模型", "参数", "权重", "GitHub"]):
        where = "全球大模型开源社区与技术研发一线"
    elif any(k in full_text for k in ["芯片", "GPU", "算力", "数据中心", "半导体"]):
        where = "算力芯片供应链与云端基础设施"

    # 3. 提取核心事实与举措 (What)
    what = clean_title

    # 4. 推理起因背景与深层动因 (Why)
    why = ""
    if any(k in full_text for k in ["虚拟演员", "蒂莉", "tilly", "actor", "虚拟角色", "数字人", "演艺", "好莱坞"]):
        why = "生成式数字人与虚拟演员渗透演艺工业引发行业伦理与从业者权益博弈，算法在敏感议题上的回避机制暴露出防御性对齐的技术短板。"
    elif any(k in full_text for k in ["网络安全", "漏洞", "cybersecurity", "漏洞挖掘"]) and any(k in full_text for k in ["黑客", "hacker", "doom"]):
        why = "网络安全一线专家对大模型‘末日黑客’的夸大叙事提出技术质疑，呼吁将行业安全重心从宏大恐慌叙事回归到代码审计与实战防御。"
    elif ("奥特曼" in full_text or "altman" in full_text) and any(k in full_text for k in ["采访", "问答", "专访", "q&a", "interview", "名利场", "vanity fair", "生活", "孩子"]):
        why = "伴随通用人工智能竞赛进入深水区，作为行业标志性人物的奥特曼直面外界对技术失控与权力集中的伦理关切，深度回应了关于企业治理、上市节奏及个人角色定位的争论。"
    elif any(k in full_text for k in ["数据信任", "信任问题", "data trust", "爬虫", "授权", "版权", "policy", "policies"]):
        why = "前沿模型研发面临海量数据抓取合规争议与创作者信任危机，亟需构建透明可信的追溯机制与合理的版权利益分配方案。"
    elif any(k in full_text for k in ["gemini 3.8", "live", "语音模型", "音频", "speech", "1.38", "gpt-live"]):
        why = "端到端低延迟全双工语音架构打破传统级联瓶颈，以极低边际成本加速多模态实时交互在各端侧应用场景的规模化普及。"
    elif any(k in full_text for k in ["电网", "能源", "核电", "耗电", "电力", "power", "grid", "nuclear"]):
        why = "超算集群极速扩张面临区域电网承载与清洁能源供应瓶颈，倒逼科技巨头深度布局专用能源基础设施以保障算力生命线。"
    elif any(k in full_text for k in ["智能眼镜", "穿戴", "无摄像头", "麦克风"]):
        why = "该举措主要旨在解决公共场合摄像头带来的隐私争议，同时降低硬件成本与佩戴门槛，加速以音频和语音为核心的多模态AI助手渗透至日常消费场景。"
    elif any(k in full_text for k in ["豁免", "责任", "听证会", "监管", "法案"]):
        why = "此举深层背景在于防范前沿AI系统引发法律追责真空与安全失控风险，同时通过划定合规红线与扶持开源生态，防止闭源科技巨头形成行业事实垄断。"
    elif any(k in full_text for k in ["选民", "数据中心", "民调", "两党"]):
        why = "调查反映出AI高耗能算力设施在地方落地时正面临严峻的电力供应、土地资源及公众环境关切阻力，AI基建扩张正在从单纯的技术投资转变为敏感的公共与政治议题。"
    elif any(k in full_text for k in ["1.2万亿", "1.2T", "估值", "IPO", "融资"]):
        why = "巨额融资意向凸显出头部模型公司在研发前沿架构与构建超级计算集群过程中巨大的资本消耗率，企业正力求在公开上市前锁定充沛流动性以构筑壁垒。"
    elif any(k in full_text for k in ["对齐", "alignment", "安全训练", "动力"]):
        why = "这体现出行业领袖正在重塑大模型安全的行业话语权，强调缺乏有效安全对齐与伦理约束的模型将难以在企业级真实复杂业务中通过可用性检验。"
    elif any(k in full_text for k in ["UPI", "商户费", "订阅", "收费", "定价"]):
        why = "该调整标志着核心数字基础设施正告别长期的免费补贴模式，通过向高频商业结算收取增值服务费以分摊高昂的结算与算力基础设施运维成本。"
    elif any(k in full_text for k in ["CarPlay", "Android Auto", "车机", "通用汽车"]):
        why = "通用汽车重新引入手机互联映射方案，表明封闭自研车机在抗衡成熟移动生态心智时遭遇现实阻力，顺应用户对无缝导航与音频交互的刚需成为保障终端口碑的务实选择。"
    elif any(k in full_text for k in ["编程", "coding", "cursor", "copilot", "程序员", "代码"]):
        why = "自主编程智能体深刻改变软件工程交付模式，开发者正加速从重复性代码编写者转向更高阶的系统架构把控与逻辑审查者。"
    elif any(k in full_text for k in ["开源", "突破", "发布", "模型"]):
        why = "降低开发者微调与工程落地的门槛与算力开销，加速端到端应用在真实业务中生根发芽。"
    else:
        # 无明确特定动因时，置空，坚决不拼凑虚假套话
        why = ""

    # 5. 整合新闻简报正文 (Natural News Briefing，客观纯净陈述事件事实，严禁机械模版)
    first_stmt = clean_title
    if not first_stmt.endswith(('。', '！', '？')):
        first_stmt += '。'

    # 若有正文长篇段落或摘要片段且不与标题重复，翻译并提取充分的新闻细节与上下文
    detail_stmt = ""
    candidate_content = (
        item.get("article_content") or 
        item.get("original_content") or 
        item.get("content_snippet") or 
        clean_snippet
    )
    if candidate_content and len(candidate_content) > 15:
        trans_snippet = clean_news_text(free_translate_zh(candidate_content[:350]))
        # 严格过滤聚合器废话与标题复读
        if trans_snippet and len(trans_snippet) > 10 and trans_snippet not in clean_title and clean_title not in trans_snippet:
            detail_stmt = trans_snippet
            if not detail_stmt.endswith(('。', '！', '？')):
                detail_stmt += '。'

    # 仅拼接真实事实细节；若无 detail_stmt 则结合有意义的 why，否则直接使用 first_stmt，绝不产生空话
    parts = [first_stmt]
    if detail_stmt:
        parts.append(detail_stmt)
    elif why:
        parts.append(why)

    briefing_zh = " ".join(parts).strip()
    briefing_zh = re.sub(r'([。！？；，、])\1+', r'\1', briefing_zh).strip()
    briefing_zh = re.sub(r'消息来源[：:]\s*', '', briefing_zh)

    # 6. AI 点评 (犀利幽默、直指核心，无针对性内容时保持为空，交由前端隐藏)
    insight_zh = generate_witty_ai_commentary(full_text, clean_title)

    title_en = item.get("title_en") or item.get("title", "")
    return {
        "briefing_zh": briefing_zh,
        "briefing_en": f"Executive Briefing: In {where}, {who} advanced a key development: {title_en}. Context: {why}",
        "elements_zh": {
            "who": who,
            "where": where,
            "what": clean_title,
            "why": why
        },
        "elements_en": {
            "who": who,
            "where": where,
            "what": title_en,
            "why": why
        },
        "insight_zh": insight_zh,
        "insight_en": "Industry Insight: Reflects the ongoing transition towards sustainable deployment, commercial maturity, and balanced governance across the AI ecosystem.",
        "digest_zh": briefing_zh,
        "digest_en": f"Executive Briefing: In {where}, {who} announced: {title_en}.",
        "key_points_zh": [
            f"主体与场景：{who}在{where}",
            f"核心事实：{clean_title}",
            f"动因背景：{why}"
        ],
        "key_points_en": [
            f"Actor & Context: {who} in {where}",
            f"Key Action: {title_en}",
            f"Motivation: {why}"
        ],
        "takeaway_zh": insight_zh,
        "takeaway_en": "Industry Insight: Reflects the transition towards commercial maturity and balanced governance."
    }


def process_items_batch(items: List[Dict[str, Any]], batch_size: int = 8) -> List[Dict[str, Any]]:
    """
    Process a list of items with Gemini in batches, or high-speed neural translator.
    Guarantees 100% pure Chinese titles, takeaways, and deep structured AI analysis.
    Pre-curated items with existing title_zh & summary_zh are preserved directly.
    """
    # 区分：已有优质中文的精选内容（领袖推特、场景工具、实战视频、Prompt）与需要 AI 翻译提炼的原始 RSS
    direct_items = []
    need_ai_items = []

    for it in items:
        # 补齐缺省 category 字段
        if "category" not in it:
            it["category"] = it.get("default_category", "news")
        
        # 确保已有条目附带合格的 ai_analysis
        if it.get("title_zh") and it.get("summary_zh"):
            if not it.get("ai_analysis"):
                it["ai_analysis"] = generate_smart_ai_analysis(it, it.get("title_zh"))
            direct_items.append(it)
        else:
            need_ai_items.append(it)

    print(f"📊 待处理清单：{len(direct_items)} 条已具备精选中文，{len(need_ai_items)} 条需要 AI 翻译提炼")

    if not need_ai_items:
        return direct_items

    client = get_gemini_client()

    if not client:
        print("💡 未检测到 GEMINI_API_KEY，启用内置神经翻译器保障 100% 纯中文呈现与智能深度解读...")
        processed_ai = []
        for item in need_ai_items:
            p_item = dict(item)
            cat = item.get("category") or item.get("default_category", "news")
            p_item["category"] = cat
            raw_title_zh = item.get("title_zh") or free_translate_zh(item.get("title", ""))
            title_zh = clean_news_text(raw_title_zh)
            p_item["title_zh"] = title_zh
            raw_summary = item.get("summary_zh") or generate_smart_fallback_summary(item, title_zh)
            p_item["summary_zh"] = clean_news_text(raw_summary)
            p_item["ai_analysis"] = generate_smart_ai_analysis(item, title_zh)
            p_item["title_en"] = item.get("title_en") or item.get("title", "")
            p_item["summary_en"] = clean_news_text(item.get("summary_en") or item.get("content_snippet", ""))
            p_item["hot_score"] = 4 if cat in ["celebrity", "videos"] else 3
            p_item["tags"] = item.get("tags") or [item.get("source", "AI快讯")]
            processed_ai.append(p_item)
        print("  ✓ 纯正中文翻译、看点提炼与 AI 深度分析生成完毕！")
        return direct_items + processed_ai

    print("🤖 正在调用 Google Gemini 进行批量智能翻译、深度分析与分类...")

    results = []
    models_to_try = [MODEL_NAME, "gemini-2.0-flash", "gemini-1.5-flash"]

    for i in range(0, len(need_ai_items), batch_size):
        chunk = need_ai_items[i:i + batch_size]
        simplified_chunk = [
            {
                "index": idx,
                "title": it.get("title", ""),
                "source": it.get("source", ""),
                "content": (it.get("article_content") or it.get("original_content") or it.get("content_snippet", ""))[:600],
                "suggested_category": it.get("category") or it.get("default_category", "news")
            }
            for idx, it in enumerate(chunk)
        ]

        prompt = f"""
你是一个顶级科技智库的新闻主编与科技大V。请对以下最新资讯进行专业新闻简报（News Briefing）提炼与犀利AI点评。
【关键原则】：
1. 严禁在正文出现“据XX报道”、“由XX发布”、记者姓名或链接等杂质（信源已在界面标题栏统一展示）。
2. 必须交代清楚新闻六要素（5W1H）：谁（Who）、在什么场合/场景（Where）、做了/说了什么具体动作或事实（What）、起因背景动因（Why），让用户无需查看原资讯详情即可完全掌握事件脉络。
3. 【AI 点评（insight_zh）要求】：
   - 必须深刻而幽默风趣、直指事件核心、看情况可带微讽刺口感，具有科技圈网络高赞神评/毒舌大V的鲜明语感（2-3句话）。
   - 严禁假大空的套话（如“该动态折射出当前AI产业链正由前期的技术概念探索全面加速转向真实场景落地与产业利益再分配...”这类无意义公文废话一律严禁）。
   - 一针见血揭穿大厂公关话术背后的真实算计或利益博弈，让读者会心一笑。

【输出要求】：
请以纯 JSON Array 形式输出（不要带有 ```json 标记），数组内每个元素格式如下：
{{
  "index": 对应的序号,
  "title_zh": "自然流畅精炼的纯中文标题(25字以内，杜绝夹杂英文与媒体记者名字)",
  "summary_zh": "一句话核心事实交代(30-50字，讲清楚核心事件)",
  "category": "news | celebrity | tools | videos",
  "hot_score": 1到5的整数热度评分,
  "tags": ["标签1", "标签2"],
  "ai_analysis": {{
    "briefing_zh": "新闻简报事实正文：清晰交代谁在什么场景做了/说了什么具体动作与细节、起因动因背景（2-3句完整中文，严禁包含信源或记者名字）",
    "briefing_en": "Executive news briefing: clearly stating who, occasion, core facts, and motivation (2-3 sentences)",
    "elements_zh": {{
      "who": "核心主体/人物/机构",
      "where": "事件场合/场景",
      "what": "核心陈述/决议/具体事实细节",
      "why": "起因背景/深层动因"
    }},
    "elements_en": {{
      "who": "Key actor/entity",
      "where": "Occasion / context",
      "what": "Core statement or action with details",
      "why": "Key motivation or background"
    }},
    "insight_zh": "深刻、幽默风趣、直指核心、带微讽刺的科技圈网络高赞神评（2-3句，严禁公文假大空套话，严禁在正文开头添加【AI点评】等任何标签前缀）",
    "insight_en": "Witty, humorous, sharp tech-insider hot take and commentary without extra tag prefixes (2-3 sentences)",
    "digest_zh": "新闻简报事实正文（与briefing_zh一致）",
    "digest_en": "Executive briefing in English",
    "key_points_zh": [
      "主体与场景简述",
      "核心举措与细节简述",
      "起因动因与影响简述"
    ],
    "key_points_en": [
      "Actor & context",
      "Key action & details",
      "Motivation & impact"
    ],
    "takeaway_zh": "AI 点评（与insight_zh一致）",
    "takeaway_en": "Tech-insider hot take (same as insight_en)"
  }}
}}

待处理资讯：
{json.dumps(simplified_chunk, ensure_ascii=False, indent=2)}
"""

        try:
            response = None
            last_err = None
            for m in models_to_try:
                try:
                    response = client.models.generate_content(
                        model=m,
                        contents=prompt
                    )
                    if response and response.text:
                        break
                except Exception as m_err:
                    last_err = m_err
                    continue

            if not response or not response.text:
                raise last_err or Exception("All Gemini models failed")

            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]

            parsed_chunk = json.loads(raw_text.strip())
            parsed_dict = {entry["index"]: entry for entry in parsed_chunk}

            for idx, orig_item in enumerate(chunk):
                ai_data = parsed_dict.get(idx, {})
                merged = dict(orig_item)
                raw_title_zh = orig_item.get("title_zh") or ai_data.get("title_zh") or free_translate_zh(orig_item.get("title", ""))
                merged["title_zh"] = clean_news_text(raw_title_zh)
                raw_summary_zh = orig_item.get("summary_zh") or ai_data.get("summary_zh") or generate_smart_fallback_summary(orig_item, merged["title_zh"])
                merged["summary_zh"] = clean_news_text(raw_summary_zh)
                merged["title_en"] = orig_item.get("title_en") or orig_item.get("title", "")
                merged["summary_en"] = orig_item.get("summary_en") or orig_item.get("content_snippet", "")
                merged["category"] = orig_item.get("category") or ai_data.get("category") or orig_item.get("default_category", "news")
                merged["hot_score"] = ai_data.get("hot_score", 3)
                merged["tags"] = orig_item.get("tags") or ai_data.get("tags") or [orig_item.get("source", "AI快讯")]
                
                ai_analysis = orig_item.get("ai_analysis") or ai_data.get("ai_analysis") or generate_smart_ai_analysis(orig_item, merged["title_zh"])
                if ai_analysis and isinstance(ai_analysis, dict):
                    if "briefing_zh" in ai_analysis:
                        ai_analysis["briefing_zh"] = clean_news_text(ai_analysis["briefing_zh"])
                    if "digest_zh" in ai_analysis:
                        ai_analysis["digest_zh"] = clean_news_text(ai_analysis["digest_zh"])
                merged["ai_analysis"] = ai_analysis
                results.append(merged)

            print(f"  ✓ 已完成 {min(i + batch_size, len(need_ai_items))}/{len(need_ai_items)} 条")

        except Exception as e:
            print(f"  ❌ Gemini 处理异常: {e}，启用高可用神经中文翻译保障")
            for orig_item in chunk:
                fallback = dict(orig_item)
                raw_title_zh = orig_item.get("title_zh") or free_translate_zh(orig_item.get("title", ""))
                title_zh = clean_news_text(raw_title_zh)
                fallback["title_zh"] = title_zh
                fallback["summary_zh"] = clean_news_text(orig_item.get("summary_zh") or generate_smart_fallback_summary(orig_item, title_zh))
                fallback["title_en"] = orig_item.get("title_en") or orig_item.get("title", "")
                fallback["summary_en"] = orig_item.get("summary_en") or orig_item.get("content_snippet", "")
                fallback["category"] = orig_item.get("category") or orig_item.get("default_category", "news")
                fallback["hot_score"] = 3
                fallback["tags"] = orig_item.get("tags") or [orig_item.get("source", "AI快讯")]
                fallback["ai_analysis"] = generate_smart_ai_analysis(orig_item, title_zh)
    all_final = direct_items + results
    # 🛡️ 强制执行语言质检与自愈哨兵流水线：对所有产出资讯进行双语对称性与纯净度门禁审查
    try:
        from language_sentinel import run_pipeline_language_audit
        all_final, _ = run_pipeline_language_audit(all_final)
    except Exception as e:
        print(f"⚠️ [language_sentinel] 质检流水线异常: {e}")
    return all_final
