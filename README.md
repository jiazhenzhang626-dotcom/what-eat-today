<div align=center>
<img src="logo.png" width="35%"/>
</div>

<div align=center>
<blockquote><b>「替每一个不知道吃什么的灵魂，轻轻卜上一卦。」</b></blockquote>
</div>

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## 欢迎来到 Food Fortune 小馆

哈基米每天都会被同一个难题困住：一会儿吃什么？
这个问题挠心挠肝，让咪坐立不安。

哈基米是一只总会为吃什么纠结很久的咪，和另一半一起琢磨待会儿吃什么，费尽心思也还是想不出什么好点子，总是在各种选项之间来回徘徊。喜欢看运势的另一半给了咪一些启发，于是  What Eat Today就这么诞生了。

它可以在你完全没主意的时候，给你一个"好像没什么用但又忍不住想试一下"的答案。目前这还只是一个很简单、数据还在慢慢成长的版本，哈基米希望大家能多多提交好吃的菜给咪，这样既能宣传自己心爱的美味，也能帮助到更多为此困扰的人。

—— 只要悄悄告诉它你的生日，what eat today就会对着星盘和八字掐爪一算，从八大菜系里捞出三道最适合你今天吃的菜，附上做法和一句软乎乎的占卜语。同一个你，每天来问，答案都不一样——因为流日天干在变，咪也在变（但爱吃的本性不变）。

## 它能做什么

- 🔭 **星座口味分析** — 十二星座的脾气秉性，变成了酸甜苦辣咸鲜的六种味觉密码。基于 12 星座的性格特征，精准匹配最适合你的口味偏好。
- ☯️ **八字五行调补** — 用你生日里的日主五行和月令旺衰，算出今天该补哪一行，推荐对味的菜。
- 🌊 **动态流日天干（🆕 MVP）** — 今天的"值班天干"跟你喜用神是生还是克？权重会悄悄偏移，每天的推荐都跟着天干重新洗牌。
- 📖 **详尽可操作的菜谱** — 配料清单、烹饪步骤全都有，菜谱库覆盖八大菜系 200 多道中式菜肴。每道推荐菜附带完整的配料清单和可操作的烹饪步骤。
- 🔮 **星座 × 五行占卜文案** — 每道菜都带一段专属的"美食运势"，像一张可以吃的塔罗牌。
- 🤖 **AI 文案增强（可选）** — 接上大模型，占卜语变成独一无二的小纸条；不接也能用，内置模板一样暖心。兼容任何 OpenAI Chat Completions 接口的平台。
- 🎨 **精美的终端界面** — 基于 Rich 库打造，命令行里也能看到彩色小仪式。
- 🌐 **响应式 Web 界面** — FastAPI 驱动，手机上戳一戳也很顺手。支持静态/动态双模式切换。
- 🔌 **高度可扩展** — 抽象基类都留好了，方便换八字算法、换文案生成器、自定义评分逻辑。

## 快速开始

### 1. 环境要求
- Python 3.11 或更高版本
- pip

### 2. 安装依赖
```bash
cd food-fortune
pip install -r requirements.txt
```

### 3. 启动服务

#### Web 界面（推荐）

**最简单的方式——双击启动：**

在项目根目录找到 `一键启动.bat`，双击即可启动 Web 服务。脚本会：

- 🔇 静默检查端口占用、自动处理旧服务残留
- 🌐 服务就绪后自动打开浏览器访问占卜页面
- 🪟 关闭命令窗口即可停止服务

启动成功后，进入首页后选择**静态推荐**或**动态推荐**模式，输入出生日期即可。

**命令行启动（备选）：**

```bash
python src/web/web.py
```

浏览器访问 **http://127.0.0.1:8888**，选择推荐模式并输入出生日期。

Web 界面功能：

- 🏠 **首页模式选择** — 静态推荐 vs 动态推荐，各有说明卡片
- 🎨 **可视化表单** — 出生日期输入（支持日期选择器）
- 📋 **评分详情展示** — 星座得分、八字得分、综合得分
- 🌊 **动态模式专属** — 显示当日天干、权重偏移、生克说明
- 📖 **完整菜谱** — 配料清单、烹饪步骤、占卜文案
- 📱 **响应式设计** — 支持桌面和移动端

