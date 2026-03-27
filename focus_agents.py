#!/usr/bin/env python3
"""Focus Agents - Dedicated Hermes Instances per Project

Each focus agent is a dedicated self-learning agent focused on one project:
- Pocket-Shop Focus Agent: MTG trading automation
- Burner-Phone Focus Agent: Phone assistant development  
- Senter-Server Focus Agent: AI hub maintenance
- Zombie-Golf-Survival Focus Agent: Game development

Focus agents learn from their work and improve over time.
"""

import json
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Configuration
FOCUS_AGENTS_DIR = Path("~/.senter-server/focus_agents").expanduser()
AGENTS_CONFIG = {
    "pocket-shop": {
        "name": "Pocket-Shop Agent",
        "description": "MTG card trading automation specialist",
        "skills_path": "~/Documents/ObsidianVault/Pocket-Shop/Source/skills",
        "context_files": [
            "~/Documents/ObsidianVault/Pocket-Shop/Overview.md",
            "~/Documents/ObsidianVault/Pocket-Shop/Source/README.md"
        ],
        "goals": [
            "Build automated MTG trading loop",
            "Monitor MTGStocks for high EV sets",
            "Manage card scanning and listing pipeline",
            "Track finances with 30/30/40 splits"
        ]
    },
    "burner-phone": {
        "name": "Burner-Phone Agent", 
        "description": "Phone assistant and automation specialist",
        "skills_path": "~/Documents/ObsidianVault/Burner-Phone/Source/skills",
        "context_files": [
            "~/Documents/ObsidianVault/Burner-Phone/Overview.md",
            "~/Documents/ObsidianVault/Burner-Phone/Source/HACKATHON_OVERVIEW.md"
        ],
        "goals": [
            "Build gaze+wake detection system",
            "Implement full phone control",
            "Create embodied Hermes experience",
            "Test all phone automation features"
        ]
    },
    "senter-server": {
        "name": "Senter-Server Agent",
        "description": "AI hub maintenance and feature development",
        "skills_path": "~/Documents/ObsidianVault/Senter-Server/Source/skills",
        "context_files": [
            "~/Documents/ObsidianVault/Senter-Server/Source/README.md",
            "~/Documents/ObsidianVault/Senter-Server/Source/ARCHITECTURE.md"
        ],
        "goals": [
            "Maintain model services",
            "Build agent builder capability",
            "Collect and organize skills",
            "Implement topic-based knowledge store"
        ]
    },
    "zombie-golf-survival": {
        "name": "Zombie-Golf-Survival Agent",
        "description": "Game development specialist",
        "skills_path": "~/Documents/ObsidianVault/Zombie-Golf-Survival/Source/skills",
        "context_files": [
            "~/Documents/ObsidianVault/Zombie-Golf-Survival/Overview.md"
        ],
        "goals": [
            "Build golf course with Unreal Engine MCP",
            "Implement zombie AI and spawning",
            "Create collectible items system",
            "Add survival mechanics"
        ]
    }
}


