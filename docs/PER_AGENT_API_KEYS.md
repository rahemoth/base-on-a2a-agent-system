# Per-Agent API Key Configuration Feature

## Overview

This feature adds the ability to configure API keys on a per-agent basis in the frontend, addressing user request to add API key configuration for Google AI and OpenAI providers in the agent settings UI.

## Changes Made

### Backend Changes

#### 1. Schema Update (`backend/models/schemas.py`)
- **Added fields to `AgentConfig`:**
  - `google_api_key: Optional[str]` - Per-agent Google API key
  - `openai_api_key: Optional[str]` - Per-agent OpenAI API key

#### 2. Agent Manager Updates
- **`backend/agents/manager.py`:**
  - Modified `create_agent()` to use per-agent API keys with fallback to global settings
  - Modified `update_agent()` to use per-agent API keys with fallback to global settings
  
- **`backend/agents/a2a_manager.py`:**
  - Modified `create_agent()` to use per-agent API keys with fallback to global settings
  - Modified `update_agent()` to use per-agent API keys with fallback to global settings

**Priority System:**
```python
google_api_key = config.google_api_key or settings.google_api_key
openai_api_key = config.openai_api_key or settings.openai_api_key
```

### Frontend Changes

#### 1. AgentConfigModal Component (`frontend/src/components/AgentConfigModal.jsx`)

**Added to initial state:**
```javascript
google_api_key: null,
openai_api_key: null,
```

**New UI Elements:**

**For Google Provider:**
```jsx
<div className="form-group">
  <label>Google API Key (Optional)</label>
  <input 
    type="password" 
    value={config.google_api_key || ''}
    onChange={(e) => setConfig({ ...config, google_api_key: e.target.value || null })}
    placeholder="Leave empty to use global API key from .env"
  />
  <small className="form-hint">
    Per-agent API key overrides the global GOOGLE_API_KEY setting
  </small>
</div>
```

**For OpenAI Provider:**
```jsx
<div className="form-group">
  <label>OpenAI API Key (Optional)</label>
  <input 
    type="password" 
    value={config.openai_api_key || ''}
    onChange={(e) => setConfig({ ...config, openai_api_key: e.target.value || null })}
    placeholder="Leave empty to use global API key from .env"
  />
  <small className="form-hint">
    Per-agent API key overrides the global OPENAI_API_KEY setting
  </small>
</div>
```

## Features

### 1. Provider-Specific Display
- Google API Key field only shows when Google provider is selected
- OpenAI API Key field only shows when OpenAI provider is selected
- Keeps the UI clean and relevant

### 2. Security
- Password input type masks API keys as dots (••••••)
- No default values exposed
- Keys are optional - can be left empty

### 3. Priority System
- **Per-agent API key** (highest priority) - if provided in agent config
- **Global API key** (fallback) - from environment variables (.env file)

### 4. Backward Compatibility
- Existing agents without API keys continue to work
- Uses global API keys from environment variables
- No breaking changes to existing functionality

### 5. User Experience
- Clear labels indicating fields are optional
- Placeholder text explains fallback behavior
- Helper text explains the priority system
- Consistent with existing UI design

## Use Cases

### Use Case 1: Mixed API Keys
Different agents can use different API keys:
- **Agent 1** (Research): Uses Team API key (configured per-agent)
- **Agent 2** (Production): Uses Production API key (configured per-agent)
- **Agent 3** (Testing): Uses global API key from .env

### Use Case 2: Cost Management
Separate billing for different projects:
- **Project A agents**: Use Project A API key
- **Project B agents**: Use Project B API key

### Use Case 3: Rate Limiting
Distribute load across multiple API keys:
- Different agents use different API keys to avoid rate limits

### Use Case 4: Security Isolation
Isolate API access by agent role:
- High-privilege agents use restricted API keys
- General agents use standard API keys

## Testing

### Backend Tests
✅ Python syntax validation passed
✅ Schema changes compile correctly
✅ Agent initialization logic verified

### Frontend Tests
✅ Component builds successfully
✅ No JavaScript errors
✅ UI renders correctly for both providers

### Security Tests
✅ CodeQL scan: 0 alerts
✅ Password fields properly mask input
✅ No API keys exposed in default state

## Screenshots

### Google Provider Configuration
![Google API Configuration](https://github.com/user-attachments/assets/d4a72eb4-5d37-4204-879c-b09498a8f223)

Shows:
- Google API Key input field (password type)
- Clear labeling as "Optional"
- Helper text explaining override behavior

### OpenAI Provider Configuration
![OpenAI API Configuration](https://github.com/user-attachments/assets/e5a3cb2b-21da-4f1c-8cdd-c2bd7c58aa80)

Shows:
- OpenAI API Key input field (password type)
- OpenAI Base URL configuration (existing feature)
- Both fields working together seamlessly

## Migration Guide

### For Existing Users
No action required! Existing agents will continue to use global API keys from environment variables.

### To Use Per-Agent API Keys
1. Open agent configuration modal
2. Select the appropriate provider (Google or OpenAI)
3. Enter the API key in the corresponding field
4. Save the agent configuration

### To Revert to Global API Keys
1. Open agent configuration modal
2. Clear the API key field (leave it empty)
3. Save the agent configuration

## Technical Details

### API Request Format
When creating/updating an agent with API key:
```json
{
  "config": {
    "name": "My Agent",
    "provider": "google",
    "model": "gemini-2.0-flash-exp",
    "google_api_key": "AIza...actual-key-here",
    "system_prompt": "You are a helpful assistant"
  }
}
```

### Storage
- API keys are stored in the agent configuration
- Transmitted securely via HTTPS (in production)
- Not logged or exposed in error messages

### Initialization Flow
```
1. Agent creation/update requested
2. Check if config.google_api_key or config.openai_api_key exists
3. If yes: Use per-agent key
4. If no: Fall back to settings.google_api_key or settings.openai_api_key
5. Initialize agent with selected key
```

## Future Enhancements

Potential improvements for future versions:
1. API key validation before saving
2. Encrypted storage of API keys
3. API key rotation support
4. Usage tracking per API key
5. API key expiration warnings
6. Support for more providers (Anthropic, etc.)

## Commit Information

- **Commit Hash:** a47adb0
- **Files Changed:** 4
  - backend/models/schemas.py
  - backend/agents/manager.py
  - backend/agents/a2a_manager.py
  - frontend/src/components/AgentConfigModal.jsx
- **Lines Changed:** +44, -9

## Related Documentation

- README.md - Updated with API key configuration instructions
- FEATURE_IMPLEMENTATION.md - Technical implementation details
- COLLABORATION_EXAMPLES.md - Usage examples
