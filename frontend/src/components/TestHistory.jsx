import { useState, useEffect } from 'react';
import { getTestRunHistory, getTestRunDetail } from '../services/api';
import TestResults from './TestResults';

function TestHistory() {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedRun, setSelectedRun] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const resp = await getTestRunHistory();
      setRuns(resp.data);
    } catch (err) {
      console.error('Failed to load test history:', err);
    } finally {
      setLoading(false);
    }
  };

  const viewRun = async (runId) => {
    if (selectedRun?.id === runId) {
      setSelectedRun(null);
      return;
    }
    setLoadingDetail(true);
    try {
      const resp = await getTestRunDetail(runId);
      setSelectedRun(resp.data);
    } catch (err) {
      console.error('Failed to load run detail:', err);
    } finally {
      setLoadingDetail(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '--';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  };

  const formatDuration = (run) => {
    if (!run.started_at || !run.completed_at) return '--';
    const ms = new Date(run.completed_at) - new Date(run.started_at);
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const getStatusBadgeClass = (s) => {
    if (s === 'completed') return 'badge-pass';
    if (s === 'failed') return 'badge-fail';
    if (s === 'running') return 'badge-running';
    return 'badge-pending';
  };

  const getPassRate = (run) => {
    if (run.total_tests === 0) return '--';
    const pct = Math.round((run.passed / run.total_tests) * 100);
    return `${pct}%`;
  };

  const getPassRateClass = (run) => {
    if (run.total_tests === 0) return '';
    const pct = (run.passed / run.total_tests) * 100;
    if (pct === 100) return 'rate-pass';
    if (pct >= 80) return 'rate-warn';
    return 'rate-fail';
  };

  if (loading) {
    return <div className="loading">Loading history...</div>;
  }

  return (
    <div>
      <div className="admin-header">
        <div>
          <h2>Test History</h2>
          <p className="admin-subtitle">{runs.length} past runs</p>
        </div>
      </div>

      {runs.length === 0 ? (
        <div className="history-empty">
          No test runs yet. Go to the Runner tab and run some tests.
        </div>
      ) : (
        <div className="history-list">
          {runs.map((run) => (
            <div key={run.id}>
              <div
                className={`history-item ${
                  selectedRun?.id === run.id ? 'history-item-active' : ''
                }`}
                onClick={() => viewRun(run.id)}
              >
                <span
                  className={`history-status ${getStatusBadgeClass(run.status)}`}
                >
                  {run.status}
                </span>
                <span className={`history-rate ${getPassRateClass(run)}`}>
                  {getPassRate(run)}
                </span>
                <span className="history-counts">
                  {run.passed}/{run.total_tests} passed
                </span>
                <span className="history-duration">{formatDuration(run)}</span>
                <span className="history-time">{formatDate(run.created_at)}</span>
              </div>
              {selectedRun?.id === run.id && (
                <div className="history-detail">
                  {loadingDetail ? (
                    <div className="loading">Loading results...</div>
                  ) : (
                    <TestResults
                      results={selectedRun.results}
                      summary={{
                        total: selectedRun.total_tests,
                        passed: selectedRun.passed,
                        failed: selectedRun.failed,
                        errors: selectedRun.errors,
                        skipped: selectedRun.skipped,
                      }}
                    />
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default TestHistory;
