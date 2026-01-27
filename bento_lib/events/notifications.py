__all__ = ["format_notification"]


def format_notification(title: str, description: str, notification_type: str, action_target: str) -> dict[str, str]:
    """
    Takes in all parameters needed to construct a notification and returns a
    dictionary in the correct format.
    :param title: Notification title
    :param description: Notification description
    :param notification_type: Notification type
    :param action_target: Parameter for the target of any interaction with the notification (e.g. a click)
    :return: The formatted notification dictionary
    """
    return {
        "title": title,
        "description": description,
        "notification_type": notification_type,
        "action_target": action_target,
    }
