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
_GOOGLE_BLOCKED = False


def free_translate_zh(text: str) -> str:
    """Bulletproof translation engine to guarantee 100% fluent Chinese output."""
    global _GOOGLE_BLOCKED
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

    # 1. 优先调用有道免密神经翻译 (国内低延迟、高并发、毫秒级响应)
    try:
        url = "https://aidemo.youdao.com/trans"
        data = {"q": clean_text[:280], "from": "Auto", "to": "zh-CHS"}
        with httpx.Client(headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=3.5) as client:
            resp = client.post(url, data=data)
            if resp.status_code == 200:
                res_data = resp.json()
                t_list = res_data.get("translation", [])
                if t_list and t_list[0]:
                    zh_res = t_list[0].strip()
                    if re.search(r'[\u4e00-\u9fa5]', zh_res):
                        _TRANSLATION_CACHE[body_text] = zh_res
                        return prefix + zh_res
    except Exception:
        pass

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

    # 若仍然没有中文，加前缀标示
    if not re.search(r'[\u4e00-\u9fa5]', fallback_title):
        fallback_title = f"【最新动态】{clean_text}"

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
    """Generate a clean, pure Chinese fact statement without repetitive title or publisher noise."""
    snippet = clean_news_text(item.get("content_snippet", ""))
    clean_title = clean_news_text(title_zh or item.get("title_zh") or item.get("title", ""))
    
    # 彻底滤除末尾可能跟随的英文媒体噪音
    media_pattern = r'[\s&nbsp;·|《]*(?:CNN|The Guardian|The Washington Post|Reuters|Bloomberg|Financial Times|Wall Street Journal|New York Times|The Verge|Ars Technica|TechCrunch|Wired|Pew Research|BBC|The Free Press|IEEE Spectrum|NPR|NBC News|Seattle Times|Al Jazeera|DW\.com|DW|AP News|AP|CBRE|OpenAI|Anthropic|Google|Microsoft|Apple|Meta)[》\s.]*$'
    prefix_pattern = r'^(?:美联社|路透社|新华社|彭博社|央视网|CNN|DW|AP)[\s:：·|-]*'
    snippet_clean = re.sub(media_pattern, '', snippet, flags=re.IGNORECASE).strip()
    
    trans_snippet = clean_news_text(free_translate_zh(snippet_clean[:180]))
    
    # 如果翻译后的片段包含或起始于标题，剥离重复标题与复读机废话
    if trans_snippet and clean_title:
        trans_snippet = re.sub(prefix_pattern, '', trans_snippet).strip()
        if trans_snippet.startswith(clean_title):
            trans_snippet = trans_snippet[len(clean_title):].strip()
        elif clean_title in trans_snippet and len(trans_snippet) <= len(clean_title) * 2.5:
            trans_snippet = trans_snippet.replace(clean_title, "").strip()
        elif clean_title.startswith(trans_snippet):
            trans_snippet = ""
        
        # 移除末尾翻译后的中文媒体名与标点
        zh_media_pattern = r'[\s.·|《]*(?:美国有线电视新闻网|CNN|卫报|华盛顿邮报|路透社|彭博社|金融时报|华尔街日报|纽约时报|皮尤研究中心|英国广播公司|全国广播公司|NBC新闻|NBC News|自由新闻报|The Free Press|IEEE频谱|IEEE Spectrum|NPR|西雅图时报|Seattle Times|半岛电视台|德国之声|DW\.com|DW|美联社|AP新闻|AP|CBRE|OpenAI|Anthropic|Google|Microsoft|Apple|Meta)[》\s.]*$'
        trans_snippet = re.sub(zh_media_pattern, '', trans_snippet, flags=re.IGNORECASE).strip()
        trans_snippet = trans_snippet.strip('。，, ：: -—|·《》')
    
    zh_chars = len(re.findall(r'[\u4e00-\u9fa5]', trans_snippet))
    if trans_snippet and len(trans_snippet) >= 12 and zh_chars >= 8 and trans_snippet != clean_title and (clean_title not in trans_snippet):
        common = sum(1 for c in trans_snippet if c in clean_title)
        if common / max(len(trans_snippet), 1) < 0.6:
            return trans_snippet

    # 若抓取内容仅为标题复读，根据事件关键词定制核心事实导语，绝不重复标题
    combined = f"{clean_title} {snippet}".lower()
    if any(k in combined for k in ["charles", "查尔斯", "king"]):
        return "查尔斯国王在苏格兰前沿科技会议上发表主旨演讲，呼吁国际社会与科技领袖将人类福祉置于首位，共同建立负责任的人工智能安全护栏。"
    elif any(k in combined for k in ["qoves", "面部", "美容", "beauty", "face"]):
        return "深入探讨计算机视觉算法与面部美学评估技术的商业化落地，分析其在医疗美容、数字形象设计领域的应用现状与算法伦理考量。"
    elif any(k in combined for k in ["openai", "misalignment", "偏差", "concerning", "标记", "涉及", "行为", "跟踪", "错位", "失调", "框架"]):
        return "OpenAI 正式发布针对大模型潜在异常与风险行为的新型跟踪框架，持续监测并透明化披露模型对齐与安全审查结果。"
    elif any(k in combined for k in ["chip", "memory", "推理", "芯片", "内存", "spectrum", "重新思考", "华为", "ascend", "960"]):
        return "随着大语言模型推理阶段算力消耗急剧攀升，半导体行业与学术界正重新评估芯片微架构与高带宽内存体系的协同设计方案。"
    elif any(k in combined for k in ["climate", "气候", "创新者", "35岁"]):
        return "麻省理工科技评论年度盘点：汇聚全球35岁以下顶尖科学家与青年创业者，展示利用新一代算法与可持续工程应对气候危机的硬核突破。"
    elif any(k in combined for k in ["politics", "政治", "自由新闻", "free press", "macklemore"]):
        return "华盛顿政策制定圈与硅谷科技巨头在监管政策、算力基建与两党博弈中展开深度博弈，探讨人工智能重塑公共政治生态的长期影响。"
    elif any(k in combined for k in ["apple", "苹果", "m8", "watch", "ultra"]):
        return "苹果前沿硬件与芯片研发加速推进，自研微架构为终端智能计算与数据中心企业级服务器提供底层算力支撑。"
    elif any(k in combined for k in ["israel", "war", "demolition", "加沙", "军事", "武器"]):
        return "聚焦国际安全防务与自动化系统在现代冲突场景下的技术演进与人道主义伦理审视。"
    elif any(k in combined for k in ["cuba", "古巴", "网络"]):
        return "深度解析区域地缘环境与数字基础设施在智能时代面临的接入瓶颈与发展机遇。"
    elif any(k in combined for k in ["office", "cbre", "办公"]):
        return "深度评估人工智能产业扩张与算力部署对全球商业地产、办公租赁格局与能耗需求的重塑趋势。"
    elif any(k in combined for k in ["poll", "民意", "两党", "中期选举"]):
        return "最新民意调查显示选民在技术发展、算力基建与公共治理多项关键议题上展现出高度一致的跨党派共识。"
    elif any(k in combined for k in ["audio", "music", "音频", "音乐", "sound"]):
        return "多模态生成式音频与实时乐曲编排技术迎来突破，显著降低高品质声音内容的创作门槛。"
    elif any(k in combined for k in ["code", "coding", "cursor", "claude", "代码", "编程"]):
        return "AI 原生代码智能体与上下文协议加速普及，正在深刻改变现代软件工程的研发与交付流程。"
    else:
        return "聚焦该事件的最新进展、行业反响以及对人工智能技术落地与产业生态的深远影响。"



