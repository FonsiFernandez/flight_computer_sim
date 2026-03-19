from pathlib import Path

from models.telemetry import TelemetryFrame
from parsing.telemetry_parser import TelemetryParser


class ReplaySession:
    def __init__(self, step_frames: int = 1):
        self.step_frames = step_frames
        self.csv_path: str | None = None
        self.frames: list[TelemetryFrame] = []
        self.index = 0

    def load(self, csv_path: str | Path) -> None:
        self.csv_path = str(csv_path)
        self.frames = TelemetryParser.load_csv(csv_path)
        self.index = 0

    def restart(self) -> None:
        self.index = 0

    def next_frames(self) -> list[TelemetryFrame]:
        if self.index >= len(self.frames):
            return []

        out: list[TelemetryFrame] = []

        for _ in range(self.step_frames):
            if self.index >= len(self.frames):
                break
            out.append(self.frames[self.index])
            self.index += 1

        return out

    def is_finished(self) -> bool:
        return self.index >= len(self.frames)

    def progress_label(self) -> str:
        return f"{self.index}/{len(self.frames)}"