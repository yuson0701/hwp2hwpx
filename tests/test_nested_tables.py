"""Nested-table regression using synthetic HWP documents, never user files."""
import os
import shutil
import subprocess
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

import pytest
from hwp2hwpx.converter import convert, _jar_path


@pytest.mark.parametrize('depth', [0, 1, 2, 3, 4, 5, 8, 10, 20])
def test_nested_rows_stay_with_their_parent(tmp_path, depth):
    if not shutil.which('javac') or not shutil.which('java'):
        pytest.skip('JDK required')
    jar = _jar_path()
    fixture = Path(__file__).parent / 'java/NestedTableRegression.java'
    subprocess.run(['javac', '--release', '8', '-cp', str(jar), '-d', str(tmp_path), str(fixture)], check=True)
    source = tmp_path / 'nested.hwp'
    subprocess.run(['java', '-cp', os.pathsep.join([str(tmp_path), str(jar)]),
                    'NestedTableRegression', str(source), str(depth)], check=True)
    with ZipFile(convert(source)) as z:
        root = ET.fromstring(z.read('Contents/section0.xml'))
    tables = list(root.iter('{http://www.hancom.co.kr/hwpml/2011/paragraph}tbl'))
    assert len(tables) == depth + 1
    for level, table in enumerate(tables):
        rows = table.findall('{*}tr')
        expected = 3 if level == 0 else 2
        assert int(table.get('rowCnt')) == len(rows) == expected
        for index, row in enumerate(rows):
            cell = row.find('{*}tc')
            assert int(cell.find('{*}cellAddr').get('rowAddr')) == index
            # Direct text only: a child's content must not masquerade as its parent's.
            text = ''.join(t.text or '' for t in cell.findall('{*}subList/{*}p/{*}run/{*}t'))
            assert f'table-{100 + level}-row-{index}' in text


@pytest.mark.parametrize('siblings', [2, 3, 5, 10])
def test_sibling_tables_and_parent_text_survive_recursion(tmp_path, siblings):
    if not shutil.which('javac') or not shutil.which('java'):
        pytest.skip('JDK required')
    jar = _jar_path()
    fixtures = Path(__file__).parent / 'java'
    subprocess.run(['javac', '--release', '8', '-cp', str(jar), '-d', str(tmp_path),
                    str(fixtures / 'NestedTableRegression.java'),
                    str(fixtures / 'ParagraphContextRegression.java')], check=True)
    source = tmp_path / 'siblings.hwp'
    subprocess.run(['java', '-cp', os.pathsep.join([str(tmp_path), str(jar)]),
                    'ParagraphContextRegression', str(source), str(siblings)], check=True)
    with ZipFile(convert(source)) as z:
        root = ET.fromstring(z.read('Contents/section0.xml'))
    tables = list(root.iter('{http://www.hancom.co.kr/hwpml/2011/paragraph}tbl'))
    assert len(tables) == siblings + 1
    parent = tables[0].find('{*}tr/{*}tc/{*}subList/{*}p')
    children = parent.findall('{*}run/{*}tbl')
    assert len(children) == siblings
    assert [int(t.get('rowCnt')) for t in children] == [2] + [1] * (siblings - 1)
    text = ''.join(t.text or '' for t in parent.findall('{*}run/{*}t'))
    assert 'BETWEEN_TABLES' in text and 'AFTER_TABLES' in text
    for i in range(1, siblings):
        assert f'BETWEEN_TABLES_{i}' in text
        assert f'table-{199+i}-row-0' in ''.join(children[i].itertext())
    for child in children:
        assert 'BETWEEN_TABLES' not in ''.join(child.itertext())
        assert 'AFTER_TABLES' not in ''.join(child.itertext())
