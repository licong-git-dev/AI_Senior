"""
用药管理系统服务
提供用药提醒、药物相互作用检查、处方管理、库存提醒等功能
"""
import logging
import secrets
from typing import Optional, Dict, List, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta, time
from collections import defaultdict

logger = logging.getLogger(__name__)


# ==================== 药物基础信息 ====================

class MedicationType(Enum):
    """药物类型"""
    TABLET = 'tablet'  # 片剂
    CAPSULE = 'capsule'  # 胶囊
    LIQUID = 'liquid'  # 液体
    INJECTION = 'injection'  # 注射
    PATCH = 'patch'  # 贴剂
    DROPS = 'drops'  # 滴剂
    POWDER = 'powder'  # 粉剂
    OINTMENT = "ointment"  # 软膏


class MedicationFrequency(Enum):
    """服药频率"""
    ONCE_DAILY = 'once_daily'  # 每日一次
    TWICE_DAILY = "twice_daily"  # 每日两次
    THREE_TIMES = "three_times"  # 每日三次
    FOUR_TIMES = 'four_times'  # 每日四次
    AS_NEEDED = 'as_needed'  # 按需
    WEEKLY = "weekly"  # 每周
    ALTERNATE_DAYS = "alternate_days"  # 隔日


class MealRelation(Enum):
    """与餐关系"""
    BEFORE_MEAL = "before_meal"  # 饭前
    AFTER_MEAL = 'after_meal'  # 饭后
    WITH_MEAL = "with_meal"  # 随餐
    EMPTY_STOMACH = "empty_stomach"  # 空腹
    ANY_TIME = 'any_time'  # 任意时间
    BEDTIME = "bedtime"  # 睡前


class InteractionSeverity(Enum):
    """相互作用严重程度"""
    MILD = 'mild'  # 轻微
    MODERATE = 'moderate'  # 中等
    SEVERE = "severe"  # 严重
    CONTRAINDICATED = "contraindicated"  # 禁忌


@dataclass
class Medication:
    """药物信息"""
    medication_id: str
    name: str
    generic_name: str  # 通用名
    medication_type: MedicationType
    dosage: str  # 剂量规格
    manufacturer: Optional[str] = None
    description: Optional[str] = None
    side_effects: List[str] = field(default_factory=list)
    contraindications: List[str] = field(default_factory=list)
    storage_instructions: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "medication_id": self.medication_id,
            'name': self.name,
            "generic_name": self.generic_name,
            "medication_type": self.medication_type.value,
            'dosage': self.dosage,
            "manufacturer": self.manufacturer,
            "description": self.description,
            "side_effects": self.side_effects,
            "contraindications": self.contraindications,
            "storage_instructions": self.storage_instructions
        }


@dataclass
class DrugInteraction:
    """药物相互作用"""
    drug1: str
    drug2: str
    severity: InteractionSeverity
    description: str
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'drug1': self.drug1,
            'drug2': self.drug2,
            'severity': self.severity.value,
            "description": self.description,
            "recommendation": self.recommendation
        }


# ==================== 用药计划与记录 ====================

@dataclass
class MedicationSchedule:
    """用药计划"""
    schedule_id: str
    user_id: int
    medication_id: str
    medication_name: str
    dosage_amount: str  # 每次服用量
    frequency: MedicationFrequency
    meal_relation: MealRelation
    scheduled_times: List[str]  # HH:MM 格式
    start_date: datetime
    end_date: Optional[datetime] = None
    special_instructions: Optional[str] = None
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schedule_id": self.schedule_id,
            "medication_id": self.medication_id,
            "medication_name": self.medication_name,
            "dosage_amount": self.dosage_amount,
            'frequency': self.frequency.value,
            "meal_relation": self.meal_relation.value,
            "scheduled_times": self.scheduled_times,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat() if self.end_date else None,
            "special_instructions": self.special_instructions,
            'enabled': self.enabled
        }


@dataclass
class MedicationReminder:
    """用药提醒"""
    reminder_id: str
    user_id: int
    schedule_id: str
    medication_name: str
    dosage_amount: str
    scheduled_time: datetime
    meal_relation: MealRelation
    status: str = 'pending'  # pending/taken/skipped/delayed
    taken_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reminder_id": self.reminder_id,
            "schedule_id": self.schedule_id,
            "medication_name": self.medication_name,
            "dosage_amount": self.dosage_amount,
            "scheduled_time": self.scheduled_time.isoformat(),
            "meal_relation": self.meal_relation.value,
            'status': self.status,
            'taken_at': self.taken_at.isoformat() if self.taken_at else None,
            'notes': self.notes
        }


