"""四位行銷專員：MAYA（社群）、LEON（設計）、IRIS（SEO）、JACK（廣告）。

每位專員 = 一個專屬 system prompt + 結構化 JSON 輸出 + 無 API Key 時的 fallback。
NORA（nora.py）負責派發任務並彙整結果。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .base import run_agent
from .brand import Brand

# --- 共用輸出規範：要求 Claude 嚴格輸出 JSON ---------------------------------
_JSON_RULE = (
    "\n\n嚴格只輸出 JSON（不要 markdown、不要任何解釋文字）。所有文案使用繁體中文。"
)


@dataclass
class Specialist:
    key: str
    name: str
    role: str          # 職稱，例如「社群小編」
    icon: str          # emoji，給 UI 用
    system_prompt: str
    fallback: Callable[[Brand, str], dict]

    def run(self, brand: Brand, brief: str, *, model: str | None = None) -> dict:
        """執行任務。無 API Key（run_agent 回 {}）時走 fallback。"""
        payload = {
            "品牌設定": brand.as_context(),
            "本週任務指示": brief,
        }
        result = run_agent(self.system_prompt + _JSON_RULE, payload, model=model, max_tokens=2200)
        return result or self.fallback(brand, brief)


# === MAYA 社群小編 ===========================================================
MAYA_PROMPT = """你是 MAYA，資深社群小編，負責經營品牌的 FB / IG / Threads。
根據品牌設定與本週任務，產出可直接發佈的社群內容。

請輸出以下 JSON 結構：
{
  "threads_hooks": ["5 個吸睛的 Threads 開頭句，每句最多 30 字"],
  "weekly_calendar": [
    {"day": "週一", "channel": "IG", "topic": "貼文主題", "caption": "完整貼文文案（含 hashtag）"}
  ],
  "rewrites": {
    "original": "挑一篇上面的貼文作為原始版本",
    "versions": ["改寫版本 A（更口語）", "改寫版本 B（更專業）", "改寫版本 C（更促銷）"]
  }
}

規則：weekly_calendar 請排滿一週共 14 則貼文，平均分配在 FB、IG、Threads；
caption 要符合品牌語氣，聚焦真實賣點，避免浮誇空話。"""


def _maya_fallback(brand: Brand, brief: str) -> dict:
    name = brand.name or "你的品牌"
    sp = brand.selling_points or ["品質保證", "快速出貨", "貼心售後"]
    channels = brand.channels or ["Facebook", "Instagram", "Threads"]
    days = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]
    calendar = []
    for i in range(14):
        ch = channels[i % len(channels)]
        point = sp[i % len(sp)]
        calendar.append(
            {
                "day": days[i % 7],
                "channel": ch,
                "topic": f"{point} 主題貼文",
                "caption": f"【{name}】{point}！{brief or '本週主打'} #{name} #{point}",
            }
        )
    return {
        "threads_hooks": [f"{name}：{p}，你還在猶豫嗎？" for p in sp[:5]] or [f"{name} 新上架"],
        "weekly_calendar": calendar,
        "rewrites": {
            "original": calendar[0]["caption"],
            "versions": [
                f"（口語）欸你知道 {name} 的 {sp[0]} 嗎？",
                f"（專業）{name} 採用 {sp[0]}，為你帶來實質升級。",
                f"（促銷）限時優惠！{name} {sp[0]}，把握機會。",
            ],
        },
        "_offline": True,
    }


# === LEON 設計總監 ===========================================================
LEON_PROMPT = """你是 LEON，設計總監，不只給視覺方向，連 Landing Page 和 Sales Page 完整內容都包。
根據品牌設定與本週任務，產出品牌規範與頁面內容結構。

請輸出以下 JSON 結構：
{
  "brand_guidelines": {
    "color_direction": "主色與輔色方向描述",
    "typography": "字體建議",
    "imagery": "影像 / 風格方向",
    "do": ["設計該做的 3 件事"],
    "dont": ["設計該避免的 3 件事"]
  },
  "landing_page": [
    {"section": "Hero", "headline": "主標", "subhead": "副標", "body": "說明文案", "cta": "按鈕文字"}
  ],
  "sales_page": [
    {"section": "區塊名稱", "content": "完整文案內容"}
  ]
}

