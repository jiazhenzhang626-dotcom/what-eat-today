"""八字分析器抽象基类"""

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Optional

from .bazi_types import BaziProfile


class BaseBaziAnalyzer(ABC):
    """八字分析器抽象基类

    所有八字分析实现（静态查表、动态流日修正、AI辅助等）
    必须继承此类并实现 analyze 方法。
    """

    @abstractmethod
    def analyze(self, birth: datetime, query_date: Optional[date] = None) -> BaziProfile:
        """分析八字，返回喜用神画像

        Args:
            birth: 用户的出生日期时间（datetime，包含年月日时分）
            query_date: 查询日期（未来动态版使用，静态实现可忽略此参数）

        Returns:
            BaziProfile: 包含日主、喜用神、忌神及描述的分析结果
        """
        ...
