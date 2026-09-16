"""Discovery of the numbered example scripts the GUI exposes as tabs.

The GUI never re-implements the examples: each tab runs the actual
``examples/NN_*.py`` file, so the app stays in sync with the scripts.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_EXAMPLE_GLOB = "[0-9][0-9]_*.py"
_DOCSTRING_RE = re.compile(r'^\s*"""(.*)$')
_NUMBERED_PREFIX_RE = re.compile(r"^\d+\s*[\u2014\u2013-]\s*")

# Words that should keep their acronym capitalisation in tab titles.
_ACRONYMS = {"cpu": "CPU", "imu": "IMU", "json": "JSON"}


@dataclass(frozen=True)
class ExampleScript:
    """One numbered example script, e.g. ``examples/02_imu_oneshot.py``."""

    path: Path
    number: int
    title: str
    description: str

    @property
    def tab_label(self) -> str:
        return f"{self.number:02d} · {self.title}"


def discover_examples(examples_dir: Path | None = None) -> list[ExampleScript]:
    """Return every numbered example script under ``examples/``, sorted."""
    directory = examples_dir if examples_dir is not None else default_examples_dir()
    scripts: list[ExampleScript] = []
    for path in sorted(directory.glob(_EXAMPLE_GLOB)):
        number = _number_from_stem(path.stem)
        scripts.append(
            ExampleScript(
                path=path,
                number=number,
                title=_title_from_stem(path.stem),
                description=_doc_first_line(path),
            )
        )
    return scripts


def default_examples_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "examples"


def _number_from_stem(stem: str) -> int:
    head = stem.split("_")[0]
    return int(head) if head.isdigit() else 0


def _title_from_stem(stem: str) -> str:
    words = stem.split("_")
    if words and words[0].isdigit():
        words = words[1:]
    words = [_ACRONYMS.get(word, word.capitalize()) for word in words]
    return " ".join(words) if words else stem


def _doc_first_line(path: Path) -> str:
    """Extract the first line of the script's module docstring (if any)."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    match = _DOCSTRING_RE.match(text)
    if match is None:
        return ""
    description = match.group(1).strip()
    if description.endswith('"""'):
        description = description[: -len('"""')].strip()
    return _NUMBERED_PREFIX_RE.sub("", description).strip()
