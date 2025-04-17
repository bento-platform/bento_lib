import logging
import structlog.processors
import sys
from structlog.types import EventDict, Processor

from bento_lib.config.pydantic import BentoBaseConfig
from .. import log_level_from_str, LogLevelLiteral


__all__ = [
    "drop_color_message_key",
    "STRUCTLOG_COMMON_PROCESSORS",
    "JSON_LOG_PROCESSORS",
    "CONSOLE_LOG_PROCESSORS",
    "configure_structlog",
    "configure_structlog_from_bento_config",
    "configure_structlog_uvicorn",
]


def drop_color_message_key(_logger, _method_name, event_dict: EventDict) -> EventDict:
    """
    By default, uvicorn includes a color_message key in addition to the log event message, which is formatted for
    coloured terminal output. This processor removes that key if it exists, since it's extraneous in a structured
    logging context.
    """
    event_dict.pop("color_message", None)
    return event_dict


# These common processors are used for all log messages, both ones emitted using structlog and ones formatted from
# standard-library logger objects.
# Most of these are self-explanatory; see https://www.structlog.org/en/stable/processors.html for general information on
# structlog processors.
STRUCTLOG_COMMON_PROCESSORS: list[Processor] = [
    # see https://www.structlog.org/en/stable/api.html#structlog.contextvars.merge_contextvars
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.add_log_level,
    # format events (messages) with % using positional arguments, like Python's standard logging library:
    structlog.stdlib.PositionalArgumentsFormatter(),
    # add any extra arguments passed as args/kwargs to the log call to the final object:
    structlog.stdlib.ExtraAdder(),
    drop_color_message_key,  # removes uvicorn's "color_message" extra
    structlog.processors.TimeStamper(fmt="iso"),
]

# If we're outputting logs in JSON format, make sure to:
#  - format tracebacks as dictionaries (to render as JSON), and
#  - render the log object as JSON
JSON_LOG_PROCESSORS: list[Processor] = [structlog.processors.dict_tracebacks, structlog.processors.JSONRenderer()]
# If we're outputting 'pretty' logs to stdout, use a normal console renderer
CONSOLE_LOG_PROCESSORS: list[Processor] = [
    structlog.dev.ConsoleRenderer(
        # Use a rich exception formatter, but don't show locals since it ends up being exceedingly verbose:
        exception_formatter=structlog.dev.RichTracebackFormatter(show_locals=False)
    )
]


def _build_root_logger_handler(json_logs: bool) -> logging.StreamHandler:
    """
    Create a stdout stream handler for the root logger, which is responsible for formatting structlog-emitted log
    messages, as well as processing _and_ formatting foreign (stdlib logger-emitted) messages.
    :param json_logs: Whether the root logger stream handler should output messages as JSON or human-readable text.
    """

    # handler to used for every log message
    #  - use stdout instead of stderr: https://12factor.net/logs
    handler = logging.StreamHandler(stream=sys.stdout)
    #  - formatter uses structlog for consistent output between Python logging and structlog logger objects
    #     - foreign_pre_chain is responsible for reformatting external (Python logger) log events, so we have a
    #       consistent starting point between logging and structlog event formats.
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=STRUCTLOG_COMMON_PROCESSORS,
            processors=[
                # Remove _record & _from_structlog.
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                *(JSON_LOG_PROCESSORS if json_logs else CONSOLE_LOG_PROCESSORS),
            ],
        )
    )

    return handler


def configure_structlog(json_logs: bool, log_level: LogLevelLiteral):  # pragma: no cover
    """
    Configure root structlog for the downstream service.
    :param json_logs: Whether to output logs as JSON. If this is false, a human-readable text format is used instead.
    :param log_level: The log level to output at.
    """

    structlog.configure(
        processors=STRUCTLOG_COMMON_PROCESSORS + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Set up root logger with a structlog handler and the specified log level.
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(_build_root_logger_handler(json_logs))
    root_logger.setLevel(log_level_from_str(log_level))


def configure_structlog_from_bento_config(config: BentoBaseConfig):  # pragma: no cover
    """
    Configure root structlog for the downstream Bento service if the service is using the BentoBaseConfig Pydantic model
    for configuration. The JSON log boolean and output log level are extracted from the config object.
    :param config: BentoBaseConfig-inheriting configuration object instance.
    """
    configure_structlog(json_logs=config.bento_json_logs, log_level=config.log_level)


def configure_structlog_uvicorn():  # pragma: no cover
    """
    Configure uvicorn loggers to be compatible with structlog as configured above. Error/message loggers are changed
    to propogate to the root logger configured in configure_structlog(...), and the default uvicorn access logger is
    *silenced* (to be replaced by a custom access logger elsewhere!)
    """

    for lgr in ("uvicorn", "uvicorn.error"):
        # Propogate these loggers' messages to the root logger (using the StreamHandler above, formatted by structlog)
        logging.getLogger(lgr).handlers.clear()
        logging.getLogger(lgr).propagate = True

    # Silence default uvicorn.access logs in favour of our structured alternative, attached as a middleware on the app.
    logging.getLogger("uvicorn.access").handlers.clear()
