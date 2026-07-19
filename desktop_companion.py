from __future__ import annotations

import json
from pathlib import Path
import tkinter as tk


APP_DIR = Path(__file__).resolve().parent
STATUS_FILE = APP_DIR / "data" / "companion_status.json"

PROFILES = {
    "Scout": {"accent": "#38BDF8", "tagline": "Clean setup coach"},
    "Null": {"accent": "#A78BFA", "tagline": "Quiet risk checker"},
    "Nova": {"accent": "#22D3EE", "tagline": "Catalyst and news scout"},
    "Flux": {"accent": "#F59E0B", "tagline": "Fast momentum watcher"},
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

        self.canvas = tk.Canvas(self.root, width=390, height=245, bg="#ff00ff", highlightthickness=0)
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
        self.rotate_tip()

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

    def rotate_tip(self) -> None:
        self.next_tip()
        self.root.after(9000, self.rotate_tip)

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
        mood = self.status_snapshot.get("Mood", "neutral")
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
        offset = -6 if self.bob < 40 else 0
        x = 58
        y = 82 + offset

        self.canvas.create_oval(x + 22, y + 110, x + 108, y + 127, fill="#000000", outline="", stipple="gray50")
        self.canvas.create_line(x + 62, y + 4, x + 62, y + 26, fill=accent, width=5, capstyle=tk.ROUND)
        self.canvas.create_oval(x + 52, y - 8, x + 72, y + 12, fill=core, outline="#D7FFE0", width=3)

        self.canvas.create_line(x + 17, y + 73, x + 4, y + 104, fill=accent, width=13, capstyle=tk.ROUND)
        self.canvas.create_line(x + 107, y + 73, x + 121, y + 100, fill=accent, width=13, capstyle=tk.ROUND)
        self.canvas.create_oval(x + 22, y + 50, x + 102, y + 125, fill="#101821", outline=accent, width=4)
        self.canvas.create_oval(x + 49, y + 75, x + 75, y + 101, fill=core, outline="")

        self.round_rect(x + 10, y + 18, x + 114, y + 78, 24, fill="#172232", outline=accent, width=4)
        self.round_rect(x + 28, y + 34, x + 96, y + 64, 14, fill="#0B1117", outline="#293546", width=2)
        self.canvas.create_oval(x + 45, y + 44, x + 56, y + 55, fill=core, outline="")
        self.canvas.create_oval(x + 68, y + 44, x + 79, y + 55, fill=core, outline="")
        self.canvas.create_arc(x + 51, y + 48, x + 73, y + 69, start=200, extent=140, style=tk.ARC, outline="#B7C2D0", width=3)

        self.canvas.create_line(x + 40, y + 121, x + 39, y + 143, fill=accent, width=12, capstyle=tk.ROUND)
        self.canvas.create_line(x + 86, y + 121, x + 87, y + 143, fill=accent, width=12, capstyle=tk.ROUND)
        self.canvas.create_text(x + 62, y + 166, text=self.name.upper(), fill=accent, font=("Segoe UI", 12, "bold"))

        if self.show_bubble:
            self.draw_bubble(accent, profile["tagline"])

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
