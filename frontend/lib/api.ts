import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ChatResponse {
  response: string;
  timestamp: string;
  agent_version: string;
}

export interface AgentStatus {
  version: string;
  capabilities: string[];
  learned_lessons: string[];
  total_tasks: number;
  total_reflections: number;
}

export interface AgentHistory {
  tasks: any[];
  reflections: any[];
}

export interface DemoResult {
  scenario_log: string[];
  final_status: {
    version: string;
    capabilities: string[];
    lessons_learned: string[];
  };
}

export const apiClient = {
  async sendChatMessage(message: string): Promise<ChatResponse> {
    const response = await axios.post(`${API_URL}/api/chat/send`, { message });
    return response.data;
  },

  async health() {
    const response = await axios.get(`${API_URL}/health`);
    return response.data;
  },

  async healthDeps() {
    const response = await axios.get(`${API_URL}/health/deps`);
    return response.data;
  },

  async executeTask(task: {
    type: string;
    data: any;
    should_fail_first: boolean;
  }) {
    const response = await axios.post(`${API_URL}/api/tasks/execute`, task);
    return response.data;
  },

  async getAgentStatus(): Promise<AgentStatus> {
    const response = await axios.get(`${API_URL}/api/agent/status`);
    return response.data;
  },

  async getAgentHistory(): Promise<AgentHistory> {
    const response = await axios.get(`${API_URL}/api/agent/history`);
    return response.data;
  },

  async runDemoScenario(): Promise<DemoResult> {
    const response = await axios.post(`${API_URL}/api/demo/run-scenario`);
    return response.data;
  },

  async resetDemo() {
    const response = await axios.post(`${API_URL}/api/demo/reset`);
    return response.data;
  },

  async getGraphInsights() {
    const response = await axios.get(`${API_URL}/api/graph/insights`);
    return response.data;
  },

  async getGraphTimeline(limit = 50) {
    const response = await axios.get(`${API_URL}/api/graph/timeline?limit=${limit}`);
    return response.data;
  },
};

