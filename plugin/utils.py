from __future__ import annotations
import sublime


def print_view_info(view: sublime.View | None) -> None:
    if view is None:
        print("DEBUG: view is None")
        return

    window = view.window()

    print(f"VIEW ({view.id()})")
    print("window id:", window.id() if window is not None else 'NO WINDOW')
    print("file_name:", view.file_name())
    print("element:", view.element())
    print("buffer id:", view.buffer().id())
    print("is_valid:", view.is_valid())
    print("is_dirty:", view.is_dirty())
    print("is_loading:", view.is_loading())
    print("is_primary:", view.is_primary())
