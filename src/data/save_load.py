def save_calendar_state(calendar_data, file_path):
    import json
    with open(file_path, 'w') as file:
        json.dump(calendar_data, file)

def load_calendar_state(file_path):
    import json
    with open(file_path, 'r') as file:
        return json.load(file)