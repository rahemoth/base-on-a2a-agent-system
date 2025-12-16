import React, { useState, useEffect } from 'react';
import { X, Brain, Database, Wrench, Clock, TrendingUp, BarChart3, Target, MessageSquare, AlertCircle } from 'lucide-react';
import { memoryService, cognitiveService, toolsService } from '../services/api';
import { storageService } from '../services/storage';
import './AgentInsightsModal.css';

const AgentInsightsModal = ({ agent, onClose }) => {
  const [activeTab, setActiveTab] = useState('memory');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Memory state
  const [shortTermMemory, setShortTermMemory] = useState([]);
  const [longTermMemory, setLongTermMemory] = useState([]);
  const [taskHistory, setTaskHistory] = useState([]);
  const [environmentContext, setEnvironmentContext] = useState({});
  
  // Cognitive state
  const [cognitiveState, setCognitiveState] = useState(null);
  const [reasoningChain, setReasoningChain] = useState([]);
  const [currentPlan, setCurrentPlan] = useState(null);
  const [feedbackHistory, setFeedbackHistory] = useState([]);
  
  // Tools state
  const [tools, setTools] = useState([]);
  const [toolReport, setToolReport] = useState(null);

  useEffect(() => {
    loadData();
  }, [activeTab, agent.id]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      if (activeTab === 'memory') {
        const [shortTerm, longTerm, tasks, env] = await Promise.all([
          memoryService.getShortTermMemory(agent.id, 10),
          memoryService.getLongTermMemory(agent.id, null, 10, 0.0),
          memoryService.getTaskHistory(agent.id, 10),
          memoryService.getEnvironmentContext(agent.id),
        ]);
        setShortTermMemory(shortTerm.memory || []);
        setLongTermMemory(longTerm.memories || []);
        setTaskHistory(tasks.tasks || []);
        setEnvironmentContext(env.context || {});
      } else if (activeTab === 'cognitive') {
        const [state, reasoning, plan, feedback] = await Promise.all([
          cognitiveService.getCognitiveState(agent.id),
          cognitiveService.getReasoningChain(agent.id, 5),
          cognitiveService.getCurrentPlan(agent.id),
          cognitiveService.getFeedbackHistory(agent.id, 10),
        ]);
        setCognitiveState(state.cognitive_state || {});
        setReasoningChain(reasoning.reasoning_chain || []);
        setCurrentPlan(plan.current_plan);
        setFeedbackHistory(feedback.feedback_history || []);
      } else if (activeTab === 'tools') {
        const [toolsList, report] = await Promise.all([
          toolsService.listTools(agent.id),
          toolsService.getToolReport(agent.id),
        ]);
        
        // Merge backend tools with custom tools from localStorage
        const backendTools = toolsList.tools || [];
        const customTools = storageService.getCustomTools();
        const allTools = [...backendTools, ...customTools];
        
        setTools(allTools);
        setToolReport(report.report || {});
      }
    } catch (err) {
      console.error('Error loading data:', err);
      setError(err.message || '加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleClearShortTermMemory = async () => {
    if (!confirm('确定要清除短期记忆吗？')) return;
    
    try {
      await memoryService.clearShortTermMemory(agent.id);
      loadData();
    } catch (err) {
      alert('清除失败: ' + err.message);
    }
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A';
    return new Date(timestamp).toLocaleString('zh-CN');
  };

  const renderMemoryTab = () => (
    <div className="insights-content">
      <div className="insights-section">
        <div className="section-header">
          <h3><MessageSquare size={18} /> 短期记忆 ({shortTermMemory.length})</h3>
          <button className="btn btn-sm btn-secondary" onClick={handleClearShortTermMemory}>
            清除
          </button>
        </div>
        <div className="memory-list">
          {shortTermMemory.length === 0 ? (
            <p className="empty-message">暂无短期记忆</p>
          ) : (
            shortTermMemory.map((item, idx) => (
              <div key={idx} className="memory-item">
                <div className="memory-header">
                  <span className={`memory-role ${item.role}`}>{item.role}</span>
                  <span className="memory-time">{formatTimestamp(item.timestamp)}</span>
                </div>
                <div className="memory-content">{item.content}</div>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="insights-section">
        <div className="section-header">
          <h3><Database size={18} /> 长期记忆 ({longTermMemory.length})</h3>
        </div>
        <div className="memory-list">
          {longTermMemory.length === 0 ? (
            <p className="empty-message">暂无长期记忆</p>
          ) : (
            longTermMemory.map((item, idx) => (
              <div key={idx} className="memory-item">
                <div className="memory-header">
                  <span className="memory-type">{item.memory_type}</span>
                  <span className="memory-importance">重要性: {(item.importance * 100).toFixed(0)}%</span>
                  <span className="memory-time">{formatTimestamp(item.timestamp)}</span>
                </div>
                <div className="memory-content">{item.content}</div>
                <div className="memory-meta">访问次数: {item.accessed_count}</div>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="insights-section">
        <div className="section-header">
          <h3><Clock size={18} /> 任务历史 ({taskHistory.length})</h3>
        </div>
        <div className="task-list">
          {taskHistory.length === 0 ? (
            <p className="empty-message">暂无任务历史</p>
          ) : (
            taskHistory.map((task, idx) => (
              <div key={idx} className="task-item">
                <div className="task-header">
                  <span className={`task-status ${task.status}`}>{task.status}</span>
                  <span className="task-time">{formatTimestamp(task.started_at)}</span>
                </div>
                <div className="task-description">{task.task_description}</div>
                {task.result && <div className="task-result">结果: {task.result}</div>}
              </div>
            ))
          )}
        </div>
      </div>

      <div className="insights-section">
        <div className="section-header">
          <h3><TrendingUp size={18} /> 环境上下文</h3>
        </div>
        <div className="context-grid">
          {Object.keys(environmentContext).length === 0 ? (
            <p className="empty-message">暂无环境上下文</p>
          ) : (
            Object.entries(environmentContext).map(([key, value]) => (
              <div key={key} className="context-item">
                <span className="context-key">{key}:</span>
                <span className="context-value">{JSON.stringify(value)}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );

  const renderCognitiveTab = () => (
    <div className="insights-content">
      <div className="insights-section">
        <div className="section-header">
          <h3><Brain size={18} /> 认知状态</h3>
        </div>
        {cognitiveState && (
          <div className="cognitive-state">
            <div className="state-item">
              <strong>推理链长度:</strong> {cognitiveState.reasoning_chain_length || 0}
            </div>
            <div className="state-item">
              <strong>反馈历史:</strong> {cognitiveState.feedback_history_length || 0}
            </div>
            {cognitiveState.perception && (
              <div className="state-item">
                <strong>感知状态:</strong> 
                <pre>{JSON.stringify(cognitiveState.perception, null, 2)}</pre>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="insights-section">
        <div className="section-header">
          <h3><Target size={18} /> 推理链 ({reasoningChain.length})</h3>
        </div>
        <div className="reasoning-list">
          {reasoningChain.length === 0 ? (
            <p className="empty-message">暂无推理记录</p>
          ) : (
            reasoningChain.map((reasoning, idx) => (
              <div key={idx} className="reasoning-item">
                <div className="reasoning-header">
                  <strong>目标:</strong> {reasoning.goal}
                  <span className="reasoning-time">{formatTimestamp(reasoning.timestamp)}</span>
                </div>
                <div className="reasoning-thoughts">
                  {reasoning.thoughts && reasoning.thoughts.map((thought, tidx) => (
                    <div key={tidx} className="thought-item">
                      <span className="thought-step">步骤 {thought.step}:</span>
                      <span className="thought-type">[{thought.type}]</span>
                      <span className="thought-content">{thought.content}</span>
                    </div>
                  ))}
                </div>
                <div className="reasoning-conclusion">
                  <strong>结论:</strong> {reasoning.conclusion}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="insights-section">
        <div className="section-header">
          <h3><BarChart3 size={18} /> 当前执行计划</h3>
        </div>
        {currentPlan ? (
          <div className="current-plan">
            <div className="plan-header">
              <div className="plan-info">
                <strong>任务ID:</strong> {currentPlan.task_id}
              </div>
              <div className="plan-status">
                <span className={`status-badge ${currentPlan.status}`}>{currentPlan.status}</span>
              </div>
            </div>
            <div className="plan-description">{currentPlan.task_description}</div>
            <div className="plan-steps">
              <strong>步骤:</strong>
              {currentPlan.steps && currentPlan.steps.map((step, idx) => (
                <div key={idx} className={`step-item ${idx < currentPlan.current_step ? 'completed' : ''}`}>
                  <span className="step-number">{step.step_number}.</span>
                  <span className="step-action">{step.action}</span>
                  <span className="step-description">{step.description}</span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p className="empty-message">暂无执行计划</p>
        )}
      </div>

      <div className="insights-section">
        <div className="section-header">
          <h3><AlertCircle size={18} /> 反馈历史 ({feedbackHistory.length})</h3>
        </div>
        <div className="feedback-list">
          {feedbackHistory.length === 0 ? (
            <p className="empty-message">暂无反馈记录</p>
          ) : (
            feedbackHistory.map((feedback, idx) => (
              <div key={idx} className="feedback-item">
                <div className="feedback-header">
                  <span className={`feedback-status ${feedback.success ? 'success' : 'failure'}`}>
                    {feedback.success ? '成功' : '失败'}
                  </span>
                  <span className="feedback-time">{formatTimestamp(feedback.timestamp)}</span>
                </div>
                <div className="feedback-result">结果: {feedback.result}</div>
                {feedback.lessons_learned && feedback.lessons_learned.length > 0 && (
                  <div className="feedback-lessons">
                    <strong>经验教训:</strong>
                    <ul>
                      {feedback.lessons_learned.map((lesson, lidx) => (
                        <li key={lidx}>{lesson}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {feedback.adjustments && feedback.adjustments.length > 0 && (
                  <div className="feedback-adjustments">
                    <strong>建议调整:</strong>
                    <ul>
                      {feedback.adjustments.map((adj, aidx) => (
                        <li key={aidx}>{adj}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );

  const renderToolsTab = () => (
    <div className="insights-content">
      <div className="insights-section">
        <div className="section-header">
          <h3><Wrench size={18} /> 可用工具 ({tools.length})</h3>
        </div>
        <div className="tools-grid">
          {tools.length === 0 ? (
            <p className="empty-message">暂无可用工具</p>
          ) : (
            tools.map((tool, idx) => (
              <div key={idx} className="tool-card">
                <div className="tool-header">
                  <strong>{tool.name}</strong>
                  <span className={`tool-badge ${tool.category === 'custom' ? 'custom' : tool.is_builtin ? 'builtin' : 'mcp'}`}>
                    {tool.category === 'custom' ? '自定义' : tool.is_builtin ? '内置' : 'MCP'}
                  </span>
                </div>
                <div className="tool-description">{tool.description}</div>
                <div className="tool-meta">
                  <span className="tool-category">{tool.category}</span>
                  {tool.server_name && <span className="tool-server">{tool.server_name}</span>}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {toolReport && (
        <div className="insights-section">
          <div className="section-header">
            <h3><BarChart3 size={18} /> 工具使用报告</h3>
          </div>
          <div className="tool-report">
            <div className="report-stats">
              <div className="stat-item">
                <div className="stat-value">{toolReport.total_tools || 0}</div>
                <div className="stat-label">总工具数</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">{toolReport.builtin_tools || 0}</div>
                <div className="stat-label">内置工具</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">{toolReport.mcp_tools || 0}</div>
                <div className="stat-label">MCP工具</div>
              </div>
            </div>

            {toolReport.most_used_tools && toolReport.most_used_tools.length > 0 && (
              <div className="most-used-tools">
                <h4>最常用工具</h4>
                <div className="tools-ranking">
                  {toolReport.most_used_tools.map(([name, count], idx) => (
                    <div key={idx} className="ranking-item">
                      <span className="ranking-position">{idx + 1}</span>
                      <span className="ranking-name">{name}</span>
                      <span className="ranking-count">{count} 次</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {toolReport.tool_statistics && Object.keys(toolReport.tool_statistics).length > 0 && (
              <div className="tool-statistics">
                <h4>工具统计</h4>
                {Object.entries(toolReport.tool_statistics).map(([name, stats]) => (
                  <div key={name} className="tool-stat-item">
                    <div className="tool-stat-name">{name}</div>
                    <div className="tool-stat-details">
                      <span>调用: {stats.total_calls || 0}</span>
                      <span>成功: {stats.successful_calls || 0}</span>
                      <span>失败: {stats.failed_calls || 0}</span>
                      <span>平均耗时: {(stats.avg_duration || 0).toFixed(2)}s</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content insights-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{agent.config.name} - 智能体洞察</h2>
          <button className="modal-close" onClick={onClose}>
            <X size={24} />
          </button>
        </div>

        <div className="insights-tabs">
          <button
            className={`tab-button ${activeTab === 'memory' ? 'active' : ''}`}
            onClick={() => setActiveTab('memory')}
          >
            <Database size={18} />
            记忆系统
          </button>
          <button
            className={`tab-button ${activeTab === 'cognitive' ? 'active' : ''}`}
            onClick={() => setActiveTab('cognitive')}
          >
            <Brain size={18} />
            认知状态
          </button>
          <button
            className={`tab-button ${activeTab === 'tools' ? 'active' : ''}`}
            onClick={() => setActiveTab('tools')}
          >
            <Wrench size={18} />
            工具系统
          </button>
        </div>

        <div className="modal-body">
          {loading ? (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>加载中...</p>
            </div>
          ) : error ? (
            <div className="error-state">
              <AlertCircle size={48} />
              <p>{error}</p>
              <button className="btn btn-primary" onClick={loadData}>重试</button>
            </div>
          ) : (
            <>
              {activeTab === 'memory' && renderMemoryTab()}
              {activeTab === 'cognitive' && renderCognitiveTab()}
              {activeTab === 'tools' && renderToolsTab()}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default AgentInsightsModal;
