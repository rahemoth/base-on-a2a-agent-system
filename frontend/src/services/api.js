// API Service for communicating with the backend
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const agentService = {
  // Agent CRUD operations
  async createAgent(config) {
    const response = await api.post('/api/agents/', { config });
    return response.data;
  },

  async listAgents() {
    const response = await api.get('/api/agents/');
    return response.data;
  },

  async getAgent(agentId) {
    const response = await api.get(`/api/agents/${agentId}`);
    return response.data;
  },

  async updateAgent(agentId, config) {
    const response = await api.put(`/api/agents/${agentId}`, { config });
    return response.data;
  },

  async deleteAgent(agentId) {
    const response = await api.delete(`/api/agents/${agentId}`);
    return response.data;
  },

  // Agent communication
  async sendMessage(agentId, message, context = null, stream = false) {
    const response = await api.post('/api/agents/message', {
      agent_id: agentId,
      message,
      context,
      stream,
    });
    return response.data;
  },

  // Agent collaboration
  async collaborate(agents, task, coordinatorAgent = null, maxRounds = 5) {
    const response = await api.post('/api/agents/collaborate', {
      agents,
      task,
      coordinator_agent: coordinatorAgent,
      max_rounds: maxRounds,
    });
    return response.data;
  },
};

export const mcpService = {
  async getAgentTools(agentId) {
    const response = await api.get(`/api/mcp/agents/${agentId}/tools`);
    return response.data;
  },

  async getAgentResources(agentId) {
    const response = await api.get(`/api/mcp/agents/${agentId}/resources`);
    return response.data;
  },

  async callTool(agentId, serverName, toolName, arguments_) {
    const response = await api.post(
      `/api/mcp/agents/${agentId}/tools/${serverName}/${toolName}`,
      arguments_
    );
    return response.data;
  },
};

export default api;
