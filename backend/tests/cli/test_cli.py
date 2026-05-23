"""测试：CLI 命令行参数解析功能。"""

from __future__ import annotations

import pytest

from devpulse.cli.main import create_parser


class TestCLIParser:
    """argparse 解析器单元测试。"""

    def test_parser_fetch_command(self) -> None:
        """测试 fetch 命令及参数解析。"""
        parser = create_parser()
        args = parser.parse_args(
            ["fetch", "--language", "Python", "--since", "monthly", "--top-n", "10"]
        )
        assert args.command == "fetch"
        assert args.language == "Python"
        assert args.since == "monthly"
        assert args.top_n == 10
        assert args.no_summarize is False

    def test_parser_fetch_defaults(self) -> None:
        """测试 fetch 命令默认值。"""
        parser = create_parser()
        args = parser.parse_args(["fetch"])
        assert args.command == "fetch"
        assert args.language == ""
        assert args.since == "weekly"
        assert args.top_n == 25
        assert args.no_summarize is False

    def test_parser_fetch_no_summarize(self) -> None:
        """测试 fetch --no-summarize 标志。"""
        parser = create_parser()
        args = parser.parse_args(["fetch", "--no-summarize"])
        assert args.no_summarize is True

    def test_parser_report_command(self) -> None:
        """测试 report 命令及参数解析。"""
        parser = create_parser()
        args = parser.parse_args(["report", "--limit", "5", "--week", "2026-W21"])
        assert args.command == "report"
        assert args.limit == 5
        assert args.week == "2026-W21"

    def test_parser_report_defaults(self) -> None:
        """测试 report 命令默认值。"""
        parser = create_parser()
        args = parser.parse_args(["report"])
        assert args.command == "report"
        assert args.limit == 10
        assert args.week == ""

    def test_parser_serve_command(self) -> None:
        """测试 serve 命令及参数解析。"""
        parser = create_parser()
        args = parser.parse_args(["serve", "--host", "0.0.0.0", "--port", "9000"])
        assert args.command == "serve"
        assert args.host == "0.0.0.0"
        assert args.port == 9000

    def test_parser_serve_defaults(self) -> None:
        """测试 serve 命令默认值。"""
        parser = create_parser()
        args = parser.parse_args(["serve"])
        assert args.command == "serve"
        assert args.host == "127.0.0.1"
        assert args.port == 8000

    def test_parser_status_command(self) -> None:
        """测试 status 命令解析。"""
        parser = create_parser()
        args = parser.parse_args(["status"])
        assert args.command == "status"

    def test_parser_no_command_shows_help(self, capsys) -> None:
        """无命令时显示帮助信息。"""
        parser = create_parser()
        # 模拟无命令输入
        test_args = ["devpulse"]
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(test_args)
        # 无命令时 argparse 会 exit(2) 或 exit(0) 取决于实现
        assert exc_info.value.code in (0, 2)

    def test_parser_invalid_command(self) -> None:
        """无效命令应报错退出。"""
        parser = create_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["invalid_cmd"])
        assert exc_info.value.code == 2

    def test_cli_import_main(self) -> None:
        """测试 CLI main 模块可正常导入。"""
        from devpulse.cli.main import main

        assert callable(main)
