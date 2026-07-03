"""FoodScorer 评分器测试"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pytest

# 将项目根目录加入 sys.path
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.core.static_bazi import StaticBaziAnalyzer
from src.knowledge.loader import load_constellation_flavors
from src.orchestrator.scorer import FoodScorer


@pytest.fixture
def scorer() -> FoodScorer:
    """创建评分器实例"""
    analyzer = StaticBaziAnalyzer()
    return FoodScorer(
        constellation_flavor_map=load_constellation_flavors(),
        bazi_analyzer=analyzer,
        constellation_weight=0.5,
        bazi_weight=0.5,
    )


@pytest.fixture
def sample_recipes() -> List[Dict[str, Any]]:
    """构造测试用菜谱数据"""
    return [
        {
            "name": "麻辣火锅",
            "category": "川菜",
            "flavors": ["辣", "麻", "鲜", "咸"],
            "wuxingMatch": ["火", "金"],
            "ingredients": ["辣椒", "花椒", "牛肉"],
            "steps": ["炒底料", "加水烧开", "涮菜"],
            "prepTime": 20,
            "cookTime": 30,
            "constellationMessage": {},
            "wuxingMessage": {},
        },
        {
            "name": "冰糖雪梨",
            "category": "甜品",
            "flavors": ["甜"],
            "wuxingMatch": ["水", "金"],
            "ingredients": ["雪梨", "冰糖"],
            "steps": ["雪梨切块", "加水炖煮", "加冰糖"],
            "prepTime": 5,
            "cookTime": 20,
            "constellationMessage": {},
            "wuxingMessage": {},
        },
        {
            "name": "糖醋排骨",
            "category": "鲁菜",
            "flavors": ["甜", "酸", "鲜"],
            "wuxingMatch": ["木", "土"],
            "ingredients": ["排骨", "糖", "醋"],
            "steps": ["焯水", "油炸", "收汁"],
            "prepTime": 15,
            "cookTime": 25,
            "constellationMessage": {},
            "wuxingMessage": {},
        },
        {
            "name": "清炒时蔬",
            "category": "家常",
            "flavors": ["咸", "鲜"],
            "wuxingMatch": ["木", "水"],
            "ingredients": ["时令蔬菜", "蒜", "盐"],
            "steps": ["热油", "爆蒜", "炒菜"],
            "prepTime": 5,
            "cookTime": 5,
            "constellationMessage": {},
            "wuxingMessage": {},
        },
        {
            "name": "水煮鱼",
            "category": "川菜",
            "flavors": ["辣", "麻", "鲜", "咸"],
            "wuxingMatch": ["火", "水"],
            "ingredients": ["鱼片", "辣椒", "花椒"],
            "steps": ["腌鱼", "炒料", "煮鱼"],
            "prepTime": 20,
            "cookTime": 15,
            "constellationMessage": {},
            "wuxingMessage": {},
        },
    ]


class TestFoodScorer:
    """FoodScorer 测试类"""

    def test_returns_correct_count(
        self, scorer: FoodScorer, sample_recipes: List[Dict[str, Any]]
    ) -> None:
        """测试评分是否返回指定数量的结果"""
        birth = datetime(1995, 7, 23)  # 狮子座，夏天
        results = scorer.score(sample_recipes, birth)

        # 应该返回所有菜品
        assert len(results) == len(sample_recipes)

        # 结果应按总分降序排列
        for i in range(len(results) - 1):
            assert results[i]["scores"]["total"] >= results[i + 1]["scores"]["total"]

        # 每个结果都应有必要的字段
        for r in results:
            assert "name" in r
            assert "scores" in r
            assert "constellation" in r["scores"]
            assert "bazi" in r["scores"]
            assert "total" in r["scores"]
            assert 0 <= r["scores"]["constellation"] <= 1
            assert 0 <= r["scores"]["bazi"] <= 1
            assert 0 <= r["scores"]["total"] <= 1

    def test_scoring_logic_extreme_cases(
        self, scorer: FoodScorer, sample_recipes: List[Dict[str, Any]]
    ) -> None:
        """测试极端菜谱的评分逻辑

        构造两个极端菜谱：
        - "完美匹配"：口味和五行都与用户偏好高度匹配
        - "完全不匹配"：口味和五行都不匹配

        验证前者的得分高于后者。
        """
        birth = datetime(1995, 7, 23)  # 狮子座：爱辣(8)、咸(7)、鲜(7)；夏天=火旺→身强→喜克泄耗

        extreme_recipes = [
            {
                "name": "完美匹配菜",
                "category": "测试",
                "flavors": ["辣", "鲜", "咸"],  # 狮子座最爱
                "wuxingMatch": ["金", "水", "土"],  # 火日主身强喜克泄耗
                "ingredients": [],
                "steps": [],
                "prepTime": 0,
                "cookTime": 0,
                "constellationMessage": {},
                "wuxingMessage": {},
            },
            {
                "name": "完全不匹配菜",
                "category": "测试",
                "flavors": [],  # 没有任何口味匹配
                "wuxingMatch": [],  # 没有五行匹配
                "ingredients": [],
                "steps": [],
                "prepTime": 0,
                "cookTime": 0,
                "constellationMessage": {},
                "wuxingMessage": {},
            },
        ]

        results = scorer.score(extreme_recipes, birth)

        perfect_score = results[0]["scores"]["total"]
        terrible_score = results[1]["scores"]["total"]

        # 完美匹配的得分应该明显高于完全不匹配
        assert perfect_score > terrible_score, (
            f"完美匹配得分({perfect_score:.3f})应高于完全不匹配({terrible_score:.3f})"
        )

        # 完全不匹配的得分应该接近 0
        assert terrible_score < 0.1, (
            f"完全不匹配得分应接近0，实际为 {terrible_score:.3f}"
        )

    def test_top_k_slicing(
        self, scorer: FoodScorer, sample_recipes: List[Dict[str, Any]]
    ) -> None:
        """测试 top-k 截取功能"""
        birth = datetime(1995, 7, 23)
        results = scorer.score(sample_recipes, birth)

        # 取前 2
        top2 = results[:2]
        assert len(top2) == 2

        # 取前 1
        top1 = results[:1]
        assert len(top1) == 1

        # 验证第 1 名总分 >= 第 2 名
        assert results[0]["scores"]["total"] >= results[1]["scores"]["total"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
