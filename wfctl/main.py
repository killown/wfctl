import sys
import json
from wfctl.ipc import wayfire_commands

def main():
    if len(sys.argv) < 2:
        print("Usage: wfctl <command>")
        sys.exit(1)
    
    command = ' '.join(sys.argv[1:])
    response = wayfire_commands(command)
    
    print(json.dumps(response, indent=2))

if __name__ == "__main__":
    main()

