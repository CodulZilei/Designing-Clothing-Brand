#!/usr/bin/env python3
"""g29-light — NU SUNTEM SINGURI, dark inks for light fabrics (same composition as g29-dark).
Run: python3 graphics/src/g29-light.py"""
import importlib.util
import os

spec = importlib.util.spec_from_file_location("g29", os.path.join(os.path.dirname(os.path.abspath(__file__)), "g29-dark.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.build("light")
