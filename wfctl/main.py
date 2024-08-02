import sys
import json
from wfctl.ipc import wayfire_commands
from wfctl.help import usage

def main():
    if len(sys.argv) < 2 or "-h" in sys.argv:
        usage()
        sys.exit(1)

    command = ' '.join(sys.argv[1:])
    wayfire_commands(command)

if __name__ == "__main__":
    main()

