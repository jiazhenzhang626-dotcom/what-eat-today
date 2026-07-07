"""
Food Fortune Web 界面 -- FastAPI 后端应用

启动方式:
    python src/web/web.py
    浏览器访问 http://127.0.0.1:8888

本模块仅通过导入使用现有核心模块，不修改它们。
"""

import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# 将项目根目录加入 sys.path，确保模块可导入
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from src.config.loader import load_config
from src.core.constellation import get_constellation, get_flavor_vector
from src.core.static_bazi import StaticBaziAnalyzer
from src.ai.fortune_types import FortuneContext
from src.ai.template_writer import TemplateWriter
from src.ai.openai_writer import OpenAIWriter
from src.knowledge.loader import load_recipes, load_constellation_flavors
from src.orchestrator.scorer import FoodScorer
from src.orchestrator.daily_recommender import DailyRecommender

# ---------------------------------------------------------------
# 请求模型
# ---------------------------------------------------------------
class FortuneRequest(BaseModel):
    """占卜请求体"""
    birth_date: str = Field(..., description="出生日期，格式 YYYY-MM-DD")
    birth_time: Optional[str] = Field(None, description="出生时间，格式 HH:MM（可选）")
    gender: Optional[str] = Field(None, description="性别（可选）")
    top_k: int = Field(3, ge=1, le=7, description="推荐菜品数量（1~7）")
    mode: str = Field("static", description="推荐模式：static（静态）或 dynamic（动态）")


# ---------------------------------------------------------------
# 响应模型
# ---------------------------------------------------------------
class ScoreDetail(BaseModel):
    """单道菜的得分明细"""
    constellation: float
    bazi: float
    total: float


class RecipeResult(BaseModel):
    """单道菜的推荐结果"""
    rank: int
    name: str
    category: str
    flavors: List[str]
    wuxing: List[str]
    steps: List[str]
    ingredients: List[str]
    prepTime: int
    cookTime: int
    scores: ScoreDetail
    fortune_text: str
    daily_tier: Optional[str] = None
    daily_stem: Optional[str] = None
    daily_explanation: Optional[str] = None
    shifted_weights: Optional[Dict[str, float]] = None


class UserInfo(BaseModel):
    """用户分析信息"""
    constellation: str
    day_master: str
    wuxing_tip: str
    daily_stem: Optional[str] = None
    daily_tier: Optional[str] = None
    daily_explanation: Optional[str] = None
    shifted_weights: Optional[Dict[str, float]] = None


class FortuneResponse(BaseModel):
    """占卜响应体"""
    user_info: UserInfo
    results: List[RecipeResult]


# ---------------------------------------------------------------
# 应用初始化
# ---------------------------------------------------------------
app = FastAPI(title="Food Fortune")

# 全局实例：在模块加载时初始化，复用整个应用生命周期
_config = load_config()
_recipes_data = load_recipes()
_constellation_flavors = load_constellation_flavors()

# 菜谱字典转列表格式（附带 name 字段）
_recipe_list: List[Dict[str, Any]] = [
    {"name": k, **v} for k, v in _recipes_data.items()
]

# 八字分析器
_bazi_analyzer = StaticBaziAnalyzer()

# 文案生成器：有 API Key 则用 AI，否则用模板
_ai_enabled = _config.get("ai", {}).get("enabled", False)
if _ai_enabled:
    _fortune_writer = OpenAIWriter(_config)
else:
    _fortune_writer = TemplateWriter()

# 评分器
_scorer = FoodScorer(
    constellation_flavor_map=_constellation_flavors,
    bazi_analyzer=_bazi_analyzer,
    constellation_weight=_config.get("fortune", {}).get("constellation_weight", 0.5),
    bazi_weight=_config.get("fortune", {}).get("bazi_weight", 0.5),
)

# 动态推荐器
_daily_recommender = DailyRecommender(
    constellation_flavor_map=_constellation_flavors,
    bazi_analyzer=_bazi_analyzer,
    constellation_weight=_config.get("fortune", {}).get("constellation_weight", 0.5),
    bazi_weight=_config.get("fortune", {}).get("bazi_weight", 0.5),
)


# ---------------------------------------------------------------
# 路由
# ---------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index():
    """返回模式选择首页"""
    template_path = _PROJECT_ROOT / "src" / "web" / "templates" / "index.html"
    if not template_path.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return HTMLResponse(content=template_path.read_text(encoding="utf-8"))


