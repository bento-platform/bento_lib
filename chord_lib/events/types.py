EVENT_WES_RUN_UPDATED = "wes_run_updated"
EVENT_WES_RUN_UPDATED_SCHEMA = {
    "type": "object",
    # TODO
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
        "action_type": {"type": "string"},
        "action_target": {"type": "string"},
    },
    "required": ["title", "description", "action_type", "action_target"]
}

EVENT_NOTIFICATION = "notification"
EVENT_NOTIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "action_type": {"type": "string"},
        "action_target": {"type": "string"},
        "read": {"type": "boolean"}
    },
    "required": ["id", "title", "description", "action_type", "action_target", "read"]
}
