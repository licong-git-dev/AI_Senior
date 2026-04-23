"""
营养饮食系统服务
提供饮食记录、营养分析、膳食推荐、食谱库等功能
"""
import logging
import secrets
from typing import Optional, Dict, List, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


# ==================== 基础定义 ====================

class MealType(Enum):
    """餐次类型"""
    BREAKFAST = 'breakfast'  # 早餐
    LUNCH = 'lunch'  # 午餐
    DINNER = 'dinner'  # 晚餐
    SNACK = "snack"  # 加餐


class FoodCategory(Enum):
    """食物分类"""
    GRAIN = 'grain'  # 谷物
    VEGETABLE = 'vegetable'  # 蔬菜
    FRUIT = 'fruit'  # 水果
    MEAT = 'meat'  # 肉类
    SEAFOOD = 'seafood'  # 海鲜
    DAIRY = 'dairy'  # 乳制品
    EGG = 'egg'  # 蛋类
    LEGUME = 'legume'  # 豆类
    NUT = 'nut'  # 坚果
    OIL = 'oil'  # 油脂
    BEVERAGE = "beverage"  # 饮品


class DietaryRestriction(Enum):
    """饮食限制"""
    LOW_SODIUM = 'low_sodium'  # 低盐
    LOW_FAT = 'low_fat'  # 低脂
    LOW_SUGAR = 'low_sugar'  # 低糖
    HIGH_FIBER = "high_fiber"  # 高纤维
    HIGH_PROTEIN = "high_protein"  # 高蛋白
    DIABETIC = "diabetic"  # 糖尿病饮食
    HEART_HEALTHY = "heart_healthy"  # 心脏健康
    SOFT_FOOD = 'soft_food'  # 软食
    LIQUID = "liquid"  # 流质


@dataclass
class NutritionInfo:
    """营养信息"""
    calories: float = 0  # 卡路里(kcal)
    protein: float = 0  # 蛋白质(g)
    carbs: float = 0  # 碳水化合物(g)
    fat: float = 0  # 脂肪(g)
    fiber: float = 0  # 膳食纤维(g)
    sodium: float = 0  # 钠(mg)
    sugar: float = 0  # 糖(g)
    calcium: float = 0  # 钙(mg)
    iron: float = 0  # 铁(mg)
    vitamin_c: float = 0  # 维生素C(mg)

    def to_dict(self) -> Dict[str, float]:
        return {
            'calories': self.calories,
            'protein': self.protein,
            'carbs': self.carbs,
            'fat': self.fat,
            'fiber': self.fiber,
            'sodium': self.sodium,
            'sugar': self.sugar,
            'calcium': self.calcium,
            'iron': self.iron,
            "vitamin_c": self.vitamin_c
        }

    def __add__(self, other: "NutritionInfo") -> 'NutritionInfo':
        return NutritionInfo(
            calories=self.calories + other.calories,
            protein=self.protein + other.protein,
            carbs=self.carbs + other.carbs,
            fat=self.fat + other.fat,
            fiber=self.fiber + other.fiber,
            sodium=self.sodium + other.sodium,
            sugar=self.sugar + other.sugar,
            calcium=self.calcium + other.calcium,
            iron=self.iron + other.iron,
            vitamin_c=self.vitamin_c + other.vitamin_c
        )


# ==================== 食物数据库 ====================

@dataclass
class FoodItem:
    """食物条目"""
    food_id: str
    name: str
    category: FoodCategory
    nutrition_per_100g: NutritionInfo
    serving_size: int = 100  # 标准份量(g)
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'food_id': self.food_id,
            'name': self.name,
            "category": self.category.value,
            "nutrition_per_100g": self.nutrition_per_100g.to_dict(),
            "serving_size": self.serving_size,
            "description": self.description,
            'tags': self.tags
        }


