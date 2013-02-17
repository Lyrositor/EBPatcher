# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING for more details.

"""
Functions for applying BPS patches.
"""
from zlib import crc32
from bps import operations as ops
from bps.validate import check_stream, CorruptFile
from bps.io import read_bps


def apply_to_bytearrays(iterable, source_buf, target_buf, snesHeader=0):
	"""
	Applies the BPS patch from iterable to source_buf, producing target_buf.

	iterable should be an iterable yielding BPS patch opcodes, after the
	header.

	source_buf should be a bytes object, or something impersonating one.

	target_buf should be a bytearray object, or something impersonating one.
	"""
	writeOffset = -snesHeader

	for item in iterable:

		if isinstance(item, ops.Header):
			# Just the header, nothing for us to do here.
			pass

		elif isinstance(item, ops.SourceRead):
			target_buf[writeOffset:writeOffset+item.bytespan] = \
					source_buf[writeOffset:writeOffset+item.bytespan]

		elif isinstance(item, ops.TargetRead):
			target_buf[writeOffset:writeOffset+item.bytespan] = item.payload

		elif isinstance(item, ops.SourceCopy):
			target_buf[writeOffset:writeOffset+item.bytespan] = \
					source_buf[item.offset:item.offset+item.bytespan]

		elif isinstance(item, ops.TargetCopy):
			# Because TargetCopy can be used to implement RLE-type compression,
			# we have to copy a byte at a time rather than just slicing
			# target_buf.
			for i in range(item.bytespan):
				target_buf[writeOffset+i] = target_buf[item.offset+i]

		elif isinstance(item, ops.SourceCRC32):
			pass

		elif isinstance(item, ops.TargetCRC32):
			pass

		writeOffset += item.bytespan


def apply_to_files(patch, source, target, snesHeader=0):
	"""
	Applies the BPS patch to the source file, writing to the target file.

	patch should be a file handle containing BPS patch data.

	source should be a readable, binary file handle containing the source data
	for the BPS patch.

	target should be a writable, binary file handle, which will contain the
	result of applying the given patch to the given source data.
	"""
	iterable = check_stream(read_bps(patch))
	sourceData = source.read()

	header = next(iterable)

	targetData = bytearray(header.targetSize)

	apply_to_bytearrays(iterable, sourceData, targetData, snesHeader)

	target.write(targetData)
