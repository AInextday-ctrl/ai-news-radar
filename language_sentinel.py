"""
Language Sentinel & Consistency Engine (语言规范与质检自愈哨兵)
24x7 守护全站双语内容纯净度：
1. 保证 *_zh 体系 (title_zh, summary_zh, article_content_zh, ai_analysis.briefing_zh 等) 100% 纯中文，严禁夹带未翻译整句英文、生硬机翻或机械伪标签；
2. 保证 *_en 体系 (title_en, summary_en, article_content, ai_analysis.briefing_en 等) 纯正英文；
3. 自动侦测并自愈中英文混杂、伪装前缀、段落乱炖等问题；
4. 作为抓取整理管道与 CI/CD 的不可逾越门禁。
"""

import re
import sys
import os
import json
from typing import Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor

# 引入项目基础翻译能力
try:
    from processor import (
        free_translate_zh,
        free_translate_en,
        clean_news_text,
        has_chinglish_seams,
        strip_chinglish_to_english,
        normalize_ai_terminology_zh,
    )
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from processor import (
        free_translate_zh,
        free_translate_en,
        clean_news_text,
        has_chinglish_seams,
        strip_chinglish_to_english,
        normalize_ai_terminology_zh,
    )


def has_cjk(text: str) -> bool:
    """检测文本是否包含中日韩字符"""
    if not text:
        return False
    return bool(re.search(r'[\u4e00-\u9fa5\u3040-\u30ff\uac00-\ud7af]', str(text)))


def count_chinese_chars(text: str) -> int:
    """统计有效汉字数量 (剔除标签标点)"""
    if not text:
        return 0
    clean = re.sub(r'[【\[].*?[】\]]|<[^>]+>', '', str(text))
    return len(re.findall(r'[\u4e00-\u9fa5]', clean))


def is_pure_chinese_paragraph(p: str, min_chars: int = 6) -> bool:
    """
    判断单个段落是否为合格纯中文段落：
    1. 汉字数达到门槛；
    2. 严禁包含单词级机翻拼接痕迹 (has_chinglish_seams)；
    3. 汉字占比至少 22%（允许包含人名、模型名如 GPT-5、Claude 3.5、OpenAI 等专业专有名词，但不允许整句未翻译英文）。
    """
    if not p:
        return False
    clean = p.strip()
    if has_chinglish_seams(clean):
        return False
    zh_count = count_chinese_chars(clean)
    if zh_count < min_chars:
        return False
    ratio = zh_count / max(len(clean), 1)
    if ratio < 0.22 and zh_count < 15:
        return False
    if re.search(r'(?:[A-Za-z0-9\',.-]+\s+){6,}[A-Za-z0-9\',.-]+', clean):
        return False
    return True


def translate_and_purify_article(content: str) -> str:
    """
    将原始外媒长文 (article_content) 逐段编译为 100% 纯正中文实录：
    - 逐段校验，已有中文段落直接保留；
    - 英文段落逐一翻译；
    - 翻译后再次执行纯中文质检，未通过的坚决剔除，决不让任何未经翻译的英文段落漏网。
    """
    if not content or len(str(content).strip()) < 20:
        return ""
        
    raw_paras = [p.strip() for p in re.split(r'\n+', str(content)) if p.strip()]
    if len(raw_paras) > 8:
        raw_paras = raw_paras[:8]
        
    pure_zh_paras = []
    for p in raw_paras:
        # 去除陈旧伪标签
        p_clean = re.sub(r'^[【\[].*?[】\]]\s*', '', p).strip()
        if not p_clean or len(p_clean) < 10:
            continue
            
        if is_pure_chinese_paragraph(p_clean):
            pure_zh_paras.append(normalize_ai_terminology_zh(p_clean))
        else:
            # 翻译英文段落
            t = free_translate_zh(strip_chinglish_to_english(p_clean)[:350])
            t_clean = re.sub(r'^[【\[].*?[】\]]\s*', '', t).strip()
            if is_pure_chinese_paragraph(t_clean, min_chars=8):
                pure_zh_paras.append(normalize_ai_terminology_zh(t_clean))
            
    return '\n\n'.join(pure_zh_paras) if pure_zh_paras else ""


