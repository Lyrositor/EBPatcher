#!/usr/bin/env python3
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