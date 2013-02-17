# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING for more details.

"""
Tools for creating BPS patches.

For more information about the basic algorithm used here, see the article
"Intro to Delta Encoding":

	https://gitorious.org/python-blip/pages/IntroToDeltaEncoding

"""
from zlib import crc32
from bps import operations as ops
from bps.util import BlockMap

def iter_blocks(data, blocksize):
	offset = 0

	while offset < len(data):
		block = data[offset:offset+blocksize]

		yield (block, offset)
		offset += blocksize


def measure_op(blocksrc, sourceoffset, target, targetoffset):
	"""
	Measure the match between blocksrc and target at these offsets.
	"""
	# The various parameters line up something like this:
	#
	#      v-- sourceoffset
	# ...ABCDExGHI... <-- blocksrc
	#
	# ...xxxABCDEF... <-- target
	#         ^-- targetOffset
	#
	# result: backspan = 2, forespan = 3
	#

	# Measure how far back the source and target files match from these
	# offsets.
	backspan = 0

	# We need the +1 here because the test inside the loop is actually looking
	# at the byte *before* the one pointed to by (sourceoffset-backspan), so
	# we need our span to stretch that little bit further.
	maxspan = min(sourceoffset, targetoffset) + 1

	for backspan in range(maxspan):
		if blocksrc[sourceoffset-backspan-1] != target[targetoffset-backspan-1]:
			break

	# Measure how far forward the source and target files are aligned.
	forespan = 0

	sourcespan = len(blocksrc) - sourceoffset
	targetspan = len(target) - targetoffset
	maxspan = min(sourcespan, targetspan)

	for forespan in range(maxspan):
		if blocksrc[sourceoffset+forespan] != target[targetoffset+forespan]:
			break
	else:
		# We matched right up to the end of the file.
		forespan += 1

	return backspan, forespan


def diff_bytearrays(blocksize, source, target, metadata=""):
	"""
	Yield a sequence of patch operations that transform source to target.
	"""
	yield ops.Header(len(source), len(target), metadata)

	# We assume the entire source file will be available when applying this
	# patch, so load the entire thing into the block map.
	sourcemap = BlockMap()
	for block, offset in iter_blocks(source, blocksize):
		sourcemap.add_block(block, offset)

	# Points at the next byte of the target buffer that needs to be encoded.
	targetWriteOffset = 0

	# Points at the next byte of the target buffer we're searching for
	# encodings for. If we can't find an encoding for a particular byte, we'll
	# leave targetWriteOffset alone and increment this offset, on the off
	# chance that we find a new encoding that we can extend backwards to
	# targetWriteOffset.
	targetEncodingOffset = 0

	# Keep track of blocks seen in the part of the target buffer before
	# targetWriteOffset. Because targetWriteOffset does not always advance by
	# an even multiple of the blocksize, there can be some lag between when
	# targetWriteOffset moves past a particular byte, and when that byte's
	# block is added to targetmap.
	targetmap = BlockMap()
	targetblocks = iter_blocks(target, blocksize)

	# Points to the byte just beyond the most recent block added to targetmap;
	# the difference between this and targetWriteOffset measures the 'some lag'
	# described above.
	nextTargetMapBlockOffset = 0

	# A place to store operations before we spit them out. This gives us an
	# opportunity to replace operations if we later come across a better
	# alternative encoding.
	opbuf = ops.OpBuffer(target)

	while targetEncodingOffset < len(target):
		# Keeps track of the most efficient operation for encoding this
		# particular offset that we've found so far.
		bestOp = None
		bestOpEfficiency = 0
		bestOpBackSpan = 0
		bestOpForeSpan = 0

		blockend = targetEncodingOffset + blocksize
		block = target[targetEncodingOffset:blockend]

		for sourceOffset in sourcemap.get_block(block):
			backspan, forespan = measure_op(
					source, sourceOffset,
					target, targetEncodingOffset,
				)

			if forespan == 0:
				# This block actually doesn't occur at this sourceOffset after
				# all. Perhaps it's a hash collision?
				continue

			if sourceOffset == targetEncodingOffset:
				candidate = ops.SourceRead(backspan+forespan)
			else:
				candidate = ops.SourceCopy(
						backspan+forespan,
						sourceOffset-backspan,
					)

			lastSourceCopyOffset, lastTargetCopyOffset = (
					opbuf.copy_offsets(backspan)
				)

			efficiency = candidate.efficiency(
					lastSourceCopyOffset, lastTargetCopyOffset)

			if efficiency > bestOpEfficiency:
				bestOp = candidate
				bestOpEfficiency = efficiency
				bestOpBackSpan = backspan
				bestOpForeSpan = forespan

		for targetOffset in targetmap.get_block(block):
			backspan, forespan = measure_op(
					target, targetOffset,
					target, targetEncodingOffset,
				)

			if forespan == 0:
				# This block actually doesn't occur at this sourceOffset after
				# all. Perhaps it's a hash collision?
				continue

			candidate = ops.TargetCopy(
					backspan+forespan,
					targetOffset-backspan,
				)

			lastSourceCopyOffset, lastTargetCopyOffset = (
					opbuf.copy_offsets(backspan)
				)

			efficiency = candidate.efficiency(
					lastSourceCopyOffset, lastTargetCopyOffset)

			if efficiency > bestOpEfficiency:
				bestOp = candidate
				bestOpEfficiency = efficiency
				bestOpBackSpan = backspan
				bestOpForeSpan = forespan

		# If we can't find a copy instruction that encodes this block, or the
		# best one we've found is a net efficiency loss,  we'll have to issue
		# a TargetRead... later.
		if bestOp is None or bestOpEfficiency < 1.0:
			targetEncodingOffset += 1
			continue

		# We found an encoding for the target block, so issue a TargetRead for
		# all the bytes from the end of the last block up to now.
		if targetWriteOffset < targetEncodingOffset:
			tr = ops.TargetRead(target[targetWriteOffset:targetEncodingOffset])
			opbuf.append(tr)
			targetWriteOffset = targetEncodingOffset

		opbuf.append(bestOp, rollback=bestOpBackSpan)

		targetWriteOffset += bestOpForeSpan

		# The next block we want to encode starts after the bytes we've
		# just written.
		targetEncodingOffset = targetWriteOffset

		# If it's been more than BLOCKSIZE bytes since we added a block to
		# targetmap, process the backlog.
		while (targetWriteOffset - nextTargetMapBlockOffset) >= blocksize:
			newblock, offset = next(targetblocks)
			targetmap.add_block(newblock, offset)
			nextTargetMapBlockOffset = offset + len(newblock)

	for op in opbuf:
		yield op

	if targetWriteOffset < len(target):
		# It's TargetRead all the way up to the end of the file.
		yield ops.TargetRead(target[targetWriteOffset:])

	yield ops.SourceCRC32(crc32(source))
	yield ops.TargetCRC32(crc32(target))
