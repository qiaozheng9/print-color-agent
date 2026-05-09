# 印刷色彩预测与校准智能体

基于大语言模型的印刷色彩管理顾问系统，支持色彩预测、色差计算、校准建议生成、知识库查询和历史记录浏览。

## 技术栈

| 类别 | 技术 |
|------|------|
| LLM 推理 | Xiaomi MiMo-V2.5-Pro |
| 智能体框架 | LangGraph / LangChain |
| 数据库 | SQLite + FTS5 全文搜索 |
| 界面框架 | Streamlit |
| 色彩计算 | NumPy + colour-science |
| 包管理 | uv |

## 功能概览

- **智能对话** — 自然语言提问，AI 自动调用专业工具分析
- **色彩预测** — 输入 CMYK 色值，预测 CIE L\*a\*b\* 色彩值
- **工艺对比** — 同一色值在不同纸张上的色彩表现对比
- **知识库** — FTS5 全文搜索印刷色彩管理专业知识
- **校准历史** — 浏览过往校准记录，参考历史方案

## 快速开始

### 环境要求

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) 包管理器

### 安装

```bash
git clone https://github.com/qiaozheng9/print-color-agent.git
cd print-color-agent
uv sync
```

### 配置

复制环境变量模板并填入 API Key：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```
MIMO_API_KEY=your-api-key-here
MIMO_BASE_URL=https://api.mimo.example.com/v1
MIMO_MODEL=mimo-v2.5-pro
```

### 运行

```bash
streamlit run main.py
```

浏览器访问 `http://localhost:8501`。

## 项目结构

```
main.py                    # Streamlit 入口
frontend/
  display.py               # UI 组件与样式
  pages.py                 # 页面定义
agent/
  core.py                  # LangGraph Agent 创建与调用
  prompts.py               # 系统提示词
  memory.py                # 会话记忆管理
tools/
  color_tools.py           # 色彩预测、色差计算、校准建议
  file_tools.py            # 文件解析
  knowledge_tools.py       # 知识库与历史查询
models/
  converter.py             # CMYK -> Lab 色彩转换引擎
  calibration_rules.py     # 校准规则引擎
  paper_profiles.py        # 纸张类型定义
database/
  schema.sql               # 表结构 + FTS5 虚拟表
  db_manager.py            # 连接管理
  dao.py                   # 数据访问对象
  seed_data.py             # 种子数据
```

## 预置纸张类型

| 纸张 | 克重 | 表面 | 适用场景 |
|------|------|------|---------|
| 铜版纸 | 157g | 光面 | 画册、海报、宣传页 |
| 铜版纸 | 128g | 光面 | 杂志内页、产品目录 |
| 双胶纸 | 80g | 无涂布 | 书刊印刷 |
| 哑粉纸 | 105g | 哑光 | 高端画册、艺术书籍 |

## License

MIT
