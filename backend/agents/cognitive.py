"""
Cognitive Processing Module for Agents
Implements reasoning, decision-making, and planning capabilities
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)

class DecisionType(str, Enum):
    """Types of decisions an agent can make"""
    IMMEDIATE = "immediate"  # Direct response
    PLANNED = "planned"  # Multi-step plan
    TOOL_USE = "tool_use"  # Use a tool
    DELEGATE = "delegate"  # Delegate to another agent
    CLARIFY = "clarify"  # Ask for clarification

class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

class CognitiveProcessor:
    """
    Handles cognitive processing for agents including:
    - Environmental perception
    - Reasoning (chain-of-thought)
    - Decision making
    - Planning
    - Feedback processing
    """
    
    def __init__(self, agent_id: str, agent_name: str):
        self.agent_id = agent_id
        self.agent_name = agent_name
        
        # Perception state
        self.perception_state: Dict[str, Any] = {}
        
        # Reasoning history
        self.reasoning_chain: List[Dict[str, Any]] = []
        
        # Current plan
        self.current_plan: Optional[Dict[str, Any]] = None
        
        # Feedback history
        self.feedback_history: List[Dict[str, Any]] = []
        
    def perceive_environment(
        self,
        message: str,
        context: Optional[List[Dict[str, Any]]] = None,
        available_tools: Optional[List[str]] = None,
        collaboration_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perceive and analyze the environment
        
        Args:
            message: Current input message
            context: Conversation context
            available_tools: List of available tools
            collaboration_context: Information about ongoing collaboration
        
        Returns:
            Perception state
        """
        perception = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "current_message": message,
            "message_length": len(message),
            "context_size": len(context) if context else 0,
            "has_tools": bool(available_tools),
            "available_tools": available_tools or [],
            "in_collaboration": bool(collaboration_context),
            "collaboration_info": collaboration_context or {},
        }
        
        # Analyze message complexity
        perception["complexity"] = self._assess_complexity(message, context)
        
        # Identify intent
        perception["intent"] = self._identify_intent(message)
        
        # Assess urgency
        perception["urgency"] = self._assess_urgency(message)
        
        self.perception_state = perception

        return perception
    
    def reason(
        self,
        perception: Dict[str, Any],
        task_goal: str,
        constraints: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Perform chain-of-thought reasoning
        
        Args:
            perception: Current perception state
            task_goal: The goal to achieve
            constraints: Any constraints to consider
        
        Returns:
            Reasoning result
        """
        reasoning_step = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "goal": task_goal,
            "perception_summary": {
                "complexity": perception.get("complexity"),
                "intent": perception.get("intent"),
                "urgency": perception.get("urgency"),
            },
            "constraints": constraints or [],
            "thoughts": []
        }
        
        # Step 1: Understand the task
        reasoning_step["thoughts"].append({
            "step": 1,
            "type": "understanding",
            "content": f"Task: {task_goal}. Intent: {perception.get('intent')}."
        })
        
        # Step 2: Identify available resources
        available_resources = []
        if perception.get("has_tools"):
            available_resources.append(f"Tools: {', '.join(perception.get('available_tools', []))}")
        if perception.get("context_size", 0) > 0:
            available_resources.append(f"Context: {perception.get('context_size')} messages")
        
        reasoning_step["thoughts"].append({
            "step": 2,
            "type": "resource_identification",
            "content": f"Available resources: {'; '.join(available_resources) if available_resources else 'None'}"
        })
        
        # Step 3: Consider constraints
        if constraints:
            reasoning_step["thoughts"].append({
                "step": 3,
                "type": "constraint_analysis",
                "content": f"Constraints: {'; '.join(constraints)}"
            })
        
        # Step 4: Determine approach
        approach = self._determine_approach(perception, task_goal)
        reasoning_step["thoughts"].append({
            "step": 4,
            "type": "approach",
            "content": f"Recommended approach: {approach}"
        })
        
        reasoning_step["conclusion"] = approach
        
        self.reasoning_chain.append(reasoning_step)

        return reasoning_step
    
    def decide(
        self,
        reasoning: Dict[str, Any],
        perception: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Make a decision based on reasoning and perception
        
        Args:
            reasoning: Reasoning result
            perception: Perception state
        
        Returns:
            Decision with action plan
        """
        decision = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "decision_type": None,
            "action": None,
            "parameters": {},
            "confidence": 0.0,
            "rationale": ""
        }
        
        approach = reasoning.get("conclusion", "")
        complexity = perception.get("complexity", "medium")
        has_tools = perception.get("has_tools", False)
        in_collaboration = perception.get("in_collaboration", False)
        
        # Decision logic
        if "tool" in approach.lower() and has_tools:
            decision["decision_type"] = DecisionType.TOOL_USE
            decision["action"] = "use_tool"
            decision["parameters"]["tools"] = perception.get("available_tools", [])
            decision["confidence"] = 0.8
            decision["rationale"] = "Task requires tool usage and tools are available"
        
        elif complexity == "high" or "plan" in approach.lower():
            decision["decision_type"] = DecisionType.PLANNED
            decision["action"] = "create_plan"
            decision["parameters"]["steps"] = self._create_plan_steps(reasoning, perception)
            decision["confidence"] = 0.7
            decision["rationale"] = "Complex task requires multi-step planning"
        
        elif "clarify" in approach.lower() or "unclear" in approach.lower():
            decision["decision_type"] = DecisionType.CLARIFY
            decision["action"] = "ask_clarification"
            decision["parameters"]["questions"] = self._generate_clarification_questions(perception)
            decision["confidence"] = 0.6
            decision["rationale"] = "Task requirements are unclear"
        
        elif in_collaboration and "delegate" in approach.lower():
            decision["decision_type"] = DecisionType.DELEGATE
            decision["action"] = "delegate_task"
            decision["parameters"]["collaboration_context"] = perception.get("collaboration_info", {})
            decision["confidence"] = 0.75
            decision["rationale"] = "Task can be better handled by another agent in collaboration"
        
        else:
            decision["decision_type"] = DecisionType.IMMEDIATE
            decision["action"] = "respond_directly"
            decision["parameters"]["response_type"] = "direct"
            decision["confidence"] = 0.85
            decision["rationale"] = "Task can be handled with immediate response"

        return decision
    
    def plan_execution(
        self,
        decision: Dict[str, Any],
        task_description: str
    ) -> Dict[str, Any]:
        """
        Create an execution plan based on the decision
        
        Args:
            decision: The decision made
            task_description: Description of the task
        
        Returns:
            Execution plan
        """
        plan = {
            "task_id": f"task_{self.agent_id}_{int(datetime.now(timezone.utc).timestamp())}",
            "task_description": task_description,
            "decision_type": decision["decision_type"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": TaskStatus.PENDING,
            "steps": [],
            "current_step": 0,
            "results": []
        }
        
        if decision["decision_type"] == DecisionType.PLANNED:
            plan["steps"] = decision["parameters"].get("steps", [])
        elif decision["decision_type"] == DecisionType.TOOL_USE:
            plan["steps"] = [
                {
                    "step_number": 1,
                    "action": "select_tool",
                    "description": "Select appropriate tool"
                },
                {
                    "step_number": 2,
                    "action": "execute_tool",
                    "description": "Execute selected tool"
                },
                {
                    "step_number": 3,
                    "action": "process_result",
                    "description": "Process tool result"
                }
            ]
        elif decision["decision_type"] == DecisionType.IMMEDIATE:
            plan["steps"] = [
                {
                    "step_number": 1,
                    "action": "generate_response",
                    "description": "Generate direct response"
                }
            ]
        elif decision["decision_type"] == DecisionType.CLARIFY:
            plan["steps"] = [
                {
                    "step_number": 1,
                    "action": "ask_questions",
                    "description": "Ask clarification questions",
                    "questions": decision["parameters"].get("questions", [])
                }
            ]
        elif decision["decision_type"] == DecisionType.DELEGATE:
            plan["steps"] = [
                {
                    "step_number": 1,
                    "action": "identify_delegate",
                    "description": "Identify best agent to delegate to"
                },
                {
                    "step_number": 2,
                    "action": "handoff",
                    "description": "Hand off task to selected agent"
                }
            ]
        
        self.current_plan = plan
        logger.debug(f"Agent {self.agent_id}: Created execution plan with {len(plan['steps'])} steps")
        
        return plan
    
    def process_feedback(
        self,
        result: str,
        expected_outcome: Optional[str] = None,
        success: bool = True
    ) -> Dict[str, Any]:
        """
        Process feedback from execution results
        
        Args:
            result: The execution result
            expected_outcome: Expected outcome (if any)
            success: Whether the execution was successful
        
        Returns:
            Feedback analysis
        """
        feedback = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "result": result,
            "expected": expected_outcome,
            "success": success,
            "lessons_learned": [],
            "adjustments": []
        }
        
        # Analyze result
        if success:
            feedback["lessons_learned"].append("Approach was successful")
            
            if expected_outcome:
                # Compare with expected
                if self._compare_outcomes(result, expected_outcome):
                    feedback["lessons_learned"].append("Result matches expectations")
                else:
                    feedback["lessons_learned"].append("Result differs from expectations but still successful")
                    feedback["adjustments"].append("Consider revising expectations or approach")
        else:
            feedback["lessons_learned"].append("Approach failed")
            feedback["adjustments"].append("Try alternative approach")
            feedback["adjustments"].append("Consider using tools or requesting help")
        
        # Learn from reasoning chain
        if self.reasoning_chain:
            last_reasoning = self.reasoning_chain[-1]
            if not success and last_reasoning.get("conclusion"):
                feedback["adjustments"].append(f"Reconsider approach: {last_reasoning['conclusion']}")
        
        self.feedback_history.append(feedback)

        return feedback
    
    def update_plan_status(
        self,
        step_number: int,
        status: TaskStatus,
        result: Optional[str] = None
    ):
        """Update the status of a plan step"""
        if not self.current_plan:
            return
        
        self.current_plan["current_step"] = step_number
        
        if status == TaskStatus.COMPLETED and result:
            self.current_plan["results"].append({
                "step": step_number,
                "result": result,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        if step_number >= len(self.current_plan["steps"]):
            self.current_plan["status"] = TaskStatus.COMPLETED
        else:
            self.current_plan["status"] = TaskStatus.IN_PROGRESS

    def get_cognitive_state(self) -> Dict[str, Any]:
        """Get current cognitive state for debugging/monitoring"""
        return {
            "perception": self.perception_state,
            "reasoning_chain_length": len(self.reasoning_chain),
            "current_plan": self.current_plan,
            "feedback_history_length": len(self.feedback_history)
        }
    
    # Helper methods
    
    def _assess_complexity(
        self,
        message: str,
        context: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Assess task complexity based on message and context"""
        # Simple heuristic based on message length and context
        complexity_score = 0
        
        # Message length factor
        if len(message) > 500:
            complexity_score += 2
        elif len(message) > 200:
            complexity_score += 1
        
        # Context factor
        if context and len(context) > 5:
            complexity_score += 1
        
        # Keyword analysis
        complex_keywords = ["analyze", "design", "architect", "plan", "multiple", "complex", "integrate"]
        for keyword in complex_keywords:
            if keyword in message.lower():
                complexity_score += 1
                break
        
        if complexity_score >= 3:
            return "high"
        elif complexity_score >= 1:
            return "medium"
        else:
            return "low"
    
    def _identify_intent(self, message: str) -> str:
        """Identify the intent of the message"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["what", "how", "why", "when", "where", "?"]):
            return "question"
        elif any(word in message_lower for word in ["create", "build", "make", "generate", "write"]):
            return "creation"
        elif any(word in message_lower for word in ["analyze", "review", "check", "evaluate"]):
            return "analysis"
        elif any(word in message_lower for word in ["fix", "solve", "debug", "resolve"]):
            return "problem_solving"
        elif any(word in message_lower for word in ["explain", "describe", "tell me about"]):
            return "explanation"
        else:
            return "general"
    
    def _assess_urgency(self, message: str) -> str:
        """Assess urgency of the message"""
        message_lower = message.lower()
        
        urgent_keywords = ["urgent", "asap", "immediately", "critical", "emergency"]
        if any(keyword in message_lower for keyword in urgent_keywords):
            return "high"
        
        normal_keywords = ["soon", "when possible", "please"]
        if any(keyword in message_lower for keyword in normal_keywords):
            return "medium"
        
        return "low"
    
    def _determine_approach(
        self,
        perception: Dict[str, Any],
        task_goal: str
    ) -> str:
        """Determine the best approach for the task"""
        complexity = perception.get("complexity", "medium")
        intent = perception.get("intent", "general")
        has_tools = perception.get("has_tools", False)
        
        if complexity == "high":
            return "multi-step planning required"
        elif intent == "creation" and has_tools:
            return "use tools for creation"
        elif intent == "question":
            return "provide direct answer"
        elif intent == "analysis" and has_tools:
            return "use tools for analysis"
        else:
            return "direct response"
    
    def _create_plan_steps(
        self,
        reasoning: Dict[str, Any],
        perception: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create plan steps for complex tasks"""
        steps = [
            {
                "step_number": 1,
                "action": "analyze_requirements",
                "description": "Analyze task requirements and constraints"
            },
            {
                "step_number": 2,
                "action": "gather_information",
                "description": "Gather necessary information and context"
            },
            {
                "step_number": 3,
                "action": "execute_task",
                "description": "Execute the main task"
            },
            {
                "step_number": 4,
                "action": "verify_result",
                "description": "Verify and validate the result"
            }
        ]
        
        return steps
    
    def _generate_clarification_questions(
        self,
        perception: Dict[str, Any]
    ) -> List[str]:
        """Generate clarification questions"""
        questions = []
        
        message = perception.get("current_message", "")
        
        if perception.get("complexity") == "high":
            questions.append("Could you break down this task into more specific requirements?")
        
        if perception.get("intent") == "general":
            questions.append("What specific outcome are you looking for?")
        
        if len(message) < 20:
            questions.append("Could you provide more details about what you need?")
        
        if not questions:
            questions.append("Could you clarify your requirements?")
        
        return questions
    
    def _compare_outcomes(self, actual: str, expected: str) -> bool:
        """Compare actual outcome with expected (simple similarity check)"""
        # Simple comparison - can be enhanced with more sophisticated matching
        actual_lower = actual.lower()
        expected_lower = expected.lower()
        
        # Check for keyword overlap
        actual_words = set(actual_lower.split())
        expected_words = set(expected_lower.split())
        
        overlap = actual_words.intersection(expected_words)
        
        # If more than 30% overlap, consider it matching
        if len(overlap) / max(len(expected_words), 1) > 0.3:
            return True
        
        return False
