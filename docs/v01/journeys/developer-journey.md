# Paper Agent 开发者旅程

**Version:** v01
**Status:** Draft
**Last Updated:** 2026-03-12

## 文档说明

本文档面向希望理解、扩展或贡献 Paper Agent 的开发者，包括：
- 代码库结构和架构理解
- 开发环境搭建
- 常见开发任务和扩展点
- 测试和调试策略
- 贡献指南

---

## 目标开发者角色

### 角色 1：贡献者（Contributor）
- **目标**：修复 bug、添加功能、改进文档
- **技术要求**：Python 3.10+、CLI 开发经验、基本 LLM 集成知识
- **预期产出**：Pull Request

### 角色 2：扩展开发者（Extender）
- **目标**：为特定需求定制 Paper Agent（如新数据源、新 LLM provider）
- **技术要求**：理解适配器模式、依赖注入
- **预期产出**：自定义模块或插件

### 角色 3：集成开发者（Integrator）
- **目标**：将 Paper Agent 集成到其他系统（如 IDE 插件、Web 服务）
- **技术要求**：理解 CLI 接口、JSON 输出格式
- **预期产出**：集成代码或 API 包装

### 角色 4：架构研究者（Architect）
- **目标**：理解系统设计决策，评估技术选型
- **技术要求**：软件架构、领域驱动设计
- **预期产出**：架构评审或改进建议

---

## 核心开发者旅程

### Journey 1: 理解代码库 - 从架构到实现

**目标**：快速建立对 Paper Agent 架构和代码组织的理解

#### Step 1.1: 阅读架构文档

**推荐阅读顺序**：
1. [README.md](../../README.md) - 了解项目定位和用户视角
2. [requirement.md](./requirement.md) - 理解需求和目标用户
3. [design.md](./design.md) - 理解技术架构和设计决策
4. [spec.md](./spec.md) - 理解功能规格和行为定义
5. [feature.md](./feature.md) - 理解功能视图

**关键架构概念**：
- **CLI-first 设计**：所有功能通过命令行暴露
- **分层架构**：CLI Layer → Application Layer → Domain Services → Infrastructure
- **适配器模式**：SourceAdapter、LLMProvider、StorageLayer 等抽象
- **本地优先**：SQLite 存储，文件输出，离线可用

#### Step 1.2: 探索代码结构

```
paper_agent/
├── cli/                    # CLI 层
│   ├── app.py             # Typer 命令定义
│   ├── console.py         # Rich 输出格式化
│   └── shell.py           # 交互式 REPL
├── app/                    # 应用层
│   ├── config_manager.py  # 配置管理
│   └── context.py         # 依赖注入容器
├── domain/                 # 领域层
│   ├── models/            # 领域模型
│   │   ├── paper.py       # Paper 实体
│   │   ├── digest.py      # Digest 聚合
│   │   ├── collection.py  # Collection 记录
│   │   └── ...
│   ├── exceptions.py      # 领域异常
│   └── policies/          # 业务规则
├── services/               # 领域服务
│   ├── collection_manager.py  # 论文收集
│   ├── filtering_manager.py   # 语义过滤
│   ├── search_engine.py       # 搜索引擎
│   └── digest_generator.py    # Digest 生成
├── infra/                  # 基础设施层
│   ├── sources/           # 数据源适配器
│   │   └── arxiv_adapter.py
│   ├── llm/               # LLM 提供商
│   │   ├── llm_provider.py
│   │   ├── openai_provider.py
│   │   └── anthropic_provider.py
│   └── storage/           # 存储层
│       └── sqlite_storage.py
└── contracts/              # 契约和 schema
    └── json_schema/
```

**关键文件说明**：

