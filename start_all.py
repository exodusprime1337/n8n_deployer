import os
import shutil
import subprocess
from pathlib import Path


def run_command(cmd: str, cwd=None):
    """
    Run a shell command and print its output.
    Args:
        cmd (str or list): The command to run.
        cwd (str, optional): The working directory to run the command in.
    """
    print(f"Running command: {cmd}")
    result = subprocess.run(cmd, cwd=cwd, check=True)
    if result.returncode != 0:
        print(f"Error running command: {result.stderr}")
    else:
        print(result.stdout)


def stop_existing_containers():
    """
    Stop and remove any existing Docker containers for the 'localai' project.
    This ensures a clean start for all services.
    """
    print(
        "Stopping and removing existing containers for the unified project 'localai'..."
    )
    cmd = ["docker", "compose", "-p", "localai", "-f", "docker-compose.yml", "down"]
    run_command(cmd)


def start_local_ai():
    """
    Start the local AI services using the main docker-compose.yml file.
    """
    print("Starting local AI services...")
    cmd = ["docker", "compose", "-p", "localai", "-f", "docker-compose.yml", "up", "-d"]
    run_command(cmd)


def main():
    """
    Orchestrate the setup:
    - Clone or update Supabase repo
    - Copy .env file
    - Stop any running containers
    - Start local AI services
    """
    stop_existing_containers()
    start_local_ai()


if __name__ == "__main__":
    main()