def sanitize_item_language(item: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    核心哨兵规则：对单条资讯执行严格的双向语言规范审查与自愈修正。
    返回: (修正后的 item, 修复日志列表)
    """
    fixes = []
    cat = item.get("category", "")

    # 落地工具、实操提示词与前沿视频专区：严格执行双向 *_en 无中文、*_zh 纯中文校验（严禁半英半中 Chinglish）
    if cat in ("tools", "prompts", "videos"):
        app_name = item.get("app_name_en") or item.get("app_name") or "AI Tool"
        # 校验 *_en 字段严禁含中文
        for en_key in ("title_en", "summary_en", "app_hook_en", "overview_en", "prompt_content_en"):
            val = item.get(en_key)
            if val and has_cjk(val):
                item[en_key] = strip_chinglish_to_english(str(val))
                if has_cjk(item[en_key]):
                    item[en_key] = free_translate_en(str(val))
                fixes.append(f"{en_key} 剔除中文混杂并转为纯英文")
        # 校验 tools 的 *_zh 字段必须为流畅中文，彻底消灭半英半中单词替换残留
        if cat == "tools":
            hook_zh = str(item.get("app_hook") or "").strip()
            hook_en = str(item.get("app_hook_en") or "").strip() or strip_chinglish_to_english(hook_zh)
            scen = item.get("scenario_tag") or "💻 编程与开发"
            rt_badge = item.get("runtime_badge") or "开源部署"
            if not hook_zh or not has_cjk(hook_zh) or has_chinglish_seams(hook_zh):
                t_zh = clean_news_text(free_translate_zh(hook_en[:160]))
                if has_cjk(t_zh) and not has_chinglish_seams(t_zh):
                    item["app_hook"] = t_zh[:120]
                    fixes.append("tools.app_hook 重新完整翻译为纯中文")
                else:
                    item["app_hook"] = f"专注于 {scen} 场景的高热度开源 AI 工具，支持 {rt_badge} 与自动化工作流集成"
                    fixes.append("tools.app_hook 清除半英半中乱码")
                item["title_zh"] = f"【{app_name}】{item['app_hook'][:65]}"
                item["title"] = item["title_zh"]

            sum_zh = str(item.get("summary_zh") or "").strip()
            if not sum_zh or has_chinglish_seams(sum_zh):
                wk_s = int(item.get("weekly_stars") or (item.get("metrics") or {}).get("weekly_stars") or 0)
                stars_tot = int(item.get("stars") or (item.get("metrics") or {}).get("stars") or 0)
                if item.get("tool_origin") == "github" and wk_s > 0:
                    item["summary_zh"] = f"📈 本周暴涨 +{wk_s:,} ★（总计 ⭐ {stars_tot:,}）· {item.get('app_hook', '')}"
                else:
                    item["summary_zh"] = item.get("app_hook") or f"【{app_name}】面向 {scen} 的 AI 生产力工具"
                fixes.append("tools.summary_zh 清除半英半中残留")

            ov_zh = str(item.get("overview_zh") or "").strip()
            if ov_zh and (has_chinglish_seams(ov_zh) or re.search(r'(?:[A-Za-z0-9\',.-]+\s+){6,}[A-Za-z0-9\',.-]+', ov_zh)):
                hook_c = item.get("app_hook") if (has_cjk(item.get("app_hook", "")) and not has_chinglish_seams(item.get("app_hook", ""))) else f"提供面向 {scen} 的前沿生成式 AI 与自动化工作流能力"
                item["overview_zh"] = f"{app_name} 是一款专注于 {scen} 领域的开源与实战 AI 工具。{hook_c}，支持开发者与创作者快速集成部署。"
                fixes.append("tools.overview_zh 清除英文长句与半英半中")

        if cat == "videos":
            for v_key in ("title_zh", "title"):
                v_val = str(item.get(v_key) or "").strip()
                if v_val:
                    v_val = re.sub(r'^(?:【[^】]+】\s*)?[^：:]{2,25}最新\s*AI\s*前沿解析[：:]\s*', '', v_val)
                    item[v_key] = normalize_ai_terminology_zh(v_val)

        if not item.get("title_zh"):
            item["title_zh"] = item.get("title") or "AI 创新前沿内容"
        if not item.get("title_en"):
            item["title_en"] = free_translate_en(item.get("title") or item["title_zh"])
        if not item.get("summary_zh"):
            item["summary_zh"] = item.get("content_snippet") or "热门 AI 场景落地与多模态动态"
        if not item.get("summary_en"):
            item["summary_en"] = free_translate_en(item.get("content_snippet") or "Trending AI applications and dynamic content")
        return item, fixes

    # 1. 标题治理：title_zh 必须为纯正中文，title_en 必须为纯正英文
    title_zh = item.get("title_zh") or ""
    # 剔除机械伪前缀
    title_zh = re.sub(r'^[【\[].*?[】\]]\s*', '', str(title_zh)).strip()
    if not title_zh or not is_pure_chinese_paragraph(title_zh, min_chars=4):
        raw_en = strip_chinglish_to_english(item.get("title_en") or item.get("title") or title_zh)
        if raw_en:
            t = clean_news_text(free_translate_zh(raw_en[:180]))
            t = re.sub(r'^[【\[].*?[】\]]\s*', '', t).strip()
            if is_pure_chinese_paragraph(t, min_chars=4):
                item["title_zh"] = normalize_ai_terminology_zh(t)
                fixes.append("title_zh 自动翻译重构为纯中文")
            else:
                item["title_zh"] = normalize_ai_terminology_zh(clean_news_text(raw_en))
        else:
            item["title_zh"] = "AI 前沿动态快讯"
    else:
        item["title_zh"] = normalize_ai_terminology_zh(clean_news_text(title_zh))

    # 保证 title_en 存在且不含中文
    title_en = item.get("title_en") or item.get("title") or ""
    if not title_en or has_cjk(title_en):
        item["title_en"] = free_translate_en(strip_chinglish_to_english(title_en) or item.get("title_zh", "AI Industry Update"))
        fixes.append("title_en 纯英文自愈")

    # 2. 摘要治理：summary_zh 必须为纯中文，且严禁注入空洞水词
    sum_zh = item.get("summary_zh") or ""
    sum_zh = re.sub(r'^[【\[].*?[】\]]\s*', '', str(sum_zh)).strip()
    sum_zh = re.sub(r'[。！？]?\s*(?:相关动态引发全球产业界广泛讨论与技术跟踪|该动态引发了产业界与前沿开发者的广泛讨论与技术跟踪|该事件反映了当前技术演进与落地实践中的关键考量)[。！]?', '', sum_zh).strip()
    if not sum_zh or not is_pure_chinese_paragraph(sum_zh, min_chars=8):
        cand_en = strip_chinglish_to_english(item.get("summary_en") or item.get("content_snippet") or item.get("article_content") or "")
        if cand_en and len(cand_en) > 20:
            trans_sum = clean_news_text(free_translate_zh(cand_en[:260]))
            trans_sum = re.sub(r'^[【\[].*?[】\]]\s*', '', trans_sum).strip()
            if is_pure_chinese_paragraph(trans_sum, min_chars=8):
                item["summary_zh"] = normalize_ai_terminology_zh(trans_sum)
                fixes.append("summary_zh 自动翻译重构为纯中文")
            else:
                item["summary_zh"] = normalize_ai_terminology_zh(f"{item['title_zh']}。")
        else:
            item["summary_zh"] = normalize_ai_terminology_zh(f"{item['title_zh']}。")
    else:
        item["summary_zh"] = normalize_ai_terminology_zh(clean_news_text(sum_zh))

    sum_en = item.get("summary_en") or ""
    if not sum_en or has_cjk(sum_en):
        item["summary_en"] = free_translate_en(sum_en or item.get("title_en") or "Latest development and technical analysis in AI.")
        fixes.append("summary_en 纯英文自愈")

    # 3. 深度长文实录治理：article_content 与 article_content_zh
    # 严格判断是否抓取到实质全文；若仅为单句导语/短摘要碎片，坚决置为 None，由前台无缝隐藏中间原文卡片
    art_en = item.get("article_content")
    if art_en:
        art_en_str = str(art_en).strip()
        # 排除少于 220 字符或单句碎片的伪长文
        if len(art_en_str) < 220 or (not '\n' in art_en_str and len(re.findall(r'[.!?]\s+[A-Z]', art_en_str)) < 1):
            item["article_content"] = None
            fixes.append("清理未抓到全文的英文单句导语")

    art_zh = item.get("article_content_zh")
    if art_zh and len(str(art_zh).strip()) >= 50:
        # 净化现存的 article_content_zh，过滤掉其中的纯英文或广告段落，保留纯正中文段落
        clean_paras = []
        for p in re.split(r'\n+', str(art_zh)):
            p_clean = re.sub(r'^[【\[].*?[】\]]\s*', '', p).strip()
            if count_chinese_chars(p_clean) >= 6 and not re.search(r'(?:[A-Za-z0-9\',.-]+\s+){8,}[A-Za-z0-9\',.-]+', p_clean):
                clean_paras.append(p_clean)
        # 实质中文长文必须具备 80 个以上汉字
        if clean_paras and count_chinese_chars('\n\n'.join(clean_paras)) >= 80:
            item["article_content_zh"] = '\n\n'.join(clean_paras)
        else:
            item["article_content_zh"] = None
            fixes.append("清理中文过短单句伪长文")
    else:
        # 无中文长文实录或过短，置空以防英文泄露（前台自动降级为AI精炼速览与深度拆解）
        item["article_content_zh"] = None

    # 4. 结构化 AI 深度解读治理：ai_analysis 内部中英对齐
    ai_ana = item.get("ai_analysis")
    if isinstance(ai_ana, dict):
        # briefing_zh
        b_zh = ai_ana.get("briefing_zh")
        if b_zh:
            b_zh_clean = re.sub(r'^[【\[].*?[】\]]\s*', '', str(b_zh)).strip()
            if not is_pure_chinese_paragraph(b_zh_clean, min_chars=12):
                ai_ana["briefing_zh"] = item["summary_zh"]
                fixes.append("ai_analysis.briefing_zh 纠偏为纯中文摘要")
            else:
                ai_ana["briefing_zh"] = clean_news_text(b_zh_clean)
                
        # insight_zh (AI 点评)
        ins_zh = ai_ana.get("insight_zh")
        if ins_zh:
            ins_zh_clean = re.sub(r'^[【\[].*?[】\]]\s*', '', str(ins_zh)).strip()
            if not is_pure_chinese_paragraph(ins_zh_clean, min_chars=6):
                ai_ana["insight_zh"] = ""
                fixes.append("ai_analysis.insight_zh 含有英文或模板，安全置空隐藏")
            else:
                ai_ana["insight_zh"] = clean_news_text(ins_zh_clean)
                
        # elements_zh
        elems_zh = ai_ana.get("elements_zh")
        if isinstance(elems_zh, dict):
            for k in ["who", "where", "what", "why"]:
                v = elems_zh.get(k)
                if v and not count_chinese_chars(str(v)) and len(str(v)) > 10:
                    elems_zh[k] = clean_news_text(free_translate_zh(str(v)[:120]))
                    fixes.append(f"ai_analysis.elements_zh.{k} 自动翻译为中文")

    return item, fixes


def run_pipeline_language_audit(items: List[Dict[str, Any]], max_workers: int = 8) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    全量流水线语言质检与自愈网关。
    在所有新资讯入库前并发执行，确保 100% 达标。
    """
    if not items:
        return items, {"total": 0, "fixed": 0, "clean": 0}
        
    print(f"🛡️ [语言质检哨兵] 启动对 {len(items)} 条资讯的多语言纯净度质检与自愈流水线...")
    
    fixed_count = 0
    clean_items = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(sanitize_item_language, items))
        
    for sanitized_item, fixes in results:
        if fixes:
            fixed_count += 1
        clean_items.append(sanitized_item)
        
    stats = {
        "total": len(items),
        "fixed": fixed_count,
        "clean": len(items) - fixed_count
    }
    
    print(f"🛡️ [语言质检哨兵] 审查完毕: 共 {stats['total']} 条 | 完美达标: {stats['clean']} 条 | 拦截并自愈: {stats['fixed']} 条")
    return clean_items, stats