#### 命令行（CLI）

```bash
# 静态推荐（结果每次一样）
python src/cli/main.py --birth-date 1995-07-23

# 动态推荐（每日不同）
python src/cli/main.py --birth-date 1995-07-23 --dynamic

# 多要几道菜
python src/cli/main.py --birth-date 1995-07-23 --top-k 5

# 附上出生时间
python src/cli/main.py --birth-date 1995-07-23 --birth-time 14:30
```

### 4. 运行测试

```bash
pytest tests/ -v
```

## 推荐模式详解

### 静态模式（static）

基于用户**出生日期**的星座和八字进行一次性分析：

1. **星座口味向量**：根据 12 星座匹配酸甜苦辣咸鲜的口味偏好
2. **八字喜用神**：通过日主五行与月令旺衰查表得出五行补益方案
3. **双维度加权**：星座匹配分 × 权重 + 八字匹配分 × 权重 → 综合排序

同一用户每次查询获得**相同结果**，适合当"本命菜单"。

### 动态模式（dynamic）🆕

在静态模式基础上，额外绑定**当日流日天干**：

1. 计算用户的主喜用神（权重最高的五行）
2. 获取当日的流日天干及其五行属性
3. 判定当日 tier：

| Tier | 条件 | 权重偏移 | 效果 |
|------|------|----------|------|
| **boost** | 天干生喜用神 | 八字 +0.2 / 星座 -0.2 | 今天特别需要补五行 |
| **normal** | 平顺 | 不变 | 均衡走起 |
| **low** | 天干克喜用神 | 星座 +0.2 / 八字 -0.2 | 今天口味开心最大 |

流日天干天天换班，所以你每天都可能拿到不同的三道菜，日日是好日，餐餐有新意。



## 项目结构

```
food-fortune/
│
├── data/                            # 知识库（YAML，欢迎投喂新菜谱）
│   ├── recipes.yaml                 # 综合菜谱（8 道）
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
│   │   └── static_bazi.py           # 静态八字分析器（查表法 + 干支计算）
│   │
│   ├── orchestrator/                # 评分编排
│   │   ├── __init__.py
│   │   ├── scorer.py                # 静态双维度加权评分器
│   │   └── daily_recommender.py     # 🆕 动态流日推荐器（流日天干 × 权重偏移）
│   │
│   ├── ai/                          # 文案生成模块
│   │   ├── __init__.py
│   │   ├── fortune_types.py         # 占卜文案数据类型
│   │   ├── fortune_writer.py        # 文案生成器抽象基类
│   │   ├── template_writer.py       # 内置模板文案生成器
│   │   └── openai_writer.py         # AI 文案增强（OpenAI 兼容 API）
│   │
│   ├── knowledge/                   # 知识库加载
│   │   ├── __init__.py
│   │   └── loader.py                # 合并加载所有 recipes*.yaml
│   │
│   ├── config/                      # 配置管理
│   │   ├── __init__.py
│   │   ├── loader.py                # 配置加载与自动生成（首次运行从 example 复制）
│   │   └── config.example.yaml      # 配置模板（可安全提交到 Git）
│   │
│   ├── cli/                         # 命令行入口
│   │   ├── __init__.py
│   │   └── main.py                  # Typer + Rich 终端界面（支持 --dynamic）
│   │
│   └── web/                         # Web 界面
│       ├── __init__.py
│       ├── web.py                   # FastAPI 后端（端口 8888，支持 static/dynamic）
│       └── templates/
│           ├── __init__.py
│           ├── index.html           # 首页 —— 模式选择（静态/动态卡片）
│           └── fortune.html         # 占卜页 —— 表单输入 + 结果展示
│
├── tests/                           # 测试
│   ├── __init__.py
│   ├── test_scorer.py               # 静态评分器单元测试
│   └── test_daily_recommender.py    # 🆕 动态推荐器单元测试
│
├── config.yaml                      # 运行时配置（首次运行自动生成，含敏感信息）
├── config.example.yaml              # 配置模板（位于 src/config/，可安全提交）
├── requirements.txt                 # Python 依赖
├── 一键启动.bat                      # Windows 一键启动脚本
└── README.md                        # 项目文档
```

