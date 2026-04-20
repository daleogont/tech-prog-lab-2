"""
Data Processor Module

Provides tools for transforming and validating numerical data records.
Supported transform types: normalize, scale, log, passthrough.
"""

import json
import math
from dataclasses import dataclass, field
from typing import Optional


# Constants replacing magic numbers
MAX_INPUT_SIZE = 1000
VALUE_MIN = 0
VALUE_MAX = 999_999


@dataclass
class DataRecord:
    """Represents a single validated and transformed data record."""
    id: int | str
    value: float
    original: float
    transform_type: str
    source: str
    flagged: bool = False


@dataclass
class ProcessingResult:
    """Holds results and errors from a processing run."""
    records: list[DataRecord] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)

    def get_stats(self) -> dict:
        """Compute basic statistics over processed record values."""
        if not self.records:
            return {}
        values = [r.value for r in self.records]
        return {
            "count": len(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
        }

    def save(self, data_path: str = "output_data.json", errors_path: str = "output_errors.json") -> None:
        """Persist records and errors to JSON files."""
        with open(data_path, "w", encoding="utf-8") as fp:
            json.dump([r.__dict__ for r in self.records], fp, indent=2)
        with open(errors_path, "w", encoding="utf-8") as fp:
            json.dump(self.errors, fp, indent=2)


def _apply_transform(value: float, transform_type: str, scale_factor: float) -> Optional[float]:
    """
    Apply the requested numeric transform to a value.

    Returns None when the transform cannot be applied (e.g. log of zero).
    """
    if transform_type == "normalize":
        return (value - VALUE_MIN) / (VALUE_MAX - VALUE_MIN)
    if transform_type == "scale":
        return value * scale_factor
    if transform_type == "log":
        if value <= 0:
            return None
        return math.log(value)
    return value  # passthrough


def _validate_item(item: object, index: int) -> tuple[Optional[float], Optional[str]]:
    """
    Validate a single raw input item.

    Returns (value, None) on success or (None, error_message) on failure.
    """
    if item is None:
        return None, "null item"
    if not isinstance(item, dict):
        return None, "not a dict"
    if "value" not in item:
        return None, "missing 'value' key"

    value = item["value"]
    if not isinstance(value, (int, float)):
        return None, "value is not a number"
    if value < VALUE_MIN:
        return None, "negative value"
    if value > VALUE_MAX:
        return None, "value out of range"
    return value, None


def process_data(
    raw_data: list,
    transform_type: str,
    source: str,
    scale_factor: float = 1.0,
    flagged: bool = False,
    save_results: bool = False,
) -> ProcessingResult:
    """
    Validate and transform a list of raw data items.

    Args:
        raw_data: List of dicts with at least an 'id' and 'value' key.
        transform_type: One of 'normalize', 'scale', 'log', or any other string
                        for passthrough.
        source: Label identifying the data origin.
        scale_factor: Multiplier used when transform_type is 'scale'.
        flagged: Whether to mark all resulting records as flagged.
        save_results: If True, persist results to JSON files after processing.

    Returns:
        A ProcessingResult containing records and errors.

    Raises:
        ValueError: If raw_data exceeds MAX_INPUT_SIZE.
    """
    if len(raw_data) > MAX_INPUT_SIZE:
        raise ValueError(f"Input exceeds maximum size of {MAX_INPUT_SIZE} items.")

    result = ProcessingResult()

    for index, item in enumerate(raw_data):
        record_id = item.get("id", index) if isinstance(item, dict) else index
        value, error = _validate_item(item, index)

        if error is not None:
            result.errors.append({"id": record_id, "error": error})
            continue

        transformed = _apply_transform(value, transform_type, scale_factor)
        if transformed is None:
            result.errors.append({"id": record_id, "error": f"cannot apply '{transform_type}' to value {value}"})
            continue

        result.records.append(
            DataRecord(
                id=record_id,
                value=transformed,
                original=value,
                transform_type=transform_type,
                source=source,
                flagged=flagged,
            )
        )

    stats = result.get_stats()
    if stats:
        print(
            f"Processed {stats['count']} items — "
            f"avg={stats['avg']:.4f}, min={stats['min']:.4f}, max={stats['max']:.4f}"
        )

    if save_results:
        result.save()

    return result


def load_data(filepath: str) -> Optional[list]:
    """
    Load JSON data from a file.

    Returns the parsed list, or None if the file cannot be read or parsed.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as fp:
            return json.load(fp)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Failed to load '{filepath}': {exc}")
        return None


class DataManager:
    """High-level facade for running and inspecting data processing jobs."""

    def __init__(self) -> None:
        self._result: Optional[ProcessingResult] = None

    def run(
        self,
        raw_data: list,
        transform_type: str,
        source: str,
        scale_factor: float = 1.0,
        flagged: bool = False,
        save_results: bool = False,
    ) -> ProcessingResult:
        """Execute a processing job and cache the result."""
        self._result = process_data(
            raw_data,
            transform_type,
            source,
            scale_factor=scale_factor,
            flagged=flagged,
            save_results=save_results,
        )
        return self._result

    @property
    def records(self) -> list[DataRecord]:
        """Return processed records from the last run."""
        return self._result.records if self._result else []

    @property
    def errors(self) -> list[dict]:
        """Return errors from the last run."""
        return self._result.errors if self._result else []

    @property
    def is_processed(self) -> bool:
        """True if at least one job has been run."""
        return self._result is not None


def main() -> None:
    sample = [
        {"id": 1, "value": 100},
        {"id": 2, "value": -5},
        {"id": 3, "value": 0},
        {"id": 4, "value": 500},
        None,
        {"id": 6, "value": "abc"},
    ]

    result = process_data(sample, "normalize", source="test")
    print("Records:", result.records)
    print("Errors: ", result.errors)
    print("Stats:  ", result.get_stats())


if __name__ == "__main__":
    main()
