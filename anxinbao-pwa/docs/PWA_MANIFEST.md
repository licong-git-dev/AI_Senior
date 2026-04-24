# PWA Manifest 与图标资产指南

> [`public/manifest.json`](../public/manifest.json) 控制 PWA 安装到桌面后的外观、入口和能力。本指南记录关键决策和待补的图标资产。

## 当前 manifest 改动（r10）

| 字段 | v1 → v2 | 原因 |
|---|---|---|
| `start_url` | `/` → `/?source=pwa` | 用 query 标记 PWA 源流量，便于 GA / 漏斗分析 |
| `scope` | （空）→ `/` | 显式声明 PWA 作用域，防止外链跳出 PWA 容器 |
| `display_override` | （新）`["window-controls-overlay", "standalone", "browser"]` | 桌面 PWA 支持窗口控件叠加；不支持时降级 standalone |
| `orientation` | `portrait` → `portrait-primary` | 锁定竖屏（老人翻屏易误操作） |
| `background_color` | `#667eea` → `#1e1b4b` | 与 `StandbyScreen` 渐变深色调对齐，启动时不会 "白闪" |
| `theme_color` | `#667eea` → `#4f46e5` | 与设计系统主色一致 |
| `description` | 抽象语 → 卖点直陈（方言+健康+SOS+家庭） | 应用商店截取 description 做副标题 |
| `categories` | `[health, lifestyle]` → +`medical` | 帮助商店分类索引 |
| `prefer_related_applications` | （新）`false` | 显式说明"不推荐用户改装原生 App"，避免商店降权 |
| `icons` | 单一 `any maskable` → 拆为 `any` + `maskable` 两组 | iOS / Android 兼容；maskable 占整个图标方块（带 110% 安全区） |
| `shortcuts` | （新）3 个：SOS / 聊天 / 用药 | 长按桌面图标的快捷菜单 |

## 待制作的图标资产

⚠️ 当前 `public/` 缺以下文件，**未生成会让浏览器装机时显示默认占位图**：

| 文件名 | 尺寸 | purpose | 设计要求 |
|---|---|---|---|
| `icon-192.png` | 192×192 | any | 透明背景，留 ~12% 边距 |
| `icon-512.png` | 512×512 | any | 同上，高分辨率 |
| `icon-192-maskable.png` | 192×192 | maskable | 主体在中心 80% 区域内（Android 会裁圆/方/水滴等形状） |
| `icon-512-maskable.png` | 512×512 | maskable | 同上 |
| `apple-touch-icon.png` | 180×180 | iOS 桌面 | 不透明背景，无圆角（iOS 自动加） |

### 一键生成（推荐工具）

```bash
# 用 sharp-cli（最快）
npm i -g sharp-cli
sharp -i ./logo-source.png -o ./public/icon-512.png resize 512 512
sharp -i ./logo-source.png -o ./public/icon-192.png resize 192 192

# Maskable 版本：在 logo 外面留 64px 透明边距（512 * 12.5%）再缩放
# 或者用在线工具：https://maskable.app/editor
```

或者用 [`pwa-asset-generator`](https://github.com/onderceylan/pwa-asset-generator) 一键全套：

```bash
npx pwa-asset-generator ./logo.svg ./public \
  --background "#1e1b4b" \
  --padding "10%" \
  --icon-only
```

## index.html 配套（待加）

```html
<!-- iOS 安装支持 -->
<link rel="apple-touch-icon" href="/apple-touch-icon.png" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
<meta name="apple-mobile-web-app-title" content="安心宝" />

<!-- Android 主题色 -->
<meta name="theme-color" content="#4f46e5" />
<meta name="mobile-web-app-capable" content="yes" />

<!-- 加 manifest -->
<link rel="manifest" href="/manifest.json" />

<!-- 防止 iOS 缩放（适老化关键） -->
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover" />
```

## 适老化考量

老人安装 PWA 后的触点：

1. **桌面图标**：最大化（>= 84px）+ 高对比 + 单色不要太多文字
2. **闪屏色（splash）**：用 `background_color` 定义，老人盯屏 1-2 秒不会被刺眼
3. **快捷菜单**：3 个快捷入口足够（SOS 永远在第一个）
4. **不锁横屏**：老人手抖容易误转，`portrait-primary` 强制竖屏
5. **不允许缩放**：`maximum-scale=1` 避免老人捏合误触

## 验证清单

发布前用 Chrome DevTools → Application → Manifest 检查：

- [ ] manifest.json 加载无 404
- [ ] 所有 icons 路径可访问（200）
- [ ] `Add to Home Screen` 可见（说明 manifest 合规）
- [ ] Lighthouse PWA 分 ≥ 90
- [ ] Safari 真机安装测试（iOS 兼容是难点）
- [ ] 离线场景测试（结合 [sw.js v2](../public/sw.js)）

## 后续扩展

- [ ] 制作 splash screen 资产（iOS 必须，Android 可省）
- [ ] 加 `screenshots` 字段（应用商店推荐安装时显示，提高转化）
- [ ] 加 `share_target` 字段（让安心宝出现在系统分享菜单里，子女可分享日报到安心宝）
- [ ] 加 `protocol_handlers` 字段（支持 `web+anxinbao://` URL scheme）

---

> 任何修改 manifest 后，必须 bump [sw.js](../public/sw.js) 的 `CACHE_VERSION`，否则浏览器拿到旧的 manifest。
