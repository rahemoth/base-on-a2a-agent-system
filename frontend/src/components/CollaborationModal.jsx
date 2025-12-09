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
      setError('Please select at least 2 agents for collaboration');
      return;
    }
    if (!task.trim()) {
      setError('Please enter a task description');
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
      setError('Failed to start collaboration: ' + error.message);
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
            <h2>Multi-Agent Collaboration</h2>
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
                <h3>Select Agents</h3>
                <p className="section-description">
                  Choose multiple agents to collaborate on a task. They will work together 
                  following the A2A protocol to achieve the goal.
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
                    {selectedAgents.length} agent{selectedAgents.length !== 1 ? 's' : ''} selected
                  </div>
                )}
              </div>

              <div className="form-section">
                <h3>Task Configuration</h3>
                <div className="form-group">
                  <label>Task Description *</label>
                  <textarea
                    value={task}
                    onChange={(e) => setTask(e.target.value)}
                    placeholder="Describe the task you want the agents to collaborate on..."
                    rows={4}
                    disabled={isRunning}
                  />
                  <small className="form-hint">
                    Be specific about what you want the agents to accomplish together
                  </small>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Coordinator Agent (Optional)</label>
                    <select
                      value={coordinatorAgent}
                      onChange={(e) => setCoordinatorAgent(e.target.value)}
                      disabled={isRunning}
                    >
                      <option value="">Auto (first selected agent)</option>
                      {selectedAgents.map(agentId => (
                        <option key={agentId} value={agentId}>
                          {getAgentName(agentId)}
                        </option>
                      ))}
                    </select>
                    <small className="form-hint">
                      The coordinator leads the collaboration
                    </small>
                  </div>

                  <div className="form-group">
                    <label>Max Rounds</label>
                    <input
                      type="number"
                      value={maxRounds}
                      onChange={(e) => setMaxRounds(parseInt(e.target.value))}
                      min="1"
                      max="20"
                      disabled={isRunning}
                    />
                    <small className="form-hint">
                      Number of collaboration rounds
                    </small>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="collaboration-results">
              <div className="results-header">
                <h3>Collaboration Results</h3>
                <button
                  className="btn btn-secondary"
                  onClick={() => setCollaborationResult(null)}
                >
                  Start New Collaboration
                </button>
              </div>
              
              <div className="conversation-history">
                {collaborationResult.collaboration_history?.map((msg, index) => (
                  <div
                    key={`${msg.timestamp}-${index}`}
                    className={`message ${msg.role.toLowerCase()}`}
                  >
                    <div className="message-meta">
                      <span className="message-role">{msg.role}</span>
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
              Cancel
            </button>
            <button
              className="btn btn-primary"
              onClick={handleStartCollaboration}
              disabled={isRunning || selectedAgents.length < 2 || !task.trim()}
            >
              {isRunning ? (
                <>
                  <div className="spinner-small"></div>
                  Running...
                </>
              ) : (
                <>
                  <Play size={18} />
                  Start Collaboration
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