| 文件 | 职责 | 关键类/函数 |
|------|------|------------|
| `cli/app.py` | CLI 命令入口 | `init`, `collect`, `digest`, `search`, `show`, `stats` |
| `app/context.py` | 依赖注入 | `AppContext` |
| `domain/models/paper.py` | Paper 实体 | `Paper`, `PaperMetadata` |
| `services/collection_manager.py` | 收集逻辑 | `CollectionManager.collect_from_arxiv()` |
| `services/filtering_manager.py` | 过滤逻辑 | `FilteringManager.filter_papers()` |
| `infra/storage/sqlite_storage.py` | 数据持久化 | `SQLiteStorage` |

#### Step 1.3: 理解数据流

**收集流程**：
```
CLI (collect)
  → CollectionManager.collect_from_arxiv()
    → ArxivAdapter.fetch_papers()
      → SQLiteStorage.save_paper()
  → FilteringManager.filter_papers()
    → LLMProvider.score_relevance()
      → SQLiteStorage.update_paper()
```

**Digest 生成流程**：
```
CLI (digest)
  → DigestGenerator.generate_daily_digest()
    → SQLiteStorage.get_papers_by_date()
    → 按 relevance_score 分组（high/supplemental）
    → 返回 Digest 对象
  → Console.print_paper_table()
```

**搜索流程**：
```
CLI (search)
  → SearchEngine.search()
    → SQLiteStorage.search_papers() (FTS5)
    → 返回 QueryResult 对象
  → Console.print_paper_table()
```

---

### Journey 2: 搭建开发环境

**目标**：配置本地开发环境，能够运行和调试代码

#### Step 2.1: 克隆和安装依赖

```bash
# 克隆仓库
git clone <repo-url>
cd paper_agent

# 使用 Poetry 安装依赖（推荐）
poetry install

# 或使用 pip
pip install -e .
```

#### Step 2.2: 配置开发工具

**推荐工具**：
- **IDE**: VS Code / PyCharm
- **Linter**: ruff
- **Formatter**: black
- **Type Checker**: mypy
- **测试**: pytest

**VS Code 配置示例** (`.vscode/settings.json`):
```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false
}
```

#### Step 2.3: 运行开发版本

```bash
# 使用 Poetry
poetry run paper-agent --help

# 或激活虚拟环境
poetry shell
paper-agent --help

# 或使用 pip editable install
pip install -e .
paper-agent --help
```

#### Step 2.4: 配置测试环境

```bash
# 创建测试配置
export PAPER_AGENT_CONFIG_PATH=~/.paper-agent-test/config.yaml
paper-agent init --provider openai --api-key "test-key"

# 运行测试
poetry run pytest tests/

# 运行特定测试
poetry run pytest tests/unit/test_storage.py -v
```

---

### Journey 3: 常见开发任务

#### 任务 3.1: 添加新的 arXiv 分类支持

**场景**：用户想收集 `physics.comp-ph` 分类的论文

**修改位置**：
- `infra/sources/arxiv_adapter.py`

**步骤**：
1. 检查 arXiv API 支持的分类列表
2. 无需代码修改，直接在配置中添加：
   ```bash
   paper-agent init --sources "cs.AI, cs.LG, physics.comp-ph"
   ```

**验证**：
```bash
paper-agent collect -d 7 --debug
```

#### 任务 3.2: 添加新的 LLM Provider

**场景**：支持 Azure OpenAI 或本地 LLM

**修改位置**：
- `infra/llm/` 目录
- 创建新文件：`azure_openai_provider.py`

**实现步骤**：

1. 创建新的 Provider 类：

```python
# infra/llm/azure_openai_provider.py
from paper_agent.infra.llm.llm_provider import LLMProvider

class AzureOpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, endpoint: str, deployment: str):
        self.api_key = api_key
        self.endpoint = endpoint
        self.deployment = deployment
        # 初始化 Azure OpenAI client

    def score_relevance(self, paper, interests):
        # 实现评分逻辑
        pass

    def classify_topics(self, paper):
        # 实现 topic 分类
        pass
```

2. 在 `app/context.py` 中注册：

