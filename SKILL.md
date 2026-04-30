---
name: project-memory
description: 跨会话项目级记忆系统，基于 zvec 向量库实现语义搜索。支持项目隔离、记忆分类、智能保存和自动上下文加载。
metadata:
  author: JGS-Architect
  version: "0.1.0"
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
---

# Project Memory - 跨会话项目级记忆系统

基于 zvec 向量库的语义记忆系统，让 Claude 在不同会话之间保持项目上下文记忆。

## 何时激活

- 用户提到 "记忆"、"记住"、"recall"、"remember"、"记忆系统" 等关键词
- 用户使用 `/memory` 命令
- 会话开始时需要加载项目上下文
- 用户希望保存重要的技术决策或经验

## 安装和初始化

首次使用前需要安装依赖：

```bash
cd ~/.claude/skills/project-memory && uv sync
```

## 使用方法

### 保存记忆

```bash
# 保存项目上下文
cd ~/.claude/skills/project-memory && uv run project-memory save "项目使用 Next.js 14 + App Router，数据库为 PostgreSQL" --project /path/to/project

# 保存 Bug 修复经验
cd ~/.claude/skills/project-memory && uv run project-memory save "N+1 查询问题：使用 DataLoader 批量加载解决" --type bug_fix --importance 8

# 保存技术决策
cd ~/.claude/skills/project-memory && uv run project-memory save "选择 Redis 做缓存，因为需要亚毫秒级延迟" --type decision --tags "cache,redis,architecture"

# 智能保存（自动推断类型和重要性）
cd ~/.claude/skills/project-memory && uv run project-memory auto "这个项目的 API 需要速率限制" --project /path/to/project
```

### 搜索记忆

```bash
# 语义搜索
cd ~/.claude/skills/project-memory && uv run project-memory recall "缓存方案" --project /path/to/project --json

# 按类型过滤
cd ~/.claude/skills/project-memory && uv run project-memory recall "数据库" --type project_context --json

# 按标签过滤
cd ~/.claude/skills/project-memory && uv run project-memory recall "认证" --tags "auth,security" --json
```

### 管理记忆

```bash
# 列出所有记忆
cd ~/.claude/skills/project-memory && uv run project-memory list --project /path/to/project --json

# 删除记忆
cd ~/.claude/skills/project-memory && uv run project-memory delete 5 --project /path/to/project

# 清理过期记忆
cd ~/.claude/skills/project-memory && uv run project-memory clean --days 90

# 统计信息
cd ~/.claude/skills/project-memory && uv run project-memory stats --project /path/to/project --json
```

### 自动上下文加载

```bash
# 加载项目上下文（会话开始时使用）
cd ~/.claude/skills/project-memory && uv run project-memory context --project /path/to/project --json

# 带任务描述的上下文加载
cd ~/.claude/skills/project-memory && uv run project-memory context --project /path/to/project --task "实现用户认证" --json
```

## 记忆类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `project_context` | 项目上下文 | 技术栈、架构决策、目录结构 |
| `user_preference` | 用户偏好 | 编码风格、工具选择 |
| `bug_fix` | Bug 修复经验 | 问题描述、根因分析、解决方案 |
| `code_pattern` | 代码模式 | 常用工具函数、设计模式 |
| `decision` | 技术决策 | 方案选择、权衡理由 |
| `task_status` | 任务状态 | 进行中工作、待办事项 |

## 工作流程

### 会话开始时
1. 自动调用 `context` 命令加载项目记忆
2. 将相关记忆注入当前对话上下文
3. 根据任务描述智能推荐相关记忆

### 会话过程中
1. 用户明确要求保存时，使用 `save` 命令
2. 发现重要信息时，主动使用 `auto` 命令保存
3. 需要回忆之前决策时，使用 `recall` 命令

### 会话结束前
1. 总结本次会话的关键决策和发现
2. 使用 `auto` 命令保存重要信息
3. 清理过期的低重要性记忆

## 快捷别名

在 Claude Code 中可以使用以下简写：

- `/memory save <content>` - 保存记忆
- `/memory recall <query>` - 搜索记忆
- `/memory list` - 列出记忆
- `/memory clean` - 清理记忆
- `/memory context` - 加载上下文
- `/memory auto <content>` - 智能保存

## 配置

配置文件位于 `~/.claude/skills/project-memory/config.json`：

```json
{
  "embedding_model": "BAAI/bge-small-en-v1.1",
  "embedding_dim": 384,
  "default_top_k": 5,
  "max_context_memories": 10,
  "expiration_days": 90,
  "auto_save": true
}
```

## 数据存储

- 向量索引：`~/.claude/skills/project-memory/data/indexes/<project>/`
- 记忆元数据：`~/.claude/skills/project-memory/data/metadata/<project>/memories.json`
