from krita import *
from PyQt5.QtWidgets import *


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
        DOC = Krita.instance().activeDocument()

        if DOC is not None:
            self.label.setText(DOC.fileName())


Krita.instance().addDockWidgetFactory(DockWidgetFactory(
    "gitDocker", DockWidgetFactoryBase.DockRight, GitDocker))
