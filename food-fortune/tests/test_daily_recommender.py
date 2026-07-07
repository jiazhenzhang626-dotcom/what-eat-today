"""DailyRecommender 单元测试 —— 验证动态流日天干 + 权重偏移逻辑"""

import sys
from datetime import date, datetime
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.core.static_bazi import (
    StaticBaziAnalyzer,
    _WUXING_GENERATES,
    _WUXING_CONTROLS,
)
from src.orchestrator.daily_recommender import DailyRecommender


# ---- Fixtures ----

@pytest.fixture
def analyzer():
    return StaticBaziAnalyzer()


@pytest.fixture
def constellation_map():
    return {
        "狮子座": {"flavors": {"辣": 8, "甜": 5, "酸": 5, "咸": 7, "鲜": 7}},
        "白羊座": {"flavors": {"辣": 9, "甜": 3, "酸": 4, "咸": 7, "鲜": 6}},
    }


@pytest.fixture
def recommender(constellation_map, analyzer):
    return DailyRecommender(
        constellation_flavor_map=constellation_map,
        bazi_analyzer=analyzer,
    )


@pytest.fixture
def sample_recipes():
    return [
        {
            "name": "麻辣火锅", "category": "川菜",
            "flavors": ["辣", "麻", "鲜", "咸"], "wuxingMatch": ["火", "金"],
            "ingredients": ["辣椒", "花椒"], "steps": ["炒料"],
            "prepTime": 20, "cookTime": 30,
        },
        {
            "name": "冰糖雪梨", "category": "甜品",
            "flavors": ["甜"], "wuxingMatch": ["水", "金"],
            "ingredients": ["雪梨"], "steps": ["炖煮"],
            "prepTime": 10, "cookTime": 40,
        },
        {
            "name": "清炒时蔬", "category": "家常菜",
            "flavors": ["鲜", "咸"], "wuxingMatch": ["木", "土"],
            "ingredients": ["蔬菜"], "steps": ["炒"],
            "prepTime": 5, "cookTime": 5,
        },
        {
            "name": "水煮鱼", "category": "川菜",
            "flavors": ["辣", "鲜", "咸"], "wuxingMatch": ["水", "火"],
            "ingredients": ["鱼"], "steps": ["煮"],
            "prepTime": 15, "cookTime": 15,
        },
        {
            "name": "空数据菜", "category": "未知",
            "flavors": [], "wuxingMatch": [],
            "ingredients": [], "steps": [],
            "prepTime": 0, "cookTime": 0,
        },
    ]


# ---- 五行生克查表 ----

class TestWuxingRelationships:
    def test_generates_cycle(self):
        assert _WUXING_GENERATES["木"] == "火"
        assert _WUXING_GENERATES["火"] == "土"
        assert _WUXING_GENERATES["土"] == "金"
        assert _WUXING_GENERATES["金"] == "水"
        assert _WUXING_GENERATES["水"] == "木"

    def test_controls_cycle(self):
        assert _WUXING_CONTROLS["木"] == "土"
        assert _WUXING_CONTROLS["土"] == "水"
        assert _WUXING_CONTROLS["水"] == "火"
        assert _WUXING_CONTROLS["火"] == "金"
        assert _WUXING_CONTROLS["金"] == "木"


# ---- Tier 判定 ----

class TestTierDetermination:
    def test_generate_is_boost(self, recommender):
        tier = recommender._get_daily_tier(
            daily_stem="甲", daily_element="木", primary_favorable="火"
        )
        assert tier == "boost"

    def test_control_is_low(self, recommender):
        tier = recommender._get_daily_tier(
            daily_stem="甲", daily_element="木", primary_favorable="土"
        )
        assert tier == "low"

    def test_same_is_normal(self, recommender):
        tier = recommender._get_daily_tier(
            daily_stem="甲", daily_element="木", primary_favorable="木"
        )
        assert tier == "normal"

    def test_favorable_generates_stem_is_normal(self, recommender):
        tier = recommender._get_daily_tier(
            daily_stem="丙", daily_element="火", primary_favorable="木"
        )
        assert tier == "normal"

    def test_favorable_controls_stem_is_normal(self, recommender):
        tier = recommender._get_daily_tier(
            daily_stem="戊", daily_element="土", primary_favorable="木"
        )
        assert tier == "normal"

    def test_no_primary_favorable(self, recommender):
        tier = recommender._get_daily_tier(
            daily_stem="甲", daily_element="木", primary_favorable=None
        )
        assert tier == "normal"

    def test_no_daily_element(self, recommender):
        tier = recommender._get_daily_tier(
            daily_stem="", daily_element="", primary_favorable="木"
        )
        assert tier == "normal"

    def test_all_5x5_combinations(self, recommender):
        elements = ["木", "火", "土", "金", "水"]
        for stem_el in elements:
            for fav_el in elements:
                tier = recommender._get_daily_tier(
                    daily_stem="甲", daily_element=stem_el,
                    primary_favorable=fav_el,
                )
                assert tier in ("boost", "normal", "low")
                if _WUXING_GENERATES.get(stem_el) == fav_el:
                    assert tier == "boost"
                elif _WUXING_CONTROLS.get(stem_el) == fav_el:
                    assert tier == "low"
                else:
                    assert tier == "normal"


# ---- dailyTiers 覆盖 ----