@dataclass
class MedicationLog:
    """用药记录"""
    log_id: str
    user_id: int
    medication_id: str
    medication_name: str
    dosage_taken: str
    taken_at: datetime
    on_schedule: bool
    scheduled_time: Optional[datetime] = None
    side_effects_noted: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'log_id': self.log_id,
            "medication_id": self.medication_id,
            "medication_name": self.medication_name,
            "dosage_taken": self.dosage_taken,
            'taken_at': self.taken_at.isoformat(),
            "on_schedule": self.on_schedule,
            "side_effects_noted": self.side_effects_noted,
            'notes': self.notes
        }


# ==================== 处方管理 ====================

@dataclass
class Prescription:
    """处方"""
    prescription_id: str
    user_id: int
    doctor_name: str
    hospital: str
    diagnosis: str
    medications: List[Dict[str, Any]]  # 药物列表及用法
    prescribed_date: datetime
    valid_until: Optional[datetime] = None
    refills_remaining: int = 0
    notes: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prescription_id": self.prescription_id,
            "doctor_name": self.doctor_name,
            'hospital': self.hospital,
            'diagnosis': self.diagnosis,
            "medications": self.medications,
            "prescribed_date": self.prescribed_date.isoformat(),
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "refills_remaining": self.refills_remaining,
            'notes': self.notes,
            'image_url': self.image_url
        }


# ==================== 药品库存 ====================

@dataclass
class MedicationInventory:
    """药品库存"""
    inventory_id: str
    user_id: int
    medication_id: str
    medication_name: str
    current_quantity: int
    unit: str  # 片/粒/ml等
    expiry_date: Optional[datetime] = None
    low_stock_threshold: int = 10
    auto_refill: bool = False
    last_refilled: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "inventory_id": self.inventory_id,
            "medication_id": self.medication_id,
            "medication_name": self.medication_name,
            "current_quantity": self.current_quantity,
            'unit': self.unit,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "low_stock_threshold": self.low_stock_threshold,
            "is_low_stock": self.current_quantity <= self.low_stock_threshold,
            "auto_refill": self.auto_refill,
            "last_refilled": self.last_refilled.isoformat() if self.last_refilled else None
        }


# ==================== 用药提醒服务 ====================

