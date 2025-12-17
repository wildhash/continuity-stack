import { useState } from 'react';
import { apiClient } from '../lib/api';

export default function DemoScenario() {
  const [running, setRunning] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [result, setResult] = useState<any>(null);

  const runScenario = async () => {
    setRunning(true);
    setLogs([]);
    setResult(null);

    try {
      const response = await apiClient.runDemoScenario();
      setLogs(response.scenario_log || []);
      setResult(response);
    } catch (error) {
      console.error('Error running scenario:', error);
      setLogs(['Error: Failed to run demo scenario']);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">Demo Scenario</h2>
      
      <div className="mb-4">
        <p className="text-gray-700 mb-2">
          This demo shows the complete learning loop:
        </p>
        <ol className="list-decimal list-inside text-sm text-gray-600 space-y-1">
          <li>Agent attempts a task and fails</li>
          <li>Agent reflects on the failure</li>
          <li>Agent learns a lesson and gains capability</li>
          <li>Lesson is stored in the knowledge graph</li>
          <li>Agent retries the task and succeeds</li>
        </ol>
      </div>

      <button
        onClick={runScenario}
        disabled={running}
        className="w-full py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed transition-all font-semibold"
      >
        {running ? 'Running Demo...' : 'Run Demo Scenario'}
      </button>

      {logs.length > 0 && (
        <div className="mt-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Execution Log</h3>
          <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm space-y-1 max-h-96 overflow-y-auto">
            {logs.map((log, index) => (
              <div key={index}>{log}</div>
            ))}
          </div>
        </div>
      )}

      {result && result.final_status && (
        <div className="mt-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Final Status</h3>
          <div className="bg-blue-50 border-l-4 border-blue-600 p-4 rounded">
            <p className="font-semibold">Version: {result.final_status.version}</p>
            <p className="text-sm mt-2">Capabilities: {result.final_status.capabilities.length}</p>
            <p className="text-sm">Lessons Learned: {result.final_status.lessons_learned.length}</p>
            
            {result.final_status.lessons_learned.length > 0 && (
              <div className="mt-3">
                <p className="text-sm font-semibold">Latest Lessons:</p>
                <ul className="text-sm mt-1 space-y-1">
                  {result.final_status.lessons_learned.map((lesson: string, idx: number) => (
                    <li key={idx} className="text-gray-700">• {lesson}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
