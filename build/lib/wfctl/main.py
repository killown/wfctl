import sys
import json
from wfctl.ipc import wayfire_commands, watch_events
from wfctl.help import usage

def main():
    if len(sys.argv) < 2 or "-h" in sys.argv:
        usage()
        sys.exit(1)

    if "-m" in sys.argv:
        watch_events()


    command = ' '.join(sys.argv[1:])

    if "-f" in sys.argv:
        wayfire_commands(command, format="fancy_grid")
    else:   
        wayfire_commands(command)


if __name__ == "__main__":
    main()

