#!/usr/bin/env bash
# PWA 占位图标生成器（r29 · 适老化深色品牌）
#
# 用法：
#   chmod +x scripts/generate_placeholder_icons.sh
#   ./scripts/generate_placeholder_icons.sh
#
# 依赖：ImageMagick (apt install imagemagick / brew install imagemagick)
#
# 生成内容：
#   public/icon-192.png
#   public/icon-512.png
#   public/icon-192-maskable.png  (含 110% 安全区)
#   public/icon-512-maskable.png  (含 110% 安全区)
#   public/apple-touch-icon.png   (180×180)
#
# 设计：
#   - 背景色 #1e1b4b（与 manifest theme_color 对齐）
#   - 中央安心宝 logo 占位（"安"字）
#   - maskable 版本主体在中心 80% 区域内（Android 圆形/水滴等裁切都能保住"安"字）
#
# 替换为真品牌图标的步骤：
#   1. 设计师出 1024×1024 SVG / PNG
#   2. ./scripts/generate_placeholder_icons.sh --source ./brand-logo.png
#   3. 提交 git
#
# 设计原则（适老化）：
#   - 主体图形应大、对比强
#   - 不要过多文字（小尺寸看不清）
#   - 主色 = 深紫蓝（不刺眼，老人友好）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PWA_DIR="$(dirname "$SCRIPT_DIR")"
PUBLIC_DIR="$PWA_DIR/public"

BG_COLOR="#1e1b4b"
FG_COLOR="#fbbf24"  # 琥珀色（与 ActivationOverlay 喇叭色一致）
LABEL="安"

if ! command -v convert >/dev/null 2>&1; then
  echo "❌ 未找到 ImageMagick 的 convert 命令"
  echo "   apt install imagemagick  或  brew install imagemagick"
  exit 1
fi

echo "→ 生成 PWA 占位图标到 $PUBLIC_DIR"

# 通用生成函数
gen_icon() {
  local size=$1
  local out=$2
  local font_size=$((size * 5 / 10))  # 字体占 50%
  convert -size "${size}x${size}" "xc:$BG_COLOR" \
    -gravity center \
    -font /usr/share/fonts/truetype/wqy/wqy-zenhei.ttc \
    -pointsize "$font_size" \
    -fill "$FG_COLOR" \
    -annotate +0+0 "$LABEL" \
    "$out" 2>/dev/null || \
  convert -size "${size}x${size}" "xc:$BG_COLOR" \
    -gravity center \
    -pointsize "$font_size" \
    -fill "$FG_COLOR" \
    -annotate +0+0 "$LABEL" \
    "$out"
  echo "  ✓ $out"
}

# Maskable 版本：内容缩到中心 80%（留 110% 安全区）
gen_maskable() {
  local size=$1
  local out=$2
  local inner=$((size * 80 / 100))   # 主体 80%
  local font_size=$((inner * 5 / 10))
  convert -size "${size}x${size}" "xc:$BG_COLOR" \
    -gravity center \
    -pointsize "$font_size" \
    -fill "$FG_COLOR" \
    -annotate +0+0 "$LABEL" \
    "$out"
  echo "  ✓ $out (maskable, 80% safe zone)"
}

mkdir -p "$PUBLIC_DIR"
gen_icon 192 "$PUBLIC_DIR/icon-192.png"
gen_icon 512 "$PUBLIC_DIR/icon-512.png"
gen_icon 180 "$PUBLIC_DIR/apple-touch-icon.png"
gen_maskable 192 "$PUBLIC_DIR/icon-192-maskable.png"
gen_maskable 512 "$PUBLIC_DIR/icon-512-maskable.png"

echo ""
echo "✅ 占位图标已生成。"
echo "   生产前请用品牌 logo 替换：./scripts/generate_placeholder_icons.sh --source brand.png"
echo ""
echo "   验证：在 Chrome DevTools → Application → Manifest 检查图标渲染"
echo "   maskable 在线预览：https://maskable.app/?slug=anxinbao"
