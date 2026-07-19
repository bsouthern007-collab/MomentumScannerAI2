from __future__ import annotations

import json
import math
from pathlib import Path
import tkinter as tk


APP_DIR = Path(__file__).resolve().parent
STATUS_FILE = APP_DIR / "data" / "companion_status.json"

PROFILES = {
    "Scout": {"accent": "#38BDF8", "tagline": "Clean setup coach", "style": "robot"},
    "Null": {"accent": "#A78BFA", "tagline": "Quiet risk checker", "style": "hood"},
    "Nova": {"accent": "#22D3EE", "tagline": "Catalyst and news scout", "style": "star"},
    "Flux": {"accent": "#F59E0B", "tagline": "Fast momentum watcher", "style": "bolt"},
}

TIPS = [
    "Wait for the entry trigger. Do not chase early candles.",
    "Check the stop first. If the risk feels too big, size down or skip.",
    "Before approval: news, volume, spread, halt risk, and data source.",
    "Paper trade only after the setup, entry, stop, and target are clear.",
    "Journal the result. The review is where the learning compounds.",
]


class DesktopCompanion:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Trading for Dummys 101 companion")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#ff00ff")
        try:
            self.root.attributes("-transparentcolor", "#ff00ff")
        except tk.TclError:
            pass

        self.name = "Scout"
        self.tip_index = 0
        self.bob = 0
        self.drag_x = 0
        self.drag_y = 0
        self.show_bubble = True
        self.status_snapshot: dict[str, str] = {}
        self.status_mtime = 0.0

        self.canvas = tk.Canvas(self.root, width=360, height=220, bg="#ff00ff", highlightthickness=0)
        self.canvas.pack()
        self.root.geometry("+960+560")

        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag)
        self.canvas.bind("<Double-Button-1>", self.toggle_bubble)
        self.canvas.bind("<Button-3>", self.next_character)
        self.root.bind("<Escape>", lambda _event: self.root.destroy())
        self.root.bind("<space>", lambda _event: self.next_tip())
        self.root.bind("<Tab>", lambda _event: self.next_character())

        self.poll_status_file()
        self.animate()

    def start_drag(self, event: tk.Event) -> None:
        self.drag_x = int(event.x)
        self.drag_y = int(event.y)

    def drag(self, event: tk.Event) -> None:
        x = self.root.winfo_x() + int(event.x) - self.drag_x
        y = self.root.winfo_y() + int(event.y) - self.drag_y
        self.root.geometry(f"+{x}+{y}")

    def next_character(self, _event: tk.Event | None = None) -> None:
        names = list(PROFILES)
        self.name = names[(names.index(self.name) + 1) % len(names)]
        self.tip_index = 0
        self.draw()

    def next_tip(self) -> None:
        tips = self.active_tips()
        self.tip_index = (self.tip_index + 1) % max(1, len(tips))
        self.draw()

    def toggle_bubble(self, _event: tk.Event | None = None) -> None:
        self.show_bubble = not self.show_bubble
        self.draw()

    def poll_status_file(self) -> None:
        try:
            mtime = STATUS_FILE.stat().st_mtime
            if mtime != self.status_mtime:
                payload = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    self.status_snapshot = {str(key): str(value) for key, value in payload.items()}
                    companion = self.status_snapshot.get("Companion")
                    if companion in PROFILES:
                        self.name = companion
                    self.tip_index = 0
                    self.status_mtime = mtime
                    self.draw()
        except (OSError, json.JSONDecodeError):
            pass
        self.root.after(2500, self.poll_status_file)

    def active_tips(self) -> list[str]:
        stock = self.status_snapshot.get("Ticker", "").strip()
        if not stock:
            return TIPS
        status = self.status_snapshot.get("Status", "Watching")
        entry = self.status_snapshot.get("Entry trigger", "entry trigger")
        stop = self.status_snapshot.get("Stop", "planned stop")
        target = self.status_snapshot.get("Target 1", "target 1")
        confidence = self.status_snapshot.get("Data confidence", "data check")
        fit = self.status_snapshot.get("Playbook fit", "setup check")
        return [
            f"{stock}: {status}. Entry: {entry}.",
            f"Risk map: stop {stop}. Target {target}.",
            f"Data confidence: {confidence}. Fit: {fit}.",
            "Paper approval only after news, spread, volume, and risk checks.",
        ]

    def mood_color(self) -> str:
        signal_color = self.status_snapshot.get("Signal color", "").lower()
        if signal_color == "blue":
            return "#38BDF8"
        if signal_color == "green":
            return "#00C805"
        if signal_color == "red":
            return "#FF375F"
        mood = self.status_snapshot.get("Mood", "neutral")
        if mood == "sell":
            return "#38BDF8"
        if mood == "danger":
            return "#FF375F"
        if mood == "watch":
            return "#F59E0B"
        return "#00C805"

    def animate(self) -> None:
        self.bob = (self.bob + 1) % 80
        self.draw()
        self.root.after(55, self.animate)

    def draw(self) -> None:
        self.canvas.delete("all")
        profile = PROFILES[self.name]
        accent = profile["accent"]
        core = self.mood_color()
        offset = int(math.sin(self.bob / 80 * math.tau) * 3)
        x = 42
        y = 66 + offset

        self.canvas.create_oval(x + 20, y + 112, x + 104, y + 128, fill="#000000", outline="", stipple="gray50")
        self.round_rect(x + 14, y + 34, x + 29, y + 60, 6, fill="#101821", outline=accent, width=3)
        self.round_rect(x + 95, y + 34, x + 110, y + 60, 6, fill="#101821", outline=accent, width=3)
        self.draw_character_crest(x, y, accent, core, profile["style"])

        self.canvas.create_line(x + 24, y + 78, x + 12, y + 106, fill=accent, width=10, capstyle=tk.ROUND)
        self.canvas.create_line(x + 100, y + 78, x + 112, y + 104, fill=accent, width=10, capstyle=tk.ROUND)
        self.round_rect(x + 5, y + 101, x + 22, y + 117, 5, fill=accent, outline="#101821", width=2)
        self.round_rect(x + 105, y + 98, x + 122, y + 114, 5, fill=accent, outline="#101821", width=2)

        self.round_rect(x + 16, y + 60, x + 108, y + 79, 8, fill="#101821", outline=accent, width=3)
        self.round_rect(x + 55, y + 54, x + 69, y + 70, 4, fill="#101821", outline=accent, width=3)
        self.round_rect(x + 28, y + 73, x + 96, y + 126, 10, fill="#101821", outline=accent, width=4)
        self.round_rect(x + 42, y + 84, x + 82, y + 109, 5, fill="#172232", outline="#293546", width=2)
        self.round_rect(x + 56, y + 91, x + 68, y + 103, 4, fill=core, outline="")
        self.canvas.create_line(x + 41, y + 114, x + 83, y + 114, fill=accent, width=4, capstyle=tk.ROUND)

        self.round_rect(x + 18, y + 17, x + 106, y + 68, 12, fill="#172232", outline=accent, width=4)
        self.round_rect(x + 34, y + 31, x + 90, y + 58, 7, fill="#0B1117", outline="#293546", width=2)
        if profile["style"] == "hood":
            self.canvas.create_line(x + 45, y + 43, x + 57, y + 43, fill=accent, width=6, capstyle=tk.ROUND)
            self.canvas.create_line(x + 68, y + 43, x + 80, y + 43, fill=accent, width=6, capstyle=tk.ROUND)
            self.canvas.create_line(x + 48, y + 55, x + 76, y + 55, fill="#38BDF8", width=3, capstyle=tk.ROUND)
        else:
            self.canvas.create_oval(x + 47, y + 41, x + 56, y + 50, fill=core, outline="")
            self.canvas.create_oval(x + 70, y + 41, x + 79, y + 50, fill=core, outline="")
            self.canvas.create_arc(x + 53, y + 43, x + 75, y + 62, start=200, extent=140, style=tk.ARC, outline="#B7C2D0", width=3)

        self.canvas.create_line(x + 47, y + 123, x + 46, y + 142, fill=accent, width=10, capstyle=tk.ROUND)
        self.canvas.create_line(x + 77, y + 123, x + 78, y + 142, fill=accent, width=10, capstyle=tk.ROUND)
        self.round_rect(x + 31, y + 139, x + 58, y + 151, 5, fill="#101821", outline=accent, width=3)
        self.round_rect(x + 66, y + 139, x + 93, y + 151, 5, fill="#101821", outline=accent, width=3)
        self.canvas.create_text(x + 62, y + 168, text=self.name.upper(), fill=accent, font=("Segoe UI", 11, "bold"))

        if self.show_bubble:
            self.draw_bubble(accent, profile["tagline"])

    def draw_character_crest(self, x: int, y: int, accent: str, core: str, style: str) -> None:
        if style == "hood":
            self.canvas.create_arc(x + 25, y - 4, x + 99, y + 58, start=20, extent=140, style=tk.ARC, outline=accent, width=4)
            self.canvas.create_oval(x + 24, y + 2, x + 36, y + 14, fill="#38BDF8", outline="")
            self.canvas.create_oval(x + 88, y + 2, x + 100, y + 14, fill="#38BDF8", outline="")
            return
        if style == "star":
            points = [
                x + 62, y - 5, x + 68, y + 13, x + 89, y + 13, x + 72, y + 24,
                x + 78, y + 42, x + 62, y + 31, x + 46, y + 42, x + 52, y + 24,
                x + 35, y + 13, x + 56, y + 13,
            ]
            self.canvas.create_polygon(points, fill="#38BDF8", outline=accent, width=3)
            return
        if style == "bolt":
            points = [x + 70, y - 9, x + 46, y + 33, x + 64, y + 33, x + 55, y + 72, x + 86, y + 18, x + 68, y + 18]
            self.canvas.create_polygon(points, fill=accent, outline="#FFE7B3", width=3)
            return
        self.canvas.create_line(x + 62, y - 3, x + 62, y + 18, fill=accent, width=4, capstyle=tk.ROUND)
        self.canvas.create_oval(x + 53, y - 14, x + 71, y + 4, fill=core, outline="#D7FFE0", width=3)

    def round_rect(self, x1: int, y1: int, x2: int, y2: int, radius: int, **kwargs: object) -> None:
        points = [
            x1 + radius,
            y1,
            x2 - radius,
            y1,
            x2,
            y1,
            x2,
            y1 + radius,
            x2,
            y2 - radius,
            x2,
            y2,
            x2 - radius,
            y2,
            x1 + radius,
            y2,
            x1,
            y2,
            x1,
            y2 - radius,
            x1,
            y1 + radius,
            x1,
            y1,
        ]
        self.canvas.create_polygon(points, smooth=True, **kwargs)

    def draw_bubble(self, accent: str, tagline: str) -> None:
        tips = self.active_tips()
        tip = tips[self.tip_index % len(tips)]
        status = self.status_snapshot.get("Status", tagline)
        updated = self.status_snapshot.get("Updated", "live helper")
        core = self.mood_color()

        self.round_rect(122, 20, 342, 148, 15, fill="#0B1117", outline=accent, width=3)
        self.canvas.create_polygon(122, 86, 103, 96, 122, 105, fill="#0B1117", outline=accent)
        self.canvas.create_text(136, 39, text=f"{self.name}: {tagline}", anchor="w", fill=accent, font=("Segoe UI", 9, "bold"))
        self.round_rect(136, 53, 258, 74, 8, fill="#111A24", outline=core, width=2)
        self.canvas.create_text(145, 63, text=status, anchor="w", fill="#F3F7FA", font=("Segoe UI", 8, "bold"), width=104)
        self.canvas.create_text(266, 63, text=updated, anchor="w", fill="#A8B3C2", font=("Segoe UI", 7))
        self.canvas.create_text(
            136,
            104,
            text=tip,
            anchor="w",
            fill="#F3F7FA",
            font=("Segoe UI", 10),
            width=190,
        )
        self.canvas.create_text(136, 137, text="Drag me. Right-click cycles. Space = tip. Double-click hides bubble. Esc closes.", anchor="w", fill="#A8B3C2", font=("Segoe UI", 7), width=190)

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    DesktopCompanion().run()
