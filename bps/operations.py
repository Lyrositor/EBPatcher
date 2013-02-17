# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING for more details.

"""
Classes representing patch operations.
"""
import copy
from struct import pack
from bps import util
from bps import constants as C


def _classname(obj):
	return "{0.__module__}.{0.__name__}".format(type(obj))


class BaseOperation:

	# Unless otherwise configured, an operation affects no bytes.
	bytespan = 0

	# An abbreviation for this operation. Helpful for debugging tools that
	# display a lot of operations on-screen at a time.
	marker = None

	def encode(self, sourceRelativeOffset, targetRelativeOffset):
		"""
		Returns a bytestring representing this operation.

		sourceRelativeOffset is used when encoding SourceCopy operations,
		targetRelativeOffset is used when encoding TargetCopy operations.
		"""
		raise NotImplementedError()

	def encoded_size(self, sourceRelativeOffset, targetRelativeOffset):
		"""
		Estimate the size of the bytestring returned by .encode()
		"""
		raise NotImplementedError()

	def efficiency(self, sourceRelativeOffset, targetRelativeOffset):
		"""
		Returns a float representing the efficiency of this op at this offset.
		"""
		return self.bytespan / self.encoded_size(
				sourceRelativeOffset, targetRelativeOffset
			)

	def extend(self, other):
		"""
		Concatenate the other operation with this one, if possible.

		Raises TypeError if the other operation is of an incompatible type, or
		ValueError if the other operation isn't contiguous with this one.
		"""

	def shrink(self, length):
		"""
		Reduce the bytespan of this operation by the given amount.

		If length is positive, shrinkage will occur from the front. If length
		is negative, shrinkage will occur from the end (much like Python's
		slicing operators). Length should never be 0, and abs(length) should
		never be greater than or equal to the bytespan property.
		"""


class Header(BaseOperation):

	__slots__ = [
			'sourceSize',
			'targetSize',
			'metadata',
		]

	def __init__(self, sourceSize, targetSize, metadata=""):
		assert isinstance(sourceSize, int)
		assert isinstance(targetSize, int)
		assert sourceSize >= 0
		assert targetSize >= 0
		assert isinstance(metadata, str)

		self.sourceSize = sourceSize
		self.targetSize = targetSize
		self.metadata = metadata

	def __repr__(self):
		return (
				"<{0} "
				"sourceSize={1.sourceSize} "
				"targetSize={1.targetSize}>".format(_classname(self), self)
			)

	def __eq__(self, other):
		if not isinstance(other, type(self)): return False

		if self.sourceSize != other.sourceSize: return False
		if self.targetSize != other.targetSize: return False
		if self.metadata   != other.metadata:   return False

		return True

	def extend(self, other):
		raise TypeError(
				"Cannot extend a header operation with {0!r}".format(other)
			)

	def encode(self, ignored, ignored2):
		res = [C.BPS_MAGIC]
		res.append(util.encode_var_int(self.sourceSize))
		res.append(util.encode_var_int(self.targetSize))

		metadata = self.metadata.encode('utf-8')
		res.append(util.encode_var_int(len(metadata)))
		res.append(metadata)

		return b''.join(res)

	def shrink(self, length):
		raise TypeError(
				"Cannot shrink a header, let alone by {0!r}".format(length)
			)

	def encoded_size(self, ignored, ignored2):
		encoded_metadata = self.metadata.encode('utf-8')
		return (
				len(C.BPS_MAGIC)
				+ util.measure_var_int(self.sourceSize)
				+ util.measure_var_int(self.targetSize)
				+ util.measure_var_int(len(encoded_metadata))
				+ len(encoded_metadata)
			)


