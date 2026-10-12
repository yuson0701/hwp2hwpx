from __future__ import annotations

import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

from hwp2hwpx import converter


def _write_hwpx(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("Contents/content.hpf", "<root />")


def _patch_java(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(converter, "_require_java", lambda: "java")
    monkeypatch.setattr(converter, "_jar_path", lambda: Path("fake.jar"))


def test_convert_moves_valid_hwpx(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def fake_run(args, **kwargs):
        _write_hwpx(Path(args[-1]))
        return subprocess.CompletedProcess(args, 0, "", "")

    _patch_java(monkeypatch)
    monkeypatch.setattr(converter.subprocess, "run", fake_run)

    source = tmp_path / "document.hwp"
    source.write_bytes(b"hwp")

    output = converter.convert(source)

    assert output == source.with_suffix(".hwpx").resolve()
    assert zipfile.is_zipfile(output)


def test_convert_fails_on_nonzero_exit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fake_run(args, **kwargs):
        _write_hwpx(Path(args[-1]))
        return subprocess.CompletedProcess(args, 2, "stdout", "stderr")

    _patch_java(monkeypatch)
    monkeypatch.setattr(converter.subprocess, "run", fake_run)

    source = tmp_path / "document.hwp"
    source.write_bytes(b"hwp")

    with pytest.raises(RuntimeError, match="exit code 2"):
        converter.convert(source)


def test_convert_rejects_non_zip_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fake_run(args, **kwargs):
        Path(args[-1]).write_text("not a zip", encoding="utf-8")
        return subprocess.CompletedProcess(args, 0, "", "")

    _patch_java(monkeypatch)
    monkeypatch.setattr(converter.subprocess, "run", fake_run)

    source = tmp_path / "document.hwp"
    source.write_bytes(b"hwp")

    with pytest.raises(RuntimeError, match="valid HWPX/ZIP"):
        converter.convert(source)


def test_convert_requires_existing_input(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        converter.convert(tmp_path / "missing.hwp")


def test_convert_requires_java(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(converter, "_find_java", lambda: None)

    source = tmp_path / "document.hwp"
    source.write_bytes(b"hwp")

    with pytest.raises(RuntimeError, match="Java runtime not found"):
        converter.convert(source)


def test_make_ascii_tempdir_returns_ascii_path() -> None:
    tmp_dir = converter._make_ascii_tempdir()
    try:
        assert converter._is_ascii_path(tmp_dir)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_conversion_repairs_xml_and_preserves_content(monkeypatch, tmp_path):
    header = b'<fonts><font face="&quot"/><font face="&quot;"/><font face="&amp;quot"/></fonts>'
    section = b'<hp:p xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"><hp:t>Keep me</hp:t><hp:linesegarray><hp:lineseg textpos="999"/></hp:linesegarray><hp:linesegarray/></hp:p>'
    image = bytes(range(256))

    def fake_run(args, **kwargs):
        with zipfile.ZipFile(args[-1], 'w') as z:
            z.writestr('Contents/header.xml', header)
            z.writestr('Contents/section0.xml', section)
            z.writestr('Contents/section1.xml', section)
            z.writestr('BinData/image.png', image)
        return subprocess.CompletedProcess(args, 0, '', '')

    _patch_java(monkeypatch)
    monkeypatch.setattr(converter.subprocess, 'run', fake_run)
    source = tmp_path / 'sample.hwp'
    source.write_bytes(b'hwp')
    output = converter.convert(source)
    with zipfile.ZipFile(output) as z:
        assert z.read('Contents/header.xml') == header.replace(b'&quot"', b'&quot;"')
        assert z.read('BinData/image.png') == image
        for n in (0, 1):
            assert z.read(f'Contents/section{n}.xml') == section[:section.index(b'<hp:linesegarray>')] + b'</hp:p>'
    before = output.read_bytes()
    converter._normalize_hwpx(output)
    assert output.read_bytes() == before


def test_invalid_xml_does_not_replace_existing_output(monkeypatch, tmp_path):
    def fake_run(args, **kwargs):
        with zipfile.ZipFile(args[-1], 'w') as z:
            z.writestr('Contents/header.xml', '<root value="&broken"/>')
        return subprocess.CompletedProcess(args, 0, '', '')

    _patch_java(monkeypatch)
    monkeypatch.setattr(converter.subprocess, 'run', fake_run)
    source = tmp_path / 'sample.hwp'
    source.write_bytes(b'hwp')
    output = tmp_path / 'sample.hwpx'
    output.write_bytes(b'existing document')
    with pytest.raises(RuntimeError, match='invalid XML in Contents/header.xml'):
        converter.convert(source, output)
    assert output.read_bytes() == b'existing document'
