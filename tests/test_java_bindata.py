"""Exercise the shipped JAR with generated HWP compound files."""
from pathlib import Path
import base64
import os
import shutil
import subprocess
import zipfile

import pytest

from hwp2hwpx import converter

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII="
)


@pytest.fixture(scope="module")
def java_fixture(tmp_path_factory):
    if not shutil.which("javac") or not shutil.which("java"):
        pytest.skip("JDK required for the Java integration tests")
    classes = tmp_path_factory.mktemp("java-classes")
    source = Path(__file__).parent / "java/BinDataRegression.java"
    subprocess.run([
        "javac", "--release", "8", "-encoding", "UTF-8", "-cp",
        str(converter._jar_path()), "-d", str(classes), str(source),
    ], check=True, capture_output=True, text=True)
    # Load HWPReader from the actual shipped JAR, never from a build directory.
    return os.pathsep.join([str(converter._jar_path()), str(classes)])


@pytest.mark.parametrize("compressed", [True, False])
@pytest.mark.parametrize("ordered", [True, False])
def test_image_bytes_survive_conversion(java_fixture, tmp_path, compressed, ordered):
    source = tmp_path / "synthetic.hwp"
    subprocess.run([
        "java", "-cp", java_fixture, "BinDataRegression", str(source),
        str(compressed).lower(), str(ordered).lower(),
    ], check=True, capture_output=True, text=True)
    result = converter.convert(source)
    ids = [1, 2, 3] if ordered else [3, 1, 7]
    with zipfile.ZipFile(result) as archive:
        assert archive.testzip() is None
        for identifier in ids:
            assert archive.read("BinData/image%d.png" % identifier) == PNG
