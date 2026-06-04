# PaperInsight

AI 驱动的科学论文筛选与价值评估工具。

```
PDF → Markdown 转换 → 章节提取 → LLM 深度分析 → 评分 → 排名与阅读建议
```

## 安装

```bash
# 克隆项目
git clone https://github.com/weiletao/paper-insight.git
cd paper-insight

# 安装依赖（需要 Python 3.11+ 和 uv）
uv sync
```

## 配置

编辑 `config/config.yaml`，配置 LLM 接口：

```yaml
model:
  provider: openai-compatible
  base_url: "https://your-llm-api-endpoint"
  api_key: "your-api-key"
  model_name: "your-model-name"
  temperature: 0.1
  max_tokens: 8000

converter:
  provider: mineru
```

> **前置依赖：MinerU** — PDF 转 Markdown 需要安装 [mineru-open-api](https://github.com/opendatalab/MinerU) 工具。
>
> ```bash
> # 推荐：使用 npm 安装（需要 Node.js 18+）
> npm install -g mineru-open-api
>
> # 或：使用 uv 安装工具
> uv tool install mineru-open-api
> ```
>
> 验证安装：`mineru-open-api --help` 能正常输出帮助即表示安装成功。

## 用法

### 单篇论文分析

```bash
uv run paper-insight review single paper.pdf
uv run paper-insight review single paper.pdf -o outputs
```

输出：
- `outputs/paper_name/review.md` — 深度评审报告
- `outputs/paper_name/score.json` — 结构化评分

### 批量论文分析

```bash
uv run paper-insight review batch ./papers
uv run paper-insight review batch ./papers -o outputs --force -w 4
```

输出：
- `outputs/paper_name/review.md` — 每篇论文的评审报告
- `outputs/paper_name/score.json` — 每篇论文的评分
- `outputs/ranking.md` — 论文排名（含星级评价）
- `outputs/ranking.csv` — 可导入表格软件的排名数据
- `outputs/reading-roadmap.md` — AI 生成的阅读路线图

### 命令选项

| 选项 | 说明 |
|------|------|
| `-o, --output` | 输出目录（默认 `outputs`） |
| `-f, --force` | 强制重新分析（忽略缓存） |
| `-w, --workers` | 并发工作线程数（默认 4） |

### PDF 转 Markdown（单独使用）

```bash
uv run paper-insight convert paper.pdf -o outputs
```

## 评分体系

| 维度 | 说明 | 范围 |
|------|------|------|
| problem_value | 问题的重要性和清晰度 | 1-10 |
| innovation | 方法的创新性程度 | 1-10 |
| technical_depth | 技术贡献的严谨性和深度 | 1-10 |
| experiment_quality | 实验验证的质量和可信度 | 1-10 |
| academic_impact | 对学术社区的潜在影响力 | 1-10 |
| water_paper_index | 水论文嫌疑程度 | 1-10 |

综合评分 = (5 项正向维度均值) - (水论文指数 / 10)

## 星级标准

| 星级 | 综合分 | 说明 |
|------|--------|------|
| ★★★★★ | >= 8.0 | 必读 |
| ★★★★ | >= 6.5 | 值得精读 |
| ★★★ | >= 5.0 | 可选择阅读 |
| ★★ | >= 3.5 | 了解即可 |
| ★ | < 3.5 | 不建议投入时间 |

## 缓存机制

已分析的论文默认跳过（检查 `outputs/paper_name/review.md` 是否存在）。使用 `--force` 强制重新分析。

## 项目结构

```
paper-insight/
├── config/
│   └── config.yaml           # LLM 和转换器配置
├── prompts/
│   └── deep_review.md        # 论文评审提示词模板
├── src/paper_insight/
│   ├── main.py               # CLI 入口
│   ├── cli/
│   │   ├── convert.py        # convert 命令
│   │   └── review.py         # review 命令（single / batch）
│   ├── converters/
│   │   ├── base.py           # DocumentConverter 抽象接口
│   │   └── mineru.py         # MinerU 转换器
│   ├── providers/
│   │   ├── base.py           # LLMProvider 抽象接口
│   │   ├── openai_provider.py # OpenAI 兼容接口
│   │   └── factory.py        # Provider 工厂
│   ├── extractors/
│   │   └── paper_section_extractor.py  # 章节提取器
│   ├── evaluators/
│   │   ├── base.py           # Evaluator 抽象接口
│   │   └── paper_reviewer.py # 论文评审器
│   ├── ranking/
│   │   ├── scorer.py         # 评分数据模型
│   │   ├── ranker.py         # 排名生成器
│   │   └── roadmap.py        # 阅读路线图生成器
│   ├── config/
│   │   └── settings.py       # 配置加载
│   └── utils/
│       ├── logger.py         # 日志
│       └── prompt_loader.py  # 提示词加载
└── outputs/                   # 分析输出（gitignored）
```
