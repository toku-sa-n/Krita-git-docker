from krita import *
from PyQt5.QtWidgets import *
from typing import Optional
from git import Repo
import itertools


class GitDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Git docker")

        self.repo = None
        self.path = None
        self.commits = []

        self.label = QLabel('')
        self.commitComboBox = QComboBox()
        self.commitComboBox.currentIndexChanged.connect(
            self.commit_combo_box_current_index_changed)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.commitComboBox)

        self.widget = QWidget()
        self.widget.setLayout(self.layout)

        self.setWidget(self.widget)

    def canvasChanged(self, canvas):
        self.path = self.current_file_path()

        if self.path is None:
            return

        self.repo = Repo(self.path, search_parent_directories=True)

        if self.repo is None:
            return

        MAX_ITEMS = 10
        self.commits = list(itertools.islice(
            self.repo.iter_commits(paths=self.path), MAX_ITEMS))

        self.commitComboBox.clear()
        self.commitComboBox.addItems(map(lambda c: c.summary, self.commits))

    def current_file_path(self) -> Optional[str]:
        DOC = Krita.instance().activeDocument()

        if DOC is not None:
            return DOC.fileName()
        else:
            return None

    def commit_combo_box_current_index_changed(self, index):
        self.label.setText(self.commits[index].hexsha)


Krita.instance().addDockWidgetFactory(DockWidgetFactory(
    "gitDocker", DockWidgetFactoryBase.DockRight, GitDocker))
