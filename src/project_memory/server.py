"""Web 服务器入口 - 提供 serve 命令启动 HTTP 服务"""

import os
import sys

# Windows 环境强制 UTF-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import uvicorn
from fastapi.staticfiles import StaticFiles

from .api import app


def find_frontend_dist() -> str | None:
    """查找前端构建产物目录"""
    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
    candidates = [
        os.path.join(project_root, "frontend", "dist"),
        os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"),
        os.path.join(os.getcwd(), "frontend", "dist"),
    ]
    for path in candidates:
        abs_path = os.path.abspath(path)
        if os.path.isdir(abs_path):
            return abs_path
    return None


def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    """启动 Web 服务器"""
    dist_dir = find_frontend_dist()
    if dist_dir:
        app.mount("/", StaticFiles(directory=dist_dir, html=True), name="frontend")
        print(f"Frontend: {dist_dir}")

    print(f"Project Memory Web UI: http://{host}:{port}")
    print(f"API docs: http://{host}:{port}/docs")
    uvicorn.run(app, host=host, port=port, log_level="info")
