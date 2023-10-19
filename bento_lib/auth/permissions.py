from collections.abc import Iterator
from typing import NewType

PermissionVerb = NewType("PermissionVerb", str)
PermissionNoun = NewType("PermissionNoun", str)

PermissionTuple = NewType("PermissionTuple", tuple[PermissionVerb, PermissionNoun])


RESOURCE_SPEC = {
    "key": "instance",
    "anyOf": [
        {
            "key": "project",
            "anyOf": [{"key": "dataset"}],
        },
        {"key": "data_type"},
    ],
}


class PermissionsDefinitionError(Exception):
    pass


def permission_tuple_to_str(pt: PermissionTuple) -> str:
    return f"{pt[0]}:{pt[1]}"


def _possible_keysets_for_resource_spec_rec(rs: dict, base_set: frozenset[str]) -> Iterator[frozenset[str]]:
    pass  # TODO


def possible_keysets_for_resource_spec(rs: dict) -> Iterator[frozenset[str]]:
    pass  # TODO


class PermissionsBundle:
    def __init__(self, resource_spec: dict):
        self._verbs: set[PermissionVerb] = set()
        self._nouns: set[PermissionNoun] = set()

        self._permissions: set[PermissionTuple] = set()
        self._valid_keysets_by_permission: dict[PermissionTuple, tuple[frozenset[str], ...]] = {}

        # TODO: validate
        self._resource_spec: dict = resource_spec

    def new_verb(self, verb: str) -> PermissionVerb:
        v = PermissionVerb(verb)
        if v in self._verbs:
            raise PermissionsDefinitionError(f"Verb {v} already exists")
        self._verbs.add(v)
        return v

    def new_noun(self, noun: str) -> PermissionNoun:
        n = PermissionNoun(noun)
        if n in self._nouns:
            raise PermissionsDefinitionError(f"Noun {n} already exists")
        self._nouns.add(n)
        return n

    def new_permission(
        self, verb: PermissionVerb, noun: PermissionNoun, valid_keysets: tuple[frozenset[str], ...]
    ) -> PermissionTuple:
        pt = PermissionTuple((verb, noun))

        if pt in self._permissions:
            raise PermissionsDefinitionError(f"Permission {permission_tuple_to_str(pt)} already exists")

        # TODO: validate valid_keysets
        self._valid_keysets_by_permission[pt] = valid_keysets

        return pt

    def permissions(self) -> frozenset[PermissionTuple]:
        return frozenset(self._permissions)

    def permissions_strs(self) -> frozenset[str]:
        return frozenset(map(permission_tuple_to_str, self._permissions))
