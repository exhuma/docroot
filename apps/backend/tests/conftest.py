import pytest

from app.storage import FilesystemStorage


@pytest.fixture
def storage(tmp_path):
    return FilesystemStorage(data_root=tmp_path)
