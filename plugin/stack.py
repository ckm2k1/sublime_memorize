from __future__ import annotations
from typing import Any, NamedTuple, Tuple
import sublime

class Position(NamedTuple):
    start: int
    end: int


class StackFrame:
    def __init__(
        self,
        view: sublime.View | None,
        path: str,
        code: str,
        loc: Position,
        line: int,
    ):
        self.view = view
        self.code = code
        self.loc = loc
        self.line = line
        self.path = path

    def to_json(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "loc": self.loc,
            "line": self.line,
            "path": self.path,
        }

    @classmethod
    def from_json(
        cls,
        path: str = "",
        code: str = "",
        loc: Tuple[int, int] = (0, 0),
        line: int = 0,
    ) -> StackFrame:
        return cls(None, path, code, Position(loc[0], loc[1]), line)


class CallStack:
    def __init__(self):
        self.frames: list[StackFrame] = []
        self._idx = -1

    @property
    def cur_frame(self) -> StackFrame | None:
        if self.frames:
            return self.frames[self._idx]
        return None

    def add_frame(self, frame: StackFrame) -> int:
        self.frames.append(frame)
        self.set_frame(len(self.frames) - 1)
        return self.index

    def clear(self):
        self.frames = []

    def set_frame(self, idx: int) -> StackFrame | None:
        if not self.frames:
            return None
        if idx >= len(self.frames):
            self._idx = 0
        elif idx < 0:
            self._idx = len(self.frames) - 1
        else:
            self._idx = idx
        return self.frames[self.index]

    def next_frame(self) -> StackFrame | None:
        return self.set_frame(self.index + 1)

    def prev_frame(self) -> StackFrame | None:
        return self.set_frame(self.index - 1)

    def is_cur_frame(self, idx: int) -> bool:
        return idx == self.index

    @property
    def index(self) -> int:
        return self._idx

    def to_json(self) -> list[dict[str, Any]]:
        return [f.to_json() for f in self.frames]

    @classmethod
    def from_json(cls, state: list[dict[str, Any]]) -> CallStack:
        inst = cls()
        for frame in state:
            inst.add_frame(StackFrame.from_json(**frame))
        return inst
