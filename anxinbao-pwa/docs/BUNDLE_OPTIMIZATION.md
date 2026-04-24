# 前端 Bundle 体积优化指南

> 目标：让老人在弱 4G / 老旧手机上 **3 秒内首屏**。每多 100KB 就让低端设备多等约 0.5 秒。
>
> 当前生产依赖 4 个（已剔除一个零使用的死重，详见下文）。

## 当前依赖审计

```
react           ^19.2  ~ 45 KB gzip   (框架，必需)
react-dom       ^19.2  ~ 50 KB gzip   (框架，必需)
lucide-react    ^0.562 ~ 0.5 KB/icon  (按需 tree-shake，9 个 import 文件)
date-fns        ^4.1   ~ 13 KB gzip   (按需 import，5 个文件用 format)
```

**总估算**：~110 KB gzip（含 React 运行时）。这是一个**健康的 PWA 体积**，老人手机首屏 < 2 秒。

## 历史死重（已清理）

### ❌ recharts（已移除 r9）

`recharts ^3.6.0` 历史在 package.json 但 **src/ 零引用**（grep 验证）。HealthTrendsPage 中的 `BarChart` 是本地自定义组件，不是 recharts 的。

未引用却被 `npm install` —— 部分 bundler 仍可能因 transitive deps 把它推进 chunk。已在 r9 直接从 dependencies 移除，节省 ~400 KB（gzip 后 ~120 KB）。

如未来真要画图：
- **首选**：自定义轻量 SVG（已在 HealthTrendsPage 用此方案）
- **复杂场景**：按需引 `recharts/es6/chart/LineChart` 而非 `recharts` 整包
- **Vue 风格**：`uPlot`（17 KB）或 `chart.xkcd`（30 KB）

## 静态审计：识别浪费的 import 模式

### 1. 整包 import 检查

```bash
cd anxinbao-pwa
# 找"整包 import"（应该按需 import 的库）
grep -rEn "import \* as|import \{ \* \}" src/ | grep -v node_modules

# 找 recharts / lodash / moment 等已知大库的整包引用
grep -rEn "from 'recharts'|from 'lodash'|from 'moment'" src/
```

### 2. 重复依赖检查

```bash
# 跑 npm dedupe（不增加体积，但合并重复版本）
npm dedupe

# 输出已知冲突
npx depcheck                # 检测未使用的依赖
```

### 3. 真实 bundle 分析（需 npm install + build）

```bash
# 方案 A：rollup-plugin-visualizer（vite 兼容）
npm i -D rollup-plugin-visualizer
# 在 vite.config.ts 加：
#   import { visualizer } from 'rollup-plugin-visualizer';
#   plugins: [react(), visualizer({ open: true, gzipSize: true })]
npm run build
# dist/ 会自动打开 stats.html

# 方案 B：vite-bundle-visualizer 一行命令
npx vite-bundle-visualizer

# 方案 C：source-map-explorer（最经典）
npm i -D source-map-explorer
npm run build
npx source-map-explorer 'dist/assets/*.js'
```

**当前场景**（服务器低内存）：先不做。等到上线前在本地 / CI 跑一次。

## 减重清单（按 ROI 排序）

| 优化 | 收益 | 成本 |
|---|---|---|
| 1. 移除 recharts（已做） | -120 KB gzip | 0 |
| 2. lucide-react 改 tree-shake import | -5~20 KB | S（已是 named import，确认即可） |
| 3. date-fns 替换为 dayjs | -10 KB | M（5 处 format 都要改） |
| 4. 拆 chunk：vendor / page | 不减总量但分摊加载 | M（vite.config.ts 配 manualChunks） |
| 5. 图片改 WebP | -30~50% 图片体积 | S（手动转 + sw.js 增 webp 缓存） |
| 6. preload 关键 page | TTI 提升 30%+ | M（per-route prefetch） |
| 7. 启用 brotli 压缩（nginx 层） | -15% on top of gzip | S（nginx.conf 配置） |

## 适老化场景下的优先级

老人设备特点：
- 屏幕大但 DPR 通常 1.5~2（不是 3）
- 内存 4GB / 6GB（不是 12GB）
- 4G 网络居多，5G 覆盖差
- 偶尔在地下停车场 / 电梯里失联

**最关键**：
- ✅ 首屏 SSR 友好（PWA 已是 SPA，做好 service worker 离线兜底）
- ✅ 图片懒加载（已做）
- ✅ 字体子集化（中文字体一定要做）
- ⚠️ JS chunk 分页 lazy load（当前是单个 bundle，可优化）

## 字体子集化（中文专属优化）

中文 web font 整包 ~15MB，但老人界面常用字符不超过 3000 个。

```bash
# 用 fontmin 子集化
npm i -D fontmin
node -e "
const Fontmin = require('fontmin');
new Fontmin()
  .src('public/fonts/SourceHanSans.ttf')
  .dest('public/fonts/')
  .use(Fontmin.glyph({
    text: '常用 3000 字符...这里建议从 src/ 中静态扫所有中文字符的并集'
  }))
  .run();
"
```

或者直接用 [字蛛 / font-spider](https://github.com/aui/font-spider) 自动从 HTML/CSS 扫字符。

## 监控线上真实体积

发布后定期 (1次/月) 检查：
```bash
# 用 Chrome DevTools - Network 看 transfer / resource 大小
# 用 Lighthouse 生成性能报告
npx lighthouse https://your-prod-url.com --view
```

阈值告警：
- Bundle gzip > 200 KB → ⚠️ 检查
- LCP > 2.5s → ⚠️ 优化
- TTI > 3.8s → ⚠️ 优化（适老化要 < 3s）

## 与 service worker 配合

[`sw.js`](../public/sw.js) v2 的 `MAX_CACHE_ITEMS=60` 与 stale-while-revalidate 策略已经针对小内存设备做了优化。bundle 减小后老人设备的缓存压力进一步降低。

---

> 任何新依赖加入 [package.json](../package.json) 前，请先回答：
>
> 1. 真的没有更轻量的替代吗？
> 2. 能 tree-shake 吗（`import { x } from 'lib'` 而非 `import lib`）？
> 3. 估算 gzip 后 +KB，超 20 KB 必须有强烈理由？
