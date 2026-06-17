from .models import DataDictionary

__all__ = ["DataDictionaryValidator"]


class DataDictionaryValidator:
    """
    The data dictionary validator class wraps a specific data dictionary and provides a validate method for testing
    whether dictionaries conform to this data dictionary.

    So, at ingest time in Katsu, you would have a data dictionary validator for phenopackets/biosamples'
    extra_properties fields if either of these entities have a custom extra properties data dictionary defined.
    """

    def __init__(self, data_dictionary: DataDictionary):
        self._dd = data_dictionary
        self._js_validator = data_dictionary.as_json_schema_validator(
            lang="en"  # language doesn't matter for validation
        )

    def validate(self, record: dict):
        # TODO: ?
        errs = tuple(self._js_validator.iter_errors(record))
        return errs
