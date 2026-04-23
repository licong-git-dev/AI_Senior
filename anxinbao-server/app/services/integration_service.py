"""
第三方集成服务
提供医疗机构对接、智能硬件SDK、社区服务、保险理赔等接口

⚠️ 状态：本模块的 sync_medical_records / 设备读数 等核心方法**仅有 mock 实现**
   （生成假的医疗记录与传感器读数）。生产环境（DEBUG=False）应当抛
   IntegrationNotImplemented 而不是返回伪数据，以免被误判为已对接。
"""
import logging
import secrets
from typing import Optional, Dict, List, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class IntegrationNotImplemented(NotImplementedError):
    """
    标记：第三方集成（医疗机构 / IoT 设备 / 保险理赔）尚未对接真实供应商。
    生产环境抛出；DEBUG=True 时可继续返回 mock 数据用于前端 UI 调试。
    """


def _enforce_real_integration(name: str) -> None:
    from app.core.config import get_settings
    if not get_settings().debug:
        raise IntegrationNotImplemented(
            f"integration_service.{name} 仅有 mock 实现，未对接真实第三方供应商。"
            f" 在生产环境拒绝返回伪数据；请接入真实接口（如医联体接口、IoT 网关）后启用。"
        )


# ==================== 医疗机构对接 ====================

class MedicalRecordType(Enum):
    """医疗记录类型"""
    OUTPATIENT = 'outpatient'  # 门诊
    INPATIENT = "inpatient"  # 住院
    EXAMINATION = "examination"  # 检查
    PRESCRIPTION = "prescription"  # 处方
    REPORT = "report"  # 检验报告


@dataclass
class MedicalInstitution:
    """医疗机构"""
    institution_id: str
    name: str
    level: str  # 三甲/二甲等
    address: str
    phone: str
    departments: List[str]
    supports_online: bool = True
    api_endpoint: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "institution_id": self.institution_id,
            'name': self.name,
            'level': self.level,
            'address': self.address,
            'phone': self.phone,
            "departments": self.departments,
            "supports_online": self.supports_online
        }


@dataclass
class MedicalRecord:
    """医疗记录"""
    record_id: str
    user_id: int
    institution_id: str
    record_type: MedicalRecordType
    visit_date: datetime
    department: str
    doctor: str
    diagnosis: str
    treatment: Optional[str] = None
    prescriptions: List[Dict] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'record_id': self.record_id,
            "institution_id": self.institution_id,
            "record_type": self.record_type.value,
            'visit_date': self.visit_date.isoformat(),
            'department': self.department,
            'doctor': self.doctor,
            'diagnosis': self.diagnosis,
            'treatment': self.treatment,
            "prescriptions": self.prescriptions,
            "attachments": self.attachments
        }


