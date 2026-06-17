"""NORA — 營運長特助 / Chief of Staff。

替你管整個 AI 行銷團隊：把你的一句話拆成各專員的任務（任務派發）、
並行啟動 MAYA / LEON / IRIS / JACK、最後彙整成一份團隊週報。
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from .base import has_api_key, run_agent
from .brand import Brand
from .specialists import SPECIALISTS

NORA_NAME = "NORA"
NORA_ROLE = "營運長特助 · Chief of Staff"
NORA_ICON = "👑"

# --- 任務派發 ----------------------------------------------------------------
_DISPATCH_PROMPT = """你是 NORA，AI 行銷團隊的營運長特助。
團隊有四位專員：
- MAYA 社群小編：FB / IG / Threads 貼文
- LEON 設計總監：品牌規範、Landing / Sales Page
- IRIS SEO 專員：關鍵字、競品拆解、文章大綱
- JACK 廣告投放手：Meta 廣告素材與投放決策

根據品牌設定與老闆的一句話需求，把它拆解成每位專員「本週」的具體任務指示。

嚴格只輸出 JSON（不要 markdown、不要解釋）：
{
  "maya": "給 MAYA 的本週任務指示（一段話）",
  "leon": "給 LEON 的本週任務指示",
  "iris": "給 IRIS 的本週任務指示",
  "jack": "給 JACK 的本週任務指示",
  "deadlines": ["3-5 條本週關鍵時程，例如：週三前完成廣告素材"]
}
任務指示要具體、可執行，並扣緊老闆的需求與品牌語氣。"""

# --- 週報 --------------------------------------------------------------------
_REPORT_PROMPT = """你是 NORA，AI 行銷團隊的營運長特助。
四位專員已完成本週產出。請彙整成一份給老闆的「團隊週報」。

嚴格只輸出 JSON（不要 markdown、不要解釋）：
{
  "summary": "2-3 句總結本週團隊為這個目標做了什麼",
  "highlights": ["4-6 條跨團隊重點亮點，標明來自哪位專員"],
  "next_steps": ["3-5 條老闆需要決策或下週要推進的事"]
}
語氣專業、精簡、像真的營運長在向老闆回報。"""


def _dispatch(brand: Brand, request: str, model: str | None) -> dict:
    payload = {"品牌設定": brand.as_context(), "老闆需求": request}
    plan = run_agent(_DISPATCH_PROMPT, payload, model=model, max_tokens=1200)
    if plan and all(k in plan for k in SPECIALISTS):
        return plan
    # fallback：每位專員都收到原始需求
    fallback_brief = request or "依品牌設定推進本週例行行銷工作"
    plan = {key: fallback_brief for key in SPECIALISTS}
    plan["deadlines"] = [
        "週二前：MAYA 完成本週貼文行事曆",
        "週三前：JACK 完成廣告素材並開跑測試",
        "週四前：IRIS 交出關鍵字與文章大綱",
        "週五前：LEON 完成 Landing Page 內容",
    ]
    plan["_offline"] = True
    return plan


def _report(brand: Brand, request: str, results: dict, model: str | None) -> dict:
    # 只把每位專員產出的「摘要鍵」餵給 NORA，避免 payload 過大
    digest = {key: _digest(key, res) for key, res in results.items()}
    payload = {"品牌設定": brand.as_context(), "老闆需求": request, "各專員產出摘要": digest}
    report = run_agent(_REPORT_PROMPT, payload, model=model, max_tokens=1200)
    if report.get("summary"):
        return report
    return {
        "summary": f"本週團隊針對「{request or brand.name}」完成社群、設計、SEO 與廣告四線產出。",
        "highlights": [
            "MAYA：產出一週 14 則貼文與 Threads 開頭",
            "LEON：完成品牌規範與 Landing / Sales Page 內容",
            "IRIS：盤點 20 組關鍵字並交出文章大綱",
            "JACK：產出 5 組廣告 hook 與受眾預算分配",
        ],
        "next_steps": [
            "確認本週主打訊息與預算上限",
            "選定要先上線的 Landing Page 版本",
            "核准廣告素材後開始投放測試",
        ],
        "_offline": True,
    }


def _digest(key: str, res: dict) -> str:
    """把專員產出壓成一行摘要，給 NORA 寫週報用。"""
    if key == "maya":
        cal = res.get("weekly_calendar") or []
        return f"產出 {len(cal)} 則貼文、{len(res.get('threads_hooks') or [])} 個 Threads 開頭"
    if key == "leon":
        return f"Landing Page {len(res.get('landing_page') or [])} 區塊、Sales Page {len(res.get('sales_page') or [])} 區塊"
    if key == "iris":
        return f"關鍵字 {len(res.get('keywords') or [])} 組、文章大綱：{(res.get('article_outline') or {}).get('title', '')}"
    if key == "jack":
        return f"廣告 hook {len(res.get('ad_hooks') or [])} 組、受眾 {len((res.get('audience_budget') or {}).get('audiences') or [])} 群"
    return ""


def run_team(brand: Brand, request: str, *, model: str | None = None) -> dict:
    """跑完整個 5 人團隊，回傳結構化結果給 UI。

    回傳：
      {
        "online": bool,                 # 是否有實際呼叫 Claude
        "dispatch": {...},              # NORA 的任務派發
        "results": {key: {...}},        # 四位專員產出
        "report": {...},                # NORA 週報
      }
    """
    online = has_api_key()

    dispatch = _dispatch(brand, request, model)

    # 並行啟動四位專員
    results: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=len(SPECIALISTS)) as pool:
        futures = {
            key: pool.submit(spec.run, brand, dispatch.get(key, request), model=model)
            for key, spec in SPECIALISTS.items()
        }
        for key, fut in futures.items():
            results[key] = fut.result()

    report = _report(brand, request, results, model)

    return {
        "online": online,
        "dispatch": dispatch,
        "results": results,
        "report": report,
    }
