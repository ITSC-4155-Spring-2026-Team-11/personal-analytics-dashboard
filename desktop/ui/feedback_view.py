from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel
)

from ui.schedule_view import ScheduleView
from ui.feedback_view import FeedbackView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Personal Analytics Dashboard")
        self.resize(800, 500)

        container = QWidget()
        layout = QVBoxLayout(container)

        title = QLabel("Personal Analytics Dashboard")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")

        self.schedule_view = ScheduleView()
        self.feedback_view = FeedbackView()

        layout.addWidget(title)
        layout.addWidget(self.schedule_view)
        layout.addWidget(self.feedback_view)

        self.setCentralWidget(container)
