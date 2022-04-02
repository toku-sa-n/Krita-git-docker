import itertools
import os
import subprocess
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path

from git import InvalidGitRepositoryError, Repo
from krita import (DockWidget, DockWidgetFactory, DockWidgetFactoryBase, Krita,
                   QImage, QPixmap, QSize)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QVBoxLayout, QWidget)


class GitDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Git docker")

        self.repo = None
        self.path = None
        self.commits = []
        self.file_handlers = []

        self.image_label = QLabel('')
        self.message_label = QLabel('')
        self.commit_combo_box = QComboBox()
        self.commit_combo_box.currentIndexChanged.connect(
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
        self.layout.addWidget(self.image_label)
        self.layout.addWidget(self.message_label)
        self.layout.addWidget(self.commit_combo_box)
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
            self.show_git_repository_not_found()
            return

        try:
            self.repo = Repo(self.path, search_parent_directories=True)
        except InvalidGitRepositoryError:
            self.repo = None
            self.show_git_repository_not_found()
            return

        max_items = 10
        self.commits = list(itertools.islice(
            self.repo.iter_commits(paths=self.path), max_items))

        self.commit_combo_box.clear()
        self.commit_combo_box.addItems(map(lambda c: c.summary, self.commits))
        self.message_label.clear()

    def set_thumbnail(self, hexsha):
        thumbnail = self.fetch_thumbnail(hexsha)

        if thumbnail is None:
            self.image_label.clear()
            self.message_label.setText("No thumbnail available.")
        else:
            self.image_label.setPixmap(QPixmap.fromImage(thumbnail))

    def fetch_thumbnail(self, hexsha):
        raw = self.get_revision(hexsha)

        if raw is None:
            return None

        thumbnail = None

        if is_krita_file(self.path):
            thumbnail = fetch_thumbnail_from_krita_file(raw)
        else:
            thumbnail = QImage.fromData(raw)

        if thumbnail is None:
            return None

        thumbsize = QSize(200, 150)

        return thumbnail.scaled(thumbsize, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def get_revision(self, hexsha):
        if self.path is None or self.path == '':
            return None

        if self.repo is None:
            return None

        relpath = os.path.relpath(self.path, self.repo.working_tree_dir)

        # Do not use GitPython's show command because it has a bug and
        # truncates the last '\n', making the output invalid. See
        # https://stackoverflow.com/questions/71672179/the-file-is-not-a-zip-file-error-for-the-output-of-git-show-by-gitpython
        command = ["git", "show", "%s:%s" % (hexsha, relpath)]
        with subprocess.Popen(command, stdout=subprocess.PIPE, cwd=self.repo.working_tree_dir) as p:
            out, _ = p.communicate()
            return out

    def commit_combo_box_current_index_changed(self, index):
        self.set_thumbnail(self.commits[index].hexsha)

    def open_button_clicked(self):
        if self.commit_combo_box.count() == 0:
            return

        fp = tempfile.NamedTemporaryFile()
        raw = self.get_revision(
            self.commits[self.commit_combo_box.currentIndex()])

        fp.write(raw)

        self.file_handlers.append(fp)

        doc = Krita.instance().openDocument(fp.name)
        Krita.instance().activeWindow().addView(doc)

        self.update_commits_and_combo_box()

    def commit(self):
        if self.repo is None:
            return

        if self.commit_message_box.Text() == '':
            self.message_label.setText('Commit message is empty.')
            return

        self.repo.index.add([self.path])
        self.repo.index.commit(self.commit_message_box.text())

        self.commit_message_box.clear()

        self.update_commits_and_combo_box()
        self.message_label.setText('Commited.')

    def show_git_repository_not_found(self):
        self.image_label.clear()
        self.message_label.setText('Git repository not found.')
        self.commit_combo_box.clear()


def active_document_path():
    doc = Krita.instance().activeDocument()

    if doc is not None:
        return doc.fileName()
    else:
        return None


def retrieve_commits_including_path(path):
    repo = Repo(path, search_parent_directories=True)

    return repo.iter_commits(paths=path)


def is_krita_file(path):
    extension = Path(path).suffix

    return extension in ['.kra', '.krz']


def fetch_thumbnail_from_krita_file(raw):
    with zipfile.ZipFile(BytesIO(raw), "r") as uncompressed:
        try:
            return QImage.fromData(
                uncompressed.read("mergedimage.png"))
        except KeyError:
            pass

        try:
            return QImage.fromData(
                uncompressed.read("preview.png"))
        except KeyError:
            return None


Krita.instance().addDockWidgetFactory(DockWidgetFactory(
    "gitDocker", DockWidgetFactoryBase.DockRight, GitDocker))
