import React, { useState } from 'react';
import { X, Plus, Trash2, Save, Code } from 'lucide-react';
import './CustomToolModal.css';

const CustomToolModal = ({ onClose, onSave }) => {
  const [toolConfig, setToolConfig] = useState({
    name: '',
    description: '',
    category: 'custom',
    parameters: [],
    implementation: ''
  });

  const [newParam, setNewParam] = useState({
    name: '',
    type: 'string',
    description: '',
    required: true
  });

  const paramTypes = ['string', 'number', 'boolean', 'array', 'object'];

  const handleAddParameter = () => {
    if (newParam.name.trim()) {
      setToolConfig({
        ...toolConfig,
        parameters: [...toolConfig.parameters, { ...newParam }]
      });
      setNewParam({
        name: '',
        type: 'string',
        description: '',
        required: true
      });
    }
  };

  const handleRemoveParameter = (index) => {
    setToolConfig({
      ...toolConfig,
      parameters: toolConfig.parameters.filter((_, i) => i !== index)
    });
  };

  const [errors, setErrors] = useState({});

  const validateForm = () => {
    const newErrors = {};
    
    if (!toolConfig.name.trim()) {
      newErrors.name = '请输入工具名称';
    }
    if (!toolConfig.description.trim()) {
      newErrors.description = '请输入工具描述';
    }
    if (!toolConfig.implementation.trim()) {
      newErrors.implementation = '请输入工具实现代码';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = () => {
    if (!validateForm()) {
      return;
    }

    onSave(toolConfig);
  };

  const templateCode = `# 工具实现示例
def execute(${toolConfig.parameters.map(p => p.name).join(', ')}):
    """
    ${toolConfig.description}
    
    参数:
    ${toolConfig.parameters.map(p => `${p.name} (${p.type}): ${p.description}`).join('\n    ')}
    
    返回:
    dict: 包含结果的字典
    """
    # 在此实现您的工具逻辑
    result = {
        "success": True,
        "data": None,
        "message": "工具执行成功"
    }
    
    return result
`;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content custom-tool-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="header-title">
            <Code size={24} />
            <h2>创建自定义工具</h2>
          </div>
          <button className="btn-close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          <div className="form-section">
            <h3>基本信息</h3>
            
            <div className="form-group">
              <label>工具名称 *</label>
              <input
                type="text"
                value={toolConfig.name}
                onChange={(e) => setToolConfig({ ...toolConfig, name: e.target.value })}
                placeholder="例如: calculate_sum"
                className={errors.name ? 'error' : ''}
              />
              {errors.name && <span className="error-message">{errors.name}</span>}
              <small className="form-hint">
                使用小写字母和下划线，如 my_custom_tool
              </small>
            </div>

            <div className="form-group">
              <label>工具描述 *</label>
              <textarea
                value={toolConfig.description}
                onChange={(e) => setToolConfig({ ...toolConfig, description: e.target.value })}
                placeholder="描述这个工具的功能..."
                rows={2}
                className={errors.description ? 'error' : ''}
              />
              {errors.description && <span className="error-message">{errors.description}</span>}
            </div>

            <div className="form-group">
              <label>类别</label>
              <select
                value={toolConfig.category}
                onChange={(e) => setToolConfig({ ...toolConfig, category: e.target.value })}
              >
                <option value="custom">自定义</option>
                <option value="text_processing">文本处理</option>
                <option value="data_analysis">数据分析</option>
                <option value="file_operations">文件操作</option>
                <option value="network">网络请求</option>
                <option value="utility">实用工具</option>
              </select>
            </div>
          </div>

          <div className="form-section">
            <h3>参数定义</h3>
            
            <div className="parameters-list">
              {toolConfig.parameters.map((param, index) => (
                <div key={index} className="parameter-item">
                  <div className="parameter-info">
                    <span className="parameter-name">{param.name}</span>
                    <span className="parameter-type">{param.type}</span>
                    {param.required && <span className="parameter-required">必需</span>}
                    <span className="parameter-description">{param.description}</span>
                  </div>
                  <button
                    className="btn btn-icon btn-danger"
                    onClick={() => handleRemoveParameter(index)}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>

            <div className="add-parameter-form">
              <div className="form-row">
                <div className="form-group">
                  <input
                    type="text"
                    value={newParam.name}
                    onChange={(e) => setNewParam({ ...newParam, name: e.target.value })}
                    placeholder="参数名称"
                  />
                </div>

                <div className="form-group">
                  <select
                    value={newParam.type}
                    onChange={(e) => setNewParam({ ...newParam, type: e.target.value })}
                  >
                    {paramTypes.map(type => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={newParam.required}
                      onChange={(e) => setNewParam({ ...newParam, required: e.target.checked })}
                    />
                    必需
                  </label>
                </div>
              </div>

              <div className="form-group">
                <input
                  type="text"
                  value={newParam.description}
                  onChange={(e) => setNewParam({ ...newParam, description: e.target.value })}
                  placeholder="参数描述"
                />
              </div>

              <button className="btn btn-secondary" onClick={handleAddParameter}>
                <Plus size={18} />
                添加参数
              </button>
            </div>
          </div>

          <div className="form-section">
            <h3>工具实现</h3>
            
            <div className="code-template">
              <button
                className="btn btn-sm btn-secondary"
                onClick={() => setToolConfig({ ...toolConfig, implementation: templateCode })}
              >
                使用模板
              </button>
            </div>

            <div className="form-group">
              <textarea
                value={toolConfig.implementation}
                onChange={(e) => setToolConfig({ ...toolConfig, implementation: e.target.value })}
                placeholder="输入 Python 代码实现..."
                rows={12}
                className={`code-editor ${errors.implementation ? 'error' : ''}`}
                spellCheck={false}
              />
              {errors.implementation && <span className="error-message">{errors.implementation}</span>}
              <small className="form-hint">
                实现一个 execute() 函数，接收定义的参数并返回结果字典
              </small>
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            取消
          </button>
          <button className="btn btn-primary" onClick={handleSave}>
            <Save size={18} />
            保存工具
          </button>
        </div>
      </div>
    </div>
  );
};

export default CustomToolModal;
