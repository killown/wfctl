import sys
from wfctl.ipc import wayfire_commands
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

    # Extract command from arguments
    command = ' '.join(arg for arg in sys.argv[1:] if not arg.startswith("-"))

    wayfire_commands(command)

if __name__ == "__main__":
    main()