```python
def _create_llm_provider(self, config: ConfigProfile) -> LLMProvider:
    if config.llm_provider == "azure":
        return AzureOpenAIProvider(
            api_key=config.llm_api_key,
            endpoint=config.llm_base_url,
            deployment=config.llm_model
        )
    # ... 其他 provider
```

3. 更新配置验证：

```python
# app/config_manager.py
VALID_PROVIDERS = ["openai", "anthropic", "azure"]
```

**验证**：
```bash
paper-agent init --provider azure --base-url "https://xxx.openai.azure.com" --model "gpt-4"
paper-agent collect -d 1
```

#### 任务 3.3: 添加新的数据源（如 PubMed）

**场景**：支持从 PubMed 收集生物医学论文

**修改位置**：
- `infra/sources/` 目录
- 创建新文件：`pubmed_adapter.py`

**实现步骤**：

1. 创建 Adapter 类：

```python
# infra/sources/pubmed_adapter.py
from paper_agent.domain.models.paper import Paper
from datetime import datetime

class PubMedAdapter:
    def __init__(self, email: str):
        self.email = email  # PubMed 要求提供 email

    def fetch_papers(self, query: str, days_back: int, max_results: int) -> list[Paper]:
        """从 PubMed 获取论文"""
        # 1. 构建 PubMed API 请求
        # 2. 解析响应
        # 3. 转换为 Paper 对象
        papers = []
        # ... 实现逻辑
        return papers
```

2. 在 `services/collection_manager.py` 中集成：

```python
def collect_from_pubmed(self, query: str, days_back: int, max_results: int):
    adapter = PubMedAdapter(email=self.config.pubmed_email)
    papers = adapter.fetch_papers(query, days_back, max_results)
    # ... 保存逻辑
```

3. 添加 CLI 命令：

```python
# cli/app.py
@app.command()
def collect_pubmed(
    query: str = typer.Argument(...),
    days: int = typer.Option(7, "--days", "-d"),
    max_results: int = typer.Option(100, "--max", "-m"),
):
    """Collect papers from PubMed."""
    ctx = _get_ctx()
    ctx.collection_manager.collect_from_pubmed(query, days, max_results)
```

**验证**：
```bash
paper-agent collect-pubmed "machine learning" -d 7
```

#### 任务 3.4: 添加新的输出格式（如 BibTeX）

**场景**：导出论文为 BibTeX 格式用于 LaTeX

**修改位置**：
- `domain/models/paper.py`
- `cli/app.py`

**实现步骤**：

1. 在 Paper 模型中添加导出方法：

```python
# domain/models/paper.py
class Paper:
    # ... 现有代码

    def to_bibtex(self) -> str:
        """导出为 BibTeX 格式"""
        return f"""@article{{{self.canonical_id},
  title = {{{self.title}}},
  author = {{{', '.join(self.authors)}}},
  year = {{{self.published_date.year}}},
  url = {{{self.url}}},
  abstract = {{{self.abstract}}}
}}"""
```

2. 添加 CLI 命令：

```python
# cli/app.py
@app.command()
def export_bibtex(
    output: str = typer.Option("papers.bib", "--output", "-o"),
    query: Optional[str] = typer.Option(None, "--query"),
):
    """Export papers to BibTeX format."""
    ctx = _get_ctx()
    if query:
        result = ctx.search_engine.search(query, limit=1000)
        papers = result.papers
    else:
        papers = ctx.storage.get_all_papers()

    with open(output, "w") as f:
        for paper in papers:
            f.write(paper.to_bibtex() + "\n\n")

    print_success(f"Exported {len(papers)} papers to {output}")
```

**验证**：
```bash
paper-agent export-bibtex -o my_papers.bib
paper-agent export-bibtex --query "transformer" -o transformer_papers.bib
```

#### 任务 3.5: 改进 Digest 生成策略

**场景**：调整高置信度阈值或分组逻辑

**修改位置**：
- `services/digest_generator.py`

