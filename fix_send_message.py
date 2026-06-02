with open('backend/agents/a2a_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_code = '''        # Get response from event queue
        events = []
        while not event_queue.is_closed():
            try:
                event = await asyncio.wait_for(event_queue.dequeue_event(), timeout=1.0)
                if event:
                    events.append(event)
            except asyncio.TimeoutError:
                break
        
        # Return the last message event as response
        if events:
            for event in reversed(events):
                if hasattr(event, 'message'):
                    return event.message
        
        # Fallback: create a simple response
        return types.Message(
            message_id=str(uuid.uuid4()),
            role=types.Role.ROLE_AGENT,
            parts=[types.Part(text="Agent processed your request")],
            context_id=context_id,
            task_id=task_id,
        )'''

new_code = '''        # Get response from event queue
        events = []
        max_wait = 60  # 最大等待60秒
        wait_time = 0
        
        while not event_queue.is_closed() and wait_time < max_wait:
            try:
                event = await asyncio.wait_for(event_queue.dequeue_event(), timeout=1.0)
                if event:
                    events.append(event)
                    # 如果是 Task 类型的消息，直接提取文本
                    if hasattr(event, 'task') and event.task and hasattr(event.task, 'messages'):
                        messages = event.task.messages
                        if messages and len(messages) > 0:
                            last_msg = messages[-1]
                            if hasattr(last_msg, 'parts') and last_msg.parts:
                                for part in reversed(last_msg.parts):
                                    if hasattr(part, 'text') and part.text:
                                        return types.Message(
                                            message_id=str(uuid.uuid4()),
                                            role=types.Role.ROLE_AGENT,
                                            parts=[types.Part(text=part.text)],
                                            context_id=context_id,
                                            task_id=task_id,
                                        )
                wait_time += 1
            except asyncio.TimeoutError:
                wait_time += 1
                continue
        
        # 如果从队列中获取到了事件，尝试从中提取消息
        if events:
            for event in reversed(events):
                if hasattr(event, 'message') and event.message:
                    return event.message
        
        # 如果还是没有响应，使用 fallback 响应
        return types.Message(
            message_id=str(uuid.uuid4()),
            role=types.Role.ROLE_AGENT,
            parts=[types.Part(text="Agent processed your request")],
            context_id=context_id,
            task_id=task_id,
        )'''

content = content.replace(old_code, new_code)

with open('backend/agents/a2a_manager.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed send_message response extraction!")