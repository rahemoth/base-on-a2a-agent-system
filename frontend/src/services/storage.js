// localStorage utility for managing agent data persistence
const STORAGE_KEYS = {
  CHAT_HISTORY: 'a2a_chat_history',
  AGENT_SETTINGS: 'a2a_agent_settings',
};

export const storageService = {
  // Chat History Management
  getChatHistory(agentId) {
    try {
      const allHistory = JSON.parse(localStorage.getItem(STORAGE_KEYS.CHAT_HISTORY) || '{}');
      return allHistory[agentId] || [];
    } catch (error) {
      console.error('Error loading chat history:', error);
      return [];
    }
  },

  saveChatHistory(agentId, messages) {
    try {
      const allHistory = JSON.parse(localStorage.getItem(STORAGE_KEYS.CHAT_HISTORY) || '{}');
      allHistory[agentId] = messages;
      localStorage.setItem(STORAGE_KEYS.CHAT_HISTORY, JSON.stringify(allHistory));
    } catch (error) {
      console.error('Error saving chat history:', error);
    }
  },

  clearChatHistory(agentId) {
    try {
      const allHistory = JSON.parse(localStorage.getItem(STORAGE_KEYS.CHAT_HISTORY) || '{}');
      delete allHistory[agentId];
      localStorage.setItem(STORAGE_KEYS.CHAT_HISTORY, JSON.stringify(allHistory));
    } catch (error) {
      console.error('Error clearing chat history:', error);
    }
  },

  clearAllChatHistory() {
    try {
      localStorage.removeItem(STORAGE_KEYS.CHAT_HISTORY);
    } catch (error) {
      console.error('Error clearing all chat history:', error);
    }
  },

  // Agent Settings Management
  getAgentSettings(agentId) {
    try {
      const allSettings = JSON.parse(localStorage.getItem(STORAGE_KEYS.AGENT_SETTINGS) || '{}');
      return allSettings[agentId] || null;
    } catch (error) {
      console.error('Error loading agent settings:', error);
      return null;
    }
  },

  saveAgentSettings(agentId, settings) {
    try {
      const allSettings = JSON.parse(localStorage.getItem(STORAGE_KEYS.AGENT_SETTINGS) || '{}');
      allSettings[agentId] = {
        ...settings,
        lastModified: new Date().toISOString(),
      };
      localStorage.setItem(STORAGE_KEYS.AGENT_SETTINGS, JSON.stringify(allSettings));
    } catch (error) {
      console.error('Error saving agent settings:', error);
    }
  },

  getAllAgentSettings() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEYS.AGENT_SETTINGS) || '{}');
    } catch (error) {
      console.error('Error loading all agent settings:', error);
      return {};
    }
  },

  clearAgentSettings(agentId) {
    try {
      const allSettings = JSON.parse(localStorage.getItem(STORAGE_KEYS.AGENT_SETTINGS) || '{}');
      delete allSettings[agentId];
      localStorage.setItem(STORAGE_KEYS.AGENT_SETTINGS, JSON.stringify(allSettings));
    } catch (error) {
      console.error('Error clearing agent settings:', error);
    }
  },

  // Export/Import functionality
  exportData() {
    try {
      return {
        chatHistory: JSON.parse(localStorage.getItem(STORAGE_KEYS.CHAT_HISTORY) || '{}'),
        agentSettings: JSON.parse(localStorage.getItem(STORAGE_KEYS.AGENT_SETTINGS) || '{}'),
        exportDate: new Date().toISOString(),
      };
    } catch (error) {
      console.error('Error exporting data:', error);
      return null;
    }
  },

  importData(data) {
    try {
      if (data.chatHistory) {
        localStorage.setItem(STORAGE_KEYS.CHAT_HISTORY, JSON.stringify(data.chatHistory));
      }
      if (data.agentSettings) {
        localStorage.setItem(STORAGE_KEYS.AGENT_SETTINGS, JSON.stringify(data.agentSettings));
      }
      return true;
    } catch (error) {
      console.error('Error importing data:', error);
      return false;
    }
  },
};

export default storageService;
