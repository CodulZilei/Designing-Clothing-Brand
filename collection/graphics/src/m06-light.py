#!/usr/bin/env python3
"""m06-light — NEPĂMÂNTEAN one-line wordmark, dark inks for light fabrics (same as m06-dark).
Run: python3 graphics/src/m06-light.py"""
import importlib.util
import os

spec = importlib.util.spec_from_file_location("m06", os.path.join(os.path.dirname(os.path.abspath(__file__)), "m06-dark.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.build("light")
