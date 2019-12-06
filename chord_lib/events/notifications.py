def format_notification(title: str, description: str, action_type: str, action_target: str) -> dict:
    return {
        "title": title,
        "description": description,
        "action_type": action_type,
        "action_target": action_target
    }
