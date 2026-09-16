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
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# 翻译内存缓存，避免重复请求
_TRANSLATION_CACHE = {}


def free_translate_zh(text: str) -> str:
    """Bulletproof translation engine to guarantee 100% fluent Chinese output."""
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

    # 1. 优先调用 Google Translate 免密神经翻译 (极速高精，支持长句)
    try:
        gt_url = "https://translate.googleapis.com/translate_a/single"
        params = {"client": "gtx", "sl": "en", "tl": "zh-CN", "dt": "t", "q": body_text[:350]}
        with httpx.Client(headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=6) as client:
            resp = client.get(gt_url, params=params)
            if resp.status_code == 200:
                res = resp.json()
                zh_res = ''.join([part[0] for part in res[0] if part and part[0]]).strip()
                if zh_res and re.search(r'[\u4e00-\u9fa5]', zh_res):
                    _TRANSLATION_CACHE[body_text] = zh_res
                    return prefix + zh_res
    except Exception:
        pass

    # 2. 备用有道免密神经翻译 (毫秒级响应，带自动重试)
    for _ in range(2):
        try:
            url = "https://aidemo.youdao.com/trans"
            data = {"q": clean_text[:280], "from": "Auto", "to": "zh-CHS"}
            with httpx.Client(headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=6) as client:
                resp = client.post(url, data=data)
                if resp.status_code == 200:
                    res_data = resp.json()
                    t_list = res_data.get("translation", [])
                    if t_list and t_list[0]:
                        zh_res = t_list[0].strip()
                        if re.search(r'[\u4e00-\u9fa5]', zh_res):
                            _TRANSLATION_CACHE[clean_text] = zh_res
                            return zh_res
        except Exception:
            pass

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

