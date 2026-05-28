import json

import pytest

from repositories import JsonRepository


def test_repository_returns_empty_list_when_file_does_not_exist(tmp_path):
    repository = JsonRepository(tmp_path / "missing.json")

    assert repository.load_all() == []


def test_repository_saves_and_loads_json_list(tmp_path):
    repository = JsonRepository(tmp_path / "data" / "items.json")
    data = [{"id": "1", "name": "Głosowanie próbne"}]

    repository.save_all(data)

    assert repository.load_all() == data


def test_repository_clear_overwrites_file_with_empty_list(tmp_path):
    repository = JsonRepository(tmp_path / "items.json")
    repository.save_all([{"id": "1"}])

    repository.clear()

    assert repository.load_all() == []


def test_repository_rejects_json_object_instead_of_list(tmp_path):
    path = tmp_path / "items.json"
    path.write_text(json.dumps({"id": "1"}), encoding="utf-8")
    repository = JsonRepository(path)

    with pytest.raises(ValueError):
        repository.load_all()
