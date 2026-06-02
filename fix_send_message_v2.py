with open('backend/agents/a2a_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_code = '''        # Get response from event queue
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

new_code = '''        # Get response from event queue
        events = []
        max_wait = 60  # 最大等待60秒
        wait_time = 0
        
        try:
            while wait_time < max_wait:
                try:
                    event = await asyncio.wait_for(event_queue.dequeue_event(), timeout=1.0)
                    if event:
                        logger.info(f"Received event: {type(event).__name__}")
                        events.append(event)
                        
                        # 检查是否是 Message 类型
                        if isinstance(event, types.Message):
                            logger.info(f"Got Message event with parts: {len(event.parts)}")
                            if event.parts and len(event.parts) > 0:
                                for part in event.parts:
                                    if hasattr(part, 'text') and part.text:
                                        logger.info(f"Returning message with text length: {len(part.text)}")
                                        return event
                        # 如果是其他类型的事件，尝试提取消息
                        elif hasattr(event, 'message') and event.message:
                            logger.info(f"Got event with message attribute")
                            return event.message
                        
                except asyncio.TimeoutError:
                    wait_time += 1
                    continue
        except Exception as e:
            logger.error(f"Error reading event queue: {e}")
        
        # 如果从队列中获取到了事件，尝试从中提取消息
        if events:
            logger.info(f"Total events received: {len(events)}")
            for i, event in enumerate(events):
                logger.info(f"Event {i}: {type(event).__name__}")
                if isinstance(event, types.Message):
                    return event
                if hasattr(event, 'message') and event.message:
                    return event.message
        
        # 如果还是没有响应，使用 fallback 响应
        logger.warning("No events received from agent, using fallback response")
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

print("Improved send_message response extraction with logging!")