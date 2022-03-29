from krita import *
from PyQt5.QtWidgets import *


class GitDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Git docker")
        self.widget = QWidget()
        self.main_layout = QHBoxLayout()
        self.main_layout.addWidget(QLabel(i18n('Foo')))
        self.widget.setLayout(self.main_layout)
        self.setWidget(self.widget)

    def canvasChanged(self, canvas):
        pass


Krita.instance().addDockWidgetFactory(DockWidgetFactory(
    "gitDocker", DockWidgetFactoryBase.DockRight, GitDocker))
