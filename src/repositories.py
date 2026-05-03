import json
from pathlib import Path
from typing import Any


class JsonRepository:
    """Small JSON repository used as a local file-based persistence layer."""

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)

    def load_all(self) -> list[dict[str, Any]]:
        if not self.file_path.exists() or self.file_path.stat().st_size == 0:
            return []

        with self.file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if data == {}:
            return []
        if not isinstance(data, list):
            raise ValueError(f"Expected a JSON list in {self.file_path}.")
        return data

    def save_all(self, data: list[dict[str, Any]]) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with self.file_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)

    def clear(self) -> None:
        self.save_all([])
