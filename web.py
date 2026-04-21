#!/usr/bin/env python3
"""Flask web UI for the e-commerce image generator."""
from __future__ import annotations

import os
import uuid
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file

from composer import LAYOUTS, THEMES, render
from copywriter import _fallback_copy, generate_copy

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB


@app.route("/")
def index() -> str:
    return render_template(
        "index.html",
        layouts=list(LAYOUTS),
        themes=list(THEMES),
        has_api_key=bool(os.environ.get("ANTHROPIC_API_KEY")),
    )


def _as_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


@app.route("/generate", methods=["POST"])
def generate():
    name = (request.form.get("name") or "").strip()
    if not name:
        return jsonify({"error": "請輸入商品名稱"}), 400

    price = _as_float(request.form.get("price"))
    discount_price = _as_float(request.form.get("discount_price"))
    tagline = (request.form.get("tagline") or "").strip() or None

    features_raw = request.form.get("features") or ""
    features = [line.strip() for line in features_raw.splitlines() if line.strip()]

    layout = request.form.get("layout", "square")
    theme = request.form.get("theme", "sunset")
    use_ai = request.form.get("use_ai") == "on"

    image_path: str | None = None
    upload = request.files.get("image")
    if upload and upload.filename:
        safe_name = f"{uuid.uuid4().hex}_{Path(upload.filename).name}"
        saved = UPLOAD_DIR / safe_name
        upload.save(saved)
        image_path = str(saved)

    product = {
        "name": name,
        "price": price,
        "discount_price": discount_price,
        "features": features,
        "image": image_path,
        "tagline": tagline,
    }

    if use_ai and os.environ.get("ANTHROPIC_API_KEY"):
        copy = generate_copy(product)
    else:
        copy = _fallback_copy(product)

    out_id = uuid.uuid4().hex
    output = OUTPUT_DIR / f"{out_id}.png"
    render(product, copy, layout=layout, theme=theme, output=str(output))

    return jsonify(
        {
            "image_url": f"/outputs/{out_id}.png",
            "download_url": f"/outputs/{out_id}.png?download=1",
            "copy": copy,
        }
    )


@app.route("/outputs/<filename>")
def outputs(filename: str):
    path = OUTPUT_DIR / filename
    if not path.exists() or not path.is_file():
        return ("Not Found", 404)
    as_attachment = request.args.get("download") == "1"
    return send_file(path, mimetype="image/png", as_attachment=as_attachment, download_name=filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
