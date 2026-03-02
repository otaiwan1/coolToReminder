import argparse
import sys
from src.auth import get_access_token
from src.ical_parser import fetch_and_parse_ical
from src.todo_client import TodoClient
from src.sync_engine import SyncEngine
from src import config
from src.logger import logger

def cmd_auth():
    logger.info("Starting authentication flow...")
    get_access_token()
    logger.info("Authentication successful! Token cached locally.")
    logger.info("You can now run 'python main.py sync' to synchronize assignments.")

def cmd_sync():
    logger.info("Checking authentication...")
    token = get_access_token()
    client = TodoClient(token)
    
    logger.info("Starting iCal synchronization...")
    assignments = fetch_and_parse_ical(config.ICAL_FEED_URL)
    
    # Optional: Filter out past due assignments if desired
    # For now, we sync everything parsed by the feed
    
    engine = SyncEngine(client)
    engine.sync(assignments)
    logger.info("Synchronization complete!")

def main():
    parser = argparse.ArgumentParser(description="Sync NTU Cool Assignments to Microsoft To Do")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Subcommand: auth
    parser_auth = subparsers.add_parser("auth", help="Perform initial device code authentication")
    
    # Subcommand: sync
    parser_sync = subparsers.add_parser("sync", help="Run the sync engine")
    
    args = parser.parse_args()
    
    if args.command == "auth":
        cmd_auth()
    elif args.command == "sync":
        cmd_sync()
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
