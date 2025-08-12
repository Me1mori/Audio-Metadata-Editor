from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox, QDialogButtonBox
)

class AudioTypeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selecciona el tipo de audio")

        self.layout = QVBoxLayout()
        self.label = QLabel("¿Qué tipo de audio es este?")
        self.layout.addWidget(self.label)

        self.combo = QComboBox()
        self.combo.addItems([
            "Audio completo (varias canciones)",
            "Remix",
            "Edit",
            "Canción original",
            "Otro"
        ])
        self.layout.addWidget(self.combo)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

        self.setLayout(self.layout)

    def get_selection(self):
        return self.combo.currentText()