class MedicationReminderService:
    """用药提醒服务"""

    def __init__(self):
        self.schedules: Dict[str, MedicationSchedule] = {}
        self.user_schedules: Dict[int, List[str]] = defaultdict(list)
        self.reminders: Dict[str, MedicationReminder] = {}
        self.user_reminders: Dict[int, List[str]] = defaultdict(list)
        self.logs: Dict[str, MedicationLog] = {}
        self.user_logs: Dict[int, List[str]] = defaultdict(list)

    def create_schedule(
        self,
        user_id: int,
        medication_id: str,
        medication_name: str,
        dosage_amount: str,
        frequency: MedicationFrequency,
        meal_relation: MealRelation,
        scheduled_times: List[str],
        start_date: datetime,
        end_date: datetime = None,
        special_instructions: str = None
    ) -> MedicationSchedule:
        """创建用药计划"""
        schedule_id = f"sched_{user_id}_{secrets.token_hex(4)}"

        schedule = MedicationSchedule(
            schedule_id=schedule_id,
            user_id=user_id,
            medication_id=medication_id,
            medication_name=medication_name,
            dosage_amount=dosage_amount,
            frequency=frequency,
            meal_relation=meal_relation,
            scheduled_times=scheduled_times,
            start_date=start_date,
            end_date=end_date,
            special_instructions=special_instructions
        )

        self.schedules[schedule_id] = schedule
        self.user_schedules[user_id].append(schedule_id)

        logger.info(f"创建用药计划: {medication_name} for user {user_id}")
        return schedule

    def get_user_schedules(
        self,
        user_id: int,
        enabled_only: bool = True
    ) -> List[MedicationSchedule]:
        """获取用户用药计划"""
        schedule_ids = self.user_schedules.get(user_id, [])
        schedules = [self.schedules[sid] for sid in schedule_ids if sid in self.schedules]

        if enabled_only:
            schedules = [s for s in schedules if s.enabled]

        return schedules

    def generate_daily_reminders(self, user_id: int, date: datetime = None) -> List[MedicationReminder]:
        """生成每日提醒"""
        if date is None:
            date = datetime.now()

        schedules = self.get_user_schedules(user_id)
        reminders = []

        for schedule in schedules:
            # 检查日期是否在有效期内
            if schedule.start_date.date() > date.date():
                continue
            if schedule.end_date and schedule.end_date.date() < date.date():
                continue

            for time_str in schedule.scheduled_times:
                hour, minute = map(int, time_str.split(":"))
                scheduled_time = date.replace(hour=hour, minute=minute, second=0, microsecond=0)

                reminder_id = f"rem_{user_id}_{schedule.schedule_id}_{time_str.replace(':', '')}_{date.strftime('%Y%m%d')}"

                # 避免重复创建
                if reminder_id in self.reminders:
                    reminders.append(self.reminders[reminder_id])
                    continue

                reminder = MedicationReminder(
                    reminder_id=reminder_id,
                    user_id=user_id,
                    schedule_id=schedule.schedule_id,
                    medication_name=schedule.medication_name,
                    dosage_amount=schedule.dosage_amount,
                    scheduled_time=scheduled_time,
                    meal_relation=schedule.meal_relation
                )

                self.reminders[reminder_id] = reminder
                self.user_reminders[user_id].append(reminder_id)
                reminders.append(reminder)

        return sorted(reminders, key=lambda x: x.scheduled_time)

    def mark_taken(
        self,
        reminder_id: str,
        user_id: int,
        taken_at: datetime = None,
        notes: str = None
    ) -> bool:
        """标记已服药"""
        reminder = self.reminders.get(reminder_id)
        if not reminder or reminder.user_id != user_id:
            return False

        reminder.status = "taken"
        reminder.taken_at = taken_at or datetime.now()
        reminder.notes = notes

        # 创建服药记录
        self._create_log(user_id, reminder)

        return True

    def mark_skipped(self, reminder_id: str, user_id: int, reason: str = None) -> bool:
        """标记跳过"""
        reminder = self.reminders.get(reminder_id)
        if not reminder or reminder.user_id != user_id:
            return False

        reminder.status = "skipped"
        reminder.notes = reason
        return True

    def _create_log(self, user_id: int, reminder: MedicationReminder):
        """创建服药记录"""
        log_id = f"log_{user_id}_{int(datetime.now().timestamp())}"

        # 判断是否按时服药(15分钟内算按时)
        time_diff = abs((reminder.taken_at - reminder.scheduled_time).total_seconds())
        on_schedule = time_diff <= 900

        log = MedicationLog(
            log_id=log_id,
            user_id=user_id,
            medication_id=reminder.schedule_id,
            medication_name=reminder.medication_name,
            dosage_taken=reminder.dosage_amount,
            taken_at=reminder.taken_at,
            on_schedule=on_schedule,
            scheduled_time=reminder.scheduled_time,
            notes=reminder.notes
        )

        self.logs[log_id] = log
        self.user_logs[user_id].append(log_id)

    def get_pending_reminders(self, user_id: int) -> List[MedicationReminder]:
        """获取待处理提醒"""
        reminder_ids = self.user_reminders.get(user_id, [])
        reminders = [self.reminders[rid] for rid in reminder_ids if rid in self.reminders]

        now = datetime.now()
        pending = [r for r in reminders if r.status == 'pending' and r.scheduled_time <= now + timedelta(hours=1)]

        return sorted(pending, key=lambda x: x.scheduled_time)

    def get_adherence_rate(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """计算服药依从性"""
        cutoff = datetime.now() - timedelta(days=days)

        reminder_ids = self.user_reminders.get(user_id, [])
        reminders = [
            self.reminders[rid] for rid in reminder_ids
            if rid in self.reminders and self.reminders[rid].scheduled_time >= cutoff
        ]

        total = len(reminders)
        taken = sum(1 for r in reminders if r.status == "taken")
        skipped = sum(1 for r in reminders if r.status == 'skipped')
        on_time = sum(1 for r in reminders if r.status == 'taken' and r.taken_at and
                      abs((r.taken_at - r.scheduled_time).total_seconds()) <= 900)

        return {
            "period_days": days,
            "total_scheduled": total,
            "taken_count": taken,
            "skipped_count": skipped,
            "adherence_rate": round(taken / total * 100, 1) if total > 0 else 0,
            "on_time_rate": round(on_time / taken * 100, 1) if taken > 0 else 0
        }


# ==================== 药物相互作用检查服务 ====================

class DrugInteractionService:
    """药物相互作用检查服务"""

    # 常见药物相互作用数据库(简化版)
    INTERACTIONS = [
        DrugInteraction(
            '华法林', "阿司匹林",
            InteractionSeverity.SEVERE,
            "两种抗凝药物合用会增加出血风险",
            "避免同时使用，如必须使用请咨询医生"
        ),
        DrugInteraction(
            '阿司匹林', "布洛芬",
            InteractionSeverity.MODERATE,
            "两种非甾体抗炎药合用增加胃肠道出血风险",
            "尽量避免同时使用，如有疼痛建议咨询医生"
        ),
        DrugInteraction(
            '降压药', '西地那非',
            InteractionSeverity.SEVERE,
            '可能导致血压过低',
            '禁止同时使用'
        ),
        DrugInteraction(
            '他汀类', "西柚汁",
            InteractionSeverity.MODERATE,
            "西柚汁会增加他汀类药物血药浓度",
            "服用他汀类药物期间避免饮用西柚汁"
        ),
        DrugInteraction(
            '二甲双胍', "酒精",
            InteractionSeverity.MODERATE,
            "可能增加乳酸酸中毒风险",
            '服药期间避免饮酒'
        ),
        DrugInteraction(
            '抗生素', "钙片",
            InteractionSeverity.MILD,
            "钙会影响某些抗生素吸收",
            "建议间隔2小时以上服用"
        )
    ]

    def __init__(self):
        self.interaction_db = {
            (i.drug1, i.drug2): i for i in self.INTERACTIONS
        }
        # 添加反向映射
        for i in self.INTERACTIONS:
            self.interaction_db[(i.drug2, i.drug1)] = i

    def check_interactions(
        self,
        medications: List[str]
    ) -> List[DrugInteraction]:
        """检查药物相互作用"""
        interactions = []

        for i, drug1 in enumerate(medications):
            for drug2 in medications[i + 1:]:
                # 检查精确匹配
                key = (drug1, drug2)
                if key in self.interaction_db:
                    interactions.append(self.interaction_db[key])
                    continue

                # 检查部分匹配
                for (d1, d2), interaction in self.interaction_db.items():
                    if (d1 in drug1 or drug1 in d1) and (d2 in drug2 or drug2 in d2):
                        interactions.append(interaction)
                        break

        return interactions

    def check_food_interactions(
        self,
        medication: str
    ) -> List[Dict[str, str]]:
        """检查食物相互作用"""
        food_interactions = {
            '华法林': [
                {'food': '绿叶蔬菜', 'effect': '维生素K会降低药效', 'advice': '保持稳定摄入量'},
                {'food': '蔓越莓', 'effect': '可能增强抗凝效果', 'advice': '适量食用'}
            ],
            '他汀': [
                {'food': '西柚', 'effect': '增加药物浓度', 'advice': '避免食用'}
            ],
            '降压药': [
                {'food': '高钾食物', 'effect': '可能导致高钾血症', 'advice': '监测钾摄入'}
            ],
            '抗生素': [
                {'food': '乳制品', 'effect': '影响吸收', 'advice': "间隔2小时"}
            ]
        }

        for drug, interactions in food_interactions.items():
            if drug in medication or medication in drug:
                return interactions

        return []


# ==================== 处方管理服务 ====================

class PrescriptionService:
    """处方管理服务"""

    def __init__(self):
        self.prescriptions: Dict[str, Prescription] = {}
        self.user_prescriptions: Dict[int, List[str]] = defaultdict(list)

    def add_prescription(
        self,
        user_id: int,
        doctor_name: str,
        hospital: str,
        diagnosis: str,
        medications: List[Dict[str, Any]],
        prescribed_date: datetime,
        valid_until: datetime = None,
        refills_remaining: int = 0,
        notes: str = None,
        image_url: str = None
    ) -> Prescription:
        """添加处方"""
        prescription_id = f"rx_{user_id}_{int(datetime.now().timestamp())}"

        prescription = Prescription(
            prescription_id=prescription_id,
            user_id=user_id,
            doctor_name=doctor_name,
            hospital=hospital,
            diagnosis=diagnosis,
            medications=medications,
            prescribed_date=prescribed_date,
            valid_until=valid_until,
            refills_remaining=refills_remaining,
            notes=notes,
            image_url=image_url
        )

        self.prescriptions[prescription_id] = prescription
        self.user_prescriptions[user_id].append(prescription_id)

        return prescription

    def get_user_prescriptions(
        self,
        user_id: int,
        active_only: bool = False
    ) -> List[Prescription]:
        """获取用户处方"""
        prescription_ids = self.user_prescriptions.get(user_id, [])
        prescriptions = [self.prescriptions[pid] for pid in prescription_ids if pid in self.prescriptions]

        if active_only:
            now = datetime.now()
            prescriptions = [
                p for p in prescriptions
                if p.valid_until is None or p.valid_until >= now
            ]

        return sorted(prescriptions, key=lambda x: x.prescribed_date, reverse=True)

    def use_refill(self, prescription_id: str, user_id: int) -> bool:
        """使用续方"""
        prescription = self.prescriptions.get(prescription_id)
        if not prescription or prescription.user_id != user_id:
            return False

        if prescription.refills_remaining <= 0:
            return False

        prescription.refills_remaining -= 1
        return True


# ==================== 库存管理服务 ====================

class InventoryService:
    """库存管理服务"""

    def __init__(self):
        self.inventory: Dict[str, MedicationInventory] = {}
        self.user_inventory: Dict[int, List[str]] = defaultdict(list)

    def add_medication(
        self,
        user_id: int,
        medication_id: str,
        medication_name: str,
        quantity: int,
        unit: str,
        expiry_date: datetime = None,
        low_stock_threshold: int = 10
    ) -> MedicationInventory:
        """添加药品库存"""
        inventory_id = f"inv_{user_id}_{medication_id}"

        # 如果已存在,增加数量
        if inventory_id in self.inventory:
            self.inventory[inventory_id].current_quantity += quantity
            self.inventory[inventory_id].last_refilled = datetime.now()
            return self.inventory[inventory_id]

        inv = MedicationInventory(
            inventory_id=inventory_id,
            user_id=user_id,
            medication_id=medication_id,
            medication_name=medication_name,
            current_quantity=quantity,
            unit=unit,
            expiry_date=expiry_date,
            low_stock_threshold=low_stock_threshold,
            last_refilled=datetime.now()
        )

        self.inventory[inventory_id] = inv
        self.user_inventory[user_id].append(inventory_id)

        return inv

    def consume_medication(
        self,
        user_id: int,
        medication_id: str,
        quantity: int = 1
    ) -> Tuple[bool, Optional[MedicationInventory]]:
        """消耗药品"""
        inventory_id = f"inv_{user_id}_{medication_id}"
        inv = self.inventory.get(inventory_id)

        if not inv or inv.current_quantity < quantity:
            return False, None

        inv.current_quantity -= quantity
        return True, inv

    def get_user_inventory(self, user_id: int) -> List[MedicationInventory]:
        """获取用户库存"""
        inventory_ids = self.user_inventory.get(user_id, [])
        return [self.inventory[iid] for iid in inventory_ids if iid in self.inventory]

    def get_low_stock_alerts(self, user_id: int) -> List[MedicationInventory]:
        """获取低库存警告"""
        inventory = self.get_user_inventory(user_id)
        return [inv for inv in inventory if inv.current_quantity <= inv.low_stock_threshold]

    def get_expiring_soon(self, user_id: int, days: int = 30) -> List[MedicationInventory]:
        """获取即将过期药品"""
        inventory = self.get_user_inventory(user_id)
        cutoff = datetime.now() + timedelta(days=days)

        return [
            inv for inv in inventory
            if inv.expiry_date and inv.expiry_date <= cutoff
        ]


# ==================== 统一用药管理服务 ====================

class MedicationManagementService:
    """统一用药管理服务"""

    def __init__(self):
        self.reminder = MedicationReminderService()
        self.interaction = DrugInteractionService()
        self.prescription = PrescriptionService()
        self.inventory = InventoryService()


# 全局服务实例
medication_service = MedicationManagementService()
