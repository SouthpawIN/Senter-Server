#!/usr/bin/env python3
"""Watcher - Mediator between User Chat and Focus Agents

The Watcher sits between the user's uninterrupted chat and the focus agents:
1. Listens to conversation for tasks/goals
2. Builds structured to-do lists
3. Gets user approval before executing
4. Routes approved tasks to appropriate focus agents
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Configuration
WATCHER_STATE_FILE = Path("~/.senter-server/watcher_state.json").expanduser()
FOCUS_AGENTS = {
    "pocket-shop": "MTG card trading automation",
    "burner-phone": "Phone assistant and control",
    "senter-server": "AI hub maintenance and features",
    "zombie-golf-survival": "Game development"
}


class Watcher:
    """Mediator between user chat and focus agents."""
    
    def __init__(self):
        self.pending_tasks = []
        self.active_tasks = []
        self.completed_tasks = []
        self._load_state()
    
    def _load_state(self):
        """Load watcher state from disk."""
        if WATCHER_STATE_FILE.exists():
            with open(WATCHER_STATE_FILE) as f:
                data = json.load(f)
                self.pending_tasks = data.get("pending_tasks", [])
                self.active_tasks = data.get("active_tasks", [])
                self.completed_tasks = data.get("completed_tasks", [])[-50:]  # Keep last 50
    
    def _save_state(self):
        """Save watcher state to disk."""
        data = {
            "pending_tasks": self.pending_tasks,
            "active_tasks": self.active_tasks,
            "completed_tasks": self.completed_tasks,
            "last_updated": datetime.now().isoformat()
        }
        with open(WATCHER_STATE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    
    def analyze_conversation(self, conversation: str) -> List[Dict]:
        """Analyze conversation and extract potential tasks."""
        
        # This would use LLM to extract structured tasks
        # For now, simple pattern matching
        
        tasks = []
        
        # Example patterns (would be replaced with LLM analysis)
        if "pocket" in conversation.lower() or "mtg" in conversation.lower():
            tasks.append({
                "title": "Pocket-Shop task",
                "description": "Related to MTG trading",
                "focus_agent": "pocket-shop",
                "priority": "medium"
            })
        
        if "phone" in conversation.lower() or "camera" in conversation.lower():
            tasks.append({
                "title": "Burner-Phone task",
                "description": "Related to phone control",
                "focus_agent": "burner-phone",
                "priority": "medium"
            })
        
        return tasks
    
    def build_todo_list(self, tasks: List[Dict]) -> str:
        """Build a human-readable to-do list from extracted tasks."""
        
        if not tasks:
            return "No actionable tasks found in conversation."
        
        todo_lines = ["Here's what I can help you with:"]
        
        for i, task in enumerate(tasks, 1):
            focus_name = FOCUS_AGENTS.get(task["focus_agent"], task["focus_agent"])
            todo_lines.append(
                f"{i}. [{focus_name}] {task['title']}\n"
                f"   {task.get('description', 'No description')}"
            )
        
        return "\n".join(todo_lines)
    
    def request_approval(self, todo_list: str) -> str:
        """Present to-do list to user and request approval."""
        
        return (
            f"{todo_list}\n\n"
            f"What would you like me to do?\n"
            f"- Reply with number(s) to approve specific tasks\n"
            f"- Say 'all' to approve everything\n"
            f"- Say 'no thanks' or 'later' to dismiss\n"
            f"- Or give me specific instructions"
        )
    
    def process_approval(self, user_response: str) -> List[Dict]:
        """Process user's approval response and return tasks to execute."""
        
        tasks_to_execute = []
        
        if user_response.lower() in ["no thanks", "later", "no", "none"]:
            # Clear pending tasks
            self.pending_tasks.clear()
            return tasks_to_execute
        
        elif user_response.lower() == "all":
            # Approve all pending tasks
            tasks_to_execute = self.pending_tasks.copy()
            self.pending_tasks.clear()
        
        else:
            # Parse specific numbers (e.g., "1, 3" or "just 2")
            import re
            numbers = re.findall(r'\d+', user_response)
            for num_str in numbers:
                idx = int(num_str) - 1
                if 0 <= idx < len(self.pending_tasks):
                    tasks_to_execute.append(self.pending_tasks.pop(idx))
        
        # Add metadata to tasks
        for task in tasks_to_execute:
            task["approved_at"] = datetime.now().isoformat()
            task["status"] = "pending_execution"
        
        return tasks_to_execute
    
    def route_to_focus_agent(self, task: Dict) -> str:
        """Route an approved task to the appropriate focus agent."""
        
        focus_agent = task.get("focus_agent", "general")
        task_id = f"{focus_agent}_{int(time.time())}"
        
        # Create execution record
        execution_record = {
            "task_id": task_id,
            "task": task,
            "status": "queued",
            "queued_at": datetime.now().isoformat()
        }
        
        self.active_tasks.append(execution_record)
        self._save_state()
        
        # Here we would actually invoke the focus agent
        # For now, return confirmation
        return (
            f"\u2705 Task queued for {focus_agent} focus agent:\n"
            f"   ID: {task_id}\n"
            f"   {task['title']}"
        )
    
    def execute_approved_tasks(self, approved_tasks: List[Dict]) -> str:
        """Execute all approved tasks by routing to focus agents."""
        
        if not approved_tasks:
            return "No tasks to execute."
        
        results = []
        for task in approved_tasks:
            result = self.route_to_focus_agent(task)
            results.append(result)
        
        return "\n".join(results)
    
    def get_status_report(self) -> str:
        """Get status report of all tasks."""
        
        report = [
            "\u2500"*60,
            "WATCHER STATUS REPORT",
            "\u2500"*60
        ]
        
        if self.pending_tasks:
            report.append(f"\nPENDING APPROVAL ({len(self.pending_tasks)}):")
            for task in self.pending_tasks:
                report.append(f"  • {task['title']} [{task['focus_agent']}]")
        
        if self.active_tasks:
            report.append(f"\nACTIVE ({len(self.active_tasks)}):")
            for task in self.active_tasks[-5:]:  # Show last 5
                status = task.get("status", "unknown")
                report.append(f"  • {task['task_id']}: {status}")
        
        if self.completed_tasks:
            report.append(f"\nRECENTLY COMPLETED ({len(self.completed_tasks)}):")
            for task in self.completed_tasks[-3:]:
                report.append(f"  ✓ {task.get('task_id', 'N/A')}")
        
        report.append("\u2500"*60)
        return "\n".join(report)