**实现步骤**：

1. 修改阈值常量：

```python
# services/digest_generator.py
HIGH_CONFIDENCE_THRESHOLD = 0.8  # 从 0.7 提高到 0.8
MIN_HIGH_CONFIDENCE_COUNT = 5    # 最少 5 篇高置信论文
```

2. 添加配置支持：

```python
# app/config_manager.py
class ConfigProfile:
    # ... 现有字段
    digest_high_threshold: float = 0.8
    digest_min_high_count: int = 5
```

3. 在 DigestGenerator 中使用配置：

```python
def generate_daily_digest(self, config: ConfigProfile, target_date=None):
    threshold = config.digest_high_threshold
    # ... 使用 threshold 进行分组
```

**验证**：
```bash
# 修改配置
paper-agent init  # 添加新配置项

# 重新生成 digest
paper-agent digest
```

---

### Journey 4: 测试和调试

#### Step 4.1: 单元测试

**测试结构**：
```
tests/
├── unit/              # 单元测试
│   ├── test_storage.py
│   ├── test_paper.py
│   └── test_filtering.py
├── integration/       # 集成测试
│   └── test_collection.py
└── contract/          # 契约测试
    └── test_json_output.py
```

**编写单元测试示例**：

```python
# tests/unit/test_paper.py
import pytest
from paper_agent.domain.models.paper import Paper
from datetime import datetime

def test_paper_creation():
    paper = Paper(
        paper_id="test-001",
        canonical_id="arxiv:2301.12345",
        title="Test Paper",
        authors=["Alice", "Bob"],
        abstract="This is a test.",
        published_date=datetime(2023, 1, 15),
        source="arxiv",
        url="https://arxiv.org/abs/2301.12345"
    )
    assert paper.title == "Test Paper"
    assert len(paper.authors) == 2

def test_paper_to_dict():
    paper = Paper(...)
    data = paper.to_dict()
    assert "title" in data
    assert "authors" in data
```

**运行测试**：
```bash
# 运行所有测试
poetry run pytest

# 运行特定测试文件
poetry run pytest tests/unit/test_paper.py

# 运行特定测试函数
poetry run pytest tests/unit/test_paper.py::test_paper_creation

# 显示详细输出
poetry run pytest -v

# 显示 print 输出
poetry run pytest -s
```

#### Step 4.2: 集成测试

**集成测试示例**：

```python
# tests/integration/test_collection.py
import pytest
from paper_agent.app.context import AppContext

@pytest.fixture
def app_context(tmp_path):
    """创建临时测试环境"""
    config_path = tmp_path / "config.yaml"
    ctx = AppContext(str(config_path))
    # 初始化测试配置
    return ctx

def test_collect_and_filter(app_context):
    """测试收集和过滤流程"""
    # 1. 收集论文
    record = app_context.collection_manager.collect_from_arxiv(
        categories=["cs.AI"],
        days_back=1,
        max_results=10
    )
    assert record.collected_count > 0

    # 2. 过滤论文
    papers = app_context.storage.get_all_papers(limit=10)
    interests = {"topics": ["machine learning"], "keywords": []}
    app_context.filtering_manager.filter_papers(papers, interests)

    # 3. 验证评分
    scored_papers = [p for p in papers if p.relevance_score is not None]
    assert len(scored_papers) > 0
```

#### Step 4.3: 调试技巧

**使用 debug 模式**：
```bash
paper-agent collect --debug
```

**使用 Python 调试器**：
```python
# 在代码中插入断点
import pdb; pdb.set_trace()

# 或使用 ipdb（更友好）
import ipdb; ipdb.set_trace()
```

**查看 SQL 查询**：
```python
# infra/storage/sqlite_storage.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**使用 Rich 的 inspect**：
```python
from rich import inspect
inspect(paper, methods=True)
```

---

### Journey 5: 贡献代码

#### Step 5.1: Fork 和分支

```bash
# Fork 仓库到你的 GitHub 账号