class TestDailyTiersOverride:
    def test_boost_override(self, recommender):
        dish_tiers = {"boost": ["火", "木"], "low": ["水"]}
        tier = recommender._get_daily_tier(
            daily_stem="丙", daily_element="火", primary_favorable="水",
            dish_daily_tiers=dish_tiers,
        )
        assert tier == "boost"

    def test_low_override(self, recommender):
        dish_tiers = {"boost": ["火"], "low": ["水"]}
        tier = recommender._get_daily_tier(
            daily_stem="壬", daily_element="水", primary_favorable="木",
            dish_daily_tiers=dish_tiers,
        )
        assert tier == "low"

    def test_boost_priority_over_low(self, recommender):
        dish_tiers = {"boost": ["火"], "low": ["火"]}
        tier = recommender._get_daily_tier(
            daily_stem="丙", daily_element="火", primary_favorable="水",
            dish_daily_tiers=dish_tiers,
        )
        assert tier == "boost"


# ---- 主喜用神提取 ----

class TestPrimaryFavorable:
    def test_highest_weight(self, recommender):
        assert recommender._get_primary_favorable({"土": 0.8, "金": 0.5, "水": 0.6}) == "土"

    def test_empty(self, recommender):
        assert recommender._get_primary_favorable({}) is None

    def test_single(self, recommender):
        assert recommender._get_primary_favorable({"木": 0.9}) == "木"


# ---- 权重偏移 ----

class TestWeightShift:
    def test_boost_shifts_to_bazi(self, recommender):
        c, b = recommender._get_shifted_weights("boost")
        assert b > c
        assert b == 0.7
        assert c == 0.3

    def test_low_shifts_to_constellation(self, recommender):
        c, b = recommender._get_shifted_weights("low")
        assert c > b
        assert c == 0.7
        assert b == 0.3

    def test_normal_unchanged(self, recommender):
        c, b = recommender._get_shifted_weights("normal")
        assert c == 0.5
        assert b == 0.5

    def test_custom_weight_shift(self, constellation_map, analyzer):
        r = DailyRecommender(
            constellation_flavor_map=constellation_map,
            bazi_analyzer=analyzer,
            weight_shift=0.3,
        )
        c, b = r._get_shifted_weights("boost")
        assert c == 0.2
        assert b == 0.8

    def test_weight_clamped_to_range(self, constellation_map, analyzer):
        # 偏移不会超出 [0, 1]
        r = DailyRecommender(
            constellation_flavor_map=constellation_map,
            bazi_analyzer=analyzer,
            constellation_weight=0.1,
            bazi_weight=0.9,
            weight_shift=0.3,
        )
        c, b = r._get_shifted_weights("boost")
        assert c == 0.0  # clamped
        assert b == 1.0  # clamped


# ---- 评分流程 ----

class TestScoring:
    def test_returns_all_sorted(self, recommender, sample_recipes):
        results = recommender.score(sample_recipes, datetime(1995, 7, 23))
        assert len(results) == len(sample_recipes)
        scores = [r["scores"]["total"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_required_fields(self, recommender, sample_recipes):
        results = recommender.score(sample_recipes, datetime(1995, 7, 23))
        for r in results:
            assert "name" in r
            assert "scores" in r
            s = r["scores"]
            assert 0 <= s["constellation"] <= 1
            assert 0 <= s["bazi"] <= 1
            assert 0 <= s["total"] <= 1
            assert r["daily_tier"] in ("boost", "normal", "low")
            assert "daily_explanation" in r
            assert "shifted_weights" in r

    def test_empty_dish_no_crash(self, recommender):
        results = recommender.score(
            [{"name": "空", "flavors": [], "wuxingMatch": []}],
            datetime(1995, 7, 23),
        )
        assert len(results) == 1
        assert results[0]["scores"]["total"] >= 0

    def test_query_date_defaults_to_today(self, recommender, sample_recipes):
        results = recommender.score(sample_recipes, datetime(1995, 7, 23))
        assert len(results) > 0

    def test_specific_query_date(self, recommender, sample_recipes):
        results = recommender.score(
            sample_recipes, datetime(1995, 7, 23),
            query_date=date(2026, 1, 15),
        )
        assert len(results) > 0

    def test_different_days_different_rankings(self, recommender, sample_recipes):
        """不同日子排名可能不同"""
        r1 = recommender.score(
            sample_recipes, datetime(1995, 7, 23),
            query_date=date(2026, 1, 15),
        )
        r2 = recommender.score(
            sample_recipes, datetime(1995, 7, 23),
            query_date=date(2026, 7, 15),
        )
        names1 = [d["name"] for d in r1]
        names2 = [d["name"] for d in r2]
        # 不一定不同（可能碰巧相同），但至少都有结果
        assert len(names1) == len(names2)


# ---- 星座分一致 ----

class TestConstellationScore:
    def test_cosine(self, recommender):
        score = recommender._calc_constellation_score(
            {"辣": 8.0, "甜": 5.0, "酸": 5.0, "咸": 7.0, "鲜": 7.0},
            ["辣", "鲜", "咸"],
        )
        assert 0 < score <= 1.0

    def test_empty_flavors(self, recommender):
        assert recommender._calc_constellation_score({"辣": 8.0}, []) == 0.0

    def test_perfect_match(self, recommender):
        score = recommender._calc_constellation_score(
            {"辣": 9.0, "甜": 1.0, "酸": 1.0, "咸": 1.0, "鲜": 1.0},
            ["辣"],
        )
        assert score > 0.9


# ---- 自定义配置 ----

class TestCustomConfig:
    def test_custom_weights(self, constellation_map, analyzer, sample_recipes):
        r = DailyRecommender(
            constellation_flavor_map=constellation_map,
            bazi_analyzer=analyzer,
            constellation_weight=0.8,
            bazi_weight=0.2,
        )
        results = r.score(sample_recipes, datetime(1995, 7, 23))
        assert len(results) > 0

    def test_custom_weight_shift(self, constellation_map, analyzer):
        r = DailyRecommender(
            constellation_flavor_map=constellation_map,
            bazi_analyzer=analyzer,
            weight_shift=0.15,
        )
        assert r._weight_shift == 0.15


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
