import argparse
import sys
import os
import getpass
import subprocess
from src.auth import get_access_token
from src.ical_parser import fetch_and_parse_ical
from src.todo_client import TodoClient
from src.sync_engine import SyncEngine
from src import config
from src.logger import logger
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

def cmd_deploy():
    """Automate deployment of systemd service and timer on Linux."""
    if sys.platform == "win32":
        logger.error("The deploy command is intended for Linux/Ubuntu environments using Systemd.")
        sys.exit(1)
        
    logger.info("Starting automated deployment for Systemd...")
    
    # Needs sudo for deploying to /etc/systemd/system
    if os.geteuid() != 0:
        logger.error("Please run the deploy command with sudo: 'sudo venv/bin/python main.py deploy'")
        sys.exit(1)

    project_dir = os.path.abspath(os.path.dirname(__file__))
    python_exec = sys.executable
    
    # If run with sudo, getpass.getuser() might return 'root'. Make sure we get the real user if possible
    user = os.getenv("SUDO_USER", getpass.getuser())
    interval_mins = config.SYNC_INTERVAL_MINUTES

    logger.info(f"Target User: {user}")
    logger.info(f"Project Directory: {project_dir}")
    logger.info(f"Python Executable: {python_exec}")
    logger.info(f"Sync Interval: Every {interval_mins} minutes")
    
    service_content = f"""[Unit]
Description=NTU Cool to MS To Do Sync Service
After=network-online.target

[Service]
Type=oneshot
User={user}
WorkingDirectory={project_dir}
ExecStart={python_exec} {project_dir}/main.py sync
StandardOutput=journal
StandardError=journal
Environment="PYTHONUNBUFFERED=1"
"""

    timer_content = f"""[Unit]
Description=Run NTU Cool to MS To Do Sync every {interval_mins} minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec={interval_mins}min
Persistent=true

[Install]
WantedBy=timers.target
"""

    service_name = f"coolsync-{user}"
    service_path = f"/etc/systemd/system/{service_name}.service"
    timer_path = f"/etc/systemd/system/{service_name}.timer"
    
    try:
        with open(service_path, "w") as f:
            f.write(service_content)
        logger.info(f"Wrote service file to {service_path}")
        
        with open(timer_path, "w") as f:
            f.write(timer_content)
        logger.info(f"Wrote timer file to {timer_path}")
        
        # Reload daemon and enable timer
        subprocess.run(["systemctl", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "enable", "--now", f"{service_name}.timer"], check=True)
        
        logger.info(f"✅ Deployment successful! The sync tool is now running in the background for {user}.")
        logger.info(f"You can check the logs anytime using: sudo journalctl -u {service_name}.service -f")
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Sync NTU Cool Assignments to Microsoft To Do")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Subcommand: auth
    parser_auth = subparsers.add_parser("auth", help="Perform initial device code authentication")
    
    # Subcommand: sync
    parser_sync = subparsers.add_parser("sync", help="Run the sync engine")
    
    # Subcommand: deploy
    parser_deploy = subparsers.add_parser("deploy", help="Deploy as a systemd background service (Linux only)")
    
    args = parser.parse_args()
    
    if args.command == "auth":
        cmd_auth()
    elif args.command == "sync":
        cmd_sync()
    elif args.command == "deploy":
        cmd_deploy()
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
