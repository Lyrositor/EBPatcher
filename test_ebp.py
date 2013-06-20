#!/usr/bin/env python3

import array
import unittest
from os import listdir, remove, chdir
from os.path import isfile, join
from shutil import copyfile
from hashlib import sha256

import sys
sys.path.append('../')

from EBPPatch import *
from ROM import *

def isRomFilename(fname):
    return fname.lower().endswith(".smc") or fname.lower().endswith(".sfc")

def checksumOfFile(fname):
    return sha256(open(fname, 'rb').read()).hexdigest()

def checksumOfRom(rom):
    return sha256(rom.getvalue()).hexdigest()

class testEbp(unittest.TestCase):
    """
    A test class to test the creation and application of EBP patches
    """

    TMP_ROM_FNAME = "/tmp/tmp.smc"
    TMP_EBP_FNAME = "/tmp/tmp.ebp"

    def setUp(self):
        self.cleanRoms= [ ROM(join("test/clean_roms", f)) for f in
                listdir("test/clean_roms") if isRomFilename(f) ]
        self.modifiedRoms = [ ROM(join("test/modified_roms", f)) for f in
                listdir("test/modified_roms") if isRomFilename(f) ]

    def tearDown(self):
        if isfile(self.TMP_EBP_FNAME):
            remove(self.TMP_EBP_FNAME)
        if isfile(self.TMP_ROM_FNAME):
            remove(self.TMP_ROM_FNAME)

    def testCreatePatchesConsistently(self):
        """
        Test creating a patch of every modified rom against every type of
        clean rom and assert that all of these patch files are identical.
        """
        metadata = json.dumps({"patcher": "EBPatcher", "author": "x",
                               "title": "y", "description": "z"})
        for modifiedRom in self.modifiedRoms:
            first = True
            checksum = None
            for cleanRom in self.cleanRoms:
                # Create a patch of the modified rom against the clean rom
                if isfile(self.TMP_EBP_FNAME):
                    remove(self.TMP_EBP_FNAME)
                patch = EBPPatch(self.TMP_EBP_FNAME, new=True)
                patch.createFromSource(cleanRom, modifiedRom, metadata)

                # Calculate and compare the checksums
                newChecksum = checksumOfFile(self.TMP_EBP_FNAME)
                print(modifiedRom.romPath, "*", cleanRom.romPath, "=",
                        newChecksum[:5])
                if first:
                    # If this is the first time, just calculate the checksum
                    checksum = newChecksum
                    first = False
                else:
                    self.assertEqual(checksum, newChecksum)

    def testApplyPatchesConsistentlyAndCorrectly(self):
        """
        Test applying a patch against all types of clean ROMs, and ensuring that
        the produced ROM is identical to the source ROM.
        """

        metadata = json.dumps({"patcher": "EBPatcher", "author": "x",
                               "title": "y", "description": "z"})

        cleanBaseRom = self.cleanRoms[0]

        for modifiedRom in self.modifiedRoms:
            # Create a patch of this modified ROM
            # We can use any arbitrary clean rom as the base since patches are
            # created consistently, as proven in the above test.
            if isfile(self.TMP_EBP_FNAME):
                remove(self.TMP_EBP_FNAME)
            patch = EBPPatch(self.TMP_EBP_FNAME, new=True)
            patch.createFromSource(cleanBaseRom, modifiedRom, metadata)

            del patch
            patch = EBPPatch(self.TMP_EBP_FNAME)

            # Create a copy of the modified rom without a header
            modifiedRomCopy = ROM(modifiedRom.romPath)
            if modifiedRomCopy.checkHeader() > 0:
                modifiedRomCopy.removeHeader()

            for cleanRom in self.cleanRoms:
                # Create a new temporary rom
                if isfile(self.TMP_ROM_FNAME):
                    remove(self.TMP_ROM_FNAME)
                copyfile(cleanRom.romPath, self.TMP_ROM_FNAME)
                targetRom = ROM(self.TMP_ROM_FNAME)

                # Apply the patch to the temporary ROM
                patch.applyToTarget(targetRom)

                # Compare the patched ROM vs the de-headered modified ROM
                inputChecksum = checksumOfRom(modifiedRomCopy)
                outputChecksum = checksumOfRom(targetRom)
                print(cleanRom.romPath, "(", inputChecksum[:5], ") *",
                        modifiedRom.romPath, "=", outputChecksum[:5])
                self.assertEqual(inputChecksum, outputChecksum)
                

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(testEbp))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
