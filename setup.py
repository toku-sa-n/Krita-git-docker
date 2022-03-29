from distutils.core import setup

DESC = 'A Krita plugin for viewing Krita files in other git revisions.'

setup(
    name='gitdocker',
    version='0.1',
    description=DESC,
    author='Hiroki Tokunaga',
    author_email='tokusan441@gmail.com',
    url='https://github.com/toku-sa-n/Krita-git-docker',
    install_requires=['git'],
    packages=['gitdocker'],)
