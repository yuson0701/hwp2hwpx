"""Recompile the vendored hwplib reader into the bundled JAR (JDK 9+)."""
from pathlib import Path
import argparse
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def rebuild(jar: Path) -> None:
    javac = shutil.which("javac")
    if javac is None:
        raise RuntimeError("Rebuilding requires a JDK with javac (9 or newer)")
    sources = sorted((ROOT / "java" / "src").rglob("*.java"))
    with tempfile.TemporaryDirectory(prefix="hwp2hwpx-build-") as temp:
        classes = Path(temp) / "classes"
        classes.mkdir()
        subprocess.run([
            javac, "--release", "8", "-encoding", "UTF-8", "-cp", str(jar),
            "-d", str(classes), *map(str, sources),
        ], check=True)
        patches = {p.relative_to(classes).as_posix(): p.read_bytes()
                   for p in classes.rglob("*.class")}
        replacement = Path(temp) / "patched.jar"
        with zipfile.ZipFile(jar) as original, zipfile.ZipFile(replacement, "w") as output:
            if not patches.keys() <= set(original.namelist()):
                raise RuntimeError("Compiled classes do not match the bundled JAR")
            output.comment = original.comment
            for info in original.infolist():
                output.writestr(info, patches.get(info.filename, original.read(info.filename)))
        shutil.copyfile(replacement, jar)
    print("Updated " + ", ".join(sorted(patches)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jar", type=Path,
                        default=ROOT / "src/hwp2hwpx/jars/hwp2hwpx.jar")
    rebuild(parser.parse_args().jar.resolve())