class FocusAgent:
    """A dedicated self-learning agent focused on one project."""
    
    def __init__(self, agent_name: str, config: Dict):
        self.agent_name = agent_name
        self.config = config
        self.memory_file = FOCUS_AGENTS_DIR / f"{agent_name}_memory.json"
        self.task_history_file = FOCUS_AGENTS_DIR / f"{agent_name}_tasks.json"
        
        self.memory = self._load_memory()
        self.completed_tasks = self._load_task_history()
    
    def _load_memory(self) -> Dict:
        """Load agent's learned memory."""
        if self.memory_file.exists():
            with open(self.memory_file) as f:
                return json.load(f)
        return {
            "learned_patterns": [],
            "successful_approaches": [],
            "failed_approaches": [],
            "preferences": {},
            "created_at": datetime.now().isoformat()
        }
    
    def _save_memory(self):
        """Save agent's memory."""
        with open(self.memory_file, "w") as f:
            json.dump(self.memory, f, indent=2)
    
    def _load_task_history(self) -> List[Dict]:
        """Load history of completed tasks."""
        if self.task_history_file.exists():
            with open(self.task_history_file) as f:
                return json.load(f)
        return []
    
    def execute_task(self, task: Dict) -> Dict:
        """Execute a task using Hermes Agent."""
        
        result = {
            "task_id": task.get("task_id", f"task_{int(time.time())}"),
            "status": "executing",
            "started_at": datetime.now().isoformat()
        }
        
        try:
            # Build Hermes command with context
            herm es_prompt = self._build_hermes_prompt(task)
            
            # This would actually call Hermes Agent API
            # For now, simulate execution
            print(f"[Focus Agent: {self.agent_name}] Executing: {task.get('title', 'Task')}")
            
            # Simulate work
            time.sleep(1)
            
            result["status"] = "completed"
            result["completed_at"] = datetime.now().isoformat()
            result["output"] = f"Task completed by {self.agent_name}"
            
            # Learn from success
            self._learn_from_task(task, result, successful=True)
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            
            # Learn from failure
            self._learn_from_task(task, result, successful=False)
        
        # Save to history
        self.completed_tasks.append(result)
        if len(self.completed_tasks) > 100:
            self.completed_tasks = self.completed_tasks[-100:]
        
        with open(self.task_history_file, "w") as f:
            json.dump(self.completed_tasks, f, indent=2)
        
        return result
    
    def _build_hermes_prompt(self, task: Dict) -> str:
        """Build a Hermes prompt with full context."""
        
        prompt_parts = [
            f"You are the {self.config['name']}.",
            f"\nYour purpose: {self.config['description']}",
            f"\n\nCurrent task: {task.get('title', 'No title')}",
            f"Description: {task.get('description', 'No description')}",
            "\n\nRelevant goals:",
        ]
        
        for goal in self.config["goals"][:3]:
            prompt_parts.append(f"  - {goal}")
        
        # Add learned patterns
        if self.memory.get("successful_approaches"):
            prompt_parts.append("\n\nPreviously successful approaches:")
            for approach in self.memory["successful_approaches"][:3]:
                prompt_parts.append(f"  - {approach}")
        
        return "\n".join(prompt_parts)
    
    def _learn_from_task(self, task: Dict, result: Dict, successful: bool):
        """Learn from task execution."""
        
        task_summary = f"{task.get('title', 'Task')}: {task.get('description', '')[:100]}"
        
        if successful:
            # Add to successful approaches
            if "successful_approaches" not in self.memory:
                self.memory["successful_approaches"] = []
            
            # Extract what worked
            approach = f"Completed {task.get('title', 'task')} successfully"
            if approach not in self.memory["successful_approaches"]:
                self.memory["successful_approaches"].append(approach)
                if len(self.memory["successful_approaches"]) > 20:
                    self.memory["successful_approaches"] = self.memory["successful_approaches"][-20:]
        
        else:
            # Add to failed approaches
            if "failed_approaches" not in self.memory:
                self.memory["failed_approaches"] = []
            
            failure = f"Failed {task.get('title', 'task')}: {result.get('error', 'Unknown error')}"
            if failure not in self.memory["failed_approaches"]:
                self.memory["failed_approaches"].append(failure)
                if len(self.memory["failed_approaches"]) > 20:
                    self.memory["failed_approaches"] = self.memory["failed_approaches"][-20:]
        
        self._save_memory()
    
    def get_capabilities_report(self) -> str:
        """Get report of agent's capabilities and learning."""
        
        report = [
            f"\u2500"*60,
            f"FOCUS AGENT: {self.config['name']}",
            f"\u2500"*60,
            f"Description: {self.config['description']}",
            f"\nGoals:",
        ]
        
        for goal in self.config["goals"]:
            report.append(f"  \u2022 {goal}")
        
        report.extend([
            f"\nLearning Status:",
            f"  Successful approaches learned: {len(self.memory.get('successful_approaches', []))}",
            f"  Failed approaches recorded: {len(self.memory.get('failed_approaches', []))}",
            f"  Total tasks completed: {len(self.completed_tasks)}",
            f"\u2500"*60
        ])
        
        return "\n".join(report)


class FocusAgentManager:
    """Manages all focus agents."""
    
    def __init__(self):
        self.agents = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all focus agents."""
        FOCUS_AGENTS_DIR.mkdir(parents=True, exist_ok=True)
        
        for agent_name, config in AGENTS_CONFIG.items():
            self.agents[agent_name] = FocusAgent(agent_name, config)
    
    def get_agent(self, agent_name: str) -> Optional[FocusAgent]:
        """Get a specific focus agent."""
        return self.agents.get(agent_name)
    
    def route_task(self, task: Dict) -> Dict:
        """Route a task to the appropriate focus agent."""
        
        agent_name = task.get("focus_agent")
        if not agent_name or agent_name not in self.agents:
            return {"error": f"Unknown focus agent: {agent_name}"}
        
        agent = self.agents[agent_name]
        return agent.execute_task(task)
    
    def get_all_status(self) -> str:
        """Get status report for all agents."""
        
        reports = ["\u2500"*60, "ALL FOCUS AGENTS STATUS", "\u2500"*60]
        
        for agent_name, agent in self.agents.items():
            reports.append(f"\n[{agent_name.upper()}]")
            reports.append(f"  Tasks completed: {len(agent.completed_tasks)}")
            reports.append(f"  Learned approaches: {len(agent.memory.get('successful_approaches', []))}")
        
        reports.append("\u2500"*60)
        return "\n".join(reports)


# ========== MAIN INTERFACE ==========

def main():
    """Main interface for focus agents."""
    
    print("="*60)
    print("FOCUS AGENTS SYSTEM")
    print("="*60)
    
    manager = FocusAgentManager()
    
    # Show all agents
    print("\nAvailable focus agents:")
    for name, agent in manager.agents.items():
        print(f"  \u2022 {name}: {agent.config['description']}")
    
    # Example: Execute a test task
    print("\n" + "="*60)
    print("TESTING FOCUS AGENTS")
    print("="*60)
    
    test_task = {
        "title": "Test Task",
        "description": "This is a test task to verify the focus agent system works",
        "focus_agent": "pocket-shop"
    }
    
    result = manager.route_task(test_task)
    print(f"\nTask result: {result}")
    
    # Show status
    print("\n" + manager.get_all_status())


if __name__ == "__main__":
    main()
