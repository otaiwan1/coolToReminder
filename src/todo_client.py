import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import timedelta
from src.logger import logger

class TodoClient:
    def __init__(self, access_token):
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        self.base_url = "https://graph.microsoft.com/v1.0"
        
        # Setup session with retry logic for intermittent Graph API errors (e.g. 503)
        self.session = requests.Session()
        retries = Retry(
            total=3, 
            backoff_factor=1, 
            status_forcelist=[500, 502, 503, 504]
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    def get_or_create_list(self, list_name):
        """Retrieve the ID of a task list by name, creating it if it doesn't exist."""
        # Clean up name if user specifies "Tasks" because Graph API uses "Tasks" as default
        # Getting all lists
        response = self.session.get(f"{self.base_url}/me/todo/lists", headers=self.headers)
        response.raise_for_status()
        
        lists = response.json().get('value', [])
        for l in lists:
            if l.get('displayName') == list_name:
                return l.get('id')
                
        # Not found, create it
        logger.info(f"Creating To Do list: '{list_name}'")
        payload = {"displayName": list_name}
        resp = self.session.post(f"{self.base_url}/me/todo/lists", headers=self.headers, json=payload)
        resp.raise_for_status()
        return resp.json().get('id')

    def create_task(self, list_id, assignment, reminder_minutes_before, extra_payload=None):
        """Create a new task in To Do."""
        payload = self._build_task_payload(assignment, reminder_minutes_before)
        if extra_payload:
            payload.update(extra_payload)
        
        url = f"{self.base_url}/me/todo/lists/{list_id}/tasks"
        response = self.session.post(url, headers=self.headers, json=payload)
        if not response.ok:
            logger.error(f"Failed to create task '{assignment['title']}': {response.text}")
        response.raise_for_status()
        
        return response.json().get('id')

    def update_task(self, list_id, task_id, assignment, reminder_minutes_before, extra_payload=None):
        """Update an existing task in To Do."""
        payload = self._build_task_payload(assignment, reminder_minutes_before)
        if extra_payload:
            payload.update(extra_payload)
        
        url = f"{self.base_url}/me/todo/lists/{list_id}/tasks/{task_id}"
        response = self.session.patch(url, headers=self.headers, json=payload)
        if not response.ok:
            logger.error(f"Failed to update task '{assignment['title']}': {response.text}")
        response.raise_for_status()

    def delete_task(self, list_id, task_id):
        """Delete an existing task in To Do (Optional, in case event is removed)."""
        url = f"{self.base_url}/me/todo/lists/{list_id}/tasks/{task_id}"
        response = self.session.delete(url, headers=self.headers)
        response.raise_for_status()

    def _build_task_payload(self, assignment, reminder_minutes_before):
        due_dt = assignment['due_date']
        
        payload = {
            "title": assignment['title'],
            "body": {
                "content": assignment['description'],
                "contentType": "text"
            }
        }
        
        if assignment.get('due_date_iso'):
            payload["dueDateTime"] = {
                "dateTime": assignment['due_date_iso'],
                "timeZone": "Asia/Taipei"
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
