"""Real HWP -> HWPX boundary cases; regressions for attribute escaping and long paragraphs."""
import os
import shutil
import subprocess
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import pytest
from hwp2hwpx.converter import convert, _jar_path, _normalize_hwpx

@pytest.fixture(scope='module')
def fixture_runner(tmp_path_factory):
    if not shutil.which('javac') or not shutil.which('java'):
        pytest.skip('JDK required')
    build = tmp_path_factory.mktemp('xml-fixture')
    jar = _jar_path()
    subprocess.run(['javac', '--release', '8', '-cp', str(jar), '-d', str(build),
                    str(Path(__file__).parent / 'java/XmlBoundaryRegression.java')], check=True)
    def make(tmp, font, body, stale=False):
        (tmp / 'font.txt').write_text(font, encoding='utf-8')
        (tmp / 'body.txt').write_text(body, encoding='utf-8')
        source = tmp / '시험 문서 & 경계.hwp'
        subprocess.run(['java', '-cp', os.pathsep.join([str(build), str(jar)]),
                        'XmlBoundaryRegression', str(source), str(tmp / 'font.txt'),
                        str(tmp / 'body.txt')] + (['stale'] if stale else []), check=True)
        return source
    return make


@pytest.mark.parametrize('font', ['함초롬바탕', "A'B", 'Font😀',
    *[s for s in ['"', '"Font', 'A"B', 'Font"', '"Font"', 'A&B', 'A<B>C', 'A&quot;B', 'A&quotB', 'A\tB', 'A\nB']]])
def test_font_and_body_preserved(fixture_runner, tmp_path, font):
    body = '본문 < > & " \' &quot; &quot &#34; ]]> ① α ≥ → 😀 🫀 끝'
    output = convert(fixture_runner(tmp_path, font, body))
    with zipfile.ZipFile(output) as z:
        header = ET.fromstring(z.read('Contents/header.xml'))
        section = ET.fromstring(z.read('Contents/section0.xml'))
    assert font in [e.get('face') for e in header.iter() if e.tag.endswith('}font')]
    assert ''.join(''.join(t.itertext()) for t in section.iter() if t.tag.endswith('}t')) == body

@pytest.mark.parametrize('length', [1000, 65000, 65534, 65535, 65536, 100000])
def test_long_single_paragraph(fixture_runner, tmp_path, length):
    body = '가' * length
    with zipfile.ZipFile(convert(fixture_runner(tmp_path, '함초롬바탕', body))) as z:
        section = ET.fromstring(z.read('Contents/section0.xml'))
    assert ''.join(''.join(t.itertext()) for t in section.iter() if t.tag.endswith('}t')) == body

def test_stale_hwp_line_cache_removed(fixture_runner, tmp_path):
    body = '짧은 문장인데 줄 시작 위치는 999999인 시험'
    source = fixture_runner(tmp_path, '함초롬바탕', body, stale=True)
    raw = tmp_path / 'raw.hwpx'
    subprocess.run(['java', '-jar', str(_jar_path()), str(source), str(raw)], check=True, capture_output=True)
    with zipfile.ZipFile(raw) as z:
        raw_section = ET.fromstring(z.read('Contents/section0.xml'))
    assert any(e.get('textpos') == '999999' for e in raw_section.iter())
    with zipfile.ZipFile(convert(source)) as z:
        section = ET.fromstring(z.read('Contents/section0.xml'))
    assert not any(e.tag.endswith('}linesegarray') for e in section.iter())
    assert ''.join(''.join(t.itertext()) for t in section.iter() if t.tag.endswith('}t')) == body

# Deliberate broken output: these test the safety gate, not HWP conversion.
@pytest.mark.parametrize('name,data', [
    ('Contents/header.xml', b'<r a="A&quotB"/>'),
    ('Contents/section0.xml', b'<r>\x01</r>'),
    ('Contents/content.hpf', b'<r><unclosed></r>'),
    ('Contents/header.xml', b'<r>&unknown;</r>'),
])
def test_invalid_xml_rejected_without_replacing_input(tmp_path, name, data):
    path = tmp_path / 'broken.hwpx'
    with zipfile.ZipFile(path, 'w') as z: z.writestr(name, data)
    before = path.read_bytes()
    with pytest.raises(RuntimeError, match='invalid XML'):
        _normalize_hwpx(path)
    assert path.read_bytes() == before
    assert not path.with_suffix('.normalized.hwpx').exists()

def test_cell_metadata_is_escaped_exactly_once(tmp_path):
    if not shutil.which('javac') or not shutil.which('java'):
        pytest.skip('JDK required')
    jar = _jar_path()
    subprocess.run(['javac', '--release', '8', '-cp', str(jar), '-d', str(tmp_path),
                    str(Path(__file__).parent / 'java/XmlAttributeRegression.java')], check=True)
    output = tmp_path / 'metadata.xml'
    subprocess.run(['java', '-cp', os.pathsep.join([str(tmp_path), str(jar)]),
                    'XmlAttributeRegression', str(output)], check=True)
    root = ET.parse(output).getroot()
    assert root.find('{*}subList').get('metatag') == '{"name":"A&B <C> &quot;"}\t\n\r'