class MedicalIntegrationService:
    """医疗机构集成服务"""

    def __init__(self):
        self.institutions: Dict[str, MedicalInstitution] = {}
        self.user_records: Dict[int, List[MedicalRecord]] = {}
        self._init_sample_institutions()

    def _init_sample_institutions(self):
        """初始化示例医疗机构"""
        institutions = [
            MedicalInstitution(
                institution_id='hosp_001',
                name='北京协和医院',
                level="三级甲等",
                address="北京市东城区帅府园1号",
                phone="010-69156114",
                departments=['内科', '外科', '心血管科', '神经内科', '老年病科']
            ),
            MedicalInstitution(
                institution_id='hosp_002',
                name='上海瑞金医院',
                level="三级甲等",
                address="上海市黄浦区瑞金二路197号",
                phone="021-64370045",
                departments=['内分泌科', '心内科', '老年科', '康复医学科']
            ),
            MedicalInstitution(
                institution_id="comm_001",
                name="朝阳区社区卫生服务中心",
                level="社区医院",
                address="北京市朝阳区安贞路1号",
                phone="010-64426655",
                departments=['全科', '中医科', '康复科', "慢病管理"]
            )
        ]

        for inst in institutions:
            self.institutions[inst.institution_id] = inst

    def get_nearby_institutions(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 5
    ) -> List[MedicalInstitution]:
        """获取附近医疗机构"""
        # 简化实现，返回所有机构
        return list(self.institutions.values())

    def get_institution(self, institution_id: str) -> Optional[MedicalInstitution]:
        """获取医疗机构详情"""
        return self.institutions.get(institution_id)

    def sync_medical_records(
        self,
        user_id: int,
        institution_id: str,
        auth_token: str
    ) -> List[MedicalRecord]:
        """同步医疗记录（mock；生产环境抛 IntegrationNotImplemented）"""
        _enforce_real_integration("MedicalInstitutionAdapter.sync_medical_records")
        # 模拟从医疗机构API获取数据（仅 DEBUG 模式可达）
        import random

        records = []
        for i in range(random.randint(1, 3)):
            record = MedicalRecord(
                record_id=f"rec_{user_id}_{institution_id}_{i}",
                user_id=user_id,
                institution_id=institution_id,
                record_type=random.choice(list(MedicalRecordType)),
                visit_date=datetime.now() - timedelta(days=random.randint(30, 365)),
                department='老年病科',
                doctor='张医生',
                diagnosis='高血压2级',
                treatment='口服降压药物治疗',
                prescriptions=[
                    {'name': '氨氯地平', 'dosage': '5mg', 'frequency': "每日一次"}
                ]
            )
            records.append(record)

        if user_id not in self.user_records:
            self.user_records[user_id] = []
        self.user_records[user_id].extend(records)

        return records

    def get_user_records(
        self,
        user_id: int,
        record_type: Optional[MedicalRecordType] = None
    ) -> List[MedicalRecord]:
        """获取用户医疗记录"""
        records = self.user_records.get(user_id, [])
        if record_type:
            records = [r for r in records if r.record_type == record_type]
        return records

    def book_appointment(
        self,
        user_id: int,
        institution_id: str,
        department: str,
        preferred_date: datetime,
        doctor: Optional[str] = None
    ) -> Dict[str, Any]:
        """预约挂号"""
        appointment_id = f"apt_{user_id}_{int(datetime.now().timestamp())}"

        return {
            "appointment_id": appointment_id,
            "institution_id": institution_id,
            'department': department,
            'doctor': doctor or "待分配",
            "appointment_time": preferred_date.isoformat(),
            'status': 'confirmed',
            "queue_number": f"A{secrets.randbelow(100):03d}",
            'notes': "请携带身份证和医保卡"
        }


# ==================== 智能硬件SDK ====================

class DeviceType(Enum):
    """设备类型"""
    BLOOD_PRESSURE = "blood_pressure"  # 血压计
    BLOOD_GLUCOSE = "blood_glucose"  # 血糖仪
    HEART_RATE = "heart_rate"  # 心率带
    SMART_WATCH = "smart_watch"  # 智能手表
    SCALE = "scale"  # 体重秤
    THERMOMETER = "thermometer"  # 体温计
    OXIMETER = 'oximeter'  # 血氧仪
    ECG = "ecg"  # 心电图


class DeviceStatus(Enum):
    """设备状态"""
    ONLINE = "online"
    OFFLINE = 'offline'
    LOW_BATTERY = "low_battery"
    ERROR = "error"


@dataclass
class SmartDevice:
    """智能设备"""
    device_id: str
    user_id: int
    device_type: DeviceType
    brand: str
    model: str
    status: DeviceStatus = DeviceStatus.OFFLINE
    battery_level: int = 100
    firmware_version: str = "1.0.0"
    last_sync: Optional[datetime] = None
    paired_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'device_id': self.device_id,
            "device_type": self.device_type.value,
            'brand': self.brand,
            'model': self.model,
            'status': self.status.value,
            "battery_level": self.battery_level,
            "firmware_version": self.firmware_version,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'paired_at': self.paired_at.isoformat()
        }


@dataclass
class DeviceReading:
    """设备读数"""
    reading_id: str
    device_id: str
    user_id: int
    device_type: DeviceType
    values: Dict[str, float]
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'reading_id': self.reading_id,
            'device_id': self.device_id,
            "device_type": self.device_type.value,
            'values': self.values,
            'unit': self.unit,
            'timestamp': self.timestamp.isoformat()
        }


