from krita import *
from PyQt5.QtWidgets import *
from io import BytesIO
import subprocess
from typing import Optional
from git import Repo
import zipfile
import os
from pathlib import Path
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

    def get_thumbnail(self, HEXSHA):
        RAW = self.get_revision(HEXSHA)

        if RAW is None:
            return None

        thumbnail = None
        EXTENSION = Path(self.path).suffix
        if EXTENSION == '.kra':
            UNCOMPRESSED = zipfile.ZipFile(BytesIO(RAW), "r")
            thumbnail = QImage.fromData(UNCOMPRESSED.read("mergedimage.png"))
            if thumbnail is None:
                thumbnail = QImage.fromData(UNCOMPRESSED.read("preview.png"))

        if thumbnail is None:
            self.label.setText("No thumbnail available")
            return None

        self.label.setPixmap(QPixmap.fromImage(thumbnail))

    def get_revision(self, HEXSHA):
        if self.path is None:
            return None

        if self.repo is None:
            return None

        RELPATH = os.path.relpath(self.path, self.repo.working_tree_dir)

        p = subprocess.Popen(["git", "show", "%s:%s" %
                             (HEXSHA, RELPATH)], stdout=subprocess.PIPE, cwd=self.repo.working_tree_dir)
        out, _ = p.communicate()
        return out

    def commit_combo_box_current_index_changed(self, index):
        self.get_thumbnail(self.commits[index].hexsha)


Krita.instance().addDockWidgetFactory(DockWidgetFactory(
    "gitDocker", DockWidgetFactoryBase.DockRight, GitDocker))
