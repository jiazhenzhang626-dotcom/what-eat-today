"""AI 文案生成器 —— 调用 OpenAI 兼容 API 生成个性化占卜文案"""

import json
import urllib.request
import urllib.error
from typing import Any, Dict

from .fortune_types import FortuneContext
from .fortune_writer import BaseFortuneWriter


class OpenAIWriter(BaseFortuneWriter):
    """通过 OpenAI 兼容 API 生成占卜文案

    支持 OpenAI 官方 API 及任何兼容接口（如阿里百炼、DeepSeek 等）。

    使用方式:
        writer = OpenAIWriter(config)
        text = writer.write(context)
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化 AI 文案生成器

        Args:
            config: 项目配置字典，需包含 ai 段：
                - ai.api_key: API Key
                - ai.base_url: API 地址（如 https://api.openai.com/v1）
                - ai.model: 模型名（如 gpt-3.5-turbo）
        """
        ai_config = config.get("ai", {})
        self._api_key: str = ai_config.get("api_key", "")
        self._base_url: str = ai_config.get("base_url", "https://api.openai.com/v1").rstrip("/")
        self._model: str = ai_config.get("model", "gpt-3.5-turbo")
        self._timeout: int = int(ai_config.get("timeout", 15))

    def write(self, context: FortuneContext) -> str:
        """调用 AI 生成占卜文案

        Args:
            context: 占卜上下文

        Returns:
            AI 生成的占卜文案；失败时返回降级提示
        """
        if not self._api_key:
            return self._fallback(context)

        prompt = self._build_prompt(context)
        url = f"{self._base_url}/chat/completions"

        body = json.dumps({
            "model": self._model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.9,
            "max_tokens": 400,
        }).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

        req = urllib.request.Request(url, data=body, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            # API 返回错误（如 401 无效 Key、429 限流等）
            error_body = e.read().decode("utf-8", errors="replace")
            try:
                error_msg = json.loads(error_body).get("error", {}).get("message", str(e))
            except Exception:
                error_msg = str(e)
            return self._fallback(context, f"API 错误: {error_msg}")
        except Exception as e:
            # 网络超时等
            return self._fallback(context, f"请求失败: {e}")

        # 提取回复文本
        try:
            ai_text = data["choices"][0]["message"]["content"]
            return ai_text.strip()
        except (KeyError, IndexError, TypeError):
            return self._fallback(context, "AI 返回格式异常")

    def _build_prompt(self, context: FortuneContext) -> str:
        """根据上下文构建提示词"""
        return (
            f"请为我生成一段简短的中文占卜美食文案（150字以内），"
            f"包含以下要素：\n"
            f"- 菜品：{context.dish_name}\n"
            f"- 我的星座：{context.constellation}\n"
            f"- 我的日主：{context.day_master}\n"
            f"- 五行建议：{context.wuxing_tip}\n"
            f"- 口味共鸣：{context.flavor_match}\n"
            f"\n要求：语言温暖有仪式感，带一点神秘色彩，使用 emoji 点缀。"
        )

    def _fallback(self, context: FortuneContext, reason: str = "") -> str:
        """API 调用失败时的降级文案"""
        note = f"\n（AI 生成失败: {reason}）" if reason else ""
        return (
            f"今日{context.constellation}的你，与这道{context.dish_name}有着微妙的缘分。\n"
            f"{context.wuxing_tip}，{context.flavor_match}。\n"
            f"愿美食温暖你的灵魂。{note}"
        )


SYSTEM_PROMPT = """你是一个占卜美食助手，名叫"食神"。你的风格温暖、神秘、有仪式感。
你需要根据用户的星座、八字日主、五行建议和菜品信息，生成一段个性化的占卜美食文案。
文案应控制在 150 字以内，语言优美，包含对用户的星座气质和今日运势的趣味解读。
不要编造健康建议或命理断言，始终保持轻松娱乐的语气。"""
