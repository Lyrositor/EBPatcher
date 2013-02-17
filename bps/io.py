# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING for more details.

"""
Tools for reading and writing BPS patches.
"""
from struct import pack, unpack
import re
from binascii import b2a_hex, a2b_hex
from bps import util
from bps import operations as ops
from bps import constants as C
from bps.validate import CorruptFile, check_stream


NON_HEX_DIGIT_RE = re.compile("[^0-9A-Fa-f]")


def _expect_label(expected, actual):
	if actual != expected:
		raise CorruptFile("Expected {expected:r} field, "
				"not {actual:r}".format(expected=expected, actual=actual))


def _read_multiline_text(in_buf):
	lines = []
	while True:
		line = in_buf.readline()
		if line == ".\n":
			break
		if line.startswith("."): line = line[1:]
		lines.append(line)
	return "".join(lines)


def read_bps(in_buf):
	"""
	Yields BPS patch instructions from the BPS patch in in_buf.

	in_buf should implement io.IOBase, opened in 'rb' mode.
	"""
	# Keep track of the input file's CRC32, so we can check it at the end.
	in_buf = util.CRCIOWrapper(in_buf)

	# header
	magic = in_buf.read(4)

	if magic != C.BPS_MAGIC:
		raise CorruptFile("File magic should be {expected!r}, got "
				"{actual!r}".format(expected=C.BPS_MAGIC, actual=magic))

	sourcesize = util.read_var_int(in_buf)
	targetsize = util.read_var_int(in_buf)
	metadatasize = util.read_var_int(in_buf)
	metadata = in_buf.read(metadatasize).decode('utf-8')

	yield ops.Header(sourcesize, targetsize, metadata)

	targetWriteOffset = 0
	sourceRelativeOffset = 0
	targetRelativeOffset = 0
	while targetWriteOffset < targetsize:
		value = util.read_var_int(in_buf)
		opcode = value & C.OPCODEMASK
		length = (value >> C.OPCODESHIFT) + 1

		if opcode == C.OP_SOURCEREAD:
			yield ops.SourceRead(length)

		elif opcode == C.OP_TARGETREAD:
			yield ops.TargetRead(in_buf.read(length))

		elif opcode == C.OP_SOURCECOPY:
			raw_offset = util.read_var_int(in_buf)
			offset = raw_offset >> 1
			if raw_offset & 1:
				offset = -offset
			sourceRelativeOffset += offset
			yield ops.SourceCopy(length, sourceRelativeOffset)
			sourceRelativeOffset += length

		elif opcode == C.OP_TARGETCOPY:
			raw_offset = util.read_var_int(in_buf)
			offset = raw_offset >> 1
			if raw_offset & 1:
				offset = -offset
			targetRelativeOffset += offset
			yield ops.TargetCopy(length, targetRelativeOffset)
			targetRelativeOffset += length

		else:
			raise CorruptFile("Unknown opcode: {opcode:02b}".format(
				opcode=opcode))

		targetWriteOffset += length

	# footer
	yield ops.SourceCRC32(unpack("<I", in_buf.read(4))[0])
	yield ops.TargetCRC32(unpack("<I", in_buf.read(4))[0])

	# Check the patch's CRC32.
	actual = in_buf.crc32
	expected = unpack("<I", in_buf.read(4))[0]

	if expected != actual:
		raise CorruptFile("Patch claims its CRC32 is {expected:08X}, but "
				"it's really {actual:08X}".format(
					expected=expected, actual=actual)
			)


def write_bps(iterable, out_buf):
	"""
	Encodes BPS patch instructions from the iterable into a patch in out_buf.

	iterable should yield a sequence of BPS patch instructions.

	out_buf should implement io.IOBase, opened in 'wb' mode.
	"""
	# Make sure we have a sensible stream to write.
	iterable = check_stream(iterable)

	# Keep track of the patch data's CRC32, so we can write it out at the end.
	out_buf = util.CRCIOWrapper(out_buf)

	sourceRelativeOffset = 0
	targetRelativeOffset = 0

	for item in iterable:
		out_buf.write(item.encode(sourceRelativeOffset, targetRelativeOffset))

		if isinstance(item, ops.SourceCopy):
			sourceRelativeOffset = item.offset + item.bytespan
		elif isinstance(item, ops.TargetCopy):
			targetRelativeOffset = item.offset + item.bytespan

	# Lastly, write out the patch CRC32.
	out_buf.write(pack("<I", out_buf.crc32))


