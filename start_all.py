import os
import shutil
import subprocess
import time
from pathlib import Path

SUPA_BASE_REPO_URL = "https://github.com/supabase/supabase.git"


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


def clone_supabase_repo():
    """
    Clone the Supabase repository if it doesn't exist locally.
    If it already exists, pull the latest changes.
    Only the 'docker' directory is checked out using sparse checkout.
    """
    if not Path("supabase").exists():
        print("Cloning Supabase repository...")
        run_command(
            [
                "git",
                "clone",
                "--filter=blob:none",
                "--no-checkout",
                f"{SUPA_BASE_REPO_URL}",
            ]
        )
        os.chdir("supabase")
        run_command(["git", "sparse-checkout", "init", "--cone"])
        run_command(["git", "sparse-checkout", "set", "docker"])
        run_command(["git", "checkout", "master"])
        os.chdir("..")
    else:
        print("Supabase repository already exists, updating...")
        os.chdir("supabase")
        run_command(["git", "pull"])
        os.chdir("..")


def prepare_supabase_env():
    """
    Copy the root .env file to supabase/docker/.env.
    This ensures Supabase services use the correct environment variables.
    """
    env_path = os.path.join("supabase", "docker", ".env")
    env_example_path = os.path.join(".env")
    print("Copying .env in root to .env in supabase/docker...")
    shutil.copyfile(env_example_path, env_path)


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


def start_supabase(environment=None):
    """
    Start Supabase services using its Docker Compose file.
    Args:
        environment (dict, optional): Environment variables to pass (not used here).
    """
    print("Starting Supabase services...")
    cmd = [
        "docker",
        "compose",
        "-p",
        "localai",
        "-f",
        "supabase/docker/docker-compose.yml",
        "up",
        "-d",
    ]
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
    - Start Supabase services and wait for them to initialize
    - Start local AI services
    """
    clone_supabase_repo()
    prepare_supabase_env()
    stop_existing_containers()
    # Start Supabase first
    start_supabase()
    # Give Supabase some time to initialize
    # Then start the local AI services
    start_local_ai()


if __name__ == "__main__":
    main()
