"""占卜文案相关数据类型"""

from dataclasses import dataclass


@dataclass
class FortuneContext:
    """占卜文案生成所需的上下文信息

    Attributes:
        dish_name: 菜品名称
        constellation: 用户星座
        day_master: 用户日主（如 "甲木"）
        wuxing_tip: 五行调补建议（如 "今日宜补水"）
        flavor_match: 口味匹配简述（如 "你的星座偏爱鲜咸之味"）
    """
    dish_name: str
    constellation: str
    day_master: str
    wuxing_tip: str
    flavor_match: str
