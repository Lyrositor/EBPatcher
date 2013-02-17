# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING for more details.

"""
Tools for creating human-readable versions of BPS patch files.
"""
import bps.io as bio

def disassemble(in_buf, out_buf):
	"""
	Disassembles the BPS patch in in_buf, writing the result to out_buf.

	in_buf should implement io.IOBase, opened in 'rb' mode.

	out_buf should implement io.IOBase, opened in 'wt' mode.
	"""
	bio.write_bps_asm(bio.read_bps(in_buf), out_buf)


def assemble(in_buf, out_buf):
	"""
	Assembles the description in in_buf to a BPS patch in out_buf.

	in_buf should implement io.IOBase, opened in 'rt' mode.

	out_buf should implement io.IOBase, opened in 'wb' mode.
	"""
	bio.write_bps(bio.read_bps_asm(in_buf), out_buf)
