def format_notification(title: str, description: str, notification_type: str, action_target: str) -> dict:
    return {
        "title": title,
        "description": description,
        "notification_type": notification_type,
        "action_target": action_target
    }
