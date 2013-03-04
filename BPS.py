# BPS
# Handles the import and export of BPS patches.

from io import BytesIO
import json

from bps.apply import apply_to_files
from bps.diff import diff_bytearrays
from bps.io import read_bps, write_bps
from bps.operations import Header, SourceCRC32, TargetCRC32
from bps.validate import check_stream


class BPSPatch(BytesIO):
    """The standard patch format class, used to import and export patches."""

    def __init__(self, patchPath, new=False):
        """Loads an existing BPS patch or creates a new one."""

        # Set up the initial state.
        self.header = 0
        self.info = None
        self.metadata = None
        self.source = [None, None]
        self.target = [None, None]

        # Initialize the data.
        if not new:
            BytesIO.__init__(self, open(patchPath, "rb").read())
            self.valid = self.checkValidity()
        else:
            BytesIO.__init__(self)
            self.patchPath = patchPath

    def applyToTarget(self, rom):
        """Applies the patch to the target ROM."""

        # Make a copy of the ROM.
        self.seek(0)
        self.truncate(self.target[0])
        rom.seek(0)
        target = rom
        source = rom.copy()

        apply_to_files(self, source, target, self.header)

    def checkValidity(self):
        """Checks the validity of the patch and loads the patch's details."""

        # Try to load the patch's details.
        try:
            iterable = check_stream(read_bps(self))
            for i, item in enumerate(iterable):
                if isinstance(item, Header):
                    self.metadata = item.metadata
                    self.source[0] = item.sourceSize
                    self.target[0] = item.targetSize
                elif isinstance(item, SourceCRC32):
                    self.source[1] = item.value
                elif isinstance(item, TargetCRC32):
                    self.target[1] = item.value
            print("BPSPatch.checkValidity():\n"
                  "\tSource Size: {}. Source CRC32: {}.\n"
                  "\tTarget Size: {}. Target CRC32: {}.".format(self.source[0],
                  self.source[1], self.target[0], self.target[1]))
        except:
            return False

        # Check to see if it is an EBPatcher-created patch.
        try:
            self.info = json.loads(self.metadata)
            assert self.info["patcher"] == "EBPatcher"
            print("BPSPatch.checkValidity(): Patch made with EBPatcher.\n"
                  "\tTitle: {}\n\tAuthor: {}\n\tDescription: {}".format(
                  self.info["title"], self.info["author"],
                  self.info["description"]))
        except:
            self.info = None
            print("BPSPatch.checkValidity(): Patch not made with EBPatcher.")

        # If we made it this far, the patch is valid.
        return True

    def createFromSource(self, sourceROM, targetROM, metadata):
        """Creates a BPS patch from the source and target ROMs."""

        # Load the patch data.
        sourceData = sourceROM.getvalue()
        targetData = targetROM.getvalue()
        blockSize = 64  # A big block size is used to speed things up.
        iterable = diff_bytearrays(blockSize, sourceData, targetData, metadata)
        write_bps(iterable, self)

        # Write the patch to a file.
        f = open(self.patchPath, "wb")
        f.write(self.getvalue())
        f.close()

