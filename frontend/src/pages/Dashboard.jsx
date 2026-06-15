import React, { useState, useEffect } from 'react';
import { Plus, Users, RefreshCw, GitMerge, Wrench, Bot, MessageSquare, Eye, Settings, Trash2 } from 'lucide-react';
import AgentConfigModal from '../components/AgentConfigModal';
import ChatModal from '../components/ChatModal';
import CollaborationModal from '../components/CollaborationModal';
import AgentInsightsModal from '../components/AgentInsightsModal';
import CustomToolModal from '../components/CustomToolModal';
import { agentService } from '../services/api';
import { storageService } from '../services/storage';

const statusMap = {
  idle: { variant: 'success', text: '空闲' },
  busy: { variant: 'warning', text: '忙碌' },
  error: { variant: 'error', text: '错误' },
  offline: { variant: 'default', text: '离线' },
};

const Dashboard = () => {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [chatAgent, setChatAgent] = useState(null);
  const [showCollaborationModal, setShowCollaborationModal] = useState(false);
  const [insightsAgent, setInsightsAgent] = useState(null);
  const [showCustomToolModal, setShowCustomToolModal] = useState(false);

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

  const handleViewInsights = (agent) => {
    setInsightsAgent(agent);
  };

  const handleStartCollaboration = async (collaborationConfig) => {
    return await agentService.collaborate(
      collaborationConfig.agents,
      collaborationConfig.task,
      collaborationConfig.coordinator_agent,
      collaborationConfig.max_rounds
    );
  };

  const handleSaveCustomTool = (toolConfig) => {
    try {
      storageService.saveCustomTool(toolConfig);
      setShowCustomToolModal(false);
      alert('自定义工具已保存！');
    } catch (error) {
      console.error('Error saving custom tool:', error);
      alert('保存失败: ' + error.message);
    }
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#0a0a0f' }}>
      {/* Header */}
      <header style={{ 
        position: 'sticky', 
        top: 0, 
        zIndex: 40,
        background: 'rgba(255, 255, 255, 0.05)',
        backdropFilter: 'blur(10px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
      }}>
        <div style={{
          maxWidth: '1280px',
          margin: '0 auto',
          padding: '1.5rem 1rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '2rem'
        }}>
          <div>
            <h1 style={{ 
              fontSize: '1.875rem', 
              fontWeight: 'bold',
              color: '#a78bfa',
              margin: 0,
              marginBottom: '0.25rem'
            }}>
              智能体协作系统
            </h1>
            <p style={{ 
              fontSize: '0.875rem', 
              color: '#9ca3af',
              margin: 0
            }}>
              支持 MCP 的协作 AI Agents
            </p>
          </div>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button 
              onClick={loadAgents}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.5rem 1rem',
                fontSize: '0.75rem',
                fontWeight: 600,
                color: '#9ca3af',
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '0.5rem',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                e.target.style.color = '#ffffff';
              }}
              onMouseLeave={(e) => {
                e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
                e.target.style.color = '#9ca3af';
              }}
            >
              <RefreshCw size={16} />
              刷新
            </button>
            <button 
              onClick={() => setShowCustomToolModal(true)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.5rem 1rem',
                fontSize: '0.75rem',
                fontWeight: 600,
                color: '#9ca3af',
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '0.5rem',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                e.target.style.color = '#ffffff';
              }}
              onMouseLeave={(e) => {
                e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
                e.target.style.color = '#9ca3af';
              }}
            >
              <Wrench size={16} />
              自定义工具
            </button>
            {agents.length >= 2 && (
              <button 
                onClick={() => setShowCollaborationModal(true)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.5rem 1rem',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  color: '#9ca3af',
                  backgroundColor: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '0.5rem',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
                onMouseEnter={(e) => {
                  e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                  e.target.style.color = '#ffffff';
                }}
                onMouseLeave={(e) => {
                  e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
                  e.target.style.color = '#9ca3af';
                }}
              >
                <GitMerge size={16} />
                协作
              </button>
            )}
            <button 
              onClick={handleCreateAgent}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.75rem 1.5rem',
                fontSize: '0.875rem',
                fontWeight: 600,
                color: '#ffffff',
                background: 'linear-gradient(135deg, #7c3aed, #8b5cf6)',
                border: 'none',
                borderRadius: '0.5rem',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                boxShadow: '0 4px 15px rgba(139, 92, 246, 0.3)'
              }}
              onMouseEnter={(e) => {
                e.target.style.boxShadow = '0 8px 25px rgba(139, 92, 246, 0.4)';
                e.target.style.transform = 'translateY(-2px)';
              }}
              onMouseLeave={(e) => {
                e.target.style.boxShadow = '0 4px 15px rgba(139, 92, 246, 0.3)';
                e.target.style.transform = 'translateY(0)';
              }}
            >
              <Plus size={18} />
              创建 Agent
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main style={{ padding: '4rem 1rem 3rem' }}>
        <div style={{ maxWidth: '1280px', margin: '0 auto' }}>
          {loading ? (
            <div style={{ 
              display: 'flex', 
              flexDirection: 'column', 
              alignItems: 'center', 
              justifyContent: 'center',
              padding: '8rem 2rem',
              color: '#9ca3af'
            }}>
              <div style={{
                width: '48px',
                height: '48px',
                border: '3px solid rgba(255, 255, 255, 0.1)',
                borderTopColor: '#8b5cf6',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite',
                marginBottom: '1rem'
              }} />
              <p>加载 Agents 中...</p>
            </div>
          ) : agents.length === 0 ? (
            <div style={{ 
              display: 'flex', 
              flexDirection: 'column', 
              alignItems: 'center', 
              justifyContent: 'center',
              padding: '6rem 2rem',
              textAlign: 'center',
              backgroundColor: '#111118',
              borderRadius: '1.5rem',
              border: '2px dashed rgba(255, 255, 255, 0.1)'
            }}>
              <div style={{ 
                color: '#8b5cf6', 
                marginBottom: '1.5rem',
                opacity: 0.5,
                animation: 'pulse 2s ease-in-out infinite'
              }}>
                <Users size={64} />
              </div>
              <h2 style={{ 
                fontSize: '1.5rem', 
                fontWeight: 600, 
                color: '#ffffff',
                margin: '0 0 0.5rem'
              }}>
                还没有 Agents
              </h2>
              <p style={{ 
                fontSize: '1rem', 
                color: '#9ca3af',
                margin: '0 0 2rem',
                maxWidth: '400px'
              }}>
                创建您的第一个 AI Agent 来开始使用
              </p>
              <button 
                onClick={handleCreateAgent}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '1rem 2rem',
                  fontSize: '1rem',
                  fontWeight: 600,
                  color: '#ffffff',
                  background: 'linear-gradient(135deg, #7c3aed, #8b5cf6)',
                  border: 'none',
                  borderRadius: '0.5rem',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  boxShadow: '0 4px 15px rgba(139, 92, 246, 0.3)'
                }}
              >
                <Plus size={18} />
                创建第一个 Agent
              </button>
            </div>
          ) : (
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', 
              gap: '1.5rem' 
            }}>
              {agents.map((agent, index) => {
                const status = statusMap[agent.status] || statusMap.offline;
                const statusColor = {
                  success: { bg: 'rgba(16, 185, 129, 0.2)', color: '#10b981', border: 'rgba(16, 185, 129, 0.3)' },
                  warning: { bg: 'rgba(245, 158, 11, 0.2)', color: '#f59e0b', border: 'rgba(245, 158, 11, 0.3)' },
                  error: { bg: 'rgba(239, 68, 68, 0.2)', color: '#ef4444', border: 'rgba(239, 68, 68, 0.3)' },
                  default: { bg: 'rgba(255, 255, 255, 0.1)', color: '#9ca3af', border: 'rgba(255, 255, 255, 0.1)' }
                }[status.variant];
                
                return (
                  <div 
                    key={agent.id} 
                    style={{
                      backgroundColor: '#111118',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      borderRadius: '1rem',
                      padding: '1.5rem',
                      transition: 'all 0.3s ease',
                      animation: `fadeIn 0.5s ease-out ${index * 0.1}s both`
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.3)';
                      e.currentTarget.style.boxShadow = '0 0 30px rgba(139, 92, 246, 0.15)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.1)';
                      e.currentTarget.style.boxShadow = 'none';
                    }}
                  >
                    {/* Card Header */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
                      <div style={{ 
                        width: '48px', 
                        height: '48px', 
                        borderRadius: '12px', 
                        backgroundColor: 'rgba(139, 92, 246, 0.1)',
                        border: '1px solid rgba(139, 92, 246, 0.2)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}>
                        <Bot size={24} style={{ color: '#a78bfa' }} />
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <h3 style={{ 
                          fontSize: '1.125rem', 
                          fontWeight: 'bold', 
                          color: '#ffffff',
                          margin: 0,
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis'
                        }}>
                          {agent.config.name}
                        </h3>
                      </div>
                      <span style={{
                        backgroundColor: statusColor.bg,
                        color: statusColor.color,
                        border: `1px solid ${statusColor.border}`,
                        borderRadius: '9999px',
                        padding: '4px 12px',
                        fontSize: '12px',
                        fontWeight: 500
                      }}>
                        {status.text}
                      </span>
                    </div>

                    {/* Description */}
                    <p style={{ 
                      color: '#9ca3af', 
                      fontSize: '0.875rem',
                      margin: '0 0 1rem',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden'
                    }}>
                      {agent.config.description || '无描述'}
                    </p>

                    {/* Tags */}
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1rem' }}>
                      <span style={{
                        backgroundColor: 'rgba(255, 255, 255, 0.05)',
                        color: '#9ca3af',
                        border: '1px solid rgba(255, 255, 255, 0.05)',
                        borderRadius: '8px',
                        padding: '6px 12px',
                        fontSize: '12px'
                      }}>
                        模型: {agent.config.model}
                      </span>
                      <span style={{
                        backgroundColor: 'rgba(255, 255, 255, 0.05)',
                        color: '#9ca3af',
                        border: '1px solid rgba(255, 255, 255, 0.05)',
                        borderRadius: '8px',
                        padding: '6px 12px',
                        fontSize: '12px'
                      }}>
                        温度: {agent.config.temperature}
                      </span>
                      {agent.config.mcp_servers?.length > 0 && (
                        <span style={{
                          backgroundColor: 'rgba(139, 92, 246, 0.2)',
                          color: '#a78bfa',
                          border: '1px solid rgba(139, 92, 246, 0.3)',
                          borderRadius: '8px',
                          padding: '6px 12px',
                          fontSize: '12px'
                        }}>
                          MCP: {agent.config.mcp_servers.length}
                        </span>
                      )}
                    </div>

                    {/* Actions */}
                    <div style={{ 
                      display: 'flex', 
                      gap: '0.5rem', 
                      paddingTop: '1rem',
                      borderTop: '1px solid rgba(255, 255, 255, 0.1)'
                    }}>
                      <button 
                        onClick={() => handleChatAgent(agent)}
                        style={{
                          flex: 1,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '0.5rem',
                          padding: '0.5rem 1rem',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          color: '#9ca3af',
                          backgroundColor: 'transparent',
                          border: 'none',
                          borderRadius: '0.5rem',
                          cursor: 'pointer',
                          transition: 'all 0.2s ease'
                        }}
                        onMouseEnter={(e) => {
                          e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                          e.target.style.color = '#ffffff';
                        }}
                        onMouseLeave={(e) => {
                          e.target.style.backgroundColor = 'transparent';
                          e.target.style.color = '#9ca3af';
                        }}
                      >
                        <MessageSquare size={14} />
                        聊天
                      </button>
                      <button 
                        onClick={() => handleViewInsights(agent)}
                        style={{
                          flex: 1,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '0.5rem',
                          padding: '0.5rem 1rem',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          color: '#9ca3af',
                          backgroundColor: 'transparent',
                          border: 'none',
                          borderRadius: '0.5rem',
                          cursor: 'pointer',
                          transition: 'all 0.2s ease'
                        }}
                        onMouseEnter={(e) => {
                          e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                          e.target.style.color = '#ffffff';
                        }}
                        onMouseLeave={(e) => {
                          e.target.style.backgroundColor = 'transparent';
                          e.target.style.color = '#9ca3af';
                        }}
                      >
                        <Eye size={14} />
                        洞察
                      </button>
                      <button 
                        onClick={() => handleConfigureAgent(agent)}
                        style={{
                          flex: 1,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '0.5rem',
                          padding: '0.5rem 1rem',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          color: '#9ca3af',
                          backgroundColor: 'transparent',
                          border: 'none',
                          borderRadius: '0.5rem',
                          cursor: 'pointer',
                          transition: 'all 0.2s ease'
                        }}
                        onMouseEnter={(e) => {
                          e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                          e.target.style.color = '#ffffff';
                        }}
                        onMouseLeave={(e) => {
                          e.target.style.backgroundColor = 'transparent';
                          e.target.style.color = '#9ca3af';
                        }}
                      >
                        <Settings size={14} />
                        配置
                      </button>
                      <button 
                        onClick={() => handleDeleteAgent(agent.id)}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          padding: '0.5rem 1rem',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          color: '#ef4444',
                          backgroundColor: 'transparent',
                          border: 'none',
                          borderRadius: '0.5rem',
                          cursor: 'pointer',
                          transition: 'all 0.2s ease'
                        }}
                        onMouseEnter={(e) => {
                          e.target.style.backgroundColor = 'rgba(239, 68, 68, 0.2)';
                        }}
                        onMouseLeave={(e) => {
                          e.target.style.backgroundColor = 'transparent';
                        }}
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </main>

      {/* Modals */}
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

      {insightsAgent && (
        <AgentInsightsModal
          agent={insightsAgent}
          onClose={() => setInsightsAgent(null)}
        />
      )}

      {showCustomToolModal && (
        <CustomToolModal
          onClose={() => setShowCustomToolModal(false)}
          onSave={handleSaveCustomTool}
        />
      )}

      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 0.3; }
          50% { opacity: 0.7; }
        }
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
};

export default Dashboard;