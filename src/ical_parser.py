import requests
from icalendar import Calendar
from datetime import datetime
import hashlib
import re
from src.logger import logger

def fetch_and_parse_ical(url: str):
    """Fetch iCal feed from URL and parse into a list of assignments."""
    if not url:
        raise ValueError("ICAL_FEED_URL is not set.")
        
    logger.info(f"Fetching iCal feed from: {url}")
    response = requests.get(url)
    response.raise_for_status()
    
    calendar = Calendar.from_ical(response.content)
    assignments = []
    
    for component in calendar.walk("VEVENT"):
        assignment = extract_assignment_data(component)
        if assignment:
            # We skip events without a set due date / DTSTART since To Do tasks usually need dates
            assignments.append(assignment)
            
    logger.info(f"Parsed {len(assignments)} valid assignments from iCal feed.")
    return assignments

def extract_assignment_data(event):
    """Extract relevant fields from a VEVENT component."""
    # UID is essential for syncing
    uid = str(event.get('uid', ''))
    if not uid:
        return None
        
    summary = str(event.get('summary', '無標題作業'))
    description = str(event.get('description', ''))
    url = str(event.get('url', ''))
    
    # Extract dates. Canvas usually sets DTSTART and DTEND to the same due date for assignments
    # or just DTSTART for events.
    dtstart = event.get('dtstart')
    dtend = event.get('dtend')
    
    # We use DTEND as due date if available, otherwise fallback to DTSTART
    due_date_obj = dtend.dt if dtend else (dtstart.dt if dtstart else None)
    
    if not due_date_obj:
        return None
        
    # Standardize description to include URL if present
    full_description = description.strip()
    if url:
        full_description += f"\n\n🔗 {url}"
        
    # Canvas LMS descriptions often contain HTML. We'll strip simple HTML tags if needed, 
    # but To Do body accepts some basic plain text. We'll just clean up excessive whitespace.
    full_description = clean_html(full_description)

    # Convert datetime to ISO format for MS Graph
    due_date_iso = None
    if isinstance(due_date_obj, datetime):
        due_date_iso = due_date_obj.isoformat()
    else:
        # It's a date object, not datetime (all-day event)
        due_date_iso = due_date_obj.isoformat() + "T23:59:00"

    # Compute a content hash to detect changes
    content_to_hash = f"{summary}|{full_description}|{due_date_iso}"
    content_hash = hashlib.sha256(content_to_hash.encode('utf-8')).hexdigest()

    return {
        "uid": uid,
        "title": summary,
        "description": full_description,
        "due_date": due_date_obj, # Raw datetime/date object for calculations
        "due_date_iso": due_date_iso,
        "hash": content_hash
    }

def clean_html(raw_html):
    """Remove basic HTML tags often found in Canvas descriptions."""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    
    # Convert simple HTML entities
    cleantext = cleantext.replace('&nbsp;', ' ').replace('&amp;', '&')
    return cleantext.strip()
