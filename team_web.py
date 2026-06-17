#!/usr/bin/env python3
"""你的 5 人 AI 行銷團隊 — Flask 網頁介面。

填一次品牌設定，對 NORA 說一句話，整個團隊（MAYA / LEON / IRIS / JACK）
就會並行產出社群、設計、SEO、廣告內容，並由 NORA 彙整成週報。
"""
from __future__ import annotations

import os

from flask import Flask, render_template, request

from agents import Brand
from agents.base import DEFAULT_MODEL, has_api_key
from agents.nora import run_team
from agents.specialists import SPECIALISTS

app = Flask(__name__, template_folder="templates", static_folder="static")


@app.route("/", methods=["GET"])
def index() -> str:
    return render_template(
        "team.html",
        brand=Brand(),
        request_text="",
        data=None,
        specialists=SPECIALISTS,
        has_api_key=has_api_key(),
        model=DEFAULT_MODEL,
    )


@app.route("/run", methods=["POST"])
def run() -> str:
    brand = Brand.from_form(request.form)
    request_text = (request.form.get("request") or "").strip()

    data = None
    error = None
    if brand.is_empty():
        error = "請至少填寫品牌名稱、產業或主打產品，團隊才知道要為什麼品牌工作。"
    else:
        data = run_team(brand, request_text)

    return render_template(
        "team.html",
        brand=brand,
        request_text=request_text,
        data=data,
        error=error,
        specialists=SPECIALISTS,
        has_api_key=has_api_key(),
        model=DEFAULT_MODEL,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
