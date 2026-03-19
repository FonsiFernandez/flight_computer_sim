import queue
import subprocess
import threading


class LiveSession:
    PROCESS_ENDED_MARKER = "__PROCESS_ENDED__"

    def __init__(self):
        self.process = None
        self.output_queue = queue.Queue()
        self.reader_thread = None
        self.running_reader = False
        self.executable_path: str | None = None

    def start(self, executable_path: str) -> None:
        self.stop()

        self.executable_path = executable_path
        self.process = subprocess.Popen(
            [executable_path],
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        self.running_reader = True
        self.reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self.reader_thread.start()

    def _reader_loop(self) -> None:
        if self.process is None or self.process.stdout is None:
            return

        while self.running_reader:
            line = self.process.stdout.readline()
            if not line:
                break
            self.output_queue.put(line.strip())

        self.output_queue.put(self.PROCESS_ENDED_MARKER)

    def consume_available_lines(self) -> list[str]:
        lines: list[str] = []

        while True:
            try:
                lines.append(self.output_queue.get_nowait())
            except queue.Empty:
                break

        return lines

    def send_command(self, cmd: str) -> None:
        if self.process is None or self.process.stdin is None:
            return

        self.process.stdin.write(cmd + "\n")
        self.process.stdin.flush()

    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def stop(self) -> None:
        self.running_reader = False

        if self.process is not None and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass

        if self.reader_thread is not None and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=1)

        self.process = None
        self.reader_thread = None
        self.executable_path = None

        while True:
            try:
                self.output_queue.get_nowait()
            except queue.Empty:
                break