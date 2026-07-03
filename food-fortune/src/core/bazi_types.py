"""八字相关数据类型定义"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class BaziProfile:
    """八字分析结果

    Attributes:
        day_master: 日主，例如 "甲木"、"丙火"
        favorable: 喜用神五行及其权重，如 {"水": 0.9, "木": 0.6}
        unfavorable: 忌神五行及其权重
        description: 可读的分析描述，如 "身弱喜水木"
    """
    day_master: str
    favorable: Dict[str, float] = field(default_factory=dict)
    unfavorable: Dict[str, float] = field(default_factory=dict)
    description: str = ""


if __name__ == "__main__":
    # 简单自测
    profile = BaziProfile(
        day_master="甲木",
        favorable={"水": 0.9, "木": 0.6},
        unfavorable={"金": 0.4},
        description="身弱喜水木"
    )
    print(profile)
