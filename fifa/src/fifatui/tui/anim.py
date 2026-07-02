"""A tiny frame-loop helper shared by every animated widget.

One ``FrameAnimator`` per widget: it owns a single Textual timer, calls
``frame(elapsed_seconds)`` at the requested fps until the callback returns
False, and stops idempotently (restarting cancels the previous run; external
``stop()`` — e.g. on unmount — never fires ``on_done``).
"""

from __future__ import annotations

from typing import Callable

from textual.widget import Widget


class FrameAnimator:
    def __init__(self, widget: Widget):
        self._widget = widget
        self._timer = None
        self._frame_cb: Callable[[float], bool] | None = None
        self._on_done: Callable[[], None] | None = None
        self._dt = 0.0
        self._elapsed = 0.0

    def start(
        self,
        fps: float,
        frame: Callable[[float], bool],
        on_done: Callable[[], None] | None = None,
    ) -> None:
        self.stop()
        self._dt = 1.0 / fps
        self._elapsed = 0.0
        self._frame_cb = frame
        self._on_done = on_done
        self._timer = self._widget.set_interval(self._dt, self._tick)

    def _tick(self) -> None:
        if self._frame_cb is None:
            return
        self._elapsed += self._dt
        if not self._frame_cb(self._elapsed):
            cb, self._on_done = self._on_done, None
            self.stop()
            if cb is not None:
                cb()

    def stop(self) -> None:
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
        self._frame_cb = None
        self._on_done = None

    @property
    def running(self) -> bool:
        return self._timer is not None
