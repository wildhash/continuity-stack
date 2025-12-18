import { useState } from 'react';
import Head from 'next/head';
import { apiClient } from '../lib/api';

interface RunResult {
  task_id: string;
  run_id: string;
  task_type: string;
  status: string;
  agent_version: string;
  steps: Array<{
    step: string;
    message?: string;
    capability_required?: string;
    has_capability?: boolean;
    lessons?: any[];
    error?: string;
  }>;
  error?: string;
  lesson?: string;
  output?: {
    message: string;
    memory_citations?: any[];
    graph_citations?: any[];
    citation_summary?: {
      has_citations: boolean;
      memory_count: number;
      lesson_count: number;
    };
  };
}

export default function Demo() {
  const [run1, setRun1] = useState<RunResult | null>(null);
  const [run2, setRun2] = useState<RunResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runDemo1 = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.executeTask({
        type: 'validation_task',
        data: { payload: 'test_data' },
        should_fail_first: true,
      });
      setRun1(response.data);
    } catch (err: any) {
      setError(`Run 1 failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const runDemo2 = async () => {
    if (!run1) {
      setError('Please run Demo 1 first');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.executeTask({
        type: 'validation_task',
        data: { payload: 'test_data' },
        should_fail_first: false,
      });
      setRun2(response.data);
    } catch (err: any) {
      setError(`Run 2 failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const resetDemo = async () => {
    setLoading(true);
    setError(null);
    try {
      await fetch('http://localhost:8000/api/demo/reset', { method: 'POST' });
      setRun1(null);
      setRun2(null);
    } catch (err: any) {
      setError(`Reset failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const RunCard = ({ run, title }: { run: RunResult; title: string }) => (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h3 className="text-xl font-bold mb-4 flex items-center">
        {run.status === 'failed' ? '❌' : '✅'} {title}
      </h3>
      
      <div className="space-y-3">
        <div className="flex justify-between text-sm">
          <span className="font-semibold">Status:</span>
          <span className={run.status === 'success' ? 'text-green-600' : 'text-red-600'}>
            {run.status.toUpperCase()}
          </span>
        </div>
        
        <div className="flex justify-between text-sm">
          <span className="font-semibold">Agent Version:</span>
          <span className="font-mono">{run.agent_version}</span>
        </div>

        {run.error && (
          <div className="bg-red-50 border border-red-200 rounded p-3 text-sm">
            <div className="font-semibold text-red-700">Error:</div>
            <div className="text-red-600">{run.error}</div>
          </div>
        )}

        {run.lesson && (
          <div className="bg-blue-50 border border-blue-200 rounded p-3 text-sm">
            <div className="font-semibold text-blue-700">💡 Lesson Learned:</div>
            <div className="text-blue-600">{run.lesson}</div>
          </div>
        )}

        {run.output?.citation_summary && run.output.citation_summary.has_citations && (
          <div className="bg-green-50 border border-green-200 rounded p-3 text-sm">
            <div className="font-semibold text-green-700">📚 Citations:</div>
            <div className="text-green-600">
              {run.output.citation_summary.memory_count} memories, {run.output.citation_summary.lesson_count} lessons
            </div>
          </div>
        )}

        <div className="mt-4">
          <div className="font-semibold text-sm mb-2">Execution Steps:</div>
          <div className="space-y-2">
            {run.steps.map((step, idx) => (
              <div key={idx} className="bg-gray-50 rounded p-2 text-xs">
                <div className="font-mono text-gray-600">{idx + 1}. {step.step}</div>
                {step.message && <div className="text-gray-700 mt-1">{step.message}</div>}
                {step.error && <div className="text-red-600 mt-1">Error: {step.error}</div>}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <>
      <Head>
        <title>Demo - Continuity Stack</title>
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-gray-100 to-gray-200 py-8">
        <div className="container mx-auto px-4 max-w-6xl">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              Continuity Stack Demo
            </h1>
            <p className="text-gray-600">
              Watch the agent fail → reflect → learn → succeed
            </p>
          </div>

          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
              {error}
            </div>
          )}

          <div className="flex gap-4 justify-center mb-8">
            <button
              onClick={runDemo1}
              disabled={loading}
              className="bg-red-600 hover:bg-red-700 text-white font-semibold py-3 px-6 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Running...' : '1️⃣ Run Demo (Fail)'}
            </button>

            <button
              onClick={runDemo2}
              disabled={loading || !run1}
              className="bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Running...' : '2️⃣ Run Demo (Succeed)'}
            </button>

            <button
              onClick={resetDemo}
              disabled={loading}
              className="bg-gray-600 hover:bg-gray-700 text-white font-semibold py-3 px-6 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              🔄 Reset
            </button>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <div>
              {run1 ? (
                <RunCard run={run1} title="Run 1: Initial Attempt" />
              ) : (
                <div className="bg-white rounded-lg shadow-lg p-6 text-center text-gray-400">
                  Click "Run Demo (Fail)" to start
                </div>
              )}
            </div>

            <div>
              {run2 ? (
                <RunCard run={run2} title="Run 2: After Learning" />
              ) : (
                <div className="bg-white rounded-lg shadow-lg p-6 text-center text-gray-400">
                  {run1 ? 'Click "Run Demo (Succeed)" to retry' : 'Run Demo 1 first'}
                </div>
              )}
            </div>
          </div>

          {run1 && run2 && (
            <div className="mt-8 bg-gradient-to-r from-blue-50 to-green-50 rounded-lg shadow-lg p-6">
              <h3 className="text-xl font-bold mb-4 text-center">
                🎓 Learning Summary
              </h3>
              <div className="grid md:grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-3xl font-bold text-red-600">
                    {run1.agent_version}
                  </div>
                  <div className="text-sm text-gray-600">Initial Version</div>
                </div>
                <div className="flex items-center justify-center">
                  <div className="text-4xl">→</div>
                </div>
                <div>
                  <div className="text-3xl font-bold text-green-600">
                    {run2.agent_version}
                  </div>
                  <div className="text-sm text-gray-600">Evolved Version</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
