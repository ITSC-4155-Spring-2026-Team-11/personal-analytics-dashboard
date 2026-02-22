from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox
)

from datetime import date
from services.api_client import submit_feedback

class FeedbackView(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        label = QLabel("Daily Feedback (Stress Level 1–5)")
        label.setStyleSheet("font-size: 16px;")

        self.stress_input = QSpinBox()
        self.stress_input.setRange(1, 5)
        self.stress_input.setValue(3)

        submit_btn = QPushButton("Submit Feedback")
        submit_btn.clicked.connect(self.submit)

        layout.addWidget(label)
        layout.addWidget(self.stress_input)
        layout.addWidget(submit_btn)

    def submit(self):
        payload = {
            "date": date.today().isoformat(),
            "stress_level": self.stress_input.value()
        }
        submit_feedback(payload)