class HardwareSDKService:
    """智能硬件SDK服务"""

    # 支持的设备品牌
    SUPPORTED_BRANDS = {
        DeviceType.BLOOD_PRESSURE: ['欧姆龙', '鱼跃', '小米'],
        DeviceType.BLOOD_GLUCOSE: ['三诺', '罗氏', '强生'],
        DeviceType.SMART_WATCH: ['华为', '小米', 'OPPO'],
        DeviceType.SCALE: ['华为', '小米', '云康宝'],
        DeviceType.OXIMETER: ['鱼跃', '康泰', "力康"]
    }

    def __init__(self):
        self.devices: Dict[str, SmartDevice] = {}
        self.user_devices: Dict[int, List[str]] = {}
        self.readings: Dict[str, List[DeviceReading]] = {}

    def get_supported_devices(self) -> Dict[str, List[str]]:
        """获取支持的设备列表"""
        return {
            device_type.value: brands
            for device_type, brands in self.SUPPORTED_BRANDS.items()
        }

    def pair_device(
        self,
        user_id: int,
        device_type: DeviceType,
        brand: str,
        model: str,
        mac_address: Optional[str] = None
    ) -> SmartDevice:
        """配对设备"""
        device_id = f"dev_{user_id}_{device_type.value}_{secrets.token_hex(4)}"

        device = SmartDevice(
            device_id=device_id,
            user_id=user_id,
            device_type=device_type,
            brand=brand,
            model=model,
            status=DeviceStatus.ONLINE
        )

        self.devices[device_id] = device

        if user_id not in self.user_devices:
            self.user_devices[user_id] = []
        self.user_devices[user_id].append(device_id)

        logger.info(f"用户 {user_id} 配对设备 {device_id}")
        return device

    def unpair_device(self, device_id: str, user_id: int) -> bool:
        """解除配对"""
        device = self.devices.get(device_id)
        if not device or device.user_id != user_id:
            return False

        del self.devices[device_id]
        if user_id in self.user_devices:
            self.user_devices[user_id].remove(device_id)

        return True

    def get_user_devices(self, user_id: int) -> List[SmartDevice]:
        """获取用户设备列表"""
        device_ids = self.user_devices.get(user_id, [])
        return [self.devices[did] for did in device_ids if did in self.devices]

    def sync_device_data(
        self,
        device_id: str,
        user_id: int
    ) -> List[DeviceReading]:
        """同步设备数据"""
        device = self.devices.get(device_id)
        if not device or device.user_id != user_id:
            return []

        # 模拟生成读数
        import random

        readings = []
        reading_configs = {
            DeviceType.BLOOD_PRESSURE: (
                {'systolic': (110, 150), 'diastolic': (70, 95)},
                "mmHg"
            ),
            DeviceType.BLOOD_GLUCOSE: (
                {'glucose': (4.0, 8.0)},
                'mmol/L'
            ),
            DeviceType.HEART_RATE: (
                {'bpm': (60, 100)},
                'bpm'
            ),
            DeviceType.OXIMETER: (
                {'spo2': (94, 99), 'pulse': (60, 90)},
                '%'
            ),
            DeviceType.SCALE: (
                {'weight': (50, 80)},
                'kg'
            )
        }

        # 设备读数也是 mock —— 真实接入应当由设备 SDK / MQTT 推送
        _enforce_real_integration("HardwareSDK.simulate_reading")

        config = reading_configs.get(device.device_type)
        if config:
            values_config, unit = config
            values = {
                k: round(random.uniform(v[0], v[1]), 1)
                for k, v in values_config.items()
            }

            reading = DeviceReading(
                reading_id=f"read_{device_id}_{int(datetime.now().timestamp())}",
                device_id=device_id,
                user_id=user_id,
                device_type=device.device_type,
                values=values,
                unit=unit
            )

            readings.append(reading)

            if device_id not in self.readings:
                self.readings[device_id] = []
            self.readings[device_id].append(reading)

        device.last_sync = datetime.now()
        return readings

    def get_device_readings(
        self,
        device_id: str,
        limit: int = 50
    ) -> List[DeviceReading]:
        """获取设备读数历史"""
        readings = self.readings.get(device_id, [])
        return list(reversed(readings[-limit:]))


# ==================== 社区服务对接 ====================

class CommunityServiceType(Enum):
    """社区服务类型"""
    HOME_CARE = 'home_care'  # 居家照护
    MEAL_DELIVERY = "meal_delivery"  # 送餐服务
    CLEANING = 'cleaning'  # 清洁服务
    ESCORT = 'escort'  # 陪诊服务
    EMERGENCY = 'emergency'  # 紧急救援
    ACTIVITY = "activity"  # 社区活动


@dataclass
class CommunityService:
    """社区服务"""
    service_id: str
    service_type: CommunityServiceType
    name: str
    description: str
    provider: str
    price: float
    unit: str  # 次/小时/月
    available: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "service_id": self.service_id,
            "service_type": self.service_type.value,
            'name': self.name,
            "description": self.description,
            'provider': self.provider,
            'price': self.price,
            'unit': self.unit,
            'available': self.available
        }