規則：landing_page 至少包含 Hero、核心賣點、社會證明、CTA 四個區塊；
sales_page 至少包含痛點、解方、產品特色、價格方案、保證、FAQ 等區塊。"""


def _leon_fallback(brand: Brand, brief: str) -> dict:
    name = brand.name or "你的品牌"
    sp = brand.selling_points or ["核心優勢一", "核心優勢二", "核心優勢三"]
    return {
        "brand_guidelines": {
            "color_direction": "以品牌主色為基底，搭配 1 個強調色用於 CTA",
            "typography": "標題用粗黑體、內文用易讀無襯線體",
            "imagery": "情境化產品圖，乾淨背景，聚焦使用者",
            "do": ["維持版面留白", "CTA 顏色一致", "圖文比例平衡"],
            "dont": ["避免過多字體", "避免雜亂背景", "避免低對比文字"],
        },
        "landing_page": [
            {"section": "Hero", "headline": f"{name}，{brief or '為你而生'}", "subhead": sp[0], "body": f"{name} 幫你解決日常痛點。", "cta": "立即了解"},
            {"section": "核心賣點", "headline": "為什麼選我們", "subhead": "", "body": "、".join(sp), "cta": ""},
            {"section": "社會證明", "headline": "顧客怎麼說", "subhead": "", "body": "已有眾多顧客信賴推薦。", "cta": ""},
            {"section": "CTA", "headline": "現在就開始", "subhead": "", "body": "限時優惠進行中。", "cta": "馬上購買"},
        ],
        "sales_page": [
            {"section": "痛點", "content": f"你是否也為 {brand.industry or '這件事'} 感到困擾？"},
            {"section": "解方", "content": f"{name} 提供完整解決方案。"},
            {"section": "產品特色", "content": "、".join(sp)},
            {"section": "價格方案", "content": "提供多種方案，總有一款適合你。"},
            {"section": "保證", "content": "不滿意可退，購買無負擔。"},
            {"section": "FAQ", "content": "常見問題一次解答。"},
        ],
        "_offline": True,
    }


# === IRIS SEO 專員 ===========================================================
IRIS_PROMPT = """你是 IRIS，SEO 專員，每月幫品牌抓高潛力關鍵字、拆解競品、產出附 SEO 的文章大綱。
根據品牌設定與本週任務，產出關鍵字機會與文章規劃。

請輸出以下 JSON 結構：
{
  "keywords": [
    {"keyword": "關鍵字", "intent": "資訊型/商業型/交易型", "difficulty": "低/中/高", "note": "切入建議"}
  ],
  "competitor_teardown": ["3-5 點競品文章可改善 / 可超越的觀察"],
  "article_outline": {
    "title": "文章標題",
    "meta_title": "SEO 標題（最多 30 字）",
    "meta_description": "SEO 描述（最多 80 字）",
    "outline": ["H2 段落標題與重點"]
  }
}