class FoodDatabase:
    """食物数据库"""

    def __init__(self):
        self.foods: Dict[str, FoodItem] = {}
        self._init_food_database()

    def _init_food_database(self):
        """初始化食物数据库"""
        foods = [
            # 主食
            FoodItem('food_rice', '白米饭', FoodCategory.GRAIN,
                     NutritionInfo(calories=116, protein=2.6, carbs=25.9, fat=0.3, fiber=0.3, sodium=1),
                     150, '蒸熟的白米饭', ['主食', '碳水']),
            FoodItem('food_noodles', '面条', FoodCategory.GRAIN,
                     NutritionInfo(calories=137, protein=4.5, carbs=27.5, fat=0.8, fiber=1.2, sodium=3),
                     200, '煮熟的面条', ['主食', '碳水']),
            FoodItem('food_bread', '全麦面包', FoodCategory.GRAIN,
                     NutritionInfo(calories=247, protein=9.0, carbs=43.0, fat=3.5, fiber=6.8, sodium=450),
                     50, '全麦面包片', ['主食', '高纤维']),
            FoodItem('food_oatmeal', '燕麦粥', FoodCategory.GRAIN,
                     NutritionInfo(calories=68, protein=2.4, carbs=12.0, fat=1.4, fiber=1.7, sodium=5),
                     250, '煮熟的燕麦粥', ['早餐', '高纤维']),

            # 蔬菜
            FoodItem('food_spinach', '菠菜', FoodCategory.VEGETABLE,
                     NutritionInfo(calories=23, protein=2.9, carbs=3.6, fat=0.4, fiber=2.2, sodium=79, iron=2.7, vitamin_c=28),
                     100, '新鲜菠菜', ['绿叶菜', '高铁']),
            FoodItem('food_tomato', '番茄', FoodCategory.VEGETABLE,
                     NutritionInfo(calories=18, protein=0.9, carbs=3.9, fat=0.2, fiber=1.2, sodium=5, vitamin_c=14),
                     150, '新鲜番茄', ['低卡', '维生素C']),
            FoodItem('food_broccoli', '西兰花', FoodCategory.VEGETABLE,
                     NutritionInfo(calories=34, protein=2.8, carbs=7.0, fat=0.4, fiber=2.6, sodium=33, calcium=47, vitamin_c=89),
                     100, '蒸西兰花', ['高纤维', '维生素C']),
            FoodItem('food_carrot', '胡萝卜', FoodCategory.VEGETABLE,
                     NutritionInfo(calories=41, protein=0.9, carbs=9.6, fat=0.2, fiber=2.8, sodium=69),
                     100, '胡萝卜', ['维生素A', '高纤维']),

            # 肉类
            FoodItem('food_chicken', '鸡胸肉', FoodCategory.MEAT,
                     NutritionInfo(calories=165, protein=31.0, carbs=0, fat=3.6, sodium=74),
                     100, '煮熟鸡胸肉', ['高蛋白', '低脂']),
            FoodItem('food_pork', '瘦猪肉', FoodCategory.MEAT,
                     NutritionInfo(calories=143, protein=21.0, carbs=0, fat=6.0, sodium=62, iron=1.0),
                     100, '煮熟瘦猪肉', ['高蛋白']),
            FoodItem('food_beef', '牛肉', FoodCategory.MEAT,
                     NutritionInfo(calories=250, protein=26.0, carbs=0, fat=15.0, sodium=72, iron=2.6),
                     100, '煮熟牛肉', ['高蛋白', '高铁']),

            # 海鲜
            FoodItem('food_fish', '清蒸鱼', FoodCategory.SEAFOOD,
                     NutritionInfo(calories=96, protein=20.0, carbs=0, fat=1.5, sodium=60),
                     150, '清蒸鲈鱼', ['高蛋白', '低脂', 'DHA']),
            FoodItem('food_shrimp', '虾', FoodCategory.SEAFOOD,
                     NutritionInfo(calories=99, protein=24.0, carbs=0.2, fat=0.3, sodium=111, calcium=70),
                     100, '煮虾', ['高蛋白', '低脂']),

            # 蛋奶
            FoodItem('food_egg', '鸡蛋', FoodCategory.EGG,
                     NutritionInfo(calories=155, protein=13.0, carbs=1.1, fat=11.0, sodium=124, calcium=56),
                     50, '水煮蛋', ['高蛋白', '优质蛋白']),
            FoodItem('food_milk', '牛奶', FoodCategory.DAIRY,
                     NutritionInfo(calories=42, protein=3.4, carbs=5.0, fat=1.0, sodium=44, calcium=125),
                     250, '低脂牛奶', ['高钙', '蛋白质']),
            FoodItem('food_yogurt', '酸奶', FoodCategory.DAIRY,
                     NutritionInfo(calories=59, protein=10.0, carbs=3.6, fat=0.7, sodium=36, calcium=110),
                     150, '无糖酸奶', ['益生菌', '高钙']),

            # 水果
            FoodItem('food_apple', '苹果', FoodCategory.FRUIT,
                     NutritionInfo(calories=52, protein=0.3, carbs=14.0, fat=0.2, fiber=2.4, sodium=1, vitamin_c=5),
                     200, '新鲜苹果', ['低卡', '高纤维']),
            FoodItem('food_banana', '香蕉', FoodCategory.FRUIT,
                     NutritionInfo(calories=89, protein=1.1, carbs=23.0, fat=0.3, fiber=2.6, sodium=1),
                     120, '香蕉', ['能量', '钾']),
            FoodItem('food_orange', '橙子', FoodCategory.FRUIT,
                     NutritionInfo(calories=47, protein=0.9, carbs=12.0, fat=0.1, fiber=2.4, sodium=0, vitamin_c=53),
                     200, '新鲜橙子', ['维生素C', '低卡']),

            # 豆类
            FoodItem('food_tofu', '豆腐', FoodCategory.LEGUME,
                     NutritionInfo(calories=76, protein=8.0, carbs=1.9, fat=4.8, sodium=7, calcium=350),
                     100, '嫩豆腐', ['高蛋白', '高钙', '素食']),
            FoodItem('food_soymilk', '豆浆', FoodCategory.LEGUME,
                     NutritionInfo(calories=33, protein=2.9, carbs=1.8, fat=1.6, sodium=32, calcium=25),
                     250, '无糖豆浆', ['植物蛋白', '素食']),

            # 坚果
            FoodItem('food_walnut', '核桃', FoodCategory.NUT,
                     NutritionInfo(calories=654, protein=15.0, carbs=14.0, fat=65.0, fiber=6.7, sodium=2),
                     30, '核桃仁', ['健脑', "不饱和脂肪"]),
        ]

        for food in foods:
            self.foods[food.food_id] = food

    def search(self, keyword: str, category: FoodCategory = None) -> List[FoodItem]:
        """搜索食物"""
        results = []
        keyword_lower = keyword.lower()

        for food in self.foods.values():
            if category and food.category != category:
                continue

            if (keyword_lower in food.name.lower() or
                keyword_lower in (food.description or "").lower() or
                any(keyword_lower in tag.lower() for tag in food.tags)):
                results.append(food)

        return results

    def get_by_category(self, category: FoodCategory) -> List[FoodItem]:
        """按分类获取食物"""
        return [f for f in self.foods.values() if f.category == category]


