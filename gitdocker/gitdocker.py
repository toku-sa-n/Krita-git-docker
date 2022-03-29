from krita import *
from PyQt5.QtWidgets import *
from typing import Optional


class GitDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Git docker")

        self.label = QLabel('')

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.label)

        self.widget = QWidget()
        self.widget.setLayout(self.layout)

        self.setWidget(self.widget)

    def canvasChanged(self, canvas):
        PATH = self.current_file_path()

        if PATH is not None:
            self.label.setText(PATH)

    def current_file_path(self) -> Optional[str]:
        DOC = Krita.instance().activeDocument()

        if DOC is not None:
            return DOC.fileName()
        else:
            return None


Krita.instance().addDockWidgetFactory(DockWidgetFactory(
    "gitDocker", DockWidgetFactoryBase.DockRight, GitDocker))
