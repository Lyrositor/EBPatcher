#!/usr/bin/env python3
# EarthBound Patcher
# Easy-to-use EarthBound ROM patcher for hack distribution.

import array
import os
import re
import sys

from PyQt4 import QtCore, QtGui, uic
import res

from BPS import *
from IPS import *
from ROM import *

# The hack repository website.
WEBSITE = "http://starmen.net/pkhack/"

def cap(s, l):
    """Caps a string to a certain length and appends "..." afterwards.
    Source: http://stackoverflow.com/questions/11602386/#11602405"""

    return s if len(s) <= l else s[0:l - 3] + "..."


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

        # Load the main window.
        QtGui.QApplication.__init__(self, args)
        self.main = QtGui.QMainWindow()
        uic.loadUi("ui/Main.ui", self.main)
        self.main.show()

        # The headered/unheadered buttons need to be able to be both unset.
        self.buttonGroup = QtGui.QButtonGroup()
        self.buttonGroup.addButton(self.main.ApplyStep2Headered)
        self.buttonGroup.addButton(self.main.ApplyStep2Unheadered)

        # Connect the signals.
        self.connect(self.main.HelpButton, QtCore.SIGNAL("clicked()"),
                     self.openAboutDialog)
        self.connect(self.main.ApplyStep1Button, QtCore.SIGNAL("clicked()"),
                     lambda button=1: self.selectROM(button))
        self.connect(self.main.ApplyStep1Field,
                     QtCore.SIGNAL("textChanged(QString)"),
                     lambda romPath: self.checkROM(romPath, 1))
        self.connect(self.main.ApplyStep2Button, QtCore.SIGNAL("clicked()"),
                     lambda button=1: self.selectPatch(button))
        self.connect(self.main.ApplyStep2Field,
                     QtCore.SIGNAL("textChanged(QString)"), self.checkPatch)
        self.connect(self.main.ApplyStep2Headered,
                     QtCore.SIGNAL("toggled(bool)"), self.setHeadered)
        self.connect(self.main.ApplyStep2Unheadered,
                     QtCore.SIGNAL("toggled(bool)"), self.setUnheadered)
        self.connect(self.main.ApplyPatchButton, QtCore.SIGNAL("clicked()"),
                     self.applyPatchToROM)
        self.connect(self.main.CreateStep1CleanButton,
                     QtCore.SIGNAL("clicked()"),
                     lambda button=2: self.selectROM(button))
        self.connect(self.main.CreateStep1HackedButton,
                     QtCore.SIGNAL("clicked()"),
                     lambda button=3: self.selectROM(button))
        self.connect(self.main.CreateStep1CleanField,
                     QtCore.SIGNAL("textChanged(QString)"),
                     lambda romPath: self.checkROM(romPath, 2))
        self.connect(self.main.CreateStep1HackedField,
                     QtCore.SIGNAL("textChanged(QString)"),
                     lambda romPath: self.checkROM(romPath, 3))
        self.connect(self.main.CreateStep2Button, QtCore.SIGNAL("clicked()"),
                     lambda button=2: self.selectPatch(button))
        self.connect(self.main.CreatePatchButton, QtCore.SIGNAL("clicked()"),
                     self.createPatchFromROMs)
        self.connect(self, QtCore.SIGNAL("startCreatingPatch"),
                     self.startCreatingPatch, QtCore.Qt.QueuedConnection)

    def openAboutDialog(self):
        """Opens the "About" dialog window."""

        self.about = QtGui.QDialog()
        uic.loadUi("ui/About.ui", self.about)
        self.connect(self.about.GetMore, QtCore.SIGNAL("clicked()"), lambda w=0:
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

        romPath = QtGui.QFileDialog.getOpenFileName(self.main, "Open ROM", "",
                                                    "ROM files (*.smc *.sfc)")
        if romPath:
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
                self.createHackedROM = ROM(romPath, False)
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
                warning = ("<strong>Warning:</strong> this isn't a known clean "
                          "ROM. Applying a patch to it might corrupt it.")
                self.main.ApplyStep1Notice.setStyleSheet("color: red")
                self.main.ApplyStep1Notice.setText(warning)

            # Set up to the next step.
            self.main.ApplyStep2.setEnabled(True)

            # Reload the UI.
            if self.applyPatch:
                self.checkPatch()
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
                self.checkPatch()
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
                self.checkPatch()

    def selectPatch(self, button):
        """Opens the file selection dialogue for the patch."""

        # Has the button from the Apply Patch screen been pressed?
        if button == 1:
            patchPath = QtGui.QFileDialog.getOpenFileName(self.main,
                                                          "Open IPS/BPS patch",
                                                          "", "IPS/BPS patches "
                                                          "(*.bps *.ips)")
            if patchPath:
                self.resetApplyStep(2)
                if os.path.splitext(patchPath)[1] == ".bps":
                    self.applyPatch = BPSPatch(patchPath)
                else:
                    self.applyPatch = IPSPatch(patchPath)
                self.main.ApplyStep2Field.setText(patchPath)

        # Has the button from the Create Patch screen been pressed?
        elif button == 2:
            patchPath = QtGui.QFileDialog.getSaveFileName(self.main,
                                                          "Save BPS patch", "",
                                                          "BPS patch (*.bps)")
            if patchPath:
                self.resetCreateStep(2)
                if patchPath[-4:] != ".bps":
                    patchPath += ".bps"
                self.createPatch = BPSPatch(patchPath, True)
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

        # If it's an IPS patch, issue a warning to the user.
        if isinstance(self.applyPatch, IPSPatch):
            manual = True

        # If it's an EBPatcher BPS patch, display its metadata.
        elif isinstance(self.applyPatch, BPSPatch) and self.applyPatch.info:
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

        # If it's an unknown BPS patch, verify its checksum.
        elif isinstance(self.applyPatch, BPSPatch) and \
             self.applyPatch.source[1] != self.applyROM.crc:
            warning = ("<strong>Warning:</strong> the patch was not made "
                       "for this ROM. Applying it might corrupt the ROM.")
            self.main.ApplyStep2Notice.setStyleSheet("color: red;")
            self.main.ApplyStep2Notice.setAlignment(QtCore.Qt.AlignHCenter)
            self.main.ApplyStep2Notice.setText(warning)
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
            self.applyPatch.applyToTarget(self.applyROM)
            self.applyROM.writeToFile()
        except:
            QtGui.QMessageBox.critical(self.main, "Error",
                                       "There was an error applying the patch.")
            return
        self.resetApplyStep(2)
        self.resetApplyStep(1)
        QtGui.QMessageBox.information(self.main, "Success",
                                      "The patch was successfully applied.")

    def createPatchFromROMs(self):
        """Creates a BPS patch from the selected ROMs."""

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
    a = EBPatcher(sys.argv)
    sys.exit(a.exec_())