def read_bps_asm(in_buf):
	"""
	Yields BPS patch instructions from the BPS patch in in_buf.

	in_buf should implement io.IOBase, opened in 'rt' mode.
	"""
	# header
	magic = in_buf.readline()

	if magic != C.BPSASM_MAGIC:
		raise CorruptFile("BPS asm should have magic set to {expected!r}, "
				"not {actual!r}".format(expected=C.BPSASM_MAGIC, actual=magic)
			)

	label, sourcesize = in_buf.readline().split(":")
	_expect_label(C.SOURCESIZE, label)
	sourcesize = int(sourcesize)

	label, targetsize = in_buf.readline().split(":")
	_expect_label(C.TARGETSIZE, label)
	targetsize = int(targetsize)

	label, _ = in_buf.readline().split(":")
	_expect_label(C.METADATA, label)
	metadata = _read_multiline_text(in_buf)

	yield ops.Header(sourcesize, targetsize, metadata)

	targetWriteOffset = 0
	while targetWriteOffset < targetsize:
		label, value = in_buf.readline().split(":")
		item = None

		if label == C.SOURCEREAD:
			length = int(value)
			item = ops.SourceRead(length)

		elif label == C.TARGETREAD:
			data = _read_multiline_text(in_buf)
			data = NON_HEX_DIGIT_RE.sub("", data)
			data = data.encode('ascii')
			data = a2b_hex(data)
			item = ops.TargetRead(data)

		elif label == C.SOURCECOPY:
			length, offset = [int(x) for x in value.split()]
			item = ops.SourceCopy(length, offset)

		elif label == C.TARGETCOPY:
			length, offset = [int(x) for x in value.split()]
			item = ops.TargetCopy(length, offset)

		else:
			raise CorruptFile("Unknown label: {label!r}".format(label=label))

		yield item

		targetWriteOffset += item.bytespan

	label, sourcecrc32 = in_buf.readline().split(":")
	_expect_label(C.SOURCECRC32, label)
	yield ops.SourceCRC32(int(sourcecrc32, 16))

	label, targetcrc32 = in_buf.readline().split(":")
	_expect_label(C.TARGETCRC32, label)
	yield ops.TargetCRC32(int(targetcrc32, 16))


def write_bps_asm(iterable, out_buf):
	"""
	Encodes BPS patch instructions into BPS assembler in out_buf.

	iterable should yield a sequence of BPS patch instructions.

	out_buf should implement io.IOBase, opened in 'wt' mode.
	"""
	# Make sure we have a sensible stream to write.
	iterable = check_stream(iterable)

	# header
	header = next(iterable)

	out_buf.write(C.BPSASM_MAGIC)
	out_buf.write("{0}: {1:d}\n".format(C.SOURCESIZE, header.sourceSize))
	out_buf.write("{0}: {1:d}\n".format(C.TARGETSIZE, header.targetSize))

	# metadata
	out_buf.write("metadata:\n")
	lines = header.metadata.split("\n")
	if lines[-1] == "":
		lines.pop(-1)
	for line in lines:
		# Because we use a line containing only "." as the delimiter, we
		# need to escape all the lines beginning with dots.
		if line.startswith("."):
			out_buf.write(".")
		out_buf.write(line)
		out_buf.write("\n")

	out_buf.write(".\n")

	for item in iterable:
		if isinstance(item, ops.SourceRead):
			out_buf.write("sourceread: {0.bytespan}\n".format(item))

		elif isinstance(item, ops.TargetRead):
			out_buf.write("targetread:\n")
			data = item.payload
			while len(data) > 40:
				head, data = data[:40], data[40:]
				out_buf.write(b2a_hex(head).decode('ascii'))
				out_buf.write("\n")
			out_buf.write(b2a_hex(data).decode('ascii'))
			out_buf.write("\n.\n")

		elif isinstance(item, ops.SourceCopy):
			out_buf.write("sourcecopy: {0.bytespan} {0.offset}\n".format(item))

		elif isinstance(item, ops.TargetCopy):
			out_buf.write("targetcopy: {0.bytespan} {0.offset}\n".format(item))

		elif isinstance(item, ops.SourceCRC32):
			out_buf.write("sourcecrc32: {0.value:08X}\n".format(item))

		elif isinstance(item, ops.TargetCRC32):
			out_buf.write("targetcrc32: {0.value:08X}\n".format(item))
