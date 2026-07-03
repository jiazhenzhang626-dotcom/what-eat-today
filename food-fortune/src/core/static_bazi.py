"""静态八字分析器 —— 基于公历日期的日柱干支计算 + 硬编码喜用神查表"""

from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

from .bazi_analyzer import BaseBaziAnalyzer
from .bazi_types import BaziProfile

# ============================================================
# 天干地支常量
# ============================================================

_HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
_EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 天干 → 五行
_STEM_ELEMENT: Dict[str, str] = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}

# 天干 → 阴阳（备用于未来扩展）
_STEM_YINYANG: Dict[str, str] = {
    "甲": "阳", "乙": "阴",
    "丙": "阳", "丁": "阴",
    "戊": "阳", "己": "阴",
    "庚": "阳", "辛": "阴",
    "壬": "阳", "癸": "阴",
}

# 所有五行
_ALL_WUXING = ["木", "火", "土", "金", "水"]

# ============================================================
# 五行生克关系
# ============================================================
# 生：木生火、火生土、土生金、金生水、水生木
# 克：木克土、土克水、水克火、火克金、金克木

_WUXING_GENERATES: Dict[str, str] = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_WUXING_GENERATED_BY: Dict[str, str] = {"火": "木", "土": "火", "金": "土", "水": "金", "木": "水"}
_WUXING_CONTROLS: Dict[str, str] = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
_WUXING_CONTROLLED_BY: Dict[str, str] = {"土": "木", "水": "土", "火": "水", "金": "火", "木": "金"}


def _date_to_ganzhi(birth_date: date) -> Tuple[str, str]:
    """计算某公历日期对应的日柱干支

    算法：以 1900-01-01 = 甲戌日（干支序号 10）为基准，
    计算天数差后取模得到干支序号。

    Args:
        birth_date: 公历日期

    Returns:
        (天干, 地支) 如 ("甲", "子")
    """
    base_date = date(1900, 1, 1)
    base_ganzhi_index = 10  # 甲戌在60甲子中的序号

    days_diff = (birth_date - base_date).days
    ganzhi_index = (base_ganzhi_index + days_diff) % 60

    gan_index = ganzhi_index % 10
    zhi_index = ganzhi_index % 12

    return _HEAVENLY_STEMS[gan_index], _EARTHLY_BRANCHES[zhi_index]


def _month_to_season_element(month: int) -> str:
    """根据月份返回当令五行

    简化规则：
    - 春（2,3,4月）→ 木旺
    - 夏（5,6,7月）→ 火旺
    - 秋（8,9,10月）→ 金旺
    - 冬（11,12,1月）→ 水旺
    - 四季末（3,6,9,12月）带土气（此处简化为四季取主气）
    """
    if month in (2, 3, 4):
        return "木"
    elif month in (5, 6, 7):
        return "火"
    elif month in (8, 9, 10):
        return "金"
    else:
        return "水"


def _analyze_by_element(day_master_element: str, season_element: str) -> Tuple[Dict[str, float], Dict[str, float], str]:
    """基于日主五行和月令五行分析喜用神

    核心逻辑（扶抑法简化）：
    - 日主五行 == 月令五行 → 身强 → 喜克泄耗
    - 日主五行 != 月令五行 → 身弱 → 喜生扶

    身强时的喜用：官杀（克我）+ 食伤（我生）+ 财（我克）
    身弱时的喜用：印（生我）+ 比劫（同我）

    Returns:
        (favorable, unfavorable, description)
    """
    if day_master_element == season_element:
        # 身强：喜克、泄、耗
        controlling = _WUXING_CONTROLS[day_master_element]  # 官杀（克我）
        generated = _WUXING_GENERATES[day_master_element]   # 食伤（我生）
        draining = _WUXING_CONTROLLED_BY[day_master_element]  # 财（我克）

        favorable = {
            controlling: 0.5,
            generated: 0.8,
            draining: 0.6,
        }
        # 同时自身元素和生我元素为忌
        supporting = _WUXING_GENERATED_BY[day_master_element]
        unfavorable = {
            day_master_element: 0.3,
            supporting: 0.4,
        }
        description = f"身强喜克泄耗，宜{controlling}、{generated}、{draining}"
    else:
        # 身弱：喜生、扶
        supporting = _WUXING_GENERATED_BY[day_master_element]  # 印（生我）
        same = day_master_element  # 比劫（同我）

        favorable = {
            supporting: 0.9,
            same: 0.6,
        }
        # 克我者、我克者、我生者为忌
        controlling = _WUXING_CONTROLS[day_master_element]
        generated = _WUXING_GENERATES[day_master_element]
        draining = _WUXING_CONTROLLED_BY[day_master_element]
        unfavorable = {
            controlling: 0.5,
            generated: 0.3,
            draining: 0.4,
        }
        description = f"身弱喜生扶，宜{supporting}、{same}"

    return favorable, unfavorable, description


class StaticBaziAnalyzer(BaseBaziAnalyzer):
    """静态八字分析器

    使用公历日期计算日柱干支，基于日主五行和月令五行
    通过硬编码的扶抑法查表得出喜用神。
    query_date 参数在本实现中被忽略，供未来动态版使用。
    """

    def analyze(self, birth: datetime, query_date: Optional[date] = None) -> BaziProfile:
        """分析八字，返回喜用神画像

        Args:
            birth: 用户的出生日期时间
            query_date: 查询日期（当前实现忽略此参数）

        Returns:
            BaziProfile: 分析结果
        """
        birth_date = birth.date()
        month = birth_date.month

        # 1. 计算日柱干支
        day_gan, day_zhi = _date_to_ganzhi(birth_date)

        # 2. 日主 = 日柱天干
        day_master_element = _STEM_ELEMENT[day_gan]
        day_master_full = f"{day_gan}{day_master_element}"

        # 3. 确定月令五行
        season_element = _month_to_season_element(month)

        # 4. 扶抑法分析喜用神
        favorable, unfavorable, description = _analyze_by_element(day_master_element, season_element)

        return BaziProfile(
            day_master=day_master_full,
            favorable=favorable,
            unfavorable=unfavorable,
            description=description,
        )


if __name__ == "__main__":
    # 简单自测
    analyzer = StaticBaziAnalyzer()

    for test_date, expected_stem in [
        (datetime(1995, 7, 23), None),
        (datetime(2000, 1, 1), None),
        (datetime(1984, 2, 4), None),
        (datetime(2023, 6, 30), None),
    ]:
        profile = analyzer.analyze(test_date)
        print(f"{test_date.date()} → 日主: {profile.day_master}, {profile.description}")
        print(f"  喜用: {profile.favorable}, 忌: {profile.unfavorable}")