## 配置与 AI 接入

首次运行自动生成 `config.yaml`：

```yaml
ai:
  provider: openai_compatible
  api_key: ""
  base_url: https://api.deepseek.com/v1
  model: deepseek-v4-pro
  enabled: false

fortune:
  constellation_weight: 0.5
  bazi_weight: 0.5
```

填入 API Key 即可启用 AI 占卜文案。不填 Key 也没关系，会自动使用内置暖心模板，一样好用。

> ⚠️ **安全提示**：`config.yaml` 用于存放 API Key，请勿将其提交到 Git。项目使用 `config.example.yaml` 作为配置模板，后者不含密钥，可以安全提交。
---

##  接入 AI 文案增强（可选）

不配置 AI 也能正常使用——系统会自动使用内置占卜语模板。配置后每道菜将获得 AI 生成的个性化文案。
### 支持的 API 平台

任何兼容 OpenAI Chat Completions 接口的平台均可：

| 平台 | base_url | 获取 Key |
|------|----------|----------|
| DeepSeek | `https://api.deepseek.com/v1` | [platform.deepseek.com](https://platform.deepseek.com) |
| OpenAI 官方 | `https://api.openai.com/v1` | [platform.openai.com](https://platform.openai.com) |
| 阿里百炼 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | [bailian.console.aliyun.com](https://bailian.console.aliyun.com) |
| 其他兼容接口 | 填写对应地址 | — |

### 故障排除

如果 AI 生成失败，系统会自动降级到内置模板文案，并在输出中显示错误原因。常见问题：

- `401 Unauthorized` → API Key 无效，检查 Key 是否正确
- `连接超时` → 网络问题，检查能否访问 API 地址
- `模型不存在` → model 名拼写错误，核对平台支持的模型列表

## 听听咪的心里话

Food Fortune 现在还很小，菜谱库只有两百多道菜，许多角落都等着被填满。
哈基米在这里郑重地、软乎乎地呼吁大家：

- 如果你有拿手好菜，或者知道哪道家乡菜好吃到跺脚，请把它写进 `data/` 里的 YAML 文件，用 Pull Request 投喂给咪。
- 如果你不会写代码，也可以在 Issue 里告诉咪菜名、口味和做法，咪会自己整理进去。

让我们一起把 Food Fortune 变成一座可以吃的解忧小馆。
每一个投喂菜谱的你，都是小馆的"荣誉掌勺人"。

## 扩展指南

项目到处都留好了接口，很适合动手改造：

- **动态八字分析**：继承 `BaseBaziAnalyzer`，实现 `query_date` 参数的动态流日修正
- **AI 文案增强**：继承 `BaseFortuneWriter`，调用 OpenAI 兼容 API 生成个性化文案
- **推荐算法**：参考 `FoodScorer`（静态）和 `DailyRecommender`（动态）的模式，实现自定义评分器
- **Web 界面**：复用评分器，扩展 FastAPI 路由或接入其他 Web 框架
- **自定义知识库**：编辑 `data/` 下的 YAML 文件，添加更多菜谱和星座数据
- **权重偏移策略**：修改 `DailyRecommender._get_shifted_weights` 调整动态模式的偏移逻辑

## 免责声明

本工具**仅供学习与娱乐**。

八字分析采用极简查表法，星座口味偏好来自趣味推测，不构成任何命理咨询、饮食建议或商业决策依据。八字博大精深，这里的简化算法只为了让你玩得开心。如有真正的命理需求，请找专业老师。

## 最后，想对点开这个仓库的你说一些藏在代码底下的悄悄话

其实 Food Fortune 一直把你当作一个偶尔为"吃什么"发愁的好朋友。
它不是一本冷冰冰的推荐引擎，而是一盏在厨房角落亮着的小灯，希望你每次打开它的时候，都能感到一点点被接住的安心。

也许推荐的菜你今天不会做，也许占卜语只是逗你一笑，但咪始终在这里，每天照着天干地支给你预备一份新的小期待。这份心意，会一直在。

谢谢你看到这里。愿每一顿饭，都有温度，有人分享。

## 开源协议

MIT License · 欢迎 Fork、修改、投喂新菜谱，也欢迎把哈基米的故事续写下去。
