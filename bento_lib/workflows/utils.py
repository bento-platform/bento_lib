__all__ = [
    "namespaced_input",
]


def namespaced_input(workflow_id: str, input_id: str) -> str:
    return f"{workflow_id}.{input_id}"
