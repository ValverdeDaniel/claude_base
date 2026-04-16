import { useState, useEffect } from 'react';
import { getTests, runTests } from '../services/api';
import TestResults from './TestResults';

function TestRunner({ onRunStarted, runResults }) {
  const [modules, setModules] = useState([]);
  const [totalTests, setTotalTests] = useState(0);
  const [loading, setLoading] = useState(true);
  const [expandedModules, setExpandedModules] = useState(new Set());
  const [selectedTests, setSelectedTests] = useState(new Set());
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadTests();
  }, []);

  const loadTests = async () => {
    try {
      const resp = await getTests();
      setModules(resp.data.modules);
      setTotalTests(resp.data.total);
      setExpandedModules(new Set(resp.data.modules.map((m) => m.module)));
      // Select all by default
      const allIds = new Set(
        resp.data.modules.flatMap((m) => m.tests.map((t) => t.id))
      );
      setSelectedTests(allIds);
    } catch (err) {
      console.error('Failed to load tests:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleModule = (moduleName) => {
    setExpandedModules((prev) => {
      const next = new Set(prev);
      if (next.has(moduleName)) next.delete(moduleName);
      else next.add(moduleName);
      return next;
    });
  };

  const toggleSelectAll = (mod) => {
    const ids = mod.tests.map((t) => t.id);
    const allSelected = ids.every((id) => selectedTests.has(id));
    setSelectedTests((prev) => {
      const next = new Set(prev);
      if (allSelected) {
        ids.forEach((id) => next.delete(id));
      } else {
        ids.forEach((id) => next.add(id));
      }
      return next;
    });
  };

  const toggleTest = (testId) => {
    setSelectedTests((prev) => {
      const next = new Set(prev);
      if (next.has(testId)) next.delete(testId);
      else next.add(testId);
      return next;
    });
  };

  const handleRun = async (ids) => {
    setStarting(true);
    setError('');
    try {
      const resp = await runTests(ids);
      onRunStarted(resp.data.id);
    } catch (err) {
      if (err.response?.status === 409) {
        setError('A test run is already in progress.');
      } else {
        setError('Failed to start test run.');
      }
    } finally {
      setStarting(false);
    }
  };

  const handleRunAll = () => handleRun([]);

  const handleRunSelected = () => handleRun([...selectedTests]);

  const handleRunModule = (mod) => {
    const ids = mod.tests.map((t) => t.id);
    handleRun(ids);
  };

  if (loading) {
    return <div className="loading">Loading tests...</div>;
  }

  return (
    <div>
      <div className="admin-header">
        <div>
          <h2>Test Runner</h2>
          <p className="admin-subtitle">
            {totalTests} tests discovered &middot; {selectedTests.size} selected
          </p>
        </div>
        <div className="admin-header-actions">
          <button
            className="btn btn-secondary admin-run-all"
            onClick={handleRunSelected}
            disabled={starting || selectedTests.size === 0}
          >
            Run Selected ({selectedTests.size})
          </button>
          <button
            className="btn btn-primary admin-run-all"
            onClick={handleRunAll}
            disabled={starting}
          >
            {starting ? 'Starting...' : 'Run All Tests'}
          </button>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      {runResults && (
        <TestResults
          results={runResults.results}
          summary={{
            total: runResults.total_tests,
            passed: runResults.passed,
            failed: runResults.failed,
            errors: runResults.errors,
            skipped: runResults.skipped,
          }}
        />
      )}

      <div className="admin-modules">
        {modules.map((mod) => {
          const isExpanded = expandedModules.has(mod.module);
          const modIds = mod.tests.map((t) => t.id);
          const allSelected = modIds.every((id) => selectedTests.has(id));
          const someSelected =
            !allSelected && modIds.some((id) => selectedTests.has(id));

          return (
            <div key={mod.module} className="admin-module">
              <div className="module-header">
                <input
                  type="checkbox"
                  className="test-checkbox"
                  checked={allSelected}
                  ref={(el) => {
                    if (el) el.indeterminate = someSelected;
                  }}
                  onChange={() => toggleSelectAll(mod)}
                />
                <span
                  className={`module-chevron ${isExpanded ? 'expanded' : ''}`}
                  onClick={() => toggleModule(mod.module)}
                >
                  &#9654;
                </span>
                <span
                  className="module-name"
                  onClick={() => toggleModule(mod.module)}
                >
                  {mod.module}
                </span>
                <span className="module-count">{mod.tests.length} tests</span>
                <button
                  className="btn btn-secondary btn-sm module-run-btn"
                  onClick={() => handleRunModule(mod)}
                  disabled={starting}
                >
                  Run
                </button>
              </div>
              {isExpanded && (
                <div className="module-tests">
                  {mod.tests.map((test) => (
                    <div key={test.id} className="test-item">
                      <div className="test-row">
                        <input
                          type="checkbox"
                          className="test-checkbox"
                          checked={selectedTests.has(test.id)}
                          onChange={() => toggleTest(test.id)}
                        />
                        <span className="test-status test-pending" />
                        <div className="test-info">
                          <span className="test-method">{test.method}</span>
                          {test.description && (
                            <span className="test-description">
                              {test.description}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default TestRunner;