# 克隆你的 fork
git clone https://github.com/YOUR_USERNAME/paper_agent.git
cd paper_agent

# 添加上游仓库
git remote add upstream https://github.com/ORIGINAL_OWNER/paper_agent.git

# 创建功能分支
git checkout -b feature/add-pubmed-support
```

#### Step 5.2: 开发和测试

```bash
# 进行修改
# ...

# 运行测试
poetry run pytest

# 运行 linter
poetry run ruff check .

# 格式化代码
poetry run black .

# 类型检查
poetry run mypy paper_agent/
```

#### Step 5.3: 提交和推送

```bash
# 提交修改
git add .
git commit -m "feat: add PubMed adapter support"

# 推送到你的 fork
git push origin feature/add-pubmed-support
```

#### Step 5.4: 创建 Pull Request

1. 在 GitHub 上打开你的 fork
2. 点击 "New Pull Request"
3. 填写 PR 描述：
   - 修改内容
   - 测试方法
   - 相关 issue

**PR 描述模板**：
```markdown
## 修改内容
添加 PubMed 数据源支持，允许用户从 PubMed 收集生物医学论文。

## 修改文件
- `infra/sources/pubmed_adapter.py` - 新增 PubMed 适配器
- `services/collection_manager.py` - 添加 collect_from_pubmed 方法
- `cli/app.py` - 添加 collect-pubmed 命令
- `tests/integration/test_pubmed.py` - 添加集成测试

## 测试
- [x] 单元测试通过
- [x] 集成测试通过
- [x] 手动测试：`paper-agent collect-pubmed "machine learning" -d 7`

## 相关 Issue
Closes #123
```

---

## 扩展点和插件机制

### 扩展点 1: 自定义数据源

**接口**：无强制接口，但建议遵循以下模式

```python
class CustomSourceAdapter:
    def fetch_papers(self, query: str, days_back: int, max_results: int) -> list[Paper]:
        """获取论文列表"""
        pass
```

**集成方式**：
- 在 `services/collection_manager.py` 中添加新方法
- 或通过配置文件指定自定义 adapter 路径（未来支持）

### 扩展点 2: 自定义 LLM Provider

**接口**：`infra/llm/llm_provider.py`

```python
class LLMProvider(ABC):
    @abstractmethod
    def score_relevance(self, paper: Paper, interests: dict) -> float:
        pass

    @abstractmethod
    def classify_topics(self, paper: Paper) -> list[str]:
        pass
```

**集成方式**：
- 继承 `LLMProvider`
- 在 `app/context.py` 中注册

### 扩展点 3: 自定义输出格式

**方式 1：扩展 Paper 模型**
```python
# domain/models/paper.py
class Paper:
    def to_custom_format(self) -> str:
        # 自定义格式
        pass
```

**方式 2：创建独立的 Formatter**
```python
# infra/reports/custom_formatter.py
class CustomFormatter:
    def format_paper(self, paper: Paper) -> str:
        pass

    def format_digest(self, digest: Digest) -> str:
        pass
```

### 扩展点 4: 自定义存储后端

**接口**：`infra/storage/` 目录

```python
class CustomStorage:
    def save_paper(self, paper: Paper) -> None:
        pass

    def get_paper(self, paper_id: str) -> Paper | None:
        pass

    def search_papers(self, query: str, limit: int) -> list[Paper]:
        pass
