"""
营养饮食管理API
提供饮食记录、营养分析、膳食推荐、食谱库等接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.services.nutrition_service import (
    nutrition_service,
    MealType,
    FoodCategory,
    DietaryRestriction
)
from app.core.security import get_current_user

router = APIRouter(prefix="/api/nutrition", tags=["营养饮食"])


# ==================== 请求模型 ====================

class RecordMealRequest(BaseModel):
    """记录餐次请求"""
    meal_type: str = Field(..., description="餐次类型: breakfast/lunch/dinner/snack")
    foods: List[Dict[str, Any]] = Field(..., description="食物列表 [{food_id, amount_g}]")
    date: Optional[datetime] = Field(None, description='日期')
    notes: Optional[str] = Field(None, description='备注')
    photo_url: Optional[str] = Field(None, description="照片URL")


class SearchFoodRequest(BaseModel):
    """搜索食物请求"""
    keyword: str = Field(..., min_length=1, description='搜索关键词')
    category: Optional[str] = Field(None, description="食物分类")


class SearchRecipeRequest(BaseModel):
    """搜索食谱请求"""
    keyword: Optional[str] = Field(None, description="关键词")
    category: Optional[str] = Field(None, description="分类: breakfast/lunch/dinner/soup/porridge")
    tags: Optional[List[str]] = Field(None, description='标签列表')
    suitable_for: Optional[str] = Field(None, description='适合人群')


# ==================== 食物数据库API ====================

@router.get('/foods')
async def get_food_list(
    category: Optional[str] = Query(None, description="食物分类"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取食物列表

    按分类获取食物数据库中的食物
    """
    if category:
        try:
            cat = FoodCategory(category)
            foods = nutrition_service.food_db.get_by_category(cat)
        except ValueError:
            valid_cats = [c.value for c in FoodCategory]
            raise HTTPException(
                status_code=400,
                detail=f"无效的分类，可选: {valid_cats}"
            )
    else:
        foods = list(nutrition_service.food_db.foods.values())

    return {
        'foods': [f.to_dict() for f in foods],
        "count": len(foods)
    }


