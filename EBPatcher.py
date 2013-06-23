#!/usr/bin/env python3

"""
    EarthBound Patcher - An easy-to-use EarthBound ROM patcher.
    Copyright (C) 2013  Lyrositor <gagne.marc@gmail.com>

    This file is part of EarthBound Patcher.

    EarthBound Patcher is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    EarthBound Patcher is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with EarthBound Patcher.  If not, see <http://www.gnu.org/licenses/>.
"""

# EarthBound Patcher
# An easy-to-use EarthBound ROM patcher.

import array
import os
import re
import sys

from PyQt4 import QtCore, QtGui
import res

from EBPPatch import *
from IPSPatch import *
from ROM import *
from ui import About, Main

# The current EBPatcher version.
VERSION = 1.0

# The hack repository website.
WEBSITE = "http://hacks.lyros.net/"

def cap(s, l):
    """Caps a string to a certain length and appends "..." afterwards.
    Source: http://stackoverflow.com/questions/11602386/#11602405"""

    return s if len(s) <= l else s[0:l - 3] + "..."


class MainWindow(QtGui.QMainWindow, Main.Ui_MainWindow):
    """The main window for EBPatcher."""


class AboutDialog(QtGui.QDialog, About.Ui_Dialog):
    """The about dialog for EBPatcher."""


