"""
Custom Django test runner that outputs one JSON line per test result.

Used by the admin panel's subprocess-based test executor so results can
be streamed and parsed without touching the main process's database
settings.
"""

import json
import sys
import time
import unittest

from django.test.runner import DiscoverRunner


class _StreamingResult(unittest.TestResult):
    """Writes a JSON line to stdout after each test completes."""

    PREFIX = '__TEST_JSON__'

    def startTest(self, test):
        super().startTest(test)
        self._start_time = time.time()

    def _emit(self, test, status, output=''):
        duration = round((time.time() - self._start_time) * 1000, 2)
        method = str(test).split()[0]
        module = test.__class__.__module__
        cls = test.__class__.__name__
        line = json.dumps({
            'type': 'result',
            'test_id': f'{module}.{cls}.{method}',
            'module': module,
            'class_name': cls,
            'method': method,
            'description': test.shortDescription() or '',
            'status': status,
            'duration_ms': duration,
            'output': output,
        })
        sys.stdout.write(f'{self.PREFIX}{line}\n')
        sys.stdout.flush()

    def addSuccess(self, test):
        super().addSuccess(test)
        self._emit(test, 'pass')

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._emit(test, 'fail', self._exc_info_to_string(err, test))

    def addError(self, test, err):
        super().addError(test, err)
        self._emit(test, 'error', self._exc_info_to_string(err, test))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self._emit(test, 'skipped', reason)


class _StreamingRunner(unittest.TextTestRunner):
    """TextTestRunner replacement that uses _StreamingResult."""

    def run(self, suite):
        result = _StreamingResult()
        # Emit total count before starting
        total = suite.countTestCases()
        line = json.dumps({'type': 'total', 'count': total})
        sys.stdout.write(f'{_StreamingResult.PREFIX}{line}\n')
        sys.stdout.flush()

        suite(result)
        return result


class StreamingDiscoverRunner(DiscoverRunner):
    """Drop-in DiscoverRunner that streams JSON results to stdout."""
    test_runner = _StreamingRunner
