# 🔮 Food Fortune · 占卜美食引擎

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

> 根据你的出生日期，结合**星座口味偏好**和**八字五行调补**，推荐今日最适合吃的 3 道中国菜，附详细做法与占卜文案。

## ✨ 功能特点

- 🔭 **星座口味分析** — 基于 12 星座的性格特征，匹配最适合你的口味偏好
- ☯️ **八字五行调补** — 根据出生日期的日主五行与月令旺衰，推荐五行调和的菜品
- 📖 **详细菜谱** — 每道推荐菜附带完整的配料清单和可操作的烹饪步骤
- 🔮 **占卜文案** — 每道菜配有星座 + 五行的个性化占卜解读，支持 AI 增强
- 🤖 **AI 文案增强（可选）** — 接入 OpenAI 兼容 API，生成独一无二的占卜语；不配置 Key 时自动使用内置模板
- 🎨 **精美终端界面** — 基于 Rich 库的彩色终端输出，视觉体验极佳
- 🔌 **可扩展架构** — 通过抽象基类预留 AI 文案增强和动态八字修正接口

## 🚀 快速开始

### 1. 环境要求

- Python 3.11 或更高版本
- pip

### 2. 安装依赖

```bash
cd food-fortune
pip install -r requirements.txt
```

### 3. 运行

#### 命令行（CLI）

```bash
# 基本用法（必填出生日期）
python src/cli/main.py --birth-date 1995-07-23

# 指定推荐数量
python src/cli/main.py --birth-date 1995-07-23 --top-k 5

# 附加出生时间（未来动态版将使用此参数）
python src/cli/main.py --birth-date 1995-07-23 --birth-time 14:30
```

#### Web 界面

**最简单的方式——双击启动：**

在项目根目录找到 `一键启动.bat`，双击即可启动 Web 服务。脚本会：

- 🔇 静默检查端口占用、自动处理旧服务残留
- 🌐 服务就绪后自动打开浏览器访问占卜页面
- 🪟 关闭命令窗口即可停止服务

启动成功后，你只会看到两行提示：

```
正在为你准备今日食运…
页面已打开，关闭本窗口即可停止服务。
```

> 💡 **遇到端口占用？** 如果 8888 端口被其他程序占用，脚本会提示 `抱歉，8888 端口被其他程序占用了，请关闭占用程序后再试。`——关闭那个程序后重新双击即可。如果是本项目旧服务的残留进程，脚本会静默清理，无需任何操作。

**命令行启动（备选）：**

```bash
python src/web/web.py
```

浏览器访问 **http://127.0.0.1:8888**，在网页中输入出生日期即可获得推荐。

Web 界面功能：
- 🎨 可视化表单输入出生日期（支持日期选择器）
- 📋 展示推荐菜品及完整评分详情
- 📖 每道菜附带配料清单、烹饪步骤、星座文案、五行文案
- 🌐 响应式设计，支持桌面和移动端

首次运行时会自动在项目根目录生成 `config.yaml`，你可以按需编辑。

### 4. 运行测试

```bash
pytest tests/ -v
```

## 📁 项目结构

```
food-fortune/
│
├── data/                            # 知识库（YAML，用户可编辑）
│   ├── recipes.yaml                 # 菜谱数据库（综合，8 道）
│   ├── recipes_sichuan.yaml         # 川菜专辑（20 道）
│   ├── recipes_yue.yaml             # 粤菜专辑（24 道）
│   ├── recipes_su.yaml              # 苏菜专辑（25 道）
│   ├── recipes_zhe.yaml             # 浙菜专辑（24 道）
│   ├── recipes_hui.yaml             # 徽菜专辑（25 道）
│   ├── recipes_xiang.yaml           # 湘菜专辑（24 道）
│   ├── recipes_min.yaml             # 闽菜专辑（24 道）
│   ├── recipes_home.yaml            # 家常菜专辑（25 道）
│   ├── constellation_flavors.yaml   # 星座口味偏好映射（12 星座）
│   └── wuxing_food.yaml             # 五行食物属性（5 行）
│
├── src/                             # 源代码
│   ├── __init__.py
│   │
│   ├── core/                        # 核心领域逻辑
│   │   ├── __init__.py
│   │   ├── bazi_types.py            # 八字数据类型定义
│   │   ├── bazi_analyzer.py         # 八字分析器抽象基类
│   │   ├── constellation.py         # 星座判断与口味向量
│   │   └── static_bazi.py           # 静态八字分析器（查表法）
│   │
│   ├── ai/                          # 文案生成模块
│   │   ├── __init__.py
│   │   ├── fortune_types.py         # 占卜文案数据类型
│   │   ├── fortune_writer.py        # 文案生成器抽象基类
│   │   ├── template_writer.py       # 内置模板文案生成器
│   │   └── openai_writer.py         # AI 文案增强（需 API Key）
│   │
│   ├── orchestrator/                # 评分编排
│   │   ├── __init__.py
│   │   └── scorer.py                # 双维度加权评分器
│   │
│   ├── knowledge/                   # 知识库加载
│   │   ├── __init__.py
│   │   └── loader.py                # 合并加载所有 recipes*.yaml
│   │
│   ├── config/                      # 配置管理
│   │   ├── __init__.py
│   │   ├── loader.py                # 配置加载与自动生成
│   │   └── config.example.yaml      # 配置模板
│   │
│   ├── cli/                         # 命令行入口
│   │   ├── __init__.py
│   │   └── main.py                  # Typer + Rich 终端界面
│   │
│   └── web/                         # Web 界面
│       ├── __init__.py
│       ├── web.py                   # FastAPI 后端（端口 8888）
│       └── templates/
│           ├── __init__.py
│           └── index.html           # 前端页面（响应式设计）
│
├── tests/                           # 测试
│   ├── __init__.py
│   └── test_scorer.py               # 评分器单元测试
│
├── config.yaml                      # 运行时配置（自动生成）
├── requirements.txt                 # Python 依赖
└── README.md                        # 项目文档
```

