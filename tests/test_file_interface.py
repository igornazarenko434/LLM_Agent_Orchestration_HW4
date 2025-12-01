import json
import os
import time
from pathlib import Path

import pytest

from hw4_tourguide.file_interface import FileInterface, CheckpointWriter


@pytest.mark.unit
def test_file_interface_read_write(tmp_path: Path):
    fi = FileInterface()
    data = {"a": 1}
    path = fi.write_json(tmp_path / "test.json", data)
    assert path.exists()
    assert fi.read_json(path) == data


@pytest.mark.unit
def test_file_interface_schema_required(tmp_path: Path):
    fi = FileInterface()
    schema = {"required": ["foo", "bar"]}
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(schema))
    good = {"foo": 1, "bar": 2}
    fi.write_json(tmp_path / "good.json", good)
    assert fi.read_json(tmp_path / "good.json", schema_path) == good
    bad = {"foo": 1}
    fi.write_json(tmp_path / "bad.json", bad)
    with pytest.raises(ValueError):
        fi.read_json(tmp_path / "bad.json", schema_path)


@pytest.mark.unit
def test_checkpoint_writer_basic(tmp_path: Path):
    cw = CheckpointWriter(base_dir=tmp_path, retention_days=7)
    tid = "tid123"
    cw.write(tid, "01_test.json", {"x": 1})
    assert (tmp_path / tid / "01_test.json").exists()
    assert cw.read(tid, "01_test.json") == {"x": 1}
    files = cw.list(tid)
    assert len(files) == 1


@pytest.mark.unit
def test_checkpoint_cleanup(tmp_path: Path, monkeypatch):
    cw = CheckpointWriter(base_dir=tmp_path, retention_days=1)
    tid = "tid456"
    target = cw.write(tid, "01_old.json", {"y": 1})
    old_time = time.time() - (2 * 86400)
    os.utime(target, (old_time, old_time))
    removed = cw.cleanup_old()
    assert target in removed or not target.exists()
