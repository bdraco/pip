import os
from pathlib import Path
from typing import Iterator
from unittest.mock import Mock

import pytest
from pip._vendor.cachecontrol.caches import FileCache

from pip._internal.network.cache import SafeFileCache


@pytest.fixture(scope="function")
def cache_tmpdir(tmpdir: Path) -> Iterator[Path]:
    cache_dir = tmpdir.joinpath("cache")
    cache_dir.mkdir(parents=True)
    yield cache_dir


class TestSafeFileCache:
    """
    The no_perms test are useless on Windows since SafeFileCache uses
    pip._internal.utils.filesystem.check_path_owner which is based on
    os.geteuid which is absent on Windows.
    """

    def test_cache_roundtrip(self, cache_tmpdir: Path) -> None:
        cache = SafeFileCache(os.fspath(cache_tmpdir))
        assert cache.get("test key") is None
        cache.set("test key", b"a test string")
        assert cache.get("test key") == b"a test string"
        cache.delete("test key")
        assert cache.get("test key") is None

    def test_cache_roundtrip_body(self, cache_tmpdir: Path) -> None:
        cache = SafeFileCache(os.fspath(cache_tmpdir))
        assert cache.get_body("test key") is None
        cache.set_body("test key", b"a test string")
        body = cache.get_body("test key")
        assert body is not None
        with body:
            assert body.read() == b"a test string"
        cache.delete("test key")
        assert cache.get_body("test key") is None

    @pytest.mark.skipif("sys.platform == 'win32'")
    def test_safe_get_no_perms(
        self, cache_tmpdir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        os.chmod(cache_tmpdir, 000)

        monkeypatch.setattr(os.path, "exists", lambda x: True)

        cache = SafeFileCache(os.fspath(cache_tmpdir))
        cache.get("foo")

    @pytest.mark.skipif("sys.platform == 'win32'")
    def test_safe_set_no_perms(self, cache_tmpdir: Path) -> None:
        os.chmod(cache_tmpdir, 000)

        cache = SafeFileCache(os.fspath(cache_tmpdir))
        cache.set("foo", b"bar")

    @pytest.mark.skipif("sys.platform == 'win32'")
    def test_safe_delete_no_perms(self, cache_tmpdir: Path) -> None:
        os.chmod(cache_tmpdir, 000)

        cache = SafeFileCache(os.fspath(cache_tmpdir))
        cache.delete("foo")

    def test_cache_hashes_are_same(self, cache_tmpdir: Path) -> None:
        cache = SafeFileCache(os.fspath(cache_tmpdir))
        key = "test key"
        fake_cache = Mock(FileCache, directory=cache.directory, encode=FileCache.encode)
        assert cache._get_cache_path(key) == FileCache._fn(fake_cache, key)
