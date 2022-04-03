# Krita-git-docker
A Krita plugin for viewing Krita files in other git revisions.

## Screenshot

![Screenshot](screenshot.png)

## Features

* You can open your file in the previous commit.
* You can commit the file you are editing without opening your terminal.

## Installation

You need `GitPython`.

```sh
pip install --user GitPython
```

Clone this project and copy `gitdocker.desktop` and the `gitdocker/` directory into to the `pykrita` directory in your Krita resource folder. See [the documentation](https://docs.krita.org/en/reference_manual/resource_management.html#resource-management) for the location of the Krita resource folder.

## Usage

Open an image with Krita. If the file is untracked, the docker will say, "Git repository not found."

The docker will show the thumbnail if the file is tracked, and the combo box lists the newest ten commits' summaries. Click the "open" button to open the revision.

After modifying the image, write the commit message in the textbox and push the "Commit" button. Note that this will commit all staged files, not only the image.

## Limitation

Any commits made by this plugin are not GPG-signed.

## License

All files are licensed under GNU General Public License v3.0. See [LICENSE](https://github.com/toku-sa-n/Krita-git-docker/blob/main/LICENSE).
