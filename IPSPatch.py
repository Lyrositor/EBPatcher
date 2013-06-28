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

# IPSPatch
# Handles the import of IPS patches (legacy).
# Heavily based on the python-ips module.

from io import BytesIO
import os
import struct


class IPSPatch(BytesIO):
    """The legacy patch format class, used to import patches."""

    def __init__(self, patchPath, new=False):
        """Loads an existing IPS patch."""

        if not new:
            # Initialize the data.
            super().__init__(open(patchPath, "rb").read())
            self.header = 0

            # Check its validity and load the records.
            self.valid = self.checkValidity()
            self.records = self.loadRecords()
            if self.valid and self.records:
                print("IPSPatch.__init__(): Valid IPS patch.")
            else:
                print("IPSPatch.__init__(): Invalid IPS patch.")

    def checkValidity(self):
        """Checks whether or not this patch is valid."""

        if self.read(5) != b"PATCH":
            return False
        return True

    def loadRecords(self):
        """Loads the IPS records from the patch."""

        # Position the cursor at the start of the first record.
        self.seek(5)

        # Start loading the records.
        records = {}
        while True:

            # Read until an EOF is encountered.
            i = self.read(3)
            if i == b"EOF":
                break

            # If the end has been reached, the patch is corrupt.
            if not i:
                return None

            self.seek(-3, os.SEEK_CUR)

            # Get the record details.
            offset = int.from_bytes(self.read(3), "big")
            size = int.from_bytes(self.read(2), "big")

            # If it's an RLE record, treat it as such.
            if size == 0:
                i = self.read(2)
                sizeRLE = int.from_bytes(i, "big")
                diff = self.read(1) * sizeRLE

            # Otherwise, read it as a normal record.
            else:
                diff = self.read(size)

            records[offset] = diff

        return records

    def applyToTarget(self, rom):
        """Applies the patch to the target ROM's data."""

        # Expand the ROM if necessary.
        last = sorted(self.records)[len(self.records) - 1]
        newSize = last + len(self.records[last]) - self.header
        if newSize > len(rom.getvalue()):
            rom.modifySize(newSize)

        # Apply the records.
        for offset, diff in self.records.items():
            rom.seek(offset - self.header)
            rom.write(diff)
