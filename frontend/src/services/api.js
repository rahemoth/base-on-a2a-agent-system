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

  // Test model connection
  async testConnection(config) {
    const response = await api.post('/api/agents/test-connection', config);
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

// Agent Memory API
export const memoryService = {
  async getShortTermMemory(agentId, limit = null) {
    const params = limit ? { limit } : {};
    const response = await api.get(`/api/agents/${agentId}/memory/short-term`, { params });
    return response.data;
  },

  async getLongTermMemory(agentId, memoryType = null, limit = 10, minImportance = 0.0) {
    const params = { limit, min_importance: minImportance };
    if (memoryType) params.memory_type = memoryType;
    const response = await api.get(`/api/agents/${agentId}/memory/long-term`, { params });
    return response.data;
  },

  async getTaskHistory(agentId, limit = 10, status = null) {
    const params = { limit };
    if (status) params.status = status;
    const response = await api.get(`/api/agents/${agentId}/memory/tasks`, { params });
    return response.data;
  },

  async getEnvironmentContext(agentId) {
    const response = await api.get(`/api/agents/${agentId}/memory/environment`);
    return response.data;
  },

  async clearShortTermMemory(agentId) {
    const response = await api.delete(`/api/agents/${agentId}/memory/short-term`);
    return response.data;
  },
};

// RAG Memory System API
export const ragService = {
  async getStats(agentId) {
    const response = await api.get(`/api/rag/stats/${agentId}`);
    return response.data;
  },

  async queryMemory(agentId, query, k = 10, useGraphReasoning = false) {
    const response = await api.post('/api/rag/query', null, {
      params: {
        agent_id: agentId,
        query,
        k,
        use_graph_reasoning: useGraphReasoning,
      },
    });
    return response.data;
  },

  async addDialogue(agentId, dialogue) {
    const response = await api.post('/api/rag/add', dialogue, {
      params: { agent_id: agentId },
    });
    return response.data;
  },

  async getEntityRelations(agentId, entityName) {
    const response = await api.post(`/api/rag/entities/${agentId}`, null, {
      params: { entity_name: entityName },
    });
    return response.data;
  },

  async clearMemory(agentId) {
    const response = await api.delete(`/api/rag/clear/${agentId}`);
    return response.data;
  },

  async getConfig() {
    const response = await api.get('/api/rag/config');
    return response.data;
  },

  async updateConfig(config) {
    const response = await api.post('/api/rag/config', config);
    return response.data;
  },
};

// Agent Cognitive API
export const cognitiveService = {
  async getCognitiveState(agentId) {
    const response = await api.get(`/api/agents/${agentId}/cognitive/state`);
    return response.data;
  },

  async getReasoningChain(agentId, limit = 5) {
    const response = await api.get(`/api/agents/${agentId}/cognitive/reasoning-chain`, {
      params: { limit }
    });
    return response.data;
  },

  async getCurrentPlan(agentId) {
    const response = await api.get(`/api/agents/${agentId}/cognitive/current-plan`);
    return response.data;
  },

  async getFeedbackHistory(agentId, limit = 10) {
    const response = await api.get(`/api/agents/${agentId}/cognitive/feedback-history`, {
      params: { limit }
    });
    return response.data;
  },
};

// Agent Tools API
export const toolsService = {
  async listTools(agentId, query = null, category = null) {
    const params = {};
    if (query) params.query = query;
    if (category) params.category = category;
    const response = await api.get(`/api/agents/${agentId}/tools`, { params });
    return response.data;
  },

  async getToolCategories(agentId) {
    const response = await api.get(`/api/agents/${agentId}/tools/categories`);
    return response.data;
  },

  async getToolStatistics(agentId, toolName = null) {
    const params = toolName ? { tool_name: toolName } : {};
    const response = await api.get(`/api/agents/${agentId}/tools/statistics`, { params });
    return response.data;
  },

  async getToolExecutionHistory(agentId, toolName = null, limit = 10) {
    const params = { limit };
    if (toolName) params.tool_name = toolName;
    const response = await api.get(`/api/agents/${agentId}/tools/execution-history`, { params });
    return response.data;
  },

  async getToolReport(agentId) {
    const response = await api.get(`/api/agents/${agentId}/tools/report`);
    return response.data;
  },
};

export default api;
