"""
安心宝数据库种子脚本
用于初始化演示数据

使用方法:
  python scripts/seed_data.py

注意: 此脚本会清空现有数据，请谨慎使用！
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
import random

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# 假设有这些模型
# from app.models import User, Device, HealthRecord, Medication, Alert, EmergencyContact, FamilyRelation

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """哈希密码"""
    return pwd_context.hash(password)


# 演示用户数据
DEMO_USERS = [
    {
        "phone": "13800138001",
        "password": "123456",
        "name": "张大爷",
        "role": "elderly",
        "avatar": None
    },
    {
        "phone": "13800138002",
        "password": "123456",
        "name": "李奶奶",
        "role": "elderly",
        "avatar": None
    },
    {
        "phone": "13800138003",
        "password": "123456",
        "name": "王先生",
        "role": "family",
        "avatar": None
    },
    {
        "phone": "13800138004",
        "password": "123456",
        "name": "陈女士",
        "role": "family",
        "avatar": None
    },
    {
        "phone": "13800138000",
        "password": "admin123",
        "name": "管理员",
        "role": "admin",
        "avatar": None
    }
]

# 演示设备数据
DEMO_DEVICES = [
    {
        "device_id": "WATCH_001",
        "device_type": "watch",
        "name": "智能手表A1",
        "model": "安心宝 A1",
        "status": "online",
        "battery": 85,
        "user_index": 0  # 对应张大爷
    },
    {
        "device_id": "BP_001",
        "device_type": "bp_monitor",
        "name": "血压仪B1",
        "model": "安心宝 B1",
        "status": "online",
        "battery": 92,
        "user_index": 0
    },
    {
        "device_id": "WATCH_002",
        "device_type": "watch",
        "name": "智能手表A1",
        "model": "安心宝 A1",
        "status": "offline",
        "battery": 15,
        "user_index": 1  # 对应李奶奶
    },
    {
        "device_id": "BS_001",
        "device_type": "glucose_meter",
        "name": "血糖仪G1",
        "model": "安心宝 G1",
        "status": "online",
        "battery": 78,
        "user_index": 1
    }
]

# 演示用药数据
DEMO_MEDICATIONS = [
    {
        "name": "阿司匹林",
        "dosage": "100mg",
        "frequency": "每日一次",
        "reminder_times": ["08:00"],
        "notes": "饭后服用",
        "user_index": 0
    },
    {
        "name": "降压药",
        "dosage": "10mg",
        "frequency": "每日两次",
        "reminder_times": ["08:00", "20:00"],
        "notes": "按时服用，不可漏服",
        "user_index": 0
    },
    {
        "name": "钙片",
        "dosage": "500mg",
        "frequency": "每日一次",
        "reminder_times": ["09:00"],
        "notes": "饭后半小时服用",
        "user_index": 1
    },
    {
        "name": "二甲双胍",
        "dosage": "500mg",
        "frequency": "每日三次",
        "reminder_times": ["07:30", "12:00", "18:00"],
        "notes": "餐前服用",
        "user_index": 1
    }
]

# 演示紧急联系人
DEMO_EMERGENCY_CONTACTS = [
    {
        "name": "张明",
        "phone": "13900139001",
        "relation": "儿子",
        "priority": 1,
        "user_index": 0
    },
    {
        "name": "张芳",
        "phone": "13900139002",
        "relation": "女儿",
        "priority": 2,
        "user_index": 0
    },
    {
        "name": "李华",
        "phone": "13900139003",
        "relation": "儿子",
        "priority": 1,
        "user_index": 1
    }
]


def generate_health_records(user_id: int, days: int = 30):
    """生成健康记录数据"""
    records = []
    now = datetime.now()

    for i in range(days):
        record_date = now - timedelta(days=i)

        # 血压记录（每天2次）
        for hour in [8, 20]:
            systolic = random.randint(115, 145)
            diastolic = random.randint(70, 95)
            records.append({
                "user_id": user_id,
                "record_type": "bp",
                "value": f"{systolic}/{diastolic}",
                "unit": "mmHg",
                "measured_at": record_date.replace(hour=hour, minute=random.randint(0, 30)),
                "notes": "自动同步" if random.random() > 0.3 else None
            })

        # 心率记录（每天3次）
        for hour in [8, 14, 20]:
            records.append({
                "user_id": user_id,
                "record_type": "hr",
                "value": str(random.randint(60, 95)),
                "unit": "bpm",
                "measured_at": record_date.replace(hour=hour, minute=random.randint(0, 30)),
                "notes": None
            })

        # 血糖记录（每天2次）
        if random.random() > 0.3:  # 70%概率有血糖记录
            # 空腹血糖
            records.append({
                "user_id": user_id,
                "record_type": "bs",
                "value": f"{random.uniform(4.5, 7.0):.1f}",
                "unit": "mmol/L",
                "measured_at": record_date.replace(hour=7, minute=random.randint(0, 30)),
                "notes": "空腹"
            })
            # 餐后血糖
            records.append({
                "user_id": user_id,
                "record_type": "bs",
                "value": f"{random.uniform(6.0, 10.0):.1f}",
                "unit": "mmol/L",
                "measured_at": record_date.replace(hour=10, minute=random.randint(0, 30)),
                "notes": "餐后2小时"
            })

    return records


def generate_alerts(user_id: int, count: int = 10):
    """生成告警数据"""
    alerts = []
    now = datetime.now()

    alert_types = [
        {"type": "health", "level": "medium", "title": "血压偏高提醒", "content": "您的血压读数145/95mmHg，略高于正常范围，建议休息后再测量。"},
        {"type": "health", "level": "high", "title": "心率异常告警", "content": "检测到心率过速（105次/分），请保持静止状态，如持续异常请就医。"},
        {"type": "device", "level": "low", "title": "设备电量不足", "content": "您的智能手表电量仅剩15%，请及时充电。"},
        {"type": "device", "level": "medium", "title": "设备离线提醒", "content": "血压仪已离线超过2小时，请检查设备状态。"},
        {"type": "medication", "level": "medium", "title": "用药提醒", "content": "该服用降压药了，请记得按时服药。"},
        {"type": "sos", "level": "critical", "title": "紧急求助", "content": "用户触发了SOS紧急求助！"},
    ]

    statuses = ["pending", "handling", "resolved", "resolved", "resolved"]

    for i in range(count):
        alert_info = random.choice(alert_types)
        created = now - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
        status = random.choice(statuses)

        alerts.append({
            "user_id": user_id,
            "alert_type": alert_info["type"],
            "level": alert_info["level"],
            "title": alert_info["title"],
            "content": alert_info["content"],
            "status": status,
            "created_at": created,
            "handled_at": created + timedelta(minutes=random.randint(5, 60)) if status in ["handling", "resolved"] else None
        })

    return alerts


def seed_database():
    """执行数据库种子"""
    print("=" * 50)
    print("安心宝数据库种子脚本")
    print("=" * 50)

    # 这里应该使用实际的数据库连接和模型
    # 以下为示例代码结构

    print("\n[1/6] 创建演示用户...")
    for user in DEMO_USERS:
        user_data = {
            **user,
            "password_hash": hash_password(user["password"]),
            "status": "active",
            "created_at": datetime.now()
        }
        del user_data["password"]
        print(f"  - 创建用户: {user['name']} ({user['phone']})")

    print("\n[2/6] 创建演示设备...")
    for device in DEMO_DEVICES:
        print(f"  - 创建设备: {device['name']} ({device['device_id']})")

    print("\n[3/6] 创建用药提醒...")
    for med in DEMO_MEDICATIONS:
        print(f"  - 创建用药: {med['name']} - {med['dosage']}")

    print("\n[4/6] 创建紧急联系人...")
    for contact in DEMO_EMERGENCY_CONTACTS:
        print(f"  - 创建联系人: {contact['name']} ({contact['relation']})")

    print("\n[5/6] 生成健康记录...")
    for i, user in enumerate(DEMO_USERS[:2]):  # 只为老人用户生成
        records = generate_health_records(i + 1, 30)
        print(f"  - 为 {user['name']} 生成 {len(records)} 条健康记录")

    print("\n[6/6] 生成告警记录...")
    for i, user in enumerate(DEMO_USERS[:2]):
        alerts = generate_alerts(i + 1, 10)
        print(f"  - 为 {user['name']} 生成 {len(alerts)} 条告警记录")

    print("\n" + "=" * 50)
    print("数据库种子完成！")
    print("=" * 50)
    print("\n演示账号信息:")
    print("-" * 50)
    print(f"管理员: 13800138000 / admin123")
    print(f"老人端: 13800138001 / 123456 (张大爷)")
    print(f"老人端: 13800138002 / 123456 (李奶奶)")
    print(f"家属端: 13800138003 / 123456 (王先生)")
    print(f"家属端: 13800138004 / 123456 (陈女士)")
    print("-" * 50)


if __name__ == "__main__":
    seed_database()