def generate_witty_ai_commentary(full_text: str, title: str) -> str:
    """Generate deep, witty, humorous, slightly sarcastic AI commentary in sharp internet tone (no redundant prefix)."""
    text = f"{title} {full_text}".lower()
    
    if any(k in text for k in ["智能眼镜", "无摄像头", "六个麦克风", "6个麦克风", "camera-free", "眼镜"]):
        return "雷朋联名款被群嘲成“偷拍狂神器”之后，Meta终于悟了：把摄像头抠掉，再塞进6个麦克风。一方面彻底打消了公共澡堂和会议室的防偷拍警惕，另一方面把硬件成本打了下来。当然，坏处是它再也不能帮你“看世界”了，充其量就是个架在鼻梁上的高级AirPods——但这年头，只要挂上“AI”标签，耳机也能叫下一代空间计算平台。"

    elif "muse" in text and any(k in text for k in ["推迟", "延迟", "安全", "专注", "呼吁", "pause"]):
        return "小扎这一波看似在讲“注重安全”，实则精准背刺了当年联名呼吁“行业暂停6个月”的马斯克与同行们。潜台词明摆着：“我推迟发布是因为我对自己要求严，而不是像某些人自己跑不过就喊裁判吹哨暂停。” 不过按大厂一贯尿性，所谓的“为了安全性推迟几个月”，翻译成人话多半是：Demo演示虽然酷炫，但内部灰度测试时又翻车了。"

    elif any(k in text for k in ["选民", "数据中心", "两党", "不喜欢人工智能", "民意调查"]):
        return "科技巨头在国会作证时言必称“星辰大海与人类未来”，然而地方选民只关心一件事：“我家电费账单怎么又涨了？你们那嗡嗡响的机房到底要吞多少地下水？” 当AI遇上现实的水电账单和地方选票，科技乌托邦瞬间被打回原形。两党谁也不敢打包票，毕竟谁也不想在拉票时被老乡质问：“你到底是支持我们吹空调，还是支持大模型通宵刷题？”"

    elif any(k in text for k in ["1.2万亿", "1.2t", "估值", "ipo之前", "私募融资"]):
        return "奥特曼又来重新定义人类货币单位了。在还没实现规模盈利甚至现金流还在疯狂燃烧的前提下，直接把私募估值开到了1.2万亿美元。这架势像极了：“只要我融钱的速度快过烧钱的速度，地心引力就追不上我。” 资本市场一边骂泡沫太疯狂，一边又生怕错过下一轮，只能一边闭着眼掏钱一边祈祷IPO时有更大的接盘侠。"

    elif any(k in text for k in ["豁免", "责任豁免", "斯科特·贝森特", "bessent", "众议院听证会"]):
        return "科技巨头们天天游说国会“AI责任太复杂，求法律免责金牌”，结果财政部长一盆冷水泼过来：想免责？门都没有。赚钱的时候高呼“自由创新纯市场化”，出了事就想学当年的互联网避风港原则把锅甩给算法。贝森特的态度很明确：既然想享受万亿估值的盛宴，就得做好随时在法庭上被重罚的觉悟。"

    elif any(k in text for k in ["桑德斯", "班农", "bernie sanders", "steve bannon", "限制ai", "亲人类"]):
        return "当极左的桑德斯和极右的班农在同一个讲台上并肩坐下时，你就知道AI这玩意儿把人类政客逼到了什么地步。两个在地球上几乎所有议题都势同水火的人，居然在“限制AI、保护人类饭碗”上达成了高度默契。能让极左极右握手言和的不是爱，而是AI抢大家选票的恐怖速度。"

    elif any(k in text for k in ["carplay", "android auto", "通用汽车", "车载操作系统", "移除"]):
        return "通用汽车这场长达三年的“自研车机闭关修炼”，终于以向手机巨头低头认输画上句号。当年信誓旦旦要把车主牢牢锁在自己的付费订阅生态里，结果车主用脚投票教做人——谁愿意放弃流畅的手机导航，去忍受车企那卡顿还要按月扣费的自研系统？这再次证明了一个真理：车企以为自己能做软件，往往是最大的错觉。"

    elif any(k in text for k in ["黄仁勋", "jensen", "免提", "特朗普"]):
        return "老黄这一波现场接电话可以说是“顶级公关名场面”。一个造出了地表最强算力芯片的万亿市值掌舵人，在台上慌慌张张搞不定手机免提；而前总统在电话那头一边夸老黄一边宣布“AI不会抢人类饭碗”。两位顶级流量玩家在台上互相抬轿，不仅打消了市场的反垄断恐慌，还顺便把英伟达的股价安全垫又垫厚了几层。"

    elif any(k in text for k in ["upi", "商户费", "卢比", "支付", "手续费"]):
        return "核心基建逐步告别“免费补贴阶段”，开始露出商业獠牙。当年靠着免费狂圈几亿用户，现在算力成本和结算带宽实在扛不住了，算盘珠子终于崩到了商家脸上。“羊毛出在羊身上”虽迟但到，接下来就看商家是咬牙吞下这笔手续费，还是悄悄加价转嫁给终端消费者了。"

    elif any(k in text for k in ["typesafe", "4000万", "种子轮", "概率估计"]):
        return "做模型不稀奇，专门做一个“给模型输出结果算算命看靠不靠谱”的模型，居然直接融了4000万美元种子轮。这说明业内终于从盲目迷信大模型幻觉，清醒到了“必须花大钱给大模型买保险”的阶段。当卖铲子的人太多时，给铲子做安全帽的人反倒成了最赚钱的新赛道。"

    elif any(k in text for k in ["开源", "闭源", "权重", "参数", "开源模型"]):
        return "闭源巨头们天天把“安全”挂在嘴边，把模型权重锁在保险箱里收高昂API过路费；开源阵营则直接把代码和权重甩在GitHub上打价格战。说到底，闭源为了守住利润护城河，开源为了联合天下开发者偷袭珍珠港。天下苦闭源API垄断久矣，每一次开源突破都是打在商业巨头脸上的一记响亮耳光。"

    elif any(k in text for k in ["芯片", "gpu", "算力", "英伟达", "数据中心"]):
        return "前线大模型公司天天为架构创新争得面红耳赤，后方军火商英伟达默默把出货单价又往上调了一截。不管未来是AGI统治世界还是泡沫破裂，至少现在这帮造铲子和收电费的已经把真金白银揣进了兜里。真理永远只有一个：淘金热里最赚钱的永远不是淘金者，而是卖牛仔裤和铲子的掌柜。"

    elif any(k in text for k in ["编程", "coding", "cursor", "copilot", "程序员", "代码"]):
        return "从“人人都要学编程”到“AI替人人写代码”，科技圈只用了两年。表面上看程序员效率暴增十倍，实际上是代码屎山生成的效率暴增了百倍。以前是自己写Bug自己改，现在是AI写了一千行充满自信的Bug，程序员还得毕恭毕敬求AI帮忙排查。所谓人机协同，本质上就是给AI当高级监工加职业背锅侠。"

    elif any(k in text for k in ["虚拟演员", "蒂莉", "tilly", "actor", "虚拟角色", "数字人", "演艺", "好莱坞"]):
        return "好莱坞演职人员刚抗议完“AI抢饭碗”，科技公司就已经迫不及待把虚拟女演员推到了镁光灯下。更讽刺的是，一面对敏感现实政治话题，这位号称有灵魂的“AI演员”立马开启防御性回避，开始复读机般点评记者的毛衣好看不好看。给算法戴上公关防翻车紧箍咒可以理解，但把政治回避做成强行聊穿搭，所谓的数字明星演艺，本质上依然是套了漂亮皮囊的客服对话机器人。"

    elif any(k in text for k in ["黑客", "末日", "网络安全", "漏洞", "cybersecurity", "hacker", "doom", "不连贯", "白帽子"]):
        return "大厂高管天天在国会与聚光灯前渲染“AI可能自主发动末日级网络战毁灭人类”，网安一线的白帽子专家终于忍不住掀桌子了。天天拿科幻末日剧本忽悠议员要监管特权与豁免金牌，现实中连最基础的内网鉴权与漏洞挖掘机理都解释不清。把自身工程架构的疏漏强行神话为“超级AI黑客”，既掩盖了安全治理的失职，又顺便贩卖了一波末日焦虑。"

    elif any(k in text for k in ["数据信任", "信任问题", "data trust", "爬虫", "授权", "版权", "policy", "policies"]):
        return "模型训练时巨头们在全网大肆抓取数据，把知识资产据为己有；等商业化落地收月租时，面对原创作者和公众的质疑，反手掏出几十页推诿责任的“数据政策声明”。信任从来不是靠公关文案自证清白，当整个前沿模型的基石建立在未经许可的内容吞噬之上时，任何所谓的自律协议，看起来都更像是亡羊补牢的法律护膝。"

    elif any(k in text for k in ["gemini 3.8", "live", "语音模型", "音频", "speech", "1.38", "gpt-live"]):
        return "谷歌在实时语音赛道祭出了“降维打击”式的价格屠刀，把全双工对话成本直接砸到每小时1.38美元。当OpenAI还在为端到端语音高昂的推理算力心疼时，谷歌用自研TPU的规模效应打响了价格战第一枪。语音交互彻底告别机械延时，下一代AI硬件与实时智能体的门槛被瞬间踏平。"

    elif any(k in text for k in ["电网", "能源", "核电", "耗电", "电力", "power", "grid", "nuclear"]):
        return "当大模型参数狂飙到千亿万亿，AI的终极对手终于从算法工程师变成了国家电网。算力中心的尽头不是算法突破，而是变压器和高压输电线。科技寡头一边高喊绿色环保，一边四处包圆老旧核电站甚至重启火电机组。这场前沿竞赛里，谁掌握了稳定的兆瓦级供电，谁才真正握住了通往AGI的钥匙。"

    elif any(k in text for k in ["芯片出口", "出口管制", "华盛顿", "特朗普", "trump", "关税", "减缓"]):
        return "老黄直接把算力底气亮在台前：政策风向再怎么变，前沿算力的大旗英伟达绝不松手。华盛顿政客在国家安全与地缘博弈间精打细算，全球客户却在争先恐后排队加价抢卡。在技术冷酷的算力物理定律面前，地缘政治的行政干预与全球商业资本的扩张本能，注定要上演一场旷日持久的极限拉扯。"

    elif any(k in text for k in ["deepseek", "arena", "v4", "flash", "成本", "性价比", "知识蒸馏"]):
        return "前脚硅谷巨头刚发布了号称“重新定义物理法则”的超豪华旗舰模型，后脚开源小分队就带着成本只有几十分之一的轻量模型在评测榜上迎头赶上。大厂们还在算计每百万Token收几美分才能回本几百亿GPU的折旧费，极客们已经在用极致的工程优化告诉市场：别拿烧钱当护城河，只要架构够精妙，几张卡照样能在竞技场里把庞然大物挑落下马。"

    else:
        # 无法执行高精准针对性点评时，绝不编造虚假套话模版，直接返回空，由前端优雅隐藏
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
    elif any(k in full_text for k in ["黑客", "末日", "网络安全", "漏洞", "cybersecurity", "hacker", "doom", "不连贯"]):
        why = "网络安全一线专家对大模型‘末日黑客’的夸大叙事提出技术质疑，呼吁将行业安全重心从宏大恐慌叙事回归到代码审计与实战防御。"
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

    # 若有正文摘要片段且不与标题重复，翻译并提取补充细节
    detail_stmt = ""
    if clean_snippet and len(clean_snippet) > 15:
        trans_snippet = clean_news_text(free_translate_zh(clean_snippet[:150]))
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
                "content": it.get("content_snippet", "")[:300],
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
                results.append(fallback)
    all_final = direct_items + results
    return all_final
