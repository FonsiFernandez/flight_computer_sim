import re


LOG_LINE_PATTERN = re.compile(
    r"\[(?P<level>INFO|WARN|ERROR)\]\[T\+(?P<time>\d+)\s+ms\]\s+(?P<message>.+)"
)


class LogParser:
    @staticmethod
    def parse(line: str) -> dict | None:
        match = LOG_LINE_PATTERN.search(line)
        if not match:
            return None

        return {
            "level": match.group("level"),
            "time_ms": int(match.group("time")),
            "message": match.group("message"),
        }