```

**集成方式**：
- 实现存储接口
- 在 `app/context.py` 中替换 `SQLiteStorage`

---

## 架构决策记录（ADR）

### ADR-001: 为什么选择 SQLite？

**决策**：使用 SQLite 作为本地存储

**理由**：
- 零配置，无需独立数据库服务
- 支持 FTS5 全文搜索
- 足够处理数万篇论文
- 便于备份和迁移（单文件）

**权衡**：
- 不支持分布式
- 并发写入有限制
- 对于 v01 的单用户场景足够

### ADR-002: 为什么使用 Typer？

**决策**：使用 Typer 构建 CLI

**理由**：
- 基于类型提示，代码简洁
- 自动生成帮助文档
- 与 Rich 集成良好
- 支持交互式和脚本化使用

**权衡**：
- 学习曲线（相比 argparse）
- 依赖较重

### ADR-003: 为什么 LLM 评分在收集后执行？

**决策**：收集和过滤分离

**理由**：
- 收集可以离线或批量执行
- 过滤可以重新执行（调整兴趣后）
- 降低 API 调用失败的影响
- 支持 `--no-filter` 选项

**权衡**：
- 首次使用需要两步操作
- 数据库中会有未评分论文

### ADR-004: 为什么 Digest 是默认入口？

**决策**：Digest-first 而非 Inbox-first

**理由**：
- 符合研究者的日常习惯（每日查看新论文）
- 降低信息过载
- 提供结构化的 intake surface

**权衡**：
- 需要定期收集才有价值
- 不适合一次性查询场景（应使用 search）

---

## 常见问题（FAQ）

### Q1: 如何添加新的 CLI 命令？

在 `cli/app.py` 中添加：
```python
@app.command()
def my_command(
    arg: str = typer.Argument(...),
    option: int = typer.Option(10, "--opt"),
):
    """Command description."""
    ctx = _get_ctx()
    # 实现逻辑
```

### Q2: 如何修改数据库 schema？

1. 修改 `infra/storage/sqlite_storage.py` 中的 `_create_tables()`
2. 创建迁移脚本（未来支持）
3. 或删除数据库重新初始化（开发阶段）

### Q3: 如何调试 LLM 调用？

```python
# 在 LLMProvider 中添加日志
import logging
logger = logging.getLogger(__name__)

def score_relevance(self, paper, interests):
    logger.debug(f"Scoring paper: {paper.title}")
    logger.debug(f"Interests: {interests}")
    # ...
```

### Q4: 如何处理 API 限流？

在 `infra/llm/` 中添加重试逻辑：
```python
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def score_relevance(self, paper, interests):
    # API 调用
    pass
```

### Q5: 如何支持多语言论文？

1. 在 `domain/models/paper.py` 中添加 `language` 字段
2. 在收集时检测语言
3. 在过滤时考虑语言偏好

---

## 性能优化指南

### 优化 1: 批量 LLM 调用

**问题**：逐篇调用 LLM 效率低

**解决**：
```python
# services/filtering_manager.py
def filter_papers_batch(self, papers: list[Paper], interests: dict, batch_size: int = 10):
    for i in range(0, len(papers), batch_size):
        batch = papers[i:i+batch_size]
        # 批量调用 LLM
        scores = self.llm_provider.score_relevance_batch(batch, interests)
        for paper, score in zip(batch, scores):
            paper.relevance_score = score
            self.storage.update_paper(paper)
```

### 优化 2: 缓存 LLM 结果

**问题**：重复评分相同论文

**解决**：
```python
# infra/llm/llm_provider.py
from functools import lru_cache

@lru_cache(maxsize=1000)
def score_relevance(self, paper_id: str, interests_hash: str):
    # 使用 paper_id 和 interests 的 hash 作为缓存键
    pass
```

### 优化 3: 索引优化

**问题**：搜索慢

**解决**：
```sql
-- 在 sqlite_storage.py 中添加索引
CREATE INDEX idx_papers_published_date ON papers(published_date);
CREATE INDEX idx_papers_relevance_score ON papers(relevance_score);
CREATE INDEX idx_papers_lifecycle_state ON papers(lifecycle_state);
```

---

## 下一步

- 查看 [用户旅程](./user-journey.md) 了解用户视角
- 查看 [Design](./design.md) 了解详细架构
- 查看 [Spec](./spec.md) 了解功能规格
- 加入开发讨论：[GitHub Discussions](https://github.com/...)
