from krita import (
    DockWidget,
    Krita,
    DockWidgetFactory,
    DockWidgetFactoryBase,
    QImage,
    QPixmap,
    QSize)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QLabel,
    QComboBox,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QPushButton,
    QLineEdit)
from io import BytesIO
import subprocess
import tempfile
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
        self.file_handlers = []

        self.label = QLabel('')
        self.commitComboBox = QComboBox()
        self.commitComboBox.currentIndexChanged.connect(
            self.commit_combo_box_current_index_changed)

        self.open_button = QPushButton("Open")
        self.open_button.clicked.connect(self.open_button_clicked)

        self.commit_message_box = QLineEdit()

        self.commit_button = QPushButton("Commit")
        self.commit_button.clicked.connect(self.commit)

        self.commit_layout = QHBoxLayout()
        self.commit_layout.addWidget(self.commit_message_box)
        self.commit_layout.addWidget(self.commit_button)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.commitComboBox)
        self.layout.addWidget(self.open_button)
        self.layout.addLayout(self.commit_layout)

        self.widget = QWidget()
        self.widget.setLayout(self.layout)

        self.setWidget(self.widget)

    def __del__(self):
        for fp in self.file_handlers:
            fp.close()

    def canvasChanged(self, canvas):
        self.update_commits_and_combo_box()

    def update_commits_and_combo_box(self):
        self.path = active_document_path()

        if self.path is None or self.path == '':
            return

        self.repo = Repo(self.path, search_parent_directories=True)

        if self.repo is None:
            return

        MAX_ITEMS = 10
        self.commits = list(itertools.islice(
            self.repo.iter_commits(paths=self.path), MAX_ITEMS))

        self.commitComboBox.clear()
        self.commitComboBox.addItems(map(lambda c: c.summary, self.commits))

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

        THUMBSIZE = QSize(200, 150)

        thumbnail = thumbnail.scaled(
            THUMBSIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.label.setPixmap(QPixmap.fromImage(thumbnail))

    def get_revision(self, HEXSHA):
        if self.path is None:
            return None

        if self.repo is None:
            return None

        RELPATH = os.path.relpath(self.path, self.repo.working_tree_dir)

        # Do not use GitPython's show command because it has a bug and
        # truncates the last '\n', making the output invalid. See
        # https://stackoverflow.com/questions/71672179/the-file-is-not-a-zip-file-error-for-the-output-of-git-show-by-gitpython
        COMMAND = ["git", "show", "%s:%s" % (HEXSHA, RELPATH)]
        p = subprocess.Popen(COMMAND, stdout=subprocess.PIPE,
                             cwd=self.repo.working_tree_dir)
        out, _ = p.communicate()
        return out

    def commit_combo_box_current_index_changed(self, index):
        self.get_thumbnail(self.commits[index].hexsha)

    def open_button_clicked(self):
        FP = tempfile.NamedTemporaryFile()
        RAW = self.get_revision(
            self.commits[self.commitComboBox.currentIndex()])

        FP.write(RAW)

        self.file_handlers.append(FP)

        D = Krita.instance().openDocument(FP.name)
        Krita.instance().activeWindow().addView(D)

    def commit(self):
        if self.repo is None:
            return

        self.repo.index.add([self.path])
        self.repo.index.commit(self.commit_message_box.text())

        self.commit_message_box.clear()

        self.update_commits_and_combo_box()


def active_document_path():
    DOC = Krita.instance().activeDocument()

    if DOC is not None:
        return DOC.fileName()
    else:
        return None


def retrieve_commits_including_path(PATH):
    REPO = Repo(PATH, search_parent_directories=True)

    return REPO.iter_commits(paths=PATH)


Krita.instance().addDockWidgetFactory(DockWidgetFactory(
    "gitDocker", DockWidgetFactoryBase.DockRight, GitDocker))
