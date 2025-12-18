import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ChatResponse {
  response: string;
  timestamp: string;
  agent_version: string;
}

export const apiClient = {
  async sendChatMessage(message: string): Promise<ChatResponse> {
    const response = await axios.post(`${API_URL}/api/chat/send`, { message });
    return response.data;
  },

  async health() {
    return axios.get(`${API_URL}/health`);
  },

  async healthDeps() {
    return axios.get(`${API_URL}/health/deps`);
  },

  async executeTask(task: {
    type: string;
    data: any;
    should_fail_first: boolean;
  }) {
    return axios.post(`${API_URL}/api/tasks/execute`, task);
  },

  async getAgentStatus() {
    return axios.get(`${API_URL}/api/agent/status`);
  },

  async getAgentHistory() {
    return axios.get(`${API_URL}/api/agent/history`);
  },

  async runDemoScenario() {
    return axios.post(`${API_URL}/api/demo/run-scenario`);
  },

  async resetDemo() {
    return axios.post(`${API_URL}/api/demo/reset`);
  },

  async getGraphInsights() {
    return axios.get(`${API_URL}/api/graph/insights`);
  },

  async getGraphTimeline(limit = 50) {
    return axios.get(`${API_URL}/api/graph/timeline?limit=${limit}`);
  },
};
