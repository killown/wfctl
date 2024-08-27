import sys
from wfctl.ipc import execute_command
from wfctl.help import usage
from wfctl.utils import watch_events

def main() -> None:
    """Main function to handle command-line arguments and execute commands."""
    if len(sys.argv) < 2 or "-h" in sys.argv:
        usage()
        sys.exit(1)

    if "-m" in sys.argv:
        watch_events()
        return

    # Extract command from arguments as a list
    command = " ".join([arg for arg in sys.argv[1:]])

    # Check if command is empty after processing
    if not command:
        print("Error: No command provided.")
        usage()
        sys.exit(1)

    execute_command(command)

if __name__ == "__main__":
    main()

