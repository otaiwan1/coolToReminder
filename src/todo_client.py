import requests
from datetime import timedelta

class TodoClient:
    def __init__(self, access_token):
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        self.base_url = "https://graph.microsoft.com/v1.0"

    def get_or_create_list(self, list_name):
        """Retrieve the ID of a task list by name, creating it if it doesn't exist."""
        # Clean up name if user specifies "Tasks" because Graph API uses "Tasks" as default
        # Getting all lists
        response = requests.get(f"{self.base_url}/me/todo/lists", headers=self.headers)
        response.raise_for_status()
        
        lists = response.json().get('value', [])
        for l in lists:
            if l.get('displayName') == list_name:
                return l.get('id')
                
        # Not found, create it
        print(f"Creating To Do list: '{list_name}'")
        payload = {"displayName": list_name}
        resp = requests.post(f"{self.base_url}/me/todo/lists", headers=self.headers, json=payload)
        resp.raise_for_status()
        return resp.json().get('id')

    def create_task(self, list_id, assignment, reminder_minutes_before):
        """Create a new task in To Do."""
        payload = self._build_task_payload(assignment, reminder_minutes_before)
        
        url = f"{self.base_url}/me/todo/lists/{list_id}/tasks"
        response = requests.post(url, headers=self.headers, json=payload)
        if not response.ok:
            print(f"Failed to create task '{assignment['title']}': {response.text}")
        response.raise_for_status()
        
        return response.json().get('id')

    def update_task(self, list_id, task_id, assignment, reminder_minutes_before):
        """Update an existing task in To Do."""
        payload = self._build_task_payload(assignment, reminder_minutes_before)
        
        url = f"{self.base_url}/me/todo/lists/{list_id}/tasks/{task_id}"
        response = requests.patch(url, headers=self.headers, json=payload)
        if not response.ok:
            print(f"Failed to update task '{assignment['title']}': {response.text}")
        response.raise_for_status()

    def delete_task(self, list_id, task_id):
        """Delete an existing task in To Do (Optional, in case event is removed)."""
        url = f"{self.base_url}/me/todo/lists/{list_id}/tasks/{task_id}"
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()

    def _build_task_payload(self, assignment, reminder_minutes_before):
        due_dt = assignment['due_date']
        
        payload = {
            "title": assignment['title'],
            "body": {
                "content": assignment['description'],
                "contentType": "text"
            },
            # NTU time zone
            "dueDateTime": {
                "dateTime": assignment['due_date_iso'],
                "timeZone": "Asia/Taipei"
            }
        }
        
        if due_dt and reminder_minutes_before > 0:
            try:
                # Calculate reminder time
                reminder_dt = due_dt - timedelta(minutes=reminder_minutes_before)
                payload["isReminderOn"] = True
                payload["reminderDateTime"] = {
                    "dateTime": reminder_dt.isoformat(),
                    "timeZone": "Asia/Taipei"
                }
            except TypeError:
                # If due_dt is a date instead of datetime, skip reminder
                payload["isReminderOn"] = False
        else:
             payload["isReminderOn"] = False
             
        return payload
