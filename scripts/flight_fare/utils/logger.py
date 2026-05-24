# import logging
# import sys
# from pathlib import Path
# import io


# def get_logger(name: str, log_file: Path | None = None) -> logging.Logger:
#     logger = logging.getLogger(name)

#     if logger.handlers:
#         return logger

#     logger.setLevel(logging.DEBUG)

#     fmt = logging.Formatter(
#         fmt="%(asctime)s  %(levelname)-8s  [%(name)s]  %(message)s",
#         datefmt="%H:%M:%S",
#     )

#     # 🔥 FIX: force UTF-8 safe output on Windows
#     stream = io.TextIOWrapper(
#         sys.stdout.buffer,
#         encoding="utf-8",
#         errors="replace"
#     )

#     ch = logging.StreamHandler(stream)
#     ch.setLevel(logging.INFO)
#     ch.setFormatter(fmt)
#     logger.addHandler(ch)

#     if log_file:
#         log_file.parent.mkdir(parents=True, exist_ok=True)
#         fh = logging.FileHandler(log_file, encoding="utf-8")
#         fh.setLevel(logging.DEBUG)
#         fh.setFormatter(fmt)
#         logger.addHandler(fh)

#     return logger

import logging
import sys
from pathlib import Path
import io


def get_logger(name: str, log_file: Path | None = None) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        fmt="%(asctime)s  %(levelname)-8s  [%(name)s]  %(message)s",
        datefmt="%H:%M:%S",
    )

    # Handle both terminal (has .buffer) and Jupyter (no .buffer)
    if hasattr(sys.stdout, "buffer"):
        # Terminal / normal Python — wrap for UTF-8 safety on Windows
        stream = io.TextIOWrapper(
            sys.stdout.buffer,
            encoding="utf-8",
            errors="replace"
        )
    else:
        # Jupyter notebook — OutStream has no .buffer, use it directly
        stream = sys.stdout

    ch = logging.StreamHandler(stream)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger