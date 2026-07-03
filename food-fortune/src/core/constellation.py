"""星座判断与口味向量加载"""

from typing import Dict

from ..knowledge.loader import load_constellation_flavors

# 星座日期范围（月、日开始日）
_ZODIAC_DATES = [
    ((3, 21), (4, 19), "白羊座"),
    ((4, 20), (5, 20), "金牛座"),
    ((5, 21), (6, 21), "双子座"),
    ((6, 22), (7, 22), "巨蟹座"),
    ((7, 23), (8, 22), "狮子座"),
    ((8, 23), (9, 22), "处女座"),
    ((9, 23), (10, 23), "天秤座"),
    ((10, 24), (11, 22), "天蝎座"),
    ((11, 23), (12, 21), "射手座"),
    ((12, 22), (1, 19), "摩羯座"),
    ((1, 20), (2, 18), "水瓶座"),
    ((2, 19), (3, 20), "双鱼座"),
]


def get_constellation(month: int, day: int) -> str:
    """根据月日返回星座名称

    Args:
        month: 出生月份（1-12）
        day: 出生日期（1-31）

    Returns:
        星座名称，如 "白羊座"
    """
    for (start_m, start_d), (end_m, end_d), name in _ZODIAC_DATES:
        if (month == start_m and day >= start_d) or (month == end_m and day <= end_d):
            return name
    # 摩羯座跨年情况（12月22日-1月19日）
    return "摩羯座"


def get_flavor_vector(constellation: str) -> Dict[str, float]:
    """获取指定星座的口味偏好向量

    Args:
        constellation: 星座名称

    Returns:
        口味向量字典，如 {"辣": 9.0, "甜": 3.0, "酸": 4.0, "咸": 7.0, "鲜": 6.0}
    """
    data = load_constellation_flavors()
    flavor_data = data.get(constellation, {}).get("flavors", {})
    return {k: float(v) for k, v in flavor_data.items()}


if __name__ == "__main__":
    # 简单自测
    print("7月23日星座:", get_constellation(7, 23))
    print("巨蟹座口味向量:", get_flavor_vector("巨蟹座"))
