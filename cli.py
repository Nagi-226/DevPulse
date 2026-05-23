"""DevPulse CLI 快捷入口。

用法:
    python cli.py fetch
    python cli.py report
    python cli.py serve
    python cli.py status
"""

import os
import sys

# 确保 backend 目录在 path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from devpulse.cli.main import main  # noqa: E402

if __name__ == "__main__":
    main()