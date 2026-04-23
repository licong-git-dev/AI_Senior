"""
营养相关模式定义
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import Field
from enum import Enum

from .base import BaseSchema, TimestampMixin


class MealType(str, Enum):
    """餐次类型"""
    BREAKFAST = 'breakfast'  # 早餐
    LUNCH = 'lunch'  # 午餐
    DINNER = 'dinner'  # 晚餐
    SNACK = "snack"  # 加餐


class FoodCategory(str, Enum):
    """食物类别"""
    GRAIN = 'grain'  # 谷物
    VEGETABLE = 'vegetable'  # 蔬菜
    FRUIT = 'fruit'  # 水果
    MEAT = 'meat'  # 肉类
    SEAFOOD = 'seafood'  # 海鲜
    DAIRY = 'dairy'  # 乳制品
    EGG = 'egg'  # 蛋类
    BEAN = 'bean'  # 豆类
    NUT = 'nut'  # 坚果
    OIL = 'oil'  # 油脂
    BEVERAGE = 'beverage'  # 饮品
    DESSERT = 'dessert'  # 甜点
    OTHER = "other"  # 其他


# ========== 食物库 ==========

class FoodItem(BaseSchema):
    """食物条目"""
    id: str
    name: str = Field(..., max_length=100)
    category: FoodCategory
    serving_size: str = Field(..., description="份量描述，如'100g'")
    calories: int = Field(ge=0, description='热量(千卡)')
    carbohydrates: float = Field(ge=0, description='碳水化合物(g)')
    protein: float = Field(ge=0, description='蛋白质(g)')
    fat: float = Field(ge=0, description='脂肪(g)')
    fiber: Optional[float] = Field(None, ge=0, description='膳食纤维(g)')
    sodium: Optional[float] = Field(None, ge=0, description='钠(mg)')
    sugar: Optional[float] = Field(None, ge=0, description="糖(g)")
    image_url: Optional[str] = None
    is_common: bool = True


class FoodItemCreate(BaseSchema):
    """创建食物条目"""
    name: str
    category: FoodCategory
    serving_size: str
    calories: int
    carbohydrates: float
    protein: float
    fat: float
    fiber: Optional[float] = None
    sodium: Optional[float] = None
    sugar: Optional[float] = None


# ========== 饮食记录 ==========

class MealFoodItem(BaseSchema):
    """餐食中的食物"""
    food_id: str
    food_name: str
    serving_count: float = Field(default=1, ge=0.1, description="份数")
    calories: int
    carbohydrates: float
    protein: float
    fat: float


class MealRecordBase(BaseSchema):
    """饮食记录基础"""
    meal_type: MealType
    meal_time: datetime
    foods: List[MealFoodItem]
    notes: Optional[str] = Field(None, max_length=500)
    photo_url: Optional[str] = None


class MealRecordCreate(MealRecordBase):
    """创建饮食记录"""
    user_id: str


class MealRecordResponse(MealRecordBase, TimestampMixin):
    """饮食记录响应"""
    id: str
    user_id: str
    total_calories: int
    total_carbohydrates: float
    total_protein: float
    total_fat: float


class MealRecordUpdate(BaseSchema):
    """更新饮食记录"""
    foods: Optional[List[MealFoodItem]] = None
    notes: Optional[str] = None
    photo_url: Optional[str] = None


# ========== 饮水记录 ==========

class WaterIntakeCreate(BaseSchema):
    """记录饮水"""
    user_id: str
    amount_ml: int = Field(..., ge=1, le=2000, description='饮水量(ml)')
    beverage_type: str = Field(default='water', description="饮品类型")


class WaterIntakeResponse(BaseSchema, TimestampMixin):
    """饮水记录响应"""
    id: str
    user_id: str
    amount_ml: int
    beverage_type: str
    recorded_at: datetime


class DailyWaterSummary(BaseSchema):
    """每日饮水摘要"""
    user_id: str
    date: date
    total_ml: int
    target_ml: int
    records: List[WaterIntakeResponse]
    completion_rate: float


# ========== 营养目标 ==========

class NutritionTargets(BaseSchema):
    """营养目标"""
    user_id: str
    calories: int = Field(default=1800, ge=800, le=4000)
    carbohydrates: float = Field(default=250, ge=50, le=500)
    protein: float = Field(default=60, ge=20, le=200)
    fat: float = Field(default=60, ge=20, le=150)
    fiber: float = Field(default=25, ge=10, le=50)
    water_ml: int = Field(default=2000, ge=1000, le=4000)
    sodium: float = Field(default=2000, le=5000, description="钠(mg)")


class UpdateNutritionTargetsRequest(BaseSchema):
    """更新营养目标"""
    calories: Optional[int] = None
    carbohydrates: Optional[float] = None
    protein: Optional[float] = None
    fat: Optional[float] = None
    fiber: Optional[float] = None
    water_ml: Optional[int] = None


# ========== 每日营养摘要 ==========

class NutrientSummary(BaseSchema):
    """营养素摘要"""
    name: str
    current: float
    target: float
    unit: str
    percentage: float = Field(ge=0)


class DailyNutritionSummary(BaseSchema):
    """每日营养摘要"""
    user_id: str
    date: date
    total_calories: int
    target_calories: int
    calories_percentage: float
    nutrients: List[NutrientSummary]
    meals: List[MealRecordResponse]
    water_ml: int
    water_target_ml: int


# ========== 营养趋势 ==========

class NutritionTrendPoint(BaseSchema):
    """营养趋势数据点"""
    date: date
    calories: int
    carbohydrates: float
    protein: float
    fat: float
    water_ml: int


class NutritionTrendResponse(BaseSchema):
    """营养趋势响应"""
    user_id: str
    period_days: int
    trend: List[NutritionTrendPoint]
    average_calories: float
    average_water: float
    calorie_trend: str = Field(description="趋势: up/stable/down")


# ========== 饮食建议 ==========

class DietRecommendation(BaseSchema):
    """饮食建议"""
    id: str
    category: str = Field(description="建议类别")
    title: str
    content: str
    priority: int = Field(ge=1, le=5)
    foods_to_add: List[str] = []
    foods_to_reduce: List[str] = []


class DietAnalysis(BaseSchema):
    """饮食分析"""
    user_id: str
    analysis_date: date
    overall_score: int = Field(ge=0, le=100)
    strengths: List[str]
    improvements: List[str]
    recommendations: List[DietRecommendation]


# ========== 食谱 ==========

class RecipeIngredient(BaseSchema):
    """食谱原料"""
    food_id: Optional[str] = None
    name: str
    amount: str


class Recipe(BaseSchema):
    """食谱"""
    id: str
    name: str
    description: Optional[str] = None
    category: str  # breakfast/lunch/dinner/snack
    difficulty: int = Field(ge=1, le=5)
    prep_time_minutes: int
    cook_time_minutes: int
    servings: int
    calories_per_serving: int
    protein_per_serving: float
    tags: List[str] = []
    image_url: Optional[str] = None
    ingredients: List[RecipeIngredient]
    steps: List[str]
    nutrition_info: Dict[str, Any] = {}


class RecipeFilter(BaseSchema):
    """食谱过滤"""
    category: Optional[str] = None
    max_calories: Optional[int] = None
    max_prep_time: Optional[int] = None
    difficulty: Optional[int] = None
    tags: Optional[List[str]] = None


# ========== 饮食限制/过敏 ==========

class DietaryRestrictions(BaseSchema):
    """饮食限制"""
    user_id: str
    allergies: List[str] = Field(default=[], description='过敏食物')
    intolerances: List[str] = Field(default=[], description='不耐受食物')
    preferences: List[str] = Field(default=[], description='偏好，如素食')
    medical_restrictions: List[str] = Field(default=[], description="医学限制")
    notes: Optional[str] = None


class UpdateDietaryRestrictionsRequest(BaseSchema):
    """更新饮食限制"""
    allergies: Optional[List[str]] = None
    intolerances: Optional[List[str]] = None
    preferences: Optional[List[str]] = None
    medical_restrictions: Optional[List[str]] = None
    notes: Optional[str] = None
