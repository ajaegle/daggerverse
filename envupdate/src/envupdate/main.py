import re
from pathlib import PurePosixPath
from typing import Annotated
from typing_extensions import Doc

from dagger import Directory, function, object_type

MANAGED_START = "# managed by image automation start"
MANAGED_END = "# managed by image automation end"

KEY_RE = re.compile(r"^[A-Z0-9_]+$")
VALUE_RE = re.compile(r"^[A-Za-z0-9._:@-]+$")


def _validate_env_file_path(env_file_path: str) -> None:
    errors: list[str] = []
    if not env_file_path:
        errors.append("env_file_path must not be empty")
    else:
        rel_path = PurePosixPath(env_file_path)
        if rel_path.is_absolute():
            errors.append(f"env_file_path '{env_file_path}' must be relative, not absolute")
        if ".." in rel_path.parts:
            errors.append(f"env_file_path '{env_file_path}' must not contain parent traversal ('..')")
    if errors:
        raise ValueError("invalid env file path:\n- " + "\n- ".join(errors))


def _parse_updates(raw_updates: list[str]) -> dict[str, str]:
    errors: list[str] = []
    updates: dict[str, str] = {}
    if not raw_updates:
        errors.append("at least one --update KEY=VALUE entry is required")
        raise ValueError("invalid updates:\n- " + "\n- ".join(errors))

    for raw in raw_updates:
        if raw.count("=") != 1:
            errors.append(f"invalid update '{raw}': expected exactly one '='")
            continue

        key, value = raw.split("=", 1)
        if not KEY_RE.fullmatch(key):
            errors.append(f"invalid key '{key}' in update '{raw}': expected [A-Z0-9_]+")
            continue
        if key in updates:
            errors.append(f"duplicate update key '{key}' in update input")
            continue
        if not value:
            errors.append(f"invalid value for key '{key}': value must not be empty")
            continue
        if not VALUE_RE.fullmatch(value):
            errors.append(f"invalid value for key '{key}': unsupported characters in '{value}'")
            continue
        if value.startswith("@") or value.endswith("@") or value.count("@") > 1:
            errors.append(f"invalid '@' placement in value for key '{key}'")
            continue
        updates[key] = value

    if errors:
        raise ValueError("invalid updates:\n- " + "\n- ".join(errors))
    return updates


async def _read_env_lines(directory: Directory, env_file_path: str) -> list[str]:
    try:
        content = await directory.file(env_file_path).contents()
    except Exception as err:
        raise ValueError(f"cannot read '{env_file_path}' (missing/unreadable/invalid UTF-8): {err}") from err
    return content.splitlines()


def _find_managed_block(lines: list[str], env_file_path: str) -> tuple[int, int]:
    errors: list[str] = []
    start_indexes = [idx for idx, line in enumerate(lines) if line == MANAGED_START]
    end_indexes = [idx for idx, line in enumerate(lines) if line == MANAGED_END]

    managed_start = -1
    managed_end = -1
    if len(start_indexes) != 1:
        errors.append(f"file '{env_file_path}' must contain exactly one start marker '{MANAGED_START}'")
    else:
        managed_start = start_indexes[0]

    if len(end_indexes) != 1:
        errors.append(f"file '{env_file_path}' must contain exactly one end marker '{MANAGED_END}'")
    else:
        managed_end = end_indexes[0]

    if managed_start != -1 and managed_end != -1 and managed_start >= managed_end:
        errors.append(f"file '{env_file_path}' has malformed marker order: start must appear before end")

    if errors:
        raise ValueError("invalid env file markers:\n- " + "\n- ".join(errors))
    return managed_start, managed_end


@object_type
class Envupdate:
    @function
    async def update_file(
            self,
            directory: Annotated[Directory, Doc("Directory containing the target env file")],
            env_file_path: Annotated[str, Doc("Relative path to the target env file")],
            update: Annotated[list[str], Doc("Repeated KEY=VALUE updates")],
    ) -> Directory:
        """Update requested KEY=VALUE lines inside the managed block of a single env file."""
        _validate_env_file_path(env_file_path)
        updates = _parse_updates(update)

        lines = await _read_env_lines(directory, env_file_path)
        managed_start, managed_end = _find_managed_block(lines, env_file_path)

        # For each requested key, require exactly one match within the managed section.
        errors: list[str] = []
        for key, value in updates.items():
            found = False
            for line_index, line in enumerate(lines[managed_start + 1: managed_end], start=managed_start + 1):
                if not line.startswith(f"{key}="):
                    continue
                if found:
                    errors.append(f"file '{env_file_path}' managed block contains duplicate requested key '{key}'")
                    continue
                lines[line_index] = f"{key}={value}"
                found = True

            if not found:
                errors.append(f"file '{env_file_path}' managed block is missing requested key '{key}'")

        if errors:
            raise ValueError("invalid env update:\n- " + "\n- ".join(errors))

        rewritten = "\n".join(lines) + "\n"

        return directory.with_new_file(env_file_path, rewritten)
