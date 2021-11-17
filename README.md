EBPatcher
=========

*An easy-to-use EarthBound ROM patcher.*

**EarthBound Patcher** is a brand-new tool to assist with the creation and distribution of hacks for EarthBound ROMs. Its features include:

* **Creation and Application:** EarthBound Patcher can create EBP (EarthBound Patch) patches as well as apply IPS or EBP patches, including patches created with other patchers.
* **Portability:** EarthBound Patcher runs on Windows, Mac and Linux.
* **Ease-of-use:** EarthBound Patcher makes applying and creating hacks dead simple – no more will you have to worry about ROM headers or their lack thereof; EarthBound Patcher tries to automatically detect what kind of ROM to patch. It can even detect if you're using an unconventional ROM, in which case it will patch it to the standard version.
* **Patch Metadata:** EarthBound Patcher created patches can contain metadata, including the patch’s title, the patch’s author and a short description for the patch. This information is displayed by EarthBound Patcher when you open the patch for applying. This ensures you always know what a patch is for.

EarthBound Patcher is licensed under the terms of the [GNU Public License v3](http://www.gnu.org/licenses/gpl.html).

## Installing ##
If a binary version of EarthBound Patcher does not exist for your system, you will have to install and run EarthBound Patcher manually, using Python. However, **Don't Panic**, as there are very few steps to do so.

EarthBound Patcher requires [Python 3.2](http://python.org/) or higher to run. Additionally, you will need the [PyQt5](http://www.riverbankcomputing.com/software/pyqt/intro) module (for Python 3).

Once you have downloaded and installed the dependencies, you will have to clone the repository and run EarthBound Patcher:

    git clone https://github.com/Lyrositor/EBPatcher.git
    cd EBPatcher
    python3.2 EBPatcher.py

The exact commands you need to type might vary, depending on your operating system.
