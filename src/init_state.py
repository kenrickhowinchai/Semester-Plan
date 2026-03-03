# This code can be run once to create the initial state file structure
import os
import json
import sys

# Get the path to the resources directory
# Handle both development and frozen (exe) environments
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    application_path = os.path.dirname(sys.executable)
    resources_dir = os.path.join(application_path, '_internal', 'resources')
else:
    # Running in development mode
    resources_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources')

# Create the state file with an empty structure
state = {
    "semester_assignments": {},
    "expanded_groups": {},
    "window": {
        "width": 1600,
        "height": 900,
    }
}

# Write the initial state file
state_file = os.path.join(resources_dir, 'calendar_state.json')
with open(state_file, 'w', encoding='utf-8') as f:
    json.dump(state, f, indent=2, ensure_ascii=False)

print(f"Created initial state file at {state_file}")