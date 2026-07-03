"""配置加载工具"""

import shutil
import sys
from pathlib import Path
from typing import Any, Dict

import yaml

# 项目根目录 = src/config/ 的上两级
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CONFIG_PATH = _PROJECT_ROOT / "config.yaml"
_CONFIG_EXAMPLE_PATH = _PROJECT_ROOT / "src" / "config" / "config.example.yaml"


def _safe_print(*args, **kwargs) -> None:
    """跨平台安全打印，自动处理 Windows GBK 编码问题"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # 回退：过滤掉无法编码的字符
        import io
        safe_args = []
        for a in args:
            if isinstance(a, str):
                safe_args.append(a.encode(sys.stdout.encoding or "gbk", errors="replace").decode(sys.stdout.encoding or "gbk"))
            else:
                safe_args.append(a)
        print(*safe_args, **kwargs)


def load_config() -> Dict[str, Any]:
    """加载项目配置

    查找项目根目录下的 config.yaml，若不存在则复制
    config.example.yaml 为 config.yaml 并提示用户编辑。

    若 ai.api_key 为空或不存在，则自动设置 ai.enabled = False。

    Returns:
        配置字典
    """
    if not _CONFIG_PATH.exists():
        _copy_example_config()

    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    # 自动判断 AI 是否启用
    ai_config = config.setdefault("ai", {})
    api_key = ai_config.get("api_key", "")
    if not api_key:
        ai_config["enabled"] = False
    else:
        ai_config["enabled"] = True

    # 确保 fortune 配置有默认值
    fortune_config = config.setdefault("fortune", {})
    fortune_config.setdefault("constellation_weight", 0.5)
    fortune_config.setdefault("bazi_weight", 0.5)

    return config


def _copy_example_config() -> None:
    """复制示例配置文件到项目根目录"""
    if not _CONFIG_EXAMPLE_PATH.exists():
        _safe_print(f"[!] 示例配置文件不存在: {_CONFIG_EXAMPLE_PATH}", file=sys.stderr)
        return

    shutil.copy2(_CONFIG_EXAMPLE_PATH, _CONFIG_PATH)
    _safe_print(f"[*] 已创建配置文件: {_CONFIG_PATH}")
    _safe_print("   请根据需要编辑 config.yaml 中的 API Key 等配置。")
    _safe_print("   当前将使用静态文案模式运行。\n")


if __name__ == "__main__":
    config = load_config()
    print(f"AI enabled: {config['ai']['enabled']}")
    print(f"Constellation weight: {config['fortune']['constellation_weight']}")
    print(f"Bazi weight: {config['fortune']['bazi_weight']}")
