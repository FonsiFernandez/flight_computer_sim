from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class StatusTile(QFrame):
    def __init__(self, title: str):
        super().__init__()
        self.setObjectName("StatusTile")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("TileTitle")

        self.value_label = QLabel("--")
        self.value_label.setObjectName("TileValue")

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)

        self.set_color("#7f8c9a")

    def set_value(self, text: str):
        self.value_label.setText(text)

    def set_color(self, color: str):
        self.setStyleSheet(f"""
            QFrame#StatusTile {{
                background-color: #10161d;
                border: 1px solid {color};
                border-radius: 10px;
            }}
            QLabel#TileTitle {{
                color: #9fb3c8;
                font-size: 11px;
                font-weight: 600;
            }}
            QLabel#TileValue {{
                color: {color};
                font-size: 18px;
                font-weight: 700;
            }}
        """)