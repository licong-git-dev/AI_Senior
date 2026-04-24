#!/bin/bash
# 依赖安全审计（SCA · Software Composition Analysis）
#
# 用途：扫描 requirements.txt 中已知的 CVE 漏洞，杜绝把"已知有漏洞的依赖"带上生产。
#
# 工具优先级：pip-audit (PyPA 官方) > safety (Pyup) > 无
# 任一可用即可；都没装会给出安装指引并以非零退出码失败。
#
# 用法：
#   bash scripts/security_audit.sh           # 普通输出
#   bash scripts/security_audit.sh --json    # JSON 输出（CI 解析用）
#
# 性能：纯静态扫描，不联网下载真实包，**对低内存机器友好**。
# 离线场景：pip-audit 默认连接 PyPI advisory DB，可加 --offline + 本地 db 文件
#          （超出本脚本范围，常规网络不需关心）。

set -e

cd "$(dirname "$0")/.."

JSON=false
if [[ "$1" == "--json" ]]; then
    JSON=true
fi

echo "===== 依赖安全审计（SCA）====="
echo "目标：anxinbao-server/requirements.txt"
echo ""

if command -v pip-audit >/dev/null 2>&1; then
    echo "→ 使用 pip-audit"
    if [[ "$JSON" == "true" ]]; then
        pip-audit -r requirements.txt --format json
    else
        pip-audit -r requirements.txt --desc
    fi
elif command -v safety >/dev/null 2>&1; then
    echo "→ 使用 safety"
    if [[ "$JSON" == "true" ]]; then
        safety check -r requirements.txt --json
    else
        safety check -r requirements.txt
    fi
else
    cat <<'EOF'
⚠️  未检测到 pip-audit 或 safety。

请安装其一：
  pip install pip-audit             # 推荐（PyPA 官方）
  pip install safety                # 备选

然后重新运行本脚本。

如果环境受限无法装额外工具，可以手动比对：
  https://github.com/advisories?query=pypi%3A<package-name>
  https://osv.dev/list?ecosystem=PyPI

CI 中使用 .github/workflows/integration-self-check.yml 可加这一步：
  - run: pip install pip-audit && pip-audit -r anxinbao-server/requirements.txt
EOF
    exit 1
fi
