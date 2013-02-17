# ROM
# Handles read and write operations to EarthBound ROMs.

from io import BytesIO
from hashlib import md5
from zlib import crc32

D = [0x45, 0x41, 0x52, 0x54, 0x48, 0x20, 0x42, 0x4f, 0x55, 0x4E, 0x44]
EB_MD5 = "a864b2e5c141d2dec1c4cbed75a42a85"  # Unheadered - clean.

# There is a different version of the ROM used by some members of the community.
# Patch it to the clean version.
EB_WRONG_MD5 = "8c28ce81c7d359cf9ccaa00d41f8ad33"
EB_WRONG_DIFF = {0x281d: 0xd0, 0x281e: 0x1a, 0x839d: 0x31, 0x83a8: 0x32,
                 0xa128: 0x31, 0xa141: 0xf0, 0xffcc: 0x20, 0xffcd: 0x20,
                 0xffce: 0x20, 0xffd5: 0x31, 0x1ffe7: 0xef, 0x1ffe8: 0xef,
                 0x1ffe9: 0xff, 0x1ffea: 0xc1, 0x3fdd6: 0xef, 0x3fdd7: 0xf2,
                 0x3fdd8: 0xfd, 0x3fdd9: 0xc3, 0x3fdda: 0xf0}

# ExHiROM expanded ROMs have two bytes different from LoROM.
EXHIROM_DIFF = {0x0ffd5: 0x31, 0x0ffd7: 0x0c}


class ROM(BytesIO):
    """A container for manipulating EarthBound ROM data as a file."""

    def __init__(self, romPath=None, trim=True, source=None):
        """Loads the ROM's data in a buffer."""

        if not source:
            # Load the data and remove the header/expanded area, if present.
            # If the specified ROM is the hacked ROM used to create new patches,
            # don't remove the expanded area, if present.
            BytesIO.__init__(self, open(romPath, "rb").read())
            self.romPath = romPath
            self.clean = False
            self.valid = False
            if len(self.getvalue()) < 0x300000:
                return
            self.checkHeader()
            if trim:
                self.checkExpanded()

            # Get the CRC32 checksum (for BPS patches).
            self.crc = crc32(self.getvalue()) & 0xffffffff

            # Check the MD5 checksum.
            self.checkMD5()
            if not self.valid:
                b = self.getbuffer()
                if b[len(b) - 1] == 0xFF:
                    b[len(b) - 1] = 0
                del b
                self.checkMD5()

            # If the MD5 check failed, see if it's at least an EarthBound ROM.
            self.checkEarthBound()
        else:
            # Copy the data from the source ROM file.
            self.romPath = source.romPath
            self.clean = source.clean
            self.valid = source.valid
            self.crc = source.crc
            self.header = source.header
            self.md5 = source.md5
            self.write(source.getvalue())
            self.seek(0)

    def copy(self):
        """Returns a copy of the ROM."""

        return ROM(source=self)

    def checkHeader(self):
        """Check to see if the ROM is headered or not."""

        self.header = 0
        d = self.getvalue()
        try:
            # Check for a headered HiROM.
            if ~d[0x101dc] & 0xff == d[0x101de] and \
               ~d[0x101dd] & 0xff == d[0x101df] and \
               list(d[0x101c0:0x101c0 + len(D)]) == D:
                self.header = 0x200
        except IndexError:
            pass

        try:
            # Check for a headered LoROM.
            if ~d[0x81dc] & 0xff == d[0x81de] and \
               ~d[0x81dd] & 0xff == d[0x81df] and \
               list(d[0x101c0:0x101c0 + len(D)]) == D:
                self.header = 0x200
        except IndexError:
            pass

        # Remove the header from the data.
        newData = bytearray(d[self.header:])
        self.seek(-0x200, 2)
        self.truncate()
        self.seek(0)
        self.write(newData)

    def checkExpanded(self):
        """Check to see if the ROM is HiROM or ExHiROM."""

        newData = bytearray(self.getvalue())
        if len(newData) > 0x300000:
            if len(newData) > 0x400000:
                for offset, diff in EXHIROM_DIFF.items():
                    newData[offset] = diff
            self.truncate(0x300000)
            self.seek(0)
            self.write(newData[:0x300000])

    def checkMD5(self):
        """Check to see if the ROM matches a known MD5 checksum."""

        self.md5 = md5(self.getvalue()).hexdigest()
        # If this is the slightly different version, patch it
        if self.md5 == EB_WRONG_MD5:
            newData = bytearray(self.getvalue())
            for offset, diff in EB_WRONG_DIFF.items():
                newData[offset] = diff
            self.seek(0)
            self.write(newData)
            self.md5 = md5(self.getvalue()).hexdigest()
        if self.md5 == EB_MD5:
            self.clean = True
            self.valid = True

    def checkEarthBound(self):
        """As a last resort, check if the ROM is named "EARTH BOUND"."""

        d = self.getvalue()
        if d[0xffc0:0xffcb] == b"EARTH BOUND":
            self.valid = True

    def modifySize(self, size):
        """Expands or shrinks the size of the ROM."""

        self.truncate(size)
        b = bytearray(self.getvalue())
        if len(b) < size:
            while len(b) < size:
                b.append(0)
            self.seek(0)
            self.write(b)

    def writeToFile(self):
        """Write the data to the ROM file."""

        d = bytearray(self.getvalue())
        if len(d) > 0x300000 and d[len(d) - 1] == 0:
            d[len(d) - 1] = 0xFF  # Fix for Lunar IPS patching.
        f = open(self.romPath, "wb")
        f.write(d)
        f.close()