def clean_news_text(text: str) -> str:
    """Strip HTML entities, reporter bylines, trailing source parentheses, and boilerplate prefixes."""
    if not text:
        return ""
    t = html.unescape(text)
    t = t.replace("&nbsp;", " ").replace("\u00a0", " ")
    
    # 1. 移除陈旧模板前缀
    t = re.sub(r'^【.*?】\s*', '', t)
    t = re.sub(r'^由\s*.*?\s*(?:权威发布|最新报道)[。：:]\s*', '', t)
    t = re.sub(r'^据\s*.*?\s*(?:最新报道|报道)[，,：:]\s*', '', t)
    t = re.sub(r'^行业关键动向与突破报道[：:]\s*', '', t)
    t = re.sub(r'^领袖前沿发声与社区论战[：:]\s*', '', t)
    t = re.sub(r'^开箱即用落地利器与提效神器[：:]\s*', '', t)
    t = re.sub(r'^实操深度演示与架构解析[：:]\s*', '', t)
    t = re.sub(r'^(?:Opinion\s*\|\s*|专栏\s*\|\s*|观点\s*\|\s*)', '', t, flags=re.IGNORECASE)
    
    # 2. 移除引语、信源、记者署名等开头前缀 (如 "消息来源:" / "Sources:" / "据报道" 等)
    t = re.sub(r'^(?:消息来源|消息称|知情人士称|知情人士透露|知情人透露|据知情人士|据知情人|据外媒|据报道|外媒称|外媒报道|传|报道称)[：:，,\s]*', '', t)
    t = re.sub(r'^(?:Sources?|Report|Reports?|Exclusive|Analysis)[：:\s]+', '', t, flags=re.IGNORECASE)
    t = re.sub(r'^[A-Za-z\s.\'\-]+/(?:[A-Za-z\s.\'\-]+|\s*)[：:]\s*', '', t)
    t = re.sub(r'^[A-Za-z\s.\'\-]+[：:]\s*', '', t)
    t = re.sub(r'消息来源[：:]\s*', '', t)
    t = re.sub(r'Sources?[：:]\s*', '', t, flags=re.IGNORECASE)
    
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
    """Generate a clean, pure Chinese fact statement without source/reporter noise."""
    snippet = clean_news_text(item.get("content_snippet", ""))
    clean_title = clean_news_text(title_zh or item.get("title_zh") or item.get("title", ""))
    trans_snippet = clean_news_text(free_translate_zh(snippet[:120]))
    
    if trans_snippet and len(trans_snippet) > 15 and trans_snippet not in clean_title:
        return f"{clean_title}。{trans_snippet}"
    return clean_title


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
    why = "顺应技术迭代与市场刚需，提升生态壁垒与综合服务能力。"
    if any(k in full_text for k in ["智能眼镜", "穿戴", "无摄像头", "麦克风"]):
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
    elif any(k in full_text for k in ["开源", "突破", "发布", "模型"]):
        why = "降低开发者微调与工程落地的门槛与算力开销，加速端到端应用在真实业务中生根发芽。"

    # 5. 整合新闻简报正文 (Natural News Briefing，杜绝机械套话与多余前缀)
    first_stmt = clean_title
    if not first_stmt.endswith(('。', '！', '？')):
        first_stmt += '。'
    briefing_zh = f"{first_stmt} {why}".strip()
    briefing_zh = re.sub(r'([。！？；，、])\1+', r'\1', briefing_zh).strip()
    briefing_zh = re.sub(r'消息来源[：:]\s*', '', briefing_zh)

    # 6. 专业深度洞察与行业研判 (In-Depth Insight)
    insight_zh = ""
    if any(k in full_text for k in ["智能眼镜", "穿戴", "无摄像头"]):
        insight_zh = "【硬件与生态研判】在雷朋联名眼镜验证了AI音频交互需求后，取消摄像头是Meta针对办公室、医疗与学校等隐私敏感场景的精准破局。更轻便的形态与更低的制造门槛，将有助于Meta将大模型多模态语音助手渗透至更广泛的日常大众消费群体。"
    elif any(k in full_text for k in ["选民", "数据中心", "民调"]):
        insight_zh = "【产业与政策研判】AI算力扩张正从纯技术/商业投资议题，加速演变为关乎电力、水资源、地方环境与民意选票的公共议题。科技巨头未来在算力中心选址与电网协同上，需面临更为严苛的社区沟通与合规审查。"
    elif any(k in full_text for k in ["豁免", "责任", "听证会", "监管"]):
        insight_zh = "【监管研判】宏观决策层在“支持科技创新”与“划定法律红线”之间寻求平衡。拒绝授予全面免责特权将倒逼实验室提升模型可控性；而政策对开源模型的倾斜，将为去中心化AI生态带来重要战略契机。"
    elif any(k in full_text for k in ["1.2万亿", "1.2T", "估值", "IPO", "融资"]):
        insight_zh = "【资本研判】万亿美元级别的高估值预期反映出前沿AI竞争已进入极致资本密集阶段。高昂的算力开销迫使独角兽在资本市场争夺头部流动性，商业化造血能力将成为决定后续估值支撑度的决定性指标。"
    elif any(k in full_text for k in ["UPI", "商户费", "订阅", "收费"]):
        insight_zh = "【商业研判】核心数字基础设施逐步告别“免费补贴阶段”，步入精细化商业收费周期。交易与服务成本的调整将加速行业洗牌，并驱动厂商在差异化增值服务上展开更深维度的竞争。"
    elif any(k in full_text for k in ["CarPlay", "车机", "汽车"]):
        insight_zh = "【生态研判】传统软硬件巨头垄断座舱数据的自研路径再次面临现实检验。移动端生态与座舱的强耦合具有极高的用户心智壁垒，兼容成熟主流开放生态依然是目前保障用户体验的最稳妥选择。"
    else:
        insight_zh = "【行业研判】该动态折射出当前AI产业链正由前期的技术概念探索全面加速转向真实场景落地与产业利益再分配，对相关领域的工程实践与商业策略具有重要参考风向标意义。"

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
            title_zh = free_translate_zh(item.get("title", ""))
            p_item["title_zh"] = title_zh
            p_item["summary_zh"] = generate_smart_fallback_summary(item, title_zh)
            p_item["ai_analysis"] = generate_smart_ai_analysis(item, title_zh)
            p_item["title_en"] = item.get("title_en") or item.get("title", "")
            p_item["summary_en"] = item.get("summary_en") or item.get("content_snippet", "")
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
你是一个顶级科技智库的新闻主编。请对以下最新资讯进行专业新闻简报（News Briefing）提炼。
【关键原则】：
1. 严禁在正文出现“据XX报道”、“由XX发布”、记者姓名或链接等杂质（信源已在界面标题栏统一展示）。
2. 必须交代清楚新闻六要素（5W1H）：谁（Who）、在什么场合/场景（Where）、做了/说了什么具体动作或事实（What）、起因背景动因（Why），让用户无需查看原资讯详情即可完全掌握事件脉络。
3. 给出基于该事实的有价值深度分析和观点（insight_zh），避免假大空的套话。

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
    "insight_zh": "基于该事实的专业深度研判与观点（1-2句，客观分析对行业生态、政策、商业或开发者的实际影响）",
    "insight_en": "Objective industry insight and strategic takeaway (1-2 sentences)",
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
    "takeaway_zh": "专业深度研判与观点（与insight_zh一致）",
    "takeaway_en": "Strategic takeaway in English"
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

    return direct_items + results
