import React, { useState, useEffect, useRef } from 'react';
import { X, Send, Trash2, Download, Wrench, ChevronDown, ChevronUp } from 'lucide-react';
import { agentService, mcpService, toolsService } from '../services/api';
import { storageService } from '../services/storage';
import './ChatModal.css';

const ChatModal = ({ agent, onClose }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [availableTools, setAvailableTools] = useState(null);
  const [showToolsPanel, setShowToolsPanel] = useState(false);
  const [loadingTools, setLoadingTools] = useState(false);
  const messagesEndRef = useRef(null);

  // Load chat history from localStorage on mount
  useEffect(() => {
    const history = storageService.getChatHistory(agent.id);
    if (history && history.length > 0) {
      setMessages(history);
    }
    
    // Load available tools
    loadAvailableTools();
  }, [agent.id]);

  const loadAvailableTools = async () => {
    setLoadingTools(true);
    try {
      // Try to get tools from both MCP and tool manager
      const [mcpToolsResult, toolsResult] = await Promise.allSettled([
        mcpService.getAgentTools(agent.id),
        toolsService.listTools(agent.id)
      ]);
      
      const tools = {
        mcp: mcpToolsResult.status === 'fulfilled' ? mcpToolsResult.value.tools : {},
        builtin: toolsResult.status === 'fulfilled' ? toolsResult.value.tools : []
      };
      
      setAvailableTools(tools);
    } catch (error) {
      console.error('Error loading tools:', error);
      setAvailableTools({ mcp: {}, builtin: [] });
    } finally {
      setLoadingTools(false);
    }
  };

  // Save chat history to localStorage whenever messages change
  useEffect(() => {
    if (messages.length > 0) {
      storageService.saveChatHistory(agent.id, messages);
    }
  }, [messages, agent.id]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // Include available tools information in context for the first message
      let contextWithTools = [...messages, userMessage];
      
      // If this is the first user message and tools are available, prepend a system message
      if (messages.length === 0 && availableTools) {
        const toolsInfo = getToolsInfoMessage();
        if (toolsInfo) {
          contextWithTools = [
            {
              role: 'system',
              content: toolsInfo,
              timestamp: new Date().toISOString()
            },
            ...contextWithTools
          ];
        }
      }
      
      const response = await agentService.sendMessage(agent.id, input, contextWithTools);
      
      const agentMessage = {
        role: 'agent',
        content: response.response,
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, agentMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        role: 'system',
        content: '错误: 无法从 Agent 获取响应',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const getToolsInfoMessage = () => {
    if (!availableTools) return null;
    
    const mcpTools = availableTools.mcp || {};
    const builtinTools = availableTools.builtin || [];
    
    let toolsMessage = '';
    
    // Add MCP tools info
    const mcpServers = Object.keys(mcpTools);
    if (mcpServers.length > 0) {
      toolsMessage += '你配置了以下 MCP 服务器和工具:\n\n';
      mcpServers.forEach(serverName => {
        const tools = mcpTools[serverName];
        if (tools && tools.length > 0) {
          toolsMessage += `【${serverName}】服务器:\n`;
          tools.forEach(tool => {
            toolsMessage += `  - ${tool.name}: ${tool.description}\n`;
          });
          toolsMessage += '\n';
        }
      });
    }
    
    // Add builtin tools info
    if (builtinTools.length > 0) {
      toolsMessage += '你还有以下内置工具:\n';
      builtinTools.forEach(tool => {
        toolsMessage += `  - ${tool.name}: ${tool.description}\n`;
      });
    }
    
    if (toolsMessage) {
      toolsMessage += '\n请在需要时主动使用这些工具来帮助用户完成任务。';
      return toolsMessage;
    }
    
    return null;
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClearHistory = () => {
    if (confirm('确定要清除此对话的历史记录吗？')) {
      setMessages([]);
      storageService.clearChatHistory(agent.id);
    }
  };

  const handleExportHistory = () => {
    const dataStr = JSON.stringify(messages, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `chat_${agent.config.name}_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="chat-modal" onClick={(e) => e.stopPropagation()}>
        <div className="chat-header">
          <div>
            <h2>与 {agent.config.name} 聊天</h2>
            <p className="chat-subtitle">{agent.config.description}</p>
          </div>
          <div className="chat-header-actions">
            <button 
              className="btn btn-icon" 
              onClick={() => setShowToolsPanel(!showToolsPanel)}
              title={showToolsPanel ? "隐藏工具面板" : "显示可用工具"}
            >
              <Wrench size={18} />
            </button>
            {messages.length > 0 && (
              <>
                <button 
                  className="btn btn-icon" 
                  onClick={handleExportHistory}
                  title="导出对话"
                >
                  <Download size={18} />
                </button>
                <button 
                  className="btn btn-icon" 
                  onClick={handleClearHistory}
                  title="清除历史"
                >
                  <Trash2 size={18} />
                </button>
              </>
            )}
            <button className="btn-close" onClick={onClose}>
              <X size={20} />
            </button>
          </div>
        </div>

        {showToolsPanel && availableTools && (
          <div className="tools-panel">
            <div className="tools-panel-header">
              <h3><Wrench size={16} /> 可用工具</h3>
              <button 
                className="btn-icon-small" 
                onClick={() => setShowToolsPanel(false)}
                title="关闭"
              >
                <ChevronUp size={16} />
              </button>
            </div>
            <div className="tools-panel-content">
              {Object.keys(availableTools.mcp || {}).length === 0 && 
               (!availableTools.builtin || availableTools.builtin.length === 0) ? (
                <p className="no-tools-message">此 Agent 未配置任何 MCP 服务器或工具</p>
              ) : (
                <>
                  {Object.keys(availableTools.mcp || {}).map(serverName => {
                    const tools = availableTools.mcp[serverName];
                    if (!tools || tools.length === 0) return null;
                    return (
                      <div key={serverName} className="tool-server-group">
                        <h4>{serverName} 服务器</h4>
                        <ul className="tool-list">
                          {tools.map((tool, idx) => (
                            <li key={idx} className="tool-item">
                              <strong>{tool.name}</strong>
                              <p>{tool.description}</p>
                            </li>
                          ))}
                        </ul>
                      </div>
                    );
                  })}
                  {availableTools.builtin && availableTools.builtin.length > 0 && (
                    <div className="tool-server-group">
                      <h4>内置工具</h4>
                      <ul className="tool-list">
                        {availableTools.builtin.map((tool, idx) => (
                          <li key={idx} className="tool-item">
                            <strong>{tool.name}</strong>
                            <p>{tool.description}</p>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}

        <div className="chat-messages">
          {messages.length === 0 && (
            <div className="empty-state">
              <p>开始与这个 Agent 对话</p>
            </div>
          )}
          
          {messages.map((msg, index) => (
            <div key={index} className={`message ${msg.role}`}>
              <div className="message-content">
                <div className="message-header">
                  <span className="message-role">{msg.role === 'user' ? '你' : agent.config.name}</span>
                  <span className="message-time">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <div className="message-text">{msg.content}</div>
              </div>
            </div>
          ))}
          
          {loading && (
            <div className="message agent">
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-container">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="输入您的消息..."
            rows={1}
            disabled={loading}
          />
          <button 
            className="btn-send" 
            onClick={handleSend}
            disabled={loading || !input.trim()}
          >
            <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatModal;