規則：keywords 請列出 20 組高潛力關鍵字，涵蓋不同搜尋意圖；
article_outline 的大綱至少 6 個 H2，聚焦能帶來自然流量的主題。"""


def _iris_fallback(brand: Brand, brief: str) -> dict:
    industry = brand.industry or brand.name or "你的品類"
    seeds = brand.selling_points or [industry]
    keywords = []
    templates = ["{} 推薦", "{} 比較", "{} 評價", "{} 怎麼選", "{} 入門", "{} 品牌"]
    for i in range(20):
        base = seeds[i % len(seeds)]
        kw = templates[i % len(templates)].format(base if i % 2 else industry)
        keywords.append(
            {
                "keyword": kw,
                "intent": ["資訊型", "商業型", "交易型"][i % 3],
                "difficulty": ["低", "中", "高"][i % 3],
                "note": "從長尾切入，先卡資訊型版位",
            }
        )
    return {
        "keywords": keywords,
        "competitor_teardown": [
            "競品文章缺乏實測數據，可補上具體比較",
            "競品標題未含主關鍵字，可優化 Meta",
            "競品內文結構鬆散，可用清楚 H2 分段",
        ],
        "article_outline": {
            "title": f"{industry} 完整選購指南",
            "meta_title": f"{industry} 怎麼選？2024 指南",
            "meta_description": f"想入手 {industry}？本文帶你一次看懂挑選重點與推薦。",
            "outline": [
                f"H2：什麼是 {industry}",
                "H2：挑選前要先想清楚的 3 件事",
                "H2：關鍵規格怎麼看",
                "H2：常見品牌與價位帶比較",
                f"H2：{brand.name or '我們'} 的優勢",
                "H2：常見問題 FAQ",
            ],
        },
        "_offline": True,
    }


# === JACK 廣告投放手 =========================================================
JACK_PROMPT = """你是 JACK，廣告投放手，每天看 Meta 數據幫品牌決策（加碼、暫停、換素材）。
根據品牌設定與本週任務，產出廣告素材、每日數據簡報規則與受眾預算分配。

請輸出以下 JSON 結構：
{
  "ad_hooks": [
    {"hook": "廣告開頭 hook", "primary_text": "主文案", "cta": "行動呼籲"}
  ],
  "daily_report_template": ["每天要看的指標與加碼/暫停/換素材的判斷規則"],
  "audience_budget": {
    "audiences": [{"name": "受眾名稱", "targeting": "鎖定方式", "budget_pct": 40}],
    "notes": "預算分配與測試建議"
  }
}

規則：ad_hooks 請給 5 組不同角度（痛點、好奇、優惠、社會證明、急迫感）；
audience_budget 的 budget_pct 加總為 100。"""


def _jack_fallback(brand: Brand, brief: str) -> dict:
    name = brand.name or "你的品牌"
    sp = brand.selling_points or ["核心賣點"]
    return {
        "ad_hooks": [
            {"hook": f"還在為 {brand.industry or '這件事'} 煩惱嗎？", "primary_text": f"{name} 幫你解決。", "cta": "了解更多"},
            {"hook": "你絕對沒想到的小秘密…", "primary_text": f"{name}：{sp[0]}。", "cta": "立即查看"},
            {"hook": "限時優惠倒數中！", "primary_text": f"{name} 特惠進行中。", "cta": "搶購"},
            {"hook": "上萬人都選它", "primary_text": f"{name} 深受信賴。", "cta": "看看為什麼"},
            {"hook": "今天不買，明天就漲價", "primary_text": f"{name} 限時價。", "cta": "馬上下單"},
        ],
        "daily_report_template": [
            "看 CTR：低於 1% 換素材",
            "看 CPA：高於目標 1.5 倍暫停該組",
            "看 ROAS：高於 3 的受眾加碼預算 20%",
        ],
        "audience_budget": {
            "audiences": [
                {"name": "核心受眾", "targeting": brand.audience or "主要客群興趣", "budget_pct": 50},
                {"name": "類似受眾 1%", "targeting": "購買者 LAL 1%", "budget_pct": 30},
                {"name": "再行銷", "targeting": "近 30 天造訪未購買", "budget_pct": 20},
            ],
            "notes": "先用核心受眾測素材，跑出贏家再擴量到類似受眾。",
        },
        "_offline": True,
    }


# === 註冊表（NORA 依此派發） =================================================
SPECIALISTS: dict[str, Specialist] = {
    "maya": Specialist("maya", "MAYA", "社群小編", "📣", MAYA_PROMPT, _maya_fallback),
    "leon": Specialist("leon", "LEON", "設計總監", "🎨", LEON_PROMPT, _leon_fallback),
    "iris": Specialist("iris", "IRIS", "SEO 專員", "🔍", IRIS_PROMPT, _iris_fallback),
    "jack": Specialist("jack", "JACK", "廣告投放手", "📊", JACK_PROMPT, _jack_fallback),
}
