"""CLI 入口 - 基于 typer"""

import json
import os
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .memory import MemoryManager
from .types import (
    AutoContextRequest,
    MemoryType,
    RecallRequest,
    SaveRequest,
)

app = typer.Typer(
    name="project-memory",
    help="Claude Code 跨会话项目级记忆系统",
    no_args_is_help=True,
)
console = Console()
error_console = Console(stderr=True)


def _json_output(data: object) -> None:
    """输出 JSON 格式（Claude 解析用）"""
    if hasattr(data, "model_dump"):
        result = data.model_dump()
    elif isinstance(data, list):
        result = []
        for item in data:
            if hasattr(item, "model_dump"):
                result.append(item.model_dump())
            elif hasattr(item, "memory") and hasattr(item, "score"):
                result.append({
                    "memory": item.memory.model_dump(),
                    "score": item.score,
                })
            else:
                result.append(item)
    else:
        result = data
    console.print(json.dumps(result, ensure_ascii=False, default=str))


@app.command()
def save(
    content: str = typer.Argument(..., help="记忆内容"),
    project: str = typer.Option(".", "--project", "-p", help="项目路径"),
    type: str = typer.Option("project_context", "--type", "-t", help="记忆类型"),
    tags: Optional[str] = typer.Option(None, "--tags", help="标签，逗号分隔"),
    importance: int = typer.Option(5, "--importance", "-i", help="重要性 1-10"),
    json_out: bool = typer.Option(False, "--json", help="JSON 输出"),
) -> None:
    """保存一条记忆"""
    manager = MemoryManager()
    tag_list = tags.split(",") if tags else []
    memory_type = MemoryType(type)

    request = SaveRequest(
        content=content,
        memory_type=memory_type,
        tags=tag_list,
        project_path=os.path.abspath(project),
        importance=importance,
    )

    result = manager.save(request)

    if json_out:
        _json_output(result)
    else:
        console.print(f"[green]Saved memory #{result.id}[/green]")
        console.print(f"  Type: {result.memory_type.value}")
        console.print(f"  Content: {result.content[:80]}...")


@app.command()
def recall(
    query: str = typer.Argument(..., help="搜索查询"),
    project: str = typer.Option(".", "--project", "-p", help="项目路径"),
    type: Optional[str] = typer.Option(None, "--type", "-t", help="记忆类型过滤"),
    tags: Optional[str] = typer.Option(None, "--tags", help="标签过滤，逗号分隔"),
    limit: int = typer.Option(5, "--limit", "-l", help="返回数量"),
    json_out: bool = typer.Option(False, "--json", help="JSON 输出"),
) -> None:
    """语义搜索记忆"""
    manager = MemoryManager()
    tag_list = tags.split(",") if tags else []
    memory_type = MemoryType(type) if type else None

    request = RecallRequest(
        query=query,
        project_path=os.path.abspath(project),
        memory_type=memory_type,
        tags=tag_list,
        limit=limit,
    )

    results = manager.recall(request)

    if json_out:
        _json_output(results)
    else:
        if not results:
            console.print("[yellow]No memories found[/yellow]")
            return

        table = Table(title=f"Search Results for: {query}")
        table.add_column("ID", style="cyan", width=6)
        table.add_column("Score", style="green", width=8)
        table.add_column("Type", style="magenta", width=16)
        table.add_column("Content", width=50)
        table.add_column("Tags", width=20)

        for result in results:
            table.add_row(
                str(result.memory.id),
                f"{result.score:.4f}",
                result.memory.memory_type.value,
                result.memory.content[:50],
                ", ".join(result.memory.tags[:3]),
            )

        console.print(table)


@app.command("list")
def list_memories(
    project: str = typer.Option(".", "--project", "-p", help="项目路径"),
    type: Optional[str] = typer.Option(None, "--type", "-t", help="记忆类型过滤"),
    limit: int = typer.Option(50, "--limit", "-l", help="返回数量"),
    json_out: bool = typer.Option(False, "--json", help="JSON 输出"),
) -> None:
    """列出项目所有记忆"""
    manager = MemoryManager()
    memory_type = MemoryType(type) if type else None

    memories = manager.list_memories(
        project_path=os.path.abspath(project),
        memory_type=memory_type,
        limit=limit,
    )

    if json_out:
        _json_output(memories)
    else:
        if not memories:
            console.print("[yellow]No memories found[/yellow]")
            return

        table = Table(title=f"Project Memories ({os.path.abspath(project)})")
        table.add_column("ID", style="cyan", width=6)
        table.add_column("Type", style="magenta", width=16)
        table.add_column("Importance", style="yellow", width=12)
        table.add_column("Content", width=50)
        table.add_column("Tags", width=20)

        for memory in memories:
            table.add_row(
                str(memory.id),
                memory.memory_type.value,
                str(memory.importance),
                memory.content[:50],
                ", ".join(memory.tags[:3]),
            )

        console.print(table)


