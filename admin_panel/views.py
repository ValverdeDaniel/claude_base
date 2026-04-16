import json
import subprocess
import sys
import threading
import unittest

import django.db
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import TestResult, TestRun

# ---------------------------------------------------------------------------
# In-memory progress store
#
# The test subprocess is completely isolated — it never touches the main
# process's database connections or settings.  Progress is tracked here
# in a plain dict so the polling endpoint can return live counters.
# ---------------------------------------------------------------------------
_active_runs = {}  # run_id -> dict
_lock = threading.Lock()

_STATUS_KEY = {
    'pass': 'passed',
    'fail': 'failed',
    'error': 'errors',
    'skipped': 'skipped',
}

# Prefix emitted by admin_panel.runner._StreamingResult
_JSON_PREFIX = '__TEST_JSON__'


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
                    _append_test_info(tests, test)
            elif isinstance(test_group, unittest.TestCase):
                _append_test_info(tests, test_group)
    return tests


def _append_test_info(tests, test):
    method_name = str(test).split()[0]
    module = test.__class__.__module__
    class_name = test.__class__.__name__
    tests.append({
        'id': f'{module}.{class_name}.{method_name}',
        'module': module,
        'class': class_name,
        'method': method_name,
        'description': test.shortDescription() or '',
    })


def _run_tests_in_thread(run_id, test_ids):
    """Spawn a subprocess to run tests, streaming JSON results."""
    # Close connections inherited from the request thread
    django.db.connections.close_all()

    # Mark as running in the DB
    run = TestRun.objects.get(pk=run_id)
    run.status = 'running'
    run.started_at = timezone.now()
    run.save(update_fields=['status', 'started_at'])

    # Initialize in-memory progress
    with _lock:
        _active_runs[run_id] = {
            'status': 'running',
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': 0,
            'skipped': 0,
            'current_test': '',
            'cancelled': False,
        }

    # Build the manage.py test command
    cmd = [
        sys.executable,
        str(settings.BASE_DIR / 'manage.py'),
        'test',
        '--testrunner=admin_panel.runner.StreamingDiscoverRunner',
        '--no-input',
    ]
    if test_ids:
        cmd.extend(test_ids)

    collected_results = []
    proc = None

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(settings.BASE_DIR),
        )

        for line in proc.stdout:
            # Check for cancellation
            with _lock:
                if _active_runs.get(run_id, {}).get('cancelled'):
                    proc.terminate()
                    break

            line = line.rstrip('\n')
            if not line.startswith(_JSON_PREFIX):
                continue

            data = json.loads(line[len(_JSON_PREFIX):])

            if data['type'] == 'total':
                with _lock:
                    if run_id in _active_runs:
                        _active_runs[run_id]['total_tests'] = data['count']
                # Also persist total to DB so history shows it
                run.total_tests = data['count']
                run.save(update_fields=['total_tests'])

            elif data['type'] == 'result':
                collected_results.append(data)
                with _lock:
                    if run_id in _active_runs:
                        _active_runs[run_id]['current_test'] = data['test_id']
                        key = _STATUS_KEY[data['status']]
                        _active_runs[run_id][key] += 1

        proc.wait()

    except Exception:
        with _lock:
            if run_id in _active_runs:
                _active_runs[run_id]['status'] = 'failed'

    # Persist results to the real database
    was_cancelled = False
    with _lock:
        prog = _active_runs.get(run_id, {})
        was_cancelled = prog.get('cancelled', False)
        mem_status = prog.get('status', 'completed')

    try:
        run.refresh_from_db()

        TestResult.objects.bulk_create([
            TestResult(
                test_run=run,
                test_id=r['test_id'],
                module=r['module'],
                class_name=r['class_name'],
                method=r['method'],
                description=r['description'],
                status=r['status'],
                duration_ms=r['duration_ms'],
                output=r['output'],
            )
            for r in collected_results
        ])

        run.passed = sum(1 for r in collected_results if r['status'] == 'pass')
        run.failed = sum(1 for r in collected_results if r['status'] == 'fail')
        run.errors = sum(1 for r in collected_results if r['status'] == 'error')
        run.skipped = sum(1 for r in collected_results if r['status'] == 'skipped')
        run.total_tests = len(collected_results)
        run.current_test = ''
        run.completed_at = timezone.now()

        if was_cancelled or mem_status == 'failed':
            run.status = 'failed'
        else:
            run.status = 'completed'

        run.save()
    except Exception:
        pass  # Best-effort
    finally:
        with _lock:
            _active_runs.pop(run_id, None)
        django.db.close_old_connections()


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

class ListTestsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tests = discover_tests()

        modules = {}
        for test in tests:
            mod = test['module']
            if mod not in modules:
                modules[mod] = {'module': mod, 'tests': []}
            modules[mod]['tests'].append(test)

        return Response({
            'total': len(tests),
            'modules': list(modules.values()),
        })


class RunTestsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Clean up orphaned runs
        stale = TestRun.objects.filter(status__in=['pending', 'running'])
        for orphan in stale:
            if orphan.pk not in _active_runs:
                orphan.status = 'failed'
                orphan.completed_at = timezone.now()
                orphan.current_test = ''
                orphan.save(update_fields=['status', 'completed_at', 'current_test'])

        if _active_runs:
            return Response(
                {'error': 'A test run is already in progress.'},
                status=status.HTTP_409_CONFLICT,
            )

        test_ids = request.data.get('test_ids', [])
        run = TestRun.objects.create(user=request.user)

        thread = threading.Thread(
            target=_run_tests_in_thread,
            args=(run.id, test_ids),
            daemon=True,
        )
        thread.start()

        return Response({
            'id': run.id,
            'status': run.status,
        }, status=status.HTTP_201_CREATED)


class TestRunStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        with _lock:
            prog = _active_runs.get(pk)
            if prog:
                return Response({
                    'id': pk,
                    'status': prog['status'],
                    'total_tests': prog['total_tests'],
                    'passed': prog['passed'],
                    'failed': prog['failed'],
                    'errors': prog['errors'],
                    'skipped': prog['skipped'],
                    'current_test': prog['current_test'],
                })

        try:
            run = TestRun.objects.get(pk=pk)
        except TestRun.DoesNotExist:
            return Response(
                {'error': 'Test run not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({
            'id': run.id,
            'status': run.status,
            'total_tests': run.total_tests,
            'passed': run.passed,
            'failed': run.failed,
            'errors': run.errors,
            'skipped': run.skipped,
            'current_test': run.current_test,
        })


class CancelTestRunView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        with _lock:
            prog = _active_runs.get(pk)
            if prog:
                prog['cancelled'] = True
                return Response({'message': 'Cancellation requested.'})

        return Response(
            {'error': 'No active run found with that ID.'},
            status=status.HTTP_404_NOT_FOUND,
        )


class TestRunDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            run = TestRun.objects.get(pk=pk)
        except TestRun.DoesNotExist:
            return Response(
                {'error': 'Test run not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        results = run.results.all().order_by('completed_at')

        return Response({
            'id': run.id,
            'status': run.status,
            'total_tests': run.total_tests,
            'passed': run.passed,
            'failed': run.failed,
            'errors': run.errors,
            'skipped': run.skipped,
            'current_test': run.current_test,
            'created_at': run.created_at,
            'started_at': run.started_at,
            'completed_at': run.completed_at,
            'results': [
                {
                    'id': r.id,
                    'test_id': r.test_id,
                    'module': r.module,
                    'class': r.class_name,
                    'method': r.method,
                    'description': r.description,
                    'status': r.status,
                    'duration_ms': r.duration_ms,
                    'output': r.output,
                }
                for r in results
            ],
        })


class TestRunListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        runs = TestRun.objects.all()[:50]

        return Response([
            {
                'id': run.id,
                'status': run.status,
                'total_tests': run.total_tests,
                'passed': run.passed,
                'failed': run.failed,
                'errors': run.errors,
                'skipped': run.skipped,
                'created_at': run.created_at,
                'started_at': run.started_at,
                'completed_at': run.completed_at,
            }
            for run in runs
        ])
