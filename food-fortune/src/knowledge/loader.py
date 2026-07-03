"""知识库数据加载工具"""

from pathlib import Path
from typing import Any, Dict

import yaml

# 项目根目录 = src/knowledge/ 的上两级
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _PROJECT_ROOT / "data"


def load_yaml(path: Path) -> Dict[str, Any]:
    """加载 YAML 文件并返回 Python 字典

    Args:
        path: YAML 文件的 Path 对象

    Returns:
        解析后的字典。文件不存在时返回空字典。
    """
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if data is not None else {}


def load_recipes() -> Dict[str, Any]:
    """加载菜谱数据（合并所有 recipes*.yaml 文件）

    遍历 data 目录下所有 recipes*.yaml 文件，合并为一个菜谱字典。
    若菜名重复，后加载的文件覆盖先加载的。

    Returns:
        菜谱字典，key 为菜名，value 为菜品详情
    """
    recipes: Dict[str, Any] = {}
    # 按文件名排序保证加载顺序稳定
    yaml_paths = sorted(_DATA_DIR.glob("recipes*.yaml"))
    for path in yaml_paths:
        data = load_yaml(path)
        if data:
            recipes.update(data)
    return recipes


def load_constellation_flavors() -> Dict[str, Any]:
    """加载星座口味偏好数据

    Returns:
        星座口味字典，key 为星座名
    """
    return load_yaml(_DATA_DIR / "constellation_flavors.yaml")


def load_wuxing_food() -> Dict[str, Any]:
    """加载五行食物数据

    Returns:
        五行食物字典，key 为五行名称
    """
    return load_yaml(_DATA_DIR / "wuxing_food.yaml")


if __name__ == "__main__":
    # 简单自测
    recipes = load_recipes()
    print(f"已加载 {len(recipes)} 道菜品")
    for name in recipes:
        print(f"  - {name}")

    flavors = load_constellation_flavors()
    print(f"已加载 {len(flavors)} 个星座口味数据")

    wuxing = load_wuxing_food()
    print(f"已加载 {len(wuxing)} 个五行数据")
