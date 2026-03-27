#!/usr/bin/env python3
"""Senter Chat - Three-Agent System Interface

The default chat interface for Senter-Server with:
- Chat Agent: Immediate, conversational responses
- Planning Agent: Silent observer, extracts goals, proposes projects  
- Worker Agent: Executes long-term tasks via Hermes
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import subprocess
import requests

# Configuration
SENTER_SERVER_URL = "http://100.84.195.22:8100/v1"
CHAT_HISTORY_FILE = Path("~/.senter-server/chat_history.json").expanduser()
PROJECTS_FILE = Path("~/.senter-server/projects.json").expanduser()


class ThreeAgentSystem:
    """Three-agent architecture for Senter-Server chat."""
    
    def __init__(self):
        self.chat_history = []
        self.pending_projects = []
        self.active_worker_tasks = []
        self._load_history()
    
    def _load_history(self):
        """Load previous chat history."""
        if CHAT_HISTORY_FILE.exists():
            with open(CHAT_HISTORY_FILE) as f:
                data = json.load(f)
                self.chat_history = data.get("history", [])
                self.pending_projects = data.get("pending_projects", [])
    
    def _save_history(self):
        """Save chat history to disk."""
        data = {
            "history": self.chat_history[-100:],  # Keep last 100 messages
            "pending_projects": self.pending_projects,
            "last_updated": datetime.now().isoformat()
        }
        with open(CHAT_HISTORY_FILE, "w") as f:
            json.dump(data, f, indent=2)
    
    # ========== CHAT AGENT (Immediate Responses) ==========
    
    def chat_agent_response(self, user_message: str) -> str:
        """Chat agent provides immediate conversational response."""
        
        # Build context from recent history
        context_messages = self.chat_history[-10:]  # Last 10 messages
        
        # Add current message
        context_messages.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # System prompt for chat agent
        system_prompt = """You are the Chat Agent of Senter-Server.
        
        Your purpose: Provide immediate, helpful, conversational responses.
        
        You have access to:
        - Qwen3.5-35B for reasoning (port 8100)
        - Qwen Omni for vision/audio (port 8100) 
        - Soprano TTS for speech output (port 8102)
        - Burner-Phone for device control
        - Pocket-Shop for MTG trading
        
        Be conversational, helpful, and concise. If the user mentions a long-term goal,
        acknowledge it briefly - the Planning Agent will handle extracting projects."""
        
        # Call Senter-Server LLM
        try:
            response = requests.post(
                f"{SENTER_SERVER_URL}/chat/completions",
                json={
                    "model": "qwen3.5-35b-a3b",
                    "messages": [
                        {"role": "system", "content": system_prompt}
                    ] + context_messages,
                    "max_tokens": 512,
                    "temperature": 0.7
                },
                timeout=30
            )
            
            assistant_response = response.json()["choices"][0]["message"]["content"]
            
            # Save to history
            self.chat_history.append({
                "role": "assistant",
                "content": assistant_response,
                "timestamp": datetime.now().isoformat(),
                "agent": "chat"
            })
            
            return assistant_response
            
        except Exception as e:
            return f"[Chat agent error: {e}]"
    
    # ========== PLANNING AGENT (Silent Observer) ==========
    
    def planning_agent_analyze(self, conversation_snippet: str) -> List[Dict]:
        """Planning agent silently analyzes conversation for goals/projects."""
        
        system_prompt = """You are the Planning Agent of Senter-Server.
        
        Your purpose: Silently analyze conversations to extract long-term goals and projects.
        
        Look for:
        - Goals the user wants to achieve ("I want to...", "I should...")
        - Projects they mention ("building X", "setting up Y")
        - Tasks that require multiple steps
        - Learning objectives
        
        For each goal found, propose a structured project:
        {
            "title": "Brief project name",
            "description": "What this project accomplishes",
            "steps": ["step 1", "step 2", ...],
            "focus_agent": "which focus agent should handle this",
            "priority": "high/medium/low",
            "requires_approval": true
        }
        
        Return a list of proposed projects, or empty list if none found."""
        
        try:
            response = requests.post(
                f"{SENTER_SERVER_URL}/chat/completions",
                json={
                    "model": "qwen3.5-35b-a3b",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Analyze this conversation for goals/projects:\n\n{conversation_snippet}"}
                    ],
                    "max_tokens": 1024,
                    "temperature": 0.5
                },
                timeout=30
            )
            
            # Parse JSON response
            content = response.json()["choices"][0]["message"]["content"]
            projects = json.loads(content)
            
            # Add to pending projects (awaiting user approval)
            for project in projects:
                project["proposed_at"] = datetime.now().isoformat()
                project["status"] = "pending_approval"
                self.pending_projects.append(project)
            
            return projects
            
        except Exception as e:
            print(f"Planning agent error: {e}")
            return []
    
    # ========== WORKER AGENT (Task Execution) ==========
    
    def worker_agent_execute(self, project: Dict) -> str:
        """Worker agent executes approved projects via Hermes."""
        
        task_id = f"task_{int(time.time())}"
        
        # Create Hermes task
        try:
            # This would integrate with Hermes Agent API
            # For now, simulate with subprocess
            result = subprocess.run(
                ["python3", "-c", f"print('Executing: {project['title']}')"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            self.active_worker_tasks.append({
                "task_id": task_id,
                "project": project,
                "status": "completed",
                "started_at": datetime.now().isoformat(),
                "completed_at": datetime.now().isoformat()
            })
            
            return f"Task {task_id} completed: {project['title']}"
            
        except Exception as e:
            return f"Worker agent error: {e}"
    
    # ========== MAIN INTERFACE ==========
    
    def process_message(self, user_message: str) -> Dict:
        """Process a user message through all three agents."""
        
        result = {
            "chat_response": None,
            "proposed_projects": [],
            "worker_updates": []
        }
        
        # 1. Chat Agent - immediate response
        result["chat_response"] = self.chat_agent_response(user_message)
        
        # 2. Planning Agent - silently analyze for projects
        conversation_context = "\n".join([
            m["content"] for m in self.chat_history[-5:]
        ]) + f"\nUser: {user_message}"
        result["proposed_projects"] = self.planning_agent_analyze(conversation_context)
        
        # 3. Check worker task status
        for task in self.active_worker_tasks:
            if task["status"] == "running":
                # Check progress...
                pass
        
        # Save history
        self._save_history()
        
        return result
    
    def propose_projects_to_user(self) -> str:
        """Present pending projects to user for approval."""
        
        if not self.pending_projects:
            return None
        
        proposals = []
        for project in self.pending_projects[:3]:  # Show up to 3
            proposals.append(
                f"• {project['title']}: {project['description']}\n  "
                f"Steps: {', '.join(project['steps'][:3])}..."
            )
        
        return (
            f"I noticed some goals in our conversation. Would you like me to work on these?\n\n"
            + "\n\n".join(proposals) + "\n\n"
            f"Respond with project number to approve, or 'no thanks' to dismiss."
        )


# ========== INTERACTIVE CHAT INTERFACE ==========

def interactive_chat():
    """Run interactive three-agent chat."""
    
    print("="*60)
    print("SENTER-SERVER THREE-AGENT CHAT")
    print("="*60)
    print("\nChat Agent: Immediate responses")
    print("Planning Agent: Silent goal extraction")
    print("Worker Agent: Background task execution")
    print("\nType 'quit' to exit\n")
    
    system = ThreeAgentSystem()
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ["quit", "exit"]:
            break
        
        # Process through three agents
        result = system.process_message(user_input)
        
        # Show chat response
        print(f"\nChat Agent: {result['chat_response']}\n")
        
        # Check for proposed projects
        if result["proposed_projects"]:
            proposal_text = system.propose_projects_to_user()
            if proposal_text:
                print(f"\nPlanning Agent: {proposal_text}\n")


if __name__ == "__main__":
    interactive_chat()