class SourceRead(BaseOperation):

	__slots__ = ['bytespan']

	marker = 'sr'

	def __init__(self, bytespan):
		assert isinstance(bytespan, int)
		assert bytespan > 0

		self.bytespan = bytespan

	def __repr__(self):
		return "<{0} bytespan={1.bytespan}>".format(
				_classname(self), self)

	def __eq__(self, other):
		if not isinstance(other, type(self)): return False

		if self.bytespan != other.bytespan: return False

		return True

	def extend(self, other):
		if not isinstance(other, type(self)):
			raise TypeError(
					"Cannot extend a SourceRead with {0!r}".format(other)
				)
		self.bytespan += other.bytespan

	def encode(self, ignored, ignored2):
		return util.encode_var_int(
				(self.bytespan - 1) << C.OPCODESHIFT | C.OP_SOURCEREAD
			)

	def shrink(self, length):
		if length == 0:
			raise ValueError(
					"Cannot shrink: {0!r} is too small".format(length))

		if abs(length) >= self.bytespan:
			raise ValueError(
					"Cannot shrink: {0!r} is too large".format(length))

		self.bytespan -= abs(length)

	def encoded_size(self, ignored, ignored2):
		return util.measure_var_int (
				(self.bytespan - 1) << C.OPCODESHIFT | C.OP_SOURCEREAD
			)


class TargetRead(BaseOperation):

	__slots__ = ['_payload']

	marker = 'tR'

	def __init__(self, payload):
		assert isinstance(payload, bytes)
		assert len(payload) > 0

		self._payload = [payload]

	def __repr__(self):
		return "<{0} bytespan={1.bytespan}>".format(
				_classname(self), self
			)

	def __eq__(self, other):
		if not isinstance(other, type(self)): return False

		if self.payload != other.payload: return False

		return True

	@property
	def payload(self):
		# If we have multiple byte-chunks in the payload, join them together
		# then store the result so we don't have to do that (potentially
		# expensive) operation again.
		if len(self._payload) > 1:
			self._payload = [b''.join(self._payload)]
		return self._payload[0]

	@property
	def bytespan(self):
		return len(self.payload)

	def extend(self, other):
		if not isinstance(other, type(self)):
			raise TypeError(
					"Cannot extend a TargetRead with {0!r}".format(other)
				)
		self._payload.append(other.payload)

	def encode(self, ignored, ignored2):
		payload = self.payload
		return b''.join([
				util.encode_var_int(
					(len(payload) - 1) << C.OPCODESHIFT | C.OP_TARGETREAD
				),
				payload,
			])

	def shrink(self, length):
		if length == 0:
			raise ValueError(
					"Cannot shrink: {0!r} is too small".format(length))

		if abs(length) >= self.bytespan:
			raise ValueError(
					"Cannot shrink: {0!r} is too large".format(length))

		if length > 0:
			self._payload = [self.payload[length:]]
		else:
			self._payload = [self.payload[:length]]

	def encoded_size(self, ignored, ignored2):
		bytespan = self.bytespan
		return util.measure_var_int(
				(bytespan - 1) << C.OPCODESHIFT | C.OP_TARGETREAD
			) + bytespan


class _BaseCopy(BaseOperation):

	__slots__ = [
			'bytespan',
			'offset',
		]

	def __init__(self, bytespan, offset):
		assert isinstance(bytespan, int)
		assert bytespan > 0, "Bytespan must be > 0, not {0}".format(bytespan)
		assert isinstance(offset, int)
		assert offset >= 0, "Offset must be >= 0, not {0}".format(offset)

		self.bytespan = bytespan
		self.offset = offset

	def __repr__(self):
		return "<{0} bytespan={1.bytespan} offset={1.offset}>".format(
				_classname(self), self
			)

	def __eq__(self, other):
		if not isinstance(other, type(self)): return False

		if self.bytespan != other.bytespan: return False
		if self.offset   != other.offset:   return False

		return True

	def extend(self, other):
		if not isinstance(other, type(self)):
			raise TypeError(
					"Cannot extend a {0} with {1!r}".format(
						type(self).__name__, other,
					)
				)
		if other.offset != self.offset + self.bytespan:
			raise ValueError(
					"Cannot extend {0!r} with non-contiguous op {1!r}".format(
						self, other,
					)
				)

		self.bytespan += other.bytespan

	def shrink(self, length):
		if length == 0:
			raise ValueError(
					"Cannot shrink: {0!r} is too small".format(length))

		if abs(length) >= self.bytespan:
			raise ValueError(
					"Cannot shrink: {0!r} is too large".format(length))

		if length > 0:
			self.bytespan -= length
			self.offset += length
		else:
			self.bytespan += length


