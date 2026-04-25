#!/bin/bash
# 一键将 backend/ 同步到 HF Space 并部署
# 用法：./deploy-backend.sh "修改说明"

set -e

BACKEND_SRC="$(dirname "$0")/backend"
HF_REPO="$(dirname "$0")/../xingu-tool-api"
COMMIT_MSG="${1:-update backend}"

echo "🔄 同步 backend/ → xingu-tool-api/ ..."
rsync -av \
  --exclude='venv/' \
  --exclude='__pycache__/' \
  --exclude='*.db' \
  --exclude='.env' \
  --exclude='*.pyc' \
  "$BACKEND_SRC/" "$HF_REPO/"

echo "📦 提交并推送到 Hugging Face ..."
cd "$HF_REPO"
git add .
git commit --no-verify -m "$COMMIT_MSG" || echo "⚠️  没有新变更，跳过 commit"
git push

echo "✅ 部署完成！"
echo "🌐 查看状态：https://huggingface.co/spaces/youzi530/xingu-tool-api"