@router.post("/foods/search")
async def search_foods(
    request: SearchFoodRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    搜索食物

    根据关键词和分类搜索食物
    """
    category = None
    if request.category:
        try:
            category = FoodCategory(request.category)
        except ValueError:
            pass

    foods = nutrition_service.food_db.search(request.keyword, category)

    return {
        'keyword': request.keyword,
        'foods': [f.to_dict() for f in foods],
        'count': len(foods)
    }


@router.get("/foods/{food_id}")
async def get_food_detail(
    food_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取食物详情

    获取单个食物的详细营养信息
    """
    food = nutrition_service.food_db.foods.get(food_id)
    if not food:
        raise HTTPException(status_code=404, detail='食物不存在')

    return {"food": food.to_dict()}


@router.get("/foods/categories/list")
async def get_food_categories(current_user: dict = Depends(get_current_user)):
    """
    获取食物分类列表
    """
    categories = [
        {'value': c.value, 'label': {
            'grain': '谷物',
            'vegetable': '蔬菜',
            'fruit': '水果',
            'meat': '肉类',
            'seafood': '海鲜',
            'dairy': '乳制品',
            'egg': '蛋类',
            'legume': '豆类',
            'nut': '坚果',
            'oil': '油脂',
            'beverage': '饮品'
        }.get(c.value, c.value)}
        for c in FoodCategory
    ]

    return {'categories': categories}


# ==================== 饮食记录API ====================

@router.post("/meals")
async def record_meal(
    request: RecordMealRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    记录餐次

    记录一餐的食物摄入
    """
    user_id = int(current_user['sub'])

    try:
        meal_type = MealType(request.meal_type)
    except ValueError:
        valid_types = [t.value for t in MealType]
        raise HTTPException(
            status_code=400,
            detail=f"无效的餐次类型，可选: {valid_types}"
        )

    meal = nutrition_service.diet_record.record_meal(
        user_id,
        meal_type,
        request.foods,
        request.date,
        request.notes,
        request.photo_url
    )

    return {
        'success': True,
        'meal': meal.to_dict(),
        "message": f"{meal_type.value}记录成功"
    }


@router.get("/meals/today")
async def get_today_meals(current_user: dict = Depends(get_current_user)):
    """
    获取今日饮食记录
    """
    user_id = int(current_user['sub'])

    summary = nutrition_service.diet_record.get_daily_summary(user_id)

    return summary


@router.get("/meals/summary")
async def get_daily_summary(
    date: Optional[str] = Query(None, description="日期 YYYY-MM-DD"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取每日营养摄入汇总

    返回当日所有餐次的营养总量及与推荐量的对比
    """
    user_id = int(current_user['sub'])

    target_date = None
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误，应为YYYY-MM-DD")

    summary = nutrition_service.diet_record.get_daily_summary(user_id, target_date)

    return summary


@router.get("/meals/weekly")
async def get_weekly_analysis(current_user: dict = Depends(get_current_user)):
    """
    获取每周营养分析

    分析过去7天的营养摄入趋势
    """
    user_id = int(current_user['sub'])

    analysis = nutrition_service.diet_record.get_weekly_analysis(user_id)

    return analysis


@router.get("/recommendations/daily")
async def get_daily_recommendations(current_user: dict = Depends(get_current_user)):
    """
    获取每日营养推荐量

    返回老年人每日各营养素的推荐摄入范围
    """
    recommendations = nutrition_service.diet_record.DAILY_RECOMMENDATIONS

    formatted = {}
    for nutrient, rec in recommendations.items():
        formatted[nutrient] = {
            'min': rec['min'],
            'max': rec['max'],
            'unit': rec['unit'],
            'name': {
                'calories': '热量',
                'protein': '蛋白质',
                'carbs': '碳水化合物',
                'fat': '脂肪',
                'fiber': '膳食纤维',
                'sodium': '钠',
                'calcium': "钙"
            }.get(nutrient, nutrient)
        }

    return {"recommendations": formatted}


# ==================== 食谱库API ====================

@router.get("/recipes")
async def get_recipe_list(
    category: Optional[str] = Query(None, description="分类"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取食谱列表
    """
    recipes = nutrition_service.recipe.search_recipes(category=category)

    return {
        'recipes': [r.to_dict() for r in recipes],
        'count': len(recipes)
    }


@router.post("/recipes/search")
async def search_recipes(
    request: SearchRecipeRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    搜索食谱

    根据关键词、分类、标签等搜索食谱
    """
    recipes = nutrition_service.recipe.search_recipes(
        keyword=request.keyword,
        category=request.category,
        tags=request.tags,
        suitable_for=request.suitable_for
    )

    return {
        'recipes': [r.to_dict() for r in recipes],
        'count': len(recipes)
    }


@router.get("/recipes/{recipe_id}")
async def get_recipe_detail(
    recipe_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取食谱详情

    获取完整的食谱信息，包括食材、步骤、营养
    """
    recipe = nutrition_service.recipe.recipes.get(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail='食谱不存在')

    return {"recipe": recipe.to_dict()}


@router.get("/recipes/menu/daily")
async def get_daily_menu(
    dietary_restrictions: Optional[List[str]] = Query(None, description="饮食限制"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取每日推荐菜单

    根据饮食限制推荐早中晚餐
    """
    menu = nutrition_service.recipe.get_daily_menu(dietary_restrictions)

    return {
        'menu': menu,
        'date': datetime.now().strftime("%Y-%m-%d")
    }


@router.get("/recipes/tags")
async def get_recipe_tags(current_user: dict = Depends(get_current_user)):
    """
    获取食谱标签列表
    """
    all_tags = set()
    for recipe in nutrition_service.recipe.recipes.values():
        all_tags.update(recipe.tags)

    return {'tags': sorted(list(all_tags))}


@router.get("/recipes/categories")
async def get_recipe_categories(current_user: dict = Depends(get_current_user)):
    """
    获取食谱分类列表
    """
    categories = [
        {'value': 'breakfast', 'label': '早餐'},
        {'value': 'lunch', 'label': '午餐'},
        {'value': 'dinner', 'label': '晚餐'},
        {'value': 'soup', 'label': '汤品'},
        {'value': 'porridge', 'label': '粥品'}
    ]

    return {"categories": categories}


# ==================== 饮食限制API ====================

@router.get("/dietary-restrictions")
async def get_dietary_restrictions(current_user: dict = Depends(get_current_user)):
    """
    获取饮食限制选项
    """
    restrictions = [
        {'value': r.value, 'label': {
            'low_sodium': '低盐',
            'low_fat': '低脂',
            'low_sugar': '低糖',
            'high_fiber': '高纤维',
            'high_protein': '高蛋白',
            'diabetic': '糖尿病饮食',
            'heart_healthy': '心脏健康',
            'soft_food': '软食',
            'liquid': "流质"
        }.get(r.value, r.value)}
        for r in DietaryRestriction
    ]

    return {"restrictions": restrictions}


# ==================== 营养仪表板API ====================

@router.get("/dashboard")
async def get_nutrition_dashboard(current_user: dict = Depends(get_current_user)):
    """
    获取营养饮食仪表板

    综合展示饮食和营养数据
    """
    user_id = int(current_user['sub'])

    # 今日摘要
    today_summary = nutrition_service.diet_record.get_daily_summary(user_id)

    # 每周分析
    weekly = nutrition_service.diet_record.get_weekly_analysis(user_id)

    # 推荐菜单
    menu = nutrition_service.recipe.get_daily_menu()

    # 营养状况评估
    comparisons = today_summary.get("comparisons", {})
    issues = []
    for nutrient, data in comparisons.items():
        if data.get('status') == 'low':
            issues.append(f'{nutrient}摄入不足')
        elif data.get('status') == "high":
            issues.append(f"{nutrient}摄入过高")

    return {
        'today': {
            'meal_count': today_summary.get("meal_count", 0),
            "total_calories": today_summary.get('total_nutrition', {}).get('calories', 0),
            "nutrition_status": comparisons
        },
        'weekly': {
            "avg_calories": weekly.get('averages', {}).get('calories', 0),
            "avg_protein": weekly.get('averages', {}).get('protein', 0),
            "recommendations": weekly.get("recommendations", [])
        },
        "suggested_menu": menu,
        "health_issues": issues,
        'overall_status': "good" if not issues else "needs_attention"
    }
