import unittest
import tempfile
from git import Repo


class TestGitMethods(unittest.TestCase):
    def test_git_init(self):
        directory = tempfile.TemporaryFile()
        repo = Repo.init(directory.name)
        assert not repo.bare


if __name__ == '__main__':
    unittest.main()
