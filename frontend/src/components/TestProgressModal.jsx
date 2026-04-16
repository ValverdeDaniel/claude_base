import { useState, useEffect, useRef } from 'react';
import { getTestRunStatus, cancelTestRun } from '../services/api';

function TestProgressModal({ runId, onComplete }) {
  const [progress, setProgress] = useState(null);
  const [error, setError] = useState('');
  const [cancelling, setCancelling] = useState(false);
  const intervalRef = useRef(null);

  useEffect(() => {
    if (!runId) return;

    const poll = async () => {
      try {
        const resp = await getTestRunStatus(runId);
        setProgress(resp.data);
        if (resp.data.status === 'completed' || resp.data.status === 'failed') {
          clearInterval(intervalRef.current);
          onComplete(runId, resp.data.status);
        }
      } catch (err) {
        setError('Lost connection to test runner.');
        clearInterval(intervalRef.current);
      }
    };

    // Poll immediately, then every 1.5s
    poll();
    intervalRef.current = setInterval(poll, 1500);

    return () => clearInterval(intervalRef.current);
  }, [runId, onComplete]);

  const handleCancel = async () => {
    setCancelling(true);
    try {
      await cancelTestRun(runId);
    } catch (err) {
      console.error('Failed to cancel:', err);
    }
  };

  const completed =
    progress
      ? progress.passed + progress.failed + progress.errors + progress.skipped
      : 0;
  const total = progress?.total_tests || 0;
  const pct = total > 0 ? Math.round((completed / total) * 100) : 0;

  // Show a "setting up" state while total is still 0
  const isSettingUp = progress && progress.status === 'running' && total === 0;

  // Extract just the method name from the full test ID
  const currentTestName = progress?.current_test
    ? progress.current_test.split('.').pop()
    : '';

  return (
    <div className="progress-overlay">
      <div className="progress-modal">
        <h3>{isSettingUp ? 'Setting Up Test Database...' : 'Running Tests'}</h3>

        {error && <div className="error-message">{error}</div>}

        <div className="progress-bar-track">
          <div
            className={`progress-bar-fill ${isSettingUp ? 'progress-bar-indeterminate' : ''}`}
            style={{ width: isSettingUp ? '100%' : `${pct}%` }}
          />
        </div>

        {!isSettingUp && (
          <>
            <div className="progress-pct">{pct}%</div>

            <div className="progress-counters">
              <div className="progress-counter">
                <span className="progress-counter-count">{completed}</span>
                <span className="progress-counter-label">/ {total}</span>
              </div>
              <div className="progress-counter counter-pass">
                <span className="progress-counter-count">{progress?.passed || 0}</span>
                <span className="progress-counter-label">passed</span>
              </div>
              <div className="progress-counter counter-fail">
                <span className="progress-counter-count">
                  {(progress?.failed || 0) + (progress?.errors || 0)}
                </span>
                <span className="progress-counter-label">failed</span>
              </div>
            </div>

            {currentTestName && (
              <div className="progress-current-test">
                {currentTestName}
              </div>
            )}
          </>
        )}

        {isSettingUp && (
          <p className="progress-setup-hint">
            Creating test database and running migrations...
          </p>
        )}

        <button
          className="btn btn-danger progress-cancel-btn"
          onClick={handleCancel}
          disabled={cancelling}
        >
          {cancelling ? 'Cancelling...' : 'Cancel'}
        </button>
      </div>
    </div>
  );
}

export default TestProgressModal;