# ==================== 饮食记录 ====================

@dataclass
class MealRecord:
    """餐次记录"""
    meal_id: str
    user_id: int
    meal_type: MealType
    date: datetime
    foods: List[Dict[str, Any]]  # {food_id, name, amount_g, nutrition}
    total_nutrition: NutritionInfo
    notes: Optional[str] = None
    photo_url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'meal_id': self.meal_id,
            'meal_type': self.meal_type.value,
            'date': self.date.isoformat(),
            'foods': self.foods,
            "total_nutrition": self.total_nutrition.to_dict(),
            'notes': self.notes,
            'photo_url': self.photo_url
        }


class DietRecordService:
    """饮食记录服务"""

    # 老年人每日推荐摄入量
    DAILY_RECOMMENDATIONS = {
        'calories': {'min': 1500, 'max': 2000, 'unit': 'kcal'},
        'protein': {'min': 50, 'max': 70, 'unit': 'g'},
        'carbs': {'min': 200, 'max': 300, 'unit': 'g'},
        'fat': {'min': 40, 'max': 60, 'unit': 'g'},
        'fiber': {'min': 25, 'max': 30, 'unit': 'g'},
        'sodium': {'min': 0, 'max': 2000, 'unit': 'mg'},
        'calcium': {'min': 1000, 'max': 1200, 'unit': "mg"},
    }

    def __init__(self):
        self.food_db = FoodDatabase()
        self.meals: Dict[str, MealRecord] = {}
        self.user_meals: Dict[int, List[str]] = defaultdict(list)

    def record_meal(
        self,
        user_id: int,
        meal_type: MealType,
        foods: List[Dict[str, Any]],  # {food_id, amount_g}
        date: datetime = None,
        notes: str = None,
        photo_url: str = None
    ) -> MealRecord:
        """记录一餐"""
        meal_id = f"meal_{user_id}_{int(datetime.now().timestamp())}"

        # 计算营养总量
        total_nutrition = NutritionInfo()
        food_details = []

        for food_entry in foods:
            food_id = food_entry.get('food_id')
            amount_g = food_entry.get('amount_g', 100)

            food = self.food_db.foods.get(food_id)
            if not food:
                continue

            # 按比例计算营养
            ratio = amount_g / 100
            food_nutrition = NutritionInfo(
                calories=food.nutrition_per_100g.calories * ratio,
                protein=food.nutrition_per_100g.protein * ratio,
                carbs=food.nutrition_per_100g.carbs * ratio,
                fat=food.nutrition_per_100g.fat * ratio,
                fiber=food.nutrition_per_100g.fiber * ratio,
                sodium=food.nutrition_per_100g.sodium * ratio,
                sugar=food.nutrition_per_100g.sugar * ratio,
                calcium=food.nutrition_per_100g.calcium * ratio,
                iron=food.nutrition_per_100g.iron * ratio,
                vitamin_c=food.nutrition_per_100g.vitamin_c * ratio
            )

            total_nutrition = total_nutrition + food_nutrition

            food_details.append({
                'food_id': food_id,
                'name': food.name,
                'amount_g': amount_g,
                "nutrition": food_nutrition.to_dict()
            })

        meal = MealRecord(
            meal_id=meal_id,
            user_id=user_id,
            meal_type=meal_type,
            date=date or datetime.now(),
            foods=food_details,
            total_nutrition=total_nutrition,
            notes=notes,
            photo_url=photo_url
        )

        self.meals[meal_id] = meal
        self.user_meals[user_id].append(meal_id)

        return meal

    def get_daily_summary(self, user_id: int, date: datetime = None) -> Dict[str, Any]:
        """获取每日营养摄入汇总"""
        if date is None:
            date = datetime.now()

        date_str = date.strftime("%Y-%m-%d")
        meal_ids = self.user_meals.get(user_id, [])

        daily_meals = []
        total_nutrition = NutritionInfo()

        for meal_id in meal_ids:
            meal = self.meals.get(meal_id)
            if meal and meal.date.strftime('%Y-%m-%d') == date_str:
                daily_meals.append(meal)
                total_nutrition = total_nutrition + meal.total_nutrition

        # 与推荐量比较
        comparisons = {}
        for nutrient, rec in self.DAILY_RECOMMENDATIONS.items():
            value = getattr(total_nutrition, nutrient, 0)
            status = 'normal'
            if value < rec['min']:
                status = 'low'
            elif value > rec['max']:
                status = 'high'

            comparisons[nutrient] = {
                'current': round(value, 1),
                'recommended_min': rec['min'],
                'recommended_max': rec['max'],
                'unit': rec['unit'],
                'status': status,
                'percentage': round(value / rec['max'] * 100, 1)
            }

        return {
            'date': date_str,
            'meals': [m.to_dict() for m in daily_meals],
            "meal_count": len(daily_meals),
            "total_nutrition": total_nutrition.to_dict(),
            "comparisons": comparisons
        }

    def get_weekly_analysis(self, user_id: int) -> Dict[str, Any]:
        """获取每周营养分析"""
        analysis = []

        for i in range(7):
            date = datetime.now() - timedelta(days=i)
            daily = self.get_daily_summary(user_id, date)
            analysis.append({
                'date': daily['date'],
                'calories': daily["total_nutrition"]['calories'],
                'protein': daily["total_nutrition"]['protein'],
                'meal_count': daily['meal_count']
            })

        # 计算平均值
        avg_calories = sum(d['calories'] for d in analysis) / 7
        avg_protein = sum(d['protein'] for d in analysis) / 7

        return {
            'daily_data': analysis,
            'averages': {
                'calories': round(avg_calories, 1),
                "protein": round(avg_protein, 1)
            },
            "recommendations": self._generate_recommendations(avg_calories, avg_protein)
        }

    def _generate_recommendations(self, avg_calories: float, avg_protein: float) -> List[str]:
        """生成饮食建议"""
        recommendations = []

        if avg_calories < 1500:
            recommendations.append("每日热量摄入偏低，建议适当增加主食和优质蛋白摄入")
        elif avg_calories > 2000:
            recommendations.append("每日热量摄入偏高，建议减少高油高糖食物")

        if avg_protein < 50:
            recommendations.append("蛋白质摄入不足，建议多吃鱼、蛋、豆制品")

        if not recommendations:
            recommendations.append("您的饮食营养均衡，请继续保持！")

        return recommendations


