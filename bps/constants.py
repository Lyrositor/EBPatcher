# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING for more details.

BPS_MAGIC = b'BPS1'
BPSASM_MAGIC = 'bpsasm\n'

# Headings used by the BPS assembly format.
SOURCESIZE  = "sourcesize"
TARGETSIZE  = "targetsize"
METADATA    = "metadata"
SOURCEREAD  = "sourceread"
TARGETREAD  = "targetread"
SOURCECOPY  = "sourcecopy"
TARGETCOPY  = "targetcopy"
SOURCECRC32 = "sourcecrc32"
TARGETCRC32 = "targetcrc32"

# Values used in patch-hunk encoding.
OP_SOURCEREAD = 0b00
OP_TARGETREAD = 0b01
OP_SOURCECOPY = 0b10
OP_TARGETCOPY = 0b11

OPCODEMASK = 0b11
OPCODESHIFT = 2
