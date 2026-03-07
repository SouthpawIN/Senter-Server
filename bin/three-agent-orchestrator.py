#!/usr/bin/env python3
"""
Three-Agent Orchestrator for Senter Server
===========================================

Manages the three-agent system:
1. Chat Agent - Uninterrupted conversation, quick tasks
2. Planner Agent - Silent goal extraction from conversations  
3. Worker Agent - Hermes integration for background execution

All backed by Senter-Server multimodal models via TailScale.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

class AgentState(Enum):
    IDLE = "idle"
    ACTIVE = "active"
    PROCESSING = "processing"
    WAITING_CONFIRMATION = "waiting_confirmation"

@dataclass
class UserGoal:
    """Represents a goal extracted from conversation"""
    id: str
    title: str
    description: str
    priority: int  # 1-5, 5 being highest
    status: str = "proposed"  # proposed, confirmed, in_progress, completed
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    confirmation_required: bool = True
    hermes_job_id: Optional[str] = None

@dataclass
class ConversationContext:
    """Maintains conversation state across agents"""
    session_id: str
    user_message_history: List[Dict] = field(default_factory=list)
    current_intent: Optional[str] = None
    pending_goals: List[str] = field(default_factory=list)  # goal IDs

class ChatAgent:
    """
    Uninterrupted Chat Agent
    
    Handles immediate user interaction, quick tasks, home automation.
    Never interrupted - always available for conversation.
    """
    
    def __init__(self, server_config: Dict):
        self.server_config = server_config
        self.state = AgentState.IDLE
        self.context: Optional[ConversationContext] = None
        self.qwen_endpoint = f"http://{server_config['tailscale_ip']}:{server_config.get('qwen_port', 8100)}/v1/chat/completions"
        
    async def process_message(self, message: str, context: ConversationContext) -> str:
        """Process user message and generate response"""
        self.state = AgentState.ACTIVE
        
        # Build conversation history
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant. Be conversational, direct, and efficient. Handle quick tasks, questions, and home automation commands."}
        ] + context.user_message_history[-10:]  # Last 10 messages for context
        messages.append({"role": "user", "content": message})
        
        # Call Qwen-27B via Senter-Server
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.qwen_endpoint,
                json={
                    "model": "qwen3.5-27b",
                    "messages": messages,
                    "max_tokens": 500,
                    "temperature": 0.7
                }
            ) as response:
                data = await response.json()
                reply = data["choices"][0]["message"]["content"]
        
        # Update context
        context.user_message_history.append({"role": "user", "content": message})
        context.user_message_history.append({"role": "assistant", "content": reply})
        
        self.state = AgentState.IDLE
        return reply
    
    async def handle_quick_task(self, task: str) -> Dict:
        """Handle quick one-shot tasks like home automation"""
        # Parse intent and execute
        result = {
            "task": task,
            "status": "executed",
            "timestamp": datetime.now().isoformat()
        }
        
        # Example: home automation routing
        if "light" in task.lower() or "volume" in task.lower():
            # Route to home automation system
            result["routing"] = "home_automation"
        
        return result


class PlannerAgent:
    """
    Silent Planning Agent
    
    Monitors all conversations, extracts goals and projects,
    proposes plans to Chat Agent for user confirmation.
    """
    
    def __init__(self, server_config: Dict):
        self.server_config = server_config
        self.state = AgentState.IDDE
        self.extracted_goals: List[UserGoal] = []
        self.goal_counter = 0
        self.qwen_endpoint = f"http://{server_config['tailscale_ip']}:{server_config.get('qwen_port', 8100)}/v1/chat/completions"
        
    async def analyze_conversation(self, conversation: List[Dict]) -> List[UserGoal]:
        """Analyze conversation for potential goals and projects"""
        self.state = AgentState.PROCESSING
        
        # Build prompt for goal extraction
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in conversation[-20:]  # Last 20 messages
        ])
        
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.qwen_endpoint,
                json={
                    "model": "qwen3.5-27b",
                    "messages": [
                        {
                            "role": "system",
                            "content": """You are a goal extraction assistant. Analyze conversations and identify:

1. Long-term projects the user wants to work on
2. Goals that would improve their life (happiness, finances, health, skills)
3. Tasks that require multi-step execution
4. Things the user mentioned but hasn't started yet

Output JSON array of goals with: title, description, priority (1-5), and whether confirmation is needed.

