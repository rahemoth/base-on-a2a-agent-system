import React, { useState } from 'react';
import { X, Play, Users } from 'lucide-react';
import './CollaborationModal.css';

const CollaborationModal = ({ agents, onClose, onStartCollaboration }) => {
  const [selectedAgents, setSelectedAgents] = useState([]);
  const [task, setTask] = useState('');
  const [maxRounds, setMaxRounds] = useState(5);
  const [coordinatorAgent, setCoordinatorAgent] = useState('');
  const [collaborationResult, setCollaborationResult] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState(null);

  const handleAgentToggle = (agentId) => {
    setSelectedAgents(prev => {
      if (prev.includes(agentId)) {
        return prev.filter(id => id !== agentId);
      } else {
        return [...prev, agentId];
      }
    });
  };

  const handleStartCollaboration = async () => {
    // Clear previous errors
    setError(null);
    
    // Validation
    if (selectedAgents.length < 2) {
      setError('请至少选择 2 个 Agent 进行协作');
      return;
    }
    if (!task.trim()) {
      setError('请输入任务描述');
      return;
    }

    setIsRunning(true);
    setCollaborationResult(null);

    try {
      const result = await onStartCollaboration({
        agents: selectedAgents,
        task: task,
        coordinator_agent: coordinatorAgent || null,
        max_rounds: maxRounds
      });
      setCollaborationResult(result);
    } catch (error) {
      setError('启动协作失败: ' + error.message);
    } finally {
      setIsRunning(false);
    }
  };

  const getAgentName = (agentId) => {
    const agent = agents.find(a => a.id === agentId);
    return agent?.config?.name || agentId;
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content collaboration-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="header-title">
            <Users size={24} />
            <h2>多 Agent 协作</h2>
          </div>
          <button className="btn-close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}
          
          {!collaborationResult ? (
            <>
              <div className="form-section">
                <h3>选择 Agents</h3>
                <p className="section-description">
                  选择多个 Agent 来协作完成任务。它们将遵循 A2A 协议共同工作以实现目标。
                </p>
                <div className="agents-selection">
                  {agents.map(agent => (
                    <div
                      key={agent.id}
                      className={`agent-item ${selectedAgents.includes(agent.id) ? 'selected' : ''}`}
                      onClick={() => handleAgentToggle(agent.id)}
                    >
                      <input
                        type="checkbox"
                        checked={selectedAgents.includes(agent.id)}
                        readOnly
                      />
                      <div className="agent-info">
                        <div className="agent-name">{agent.config.name}</div>
                        <div className="agent-model">
                          {agent.config.provider} - {agent.config.model}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                {selectedAgents.length > 0 && (
                  <div className="selected-count">
                    已选择 {selectedAgents.length} 个 Agent
                  </div>
                )}
              </div>

              <div className="form-section">
                <h3>任务配置</h3>
                <div className="form-group">
                  <label>任务描述 *</label>
                  <textarea
                    value={task}
                    onChange={(e) => setTask(e.target.value)}
                    placeholder="描述您希望 Agents 协作完成的任务..."
                    rows={4}
                    disabled={isRunning}
                  />
                  <small className="form-hint">
                    请具体说明您希望 Agents 共同完成什么
                  </small>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>协调员 Agent (可选)</label>
                    <select
                      value={coordinatorAgent}
                      onChange={(e) => setCoordinatorAgent(e.target.value)}
                      disabled={isRunning}
                    >
                      <option value="">自动 (第一个选中的 Agent)</option>
                      {selectedAgents.map(agentId => (
                        <option key={agentId} value={agentId}>
                          {getAgentName(agentId)}
                        </option>
                      ))}
                    </select>
                    <small className="form-hint">
                      协调员负责引导协作过程
                    </small>
                  </div>

                  <div className="form-group">
                    <label>最大轮数</label>
                    <input
                      type="number"
                      value={maxRounds}
                      onChange={(e) => setMaxRounds(parseInt(e.target.value))}
                      min="1"
                      max="20"
                      disabled={isRunning}
                    />
                    <small className="form-hint">
                      协作的轮数
                    </small>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="collaboration-results">
              <div className="results-header">
                <h3>协作结果</h3>
                <button
                  className="btn btn-secondary"
                  onClick={() => setCollaborationResult(null)}
                >
                  开始新协作
                </button>
              </div>
              
              <div className="conversation-history">
                {collaborationResult.collaboration_history?.map((msg, index) => (
                  <div
                    key={`${msg.timestamp}-${index}`}
                    className={`message ${msg.role.toLowerCase()}`}
                  >
                    <div className="message-meta">
                      <span className="message-role">{msg.role === 'system' ? '系统' : 'Agent'}</span>
                      {msg.metadata?.agent_name && (
                        <span className="message-agent">{msg.metadata.agent_name}</span>
                      )}
                      <span className="message-time">
                        {new Date(msg.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="message-content">{msg.content}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {!collaborationResult && (
          <div className="modal-footer">
            <button className="btn btn-secondary" onClick={onClose} disabled={isRunning}>
              取消
            </button>
            <button
              className="btn btn-primary"
              onClick={handleStartCollaboration}
              disabled={isRunning || selectedAgents.length < 2 || !task.trim()}
            >
              {isRunning ? (
                <>
                  <div className="spinner-small"></div>
                  运行中...
                </>
              ) : (
                <>
                  <Play size={18} />
                  开始协作
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default CollaborationModal;