class EBPatcher(QtGui.QApplication):
    """The Qt application used for EBPatcher."""

    def __init__(self, args):
        """Initializes the application and opens the main window."""

        # Initialize variables.
        self.applyPatch = None
        self.applyROM = None
        self.createPatch = None
        self.createCleanROM = None
        self.createHackedROM = None
        self.currentPath = ""

        # Load the main window.
        QtGui.QApplication.__init__(self, args)
        self.main = MainWindow()
        self.main.setupUi(self.main)
        self.main.show()

        # Set the version number.
        self.main.VersionNumber.setText("{0:.1f}".format(VERSION))

        # The headered/unheadered buttons need to be able to be both unset.
        self.buttonGroup = QtGui.QButtonGroup()
        self.buttonGroup.addButton(self.main.ApplyStep2Headered)
        self.buttonGroup.addButton(self.main.ApplyStep2Unheadered)

        # Connect the signals.
        self.main.HelpButton.clicked.connect(self.openAboutDialog)
        self.main.ApplyStep1Button.clicked.connect(lambda button=1:
                                                   self.selectROM(1))
        self.main.ApplyStep1Field.textChanged.connect(lambda romPath:
                                                      self.checkROM(romPath, 1))
        self.main.ApplyStep2Button.clicked.connect(lambda button=1:
                                                   self.selectPatch(1))
        self.main.ApplyStep2Field.textChanged.connect(self.checkPatch)
        self.main.ApplyStep2Headered.toggled.connect(self.setHeadered)
        self.main.ApplyStep2Unheadered.toggled.connect(self.setUnheadered)
        self.main.ApplyPatchButton.clicked.connect(self.applyPatchToROM)
        self.main.CreateStep1CleanButton.clicked.connect(lambda button=2:
                                                         self.selectROM(2))
        self.main.CreateStep1HackedButton.clicked.connect(lambda button=3:
                                                         self.selectROM(3))
        self.main.CreateStep1CleanField.textChanged.connect(lambda romPath:
                                                      self.checkROM(romPath, 2))
        self.main.CreateStep1HackedField.textChanged.connect(lambda romPath:
                                                      self.checkROM(romPath, 3))
        self.main.CreateStep2Button.clicked.connect(lambda button=2:
                                                    self.selectPatch(2))
        self.main.CreatePatchButton.clicked.connect(self.createPatchFromROMs)
        self.connect(self, QtCore.SIGNAL("startCreatingPatch"),
                     self.startCreatingPatch, QtCore.Qt.QueuedConnection)

    def openAboutDialog(self):
        """Opens the "About" dialog window."""

        self.about = AboutDialog()
        self.about.setupUi(self.about)
        self.about.GetMore.clicked.connect(lambda w=0:
                           QtGui.QDesktopServices.openUrl(QtCore.QUrl(WEBSITE)))
        self.about.setModal(True)
        self.about.show()

    def resetApplyStep(self, curStep=0):
        """Resets the current apply step to its default state."""

        self.main.ApplyStep2Notice.clear()
        self.main.ApplyStep2Notice.setStyleSheet("")
        self.main.ApplyPatchButton.setDisabled(True)
        # Reset everything to step 1, disabling step 2.
        if curStep == 1:
            self.applyROM = None
            self.main.ApplyStep1Field.clear()
            self.main.ApplyStep1Notice.clear()
            self.main.ApplyStep2.setDisabled(True)
        # Reset everything to step 2, disabling the apply button.
        elif curStep == 2:
            self.applyPatch = None
            self.main.ApplyStep2Field.clear()
            self.buttonGroup.setExclusive(False)
            self.main.ApplyStep2Headered.setChecked(False)
            self.main.ApplyStep2Unheadered.setChecked(False)
            self.buttonGroup.setExclusive(True)
            self.main.ApplyStep2Choice.setDisabled(True)
            self.main.ApplyStep2ChoiceLabel.setDisabled(True)

    def resetCreateStep(self, curStep=0, clean=True, hacked=True):
        """Resets the current create step to its default state."""

        self.main.CreatePatchButton.setDisabled(True)
        # Reset everything to step 1, disabling step 2.
        if curStep == 1:
            if clean:
                self.createCleanROM = None
                self.main.CreateStep1CleanField.clear()
            if hacked:
                self.createHackedROM = None
                self.main.CreateStep1HackedField.clear()
            self.main.CreateStep1Notice.clear()
            self.main.CreateStep1.setEnabled(True)
            self.main.CreateStep2.setDisabled(True)
        # Reset everything to step 2, disabling the create button.
        elif curStep == 2:
            self.createPatch = None
            self.main.CreateStep2Field.clear()
            self.main.CreateStep2PatchAuthor.clear()
            self.main.CreateStep2PatchDescription.clear()
            self.main.CreateStep2PatchTitle.clear()
            self.main.CreateStep2.setEnabled(True)

    def selectROM(self, button):
        """Opens the file selection dialogue for the EarthBound ROM."""

        romPath = QtGui.QFileDialog.getOpenFileName(self.main, "Open ROM",
                                                    self.currentPath,
                                                    "ROM files (*.smc *.sfc)")
        if romPath:
            self.currentPath = os.path.dirname(romPath)
            # Has the Apply Patch browse button been pressed?
            if button == 1:
                self.resetApplyStep(1)
                self.applyROM = ROM(romPath)
                self.main.ApplyStep1Field.setText(romPath)
            # Has the Clean ROM browse button been pressed?
            elif button == 2:
                self.createCleanROM = ROM(romPath)
                self.main.CreateStep1CleanField.setText(romPath)
            # Has the Hacked ROM browse button been pressed?
            elif button == 3:
                self.createHackedROM = ROM(romPath)
                self.main.CreateStep1HackedField.setText(romPath)

    def checkROM(self, romPath, field):
        """Check the validity of the specified ROM."""

        if field == 1:
            if not self.applyROM:
                return

            # Make sure the file is a valid EarthBound ROM.
            if not self.applyROM.valid:
                self.resetApplyStep(1)
                QtGui.QMessageBox.critical(self.main, "Error",
                                           "You have specified an invalid ROM.")
                return

            # If the ROM isn't a clean ROM, notify the user.
            if not self.applyROM.clean:
                warning = ("<strong>Warning:</strong> this file is not a clean "
                           "EarthBound ROM. Patching it may produce a ROM which"
                           " plays incorrectly.")
                self.main.ApplyStep1Notice.setStyleSheet("color: red")
                self.main.ApplyStep1Notice.setText(warning)

            # Set up to the next step.
            self.main.ApplyStep2.setEnabled(True)

            # Reload the UI.
            if self.applyPatch:
                self.checkPatch(None)
        elif field == 2:
            if not self.createCleanROM:
                return

            # The ROM has to be a clean ROM.
            if not self.createCleanROM.clean:
                self.resetCreateStep(1, True, False)
                QtGui.QMessageBox.critical(self.main, "Error", "This ROM must "
                                           "be a known clean ROM.")
                return

            # If both ROMs are open, set up the next step.
            if self.createHackedROM:
                self.main.CreateStep2.setEnabled(True)

            # Reload the UI.
            if self.createPatch:
                self.checkPatch(None)
        elif field == 3:
            if not self.createHackedROM:
                return

            # The hacked ROM need only be valid.
            if not self.createHackedROM.valid:
                self.resetCreateStep(1, False, True)
                QtGui.QMessageBox.critical(self.main, "Error",
                                           "You have specified an invalid ROM.")
                return

            # If both ROMs are open, set up the next step.
            if self.createCleanROM:
                self.main.CreateStep2.setEnabled(True)

            # Reload the UI.
            if self.createPatch:
                self.checkPatch(None)

    def selectPatch(self, button):
        """Opens the file selection dialogue for the patch."""

        # Has the button from the Apply Patch screen been pressed?
        if button == 1:
            patchPath = QtGui.QFileDialog.getOpenFileName(self.main,
                        "Open EBP/IPS patch", self.currentPath, "EBP/IPS "
                        "patches (*.ebp *.ips)")
            if patchPath:
                self.currentPath = os.path.dirname(patchPath)
                self.resetApplyStep(2)
                if os.path.splitext(patchPath)[1] == ".ebp":
                    self.applyPatch = EBPPatch(patchPath)
                else:
                    self.applyPatch = IPSPatch(patchPath)
                self.main.ApplyStep2Field.setText(patchPath)

        # Has the button from the Create Patch screen been pressed?
        elif button == 2:
            patchPath = QtGui.QFileDialog.getSaveFileName(self.main, "Save EBP "
                        "patch", os.path.join(self.currentPath, "patch.ebp"),
                        "EBP patch (*.ebp)")
            if patchPath:
                self.currentPath = os.path.dirname(patchPath)
                self.resetCreateStep(2)
                if patchPath[-4:] != ".ebp":
                    patchPath += ".ebp"
                self.createPatch = EBPPatch(patchPath, True)
                self.main.CreateStep2Field.setText(patchPath)
                self.main.CreatePatchButton.setEnabled(True)

    def checkPatch(self, patchPath):
        """Check the validity of the specified patch."""

        if not self.applyPatch:
            return

        # Check its validity and load its contents.
        if not self.applyPatch.valid:
            self.resetApplyStep(2)
            QtGui.QMessageBox.critical(self.main, "Error", "You have "
                                       "specified an invalid patch.")
            return

        manual = False

        # If it's an EBP with metadata, display its metadata.
        if isinstance(self.applyPatch, EBPPatch) and self.applyPatch.info:
            title = self.applyPatch.info["title"]
            if not title:
                title = "<em>Unknown</em>"
            author = self.applyPatch.info["author"]
            if not author:
                author = "<em>Unknown</em>"
            description = cap(self.applyPatch.info["description"], 150)
            if not description:
                description = "<em>Unknown</em>"
            information = ("<p><strong>Title:</strong> {}</p>"
                           "<p><strong>Author:</strong> {}</p>"
                           "<p><strong>Description:</strong> {}</p>".format(
                           title, author, description))
            self.main.ApplyStep2Notice.setAlignment(QtCore.Qt.AlignJustify)
            self.main.ApplyStep2Notice.setText(information)

        # If it's an EBP patch with no metadata or if it's an IPS patch, issue
        # a warning to the user.
        else:
            manual = True

        # If the user must specify whether the patch is for headered or
        # unheadered ROMs, enable the radio buttons, and vice-versa.
        if manual:
            self.main.ApplyStep2Choice.setEnabled(True)
            self.main.ApplyStep2ChoiceLabel.setEnabled(True)
            self.main.ApplyStep2Headered.setChecked(True)
        else:
            self.buttonGroup.setExclusive(False)
            self.main.ApplyStep2Headered.setChecked(False)
            self.main.ApplyStep2Unheadered.setChecked(False)
            self.buttonGroup.setExclusive(True)
            self.main.ApplyStep2Choice.setDisabled(True)
            self.main.ApplyStep2ChoiceLabel.setDisabled(True)
            self.applyPatch.header = 0

        # Let the user move on to the next step.
        self.main.ApplyPatchButton.setEnabled(True)

    def setHeadered(self, on):
        """Sets the patch to the headered type."""

        if on and self.applyPatch:
            self.applyPatch.header = 0x200
            self.main.ApplyStep2Unheadered.setChecked(False)

    def setUnheadered(self, on):
        """Sets the patch to the unheadered type."""

        if on and self.applyPatch:
            self.applyPatch.header = 0
            self.main.ApplyStep2Headered.setChecked(False)

    def applyPatchToROM(self):
        """Apply the selected patch to the selected ROM."""

        try:
            self.main.setCursor(QtCore.Qt.WaitCursor)
            self.applyPatch.applyToTarget(self.applyROM)
            self.applyROM.writeToFile()
        except:
            self.main.setCursor(QtCore.Qt.ArrowCursor)
            QtGui.QMessageBox.critical(self.main, "Error",
                                       "There was an error applying the patch.")
            return
        self.main.setCursor(QtCore.Qt.ArrowCursor)
        self.resetApplyStep(2)
        self.resetApplyStep(1)
        QtGui.QMessageBox.information(self.main, "Success",
                                      "The patch was successfully applied.")

    def createPatchFromROMs(self):
        """Creates a EBP patch from the selected ROMs."""

        self.main.CreateStep1.setDisabled(True)
        self.main.CreateStep2.setDisabled(True)
        self.main.CreatePatchButton.setDisabled(True)
        self.main.setCursor(QtCore.Qt.WaitCursor)
        self.emit(QtCore.SIGNAL("startCreatingPatch"))

    def startCreatingPatch(self):
        """Starts creating the patch in its own thread."""

        # Prepare the metadata.
        author = self.main.CreateStep2PatchAuthor.text()
        description = self.main.CreateStep2PatchDescription.toPlainText()
        title = self.main.CreateStep2PatchTitle.text()
        metadata = json.dumps({"patcher": "EBPatcher", "author": author,
                               "title": title, "description": description})

        # Try to create the patch; if it fails, display an error message.
        try:
            self.createPatch.createFromSource(self.createCleanROM,
                                              self.createHackedROM, metadata)
        except:
            QtGui.QMessageBox.critical(self.main, "Error",
                                       "There was an error creating the patch.")
            self.main.CreateStep1.setEnabled(True)
            self.main.CreateStep2.setEnabled(True)
            self.main.CreatePatchButton.setEnabled(True)
            self.main.setCursor(QtCore.Qt.ArrowCursor)
            return

        # Restore the window to its original setting, display a success message.
        self.main.setCursor(QtCore.Qt.ArrowCursor)
        self.resetCreateStep(2)
        self.resetCreateStep(1)
        QtGui.QMessageBox.information(self.main, "Success",
                                      "The patch was successfully created.")

########
# MAIN #
########

if __name__ == "__main__":
    print("EarthBound Patcher - {0:.1f}".format(VERSION))
    stdout = sys.stdout
    stderr = sys.stderr
    if ("-d" in sys.argv or "--debug" in sys.argv):
        print("Running in debug mode.")
    else:
        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(os.devnull, "w")
    a = EBPatcher(sys.argv)
    exit = a.exec_()
    sys.stdout = stdout
    sys.stderr = stderr
    sys.exit(exit)
