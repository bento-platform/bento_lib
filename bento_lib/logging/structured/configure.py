import logging
import structlog.processors
import sys
from structlog.types import EventDict, Processor

from .. import log_level_from_str, LogLevelLiteral


__all__ = [
    "drop_color_message_key",
    "STRUCTLOG_COMMON_PROCESSORS",
    "JSON_LOG_PROCESSORS",
    "CONSOLE_LOG_PROCESSORS",
    "configure_structlog",
]


def drop_color_message_key(_logger, _method_name, event_dict: EventDict) -> EventDict:
    """
    By default, uvicorn includes a color_message key in addition to the log event message, which is formatted for
    coloured terminal output. This processor removes that key if it exists, since it's extraneous in a structured
    logging context.
    """
    event_dict.pop("color_message", None)
    return event_dict


STRUCTLOG_COMMON_PROCESSORS: list[Processor] = [
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.add_log_level,
    # format events (messages) with % using positional arguments, like Python's standard logging library:
    structlog.stdlib.PositionalArgumentsFormatter(),
    structlog.stdlib.ExtraAdder(),
    drop_color_message_key,  # removes uvicorn's "color_message" extra
    structlog.processors.TimeStamper(fmt="iso"),
]

JSON_LOG_PROCESSORS: list[Processor] = [structlog.processors.dict_tracebacks, structlog.processors.JSONRenderer()]
CONSOLE_LOG_PROCESSORS: list[Processor] = [
    structlog.dev.ConsoleRenderer(
        # Use a rich exception formatter, but don't show locals since it ends up being exceedingly verbose:
        exception_formatter=structlog.dev.RichTracebackFormatter(show_locals=False)
    )
]


def _build_root_logger_handler(json_logs: bool) -> logging.StreamHandler:
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
    structlog.configure(
        processors=STRUCTLOG_COMMON_PROCESSORS + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(_build_root_logger_handler(json_logs))
    root_logger.setLevel(log_level_from_str(log_level))


def configure_structlog_uvicorn():  # pragma: no cover
    for lgr in ("uvicorn", "uvicorn.error"):
        # Propogate these loggers' messages to the root logger (using the StreamHandler above, formatted by structlog)
        logging.getLogger(lgr).handlers.clear()
        logging.getLogger(lgr).propagate = True

    # Silence default uvicorn.access logs in favour of our structured alternative, attached as a middleware on the app.
    logging.getLogger("uvicorn.access").handlers.clear()
