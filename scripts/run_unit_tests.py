#!/usr/bin/env python3
"""Run a subset of unit tests without pytest (to avoid plugin issues).
"""
from importlib import import_module

mod = import_module('tests.test_jupiter_client')

failed = 0
for name in dir(mod):
    if name.startswith('test_'):
        fn = getattr(mod, name)
        try:
            fn()
            print(f'OK: {name}')
        except AssertionError as e:
            failed += 1
            print(f'FAIL: {name} -> {e}')
        except Exception as e:
            failed += 1
            print(f'ERROR: {name} -> {e}')

if failed:
    raise SystemExit(1)
