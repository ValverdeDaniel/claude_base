import { useState, useCallback } from 'react';
import { getTestRunDetail } from '../services/api';
import TestRunner from './TestRunner';
import TestProgressModal from './TestProgressModal';
import TestHistory from './TestHistory';

function AdminPage() {
  const [activeTab, setActiveTab] = useState('runner');
  const [currentRunId, setCurrentRunId] = useState(null);
  const [showProgress, setShowProgress] = useState(false);
  const [runResults, setRunResults] = useState(null);

  const handleRunStarted = (runId) => {
    setCurrentRunId(runId);
    setShowProgress(true);
    setRunResults(null);
  };

  const handleRunComplete = useCallback(async (runId, finalStatus) => {
    setShowProgress(false);
    try {
      const resp = await getTestRunDetail(runId);
      setRunResults(resp.data);
      setActiveTab('runner');
    } catch (err) {
      console.error('Failed to fetch run results:', err);
    }
  }, []);

  return (
    <div className="admin-container">
      <div className="admin-tabs">
        <button
          className={`admin-tab ${activeTab === 'runner' ? 'active' : ''}`}
          onClick={() => setActiveTab('runner')}
        >
          Runner
        </button>
        <button
          className={`admin-tab ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          History
        </button>
      </div>

      {activeTab === 'runner' && (
        <TestRunner
          onRunStarted={handleRunStarted}
          runResults={runResults}
        />
      )}

      {activeTab === 'history' && <TestHistory />}

      {showProgress && currentRunId && (
        <TestProgressModal
          runId={currentRunId}
          onComplete={handleRunComplete}
        />
      )}
    </div>
  );
}

export default AdminPage;
