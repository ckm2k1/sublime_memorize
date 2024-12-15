from __future__ import annotations
import sublime
import sublime_plugin

from .plugin.windows import WindowRegistry
from .plugin.stack import Position, StackFrame


OUTPUT_PANEL_NAME = "memorize"
wreg = WindowRegistry()


def plugin_loaded() -> None:
    global wreg
    for window in sublime.windows():
        wreg.add_window(window)


def plugin_unloaded() -> None:
    wreg.close()


class MemorizeAddFrameCommand(sublime_plugin.TextCommand):
    def run(self, edit: sublime.Edit):
        if (wnd := wreg.find_window(self.view.window())) is not None:
            frame = self.get_frame()
            if frame is not None:
                idx = wnd.add_frame(frame)
                sublime.status_message(f"memorized new frame: {idx}")
                wnd.window.run_command("memorize_show_stack")
        else:
            sublime.status_message("Error: no windows found for memorize")

    def get_frame(self) -> StackFrame | None:
        code, loc, sline = get_sel_code_and_loc(self.view)
        if code:
            return StackFrame(
                self.view, self.view.file_name(), code, loc, sline
            )
        return None


class MemorizeShowStackCommand(sublime_plugin.WindowCommand):
    def run(self):
        if (wm := wreg.find_window(self.window)) is not None:
            wm.show_stack()


class MemorizeClearStackCommand(sublime_plugin.WindowCommand):
    def run(self):
        if (wm := wreg.find_window(self.window)) is not None:
            s = wm.clear_stack()
            sublime.status_message("Current stack cleared")


class MemorizeJumpToFrameCommand(sublime_plugin.WindowCommand):
    def run(self, idx: int) -> None:
        if wm := wreg.find_window(self.window.id()):
            sublime.status_message(f"Jumping to frame: {idx}")
            wm.show_frame(idx)


class MemorizeNextFrameCommand(sublime_plugin.WindowCommand):
    def run(self) -> None:
        if wm := wreg.find_window(self.window.id()):
            wm.next_frame()


class MemorizePrevFrameCommand(sublime_plugin.WindowCommand):
    def run(self) -> None:
        if wm := wreg.find_window(self.window.id()):
            wm.prev_frame()


class MemorizeHideStackCommand(sublime_plugin.WindowCommand):
    def run(self) -> None:
        if wm := wreg.find_window(self.window.id()):
            wm.hide_stack()


class MemorizeDeleteFrameCommand(sublime_plugin.WindowCommand):
    def run(self, idx: int | None = None) -> None:
        if wm := wreg.find_window(self.window.id()):
            wm.delete_frame(idx)


def get_sel_code_and_loc(view: sublime.View) -> tuple[str, Position, int]:
    regs = []
    code = ""
    for p in view.sel():
        if p.empty():
            p = view.full_line(p)
        regs.extend(p.to_tuple())
        if view.substr(p).strip():
            code += view.export_to_html(p, minihtml=True)
    l, h = min(regs), max(regs)
    return code, Position(l, h), view.rowcol(l)[0] + 1


def is_empty_sel(sel: sublime.Selection) -> bool:
    return all(map(lambda r: r.empty(), sel))
