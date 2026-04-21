# 電商圖文產生器 (E-commerce Image Generator)

以 Python + Pillow 合成電商促銷圖，搭配 Claude API 自動產生繁中行銷文案。

## 功能

- **圖片合成**：1080x1080 社群方形貼文、1200x628 橫幅 Banner
- **AI 文案**：呼叫 Claude API 自動生成標語、亮點、CTA、徽章
- **離線模式**：無 API Key 時自動 fallback 到模板文案
- **三種主題配色**：sunset（橘紅）、ocean（藍色）、mono（黑白）
- **折扣標示**：原價劃線 + 折扣價強調
- **繁中字體**：內建使用 WenQuanYi Zen Hei

## 安裝

```bash
pip install -r requirements.txt
```

需要系統安裝中文字型 `wqy-zenhei`（Debian/Ubuntu 可以 `apt install fonts-wqy-zenhei`）。若使用其他字型，修改 `composer.py` 的 `FONT_PATH`。

## 使用方式

### 方式 0：網頁介面（推薦）

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # 可選，沒設定會用模板文案
python3 web.py
```

在瀏覽器打開 <http://localhost:5000>，填寫表單、上傳商品圖，即可即時預覽並下載 PNG。

### 方式 1：以 JSON 檔傳入商品資料

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python3 ecom_gen.py --product-json examples/sample_product.json -o out.png
```

商品 JSON 格式：

```json
{
  "name": "極簡無線降噪耳機 Pro",
  "price": 4990,
  "discount_price": 3690,
  "features": ["40小時超長續航", "主動降噪 -42dB", "Hi-Res 無損音質"],
  "image": "examples/placeholder.png"
}
```

### 方式 2：以命令列參數傳入

```bash
python3 ecom_gen.py \
  --name "極簡無線降噪耳機 Pro" \
  --price 4990 --discount-price 3690 \
  --features "40小時續航" "主動降噪" "Hi-Res 音質" \
  --image examples/placeholder.png \
  --layout banner --theme ocean \
  -o banner.png
```

### 離線模式（無 Claude API）

```bash
python3 ecom_gen.py --product-json examples/sample_product.json --no-ai -o out.png
```

## 參數

| 參數 | 說明 |
|------|------|
| `--product-json` | 商品 JSON 檔路徑 |
| `--name` / `--price` / `--discount-price` | 商品基本資料 |
| `--features` | 賣點列表（空白分隔） |
| `--image` | 商品圖路徑（建議透明背景 PNG） |
| `--tagline` | 自訂標語（覆寫 AI 輸出） |
| `--layout` | `square` (1080x1080) 或 `banner` (1200x628) |
| `--theme` | `sunset` / `ocean` / `mono` |
| `--output`, `-o` | 輸出 PNG 路徑 |
| `--no-ai` | 跳過 Claude API |
| `--model` | Claude 模型，預設 `claude-sonnet-4-6` |
| `--copy-out` | 另存產生的文案 JSON |

## 專案結構

```
.
├── ecom_gen.py              # CLI 進入點
├── web.py                   # Flask 網頁介面
├── copywriter.py            # Claude API 文案生成
├── composer.py              # PIL 圖片合成（版型、主題）
├── templates/index.html     # 網頁表單
├── static/style.css         # 網頁樣式
├── requirements.txt
└── examples/
    ├── sample_product.json
    ├── make_placeholder.py  # 產生測試用商品圖
    └── placeholder.png
```

## 延伸方向

- 新增其他版型（如 1080x1920 直式限動、960x960 EDM）
- 加入多商品拼貼（2x2 格、輪播卡片）
- 整合外部 AI 圖像生成（DALL·E、SD）產出商品情境圖
- 包裝成 FastAPI 服務，前端上傳圖片即時預覽
