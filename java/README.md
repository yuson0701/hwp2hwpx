# Bundled hwplib image-compression fix

The Python package ships a fat JAR containing hwplib 1.1.10. Its
`HWPReader.getCompressMethod(id)` used `DocInfo.getBinDataList().get(id - 1)`.
The storage ID in `BINxxxx.ext` need not equal the record's position in DocInfo:
records may be reordered, and IDs may have gaps. With mixed compression flags,
the old lookup can leave compressed images undecoded or try to inflate raw
JPEG/PNG bytes. Conversion may still report success while emitting broken images.

This fork looks up the non-link BinData record by `getBinDataID()` and preserves
the existing storage-default fallback when no record matches. The fix happens
before conversion, not by replacing image bytes after writing the HWPX.

## Source and build

`src/kr/dogfoot/hwplib/reader/HWPReader.java` comes from the Apache-2.0 licensed
[hwplib 1.1.10 source archive](https://repo.maven.apache.org/maven2/kr/dogfoot/hwplib/1.1.10/hwplib-1.1.10-sources.jar).
Only `getCompressMethod` is changed. See the repository LICENSE and NOTICE.

From the repository root, with Python 3.8+ and JDK 9+:

```sh
python scripts/rebuild_java_patch.py
```

The script compiles against the existing fat JAR with `--release 8` and replaces
the vendored `HWPReader` and `ForTable` classes and their enum-switch companions.
It needs no Maven, network access, or new runtime dependency. Normal users still
need only a Java runtime. Different JDK compilers may produce different class
bytes; the source, target level, and unchanged JAR entries are auditable.

## Regression tests

```sh
python -m pip install -e '.[test]'
python -m pytest
```

The integration tests generate minimal HWP compound documents locally. They cover
ordered and reordered/sparse IDs with raw, explicitly compressed, and default
compression, under both document-wide compression settings. They check the reader
and then the public Python conversion API, asserting exact PNG bytes in HWPX.
They load the actual bundled JAR and run on Linux, Windows, and macOS in CI.
No private/user documents are included. Java integration tests skip locally if
no JDK is available; CI installs one explicitly.

## Nested-table context fix (post3)

`src/kr/dogfoot/hwp2hwpx/section/object/ForTable.java` is from
https://github.com/neolord0/hwp2hwpx/blob/main/src/main/java/kr/dogfoot/hwp2hwpx/section/object/ForTable.java
(Apache-2.0). Its conversion logic matches the previously bundled class.
The modification saves `table` and `hwpTable` on entry and restores them in a
`finally` block. `trs()` calls the cell converter, which can recursively invoke
the same converter for nested tables. Without restoration, the next parent row
is appended to the most recently converted child.

Synthetic integration tests cover zero through three levels of nesting and
check both row counts and the owning cells' text. With the previous JAR, depths
2 and 3 fail; with the patch all four pass. No count rewriting is performed.
