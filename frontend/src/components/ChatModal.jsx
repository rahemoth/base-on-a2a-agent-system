import React, { useState, useEffect, useRef } from 'react';
import { X, Send } from 'lucide-react';
import { agentService } from '../services/api';
import './ChatModal.css';

const ChatModal = ({ agent, onClose }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

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

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="chat-modal" onClick={(e) => e.stopPropagation()}>
        <div className="chat-header">
          <div>
            <h2>与 {agent.config.name} 聊天</h2>
            <p className="chat-subtitle">{agent.config.description}</p>
          </div>
          <button className="btn-close" onClick={onClose}>
            <X size={20} />
          </button>
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
