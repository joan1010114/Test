"""品牌設定：填一次、整個行銷團隊共用的脈絡。"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class Brand:
    """你的真實品牌資料。每位 agent 都會讀到這份設定。"""

    name: str = ""                       # 品牌 / 產品名稱
    industry: str = ""                   # 產業 / 品類，例如「無線降噪耳機」
    audience: str = ""                   # 目標受眾，例如「25-40 歲通勤上班族」
    tone: str = ""                       # 品牌語氣，例如「專業但親切、不浮誇」
    products: list[str] = field(default_factory=list)  # 主打產品 / 服務
    selling_points: list[str] = field(default_factory=list)  # 核心賣點
    channels: list[str] = field(default_factory=list)  # 主力通路，例如 FB / IG / Threads
    website: str = ""                    # 官網 / Landing Page 網址（可選）
    notes: str = ""                      # 其他補充（活動、禁忌字、競品等）

    def as_context(self) -> dict:
        """轉成傳給 Claude 的脈絡 dict。"""
        return asdict(self)

    def is_empty(self) -> bool:
        return not (self.name or self.industry or self.products)

    @classmethod
    def from_form(cls, form) -> "Brand":
        """從 Flask request.form 建立 Brand。多行欄位以換行分隔。"""

        def lines(key: str) -> list[str]:
            raw = form.get(key) or ""
            return [s.strip() for s in raw.splitlines() if s.strip()]

        return cls(
            name=(form.get("name") or "").strip(),
            industry=(form.get("industry") or "").strip(),
            audience=(form.get("audience") or "").strip(),
            tone=(form.get("tone") or "").strip(),
            products=lines("products"),
            selling_points=lines("selling_points"),
            channels=lines("channels") or ["Facebook", "Instagram", "Threads"],
            website=(form.get("website") or "").strip(),
            notes=(form.get("notes") or "").strip(),
        )
