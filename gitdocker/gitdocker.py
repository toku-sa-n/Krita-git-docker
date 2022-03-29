from krita import *
from PyQt5.QtWidgets import *
from typing import Optional
from git import Repo


class GitDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Git docker")

        self.label = QLabel('')
        self.git_label = QLabel('')

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.git_label)

        self.widget = QWidget()
        self.widget.setLayout(self.layout)

        self.setWidget(self.widget)

    def canvasChanged(self, canvas):
        PATH = self.current_file_path()

        if PATH is None:
            return

        REPO = Repo(PATH, search_parent_directories=True)

        if REPO is None:
            return

        s = ''
        for commit in REPO.iter_commits(paths=PATH):
            s += commit.message+'\n'

        self.label.setText(s)

    def current_repo(self) -> Optional[Repo]:
        PATH = self.current_file_path()

        if PATH is not None:
            return Repo(PATH, search_parent_directories=True)
        else:
            return None

    def current_file_path(self) -> Optional[str]:
        DOC = Krita.instance().activeDocument()

        if DOC is not None:
            return DOC.fileName()
        else:
            return None


Krita.instance().addDockWidgetFactory(DockWidgetFactory(
    "gitDocker", DockWidgetFactoryBase.DockRight, GitDocker))
