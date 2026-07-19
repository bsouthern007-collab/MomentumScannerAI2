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

        self.canvas = tk.Canvas(self.root, width=420, height=260, bg="#ff00ff", highlightthickness=0)
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
        offset = int(math.sin(self.bob / 80 * math.tau) * 4)
        x = 56
        y = 84 + offset

        self.canvas.create_oval(x + 17, y + 125, x + 121, y + 144, fill="#000000", outline="", stipple="gray50")
        self.canvas.create_oval(x + 15, y + 43, x + 39, y + 73, fill="#101821", outline=accent, width=4)
        self.canvas.create_oval(x + 99, y + 43, x + 123, y + 73, fill="#101821", outline=accent, width=4)
        self.draw_character_crest(x, y, accent, core, profile["style"])

        self.canvas.create_line(x + 24, y + 86, x + 8, y + 118, fill=accent, width=14, capstyle=tk.ROUND)
        self.canvas.create_line(x + 112, y + 86, x + 128, y + 114, fill=accent, width=14, capstyle=tk.ROUND)
        self.canvas.create_oval(x + 2, y + 111, x + 20, y + 129, fill=accent, outline="#101821", width=2)
        self.canvas.create_oval(x + 119, y + 107, x + 137, y + 125, fill=accent, outline="#101821", width=2)

        self.round_rect(x + 24, y + 59, x + 112, y + 137, 28, fill="#101821", outline=accent, width=4)
        self.round_rect(x + 40, y + 75, x + 96, y + 114, 16, fill="#172232", outline="#293546", width=2)
        self.canvas.create_oval(x + 55, y + 84, x + 81, y + 110, fill=core, outline="")
        self.canvas.create_line(x + 42, y + 119, x + 94, y + 119, fill=accent, width=5, capstyle=tk.ROUND)

        self.round_rect(x + 12, y + 18, x + 124, y + 84, 28, fill="#172232", outline=accent, width=4)
        self.round_rect(x + 29, y + 34, x + 107, y + 68, 15, fill="#0B1117", outline="#293546", width=2)
        if profile["style"] == "hood":
            self.canvas.create_line(x + 43, y + 51, x + 58, y + 51, fill=accent, width=7, capstyle=tk.ROUND)
            self.canvas.create_line(x + 78, y + 51, x + 93, y + 51, fill=accent, width=7, capstyle=tk.ROUND)
            self.canvas.create_line(x + 50, y + 65, x + 88, y + 65, fill="#38BDF8", width=4, capstyle=tk.ROUND)
        else:
            self.canvas.create_oval(x + 48, y + 45, x + 59, y + 56, fill=core, outline="")
            self.canvas.create_oval(x + 77, y + 45, x + 88, y + 56, fill=core, outline="")
            self.canvas.create_arc(x + 54, y + 49, x + 82, y + 72, start=200, extent=140, style=tk.ARC, outline="#B7C2D0", width=3)

        self.canvas.create_line(x + 45, y + 133, x + 44, y + 154, fill=accent, width=12, capstyle=tk.ROUND)
        self.canvas.create_line(x + 91, y + 133, x + 92, y + 154, fill=accent, width=12, capstyle=tk.ROUND)
        self.canvas.create_oval(x + 31, y + 150, x + 58, y + 162, fill="#101821", outline=accent, width=3)
        self.canvas.create_oval(x + 78, y + 150, x + 105, y + 162, fill="#101821", outline=accent, width=3)
        self.canvas.create_text(x + 68, y + 181, text=self.name.upper(), fill=accent, font=("Segoe UI", 12, "bold"))

        if self.show_bubble:
            self.draw_bubble(accent, profile["tagline"])

    def draw_character_crest(self, x: int, y: int, accent: str, core: str, style: str) -> None:
        if style == "hood":
            self.canvas.create_arc(x + 28, y - 2, x + 108, y + 68, start=20, extent=140, style=tk.ARC, outline=accent, width=5)
            self.canvas.create_oval(x + 25, y + 4, x + 39, y + 18, fill="#38BDF8", outline="")
            self.canvas.create_oval(x + 97, y + 4, x + 111, y + 18, fill="#38BDF8", outline="")
            return
        if style == "star":
            points = [
                x + 68, y - 4, x + 76, y + 18, x + 100, y + 18, x + 80, y + 31,
                x + 88, y + 54, x + 68, y + 40, x + 48, y + 54, x + 56, y + 31,
                x + 36, y + 18, x + 60, y + 18,
            ]
            self.canvas.create_polygon(points, fill="#38BDF8", outline=accent, width=3)
            return
        if style == "bolt":
            points = [x + 76, y - 10, x + 48, y + 39, x + 69, y + 39, x + 58, y + 88, x + 95, y + 23, x + 73, y + 23]
            self.canvas.create_polygon(points, fill=accent, outline="#FFE7B3", width=3)
            return
        self.canvas.create_line(x + 68, y - 2, x + 68, y + 24, fill=accent, width=5, capstyle=tk.ROUND)
        self.canvas.create_oval(x + 57, y - 16, x + 79, y + 6, fill=core, outline="#D7FFE0", width=3)

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

        self.round_rect(146, 24, 382, 160, 18, fill="#0B1117", outline=accent, width=3)
        self.canvas.create_polygon(146, 96, 125, 107, 146, 116, fill="#0B1117", outline=accent)
        self.canvas.create_text(160, 44, text=f"{self.name}: {tagline}", anchor="w", fill=accent, font=("Segoe UI", 9, "bold"))
        self.round_rect(160, 58, 284, 78, 10, fill="#111A24", outline=core, width=2)
        self.canvas.create_text(169, 68, text=status, anchor="w", fill="#F3F7FA", font=("Segoe UI", 8, "bold"), width=106)
        self.canvas.create_text(292, 68, text=updated, anchor="w", fill="#A8B3C2", font=("Segoe UI", 7))
        self.canvas.create_text(
            160,
            107,
            text=tip,
            anchor="w",
            fill="#F3F7FA",
            font=("Segoe UI", 10),
            width=202,
        )
        self.canvas.create_text(160, 148, text="Drag me. Right-click cycles. Space = tip. Double-click hides bubble. Esc closes.", anchor="w", fill="#A8B3C2", font=("Segoe UI", 7))

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    DesktopCompanion().run()
