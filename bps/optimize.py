# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING for more details.

"""
Tools for optimizing BPS patches.
"""
from io import BytesIO
from bps import operations as ops
from bps.validate import check_stream

def optimize(iterable):
	"""
	Yields a simplified sequence of patch operations from iterable.
	"""
	iterable = check_stream(iterable)

	header = next(iterable)
	yield header

	lastItem = next(iterable)

	if isinstance(lastItem, ops.SourceCopy) and lastItem.offset == 0:
		# SourceCopy is copying from the start of the file, so it might as well
		# be a SourceRead.
		lastItem = ops.SourceRead(lastItem.bytespan)

	targetWriteOffset = 0
	for item in iterable:

		if (
				isinstance(lastItem, ops.SourceRead) and
				isinstance(item, ops.SourceRead)
			):
			# We can merge consecutive SourceRead operations.
			lastItem.extend(item)
			continue

		elif (
				isinstance(lastItem, ops.TargetRead) and
				isinstance(item, ops.TargetRead)
			):
			# We can merge consecutive TargetRead operations.
			lastItem.extend(item)
			continue

		elif (
				isinstance(lastItem, ops.SourceCopy) and
				isinstance(item, ops.SourceCopy) and
				lastItem.offset + lastItem.bytespan == item.offset
			):
			# We can merge consecutive SourceCopy operations, as long as the
			# following ones have a relative offset of 0 from the end of the
			# previous one.
			lastItem.extend(item)
			continue

		elif (
				isinstance(lastItem, ops.TargetCopy) and
				isinstance(item, ops.TargetCopy) and
				lastItem.offset + lastItem.bytespan == item.offset
			):
			# We can merge consecutive TargetCopy operations, as long as the
			# following ones have a relative offset of 0 from the end of the
			# previous one.
			lastItem.extend(item)
			continue

		if (
				isinstance(lastItem, ops.SourceCopy) and
				lastItem.offset == targetWriteOffset
			):
			# A SourceRead is just a SourceCopy that implicitly has its read
			# off set set to targetWriteOffset.
			lastItem = ops.SourceRead(lastItem.bytespan)

		yield lastItem

		targetWriteOffset += lastItem.bytespan

		lastItem = item

	yield lastItem
