import { useState } from 'react';

function TestResults({ results, summary }) {
  const [expandedModules, setExpandedModules] = useState(() => {
    // Auto-expand all modules
    const mods = new Set();
    results.forEach((r) => mods.add(r.module));
    return mods;
  });
  const [expandedErrors, setExpandedErrors] = useState(() => {
    // Auto-expand failed tests
    const ids = new Set();
    results.forEach((r) => {
      if (r.status === 'fail' || r.status === 'error') ids.add(r.test_id);
    });
    return ids;
  });

  const toggleModule = (mod) => {
    setExpandedModules((prev) => {
      const next = new Set(prev);
      if (next.has(mod)) next.delete(mod);
      else next.add(mod);
      return next;
    });
  };

  const toggleError = (testId) => {
    setExpandedErrors((prev) => {
      const next = new Set(prev);
      if (next.has(testId)) next.delete(testId);
      else next.add(testId);
      return next;
    });
  };

  // Group results by module
  const modules = {};
  results.forEach((r) => {
    if (!modules[r.module]) {
      modules[r.module] = { module: r.module, tests: [] };
    }
    modules[r.module].tests.push(r);
  });
  const moduleList = Object.values(modules);

  const getModuleStats = (mod) => {
    const passed = mod.tests.filter((t) => t.status === 'pass').length;
    const failed = mod.tests.filter(
      (t) => t.status === 'fail' || t.status === 'error'
    ).length;
    return { total: mod.tests.length, passed, failed };
  };

  const getStatusClass = (s) => {
    if (s === 'pass') return 'test-pass';
    if (s === 'fail') return 'test-fail';
    if (s === 'error') return 'test-error';
    if (s === 'skipped') return 'test-skipped';
    return 'test-pending';
  };

  return (
    <div className="test-results-container">
      {/* Summary bar */}
      <div
        className={`admin-summary ${
          summary.failed + summary.errors > 0 ? 'has-failures' : 'all-passed'
        }`}
      >
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

      {/* Module groups */}
      <div className="admin-modules">
        {moduleList.map((mod) => {
          const stats = getModuleStats(mod);
          const isExpanded = expandedModules.has(mod.module);
          return (
            <div key={mod.module} className="admin-module">
              <div
                className="module-header"
                onClick={() => toggleModule(mod.module)}
              >
                <span
                  className={`module-chevron ${isExpanded ? 'expanded' : ''}`}
                >
                  &#9654;
                </span>
                <span className="module-name">{mod.module}</span>
                <span className="module-count">{stats.total} tests</span>
                <span
                  className={`module-badge ${
                    stats.failed > 0 ? 'badge-fail' : 'badge-pass'
                  }`}
                >
                  {stats.passed}/{stats.total} passed
                </span>
              </div>
              {isExpanded && (
                <div className="module-tests">
                  {mod.tests.map((test) => {
                    const hasOutput = test.output && test.output.length > 0;
                    const isErrorExpanded = expandedErrors.has(test.test_id);
                    return (
                      <div key={test.test_id} className="test-item">
                        <div className="test-row">
                          <span
                            className={`test-status ${getStatusClass(
                              test.status
                            )}`}
                          />
                          <div className="test-info">
                            <span className="test-method">{test.method}</span>
                            {test.description && (
                              <span className="test-description">
                                {test.description}
                              </span>
                            )}
                          </div>
                          <span className="test-duration">
                            {test.duration_ms}ms
                          </span>
                          {hasOutput && (
                            <button
                              className="btn-icon"
                              onClick={() => toggleError(test.test_id)}
                              title="Toggle output"
                            >
                              {isErrorExpanded ? '\u25B2' : '\u25BC'}
                            </button>
                          )}
                        </div>
                        {hasOutput && isErrorExpanded && (
                          <pre className="test-output">{test.output}</pre>
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

export default TestResults;
