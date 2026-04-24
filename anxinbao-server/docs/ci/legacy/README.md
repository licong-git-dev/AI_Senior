# Legacy CI Templates（历史拆分前的工作流）

本目录的 `*.yml.template` 是 anxinbao-server 作为**独立仓库**时的 GitHub Actions 工作流。

## 为什么搬到这里

GitHub Actions 工作流必须放在 **仓库根** 的 `.github/workflows/` 才会被识别。当前仓库布局：

```
AI_Senior/                       ← 仓库根
├── .github/workflows/           ← 这里才生效
├── anxinbao-server/
│   └── .github/workflows/       ← 在 monorepo 下不生效
└── anxinbao-pwa/
```

之前 `anxinbao-server/.github/workflows/` 下的工作流**从未真正运行过**（误以为有 CI 实际却没有），是潜在的"我以为有人守门，其实没有"的伪 ✅。

## 怎么启用

### 方式 A：把后端单独切成独立仓库（推荐长期）
- `git subtree split --prefix=anxinbao-server -b backend-only`
- 推到独立 `anxinbao-server` 仓库
- 在那里 `mv docs/ci/legacy/ci.yml.template .github/workflows/ci.yml`

### 方式 B：在 monorepo 下集成进根目录工作流
- 把 `ci.yml.template` 内容合并到 [`/.github/workflows/integration-self-check.yml`](../integration-self-check.yml)
  （需要把所有 `working-directory` 设为 `anxinbao-server`）
- 删除本目录

### 方式 C：保留为参考
- 适合现状：仓库还在演化中，等业务稳定再决定 A/B
- 至少不再让人误以为它在跑

## 文件清单

- `ci.yml.template` — 单元测试 + 覆盖率，跑 pytest
- `ci-cd.yml.template` — 构建 docker 镜像、自动部署
