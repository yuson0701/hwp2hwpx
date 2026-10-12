# hwp2hwpx

## Compatibility fixes in this fork (1.0.1.post4)

This fork fixes corrupted images when HWP BinData records are out of storage-ID
order. The bundled Java reader now matches compression flags by the actual
storage ID. Mixed compressed BMP and uncompressed PNG/JPEG data are preserved.
See [the Java patch and regression tests](java/README.md).

Nested tables are now converted with their parent context restored after each
recursive conversion. Previously a later parent row could be appended to a
nested child table, leaving both tables inconsistent. This fix is in the bundled
Java converter, and preserves row ownership rather than changing declared counts.

Paragraph conversion now restores the parent paragraph, run, and text-buffer
state after recursively converting embedded content. This prevents an
IndexOutOfBoundsException or skipped sibling objects after a nested table.

The Python CLI/API also normalizes the Java output before publishing it:

- Remove cached `hp:linesegarray` data so Hangul recalculates line positions.
  Stale caches caused macOS Hangul to reject a document as damaged or modified.
- Repair the observed missing semicolon in `&quot` at an attribute boundary.
- Parse every XML/HPF entry and reject remaining XML errors before replacing
  the destination. Image bytes and other document content are preserved.

Line and page breaks can change when Hangul recalculates the layout, especially
with different installed fonts. These additional fixes run in the Python
wrapper; invoking the bundled JAR directly does not apply them.

Install this fork in your Python virtual environment:

```sh
python -m pip install --upgrade "git+https://github.com/yuson0701/hwp2hwpx.git"
```

The CLI and Python API are unchanged. Java is still required. This fixes the
identified image-compression bug; it does not guarantee identical page layout
for every HWP document.


[![CI](https://github.com/kossembly-dot/hwp2hwpx/actions/workflows/ci.yml/badge.svg)](https://github.com/kossembly-dot/hwp2hwpx/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/hwp2hwpx)](https://pypi.org/project/hwp2hwpx/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

Convert HWP files to HWPX format — the only `pip install`-able HWP→HWPX converter.

HWP is the legacy binary format used by [Hangul (한글)](https://www.hancom.com/), the dominant word processor in South Korea. HWPX is the modern XML-based format (OWPML/ODF-like ZIP archive). This package converts between them programmatically — no Hangul installation or GUI required.

[🇰🇷 한국어](#한국어)

## Why?

| Tool | What it does | Limitation |
|------|-------------|------------|
| **Hangul GUI** | Open HWP → Save As HWPX | Manual, not scriptable |
| **HwpxConverter.exe** | Bundled with Hangul, GUI only | No CLI, Windows only |
| **kordoc** | Parses HWP → Markdown/JSON | Extracts *content*, doesn't convert *format* |
| **hwp2hwpx** ← this | Converts HWP → HWPX (valid ZIP/XML) | Needs Java runtime |

If you need to **read** HWP content → use [kordoc](https://github.com/chrisryugj/kordoc).
If you need a **real HWPX file** you can open/edit in Hangul → use this.

## Install

```bash
pip install hwp2hwpx
```

Requires Java Runtime (JRE) 8+:

```bash
# Windows
winget install EclipseAdoptium.Temurin.21.JDK

# macOS
brew install temurin

# Linux (Debian/Ubuntu)
apt install default-jre
```

## Usage

### CLI

```bash
# Single file
hwp2hwpx document.hwp

# Multiple files
hwp2hwpx *.hwp

# Output directory
hwp2hwpx document.hwp -o output/

# Recursive folder conversion
hwp2hwpx ./documents/ -r
```

### Python API

```python
from hwp2hwpx import convert, convert_batch

# Single file
output_path = convert("document.hwp")
output_path = convert("document.hwp", "output.hwpx")

# Batch
results = convert_batch(["a.hwp", "b.hwp"], output_dir="output/")
for input_path, output_path, error in results:
    if error:
        print(f"FAIL: {input_path}: {error}")
    else:
        print(f"OK: {output_path}")
```

## How it works

Bundles [neolord0/hwp2hwpx](https://github.com/neolord0/hwp2hwpx) Java library as a fat JAR:
- **hwplib** — reads HWP binary (OLE2/CFB compound document)
- **hwpxlib** — writes HWPX XML (ZIP archive with OWPML structure)

Pure file-format conversion. No Hangul installation, no COM API, no DRM issues.

Korean file paths on Windows are automatically handled via temp-file workaround (JVM encoding issue bypass).

## Development

```bash
pip install -e ".[test]"
pytest
```

## License

Apache License 2.0

Based on Java libraries by [neolord0](https://github.com/neolord0):
- [hwp2hwpx](https://github.com/neolord0/hwp2hwpx)
- [hwplib](https://github.com/neolord0/hwplib)
- [hwpxlib](https://github.com/neolord0/hwpxlib)

---

## 한국어

HWP(한글 워드프로세서) 파일을 HWPX(OWPML) 형식으로 변환하는 Python 패키지.

`pip install hwp2hwpx` 한 줄로 설치, 바로 사용. 한글 프로그램 설치 불필요.

### 설치

```bash
pip install hwp2hwpx
```

Java 필요: `winget install EclipseAdoptium.Temurin.21.JDK`

### 사용법

```bash
hwp2hwpx 문서.hwp
hwp2hwpx *.hwp -o 출력폴더/
```

```python
from hwp2hwpx import convert
convert("문서.hwp")
```

### kordoc과의 차이

- **kordoc**: HWP를 **읽어서** 마크다운/JSON으로 추출 (텍스트 파싱)
- **hwp2hwpx**: HWP를 **HWPX 파일로 변환** (한글에서 열 수 있는 완전한 문서)
