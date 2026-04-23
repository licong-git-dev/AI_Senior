#!/usr/bin/env python3
"""
集成真实性自检脚本（离线，**不启动 FastAPI 服务**，对低内存机器友好）。

用途：
    填好 .env 后运行此脚本，逐项检查每个第三方集成是 real / placeholder /
    missing / weak。production_ready=False 时打印"上线前必须解决"清单。

用法：
    cd anxinbao-server
    python scripts/check_integrations.py            # 普通检查
    python scripts/check_integrations.py --json     # 输出 JSON（便于 CI 解析）
    python scripts/check_integrations.py --strict   # production_ready 失败时退出码非 0

设计原则（与 GET /health/integrations 端点一致）：
- 仅读取 Settings 与环境变量，不发起网络请求，不连接数据库；
- 与 main.py 中的 _classify / integrations_health 逻辑保持一致；
- 暴露"凭据缺失静默走入 mock"的潜在生产事故。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# 让脚本可以从 anxinbao-server/ 直接运行（添加项目根到 sys.path）
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.core.config import get_settings  # noqa: E402

_PLACEHOLDER_HINTS = ("test_", "your_", "xxx", "changeme", "placeholder", "example", "please-replace")


def classify(value: str | None) -> str:
    if not value:
        return "missing"
    v = str(value).strip().lower()
    if not v:
        return "missing"
    if any(h in v for h in _PLACEHOLDER_HINTS):
        return "placeholder"
    return "real"


def collect():
    s = get_settings()

    checks = [
        ("dashscope_qwen", classify(getattr(s, "dashscope_api_key", "")),
         "通义千问 AI 对话"),
        ("xfyun_asr_tts",
         classify(
             (getattr(s, "xfyun_appid", "") or "")
             and (getattr(s, "xfyun_api_key", "") or "")
             and (getattr(s, "xfyun_api_secret", "") or "")
         ),
         "讯飞语音识别/合成（含方言）"),
        ("aliyun_sms",
         classify(getattr(s, "aliyun_access_key_id", "")),
         "阿里云短信（健康告警 / SOS 紧急通知）"),
        ("sms_template_emergency",
         classify(getattr(s, "sms_template_emergency", "")),
         "SOS 紧急短信模板（缺失则 SOS 通知发不出去）"),
        ("jpush",
         classify(getattr(s, "jpush_app_key", "")),
         "极光推送"),
        ("alipay",
         classify(getattr(s, "alipay_app_id", "")),
         "支付宝（订阅付费）"),
        ("encryption_key",
         classify(getattr(s, "encryption_key", "")),
         "敏感数据加密密钥"),
        ("jwt_secret",
         "real" if (
             getattr(s, "jwt_secret_key", "")
             and len(str(s.jwt_secret_key)) >= 32
             and classify(s.jwt_secret_key) == "real"
         ) else "weak",
         "JWT 签名密钥"),
    ]

    critical = {"aliyun_sms", "sms_template_emergency", "alipay", "encryption_key", "jwt_secret"}
    rows = []
    critical_missing = []
    for name, status, desc in checks:
        production_ready = status == "real"
        rows.append({
            "name": name,
            "description": desc,
            "status": status,
            "production_ready": production_ready,
        })
        if name in critical and not production_ready:
            critical_missing.append(name)

    return {
        "service": "anxinbao-server",
        "production_ready": len(critical_missing) == 0,
        "critical_missing": critical_missing,
        "integrations": rows,
    }


_ICONS = {
    "real": "🟢",
    "placeholder": "🟡",
    "missing": "🔴",
    "weak": "🔴",
}


def print_human(report: dict) -> None:
    print()
    print("======== 安心宝集成真实性自检 ========")
    print(f"  service           : {report['service']}")
    print(f"  production_ready  : {report['production_ready']}")
    print()
    print(f"  {'状态':<6}{'集成':<28}{'说明'}")
    print("  " + "-" * 70)
    for row in report["integrations"]:
        icon = _ICONS.get(row["status"], "⚪")
        print(f"  {icon}    {row['name']:<28}{row['description']}  [{row['status']}]")
    print()
    if report["critical_missing"]:
        print("⚠️  上线前必须解决（critical_missing）:")
        for n in report["critical_missing"]:
            print(f"   - {n}")
        print()
    else:
        print("✅ 关键链路全部 real，可以进入预发布。")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description="离线集成自检（不启动 FastAPI）")
    parser.add_argument("--json", action="store_true", help="输出 JSON 而非可读表格")
    parser.add_argument("--strict", action="store_true",
                        help="critical_missing 非空时以非零退出码结束（CI 用）")
    args = parser.parse_args()

    # 确保从 .env 加载
    os.chdir(ROOT)
    report = collect()

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_human(report)

    if args.strict and not report["production_ready"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
