import json
import os
from src.todo_client import TodoClient
from src import config
import requests
from datetime import datetime

class SyncEngine:
    def __init__(self, todo_client: TodoClient):
        self.todo_client = todo_client
        self.state_file = config.SYNC_STATE_FILE
        self.state = self._load_state()

    def _load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_state(self):
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=4)

    def sync(self, assignments):
        list_name = config.TODO_LIST_NAME
        list_id = self.todo_client.get_or_create_list(list_name)
        reminder_mins = config.REMINDER_MINUTES_BEFORE
        
        stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}

        # Track seen UIDs to know if an assignment was removed from iCal
        # For now, we don't aggressively delete old tasks from To Do (to preserve user's manual completion state)
        # We only create and update.
        
        for idx, assignment in enumerate(assignments):
            uid = assignment['uid']
            
            try:
                if uid not in self.state:
                    # New task
                    print(f"[{idx+1}/{len(assignments)}] Creating new task: {assignment['title']}")
                    task_id = self.todo_client.create_task(list_id, assignment, reminder_mins)
                    self.state[uid] = {
                        "taskId": task_id,
                        "hash": assignment['hash']
                    }
                    stats["created"] += 1
                else:
                    # Existing task - check if changed
                    saved_hash = self.state[uid].get('hash')
                    current_hash = assignment['hash']
                    task_id = self.state[uid].get('taskId')
                    
                    if not task_id:
                        # Corrupted state
                        print(f"[{idx+1}/{len(assignments)}] Recovering orphaned task: {assignment['title']}")
                        task_id = self.todo_client.create_task(list_id, assignment, reminder_mins)
                        self.state[uid] = {"taskId": task_id, "hash": current_hash}
                        stats["created"] += 1
                    elif saved_hash != current_hash:
                        # Task content updated in Canvas
                        print(f"[{idx+1}/{len(assignments)}] Updating changed task: {assignment['title']}")
                        self.todo_client.update_task(list_id, task_id, assignment, reminder_mins)
                        self.state[uid]['hash'] = current_hash
                        stats["updated"] += 1
                    else:
                        print(f"[{idx+1}/{len(assignments)}] No change for: {assignment['title']}")
                        stats["skipped"] += 1

            except Exception as e:
                print(f"Error syncing task '{assignment['title']}': {str(e)}")
                stats["errors"] += 1
                
        # Update the sync status task
        self._update_sync_status_task(list_id, stats)
        
        # Persist state
        self._save_state()
        
        print("\n--- Sync Summary ---")
        print(f"Tasks Created: {stats['created']}")
        print(f"Tasks Updated: {stats['updated']}")
        print(f"Tasks Skipped: {stats['skipped']}")
        print(f"Sync Errors:   {stats['errors']}")
        
    def _update_sync_status_task(self, list_id, stats):
        try:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            title = f"🔄 Last Sync: {now_str}"
            body = (
                f"✅ Last sync run at {now_str}.\n\n"
                f"--- Stats for this run ---\n"
                f"Tasks Created: {stats['created']}\n"
                f"Tasks Updated: {stats['updated']}\n"
                f"Tasks Skipped: {stats['skipped']}\n"
                f"Sync Errors: {stats['errors']}\n\n"
                "This task updates automatically for monitoring. If you check it off, it will be un-completed on the next run."
            )
            
            pseudo_assignment = {
                "title": title,
                "description": body,
                "due_date": None,
                "due_date_iso": None
            }
            
            uid = "__sync_status__"
            task_id = self.state.get(uid, {}).get("taskId")
            extra_payload = {"status": "notStarted"}
            
            if not task_id:
                task_id = self.todo_client.create_task(list_id, pseudo_assignment, 0, extra_payload)
                self.state[uid] = {"taskId": task_id}
                print(f"Created sync status tracking task.")
            else:
                try:
                    self.todo_client.update_task(list_id, task_id, pseudo_assignment, 0, extra_payload)
                    print(f"Updated sync status tracking task.")
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 404:
                        # Task was deleted by the user, recreate it
                        task_id = self.todo_client.create_task(list_id, pseudo_assignment, 0, extra_payload)
                        self.state[uid] = {"taskId": task_id}
                        print(f"Recreated missing sync status tracking task.")
                    else:
                        raise e
        except Exception as e:
            if hasattr(e, 'response') and e.response is not None:
                print(f"Failed to update sync status tracking task: {e.response.status_code} - {e.response.text}")
            else:
                print(f"Failed to update sync status tracking task: {e}")