## 🔧 配置说明

编辑项目根目录的 `config.yaml`：

```yaml
ai:
  provider: openai_compatible
  api_key: ""        # 填入 API Key 以启用 AI 文案增强
  base_url: https://api.openai.com/v1
  model: gpt-3.5-turbo
  enabled: false     # api_key 为空时自动禁用

fortune:
  constellation_weight: 0.5   # 星座口味权重
  bazi_weight: 0.5            # 八字五行权重
```

## 🤖 接入 AI 文案增强（可选）

不配置 AI 也能正常使用——系统会自动使用内置占卜语模板。配置后每道菜将获得 AI 生成的个性化文案。

### 支持的 API 平台

任何兼容 OpenAI Chat Completions 接口的平台均可：

| 平台 | base_url | 获取 Key |
|------|----------|----------|
| OpenAI 官方 | `https://api.openai.com/v1` | [platform.openai.com](https://platform.openai.com) |
| DeepSeek | `https://api.deepseek.com/v1` | [platform.deepseek.com](https://platform.deepseek.com) |
| 阿里百炼 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | [bailian.console.aliyun.com](https://bailian.console.aliyun.com) |
| 其他兼容接口 | 填写对应地址 | — |

### 配置步骤

编辑项目根目录的 `config.yaml`（首次运行后自动生成）：

```yaml
ai:
  provider: openai_compatible
  api_key: "sk-你的API-Key"           # 替换为真实 Key
  base_url: https://api.openai.com/v1  # 或上述任一平台地址
  model: gpt-3.5-turbo                # 模型名
  enabled: true                       # 填了 Key 后自动启用
```

保存后重新运行即可。运行时终端会显示 `[AI] 已启用 AI 文案增强` 提示。

### 成本参考

AI 文案每次调用约消耗 300-500 tokens。以 GPT-3.5-turbo 计（$0.002/1K tokens），每次推荐 3 道菜的成本约 **$0.003**（不到 3 分钱人民币）。DeepSeek 等国产模型价格更低。

### 故障排除

如果 AI 生成失败，系统会自动降级到内置模板文案，并在输出中显示错误原因。常见问题：

- `401 Unauthorized` → API Key 无效，检查 Key 是否正确
- `连接超时` → 网络问题，检查能否访问 API 地址
- `模型不存在` → model 名拼写错误，核对平台支持的模型列表

## 🧩 扩展指南

项目通过抽象基类实现模块解耦，你可以轻松替换以下组件：

- **动态八字分析**：继承 `BaseBaziAnalyzer`，实现 `query_date` 参数的动态流日修正
- **AI 文案增强**：继承 `BaseFortuneWriter`，调用 OpenAI 兼容 API 生成个性化文案
- **Web 界面**：复用 `FoodScorer` 评分器，接入 Flask / FastAPI 等 Web 框架
- **自定义知识库**：编辑 `data/` 下的 YAML 文件，添加更多菜谱和星座数据

## ⚠️ 免责声明

本工具**仅供学习与娱乐**。所有八字分析为极简化的静态查表法，星座口味偏好基于趣味推测，不构成任何形式的命理咨询、饮食建议或商业决策依据。请勿将本工具的分析结果用于任何严肃场合。

八字理论博大精深，本项目的简化算法仅用于满足娱乐需求，如有真正的命理咨询需求，请寻求专业人士。

## 📄 开源协议

MIT License — 欢迎 Fork、修改和贡献！
