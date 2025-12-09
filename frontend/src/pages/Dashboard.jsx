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
      alert('Failed to save agent: ' + error.message);
    }
  };

  const handleDeleteAgent = async (agentId) => {
    if (!confirm('Are you sure you want to delete this agent?')) return;
    
    try {
      await agentService.deleteAgent(agentId);
      loadAgents();
    } catch (error) {
      console.error('Error deleting agent:', error);
      alert('Failed to delete agent');
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
              <h1>A2A Multi-Agent System</h1>
              <p className="subtitle">Collaborative AI Agents with MCP Support</p>
            </div>
            <div className="header-actions">
              <button className="btn btn-secondary" onClick={loadAgents}>
                <RefreshCw size={18} />
                Refresh
              </button>
              {agents.length >= 2 && (
                <button 
                  className="btn btn-secondary" 
                  onClick={() => setShowCollaborationModal(true)}
                >
                  <GitMerge size={18} />
                  Collaborate
                </button>
              )}
              <button className="btn btn-primary" onClick={handleCreateAgent}>
                <Plus size={18} />
                Create Agent
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
              <p>Loading agents...</p>
            </div>
          ) : agents.length === 0 ? (
            <div className="empty-state">
              <Users size={64} />
              <h2>No Agents Yet</h2>
              <p>Create your first AI agent to get started</p>
              <button className="btn btn-primary" onClick={handleCreateAgent}>
                <Plus size={18} />
                Create First Agent
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