Only extract meaningful goals - ignore trivial tasks."""
                        },
                        {"role": "user", "content": f"Analyze this conversation:\n\n{conversation_text}"}
                    ],
                    "max_tokens": 400,
                    "temperature": 0.3
                }
            ) as response:
                data = await response.json()
                goals_text = data["choices"][0]["message"]["content"]
                
        # Parse goals from response
        try:
            goals_data = json.loads(goals_text.strip().strip('```json').strip('```'))
            new_goals = []
            
            for goal_info in goals_data:
                self.goal_counter += 1
                goal = UserGoal(
                    id=f"goal_{self.goal_counter}",
                    title=goal_info.get("title", "Untitled Goal"),
                    description=goal_info.get("description", ""),
                    priority=goal_info.get("priority", 3),
                    confirmation_required=True
                )
                new_goals.append(goal)
                self.extracted_goals.append(goal)
            
            return new_goals
            
        except json.JSONDecodeError:
            print(f"Failed to parse goals: {goals_text}")
            return []
    
    def propose_goal(self, goal: UserGoal) -> str:
        """Format goal proposal for Chat Agent to present to user"""
        return (
            f"🎯 I noticed you might want to work on: **{goal.title}**\n\n"
            f"{goal.description}\n\n"
            f"Would you like me to help you with this? I can break it down into steps and start working on it in the background."
        )


class WorkerAgent:
    """
    Worker Agent (Hermes Integration)
    
    Executes confirmed goals and projects using Hermes Agent framework.
    Runs continuously in background without interrupting chat.
    """
    
    def __init__(self, server_config: Dict):
        self.server_config = server_config
        self.state = AgentState.IDLE
        self.active_jobs: Dict[str, Dict] = {}
        self.hermes_path = server_config.get("hermes_path", "/home/sovthpaw/hermes-agent")
        
    async def execute_goal(self, goal: UserGoal) -> str:
        """Execute a confirmed goal using Hermes"""
        self.state = AgentState.ACTIVE
        
        # Create Hermes job
        import subprocess
        
        # Build task description for Hermes
        task_prompt = f"""
Execute this user goal:

**Title:** {goal.title}
**Description:** {goal.description}
**Priority:** {goal.priority}/5

Break this down into actionable steps and execute them. Use your available tools (file system, web search, code execution, etc.) to accomplish the goal.

Provide progress updates as you work.
"""
        
        # Schedule via Hermes cron or direct invocation
        try:
            result = subprocess.run(
                ["hermes", "--no-gateway"],  # Non-interactive mode
                input=task_prompt,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout for initial response
            )
            
            job_id = f"hermes_job_{datetime.now().timestamp()}"
            self.active_jobs[job_id] = {
                "goal_id": goal.id,
                "status": "running",
                "started_at": datetime.now().isoformat(),
                "output": result.stdout[:1000]  # First 1000 chars
            }
            
            goal.hermes_job_id = job_id
            goal.status = "in_progress"
            
            return {
                "status": "started",
                "job_id": job_id,
                "message": f"Started working on '{goal.title}' in background"
            }
            
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "message": "Initial execution timed out"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get status of active job"""
        return self.active_jobs.get(job_id)