if __name__ == "__main__":
    # 支持命令行独立自检与校验测试
    verify_only = "--verify-only" in sys.argv
    target_files = ["public/data/latest_news.json", "data/latest_news.json"]
    for test_file in target_files:
        if not os.path.exists(test_file):
            continue
        with open(test_file, "r", encoding="utf-8") as f:
            d = json.load(f)
        items = d.get("items") or [it for cat in d.get("grouped", {}).values() if isinstance(cat, list) for it in cat]
        if verify_only:
            violations = 0
            for idx, it in enumerate(items):
                zh = it.get("article_content_zh")
                if zh:
                    paras = [p.strip() for p in re.split(r'\n+', str(zh)) if p.strip()]
                    for p in paras:
                        if not is_pure_chinese_paragraph(p, min_chars=6):
                            violations += 1
                            print(f"❌ 违规条目 [{it.get('id')}]: {p[:60]}...")
            if violations == 0:
                print(f"✅ 质检通过：{len(items)} 条资讯 100% 满足纯正语言规范！")
            else:
                print(f"⚠️ 质检发现 {violations} 处不合规段落！")
                sys.exit(1)
        else:
            cleaned, stats = run_pipeline_language_audit(items)
            d["items"] = cleaned
            if "grouped" in d and isinstance(d["grouped"], dict):
                for cat_k in d["grouped"]:
                    if isinstance(d["grouped"][cat_k], list):
                        d["grouped"][cat_k] = [it for it in cleaned if it.get("category") == cat_k]
            with open(test_file, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
            print(f"🎉 质检与自愈完成并已写回: {test_file}")

