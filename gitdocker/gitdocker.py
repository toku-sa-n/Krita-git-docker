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


class TrackedDocument():
    def __init__(self):
        path = active_document_path()

        if not path:
            raise ValueError("The current document has an invalid path.")

        self.path = path

        self.repo = Repo(self.path, search_parent_directories=True)

        max_items = 10
        self.commits = list(itertools.islice(
            self.repo.iter_commits(paths=self.path), max_items))

    def fetch_thumbnail(self, hexsha):
        raw = self.get_revision(hexsha)

        if not raw:
            return None

        thumbnail = None
        if self.is_krita_file():
            thumbnail = fetch_thumbnail_from_krita_file(raw)
        else:
            thumbnail = QImage.fromData(raw)

        if not thumbnail:
            return None

        thumbSize = QSize(200, 150)

        return thumbnail.scaled(thumbSize, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def get_revision(self, hexsha):
        relpath = os.path.relpath(self.path, self.repo.working_tree_dir)

        # Do not use GitPython's show command because it has a bug and
        # truncates the last '\n', making the output invalid. See
        # https://stackoverflow.com/questions/71672179/the-file-is-not-a-zip-file-error-for-the-output-of-git-show-by-gitpython
        command = ["git", "show", "%s:%s" % (hexsha, relpath)]
        with subprocess.Popen(command, stdout=subprocess.PIPE, cwd=self.repo.working_tree_dir) as p:
            out, _ = p.communicate()
            return out

    def commit(self, message):
        if not message:
            raise ValueError("The commit message is empty.")

        if not self.is_modified_or_untracked():
            raise RuntimeError(
                "This document is neither modified nor untracked.")

        self.repo.index.add([self.path])
        self.repo.index.commit(message)

    def is_krita_file(self):
        extension = Path(self.path).suffix

        return extension in ['.kra', '.krz']

    def is_modified_or_untracked(self):
        relpath = os.path.relpath(self.path, self.repo.working_tree_dir)

        return relpath in self.modified_or_untracked_files()

    def modified_or_untracked_files(self):
        return self.untracked_files()+self.files_different_from_head()

    def untracked_files(self):
        return self.repo.git.execute(['git', 'ls-files', '--others', '--exclude-standard']).splitlines()

    def files_different_from_head(self):
        return self.repo.git.diff('HEAD', name_only=True).splitlines()


class GitDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Git docker")

        self.document = None
        self.file_handlers = []

        self.image_label = QLabel('')
        self.image_label.setAlignment(Qt.AlignCenter)

        self.message_label = QLabel('')
        self.commit_combo_box = QComboBox()
        self.commit_combo_box.currentIndexChanged.connect(
            self.commit_combo_box_current_index_changed)

        self.open_button = QPushButton("Open")
        self.open_button.clicked.connect(self.open_button_handler)

        self.commit_message_box = QLineEdit()

        self.commit_button = QPushButton("Commit")
        self.commit_button.clicked.connect(self.commit_button_handler)

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
        try:
            self.document = TrackedDocument()
        except (ValueError, InvalidGitRepositoryError):
            self.show_git_repository_not_found()
            return

        self.commit_combo_box.clear()
        self.commit_combo_box.addItems(
            map(lambda c: c.summary, self.document.commits))
        self.message_label.clear()

        if self.commit_combo_box.count() == 0:
            self.message_label.setText('This file is not tracked.')

    def set_thumbnail(self, hexsha):
        thumbnail = self.document.fetch_thumbnail(hexsha)

        if thumbnail is None:
            self.image_label.clear()
            self.message_label.setText("No thumbnail available.")
        else:
            self.image_label.setPixmap(QPixmap.fromImage(thumbnail))

    def commit_combo_box_current_index_changed(self, index):
        if index != -1:
            self.set_thumbnail(self.document.commits[index].hexsha)

    def open_button_handler(self):
        if self.commit_combo_box.count() == 0:
            return

        fp = tempfile.NamedTemporaryFile()
        raw = self.get_revision(
            self.document.commits[self.commit_combo_box.currentIndex()])

        fp.write(raw)

        self.file_handlers.append(fp)

        doc = Krita.instance().openDocument(fp.name)
        Krita.instance().activeWindow().addView(doc)

        self.update_commits_and_combo_box()

    def commit_button_handler(self):
        try:
            self.document.commit(self.commit_message_box.text())
        except ValueError:
            self.message_label.setText('Commit message is empty.')
            return
        except RuntimeError:
            self.message_label.setText('File is not changed.')
            return

        self.commit_message_box.clear()
        self.update_commits_and_combo_box()
        self.message_label.setText('Committed.')

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


def fetch_thumbnail_from_krita_file(raw):
    with zipfile.ZipFile(BytesIO(raw), "r") as uncompressed:
        for name in ["mergedimage.png", "preview.png"]:
            try:
                return QImage.fromData(uncompressed.read(name))
            except KeyError:
                pass

        return None


Krita.instance().addDockWidgetFactory(DockWidgetFactory(
    "gitDocker", DockWidgetFactoryBase.DockRight, GitDocker))