@app.get("/fortune", response_class=HTMLResponse)
async def fortune_page():
    """返回占卜表单页"""
    template_path = _PROJECT_ROOT / "src" / "web" / "templates" / "fortune.html"
    if not template_path.exists():
        raise HTTPException(status_code=404, detail="fortune.html not found")
    return HTMLResponse(content=template_path.read_text(encoding="utf-8"))


@app.post("/api/fortune", response_model=FortuneResponse)
async def fortune(req: FortuneRequest):
    """执行占卜，返回推荐菜品及文案

    Args:
        req: 包含 birth_date、birth_time、gender、top_k、mode 的请求体

    Returns:
        FortuneResponse: 用户分析信息 + 菜品推荐列表
    """
    # 1. 解析出生日期
    try:
        if req.birth_time:
            birth_dt = datetime.strptime(
                f"{req.birth_date} {req.birth_time}", "%Y-%m-%d %H:%M"
            )
        else:
            birth_dt = datetime.strptime(req.birth_date, "%Y-%m-%d")
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"日期格式错误: {e}。请使用 YYYY-MM-DD 格式。",
        )

    if not _recipe_list:
        raise HTTPException(status_code=500, detail="菜谱数据为空，请检查 data/recipes.yaml")

    # 2. 获取用户星座信息
    birth_date_obj = birth_dt.date()
    constellation = get_constellation(birth_date_obj.month, birth_date_obj.day)
    is_dynamic = req.mode == "dynamic"

    # 3. 执行评分（根据 mode 分发）
    top_k = max(1, min(7, req.top_k))
    if is_dynamic:
        scored = _daily_recommender.score(_recipe_list, birth_dt, query_date=date.today())
    else:
        scored = _scorer.score(_recipe_list, birth_dt)
    top_results = scored[: top_k]

    # 4. 构建响应
    results: List[RecipeResult] = []
    for rank, dish in enumerate(top_results, 1):
        scores = dish.get("scores", {})
        dish_name = dish.get("name", "未知")
        constellation_val = dish.get("constellation", constellation)
        day_master = dish.get("day_master", "未知")
        wuxing_tip = dish.get("wuxing_tip", "")
        flavor_match = dish.get("flavor_match", "")

        # 生成占卜文案
        context = FortuneContext(
            dish_name=dish_name,
            constellation=constellation_val,
            day_master=day_master,
            wuxing_tip=wuxing_tip,
            flavor_match=flavor_match,
        )
        fortune_text = _fortune_writer.write(context)

        results.append(RecipeResult(
            rank=rank,
            name=dish_name,
            category=dish.get("category", "未知"),
            flavors=dish.get("flavors", []),
            wuxing=dish.get("wuxingMatch", []),
            steps=dish.get("steps", []),
            ingredients=dish.get("ingredients", []),
            prepTime=dish.get("prepTime", 0),
            cookTime=dish.get("cookTime", 0),
            scores=ScoreDetail(
                constellation=round(scores.get("constellation", 0) * 100, 1),
                bazi=round(scores.get("bazi", 0) * 100, 1),
                total=round(scores.get("total", 0) * 100, 1),
            ),
            fortune_text=fortune_text,
            daily_tier=dish.get("daily_tier") if is_dynamic else None,
            daily_stem=dish.get("daily_stem") if is_dynamic else None,
            daily_explanation=dish.get("daily_explanation") if is_dynamic else None,
            shifted_weights=dish.get("shifted_weights") if is_dynamic else None,
        ))

    user_info = UserInfo(
        constellation=constellation,
        day_master=top_results[0].get("day_master", "未知") if top_results else "未知",
        wuxing_tip=top_results[0].get("wuxing_tip", "") if top_results else "",
        daily_stem=top_results[0].get("daily_stem") if is_dynamic and top_results else None,
        daily_tier=top_results[0].get("daily_tier") if is_dynamic and top_results else None,
        daily_explanation=top_results[0].get("daily_explanation") if is_dynamic and top_results else None,
        shifted_weights=top_results[0].get("shifted_weights") if is_dynamic and top_results else None,
    )

    return FortuneResponse(user_info=user_info, results=results)


# ---------------------------------------------------------------
# 启动入口
# ---------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    print(f"\n  Food Fortune Web 已启动")
    print(f"  访问地址: http://127.0.0.1:8888")
    print(f"  AI 文案: {'已启用' if _ai_enabled else '未启用（使用内置模板）'}\n")

    uvicorn.run(app, host="127.0.0.1", port=8888, log_level="info")
