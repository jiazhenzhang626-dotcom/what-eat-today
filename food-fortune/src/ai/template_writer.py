"""模板文案生成器 —— 基于 YAML 菜谱中的星座/五行文案模板组装占卜语"""

from typing import Any, Dict

from ..knowledge.loader import load_recipes
from .fortune_types import FortuneContext
from .fortune_writer import BaseFortuneWriter


class TemplateWriter(BaseFortuneWriter):
    """使用内置模板生成占卜文案

    从菜谱 YAML 中读取每道菜的 constellationMessage 和 wuxingMessage，
    结合 FortuneContext 组装成完整的占卜文案。
    不依赖任何外部 API。
    """

    def write(self, context: FortuneContext) -> str:
        """根据上下文生成占卜文案

        Args:
            context: 占卜上下文

        Returns:
            格式化的占卜文案
        """
        # 加载菜谱数据获取该菜的文案模板
        recipes = load_recipes()
        dish_data: Dict[str, Any] = recipes.get(context.dish_name, {})

        # 获取星座文案
        constellation_msgs: Dict[str, str] = dish_data.get("constellationMessage", {})
        constellation_msg = constellation_msgs.get(
            context.constellation,
            f"今日{context.constellation}的你，与这道{context.dish_name}有着奇妙的缘分。"
        )

        # 获取五行文案：取该菜 wuxingMatch 中权重最高的五行对应的文案
        wuxing_msgs: Dict[str, str] = dish_data.get("wuxingMessage", {})
        wuxing_match: list = dish_data.get("wuxingMatch", [])
        wuxing_msg = ""
        if wuxing_match:
            # 使用第一个匹配的五行作为主要文案
            primary_wuxing = wuxing_match[0]
            wuxing_msg = wuxing_msgs.get(
                primary_wuxing,
                f"[WuXing] 五行调和，这道{wuxing_match[0]}行入味的菜品正合你今日所需。"
            )

        # 组装完整文案
        lines = [
            f"-- {context.dish_name}",
            f"-- 今日占卜：",
            f"-- [星座] ：{constellation_msg}",
            f"-- [五行] ：{wuxing_msg}",
            f"-- 今日天机： 日主 {context.day_master} | {context.wuxing_tip}",
            f"-- 口味缘起：{context.flavor_match}",
            "",
            f"* 愿这道菜为你带来今日的好运与满足~",
        ]

        return "\n".join(lines)
