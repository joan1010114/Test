#!/usr/bin/env bash
# 每週自動產出一波行銷物料（週報 + 貼文圖）。
# 掛 cron 用，請改成你自己的路徑與品牌檔。
set -euo pipefail

# --- 設定 -------------------------------------------------------------------
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BRAND="${BRAND:-brands/hanfresh.json}"
REQUEST="${REQUEST:-這週主推泡菜，幫我準備一波完整行銷}"
# 要真實 AI 內容，請在執行環境設好 ANTHROPIC_API_KEY（沒設會走離線套版）
# export ANTHROPIC_API_KEY=sk-ant-...
# export ANTHROPIC_MODEL=claude-sonnet-4-6   # 可選，省成本

cd "$PROJECT_DIR"
python3 team_run.py --brand "$BRAND" --request "$REQUEST" --theme sunset

echo "完成：$(date '+%F %T')  輸出在 marketing_runs/$(date +%F)/"
