from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class PlotWidget(FigureCanvas):
    def __init__(self):
        self.figure = Figure(facecolor="#0b0f14")
        super().__init__(self.figure)

        self.ax = self.figure.add_subplot(111)
        self.ax2 = None

        self._setup_dark_axes()

    def _setup_dark_axes(self):
        self.ax.set_facecolor("#10161d")
        self.ax.tick_params(colors="#9fb3c8")

        for spine in self.ax.spines.values():
            spine.set_color("#3a4654")

        self.ax.title.set_color("#f5f8fb")
        self.ax.xaxis.label.set_color("#d9e2ec")
        self.ax.yaxis.label.set_color("#d9e2ec")
        self.ax.grid(True, color="#2c3846", alpha=0.35)

    def clear(self, with_secondary: bool = False):
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self._setup_dark_axes()

        self.ax2 = self.ax.twinx() if with_secondary else None
        if self.ax2 is not None:
            self.ax2.tick_params(colors="#9fb3c8")
            for spine in self.ax2.spines.values():
                spine.set_color("#3a4654")
            self.ax2.yaxis.label.set_color("#d9e2ec")

    def get_axis_limits(self) -> dict:
        limits = {
            "xlim": self.ax.get_xlim(),
            "ylim": self.ax.get_ylim(),
        }

        if self.ax2 is not None:
            limits["y2lim"] = self.ax2.get_ylim()

        return limits

    def restore_axis_limits(self, limits: dict | None):
        if not limits:
            return

        self.ax.set_xlim(limits["xlim"])
        self.ax.set_ylim(limits["ylim"])

        if self.ax2 is not None and "y2lim" in limits:
            self.ax2.set_ylim(limits["y2lim"])

    def draw_idle_safe(self):
        self.figure.tight_layout()
        self.draw_idle()