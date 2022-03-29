from krita import *
from PyQt5.QtWidgets import *


class GitDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Git docker")

        layout = QHBoxLayout()
        layout.addWidget(QLabel(i18n('Foo')))

        widget = QWidget()
        widget.setLayout(layout)

        self.setWidget(widget)

    def canvasChanged(self, canvas):
        pass


Krita.instance().addDockWidgetFactory(DockWidgetFactory(
    "gitDocker", DockWidgetFactoryBase.DockRight, GitDocker))
