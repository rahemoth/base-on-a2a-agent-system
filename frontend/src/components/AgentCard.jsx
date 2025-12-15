import React from 'react';
import { Bot, Trash2, MessageSquare, Settings, Eye } from 'lucide-react';
import './AgentCard.css';

const AgentCard = ({ agent, onDelete, onConfigure, onChat, onViewInsights }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'idle': return '#10b981';
      case 'busy': return '#f59e0b';
      case 'error': return '#ef4444';
      case 'offline': return '#6b7280';
      default: return '#6b7280';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'idle': return '空闲';
      case 'busy': return '忙碌';
      case 'error': return '错误';
      case 'offline': return '离线';
      default: return status;
    }
  };

  return (
    <div className="agent-card">
      <div className="agent-header">
        <div className="agent-icon">
          <Bot size={24} />
        </div>
        <div className="agent-info">
          <h3>{agent.config.name}</h3>
          <div className="agent-status" style={{ backgroundColor: getStatusColor(agent.status) }}>
            {getStatusText(agent.status)}
          </div>
        </div>
      </div>
      
      <div className="agent-body">
        <p className="agent-description">{agent.config.description || '无描述'}</p>
        <div className="agent-details">
          <div className="detail-item">
            <span className="detail-label">模型:</span>
            <span className="detail-value">{agent.config.model}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">温度:</span>
            <span className="detail-value">{agent.config.temperature}</span>
          </div>
          {agent.config.mcp_servers && agent.config.mcp_servers.length > 0 && (
            <div className="detail-item">
              <span className="detail-label">MCP 服务器:</span>
              <span className="detail-value">{agent.config.mcp_servers.length}</span>
            </div>
          )}
        </div>
      </div>
      
      <div className="agent-actions">
        <button className="btn btn-icon" onClick={() => onChat(agent)} title="聊天">
          <MessageSquare size={18} />
        </button>
        <button className="btn btn-icon" onClick={() => onViewInsights(agent)} title="查看洞察">
          <Eye size={18} />
        </button>
        <button className="btn btn-icon" onClick={() => onConfigure(agent)} title="配置">
          <Settings size={18} />
        </button>
        <button className="btn btn-icon btn-danger" onClick={() => onDelete(agent.id)} title="删除">
          <Trash2 size={18} />
        </button>
      </div>
    </div>
  );
};

export default AgentCard;
