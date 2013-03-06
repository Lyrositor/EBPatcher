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

# IPS
# Handles the import of IPS patches (legacy).
# Heavily based on the python-ips module.

from io import BytesIO
import os
import struct

def readInt(strValue):
    """Read a big-endian integer from the patch."""

    return struct.unpack_from(">I", b"\x00" * (4 - len(strValue)) + strValue)[0]


class IPSPatch(BytesIO):
    """The legacy patch format class, used to import patches."""

    def __init__(self, patchPath):
        """Loads an existing IPS patch."""

        # Initialize the data.
        BytesIO.__init__(self, open(patchPath, "rb").read())
        self.header = 0
        self.records = dict()
        self.valid = False

        # Check its validity and load the records.
        if self.getvalue() and self.read(5) == b"PATCH" and self.loadRecords():
            self.valid = True
            print("IPSPatch.__init__(): Valid IPS patch.")
        else:
            print("IPSPatch.__init__(): Invalid IPS patch.")

    def applyToTarget(self, rom):
        """Applies the patch to the target ROM's data."""

        for offset, diff in self.records.items():
            rom.seek(offset - self.header)
            rom.write(diff)

    def loadRecords(self):
        """Loads the IPS records from the patch."""

        # Position the cursor at the start of the first record.
        self.seek(5)

        # Start loading the records.
        while True:

            # Read until an EOF is encountered.
            i = self.read(3)
            if i == b"EOF":
                break

            # If the end has been reached, the patch is corrupt.
            if not i:
                return False

            self.seek(-3, os.SEEK_CUR)

            # Get the record details.
            offset = readInt(self.read(3))
            size = readInt(self.read(2))

            # If it's an RLE record, treat it as such.
            if size == 0:
                i = self.read(2)
                sizeRLE = readInt(i)
                diff = self.read(1) * sizeRLE

            # Otherwise, read it as a norml record.
            else:
                diff = self.read(size)

            self.records[offset] = diff

        return True

