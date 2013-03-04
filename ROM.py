# ROM
# Handles read and write operations to EarthBound ROMs.

from io import BytesIO
from hashlib import md5
from zlib import crc32

from BPS import *

# Unheadered, clean ROM.
EB_MD5 = "a864b2e5c141d2dec1c4cbed75a42a85"

# The "wrong" MD5 hashes, and the bytes that need to be correct to obtain the
# correct version of the ROM.
EB_WRONG_MD5 = {"8c28ce81c7d359cf9ccaa00d41f8ad33": "patches/wrong1.bps",
                "b2dcafd3252cc4697bf4b89ea3358cd5": "patches/wrong2.bps",
                "0b8c04fc0182e380ff0e3fe8fdd3b183": "patches/wrong3.bps",
                "2225f8a979296b7dcccdda17b6a4f575": "patches/wrong4.bps",
                "eb83b9b6ea5692cefe06e54ea3ec9394": "patches/wrong5.bps",
                "cc9fa297e7bf9af21f7f179e657f1aa1": "patches/wrong6.bps"}

# ExHiROM expanded ROMs have two bytes different from LoROM.
EXHIROM_DIFF = {0xffd5: 0x31, 0xffd7: 0x0c}

# The identification string for EarthBound ROMs.
ID = b"EARTH BOUND"


class ROM(BytesIO):
    """A container for manipulating EarthBound ROM data as a file."""

    def __init__(self, source, new=False):
        """Loads the ROM's data in a buffer or copies an existing ROM."""

        if not new:
            # Initialize the ROM's data.
            BytesIO.__init__(self, open(source, "rb").read())
            self.romPath = source
            self.clean = False
            self.valid = False
            self.crc = None

            # Check if there is a header; if there is one, remove it.
            self.header = self.checkHeader()
            if self.header:
                self.removeHeader()

            # Check if the ROM is big enough and if it's expanded; if it is, remove
            # the unused expanded space.
            if len(self.getvalue()) < 0x300000:
                return
            if len(self.getvalue()) > 0x300000 and self.checkExpanded():
                self.removeExpanded()

            # Check the MD5 checksum, and try to fix the ROM if it's incorrect.
            if not self.checkMD5():
                self.repairROM()

            # If we couldn't fix the ROM, try to remove a 0xff byte at the end.
            if not self.checkMD5():
                b = bytearray(self.getvalue())
                if b[len(b) - 1] == 0xFF:
                    b[len(b) - 1] = 0
                if self.checkMD5(b):
                    b = self.getbuffer()
                    b[len(b) - 1] = 0
                    del b

            # Perform a final MD5 check for its validity. If it fails, check if
            # it's at least an EarthBound ROM.
            if self.checkMD5():
                self.clean = True
                self.valid = True
                print("ROM.__init__(): Clean EarthBound ROM.")
            elif self.checkEarthBound():
                self.valid = True
                print("ROM.__init__(): Unclean EarthBound ROM.")
            else:
                print("ROM.__init__(): Invalid EarthBound ROM.")

            # Get the CRC32 checksum (for BPS patches).
            self.crc = crc32(self.getvalue()) & 0xffffffff

        else:
            # Copy the source ROM's information.
            BytesIO.__init__(self, source.getvalue())
            self.romPath = source.romPath
            self.clean = source.clean
            self.valid = source.valid
            self.crc = source.crc
            self.header = source.header

    def copy(self):
        """Returns a copy of the ROM."""

        return ROM(self, True)

    def checkHeader(self):
        """Check to see if the ROM is headered or not."""

        header = 0
        d = self.getvalue()
        try:
            # Check for a headered HiROM.
            if ~d[0x101dc] & 0xff == d[0x101de] and \
               ~d[0x101dd] & 0xff == d[0x101df] and \
               d[0x101c0:0x101c0 + len(ID)] == ID:
                header = 0x200
        except IndexError:
            pass

        try:
            # Check for a headered LoROM.
            if ~d[0x81dc] & 0xff == d[0x81de] and \
               ~d[0x81dd] & 0xff == d[0x81df] and \
               d[0x101c0:0x101c0 + len(ID)] == ID:
                header = 0x200
        except IndexError:
            pass

        if header:
            print("ROM.checkHeader(): ROM is headered.")
        else:
            print("ROM.checkHeader(): ROM is unheadered.")

        return header

    def removeHeader(self):
        """Removes the header from the data."""

        newData = bytearray(self.getvalue()[self.header:])
        self.seek(-0x200, 2)
        self.truncate()
        self.seek(0)
        self.write(newData)

    def checkExpanded(self):
        """Check to see if the ROM is HiROM or ExHiROM."""

        # Get only the first three 0x300000 bytes.
        d = bytearray(self.getvalue())[:0x300000]
        for offset, diff in EXHIROM_DIFF.items():
            d[offset] = diff

        # If the normal area is unmodified, then the expanded area is unused and
        # can be deleted.
        if self.checkMD5(d):
            print("ROM.checkExpanded(): ROM has unused expanded space.")
            return True
        # Otherwise, the expanded area should not be deleted.
        else:
            print("ROM.checkExpanded(): ROM has used expanded space.")
            return False

    def removeExpanded(self):
        """Removes the expanded space."""

        newData = bytearray(self.getvalue())
        if len(newData) > 0x400000:
            for offset, diff in EXHIROM_DIFF.items():
                newData[offset] = diff
        self.truncate(0x300000)
        self.seek(0)
        self.write(newData[:0x300000])

    def checkMD5(self, data=None):
        """Check to see if the data matches a known MD5 checksum."""

        if not data:
            data = self.getvalue()
        md5Hex = md5(data).hexdigest()
        print("ROM.checkMD5(): {}".format(md5Hex))
        if md5Hex == EB_MD5:
            return True
        else:
            return False

    def repairROM(self):
        """Attempts to repair the ROM to a known version of EarthBound."""

        md5Hex = md5(self.getvalue()).hexdigest()
        if md5Hex in EB_WRONG_MD5:
            print("ROM.repairROM(): ROM is a known wrong EarthBound ROM.")
            try:
                patch = BPSPatch(EB_WRONG_MD5[md5Hex])
            except IOError:
                print("ROM.repairROM(): Could not find repair patch file.")
                return
            copyROM = self.copy()
            try:
                patch.applyToTarget(copyROM)
            except:
                print("ROM.repairROM(): Failed to apply repair patch.")
                return
            self.seek(0)
            self.write(copyROM.getvalue())
        else:
            print("ROM.repairROM(): ROM is unknown.")

    def checkEarthBound(self):
        """As a last resort, check if the ROM is named "EARTH BOUND"."""

        d = self.getvalue()
        if d[0xffc0:0xffcb] == ID:
            print("ROM.checkEarthBound(): ROM is an EarthBound ROM.")
            return True
        else:
            print("ROM.checkEarthBound(): ROM is an unknown ROM.")
            return False

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

