"""动态日推荐评分器 —— 结合流日天干的喜用神 × 星座动态推荐

与 FoodScorer（静态双维度评分）互补：
- FoodScorer: 星座口味 + 八字五行 → 固定权重 → 固定结果
- DailyRecommender: 星座口味 + 八字五行 × 动态权重 → 每日变化

核心差异：当日流日天干对用户主喜用神的生克关系产生 boost/normal/low tier，
tier 偏移星座/八字两个维度的权重，使同一用户每天获得不同的推荐排序。

- boost（天干生喜用神）：八字权重 +0.2，星座权重 -0.2 → 优先五行调补
- low（天干克喜用神）：星座权重 +0.2，八字权重 -0.2 → 优先口味享受
- normal：权重不变
"""

import math
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.bazi_analyzer import BaseBaziAnalyzer
from ..core.constellation import get_constellation, get_flavor_vector
from ..core.static_bazi import (
    _date_to_ganzhi,
    _STEM_ELEMENT,
    _WUXING_CONTROLS,
    _WUXING_GENERATES,
)

# 口味维度标准顺序（与 scorer.py 保持一致）
_FLAVOR_KEYS = ["辣", "甜", "酸", "咸", "鲜"]

# 默认权重偏移量
_DEFAULT_WEIGHT_SHIFT = 0.2


