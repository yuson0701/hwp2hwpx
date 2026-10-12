"""HWP to HWPX converter.

Python wrapper for neolord0/hwp2hwpx Java library (Apache-2.0).
Requires Java Runtime Environment (JRE) 8 or later.

Usage::

    from hwp2hwpx import convert

    output = convert("document.hwp")
    output = convert("document.hwp", "output.hwpx")

CLI::

    hwp2hwpx document.hwp
    hwp2hwpx *.hwp -o output_dir/
"""

from __future__ import annotations

__version__ = "1.0.1.post5"

from .converter import convert, convert_batch, check_java

__all__ = ["convert", "convert_batch", "check_java", "__version__"]
