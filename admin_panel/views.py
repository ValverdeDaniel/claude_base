import io
import time
import traceback
import unittest

from django.conf import settings
from django.test.runner import DiscoverRunner
from django.test.utils import setup_test_environment, teardown_test_environment
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


def discover_tests():
    """Discover all test cases and return structured info."""
    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir=str(settings.BASE_DIR),
        pattern='tests.py',
        top_level_dir=str(settings.BASE_DIR),
    )

    tests = []
    for group in suite:
        for test_group in group:
            if isinstance(test_group, unittest.TestSuite):
                for test in test_group:
                    test_method = str(test).split()
                    method_name = test_method[0] if test_method else str(test)
                    module = test.__class__.__module__
                    class_name = test.__class__.__name__
                    tests.append({
                        'id': f'{module}.{class_name}.{method_name}',
                        'module': module,
                        'class': class_name,
                        'method': method_name,
                        'description': test.shortDescription() or '',
                    })
            elif isinstance(test_group, unittest.TestCase):
                test_method = str(test_group).split()
                method_name = test_method[0] if test_method else str(test_group)
                module = test_group.__class__.__module__
                class_name = test_group.__class__.__name__
                tests.append({
                    'id': f'{module}.{class_name}.{method_name}',
                    'module': module,
                    'class': class_name,
                    'method': method_name,
                    'description': test_group.shortDescription() or '',
                })
    return tests


class ListTestsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tests = discover_tests()

        # Group by module
        modules = {}
        for test in tests:
            mod = test['module']
            if mod not in modules:
                modules[mod] = {
                    'module': mod,
                    'tests': [],
                }
            modules[mod]['tests'].append(test)

        return Response({
            'total': len(tests),
            'modules': list(modules.values()),
        })


class RunTestsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        test_ids = request.data.get('test_ids', [])

        runner = DiscoverRunner(verbosity=0, interactive=False)
        old_config = runner.setup_databases()

        try:
            loader = unittest.TestLoader()
            full_suite = loader.discover(
                start_dir=str(settings.BASE_DIR),
                pattern='tests.py',
                top_level_dir=str(settings.BASE_DIR),
            )

            # Flatten all tests
            all_tests = []
            for group in full_suite:
                for test_group in group:
                    if isinstance(test_group, unittest.TestSuite):
                        for test in test_group:
                            all_tests.append(test)
                    elif isinstance(test_group, unittest.TestCase):
                        all_tests.append(test_group)

            # Filter to requested tests (or run all)
            if test_ids:
                id_set = set(test_ids)
                filtered = []
                for test in all_tests:
                    method_name = str(test).split()[0]
                    module = test.__class__.__module__
                    class_name = test.__class__.__name__
                    test_id = f'{module}.{class_name}.{method_name}'
                    if test_id in id_set:
                        filtered.append(test)
                tests_to_run = filtered
            else:
                tests_to_run = all_tests

            suite = unittest.TestSuite(tests_to_run)

            results = []
            for test in tests_to_run:
                single_suite = unittest.TestSuite([test])
                stream = io.StringIO()
                test_runner = unittest.TextTestRunner(
                    stream=stream, verbosity=0
                )

                method_name = str(test).split()[0]
                module = test.__class__.__module__
                class_name = test.__class__.__name__
                test_id = f'{module}.{class_name}.{method_name}'

                start = time.time()
                result = test_runner.run(single_suite)
                duration = round((time.time() - start) * 1000, 2)

                if result.errors:
                    status = 'error'
                    output = result.errors[0][1]
                elif result.failures:
                    status = 'fail'
                    output = result.failures[0][1]
                elif result.skipped:
                    status = 'skipped'
                    output = result.skipped[0][1] if result.skipped else ''
                else:
                    status = 'pass'
                    output = ''

                results.append({
                    'id': test_id,
                    'module': module,
                    'class': class_name,
                    'method': method_name,
                    'status': status,
                    'duration_ms': duration,
                    'output': output,
                    'description': test.shortDescription() or '',
                })

            passed = sum(1 for r in results if r['status'] == 'pass')
            failed = sum(1 for r in results if r['status'] == 'fail')
            errors = sum(1 for r in results if r['status'] == 'error')
            skipped = sum(1 for r in results if r['status'] == 'skipped')

            return Response({
                'summary': {
                    'total': len(results),
                    'passed': passed,
                    'failed': failed,
                    'errors': errors,
                    'skipped': skipped,
                },
                'results': results,
            })
        finally:
            runner.teardown_databases(old_config)