class DailyRecommender:
    """动态日推荐评分器

    结合星座口味偏好与八字五行喜用神，并通过当日流日天干对
    主喜用神的生克关系偏移双维度权重，使推荐每日变化。

    用法:
        recommender = DailyRecommender(
            constellation_flavor_map=flavors,
            bazi_analyzer=analyzer,
        )
        results = recommender.score(recipe_list, birth_dt)
    """

    def __init__(
        self,
        constellation_flavor_map: Dict[str, Any],
        bazi_analyzer: BaseBaziAnalyzer,
        constellation_weight: float = 0.5,
        bazi_weight: float = 0.5,
        weight_shift: float = _DEFAULT_WEIGHT_SHIFT,
    ):
        """初始化动态推荐器

        Args:
            constellation_flavor_map: 星座口味偏好数据
            bazi_analyzer: 八字分析器实例
            constellation_weight: 星座口味匹配权重（默认 0.5）
            bazi_weight: 八字五行匹配权重（默认 0.5）
            weight_shift: tier 权重偏移量（默认 0.2）
        """
        self._constellation_flavor_map = constellation_flavor_map
        self._bazi_analyzer = bazi_analyzer
        self._base_constellation_weight = constellation_weight
        self._base_bazi_weight = bazi_weight
        self._weight_shift = weight_shift

    def score(
        self,
        recipes: List[Dict[str, Any]],
        birth: datetime,
        query_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """对菜谱进行动态评分排序

        Args:
            recipes: 菜谱列表，每项为包含 name, flavors, wuxingMatch 等的字典
            birth: 用户出生日期时间
            query_date: 查询日期（默认今天），用于计算流日天干

        Returns:
            按综合得分降序排列的结果列表
        """
        if query_date is None:
            query_date = date.today()

        # 1. 获取星座和口味向量
        birth_date = birth.date()
        constellation = get_constellation(birth_date.month, birth_date.day)
        user_flavors = get_flavor_vector(constellation)

        # 2. 获取八字喜用神
        bazi_profile = self._bazi_analyzer.analyze(birth, query_date)
        favorable = bazi_profile.favorable

        # 3. 确定主喜用神（权重最高的五行）
        primary_favorable = self._get_primary_favorable(favorable)

        # 4. 计算当日流日天干及其五行
        daily_gan, _ = _date_to_ganzhi(query_date)
        daily_element = _STEM_ELEMENT.get(daily_gan, "")

        # 5. 判定当日全局 tier（基于用户喜用神）
        daily_tier = self._get_daily_tier(
            daily_stem=daily_gan,
            daily_element=daily_element,
            primary_favorable=primary_favorable,
        )

        # 6. 根据 tier 偏移权重
        c_weight, b_weight = self._get_shifted_weights(daily_tier)

        # 7. 生成生克关系的用户可读说明
        daily_explanation = self._build_daily_explanation(
            daily_gan, daily_element, daily_tier, primary_favorable
        )

        # 8. 对每道菜评分
        scored = []
        for dish_dict in recipes:
            name = dish_dict.get("name", "未知菜品")
            dish_flavors_list: List[str] = dish_dict.get("flavors", [])
            dish_wuxing: List[str] = dish_dict.get("wuxingMatch", [])

            # 计算星座口味匹配分（余弦相似度）
            constellation_score = self._calc_constellation_score(
                user_flavors, dish_flavors_list
            )

            # 计算八字五行匹配分（与 FoodScorer 相同的逻辑，无乘数）
            bazi_score = self._calc_bazi_score(favorable, dish_wuxing)

            # 加权总分（使用偏移后的权重）
            total_score = (
                c_weight * constellation_score
                + b_weight * bazi_score
            )

            # 生成口味匹配简述
            flavor_match = self._build_flavor_match(constellation, dish_flavors_list)

            # 五行建议简述
            wuxing_tip = bazi_profile.description

            scored.append({
                **dish_dict,
                "name": name,
                "scores": {
                    "constellation": round(constellation_score, 3),
                    "bazi": round(bazi_score, 3),
                    "total": round(total_score, 3),
                },
                "constellation": constellation,
                "flavor_match": flavor_match,
                "wuxing_tip": wuxing_tip,
                "day_master": bazi_profile.day_master,
                "daily_tier": daily_tier,
                "daily_stem": f"{daily_gan}{daily_element}",
                "daily_explanation": daily_explanation,
                "shifted_weights": {
                    "constellation": round(c_weight, 2),
                    "bazi": round(b_weight, 2),
                },
            })

        # 按总分降序排列
        scored.sort(key=lambda x: x["scores"]["total"], reverse=True)
        return scored

    # ---- Tier 判定 ----

    def _get_primary_favorable(
        self, favorable: Dict[str, float]
    ) -> Optional[str]:
        """从喜用神中取权重最高的五行作为主喜用神"""
        if not favorable:
            return None
        return max(favorable, key=lambda k: favorable[k])

    def _get_daily_tier(
        self,
        daily_stem: str,
        daily_element: str,
        primary_favorable: Optional[str],
        dish_daily_tiers: Optional[Dict[str, List[str]]] = None,
    ) -> str:
        """判定当日 tier

        判定顺序：
        1. 若 dish 有 dailyTiers 覆盖且当日天干在其中 → 使用覆盖 tier
        2. 否则走默认五行生克判定（天干生喜用神→boost，天干克喜用神→low）
        """
        # 1. 检查 dish 级别的 dailyTiers 覆盖
        if dish_daily_tiers and daily_element:
            if daily_element in dish_daily_tiers.get("boost", []):
                return "boost"
            if daily_element in dish_daily_tiers.get("low", []):
                return "low"

        # 2. 若无主喜用神，默认 normal
        if primary_favorable is None or not daily_element:
            return "normal"

        # 3. 五行生克判定
        if _WUXING_GENERATES.get(daily_element) == primary_favorable:
            return "boost"
        if _WUXING_CONTROLS.get(daily_element) == primary_favorable:
            return "low"

        return "normal"

    # ---- 权重偏移 ----

    def _get_shifted_weights(self, tier: str) -> tuple:
        """根据 tier 返回偏移后的 (星座权重, 八字权重)

        boost: 八字权重 +shift, 星座权重 -shift
        low:   星座权重 +shift, 八字权重 -shift
        normal: 不变
        """
        if tier == "boost":
            return (
                max(0.0, self._base_constellation_weight - self._weight_shift),
                min(1.0, self._base_bazi_weight + self._weight_shift),
            )
        elif tier == "low":
            return (
                min(1.0, self._base_constellation_weight + self._weight_shift),
                max(0.0, self._base_bazi_weight - self._weight_shift),
            )
        else:
            return (self._base_constellation_weight, self._base_bazi_weight)

    # ---- 评分计算 ----

    def _calc_constellation_score(
        self, user_flavors: Dict[str, float], dish_flavors: List[str]
    ) -> float:
        """计算星座口味匹配分（余弦相似度）

        与 FoodScorer._calc_constellation_score 逻辑一致。
        """
        dish_vec = [1.0 if k in dish_flavors else 0.0 for k in _FLAVOR_KEYS]
        user_vec = [float(user_flavors.get(k, 0.0)) for k in _FLAVOR_KEYS]

        dot_product = sum(u * d for u, d in zip(user_vec, dish_vec))
        user_norm = math.sqrt(sum(u * u for u in user_vec))
        dish_norm = math.sqrt(sum(d * d for d in dish_vec))

        if user_norm == 0 or dish_norm == 0:
            return 0.0

        return dot_product / (user_norm * dish_norm)

    def _calc_bazi_score(
        self,
        favorable: Dict[str, float],
        dish_wuxing: List[str],
    ) -> float:
        """计算八字五行匹配分

        归一化方式：分母为所有喜用神权重之和，而非只取 top N。
        这意味着只有菜品五行覆盖全部喜用神时才能得满分，
        部分匹配只能得部分分数，让不同菜品之间有更明显的区分度。

        Args:
            favorable: 喜用神权重 {"水": 0.9, "木": 0.6}
            dish_wuxing: 菜品五行标签 ["水", "金"]

        Returns:
            匹配分 [0, 1]
        """
        if not dish_wuxing or not favorable:
            return 0.0

        # 分子：菜品五行中匹配到喜用神的权重之和
        matched = sum(favorable.get(w, 0.0) for w in dish_wuxing)

        # 分母：所有喜用神权重之和（全匹配才满分）
        max_possible = sum(favorable.values())

        if max_possible == 0:
            return 0.0

        return min(matched / max_possible, 1.0)

    # ---- 文案生成 ----

    def _build_daily_explanation(
        self,
        daily_stem: str,
        daily_element: str,
        tier: str,
        primary_favorable: Optional[str],
    ) -> str:
        """生成当日生克关系的用户可读说明"""
        if not daily_stem or not daily_element:
            return ""

        stem_element_str = f"{daily_stem}({daily_element})"

        if tier == "boost":
            return (
                f"今日{stem_element_str}，{daily_element}生{primary_favorable}"
                f"——气场助益你的喜用神，优先五行调补"
            )
        elif tier == "low":
            return (
                f"今日{stem_element_str}，{daily_element}克{primary_favorable}"
                f"——气场压制你的喜用神，优先口味享受"
            )
        else:
            return f"今日{stem_element_str}——平顺之日，随心所食"

    def _build_flavor_match(
        self, constellation: str, dish_flavors: List[str]
    ) -> str:
        """生成口味匹配简述"""
        flavor_text = "、".join(dish_flavors) if dish_flavors else "多种风味"
        return f"{constellation}的味觉偏好与这道菜的{flavor_text}风味形成共鸣"


if __name__ == "__main__":
    # 简单自测
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

    from src.core.static_bazi import StaticBaziAnalyzer
    from src.knowledge.loader import load_constellation_flavors, load_recipes

    analyzer = StaticBaziAnalyzer()
    recommender = DailyRecommender(
        constellation_flavor_map=load_constellation_flavors(),
        bazi_analyzer=analyzer,
    )

    recipes_data = load_recipes()
    recipe_list = [{"name": k, **v} for k, v in recipes_data.items()]

    results = recommender.score(recipe_list, datetime(1995, 7, 23))
    print(f"每日说明: {results[0].get('daily_explanation', '')}")
    print(f"权重偏移: {results[0].get('shifted_weights', {})}")
    for i, r in enumerate(results[:5], 1):
        s = r["scores"]
        print(
            f"{i}. {r['name']:12s} | tier={r.get('daily_tier', '?'):6s} "
            f"| 星座: {s['constellation']:.3f} | 八字: {s['bazi']:.3f} | 综合: {s['total']:.3f}"
        )
