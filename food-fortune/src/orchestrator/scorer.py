"""菜品评分编排器 —— 结合星座口味与八字五行进行双维度加权评分"""

import math
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.bazi_analyzer import BaseBaziAnalyzer
from ..core.constellation import get_constellation, get_flavor_vector

# 口味维度标准顺序
_FLAVOR_KEYS = ["辣", "甜", "酸", "咸", "鲜"]


class FoodScorer:
    """美食评分器

    结合星座口味偏好与八字五行喜用神，对菜谱进行双维度评分。
    星座分使用余弦相似度计算口味匹配度，八字分使用喜用神权重累加。
    """

    def __init__(
        self,
        constellation_flavor_map: Dict[str, Any],
        bazi_analyzer: BaseBaziAnalyzer,
        constellation_weight: float = 0.5,
        bazi_weight: float = 0.5,
    ):
        """初始化评分器

        Args:
            constellation_flavor_map: 星座口味偏好数据
            bazi_analyzer: 八字分析器实例
            constellation_weight: 星座口味匹配权重
            bazi_weight: 八字五行匹配权重
        """
        self._constellation_flavor_map = constellation_flavor_map
        self._bazi_analyzer = bazi_analyzer
        self._constellation_weight = constellation_weight
        self._bazi_weight = bazi_weight

    def score(
        self,
        recipes: List[Dict[str, Any]],
        birth: datetime,
        query_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """对菜谱进行评分排序

        Args:
            recipes: 菜谱列表，每项为包含 name, flavors, wuxingMatch 等的字典
            birth: 用户出生日期时间
            query_date: 查询日期（传递给八字分析器，静态版可忽略）

        Returns:
            按综合得分降序排列的结果列表，每项包含原始菜品数据、各项得分
        """
        # 1. 获取星座和口味向量
        birth_date = birth.date()
        constellation = get_constellation(birth_date.month, birth_date.day)
        user_flavors = get_flavor_vector(constellation)

        # 2. 获取八字喜用神
        bazi_profile = self._bazi_analyzer.analyze(birth, query_date)
        favorable = bazi_profile.favorable

        # 3. 对每道菜评分
        scored = []
        for dish_dict in recipes:
            name = dish_dict.get("name", "未知菜品")
            dish_flavors_list: List[str] = dish_dict.get("flavors", [])
            dish_wuxing: List[str] = dish_dict.get("wuxingMatch", [])

            # 计算星座口味匹配分（余弦相似度）
            constellation_score = self._calc_constellation_score(user_flavors, dish_flavors_list)

            # 计算八字五行匹配分
            bazi_score = self._calc_bazi_score(favorable, dish_wuxing)

            # 加权总分
            total_score = (
                self._constellation_weight * constellation_score
                + self._bazi_weight * bazi_score
            )

            # 生成口味匹配简述
            flavor_match = self._build_flavor_match(constellation, dish_flavors_list)

            # 生成五行建议简述
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
            })

        # 按总分降序排列
        scored.sort(key=lambda x: x["scores"]["total"], reverse=True)
        return scored

    def _calc_constellation_score(
        self, user_flavors: Dict[str, float], dish_flavors: List[str]
    ) -> float:
        """计算星座口味匹配分（余弦相似度）

        Args:
            user_flavors: 用户口味向量 {辣: 9.0, 甜: 3.0, ...}
            dish_flavors: 菜品口味标签列表 ['辣', '麻', '鲜']

        Returns:
            余弦相似度 [0, 1]
        """
        # 将菜品口味标签转为独热向量
        dish_vec = [1.0 if k in dish_flavors else 0.0 for k in _FLAVOR_KEYS]
        user_vec = [float(user_flavors.get(k, 0.0)) for k in _FLAVOR_KEYS]

        # 余弦相似度
        dot_product = sum(u * d for u, d in zip(user_vec, dish_vec))
        user_norm = math.sqrt(sum(u * u for u in user_vec))
        dish_norm = math.sqrt(sum(d * d for d in dish_vec))

        if user_norm == 0 or dish_norm == 0:
            return 0.0

        return dot_product / (user_norm * dish_norm)

    def _calc_bazi_score(
        self, favorable: Dict[str, float], dish_wuxing: List[str]
    ) -> float:
        """计算八字五行匹配分

        Args:
            favorable: 喜用神五行权重 {"水": 0.9, "木": 0.6}
            dish_wuxing: 菜品五行标签 ["水", "金"]

        Returns:
            匹配分 [0, 1]，为菜品五行在喜用神中权重的归一化之和
        """
        if not dish_wuxing or not favorable:
            return 0.0

        # 累加每个匹配五行的喜用神权重
        total = sum(favorable.get(w, 0.0) for w in dish_wuxing)

        # 理论最大值：菜品所有五行都匹配且权重之和
        # 取 favorable 中最大的 len(dish_wuxing) 个值的和作为归一化基准
        max_weights = sorted(favorable.values(), reverse=True)
        max_possible = sum(max_weights[: len(dish_wuxing)])

        if max_possible == 0:
            return 0.0

        return min(total / max_possible, 1.0)

    def _build_flavor_match(self, constellation: str, dish_flavors: List[str]) -> str:
        """生成口味匹配简述

        Args:
            constellation: 用户星座
            dish_flavors: 菜品口味标签

        Returns:
            简述文字
        """
        flavor_text = "、".join(dish_flavors)
        return f"{constellation}的味觉偏好与这道菜的{flavor_text}风味形成共鸣"


if __name__ == "__main__":
    # 简单自测
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

    from src.core.static_bazi import StaticBaziAnalyzer
    from src.knowledge.loader import load_constellation_flavors, load_recipes

    analyzer = StaticBaziAnalyzer()
    scorer = FoodScorer(
        constellation_flavor_map=load_constellation_flavors(),
        bazi_analyzer=analyzer,
    )

    recipes_data = load_recipes()
    # 转成列表格式（带 name 字段）
    recipe_list = [{"name": k, **v} for k, v in recipes_data.items()]

    results = scorer.score(recipe_list, datetime(1995, 7, 23))
    for i, r in enumerate(results[:3], 1):
        s = r["scores"]
        print(f"{i}. {r['name']} | 星座: {s['constellation']:.3f} | 八字: {s['bazi']:.3f} | 综合: {s['total']:.3f}")
