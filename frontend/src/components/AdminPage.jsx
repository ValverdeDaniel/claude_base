import { useState, useEffect } from 'react';
import { getTests, runTests } from '../services/api';

function AdminPage() {
  const [modules, setModules] = useState([]);
  const [totalTests, setTotalTests] = useState(0);
  const [results, setResults] = useState({});
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [runningIds, setRunningIds] = useState(new Set());
  const [expandedModules, setExpandedModules] = useState(new Set());
  const [expandedErrors, setExpandedErrors] = useState(new Set());

  useEffect(() => {
    loadTests();
  }, []);

  const loadTests = async () => {
    try {
      const resp = await getTests();
      setModules(resp.data.modules);
      setTotalTests(resp.data.total);
      // Auto-expand all modules
      setExpandedModules(new Set(resp.data.modules.map((m) => m.module)));
    } catch (err) {
      console.error('Failed to load tests:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunAll = async () => {
    setRunning(true);
    setSummary(null);
    setResults({});
    setExpandedErrors(new Set());
    const allIds = modules.flatMap((m) => m.tests.map((t) => t.id));
    setRunningIds(new Set(allIds));
    try {
      const resp = await runTests([]);
      const resultMap = {};
      resp.data.results.forEach((r) => {
        resultMap[r.id] = r;
      });
      setResults(resultMap);
      setSummary(resp.data.summary);
      // Auto-expand errors
      const errorIds = new Set();
      resp.data.results.forEach((r) => {
        if (r.status === 'fail' || r.status === 'error') {
          errorIds.add(r.id);
        }
      });
      setExpandedErrors(errorIds);
    } catch (err) {
      console.error('Failed to run tests:', err);
    } finally {
      setRunning(false);
      setRunningIds(new Set());
    }
  };

  const handleRunModule = async (moduleName) => {
    const mod = modules.find((m) => m.module === moduleName);
    if (!mod) return;
    const ids = mod.tests.map((t) => t.id);
    setRunningIds(new Set(ids));
    // Clear previous results for this module
    setResults((prev) => {
      const next = { ...prev };
      ids.forEach((id) => delete next[id]);
      return next;
    });
    try {
      const resp = await runTests(ids);
      const resultMap = { ...results };
      resp.data.results.forEach((r) => {
        resultMap[r.id] = r;
      });
      setResults(resultMap);
      updateSummary(resultMap);
      // Auto-expand errors
      const newErrors = new Set(expandedErrors);
      resp.data.results.forEach((r) => {
        if (r.status === 'fail' || r.status === 'error') {
          newErrors.add(r.id);
        }
      });
      setExpandedErrors(newErrors);
    } catch (err) {
      console.error('Failed to run module tests:', err);
    } finally {
      setRunningIds(new Set());
    }
  };

  const handleRunSingle = async (testId) => {
    setRunningIds(new Set([testId]));
    setResults((prev) => {
      const next = { ...prev };
      delete next[testId];
      return next;
    });
    try {
      const resp = await runTests([testId]);
      const resultMap = { ...results };
      resp.data.results.forEach((r) => {
        resultMap[r.id] = r;
      });
      setResults(resultMap);
      updateSummary(resultMap);
      // Auto-expand errors
      const newErrors = new Set(expandedErrors);
      resp.data.results.forEach((r) => {
        if (r.status === 'fail' || r.status === 'error') {
          newErrors.add(r.id);
        }
      });
      setExpandedErrors(newErrors);
    } catch (err) {
      console.error('Failed to run test:', err);
    } finally {
      setRunningIds(new Set());
    }
  };

  const updateSummary = (resultMap) => {
    const all = Object.values(resultMap);
    if (all.length === 0) {
      setSummary(null);
      return;
    }
    setSummary({
      total: all.length,
      passed: all.filter((r) => r.status === 'pass').length,
      failed: all.filter((r) => r.status === 'fail').length,
      errors: all.filter((r) => r.status === 'error').length,
      skipped: all.filter((r) => r.status === 'skipped').length,
    });
  };

  const toggleModule = (moduleName) => {
    setExpandedModules((prev) => {
      const next = new Set(prev);
      if (next.has(moduleName)) {
        next.delete(moduleName);
      } else {
        next.add(moduleName);
      }
      return next;
    });
  };

  const toggleError = (testId) => {
    setExpandedErrors((prev) => {
      const next = new Set(prev);
      if (next.has(testId)) {
        next.delete(testId);
      } else {
        next.add(testId);
      }
      return next;
    });
  };

  const getStatusIcon = (testId) => {
    if (runningIds.has(testId)) return <span className="test-status test-running" />;
    const result = results[testId];
    if (!result) return <span className="test-status test-pending" />;
    if (result.status === 'pass') return <span className="test-status test-pass" />;
    if (result.status === 'fail') return <span className="test-status test-fail" />;
    if (result.status === 'error') return <span className="test-status test-error" />;
    if (result.status === 'skipped') return <span className="test-status test-skipped" />;
    return <span className="test-status test-pending" />;
  };

  const getModuleStats = (mod) => {
    const ids = mod.tests.map((t) => t.id);
    const ran = ids.filter((id) => results[id]);
    if (ran.length === 0) return null;
    const passed = ran.filter((id) => results[id].status === 'pass').length;
    const failed = ran.filter(
      (id) => results[id].status === 'fail' || results[id].status === 'error'
    ).length;
    return { ran: ran.length, total: ids.length, passed, failed };
  };

  if (loading) {
    return <div className="loading">Loading tests...</div>;
  }

  return (
    <div className="admin-container">
      <div className="admin-header">
        <div>
          <h2>Test Runner</h2>
          <p className="admin-subtitle">{totalTests} tests discovered</p>
        </div>
        <button
          className="btn btn-primary admin-run-all"
          onClick={handleRunAll}
          disabled={running}
        >
          {running ? 'Running...' : 'Run All Tests'}
        </button>
      </div>

      {summary && (
        <div className={`admin-summary ${summary.failed + summary.errors > 0 ? 'has-failures' : 'all-passed'}`}>
          <div className="summary-item summary-total">
            <span className="summary-count">{summary.total}</span>
            <span className="summary-label">Total</span>
          </div>
          <div className="summary-item summary-passed">
            <span className="summary-count">{summary.passed}</span>
            <span className="summary-label">Passed</span>
          </div>
          <div className="summary-item summary-failed">
            <span className="summary-count">{summary.failed}</span>
            <span className="summary-label">Failed</span>
          </div>
          <div className="summary-item summary-errors">
            <span className="summary-count">{summary.errors}</span>
            <span className="summary-label">Errors</span>
          </div>
        </div>
      )}

      <div className="admin-modules">
        {modules.map((mod) => {
          const stats = getModuleStats(mod);
          const isExpanded = expandedModules.has(mod.module);
          return (
            <div key={mod.module} className="admin-module">
              <div className="module-header" onClick={() => toggleModule(mod.module)}>
                <span className={`module-chevron ${isExpanded ? 'expanded' : ''}`}>
                  &#9654;
                </span>
                <span className="module-name">{mod.module}</span>
                <span className="module-count">{mod.tests.length} tests</span>
                {stats && (
                  <span className={`module-badge ${stats.failed > 0 ? 'badge-fail' : 'badge-pass'}`}>
                    {stats.passed}/{stats.ran} passed
                  </span>
                )}
                <button
                  className="btn btn-secondary btn-sm module-run-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRunModule(mod.module);
                  }}
                  disabled={running}
                >
                  Run
                </button>
              </div>
              {isExpanded && (
                <div className="module-tests">
                  {mod.tests.map((test) => {
                    const result = results[test.id];
                    const hasOutput =
                      result && result.output && result.output.length > 0;
                    const isErrorExpanded = expandedErrors.has(test.id);
                    return (
                      <div key={test.id} className="test-item">
                        <div className="test-row">
                          {getStatusIcon(test.id)}
                          <div className="test-info">
                            <span className="test-method">{test.method}</span>
                            {test.description && (
                              <span className="test-description">
                                {test.description}
                              </span>
                            )}
                          </div>
                          {result && (
                            <span className="test-duration">
                              {result.duration_ms}ms
                            </span>
                          )}
                          {hasOutput && (
                            <button
                              className="btn-icon"
                              onClick={() => toggleError(test.id)}
                              title="Toggle output"
                            >
                              {isErrorExpanded ? '\u25B2' : '\u25BC'}
                            </button>
                          )}
                          <button
                            className="btn btn-secondary btn-sm"
                            onClick={() => handleRunSingle(test.id)}
                            disabled={runningIds.has(test.id)}
                          >
                            Run
                          </button>
                        </div>
                        {hasOutput && isErrorExpanded && (
                          <pre className="test-output">{result.output}</pre>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default AdminPage;
