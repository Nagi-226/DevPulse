"""MetaGPT Role/Message 轻量模拟，兼容 MetaGPT API 风格。

提供 Role 基类和 Message 类，用于构建多 Agent 流水线。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Message:
    """MetaGPT 消息对象，用于 Agent 间通信。

    Attributes:
        content: 消息内容（任意类型）
        role: 发送者角色名
        cause_by: 触发此消息的动作类型
        sent_from: 发送者 Agent 名称
        send_to: 接收者 Agent 名称
        created_at: 创建时间戳
    """

    content: Any
    role: str = ""
    cause_by: str = ""
    sent_from: str = ""
    send_to: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __str__(self) -> str:
        return f"Message({self.role} -> {self.send_to}: {type(self.content).__name__})"


class Role(ABC):
    """MetaGPT Role 基类，定义 Agent 通用行为。

    每个 Agent 继承此类，实现 `_act` 方法定义具体行为。
    """

    def __init__(self, name: str, profile: str, goal: str, constraints: str = ""):
        """初始化 Agent 角色。

        Args:
            name: Agent 名称（如 "GitHubTrendingCrawler"）
            profile: 角色描述（如 "数据采集工程师"）
            goal: 目标描述（如 "抓取 GitHub Trending 页面"）
            constraints: 约束条件（如 "不修改源数据"）
        """
        self.name = name
        self.profile = profile
        self.goal = goal
        self.constraints = constraints
        self.memory: list[Message] = []
        self._rc = RoleContext()

    async def run(self, *args, **kwargs) -> Any:
        """执行 Agent 的主要工作流。

        默认实现：调用 _act 方法，记录消息历史。
        """
        msg = Message(
            content={"args": args, "kwargs": kwargs},
            role=self.name,
            cause_by="run",
            sent_from="System",
            send_to=self.name,
        )
        self.memory.append(msg)

        result = await self._act(*args, **kwargs)

        result_msg = Message(
            content=result,
            role=self.name,
            cause_by="act",
            sent_from=self.name,
            send_to="NextAgent",
        )
        self.memory.append(result_msg)

        return result

    @abstractmethod
    async def _act(self, *args, **kwargs) -> Any:
        """Agent 的具体行为实现，子类必须重写。

        Returns:
            执行结果，将作为 Message 传递给下一个 Agent。
        """
        pass

    def get_last_message(self) -> Message | None:
        """获取最后一条消息记录。"""
        return self.memory[-1] if self.memory else None

    def get_memory_summary(self) -> str:
        """获取内存历史摘要。"""
        return f"{self.name}: {len(self.memory)} messages"


@dataclass
class RoleContext:
    """Role 运行时上下文（简化版）。"""

    todo: str | None = None
    watch: list[str] = field(default_factory=list)
    news: list[Message] = field(default_factory=list)