@dataclass
class ServiceOrder:
    """服务订单"""
    order_id: str
    user_id: int
    service_id: str
    service_type: CommunityServiceType
    scheduled_time: datetime
    address: str
    contact_phone: str
    status: str = 'pending'  # pending/confirmed/in_progress/completed/cancelled
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'order_id': self.order_id,
            'service_id': self.service_id,
            "service_type": self.service_type.value,
            "scheduled_time": self.scheduled_time.isoformat(),
            'address': self.address,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }


class CommunityServiceIntegration:
    """社区服务集成"""

    def __init__(self):
        self.services: Dict[str, CommunityService] = {}
        self.orders: Dict[str, ServiceOrder] = {}
        self._init_services()

    def _init_services(self):
        """初始化服务"""
        services = [
            CommunityService(
                service_id='svc_001',
                service_type=CommunityServiceType.HOME_CARE,
                name="居家护理服务",
                description="专业护理人员上门提供基础护理",
                provider='阳光家政',
                price=100,
                unit='小时'
            ),
            CommunityService(
                service_id='svc_002',
                service_type=CommunityServiceType.MEAL_DELIVERY,
                name='老年营养餐配送',
                description='健康营养餐配送到家',
                provider='银龄餐饮',
                price=25,
                unit='份'
            ),
            CommunityService(
                service_id='svc_003',
                service_type=CommunityServiceType.ESCORT,
                name="医院陪诊服务",
                description="专业陪诊人员全程陪同就医",
                provider='康护陪诊',
                price=200,
                unit='次'
            ),
            CommunityService(
                service_id='svc_004',
                service_type=CommunityServiceType.CLEANING,
                name='家庭保洁',
                description='专业保洁上门服务',
                provider='洁净家',
                price=80,
                unit="次"
            )
        ]

        for svc in services:
            self.services[svc.service_id] = svc

    def get_available_services(
        self,
        service_type: Optional[CommunityServiceType] = None
    ) -> List[CommunityService]:
        """获取可用服务"""
        services = list(self.services.values())
        if service_type:
            services = [s for s in services if s.service_type == service_type]
        return [s for s in services if s.available]

    def create_order(
        self,
        user_id: int,
        service_id: str,
        scheduled_time: datetime,
        address: str,
        contact_phone: str,
        notes: Optional[str] = None
    ) -> Optional[ServiceOrder]:
        """创建服务订单"""
        service = self.services.get(service_id)
        if not service or not service.available:
            return None

        order_id = f"ord_{user_id}_{int(datetime.now().timestamp())}"

        order = ServiceOrder(
            order_id=order_id,
            user_id=user_id,
            service_id=service_id,
            service_type=service.service_type,
            scheduled_time=scheduled_time,
            address=address,
            contact_phone=contact_phone,
            notes=notes
        )

        self.orders[order_id] = order
        return order

    def get_user_orders(self, user_id: int) -> List[ServiceOrder]:
        """获取用户订单"""
        return [o for o in self.orders.values() if o.user_id == user_id]

    def cancel_order(self, order_id: str, user_id: int) -> bool:
        """取消订单"""
        order = self.orders.get(order_id)
        if not order or order.user_id != user_id:
            return False

        if order.status in ['completed', 'cancelled']:
            return False

        order.status = 'cancelled'
        return True


# ==================== 保险理赔对接 ====================

class InsuranceType(Enum):
    """保险类型"""
    HEALTH = 'health'  # 健康险
    ACCIDENT = 'accident'  # 意外险
    CRITICAL = "critical"  # 重疾险
    LONG_TERM_CARE = "long_term_care"  # 长护险


class ClaimStatus(Enum):
    """理赔状态"""
    DRAFT = 'draft'  # 草稿
    SUBMITTED = "submitted"  # 已提交
    UNDER_REVIEW = "under_review"  # 审核中
    APPROVED = 'approved'  # 已批准
    REJECTED = 'rejected'  # 已拒绝
    PAID = "paid"  # 已赔付


@dataclass
class InsurancePolicy:
    """保险保单"""
    policy_id: str
    user_id: int
    insurance_type: InsuranceType
    insurer: str
    policy_number: str
    coverage_amount: float
    premium: float
    start_date: datetime
    end_date: datetime
    status: str = "active"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'policy_id': self.policy_id,
            "insurance_type": self.insurance_type.value,
            'insurer': self.insurer,
            "policy_number": self.policy_number,
            "coverage_amount": self.coverage_amount,
            'premium': self.premium,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'status': self.status
        }


