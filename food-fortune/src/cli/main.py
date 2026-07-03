"""Food Fortune CLI —— 占卜美食引擎命令行入口"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# 将项目根目录加入 sys.path，确保模块可导入
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.config.loader import load_config
from src.core.static_bazi import StaticBaziAnalyzer
from src.ai.template_writer import TemplateWriter
from src.ai.openai_writer import OpenAIWriter
from src.knowledge.loader import load_recipes, load_constellation_flavors
from src.orchestrator.scorer import FoodScorer

app = typer.Typer(
    name="food-fortune",
    help="[Food Fortune] 占卜美食引擎 -- 根据星座与八字推荐今日最适合你的中国菜",
)
console = Console()


@app.command()
def fortune(
    birth_date: str = typer.Option(
        ...,
        "--birth-date",
        "-b",
        help="出生日期，格式 YYYY-MM-DD（必填）",
    ),
    birth_time: Optional[str] = typer.Option(
        None,
        "--birth-time",
        "-t",
        help="出生时间，格式 HH:MM（可选，静态版暂不影响结果）",
    ),
    gender: Optional[str] = typer.Option(
        None,
        "--gender",
        "-g",
        help="性别（可选，静态版暂不影响结果）",
    ),
    top_k: int = typer.Option(
        3,
        "--top-k",
        "-k",
        help="推荐菜品数量（默认 3）",
        min=1,
        max=10,
    ),
) -> None:
    """根据你的出生日期，推荐今日最适合的中国菜"""

    # ---- 1. 加载配置 ----
    config = load_config()
    ai_enabled = config.get("ai", {}).get("enabled", False)
    constellation_weight = config.get("fortune", {}).get("constellation_weight", 0.5)
    bazi_weight = config.get("fortune", {}).get("bazi_weight", 0.5)

    # ---- 2. 解析出生日期 ----
    try:
        if birth_time:
            birth_dt = datetime.strptime(f"{birth_date} {birth_time}", "%Y-%m-%d %H:%M")
        else:
            birth_dt = datetime.strptime(birth_date, "%Y-%m-%d")
    except ValueError as e:
        console.print(f"[red][X] 日期格式错误: {e}[/red]")
        console.print("[yellow]请使用格式: YYYY-MM-DD（如 1995-07-23）[/yellow]")
        raise typer.Exit(code=1)

    # ---- 3. 加载数据 ----
    recipes_data = load_recipes()
    constellation_flavors = load_constellation_flavors()

    if not recipes_data:
        console.print("[red][X] 未找到菜谱数据，请检查 data/recipes.yaml[/red]")
        raise typer.Exit(code=1)

    # 将菜谱字典转为列表格式（带 name 字段）
    recipe_list = [{"name": k, **v} for k, v in recipes_data.items()]

    # ---- 4. 初始化分析器和评分器 ----
    bazi_analyzer = StaticBaziAnalyzer()

    # 根据配置选择文案生成器
    if ai_enabled:
        fortune_writer = OpenAIWriter(config)
        ai_model = config.get("ai", {}).get("model", "unknown")
        console.print(f"[green][AI] 已启用 AI 文案增强 (model: {ai_model})[/green]")
    else:
        fortune_writer = TemplateWriter()
        console.print(
            "[yellow][i] 未配置 AI 文案增强，当前使用内置占卜语。[/yellow]\n"
            "[yellow]   在 config.yaml 中填入 api_key 即可启用 AI 个性化文案。[/yellow]"
        )

    scorer = FoodScorer(
        constellation_flavor_map=constellation_flavors,
        bazi_analyzer=bazi_analyzer,
        constellation_weight=constellation_weight,
        bazi_weight=bazi_weight,
    )

    # ---- 5. 执行评分 ----
    results = scorer.score(recipe_list, birth_dt)
    top_results = results[:top_k]

    # ---- 6. 输出结果 ----

    # 标题
    title = Text("Food Fortune - 占卜美食引擎", style="bold magenta")
    console.print(Panel(title, border_style="magenta"))

    # 用户信息
    birth_str = birth_dt.strftime("%Y年%m月%d日")
    if birth_time:
        birth_str += f" {birth_dt.strftime('%H:%M')}"
    console.print(f"[Birth] 出生日期: {birth_str}")
    if top_results:
        console.print(f"[Sign] 星座: {top_results[0].get('constellation', '未知')}")
        console.print(f"[BaZi] 日主: {top_results[0].get('day_master', '未知')}")

    console.print()
    console.print(f"[bold]>> 今日推荐 Top {len(top_results)}：[/bold]")
    console.print()

    # 逐道菜展示
    for rank, dish in enumerate(top_results, 1):
        scores = dish.get("scores", {})
        name = dish.get("name", "未知")
        category = dish.get("category", "未知")
        flavors = dish.get("flavors", [])
        wuxing = dish.get("wuxingMatch", [])
        ingredients = dish.get("ingredients", [])
        steps = dish.get("steps", [])
        prep_time = dish.get("prepTime", 0)
        cook_time = dish.get("cookTime", 0)

        # --- 排名面板 ---
        rank_text = Text(f"#{rank}  {name}", style="bold yellow")
        console.print(Panel(rank_text, border_style="yellow"))

        # --- 基本信息表 ---
        info_table = Table(show_header=False, box=None, padding=(0, 2))
        info_table.add_column("key", style="bold cyan", width=10)
        info_table.add_column("value", style="white")
        info_table.add_row("菜系", category)
        info_table.add_row("口味", "、".join(flavors))
        info_table.add_row("五行", "、".join(wuxing))
        info_table.add_row("准备", f"{prep_time} 分钟")
        info_table.add_row("烹饪", f"{cook_time} 分钟")
        console.print(info_table)

        # --- 得分明细 ---
        score_table = Table(title="[Score] 得分明细", box=None)
        score_table.add_column("维度", style="cyan")
        score_table.add_column("得分", style="green", justify="right")
        score_table.add_column("说明", style="dim")
        score_table.add_row(
            "星座口味",
            f"{scores.get('constellation', 0):.3f}",
            dish.get("flavor_match", ""),
        )
        score_table.add_row(
            "八字五行",
            f"{scores.get('bazi', 0):.3f}",
            dish.get("wuxing_tip", ""),
        )
        score_table.add_row(
            "综合得分",
            f"[bold yellow]{scores.get('total', 0):.3f}[/bold yellow]",
            f"权重 {constellation_weight}:{bazi_weight}",
        )
        console.print(score_table)

        # --- 做法步骤 ---
        if steps:
            steps_table = Table(title="[Steps] 做法步骤", box=None)
            steps_table.add_column("步骤", style="cyan", justify="right", width=5)
            steps_table.add_column("内容", style="white")
            for i, step in enumerate(steps, 1):
                steps_table.add_row(str(i), step)
            console.print(steps_table)

        # --- 配料 ---
        if ingredients:
            ing_text = "、".join(ingredients)
            console.print(f"[bold cyan][Ingredient] 配料:[/bold cyan] {ing_text}")

        # --- 占卜文案 ---
        from src.ai.fortune_types import FortuneContext
        context = FortuneContext(
            dish_name=name,
            constellation=dish.get("constellation", "未知"),
            day_master=dish.get("day_master", "未知"),
            wuxing_tip=dish.get("wuxing_tip", ""),
            flavor_match=dish.get("flavor_match", ""),
        )
        fortune_text = fortune_writer.write(context)
        console.print(Panel(fortune_text, border_style="magenta", title="[Fortune] 今日占卜"))

        console.print()  # 空行分隔
        console.print()

    # 免责声明
    console.print(
        "[dim][!] 免责声明：本工具仅供学习与娱乐，所有分析结果由算法自动生成，"
        "不构成任何饮食、医疗或决策建议。请勿用于商业用途。[/dim]"
    )


if __name__ == "__main__":
    app()
