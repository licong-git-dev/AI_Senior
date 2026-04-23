# GitHub Actions 工作流模板

> 本目录下的 `*.yml` 是**待启用**的工作流模板。GitHub PAT 必须包含 `workflow` scope 才能直接 push 到 `.github/workflows/`，本仓库当前 PAT 无此权限，因此暂存于此。

## 启用步骤（任选其一）

### 方式 A：更新 PAT scope（推荐）

1. 到 [GitHub Settings → Personal access tokens](https://github.com/settings/tokens)
2. 编辑当前在用的 token，勾选 `workflow` scope
3. 在仓库根执行：
   ```bash
   mkdir -p .github/workflows
   cp anxinbao-server/docs/ci/integration-self-check.yml .github/workflows/
   git add .github/workflows/integration-self-check.yml
   git commit -m "chore(ci): enable integration self-check workflow"
   git push
   ```

### 方式 B：通过 GitHub Web UI 创建

1. 仓库主页 → Actions tab → New workflow → Set up a workflow yourself
2. 将 [integration-self-check.yml](integration-self-check.yml) 内容粘贴进去
3. 文件名设为 `integration-self-check.yml`
4. Commit directly to main branch

## 工作流说明

### `integration-self-check.yml`

每次 PR 与 main push 触发，包含两个 job：

- **`inspect`**：信息性，打印 `python scripts/check_integrations.py` 的状态快照
- **`production-gate`**：双向守卫
  - 「缺凭据应被拦」：`DEBUG=false` 且无凭据时 `--strict` 必须退出非零，否则报错
  - 「齐凭据应通过」：注入完整 fixture 凭据后 `--strict` 必须退出 0

**为什么需要双向验证？** 单向验证（仅"缺凭据应失败"）很容易被"守卫从来没真在工作过"的 bug 欺骗 —— 守卫如果永远 exit 1（即使齐凭据），单向 CI 也会"通过"。双向验证才能锁死守卫不被绕过。

## 后续可加的工作流

- `tests.yml`：跑后端 pytest（参考 `anxinbao-server/.github/workflows/ci.yml` 中的 testing job）
- `frontend-build.yml`：跑前端 `npm run build && npm run lint`
- `release.yml`：tag 触发 docker image 构建
- `ultrareview.yml`：用 `oh-my-claudecode` 的 `/ultrareview` 自动 PR 评审

每个新工作流加进来同样需要 PAT 含 `workflow` scope，或经 web UI 创建。
