"""
药品识别模块 Pydantic 数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ==================== 枚举类型 ====================

class DosageForm(str, Enum):
    """剂型"""
    TABLET = 'tablet'
    CAPSULE = 'capsule'
    LIQUID = 'liquid'
    INJECTION = 'injection'
    TOPICAL = 'topical'
    POWDER = 'powder'
    PATCH = 'patch'


class DrugCategory(str, Enum):
    """药品类别"""
    OTC = 'otc'
    PRESCRIPTION = "prescription"
    CHINESE_MEDICINE = "chinese_medicine"


class RecognitionStatus(str, Enum):
    """识别状态"""
    SUCCESS = 'success'
    PARTIAL = 'partial'
    FAILED = 'failed'
    MANUAL = 'manual'


class InteractionSeverity(str, Enum):
    """药物相互作用严重程度"""
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'


class InteractionType(str, Enum):
    """药物相互作用类型"""
    CONTRAINDICATED = "contraindicated"
    MAJOR = 'major'
    MODERATE = 'moderate'
    MINOR = 'minor'


# ==================== 药品信息 ====================

class DrugInfoCreate(BaseModel):
    """创建药品信息"""
    name: str = Field(..., max_length=100)
    generic_name: Optional[str] = Field(None, max_length=100)
    brand_names: Optional[List[str]] = None
    barcode: Optional[str] = Field(None, max_length=50)

    specification: Optional[str] = None
    dosage_form: Optional[DosageForm] = None
    manufacturer: Optional[str] = None
    approval_number: Optional[str] = None

    drug_category: Optional[DrugCategory] = None
    therapeutic_category: Optional[str] = None

    indications: Optional[str] = None
    dosage_instructions: Optional[str] = None
    contraindications: Optional[str] = None
    side_effects: Optional[str] = None
    interactions: Optional[str] = None
    precautions: Optional[str] = None
    storage: Optional[str] = None

    elderly_precautions: Optional[str] = None
    image_url: Optional[str] = None


class DrugInfoUpdate(BaseModel):
    """更新药品信息"""
    name: Optional[str] = Field(None, max_length=100)
    generic_name: Optional[str] = Field(None, max_length=100)
    brand_names: Optional[List[str]] = None
    barcode: Optional[str] = Field(None, max_length=50)

    specification: Optional[str] = None
    dosage_form: Optional[DosageForm] = None
    manufacturer: Optional[str] = None

    drug_category: Optional[DrugCategory] = None
    therapeutic_category: Optional[str] = None

    indications: Optional[str] = None
    dosage_instructions: Optional[str] = None
    contraindications: Optional[str] = None
    side_effects: Optional[str] = None
    interactions: Optional[str] = None
    precautions: Optional[str] = None
    storage: Optional[str] = None

    elderly_precautions: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None


class DrugInfoResponse(BaseModel):
    """药品信息响应"""
    id: int
    name: str
    generic_name: Optional[str]
    brand_names: Optional[List[str]]
    barcode: Optional[str]

    specification: Optional[str]
    dosage_form: Optional[str]
    manufacturer: Optional[str]
    approval_number: Optional[str]

    drug_category: Optional[str]
    therapeutic_category: Optional[str]

    indications: Optional[str]
    dosage_instructions: Optional[str]
    contraindications: Optional[str]
    side_effects: Optional[str]
    interactions: Optional[str]
    precautions: Optional[str]
    storage: Optional[str]

    elderly_precautions: Optional[str]
    image_url: Optional[str]

    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DrugInfoBrief(BaseModel):
    """药品信息简要"""
    id: int
    name: str
    generic_name: Optional[str]
    specification: Optional[str]
    dosage_form: Optional[str]
    manufacturer: Optional[str]
    image_url: Optional[str]

    class Config:
        from_attributes = True


# ==================== 药品识别 ====================

class RecognizeDrugRequest(BaseModel):
    """识别药品请求"""
    user_id: int
    image_base64: Optional[str] = None  # Base64编码的图片
    image_url: Optional[str] = None  # 图片URL
    barcode: Optional[str] = None  # 条形码


class RecognizeDrugResponse(BaseModel):
    """识别药品响应"""
    success: bool
    status: RecognitionStatus
    recognition_id: int
    recognized_text: Optional[str]
    matched_drug: Optional[DrugInfoBrief]
    confidence: Optional[float]
    suggestions: Optional[List[DrugInfoBrief]]  # 其他可能匹配的药品
    message: Optional[str]


class DrugRecognitionLogResponse(BaseModel):
    """药品识别日志响应"""
    id: int
    user_id: int
    image_url: Optional[str]
    recognized_text: Optional[str]
    barcode: Optional[str]
    drug_info_id: Optional[int]
    matched_name: Optional[str]
    confidence: Optional[float]
    status: str
    manual_correction: Optional[str]
    added_to_medication: bool
    medication_id: Optional[int]
    recognized_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class CorrectRecognitionRequest(BaseModel):
    """更正识别结果请求"""
    recognition_id: int
    correct_drug_name: str
    correct_drug_id: Optional[int] = None


class AddToMedicationRequest(BaseModel):
    """添加到用药计划请求"""
    recognition_id: int
    dosage: str = Field(..., description="剂量，如'1片'")
    frequency: str = Field(..., description="频次，如'twice_daily'")
    times: List[str] = Field(..., description='服药时间，如["08:00", "20:00"]')
    instructions: Optional[str] = None
    start_date: Optional[datetime] = None
    quantity: Optional[int] = None


class AddToMedicationResponse(BaseModel):
    """添加到用药计划响应"""
    success: bool
    medication_id: int
    message: str


# ==================== 药物相互作用 ====================

class DrugInteractionCreate(BaseModel):
    """创建药物相互作用"""
    drug_a_id: int
    drug_b_id: int
    interaction_type: InteractionType
    severity: InteractionSeverity
    description: Optional[str] = None
    recommendation: Optional[str] = None


class DrugInteractionResponse(BaseModel):
    """药物相互作用响应"""
    id: int
    drug_a: DrugInfoBrief
    drug_b: DrugInfoBrief
    interaction_type: str
    severity: str
    description: Optional[str]
    recommendation: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CheckInteractionsRequest(BaseModel):
    """检查药物相互作用请求"""
    user_id: int
    drug_ids: Optional[List[int]] = None  # 检查指定药品
    check_all_medications: bool = False  # 检查用户所有用药


class CheckInteractionsResponse(BaseModel):
    """检查药物相互作用响应"""
    has_interactions: bool
    total_interactions: int
    critical_interactions: List[DrugInteractionResponse]
    major_interactions: List[DrugInteractionResponse]
    moderate_interactions: List[DrugInteractionResponse]
    minor_interactions: List[DrugInteractionResponse]
    recommendations: List[str]


# ==================== 药品搜索 ====================

class SearchDrugsRequest(BaseModel):
    """搜索药品请求"""
    keyword: str = Field(..., min_length=1)
    category: Optional[DrugCategory] = None
    limit: int = Field(default=20, ge=1, le=100)


class SearchDrugsResponse(BaseModel):
    """搜索药品响应"""
    drugs: List[DrugInfoBrief]
    total: int


# ==================== 老年人用药提示 ====================

class ElderlyDrugTipsRequest(BaseModel):
    """获取老年人用药提示请求"""
    drug_id: int
    user_id: Optional[int] = None  # 如提供，会结合用户健康档案


class ElderlyDrugTipsResponse(BaseModel):
    """老年人用药提示响应"""
    drug_name: str
    general_tips: List[str]
    personalized_tips: Optional[List[str]]  # 基于用户健康档案的个性化提示
    warnings: Optional[List[str]]  # 特别警告
    food_interactions: Optional[List[str]]  # 食物相互作用