class SourceCopy(_BaseCopy):

	marker = 'Sc'

	def encode(self, sourceRelativeOffset, ignored):
		relOffset = self.offset - sourceRelativeOffset

		return b''.join([
				util.encode_var_int(
					(self.bytespan - 1) << C.OPCODESHIFT | C.OP_SOURCECOPY
				),
				util.encode_var_int(
					(abs(relOffset) << 1) | (relOffset < 0)
				),
			])

	def encoded_size(self, lastSourceCopyOffset, ignored):
		relOffset = self.offset - lastSourceCopyOffset

		return util.measure_var_int(
				(self.bytespan - 1) << C.OPCODESHIFT | C.OP_SOURCECOPY
			) + util.measure_var_int(
				(abs(relOffset) << 1) | (relOffset < 0)
			)


class TargetCopy(_BaseCopy):

	marker = 'TC'

	def encode(self, ignored, targetRelativeOffset):
		relOffset = self.offset - targetRelativeOffset

		return b''.join([
				util.encode_var_int(
					(self.bytespan - 1) << C.OPCODESHIFT | C.OP_TARGETCOPY
				),
				util.encode_var_int(
					(abs(relOffset) << 1) | (relOffset < 0)
				),
			])

	def encoded_size(self, ignored, lastTargetCopyOffset):
		relOffset = self.offset - lastTargetCopyOffset

		return util.measure_var_int(
				(self.bytespan - 1) << C.OPCODESHIFT | C.OP_TARGETCOPY
			) + util.measure_var_int(
				(abs(relOffset) << 1) | (relOffset < 0)
			)


class _BaseCRC32(BaseOperation):

	__slots__ = [
			'value',
		]

	def __init__(self, value):
		assert isinstance(value, int)
		assert value >= 0
		assert value < 2**32

		self.value = value

	def __repr__(self):
		return "<{0} value=0x{1.value:08X}>".format(
				_classname(self), self
			)

	def __eq__(self, other):
		if not isinstance(other, type(self)): return False

		if self.value != other.value: return False

		return True

	def extend(self, other):
		raise TypeError(
				"Cannot extend {0!r} with {1!r}".format(self, other)
			)

	def encode(self, ignored, ignored2):
		return pack("<I", self.value)

	def shrink(self, length):
		raise TypeError(
				"Cannot shrink {0!r}, let alone by {1!r}".format(self, length)
			)

	def encoded_size(self, ignored, ignored2):
		return 4


class SourceCRC32(_BaseCRC32):
	pass


class TargetCRC32(_BaseCRC32):
	pass


def op_sequence_efficiency(oplist, lastSourceCopyOffset, lastTargetCopyOffset):

	total_encoded_size = 0
	total_bytespan = 0

	for op in oplist:
		total_bytespan += op.bytespan

		total_encoded_size += op.encoded_size(
				lastSourceCopyOffset, lastTargetCopyOffset)

		if isinstance(op, SourceCopy):
			lastSourceCopyOffset = op.offset + op.bytespan
		elif isinstance(op, TargetCopy):
			lastTargetCopyOffset = op.offset + op.bytespan

	if total_encoded_size:
		return total_bytespan / total_encoded_size

	return None


