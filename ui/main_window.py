from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QComboBox, QPushButton, QHBoxLayout, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from core.file_loader import is_audio_file, get_audio_files_in_folder
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QPixmap, QDragEnterEvent, QDropEvent
from PyQt6.QtGui import QDesktopServices
import os

from mutagen.id3 import ID3, APIC, error as ID3Error
from mutagen.mp3 import MP3

class AudioItemWidget(QWidget):
    expanded_changed = pyqtSignal(object)

    def __init__(self, filepath):
        super().__init__()
        self.filepath = filepath
        self.expanded = False
        self.edited_type = None
        self.new_cover_path = None

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(4)

        # Label con nombre archivo
        self.label = QLabel(os.path.basename(filepath))
        self.label.setStyleSheet("font-weight: normal; color: #222222;")
        self.label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.main_layout.addWidget(self.label)

        # Menú oculto (inicio oculto)
        self.menu_widget = QWidget()
        self.menu_layout = QVBoxLayout()
        self.menu_layout.setContentsMargins(20, 0, 0, 0)
        self.menu_layout.setSpacing(6)

        self.cover_label = QLabel()
        self.cover_label.setFixedSize(100, 100)
        self.cover_label.setStyleSheet("border: 1px solid #aaa;")
        self.cover_label.setAcceptDrops(True)
        self.cover_label.dragEnterEvent = self.cover_drag_enter
        self.cover_label.dropEvent = self.cover_drop_event

        # Carga la carátula embebida si existe, sino imagen por defecto
        try:
            audio = ID3(self.filepath)
            apic = audio.getall("APIC")
            if apic:
                pix = QPixmap()
                pix.loadFromData(apic[0].data)
                self.cover_label.setPixmap(pix.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio))
            else:
                raise KeyError
        except Exception:
            self.cover_label.setPixmap(QPixmap("default_cover.png").scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio))

        self.menu_layout.addWidget(QLabel("Carátula actual:"))
        self.menu_layout.addWidget(self.cover_label)

        self.path_label = QLabel(self.filepath)
        self.path_label.setWordWrap(True)
        self.menu_layout.addWidget(QLabel("Ubicación del archivo:"))
        self.menu_layout.addWidget(self.path_label)

        self.search_image_button = QPushButton("Buscar imagen en internet")
        self.search_image_button.clicked.connect(self.search_image_online)
        self.menu_layout.addWidget(self.search_image_button)

        self.combo = QComboBox()
        self.combo.addItems([
            "Audio completo",
            "Remix",
            "Edit",
            "Canción original",
            "Otro"
        ])
        self.combo.currentIndexChanged.connect(self.type_changed)
        self.menu_layout.addWidget(QLabel("Selecciona el tipo de audio:"))
        self.menu_layout.addWidget(self.combo)

        self.menu_widget.setLayout(self.menu_layout)
        self.menu_widget.setVisible(False)
        self.main_layout.addWidget(self.menu_widget)
        self.setLayout(self.main_layout)

        # Click en label para expandir/colapsar menú
        self.label.mousePressEvent = self.toggle_menu

    def toggle_menu(self, event):
        self.expanded = not self.expanded
        self.menu_widget.setVisible(self.expanded)
        self.expanded_changed.emit(self)

    def type_changed(self, index):
        self.edited_type = self.combo.currentText()

    def cover_drag_enter(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            if os.path.splitext(url.toLocalFile())[-1].lower() in (".png", ".jpg", ".jpeg"):
                event.acceptProposedAction()

    def cover_drop_event(self, event: QDropEvent):
        url = event.mimeData().urls()[0]
        path = url.toLocalFile()
        pix = QPixmap(path).scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio)
        self.cover_label.setPixmap(pix)
        self.new_cover_path = path

    def search_image_online(self):
        query = os.path.splitext(os.path.basename(self.filepath))[0].replace(" ", "+")
        url = QUrl(f"https://www.google.com/search?tbm=isch&q={query}")
        QDesktopServices.openUrl(url)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Metadata Editor - Editor Inline")
        self.resize(600, 500)

        self.layout = QVBoxLayout()
        self.label = QLabel("Arrastra archivos o carpetas aquí")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.label)

        self.list_widget = QListWidget()
        self.layout.addWidget(self.list_widget)

        # Botón guardar abajo derecha
        self.save_button = QPushButton("Guardar cambios")
        self.save_button.setFixedWidth(150)
        self.save_button.clicked.connect(self.save_changes)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        self.layout.addLayout(button_layout)

        self.setLayout(self.layout)
        self.setAcceptDrops(True)

        self.audio_items = []
        self.current_expanded = None

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        self.list_widget.clear()
        self.audio_items.clear()

        urls = event.mimeData().urls()
        paths = [url.toLocalFile() for url in urls]

        for path in paths:
            if os.path.isfile(path):
                if is_audio_file(path):
                    self.add_audio_item(path)
            elif os.path.isdir(path):
                audios = get_audio_files_in_folder(path)
                for audio in audios:
                    self.add_audio_item(audio)

    def add_audio_item(self, filepath):
        item = QListWidgetItem(self.list_widget)
        widget = AudioItemWidget(filepath)
        item.setSizeHint(widget.sizeHint())
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, widget)
        self.audio_items.append(widget)
        widget.expanded_changed.connect(self.handle_expanded_changed)

    def save_changes(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Selecciona carpeta para guardar")
        if not dir_path:
            return

        for widget in self.audio_items:
            tipo = widget.edited_type or "No definido"
            dest = os.path.join(dir_path, os.path.basename(widget.filepath))
            # Copia el archivo original
            import shutil
            shutil.copy(widget.filepath, dest)

            # Inserta carátula si cambió
            if widget.new_cover_path:
                try:
                    audio = ID3(dest)
                except ID3Error:
                    audio = MP3(dest, ID3=ID3)
                    audio.add_tags()
                    audio = audio.tags

                with open(widget.new_cover_path, "rb") as img:
                    audio.delall("APIC")
                    audio.add(
                        APIC(
                            encoding=3,
                            mime="image/jpeg",
                            type=3,
                            desc="Cover",
                            data=img.read()
                        )
                    )
                audio.save(dest)


            print(f"Guardado: {dest}  Tipo: {tipo}")

        QMessageBox.information(self, "Guardado", "Los cambios fueron guardados correctamente.")

    def handle_expanded_changed(self, expanded_widget):
        if self.current_expanded and self.current_expanded is not expanded_widget:
            self.current_expanded.expanded = False
            self.current_expanded.menu_widget.setVisible(False)
            self.update_item_size(self.current_expanded)

        if expanded_widget.expanded:
            self.current_expanded = expanded_widget
            index = None
            count = self.list_widget.count()
            for i in range(count):
                item = self.list_widget.item(i)
                widget = self.list_widget.itemWidget(item)
                if widget == expanded_widget:
                    index = i
                    break
            if index is not None:
                self.list_widget.scrollToItem(self.list_widget.item(index))
            else:
                self.current_expanded = None

            self.update_item_size(expanded_widget)

    def update_item_size(self, audio_widget):
        count = self.list_widget.count()
        for i in range(count):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if widget == audio_widget:
                item.setSizeHint(widget.sizeHint())
                break
