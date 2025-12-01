"""
file_interface.py error-handling coverage (M7.17).
"""

from pathlib import Path
import pytest

from hw4_tourguide.file_interface import CheckpointWriter, FileInterface


@pytest.mark.unit
def test_checkpoint_writer_handles_missing_dir(tmp_path):
    writer = CheckpointWriter(base_dir=tmp_path / "nonexistent")
    tid = "tid"
    writer.write(tid, "file.json", {"a": 1})
    assert (tmp_path / "nonexistent" / tid / "file.json").exists()


@pytest.mark.unit
def test_checkpoint_writer_handles_bad_payload(tmp_path):
    writer = CheckpointWriter(base_dir=tmp_path)
    tid = "tid"
    class BadObj:
        def __iter__(self): return self
    # Should not throw when writing unserializable? We expect a TypeError
    with pytest.raises(TypeError):
        writer.write(tid, "bad.json", BadObj())


@pytest.mark.unit
def test_file_interface_read_missing(tmp_path):
    fi = FileInterface()
    with pytest.raises(FileNotFoundError):
        fi.read_json(tmp_path / "missing.json")


@pytest.mark.unit
def test_file_interface_schema_validation(tmp_path):
    fi = FileInterface()
    path = tmp_path / "test.json"
    path.write_text('{"missing_required": true}')
    schema = tmp_path / "schema.json"
    schema.write_text('{"required":["foo"]}')
    with pytest.raises(ValueError):
        fi.read_json(path, schema=schema)
