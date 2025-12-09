# LM Studio Integration Fix

## Issue Summary
The system was unable to communicate with LM Studio or any LLM provider. Messages were sent but no responses were generated because text content was not being extracted from incoming messages.

## Root Cause
The A2A SDK (Agent-to-Agent protocol) uses Pydantic v2's `RootModel` pattern for discriminated unions. Specifically:

```python
class Part(RootModel[TextPart | FilePart | DataPart]):
    root: TextPart | FilePart | DataPart
```

When messages are received, the `part` objects in `message.parts` are wrapper objects. The actual `TextPart`, `FilePart`, or `DataPart` is stored in the `root` attribute.

The original code was checking:
```python
if isinstance(part, types.TextPart):  # This always failed!
    text_parts.append(part.text)
```

But it should have been:
```python
actual_part = part.root if hasattr(part, 'root') else part
if isinstance(actual_part, types.TextPart):  # Now it works!
    text_parts.append(actual_part.text)
```

## What Was Fixed

### 1. Message Text Extraction (`backend/agents/a2a_executor.py`)
**Method**: `_extract_text_from_message()`

**Before**:
```python
for part in message.parts:
    if isinstance(part, types.TextPart):
        text_parts.append(part.text)
```

**After**:
```python
for part in message.parts:
    # Unwrap the RootModel to get the actual part
    actual_part = part.root if hasattr(part, 'root') else part
    
    if isinstance(actual_part, types.TextPart):
        text_parts.append(actual_part.text)
```

### 2. API Response Extraction (`backend/api/agents_a2a.py`)
Updated the `/api/agents/message` endpoint to properly extract text from response parts using the same unwrapping logic.

### 3. Collaboration Response Extraction (`backend/agents/a2a_manager.py`)
Updated the `collaborate_agents()` method to properly extract text from agent responses.

## How to Test

### Test 1: Check Backend Starts
```bash
python run_backend.py
```

You should see:
```
INFO:     Starting A2A Agent System...
INFO:     Application startup complete.
```

### Test 2: Create Agent and Send Message (via API)

1. Start the backend:
```bash
python run_backend.py
```

2. In another terminal, create an agent:
```bash
curl -X POST http://localhost:8000/api/agents/ \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "name": "Test Agent",
      "description": "Test LM Studio agent",
      "provider": "openai",
      "model": "your-model-name",
      "system_prompt": "You are a helpful assistant.",
      "temperature": 0.7,
      "openai_base_url": "http://localhost:1234"
    }
  }'
```

**Note**: Do NOT include `/v1` in the base URL - the OpenAI SDK adds it automatically.

3. Send a message (replace `AGENT_ID` with the ID from step 2):
```bash
curl -X POST http://localhost:8000/api/agents/message \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "AGENT_ID",
    "message": "Hello, how are you?"
  }'
```

### Expected Results

**If LM Studio is running:**
You should get a proper response from your model.

**If LM Studio is NOT running:**
You should get an error message like:
```json
{
  "response": "Error processing message: Connection error."
}
```

This is correct behavior - it means the system is trying to connect to LM Studio but can't reach it.

**Before the fix:**
You would get an empty response (`{"response": ""}`) because the message text wasn't being extracted.

## Logs to Look For

With the fix in place, you should see these logs when sending a message:

```
DEBUG - Agent <ID>: Processing message
INFO - Agent <ID>: Generating response using openai with model <MODEL>
DEBUG - Agent <ID>: Calling openai API (model: <MODEL>)
```

If LM Studio isn't running, you'll see:
```
ERROR - Agent <ID>: Error processing message: Connection error.
```

This is expected and correct - it means the code is trying to call the LLM.

## Configuration for LM Studio

### Option 1: Per-Agent Configuration (Recommended)
When creating an agent via the UI or API, set:
- **Provider**: OpenAI (GPT) or LM Studio
- **Model**: The model name loaded in LM Studio
- **OpenAI API Base URL**: `http://localhost:1234` (without `/v1` - SDK adds it automatically)
- **API Key**: Any string (e.g., "lm-studio" - local models don't validate the key)

### Option 2: Global Configuration
Add to your `.env` file:
```env
OPENAI_API_KEY=lm-studio
OPENAI_BASE_URL=http://localhost:1234
```

**Important**: Do NOT include `/v1` in the base URL. The OpenAI SDK automatically appends `/v1` to the base URL.

## Troubleshooting

### Issue: "Connection error"
**Solution**: Make sure LM Studio is running and the server is started (usually on port 1234)

### Issue: 502 Bad Gateway
**Solution**: This usually happens when the base URL includes `/v1` suffix. Remove `/v1` from your base URL configuration - the OpenAI SDK adds it automatically. Use `http://localhost:1234` instead of `http://localhost:1234/v1`.

### Issue: "Empty content in response"
**Solution**: Check that a model is loaded in LM Studio and is responding. Try a simple request directly to LM Studio's API to verify it's working.

### Issue: Still getting empty responses
**Solution**: 
1. Check the backend logs for errors
2. Verify the base URL is correct (default: `http://localhost:1234`, NOT `http://localhost:1234/v1`)
3. Make sure you're using the latest version of the code with this fix

## Technical Details

### A2A SDK Part Types
The A2A SDK defines three types of message parts:
- **TextPart**: Contains text content
- **FilePart**: Contains file references
- **DataPart**: Contains structured data

All three are wrapped in a `Part` RootModel for type safety and proper serialization.

### Why RootModel?
Pydantic v2 uses `RootModel` for discriminated unions to provide:
- Type-safe serialization/deserialization
- Proper validation
- Clean JSON schema generation

The tradeoff is that you need to access the `.root` attribute to get the actual typed object.

## Related Files Changed
1. `backend/agents/a2a_executor.py` - Core text extraction fix
2. `backend/api/agents_a2a.py` - API endpoint text extraction
3. `backend/agents/a2a_manager.py` - Collaboration text extraction

## Impact
This fix enables the entire agent communication system to work properly. Before this fix, **no LLM provider** would work because message text was always empty.

Now the system properly supports:
- ✅ LM Studio (local LLMs)
- ✅ OpenAI GPT models
- ✅ Google Gemini models
- ✅ LocalAI
- ✅ Ollama
- ✅ Any OpenAI-compatible API
