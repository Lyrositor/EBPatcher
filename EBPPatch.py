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

# EBPPatch
# Handles the import of EBP (EarthBound Patch) patches.

import json

from IPSPatch import *


class EBPPatch(IPSPatch):
    """The new EarthBound patcher format for patching, based on IPS."""

    def __init__(self, patchPath, new=False):
        """Creates a new patch or loads an existing one."""

        super().__init__(patchPath, new)
        if not new:
            self.info = self.loadMetadata()
        else:
            self.patchPath = patchPath

    def loadMetadata(self):
        """Loads the metadata from the patch."""

        # Check to see if it contains metadata.
        try:
            info = json.loads(self.read().decode("utf-8"))
            assert info["patcher"] == "EBPatcher"
            print("EBPPatch.loadMetadata(): Metadata loaded.\n"
                  "\tTitle: {}\n\tAuthor: {}\n\tDescription: {}".format(
                  info["title"], info["author"], info["description"]))
        except:
            info = None
            print("EBPPatch.loadMetadata(): Failed to load metadata.")

        return info

    def createFromSource(self, sourceROM, targetROM, metadata):
        """Creates an EBP patch from the source and target ROMs."""

        # Create the records.
        i = None
        records = {}
        sourceROM.seek(0)
        targetROM.seek(0)
        s = sourceROM.read(1)
        t = targetROM.read(1)
        while t:
            if t == s and i is not None:
                i = None
            elif t != s:
                if i is not None:
                    # Check that the record's size can fit in 2 bytes.
                    if targetROM.tell() - 1 - i == 0xFFFF:
                        i = None
                        continue
                    records[i] += t
                else:
                    i = targetROM.tell() - 1
                    # Check that the offset isn't EOF. If it is, go back one
                    # byte to work around this IPS limitation.
                    if i.to_bytes(3, "big") != b"EOF":
                        records[i] = t
                    else:
                        i -= 1
                        records[i] = targetROM.getvalue()[i]
            s = sourceROM.read(1)
            t = targetROM.read(1)

        # Write the patch.
        self.seek(0)
        self.write(b"PATCH")
        for r in sorted(records):
            self.write(r.to_bytes(3, "big"))
            self.write(len(records[r]).to_bytes(2, "big"))
            self.write(records[r])
        self.write(b"EOF")
        self.write(bytes(metadata, "utf-8"))

        # Write the patch to a file.
        f = open(self.patchPath, "wb")
        f.write(self.getvalue())
        f.close()