# ========== INTERACTIVE WATCHER ==========

def interactive_watcher():
    """Run interactive watcher session."""
    
    print("="*60)
    print("WATCHER - Task Mediator")
    print("="*60)
    print("\nI listen to conversation, extract tasks, get your approval,")
    print("then route work to focus agents.\n")
    
    watcher = Watcher()
    
    while True:
        # Get conversation snippet
        conversation = input("\nEnter conversation snippet (or 'status'/'quit'): ").strip()
        
        if conversation.lower() == "quit":
            break
        
        if conversation.lower() == "status":
            print(watcher.get_status_report())
            continue
        
        # Analyze for tasks
        tasks = watcher.analyze_conversation(conversation)
        watcher.pending_tasks.extend(tasks)
        
        if not tasks:
            print("No actionable tasks found.")
            continue
        
        # Build and present to-do list
        todo_list = watcher.build_todo_list(tasks)
        approval_prompt = watcher.request_approval(todo_list)
        
        print(approval_prompt)
        
        # Get user response
        user_response = input("Your response: ").strip()
        
        # Process approval
        approved_tasks = watcher.process_approval(user_response)
        
        if approved_tasks:
            execution_result = watcher.execute_approved_tasks(approved_tasks)
            print(execution_result)
        else:
            print("No tasks approved.")


if __name__ == "__main__":
    interactive_watcher()
