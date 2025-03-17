EVENT_WES_RUN_UPDATED = "wes_run_updated"
EVENT_WES_RUN_UPDATED_SCHEMA = {
    "type": "object",
    "properties": {
        "run_id": {"type": "string"},
        "request": {"type": "object"},  # TODO
        "state": {"type": "string"},  # TODO: Enum
        "run_log": {"type": "object"},  # TODO
        "task_logs": {"type": "array"},  # TODO
        "outputs": {"type": "object"},  # TODO
    },
    # TODO: deduplicate this schema
}

EVENT_WES_RUN_FINISHED = "wes_run_finished"
EVENT_WES_RUN_FINISHED_SCHEMA = {
    "type": "object",
    # TODO
}

EVENT_CREATE_NOTIFICATION = "create_notification"
EVENT_CREATE_NOTIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "notification_type": {"type": "string"},
        "action_target": {"type": "string"},
    },
    "required": ["title", "description", "notification_type", "action_target"],
}

EVENT_NOTIFICATION = "notification"
EVENT_NOTIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "notification_type": {"type": "string"},
        "action_target": {"type": "string"},
        "read": {"type": "boolean"},
        "timestamp": {"type": "string"},
    },
    "required": ["id", "title", "description", "notification_type", "action_target", "read", "timestamp"],
}
