# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING for more details.

"""
Tools for validating BPS patches.
"""
from bps import operations as ops


class CorruptFile(ValueError):
	"""
	Raised to indicate that a BPS patch is not valid.
	"""
	pass


def _check_next(iterable):
	"""
	Internal function.

	Check the iterable does have a next value, and return it.
	"""
	try:
		return next(iterable)
	except StopIteration:
		raise CorruptFile("truncated patch: expected more opcodes after this.")


def check_stream(iterable):
	"""
	Yields items from iterable if they represent a valid BPS patch.

	Raises CorruptFile if any problems are detected.
	"""
	# Make sure we have an iterable.
	iterable = iter(iterable)

	header = _check_next(iterable)

	if not isinstance(header, ops.Header):
		raise CorruptFile("bad hunk: expected header, not "
				"{header!r}".format(header=header))

	yield header

	sourceSize           = header.sourceSize
	targetSize           = header.targetSize
	targetWriteOffset    = 0

	while targetWriteOffset < targetSize:
		item = _check_next(iterable)

		if isinstance(item, ops.SourceRead):
			# This opcode reads from the source file, from targetWriteOffset to
			# targetWriteOffset+length, so we need to be sure that byte-range
			# exists in the source file as well as the target.
			if targetWriteOffset + item.bytespan > sourceSize:
				raise CorruptFile("bad hunk: reads past the end of the "
						"source file: {item!r}".format(item=item))

		elif isinstance(item, ops.TargetRead):
			# Nothing special we need to check for this operation.
			pass

		elif isinstance(item, ops.SourceCopy):
			# Not allowed to SourceCopy past the end of the source file.
			if item.offset + item.bytespan > sourceSize:
				raise CorruptFile("bad hunk: reads past the end "
						"of the source file: {item!r}".format(item=item))

		elif isinstance(item, ops.TargetCopy):
			# Not allowed to TargetCopy an offset that points past the part
			# we've written.
			if item.offset >= targetWriteOffset:
				raise CorruptFile("bad hunk: reads past the end of the "
						"written part of the target file at "
						"{targetWriteOffset}: {item!r}".format(item=item,
							targetWriteOffset=targetWriteOffset))

		else:
			raise CorruptFile("bad hunk: unknown opcode {item!r}".format(
				item=item))

		targetWriteOffset += item.bytespan

		if targetWriteOffset > targetSize:
			raise CorruptFile("bad hunk: writes past the end of the target: "
					"{item!r}".format(item=item))

		yield item

	item = _check_next(iterable)
	if not isinstance(item, ops.SourceCRC32):
		raise CorruptFile("bad hunk: expected SourceCRC32, not "
				"{item!r}".format(item=item))
	yield item

	item = _check_next(iterable)
	if not isinstance(item, ops.TargetCRC32):
		raise CorruptFile("bad hunk: expected TargetCRC32, not "
				"{item!r}".format(item=item))
	yield item

	# Check that the iterable is now empty.
	try:
		garbage = next(iterable)
		raise CorruptFile("trailing garbage in stream: {garbage!r}".format(
				garbage=garbage))
	except StopIteration:
		pass


