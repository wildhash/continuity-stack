import { useState, useEffect } from 'react';
import Head from 'next/head';
import ChatInterface from '../components/ChatInterface';
import ProfileTimeline from '../components/ProfileTimeline';
import DemoScenario from '../components/DemoScenario';
import { apiClient } from '../lib/api';

export default function Home() {
  const [activeTab, setActiveTab] = useState<'chat' | 'timeline' | 'demo'>('chat');
  const [apiConnected, setApiConnected] = useState(false);

  useEffect(() => {
    checkApiConnection();
  }, []);

  const checkApiConnection = async () => {
    try {
      await apiClient.health();
      setApiConnected(true);
    } catch (error) {
      console.error('API connection failed:', error);
      setApiConnected(false);
    }
  };

  return (
    <>
      <Head>
        <title>Lifeline UI - Continuity Stack</title>
        <meta name="description" content="Self-evolving AI agent interface" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <main className="min-h-screen bg-gradient-to-br from-gray-100 to-gray-200">
        <div className="container mx-auto px-4 py-8">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              Lifeline UI
            </h1>
            <p className="text-gray-600">
              Continuity Stack: Self-Evolving Agent System
            </p>
            <div className="mt-2 flex items-center space-x-2">
              <div
                className={`w-3 h-3 rounded-full ${
                  apiConnected ? 'bg-green-500' : 'bg-red-500'
                }`}
              />
              <span className="text-sm text-gray-600">
                {apiConnected ? 'Connected to EchoForge API' : 'API Disconnected'}
              </span>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="mb-6">
            <div className="border-b border-gray-300">
              <nav className="-mb-px flex space-x-8">
                <button
                  onClick={() => setActiveTab('chat')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === 'chat'
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  💬 Chat
                </button>
                <button
                  onClick={() => setActiveTab('timeline')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === 'timeline'
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  📊 Profile & Timeline
                </button>
                <button
                  onClick={() => setActiveTab('demo')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === 'demo'
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  🎬 Demo Scenario
                </button>
              </nav>
            </div>
          </div>

          {/* Content Area */}
          <div className="h-[600px]">
            {!apiConnected && (
              <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg
                      className="h-5 w-5 text-yellow-400"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path
                        fillRule="evenodd"
                        d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-yellow-700">
                      Backend API is not connected. Make sure the backend server is running.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'chat' && <ChatInterface />}
            {activeTab === 'timeline' && <ProfileTimeline />}
            {activeTab === 'demo' && <DemoScenario />}
          </div>

          {/* Footer */}
          <div className="mt-8 text-center text-sm text-gray-600">
            <p>
              Continuity Stack: Lifeline UI → EchoForge API → Continuity Core
            </p>
            <p className="mt-1">
              Powered by MemMachine + Neo4j Knowledge Graph
            </p>
          </div>
        </div>
      </main>
    </>
  );
}
