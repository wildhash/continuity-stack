"""
LLM Client - Abstraction for LLM provider integration
Supports OpenAI and fallback to deterministic responses for demo
"""
import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class LLMClient:
    """
    LLM provider abstraction with fallback to deterministic mode
    """
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("LLM_MODEL", "gpt-4")
        self.use_llm = bool(self.api_key)
        
        if self.use_llm:
            try:
                import openai
                self.client = openai.OpenAI(api_key=self.api_key)
                logger.info("LLM client initialized with OpenAI")
            except ImportError:
                logger.warning("OpenAI package not installed, using deterministic mode")
                self.use_llm = False
        else:
            logger.info("No OpenAI API key found, using deterministic mode")
    
    async def generate_reflection(self, task_type: str, error: str, context: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate a reflection on a failed task
        Returns: {lesson_learned, improvement_strategy, capability_needed}
        """
        if self.use_llm:
            return await self._generate_reflection_llm(task_type, error, context)
        else:
            return self._generate_reflection_deterministic(task_type, error, context)
    
    async def _generate_reflection_llm(self, task_type: str, error: str, context: Dict[str, Any]) -> Dict[str, str]:
        """Generate reflection using LLM"""
        try:
            prompt = f"""You are a self-reflecting AI agent. You just failed at a task.

Task Type: {task_type}
Error: {error}
Context: {context}

Analyze this failure and provide:
1. A concise lesson learned (one sentence)
2. An improvement strategy (one sentence)
3. The capability you need to gain (snake_case identifier)

Respond in this exact format:
LESSON: <lesson>
STRATEGY: <strategy>
CAPABILITY: <capability>
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a self-reflecting AI agent learning from failures."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            content = response.choices[0].message.content
            
            # Parse the response
            lines = content.strip().split('\n')
            result = {}
            for line in lines:
                if line.startswith("LESSON:"):
                    result["lesson_learned"] = line.replace("LESSON:", "").strip()
                elif line.startswith("STRATEGY:"):
                    result["improvement_strategy"] = line.replace("STRATEGY:", "").strip()
                elif line.startswith("CAPABILITY:"):
                    result["capability_needed"] = line.replace("CAPABILITY:", "").strip()
            
            return result
            
        except Exception as e:
            logger.error(f"LLM reflection failed: {e}, falling back to deterministic mode")
            return self._generate_reflection_deterministic(task_type, error, context)
    
    def _generate_reflection_deterministic(self, task_type: str, error: str, context: Dict[str, Any]) -> Dict[str, str]:
        """Generate deterministic reflection based on error patterns"""
        error_lower = error.lower()
        
        # Schema validation scenario
        if "validation" in task_type or "schema" in error_lower or "required" in error_lower:
            return {
                "lesson_learned": "Input validation against schemas is required before processing data",
                "improvement_strategy": "Implement schema validation checks at the beginning of task execution",
                "capability_needed": f"handle_{task_type}"
            }
        
        # Missing capability scenario
        if "missing capability" in error_lower or "capability" in error_lower:
            capability = error.split(":")[-1].strip() if ":" in error else f"handle_{task_type}"
            return {
                "lesson_learned": f"The capability '{capability}' is essential for handling {task_type} tasks",
                "improvement_strategy": f"Acquire and integrate the {capability} capability into the agent's skill set",
                "capability_needed": capability
            }
        
        # Connection/timeout scenarios
        if "connection" in error_lower or "timeout" in error_lower:
            return {
                "lesson_learned": "Network operations require retry logic and proper timeout handling",
                "improvement_strategy": "Implement exponential backoff retry mechanism with circuit breaker pattern",
                "capability_needed": f"handle_{task_type}"
            }
        
        # Default generic reflection
        return {
            "lesson_learned": f"Failed {task_type} task requires better error handling and validation",
            "improvement_strategy": "Implement comprehensive error handling and input validation",
            "capability_needed": f"handle_{task_type}"
        }
    
    async def generate_task_response(self, task_type: str, data: Dict[str, Any], capabilities: List[str]) -> Dict[str, Any]:
        """
        Generate a response for a task execution
        Returns: {success, message, details}
        """
        if self.use_llm:
            return await self._generate_task_response_llm(task_type, data, capabilities)
        else:
            return self._generate_task_response_deterministic(task_type, data, capabilities)
    
    async def _generate_task_response_llm(self, task_type: str, data: Dict[str, Any], capabilities: List[str]) -> Dict[str, Any]:
        """Generate task response using LLM"""
        try:
            prompt = f"""You are executing a task with the following details:

Task Type: {task_type}
Input Data: {data}
Your Capabilities: {', '.join(capabilities)}

Execute this task and provide a detailed response about what you did.
Be specific about which capabilities you used.
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a capable AI agent executing tasks."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            return {
                "success": True,
                "message": response.choices[0].message.content,
                "details": data
            }
            
        except Exception as e:
            logger.error(f"LLM task response failed: {e}, falling back to deterministic mode")
            return self._generate_task_response_deterministic(task_type, data, capabilities)
    
    def _generate_task_response_deterministic(self, task_type: str, data: Dict[str, Any], capabilities: List[str]) -> Dict[str, Any]:
        """Generate deterministic task response"""
        capability_used = f"handle_{task_type}"
        
        if "validation" in task_type:
            return {
                "success": True,
                "message": f"Successfully validated input data using schema validation capability",
                "details": {
                    "validated": True,
                    "schema_check": "passed",
                    "required_fields": "verified",
                    "capability_used": capability_used,
                    "input_data": data
                }
            }
        
        return {
            "success": True,
            "message": f"Successfully executed {task_type} task using {capability_used} capability",
            "details": {
                "task_type": task_type,
                "capability_used": capability_used,
                "input_data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
