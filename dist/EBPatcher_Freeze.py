#   EarthBound Patcher - An easy-to-use EarthBound ROM patcher.
#   Copyright (C) 2013  Lyrositor <gagne.marc@gmail.com>
#
#   This file is part of EarthBound Patcher.
#
#   EarthBound Patcher is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   EarthBound Patcher is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with EarthBound Patcher.  If not, see <http://www.gnu.org/licenses/>.

# EarthBound Patcher - cx_Freeze setup script

import sys
from cx_Freeze import setup, Executable

sys.path.append("../")

from EBPatcher import VERSION

build_exe_options = {"optimize": 2, "icon": "../res/EBPatcher_Icon.ico", "include_files": [("../patches", "patches")]}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(name = "EBPatcher",
      version = str(VERSION),
      description = "EarthBound Patcher",
      options = {"build_exe": build_exe_options},
      executables = [Executable("../EBPatcher.py", base=base)])