# Project Memory

Claude Code 跨会话项目级记忆系统，基于 [zvec](https://pypi.org/project/zvec/) 向量库实现语义搜索。让 Claude 在不同会话之间保持项目上下文记忆。

## 功能特性

- **语义搜索** - 基于向量相似度的记忆检索，而非简单关键词匹配
- **项目隔离** - 每个项目独立存储索引和元数据，互不干扰
- **记忆分类** - 支持 6 种记忆类型（项目上下文、用户偏好、Bug 修复经验、代码模式、技术决策、任务状态）
- **智能保存** - 自动推断记忆类型和重要性评分，去重检测避免重复存储
- **双模式嵌入** - 支持本地模型（zvec DefaultLocalDenseEmbedding）和在线 API（火山引擎 Doubao）
- **自动上下文加载** - 会话开始时自动注入相关记忆

## 安装

依赖 Python >= 3.10，使用 [uv](https://docs.astral.sh/uv/) 管理环境：

```bash
cd ~/.claude/skills/project-memory && uv sync
```

## 配置

复制示例配置并修改：

```bash
cp config.example.json config.json
```

`config.json` 字段说明：

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `embedding_mode` | 嵌入模式：`local`（本地）或 `online`（在线 API） | `local` |
| `online_embedding.api_url` | 在线嵌入 API 地址 | 火山引擎 Doubao |
| `online_embedding.model` | 在线模型名称 | `doubao-embedding-vision-251215` |
| `online_embedding.api_key` | API Key（也可通过环境变量 `ARK_API_KEY` 设置） | - |
| `online_embedding.dim` | 在线嵌入向量维度 | `2048` |
| `embedding_dim` | 本地嵌入向量维度 | `384` |
| `default_top_k` | 默认返回数量 | `5` |
| `expiration_days` | 记忆过期天数 | `90` |

## 使用方法

### 保存记忆

```bash
uv run project-memory save "项目使用 Next.js 14 + App Router" --project /path/to/project

uv run project-memory save "N+1 查询问题：使用 DataLoader 批量加载解决" --type bug_fix --importance 8

uv run project-memory auto "这个项目的 API 需要速率限制" --project /path/to/project
```

### 搜索记忆

```bash
uv run project-memory recall "缓存方案" --project /path/to/project --json

uv run project-memory recall "数据库" --type project_context --json
```

### 管理记忆

```bash
uv run project-memory list --project /path/to/project --json
uv run project-memory delete 5 --project /path/to/project
uv run project-memory clean --days 90
uv run project-memory stats --project /path/to/project --json
```

### 上下文加载

```bash
uv run project-memory context --project /path/to/project --json
uv run project-memory context --project /path/to/project --task "实现用户认证" --json
```

## 记忆类型

| 类型 | 标识 | 说明 |
|------|------|------|
| 项目上下文 | `project_context` | 技术栈、架构决策、目录结构 |
| 用户偏好 | `user_preference` | 编码风格、工具选择 |
| Bug 修复经验 | `bug_fix` | 问题描述、根因分析、解决方案 |
| 代码模式 | `code_pattern` | 常用工具函数、设计模式 |
| 技术决策 | `decision` | 方案选择、权衡理由 |
| 任务状态 | `task_status` | 进行中工作、待办事项 |

## 项目结构

```
src/project_memory/
  __init__.py      # 包入口
  main.py          # CLI 入口（typer）
  memory.py        # 记忆管理器（高级业务层）
  store.py         # zvec 向量存储层
  embedding.py     # 嵌入生成（本地/在线双模式）
  config.py        # 配置管理
  types.py         # 数据类型定义（pydantic）
```

## 技术栈

- **zvec** - 向量存储与相似度搜索
- **sentence-transformers** - 本地文本嵌入（间接通过 zvec）
- **typer** + **rich** - CLI 框架与终端渲染
- **pydantic** - 数据模型与校验
- **httpx** - 在线嵌入 API 客户端

## 许可

Private - Internal Use Only
