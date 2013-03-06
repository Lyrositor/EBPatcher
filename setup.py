#!/usr/bin/env python3

"""
    EarthBound Patcher - An easy-to-use EarthBound ROM patcher.
    Copyright (C) 2013  Lyrositor <gagne.marc@gmail.com>

    This file is part of EarthBound Patcher.

    EarthBound Patcher is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    EarthBound Patcher is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with EarthBound Patcher.  If not, see <http://www.gnu.org/licenses/>.
"""

# EBPatcher setup script using cx_Freeze.

from cx_Freeze import setup, Executable
import sys

from EBPatcher import VERSION

build_exe_options = {"build_exe": "build",
					 "create_shared_zip": True,
					 "icon": "res/EBPatcher_Icon.ico",
					 "include_files": ["patches", "res", "ui"]}
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(name = "EBPatcher",
      version = VERSION,
      description = "EarthBound Patcher",
      options = {"build_exe": build_exe_options},
      executables = [Executable("EBPatcher.py", base=base,
								icon="res/EBPatcher_Icon.ico",
								shortcutName="EarthBound Patcher")])