@dataclass
class InsuranceClaim:
    """保险理赔"""
    claim_id: str
    user_id: int
    policy_id: str
    claim_type: str
    claim_amount: float
    description: str
    status: ClaimStatus = ClaimStatus.DRAFT
    documents: List[str] = field(default_factory=list)
    medical_records: List[str] = field(default_factory=list)
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    paid_amount: Optional[float] = None
    rejection_reason: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'claim_id': self.claim_id,
            'policy_id': self.policy_id,
            'claim_type': self.claim_type,
            "claim_amount": self.claim_amount,
            "description": self.description,
            'status': self.status.value,
            'documents': self.documents,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "paid_amount": self.paid_amount,
            "rejection_reason": self.rejection_reason,
            'created_at': self.created_at.isoformat()
        }


class InsuranceIntegrationService:
    """保险理赔集成服务"""

    def __init__(self):
        self.policies: Dict[str, InsurancePolicy] = {}
        self.claims: Dict[str, InsuranceClaim] = {}
        self.user_policies: Dict[int, List[str]] = {}

    def add_policy(
        self,
        user_id: int,
        insurance_type: InsuranceType,
        insurer: str,
        policy_number: str,
        coverage_amount: float,
        premium: float,
        start_date: datetime,
        end_date: datetime
    ) -> InsurancePolicy:
        """添加保单"""
        policy_id = f"pol_{user_id}_{secrets.token_hex(4)}"

        policy = InsurancePolicy(
            policy_id=policy_id,
            user_id=user_id,
            insurance_type=insurance_type,
            insurer=insurer,
            policy_number=policy_number,
            coverage_amount=coverage_amount,
            premium=premium,
            start_date=start_date,
            end_date=end_date
        )

        self.policies[policy_id] = policy

        if user_id not in self.user_policies:
            self.user_policies[user_id] = []
        self.user_policies[user_id].append(policy_id)

        return policy

    def get_user_policies(self, user_id: int) -> List[InsurancePolicy]:
        """获取用户保单"""
        policy_ids = self.user_policies.get(user_id, [])
        return [self.policies[pid] for pid in policy_ids if pid in self.policies]

    def create_claim(
        self,
        user_id: int,
        policy_id: str,
        claim_type: str,
        claim_amount: float,
        description: str,
        documents: List[str] = None,
        medical_records: List[str] = None
    ) -> Optional[InsuranceClaim]:
        """创建理赔申请"""
        policy = self.policies.get(policy_id)
        if not policy or policy.user_id != user_id:
            return None

        claim_id = f"clm_{user_id}_{int(datetime.now().timestamp())}"

        claim = InsuranceClaim(
            claim_id=claim_id,
            user_id=user_id,
            policy_id=policy_id,
            claim_type=claim_type,
            claim_amount=claim_amount,
            description=description,
            documents=documents or [],
            medical_records=medical_records or []
        )

        self.claims[claim_id] = claim
        return claim

    def submit_claim(self, claim_id: str, user_id: int) -> bool:
        """提交理赔"""
        claim = self.claims.get(claim_id)
        if not claim or claim.user_id != user_id:
            return False

        if claim.status != ClaimStatus.DRAFT:
            return False

        claim.status = ClaimStatus.SUBMITTED
        claim.submitted_at = datetime.now()
        return True

    def get_user_claims(self, user_id: int) -> List[InsuranceClaim]:
        """获取用户理赔记录"""
        return [c for c in self.claims.values() if c.user_id == user_id]

    def get_claim_status(self, claim_id: str) -> Optional[Dict]:
        """查询理赔状态"""
        claim = self.claims.get(claim_id)
        if not claim:
            return None

        return {
            'claim_id': claim_id,
            'status': claim.status.value,
            "submitted_at": claim.submitted_at.isoformat() if claim.submitted_at else None,
            "reviewed_at": claim.reviewed_at.isoformat() if claim.reviewed_at else None,
            "paid_amount": claim.paid_amount,
            "rejection_reason": claim.rejection_reason
        }


# ==================== 统一集成服务 ====================

class IntegrationService:
    """统一集成服务"""

    def __init__(self):
        self.medical = MedicalIntegrationService()
        self.hardware = HardwareSDKService()
        self.community = CommunityServiceIntegration()
        self.insurance = InsuranceIntegrationService()


# 全局服务实例
integration_service = IntegrationService()