@app.command()
def delete(
    memory_id: int = typer.Argument(..., help="记忆 ID"),
    project: str = typer.Option(".", "--project", "-p", help="项目路径"),
    json_out: bool = typer.Option(False, "--json", help="JSON 输出"),
) -> None:
    """删除一条记忆"""
    manager = MemoryManager()
    success = manager.delete(memory_id, project_path=os.path.abspath(project))

    if json_out:
        _json_output({"success": success, "deleted_id": memory_id})
    else:
        if success:
            console.print(f"[green]Deleted memory #{memory_id}[/green]")
        else:
            error_console.print(f"[red]Memory #{memory_id} not found[/red]")
            sys.exit(1)


@app.command()
def clean(
    project: str = typer.Option(".", "--project", "-p", help="项目路径"),
    days: int = typer.Option(90, "--days", "-d", help="过期天数"),
    json_out: bool = typer.Option(False, "--json", help="JSON 输出"),
) -> None:
    """清理过期记忆"""
    manager = MemoryManager()
    count = manager.clean(
        project_path=os.path.abspath(project),
        days=days,
    )

    if json_out:
        _json_output({"cleaned_count": count})
    else:
        console.print(f"[green]Cleaned {count} expired memories[/green]")


@app.command()
def context(
    project: str = typer.Option(".", "--project", "-p", help="项目路径"),
    task: Optional[str] = typer.Option(None, "--task", "-t", help="当前任务描述"),
    limit: int = typer.Option(10, "--limit", "-l", help="返回数量"),
    json_out: bool = typer.Option(True, "--json/--no-json", help="JSON 输出"),
) -> None:
    """获取项目上下文（自动加载相关记忆）"""
    manager = MemoryManager()

    request = AutoContextRequest(
        project_path=os.path.abspath(project),
        current_task=task,
        limit=limit,
    )

    memories = manager.get_context(request)

    if json_out:
        _json_output(memories)
    else:
        if not memories:
            console.print("[yellow]No context memories found[/yellow]")
            return

        for memory in memories:
            console.print(f"[cyan]#{memory.id}[/cyan] [{memory.memory_type.value}] {memory.content[:60]}")


@app.command()
def auto(
    content: str = typer.Argument(..., help="记忆内容"),
    project: str = typer.Option(".", "--project", "-p", help="项目路径"),
    json_out: bool = typer.Option(False, "--json", help="JSON 输出"),
) -> None:
    """智能保存 - 自动判断类型和重要性"""
    manager = MemoryManager()
    result = manager.auto_save(
        content=content,
        project_path=os.path.abspath(project),
    )

    if result is None:
        if json_out:
            _json_output({"saved": False, "reason": "similar_memory_exists"})
        else:
            console.print("[yellow]Similar memory already exists, skipped[/yellow]")
    else:
        if json_out:
            _json_output(result)
        else:
            console.print(f"[green]Auto-saved memory #{result.id}[/green]")
            console.print(f"  Inferred type: {result.memory_type.value}")
            console.print(f"  Inferred importance: {result.importance}")
            console.print(f"  Content: {result.content[:80]}")


@app.command()
def stats(
    project: str = typer.Option(".", "--project", "-p", help="项目路径"),
    json_out: bool = typer.Option(False, "--json", help="JSON 输出"),
) -> None:
    """显示项目记忆统计信息"""
    manager = MemoryManager()
    memories = manager.list_memories(project_path=os.path.abspath(project), limit=10000)

    type_counts = {}
    for memory in memories:
        t = memory.memory_type.value
        type_counts[t] = type_counts.get(t, 0) + 1

    stats_data = {
        "total": len(memories),
        "by_type": type_counts,
        "project": os.path.abspath(project),
    }

    if json_out:
        _json_output(stats_data)
    else:
        console.print(f"[bold]Memory Stats for {os.path.abspath(project)}[/bold]")
        console.print(f"Total memories: {len(memories)}")
        for t, count in type_counts.items():
            console.print(f"  {t}: {count}")


if __name__ == "__main__":
    app()
