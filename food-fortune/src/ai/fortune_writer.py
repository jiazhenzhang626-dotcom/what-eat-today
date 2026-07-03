"""占卜文案生成器抽象基类"""

from abc import ABC, abstractmethod

from .fortune_types import FortuneContext


class BaseFortuneWriter(ABC):
    """占卜文案生成器抽象基类

    所有文案生成实现（模板拼接、AI生成、多模态等）
    必须继承此类并实现 write 方法。
    """

    @abstractmethod
    def write(self, context: FortuneContext) -> str:
        """根据上下文生成占卜文案

        Args:
            context: 包含菜品、星座、日主、五行建议等信息的上下文

        Returns:
            格式化的占卜文案字符串
        """
        ...
