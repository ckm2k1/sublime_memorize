from __future__ import annotations
from typing import cast
import sublime
import sublime_plugin
from functools import partial

from .utils import print_view_info
from .stack import CallStack, StackFrame


class WindowRegistry(sublime_plugin.EventListener):
    def __init__(self):
        self.windows: dict[int, WindowManager] = {}

    def on_pre_close_window(self, window: sublime.Window) -> None:
        self.discard(window)

    def on_exit(self) -> None:
        self.close()

    def discard(self, window: sublime.Window) -> None:
        if (wm := self.find_window(window)) is not None:
            wm.close()
            self.windows.pop(wm.id)

    def close(self) -> None:
        for wm in self.windows.values():
            wm.close()

    def find_window(
        self, window: sublime.Window | int | None
    ) -> WindowManager | None:
        if window is None:
            sublime.status_message("Memorize: no window found")
            return None
        elif isinstance(window, int):
            wid = window
        else:
            wid = window.id()
        return self.windows.get(wid)

    def on_new_window(self, window: sublime.Window) -> None:
        self.add_window(window)

    def add_window(self, window: sublime.Window):
        if window.id() in self.windows:
            return
        if not window.is_valid():
            return
        self.windows[window.id()] = WindowManager(window)


class WindowManager:
    def __init__(self, window: sublime.Window):
        self.wnd = window
        self.panel: sublime.View | None = None
        self.stacks: list[CallStack] = []
        self.stack_idx = -1
        self.stack_view: sublime.HtmlSheet | None = None
        self.sm = HtmlSheetManager(self)
        self.load_state()

    def close(self) -> None:
        self.save_state()

    def load_state(self) -> None:
        if stacks := self.wnd.settings().get("mem-stacks", []):
            for s in stacks:
                self.add_stack(stack=CallStack.from_json(s))
            return

        self.add_stack()

    def add_stack(self, stack: CallStack | None = None) -> CallStack:
        s = stack if stack is not None else CallStack()
        self.stacks.append(s)
        self.stack_idx += 1
        return s

    def save_state(self) -> None:
        stacks = []
        for s in self.stacks:
            if data := s.to_json():
                stacks.append(data)

        self.wnd.settings().set("mem-stacks", stacks)

    @property
    def id(self) -> int:
        return self.wnd.id()

    @property
    def stack(self) -> CallStack:
        return self.stacks[self.stack_idx]

    @property
    def window(self) -> sublime.Window:
        return self.wnd

    def new_sheet(
        self, name: str, content: str, add_to_sel: bool = False
    ) -> sublime.HtmlSheet:
        args = {}
        if add_to_sel:
            args["flags"] = sublime.NewFileFlags.ADD_TO_SELECTION

        return cast(
            sublime.HtmlSheet, self.wnd.new_html_sheet(name, content, **args)
        )

    def show_stack(self):
        view = self.window.active_view()
        self.sm.show_stack()
        if view is not None:
            self.window.select_sheets([view.sheet(), self.sm.sheet])
            self.window.focus_view(view)

    def focus_view(self, view: sublime.View, line: int | None = None) -> None:
        if not self.window.is_valid():
            return
        self.window.focus_view(view)
        if line is not None:
            view.show_at_center(line)
            view.sel().clear()
            view.sel().add(sublime.Region(line))

    def show_frame(self, idx: int | None = None) -> None:
        idx = idx if idx is not None else self.stack.index
        if (frame := self.stack.set_frame(idx)) is not None:
            view = frame.view
            print_view_info(view)
            if view is None or view.window() is None or not view.is_valid():
                view = self.window.open_file(frame.path)
                frame.view = view
            if not view.is_loading():
                self.focus_view(view, line=frame.loc.start)
            else:
                sublime.set_timeout(
                    partial(self.focus_view, view, line=frame.loc.start),
                    delay=10,
                )
            self.sm.render_content(self.stack)

    def get_stack(self, idx: int | None = None) -> CallStack:
        if idx is None:
            return self.stack
        return self.stacks[self.stack_idx]

    def clear_stack(self) -> None:
        self.stack.clear()
        self.sm.close()
        self.save_state()

    def add_frame(self, frame: StackFrame) -> int:
        idx = self.stack.add_frame(frame)
        self.save_state()
        return idx

    def next_frame(self) -> None:
        self.stack.next_frame()
        self.show_frame()

    def prev_frame(self) -> None:
        self.stack.prev_frame()
        self.show_frame()

    def hide_stack(self) -> None:
        self.sm.close()

    def delete_frame(self, idx: int | None = None) -> None:
        if self.stack.delete_frame():
            self.save_state()
            self.sm.render_content(self.stack)
        else:
            sublime.status_message(
                f"Index `{idx}` does not exist in the stack."
            )


class HtmlSheetManager:
    def __init__(self, wm: WindowManager):
        self.sheet: sublime.HtmlSheet | None = None
        self.wm = wm
        self.id: int | None = None

    def is_open(self) -> bool:
        window = self.sheet.window() if self.sheet is not None else None
        return window is not None and window.is_valid()

    def open_sheet(self) -> sublime.Sheet:
        if not self.is_open():
            self.sheet = self.wm.new_sheet(
                "memorize-stack", "", add_to_sel=True
            )
            self.id = self.sheet.id()
            return self.sheet

        return self.sheet

    def close(self):
        if self.is_open():
            self.sheet.close()

    def show_stack(self, stack: CallStack | None = None) -> None:
        stack = self.wm.get_stack() if stack is None else stack
        if stack is not None:
            sheet = self.open_sheet()
            self.render_content(stack)

    def render_content(self, stack: CallStack | None = None) -> None:
        if self.sheet is not None:
            stack = stack if stack is not None else self.wm.get_stack()
            if stack is not None:
                self.sheet.set_contents(Renderer(stack).render())


class Renderer:
    def __init__(self, stack: CallStack):
        self.stack = stack

    def render_frame(
        self, frame: StackFrame, idx: int, selected: bool = False
    ) -> str:
        code = frame.code
        open_view_command = sublime.command_url(
            "memorize_jump_to_frame",
            {"idx": idx},
        )
        return f"""
        <div class="stack-frame{' stack-frame-selected' if selected else ''}">
            <div class="stack-frame-location">
                <a href="{open_view_command}">{str(frame.path)}:L{str(frame.line)}</a>
            </div>
            <pre>
                <code class="stack-frame-code">
                {code}
                </code>
            </pre>
        </div>
        """

    def render(self) -> str:
        body = ""
        cur_frame = self.stack.index
        for i, f in enumerate(self.stack.frames):
            body += self.render_frame(f, i, selected=cur_frame == i)

        content = f"""
        <style>
            .call-stack {{
                margin: 10px;
            }}
            .stack-frame {{
                padding: 10px;
            }}
            .stack-frame-location {{
                color: var(--greenish)
            }}
            .stack-frame-selected {{
                border: 1px solid var(--yellowish)
            }}
        </style>
        <body>
            <div class="call-stack">
            {body}
            </div>
        </body>
        """
        return content
