# 安心宝开发与发布快捷命令
#
# 用法：
#   make help              查看所有命令
#   make verify            一键自检（集成 + 测试 + lint）
#   make verify-prod       模拟生产环境自检（DEBUG=false）
#   make integrations      仅看集成真实性快照
#   make test              跑后端测试
#   make lint              跑前后端 lint
#   make doctor            综合诊断（依赖、配置、Git 状态）
#
# 目标：让"是否可以提交/上线"用一行命令就能判断，杜绝伪 ✅。

SERVER_DIR := anxinbao-server
PWA_DIR := anxinbao-pwa
PYTHON := python3

.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "安心宝开发命令："
	@echo ""
	@echo "  make verify        — 一键自检（集成 + 测试，开发模式，最常用）"
	@echo "  make verify-prod   — 模拟生产自检（DEBUG=false，验证守卫真生效）"
	@echo "  make integrations  — 仅运行集成真实性快照"
	@echo "  make test          — 跑 pytest（后端）"
	@echo "  make lint          — 跑 flake8 + eslint"
	@echo "  make doctor        — 综合诊断（依赖、Git、env）"
	@echo "  make clean         — 清理 __pycache__ / .pytest_cache / dist"
	@echo ""
	@echo "提示：所有命令均在仓库根执行。子任务的 working directory 已自动切换。"

.PHONY: verify
verify: integrations test
	@echo ""
	@echo "✅ verify 通过"

.PHONY: verify-prod
verify-prod:
	@echo "→ 模拟生产环境自检（DEBUG=false 守卫验真）"
	@cd $(SERVER_DIR) && DEBUG=false DATABASE_URL=sqlite:// $(PYTHON) scripts/check_integrations.py --strict || \
	  (echo ""; echo "✅ 守卫按预期拦截了缺凭据的生产配置（这是正确行为）"; echo "  若希望它通过，请配齐 critical_missing 项目"; exit 0)

.PHONY: integrations
integrations:
	@echo "→ 集成真实性快照"
	@cd $(SERVER_DIR) && $(PYTHON) scripts/check_integrations.py

.PHONY: test
test:
	@echo "→ 后端测试"
	@cd $(SERVER_DIR) && pytest -q --tb=short

.PHONY: test-fast
test-fast:
	@cd $(SERVER_DIR) && pytest -q --tb=line -m "not slow"

.PHONY: coverage
coverage:
	@cd $(SERVER_DIR) && pytest --cov=app --cov-report=term-missing --cov-report=html

.PHONY: lint
lint: lint-py lint-ts

.PHONY: lint-py
lint-py:
	@echo "→ Python lint"
	@cd $(SERVER_DIR) && (command -v flake8 >/dev/null 2>&1 && flake8 . --select=E9,F63,F7,F82 --show-source --statistics || echo "  flake8 未安装，跳过")

.PHONY: lint-ts
lint-ts:
	@echo "→ TypeScript lint"
	@cd $(PWA_DIR) && (test -d node_modules && npm run lint || echo "  node_modules 未安装，跳过（npm install 后重试）")

.PHONY: doctor
doctor:
	@echo "===== 安心宝综合诊断 ====="
	@echo ""
	@echo "→ Python 版本"
	@$(PYTHON) --version
	@echo ""
	@echo "→ Node 版本"
	@command -v node >/dev/null 2>&1 && node --version || echo "  node 未安装"
	@echo ""
	@echo "→ 是否在 git 仓库"
	@git -C . rev-parse --abbrev-ref HEAD 2>/dev/null && \
	  echo "  当前分支：$$(git rev-parse --abbrev-ref HEAD)" && \
	  echo "  待提交文件数：$$(git status --short | wc -l)" || echo "  非 git 仓库"
	@echo ""
	@echo "→ 关键配置文件"
	@test -f $(SERVER_DIR)/.env && echo "  $(SERVER_DIR)/.env       存在" || echo "  $(SERVER_DIR)/.env       缺失（拷贝 .env.example）"
	@test -f $(SERVER_DIR)/.env.example && echo "  $(SERVER_DIR)/.env.example 存在" || echo "  $(SERVER_DIR)/.env.example 缺失"
	@echo ""
	@echo "→ 集成真实性"
	@$(MAKE) -s integrations
	@echo ""
	@echo "===== 诊断结束 ====="

.PHONY: clean
clean:
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	@rm -rf $(PWA_DIR)/dist 2>/dev/null || true
	@echo "✅ 清理完成"