# ==================== 食谱推荐 ====================

@dataclass
class Recipe:
    """食谱"""
    recipe_id: str
    name: str
    category: str  # breakfast/lunch/dinner/soup/porridge
    description: str
    ingredients: List[Dict[str, Any]]  # {food_id, name, amount}
    steps: List[str]
    prep_time: int  # 准备时间(分钟)
    cook_time: int  # 烹饪时间(分钟)
    servings: int
    nutrition_per_serving: NutritionInfo
    tags: List[str] = field(default_factory=list)
    suitable_for: List[str] = field(default_factory=list)  # 适合人群
    difficulty: str = 'easy'  # easy/medium/hard
    image_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'recipe_id': self.recipe_id,
            'name': self.name,
            "category": self.category,
            "description": self.description,
            "ingredients": self.ingredients,
            'steps': self.steps,
            'prep_time': self.prep_time,
            'cook_time': self.cook_time,
            'servings': self.servings,
            "nutrition_per_serving": self.nutrition_per_serving.to_dict(),
            'tags': self.tags,
            "suitable_for": self.suitable_for,
            'difficulty': self.difficulty,
            'image_url': self.image_url
        }


class RecipeService:
    """食谱服务"""

    def __init__(self):
        self.recipes: Dict[str, Recipe] = {}
        self._init_recipes()

    def _init_recipes(self):
        """初始化食谱库"""
        recipes = [
            Recipe(
                'recipe_001', '小米南瓜粥', 'porridge',
                '养胃暖身的经典早餐粥',
                [
                    {'name': '小米', 'amount': '50g'},
                    {'name': '南瓜', 'amount': '100g'},
                    {'name': '水', 'amount': "适量"}
                ],
                [
                    "小米淘洗干净，浸泡30分钟",
                    "南瓜去皮切小块",
                    "锅中加水烧开，放入小米",
                    "大火煮开后转小火，加入南瓜块",
                    "煮30-40分钟至粘稠即可"
                ],
                10, 40, 2,
                NutritionInfo(calories=150, protein=4, carbs=32, fat=1, fiber=3),
                ['养胃', '易消化', '软食'],
                ['老年人', '消化不好'],
                'easy'
            ),
            Recipe(
                'recipe_002', '清蒸鲈鱼', "lunch",
                "高蛋白低脂肪的健康菜肴",
                [
                    {'name': '鲈鱼', 'amount': '1条约500g'},
                    {'name': '葱姜', 'amount': '适量'},
                    {'name': '蒸鱼豉油', 'amount': "2勺"}
                ],
                [
                    "鲈鱼处理干净，两面划几刀",
                    '鱼身铺上葱姜',
                    "大火蒸8-10分钟",
                    "倒掉蒸出的水，淋上蒸鱼豉油",
                    "撒上葱丝，淋上热油即可"
                ],
                15, 15, 3,
                NutritionInfo(calories=120, protein=22, carbs=2, fat=3, sodium=350),
                ['高蛋白', '低脂', '清淡'],
                ['心血管疾病', '减重'],
                'medium'
            ),
            Recipe(
                'recipe_003', '番茄鸡蛋汤', 'soup',
                '营养美味的家常汤品',
                [
                    {'name': '番茄', 'amount': '2个'},
                    {'name': '鸡蛋', 'amount': '2个'},
                    {'name': '葱花', 'amount': '少许'},
                    {'name': '盐', 'amount': '适量'}
                ],
                [
                    "番茄切块，鸡蛋打散",
                    "锅中放少许油，炒番茄出汁",
                    '加入适量清水煮开',
                    '淋入蛋液，轻轻搅动',
                    '加盐调味，撒葱花出锅'
                ],
                10, 15, 2,
                NutritionInfo(calories=130, protein=9, carbs=8, fat=7, vitamin_c=20),
                ['开胃', '维生素C', '易消化'],
                ['老年人', '食欲不振'],
                'easy'
            ),
            Recipe(
                'recipe_004', '蒜蓉蒸豆腐', 'dinner',
                '软嫩易嚼的高钙素菜',
                [
                    {'name': '嫩豆腐', 'amount': '1盒'},
                    {'name': '蒜末', 'amount': '2勺'},
                    {'name': '生抽', 'amount': '1勺'},
                    {'name': '葱花', 'amount': "少许"}
                ],
                [
                    "豆腐切成厚片，摆入盘中",
                    '蒜末铺在豆腐上',
                    '大火蒸8分钟',
                    '淋上生抽，撒葱花',
                    '淋上热油即可'
                ],
                5, 10, 2,
                NutritionInfo(calories=100, protein=10, carbs=4, fat=6, calcium=400),
                ['高钙', '素食', '软食'],
                ['老年人', '素食者', '骨质疏松'],
                'easy'
            ),
            Recipe(
                'recipe_005', '燕麦牛奶粥', 'breakfast',
                '营养丰富的快手早餐',
                [
                    {'name': '燕麦片', 'amount': '40g'},
                    {'name': '牛奶', 'amount': '250ml'},
                    {'name': '香蕉', 'amount': '半根'},
                    {'name': '蜂蜜', 'amount': '少许'}
                ],
                [
                    "燕麦片放入碗中",
                    "倒入牛奶，微波2分钟或小火煮",
                    '香蕉切片铺在上面',
                    '淋上少许蜂蜜即可'
                ],
                5, 5, 1,
                NutritionInfo(calories=280, protein=12, carbs=45, fat=6, fiber=5, calcium=300),
                ['高纤维', '高钙', '快手'],
                ['老年人', '三高人群'],
                "easy"
            )
        ]

        for recipe in recipes:
            self.recipes[recipe.recipe_id] = recipe

    def search_recipes(
        self,
        keyword: str = None,
        category: str = None,
        tags: List[str] = None,
        suitable_for: str = None
    ) -> List[Recipe]:
        """搜索食谱"""
        results = list(self.recipes.values())

        if keyword:
            keyword_lower = keyword.lower()
            results = [
                r for r in results
                if keyword_lower in r.name.lower() or keyword_lower in r.description.lower()
            ]

        if category:
            results = [r for r in results if r.category == category]

        if tags:
            results = [r for r in results if any(t in r.tags for t in tags)]

        if suitable_for:
            results = [r for r in results if suitable_for in r.suitable_for]

        return results

    def get_daily_menu(self, dietary_restrictions: List[str] = None) -> Dict[str, List[Recipe]]:
        """获取每日推荐菜单"""
        menu = {
            'breakfast': [],
            'lunch': [],
            'dinner': []
        }

        for recipe in self.recipes.values():
            if recipe.category in ['breakfast', 'porridge']:
                menu['breakfast'].append(recipe)
            elif recipe.category in ['lunch']:
                menu['lunch'].append(recipe)
            elif recipe.category in ['dinner', 'soup']:
                menu['dinner'].append(recipe)

        return {
            'breakfast': [r.to_dict() for r in menu['breakfast'][:2]],
            'lunch': [r.to_dict() for r in menu['lunch'][:2]],
            'dinner': [r.to_dict() for r in menu['dinner'][:2]]
        }


# ==================== 统一营养饮食服务 ====================

class NutritionService:
    """统一营养饮食服务"""

    def __init__(self):
        self.diet_record = DietRecordService()
        self.recipe = RecipeService()
        self.food_db = self.diet_record.food_db


# 全局服务实例
nutrition_service = NutritionService()
