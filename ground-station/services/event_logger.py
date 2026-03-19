from collections import deque
from datetime import datetime
from pathlib import Path


class EventLogger:
    def __init__(self, max_events: int = 200, logs_dir: str | Path = "logs"):
        self.max_events = max_events
        self.logs_dir = Path(logs_dir)

        self.lines = deque(maxlen=max_events)
        self.file = None
        self.path: Path | None = None

    def start(self, source_name: str) -> Path:
        self.logs_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_source = (
            source_name.replace("\\", "_")
            .replace("/", "_")
            .replace(":", "_")
        )

        self.path = self.logs_dir / f"events_{timestamp}_{safe_source}.log"
        self.file = open(self.path, "w", encoding="utf-8")
        return self.path

    def stop(self) -> None:
        if self.file is not None:
            self.file.close()

        self.file = None
        self.path = None

    def clear(self) -> None:
        self.lines.clear()

    def record(self, text: str) -> None:
        self.lines.appendleft(text)

        if self.file is not None:
            self.file.write(text + "\n")
            self.file.flush()

    def render_text(self) -> str:
        if not self.lines:
            return "WAITING FOR EVENTS..."
        return "\n".join(self.lines)