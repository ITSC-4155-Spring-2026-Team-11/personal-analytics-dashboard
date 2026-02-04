from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTextEdit,
    QLabel
)

from services.api_client import get_today_schedule

class ScheduleView(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        label = QLabel("Today's Schedule")
        label.setStyleSheet("font-size: 16px;")

        self.output = QTextEdit()
        self.output.setReadOnly(True)

        load_btn = QPushButton("Load Schedule")
        load_btn.clicked.connect(self.load_schedule)

        layout.addWidget(label)
        layout.addWidget(load_btn)
        layout.addWidget(self.output)

    def load_schedule(self):
        data = get_today_schedule()
        self.output.setText(str(data))
