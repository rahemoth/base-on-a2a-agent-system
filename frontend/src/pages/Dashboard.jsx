import React, { useState, useEffect } from 'react';
import { Plus, Users, RefreshCw, GitMerge } from 'lucide-react';
import AgentCard from '../components/AgentCard';
import AgentConfigModal from '../components/AgentConfigModal';
import ChatModal from '../components/ChatModal';
import CollaborationModal from '../components/CollaborationModal';
import { agentService } from '../services/api';
import './Dashboard.css';

const Dashboard = () => {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [chatAgent, setChatAgent] = useState(null);
  const [showCollaborationModal, setShowCollaborationModal] = useState(false);

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      setLoading(true);
      const data = await agentService.listAgents();
      setAgents(data);
    } catch (error) {
      console.error('Error loading agents:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAgent = () => {
    setSelectedAgent(null);
    setShowConfigModal(true);
  };

  const handleConfigureAgent = (agent) => {
    setSelectedAgent(agent);
    setShowConfigModal(true);
  };

  const handleSaveAgent = async (config) => {
    try {
      if (selectedAgent) {
        await agentService.updateAgent(selectedAgent.id, config);
      } else {
        await agentService.createAgent(config);
      }
      setShowConfigModal(false);
      loadAgents();
    } catch (error) {
      console.error('Error saving agent:', error);
      alert('保存 Agent 失败: ' + error.message);
    }
  };

  const handleDeleteAgent = async (agentId) => {
    if (!confirm('您确定要删除这个 Agent 吗？')) return;
    
    try {
      await agentService.deleteAgent(agentId);
      loadAgents();
    } catch (error) {
      console.error('Error deleting agent:', error);
      alert('删除 Agent 失败');
    }
  };

  const handleChatAgent = (agent) => {
    setChatAgent(agent);
  };

  const handleStartCollaboration = async (collaborationConfig) => {
    return await agentService.collaborate(
      collaborationConfig.agents,
      collaborationConfig.task,
      collaborationConfig.coordinator_agent,
      collaborationConfig.max_rounds
    );
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="container">
          <div className="header-content">
            <div>
              <h1>A2A 多智能体系统</h1>
              <p className="subtitle">支持 MCP 的协作 AI Agents</p>
            </div>
            <div className="header-actions">
              <button className="btn btn-secondary" onClick={loadAgents}>
                <RefreshCw size={18} />
                刷新
              </button>
              {agents.length >= 2 && (
                <button 
                  className="btn btn-secondary" 
                  onClick={() => setShowCollaborationModal(true)}
                >
                  <GitMerge size={18} />
                  协作
                </button>
              )}
              <button className="btn btn-primary" onClick={handleCreateAgent}>
                <Plus size={18} />
                创建 Agent
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="dashboard-main">
        <div className="container">
          {loading ? (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>加载 Agents 中...</p>
            </div>
          ) : agents.length === 0 ? (
            <div className="empty-state">
              <Users size={64} />
              <h2>还没有 Agents</h2>
              <p>创建您的第一个 AI Agent 来开始使用</p>
              <button className="btn btn-primary" onClick={handleCreateAgent}>
                <Plus size={18} />
                创建第一个 Agent
              </button>
            </div>
          ) : (
            <div className="agents-grid">
              {agents.map((agent) => (
                <AgentCard
                  key={agent.id}
                  agent={agent}
                  onDelete={handleDeleteAgent}
                  onConfigure={handleConfigureAgent}
                  onChat={handleChatAgent}
                />
              ))}
            </div>
          )}
        </div>
      </main>

      {showConfigModal && (
        <AgentConfigModal
          agent={selectedAgent}
          onClose={() => setShowConfigModal(false)}
          onSave={handleSaveAgent}
        />
      )}

      {chatAgent && (
        <ChatModal
          agent={chatAgent}
          onClose={() => setChatAgent(null)}
        />
      )}

      {showCollaborationModal && (
        <CollaborationModal
          agents={agents}
          onClose={() => setShowCollaborationModal(false)}
          onStartCollaboration={handleStartCollaboration}
        />
      )}
    </div>
  );
};

export default Dashboard;
