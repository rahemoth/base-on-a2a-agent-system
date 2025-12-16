import React, { useState, useEffect, useRef } from 'react';
import { X, Send, Trash2, Download } from 'lucide-react';
import { agentService } from '../services/api';
import { storageService } from '../services/storage';
import './ChatModal.css';

const ChatModal = ({ agent, onClose }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Load chat history from localStorage on mount
  useEffect(() => {
    const history = storageService.getChatHistory(agent.id);
    if (history && history.length > 0) {
      setMessages(history);
    }
  }, [agent.id]);

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
      const response = await agentService.sendMessage(agent.id, input, messages);
      
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