class OpBuffer:
	"""
	Represents a mutable sequence of patch operations.
	"""

	def __init__(self, target):
		self.target = target
		self._buf = []

	def __iter__(self):
		for row in self._buf:
			yield row[0]

	def __repr__(self):
		return "<OpBuffer with {0} items>".format(len(self._buf))

	def _append(self, operation):
		"""
		Internal method.

		Append the given operation to the list, maintaining internal caches.
		"""
		if self._buf:
			_, writeOffset, lastSourceCopyOffset, lastTargetCopyOffset = \
					self._buf[-1]
		else:
			writeOffset = lastSourceCopyOffset = lastTargetCopyOffset = 0

		writeOffset += operation.bytespan

		if isinstance(operation, SourceCopy):
			lastSourceCopyOffset = operation.offset + operation.bytespan
		elif isinstance(operation, TargetCopy):
			lastTargetCopyOffset = operation.offset + operation.bytespan

		self._buf.append( (operation, writeOffset, lastSourceCopyOffset,
				lastTargetCopyOffset) )

	def append(self, operation, rollback=0):
		# If our rollback value is big enough, remove entire operations from
		# the buffer.
		while self._buf and rollback >= self._buf[-1][0].bytespan:
			prevop, _, _, _ = self._buf.pop()
			rollback -= prevop.bytespan

		# If there's any rolling back left to do, and operations to roll
		# back...
		if rollback and self._buf:
			# We may want to mess with the last operation in the buffer, so
			# let's make a short name for it.
			prevOp, _, _, _ = self._buf[-1]

			# Grab the lastSourceCopyOffset and lastTargetCopyOffset that
			# affect prevOp.
			if len(self._buf) > 2:
				(_, writeOffset, startSourceCopyOffset,
						startTargetCopyOffset) = self._buf[-2]
			else:
				writeOffset = startSourceCopyOffset = startTargetCopyOffset = 0

			# Option 1 is to shrink the new operation, and leave the
			# previous operation alone.
			opt1newOp = copy.copy(operation)
			opt1newOp.shrink(rollback)
			opt1eff = op_sequence_efficiency(
					[prevOp, opt1newOp],
					startSourceCopyOffset, startTargetCopyOffset
				)

			# Option 2 is to shrink the last operation, and leave the new
			# operation alone.
			opt2prevOp = copy.copy(prevOp)
			opt2prevOp.shrink(-rollback)
			opt2eff = op_sequence_efficiency(
					[opt2prevOp, operation],
					startSourceCopyOffset, startTargetCopyOffset,
				)

			# Option 3 is to leave the new operation alone, and replace the
			# last operation with a TargetRead.
			trStart = writeOffset
			trEnd   = trStart + (prevOp.bytespan - rollback)
			opt3prevOp = TargetRead(self.target[trStart:trEnd])
			opt3eff = op_sequence_efficiency(
					[opt3prevOp, operation],
					startSourceCopyOffset, startTargetCopyOffset,
				)

			# Which option is the most efficient?
			maxEff = max(opt1eff, opt2eff, opt3eff)

			if maxEff == opt1eff:
				# Use the new operation we created for option 1.
				operation = opt1newOp

			elif maxEff == opt2eff:
				# Replace the last operation in self._buf with the truncated
				# one we created for option 2.
				self._buf.pop()
				self._append(opt2prevOp)

			else:
				# Replace the last operation in self._buf with the TargetRead
				# we created for option 2.
				self._buf.pop()
				if self._buf and isinstance(self._buf[-1][0], TargetRead):
					penultimateOp, *_ = self._buf.pop()
					penultimateOp.extend(opt3prevOp)
					self._append(penultimateOp)
				else:
					self._append(opt3prevOp)

		# We've been asked to roll back past the first operation.
		elif rollback:
			operation.shrink(rollback)

		self._append(operation)

	def copy_offsets(self, rollback=0):
		copyOffsets = [0, 0]

		index = len(self._buf) - 1

		while index >= 0:
			op, writeOffset, *copyOffsets = self._buf[index]

			if rollback < op.bytespan: break

			rollback -= op.bytespan
			index -= 1

		return tuple(copyOffsets)
