from typing import NewType


class PermissionDefinitionError(Exception):
    pass


Level = NewType("Level", str)

LEVEL_DATASET = Level("dataset")
LEVEL_PROJECT = Level("project")
LEVEL_INSTANCE = Level("instance")

# Levels (applicability): Specifies the minimum (most specific) level at which a permission is applicable
#  - e.g., create:project is not a relevant permission at the project or dataset level, just at the instance level
# In order of most specific to most general:
LEVELS = [
    LEVEL_DATASET,
    LEVEL_PROJECT,
    LEVEL_INSTANCE,
]

PermissionVerb = NewType("PermissionVerb", str)
PermissionNoun = NewType("PermissionNoun", str)


PERMISSIONS: list["Permission"] = []
PERMISSIONS_BY_STRING: dict[str, "Permission"] = {}


class Permission(str):
    def __init__(self, verb: PermissionVerb, noun: PermissionNoun, min_level_required: Level = LEVEL_DATASET):
        super().__init__()

        self._verb: PermissionVerb = verb
        self._noun: PermissionNoun = noun
        self._min_level_required: Level = min_level_required

        str_rep = str(self)

        if str_rep in PERMISSIONS_BY_STRING:
            raise PermissionDefinitionError(f"Permission {str_rep} already defined")

        PERMISSIONS.append(self)
        PERMISSIONS_BY_STRING[str_rep] = self

    def __new__(cls, verb: PermissionVerb, noun: PermissionNoun, min_level_required: Level = LEVEL_DATASET):
        return super().__new__(cls, cls._str_form(verb, noun))

    @classmethod
    def _str_form(cls, verb: PermissionVerb, noun: PermissionNoun) -> str:
        return f"{verb}:{noun}"

    def __repr__(self):
        return f"Permission({str(self)})"


# Verb/noun definitions ---------------------------------------------------------------------------

QUERY_VERB = PermissionVerb("query")
DOWNLOAD_VERB = PermissionVerb("download")
VIEW_VERB = PermissionVerb("view")
CREATE_VERB = PermissionVerb("create")
EDIT_VERB = PermissionVerb("edit")
DELETE_VERB = PermissionVerb("delete")
INGEST_VERB = PermissionVerb("ingest")
ANALYZE_VERB = PermissionVerb("analyze")
EXPORT_VERB = PermissionVerb("export")

PRIVATE_PORTAL = PermissionNoun("private_portal")

PROJECT_LEVEL_BOOLEAN = PermissionNoun("project_level_boolean")
DATASET_LEVEL_BOOLEAN = PermissionNoun("dataset_level_boolean")

PROJECT_LEVEL_COUNTS = PermissionNoun("project_level_counts")
DATASET_LEVEL_COUNTS = PermissionNoun("dataset_level_counts")

DATA = PermissionNoun("data")
DROP_BOX = PermissionNoun("drop_box")
RUNS = PermissionNoun("runs")

PROJECT = PermissionNoun("project")
DATASET = PermissionNoun("dataset")

NOTIFICATIONS = PermissionNoun("notifications")

PERMISSIONS_NOUN = PermissionNoun("permissions")

# Permissions definitions -------------------------------------------------------------------------

P_VIEW_PRIVATE_PORTAL = Permission(VIEW_VERB, PRIVATE_PORTAL, min_level_required=LEVEL_INSTANCE)

P_QUERY_PROJECT_LEVEL_BOOLEAN = Permission(QUERY_VERB, PROJECT_LEVEL_BOOLEAN, min_level_required=LEVEL_PROJECT)
P_QUERY_DATASET_LEVEL_BOOLEAN = Permission(QUERY_VERB, DATASET_LEVEL_BOOLEAN)

P_QUERY_PROJECT_LEVEL_COUNTS = Permission(QUERY_VERB, PROJECT_LEVEL_COUNTS, min_level_required=LEVEL_PROJECT)
P_QUERY_DATASET_LEVEL_COUNTS = Permission(QUERY_VERB, DATASET_LEVEL_COUNTS)

# Data-level: interacting with data inside of data services... and triggering workflows

P_QUERY_DATA = Permission(QUERY_VERB, DATA)  # query at full access
P_DOWNLOAD_DATA = Permission(DOWNLOAD_VERB, DATA)  # download CSVs, associated DRS objects
P_DELETE_DATA = Permission(DELETE_VERB, DATA)  # clear data from a specific data type

#   - workflow-relevant items: (types of workflows....)

P_INGEST_DATA = Permission(INGEST_VERB, DATA)
P_ANALYZE_DATA = Permission(ANALYZE_VERB, DATA)
P_EXPORT_DATA = Permission(EXPORT_VERB, DATA)

P_VIEW_RUNS = Permission(VIEW_VERB, RUNS)

#   - notifications

P_VIEW_NOTIFICATIONS = Permission(VIEW_VERB, NOTIFICATIONS)
P_CREATE_NOTIFICATIONS = Permission(CREATE_VERB, NOTIFICATIONS)

# ---

# only {everything: true} (instance-level):

#   - drop box

P_VIEW_DROP_BOX = Permission(VIEW_VERB, DROP_BOX, min_level_required=LEVEL_INSTANCE)
P_INGEST_DROP_BOX = Permission(INGEST_VERB, DROP_BOX, min_level_required=LEVEL_INSTANCE)
P_DELETE_DROP_BOX = Permission(DELETE_VERB, DROP_BOX, min_level_required=LEVEL_INSTANCE)

#   - project management

P_CREATE_PROJECT = Permission(CREATE_VERB, PROJECT, min_level_required=LEVEL_INSTANCE)
P_DELETE_PROJECT = Permission(DELETE_VERB, PROJECT, min_level_required=LEVEL_INSTANCE)

# ---

# only {everything: true} or {project: ...} (instance- or project-level):
#   - project metadata editing
#   - dataset management
P_EDIT_PROJECT = Permission(EDIT_VERB, PROJECT, min_level_required=LEVEL_PROJECT)
P_CREATE_DATASET = Permission(CREATE_VERB, DATASET, min_level_required=LEVEL_PROJECT)
P_DELETE_DATASET = Permission(DELETE_VERB, DATASET, min_level_required=LEVEL_DATASET)
# ---

#   - dataset metadata editing
P_EDIT_DATASET = Permission(EDIT_VERB, DATASET)

# can view edit permissions for the resource which granted this permission only:
P_VIEW_PERMISSIONS = Permission(VIEW_VERB, PERMISSIONS_NOUN)
P_EDIT_PERMISSIONS = Permission(EDIT_VERB, PERMISSIONS_NOUN)