class AwarenessSystem:
    """
    Multi-Modal Activation System
    
    Detects user intent through multiple channels:
    1. Gaze detection + speaking (looking at phone camera)
    2. Double-tap side button
    3. Wake word "Hermes" when not looking at phone
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.phone_ip = config.get("phone_ip", "100.79.15.54")
        self.ssh_port = config.get("ssh_port", 8022)
        self.activation_callback = None
        
    async def check_gaze_and_speech(self) -> bool:
        """Check if user is looking at phone AND speaking"""
        # This would integrate with senter-gaze or similar gaze detection
        # For now, placeholder implementation
        
        # Check gaze (camera analysis)
        gaze_detected = await self._check_gaze()
        
        # Check audio activity
        speech_detected = await self._check_audio_activity()
        
        return gaze_detected and speech_detected
    
    async def _check_gaze(self) -> bool:
        """Check if user is looking at front camera"""
        # Would call gaze detection service or analyze camera feed
        # Placeholder - in real implementation would use computer vision
        try:
            # SSH to phone and check gaze detection status
            import subprocess
            result = subprocess.run(
                ["ssh", "-p", str(self.ssh_port), f"droid@{self.phone_ip}", 
                 "cat /tmp/gaze_detected 2>/dev/null"],
                capture_output=True,
                timeout=5
            )
            return result.stdout.strip() == "true"
        except:
            return False
    
    async def _check_audio_activity(self) -> bool:
        """Check if user is currently speaking"""
        try:
            # Check audio level on phone
            import subprocess
            result = subprocess.run(
                ["ssh", "-p", str(self.ssh_port), f"droid@{self.phone_ip}",
                 "python3 -c 'import sounddevice as sd; print(sd.input_level > 0.1)' 2>/dev/null"],
                capture_output=True,
                timeout=5
            )
            return "True" in result.stdout
        except:
            # Fallback: check if audio file is being written
            return False
    
    async def check_button_double_tap(self) -> bool:
        """Check for double-tap side button event"""
        try:
            import subprocess
            result = subprocess.run(
                ["ssh", "-p", str(self.ssh_port), f"droid@{self.phone_ip}",
                 "cat /tmp/button_double_tap 2>/dev/null && echo '' > /tmp/button_double_tap"],
                capture_output=True,
                timeout=5
            )
            return result.stdout.strip() == "1"
        except:
            return False
    
    async def check_wake_word(self) -> bool:
        """Check for wake word 'Hermes'"""
        # Would integrate with wake word detection (porcupine, snowboy, etc.)
        try:
            import subprocess
            result = subprocess.run(
                ["ssh", "-p", str(self.ssh_port), f"droid@{self.phone_ip}",
                 "cat /tmp/wake_word_detected 2>/dev/null && echo '' > /tmp/wake_word_detected"],
                capture_output=True,
                timeout=5
            )
            return "hermes" in result.stdout.strip().lower()
        except:
            return False
    
    async def monitor_activations(self, callback):
        """Continuously monitor for activation events"""
        self.activation_callback = callback
        
        while True:
            # Check all activation methods
            activations = await asyncio.gather(
                self.check_gaze_and_speech(),
                self.check_button_double_tap(),
                self.check_wake_word()
            )
            
            if any(activations):
                activation_type = "gaze+speech" if activations[0] else ("button" if activations[1] else "wake_word")
                print(f"✅ Activation detected: {activation_type}")
                
                if self.activation_callback:
                    await self.activation_callback(activation_type)
            
            await asyncio.sleep(0.5)  # Check every 500ms


class ThreeAgentOrchestrator:
    """
    Main orchestrator coordinating all three agents
    
    Handles activation, routing between agents, and state management.
    """
    
    def __init__(self, server_config: Dict):
        self.server_config = server_config
        
        # Initialize agents
        self.chat_agent = ChatAgent(server_config)
        self.planner_agent = PlannerAgent(server_config)
        self.worker_agent = WorkerAgent(server_config)
        
        # Awareness system
        self.awareness = AwarenessSystem(server_config)
        
        # State
        self.active_session: Optional[ConversationContext] = None
        self.pending_proposals: List[UserGoal] = []
        
    async def handle_activation(self, activation_type: str):
        """Handle user activation via any method"""
        print(f"🎯 Activated via: {activation_type}")
        
        # Create or resume session
        if not self.active_session:
            import uuid
            self.active_session = ConversationContext(
                session_id=str(uuid.uuid4())
            )
        
        # Start listening for input
        await self.start_conversation_loop()
    
    async def start_conversation_loop(self):
        """Main conversation loop - handles user input and agent coordination"""
        while True:
            # Get user input (audio → text via Omni model)
            user_message = await self.get_user_input()
            
            if not user_message:
                break
            
            # Route to Chat Agent for immediate response
            response = await self.chat_agent.process_message(user_message, self.active_session)
            
            # Speak response (via Soprano → phone)
            await self.speak_response(response)
            
            # Silently analyze for goals (Planner Agent)
            new_goals = await self.planner_agent.analyze_conversation(
                self.active_session.user_message_history[-10:]
            )
            
            # Propose goals to user through Chat Agent
            for goal in new_goals:
                proposal = self.planner_agent.propose_goal(goal)
                print(f"📋 Goal proposal: {goal.title}")
                
                # Ask user if they want to proceed
                confirmation = await self.ask_confirmation(proposal)
                
                if confirmation:
                    # Execute via Worker Agent (Hermes)
                    result = await self.worker_agent.execute_goal(goal)
                    print(f"✅ Started background work: {result}")
    
    async def get_user_input(self) -> str:
        """Capture and transcribe user audio input"""
        # This would:
        # 1. Record audio from phone mic
        # 2. Send to Omni model for speech-to-text
        # 3. Return transcribed text
        
        # Placeholder - in real implementation would use burner-phone audio capture
        print("🎤 Listening...")
        
        # For testing, manual input
        return input("You: ")
    
    async def speak_response(self, text: str):
        """Speak text response through phone"""
        # Route to Soprano TTS → phone speakers
        import subprocess
        
        subprocess.run([
            "/home/sovthpaw/Senter/skills/speak/speak.py",
            "--device", "duo",
            "--if-on",
            text
        ])
    
    async def ask_confirmation(self, proposal: str) -> bool:
        """Ask user to confirm a goal proposal"""
        print(f"\n{proposal}\n")
        response = input("Proceed? (y/n): ").lower().strip()
        return response in ["y", "yes"]


async def main():
    """Main entry point"""
    
    # Configuration
    config = {
        "tailscale_ip": "100.84.195.22",
        "qwen_port": 8100,
        "omni_port": 8101,
        "soprano_port": 8102,
        "phone_ip": "100.79.15.54",
        "ssh_port": 8022,
        "hermes_path": "/home/sovthpaw/hermes-agent"
    }
    
    # Create orchestrator
    orchestrator = ThreeAgentOrchestrator(config)
    
    print("🚀 Three-Agent Orchestrator starting...")
    print("   - Chat Agent: Ready for conversation")
    print("   - Planner Agent: Monitoring for goals")
    print("   - Worker Agent: Hermes integration ready")
    print("   - Awareness System: Watching for activations")
    print()
    
    # Start awareness monitoring
    awareness_task = asyncio.create_task(
        orchestrator.awareness.monitor_activations(
            orchestrator.handle_activation
        )
    )
    
    try:
        # Keep running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        awareness_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())