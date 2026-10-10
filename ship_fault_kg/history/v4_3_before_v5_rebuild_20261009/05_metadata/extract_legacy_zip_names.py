"""Extract a ZIP whose legacy Chinese filenames are encoded as GBK.

The source archive stores names without the UTF-8 flag. Python and Windows then
interpret those bytes as CP437. Re-encoding to CP437 and decoding as GBK restores
the original Chinese filenames without changing file contents.
"""

from pathlib import Path
import shutil
import sys
import zipfile


def decoded_name(info: zipfile.ZipInfo) -> str:
    if info.flag_bits & 0x800:
        return info.filename
    return info.filename.encode("cp437").decode("gbk")


def main() -> None:
    archive = Path(sys.argv[1]).resolve()
    destination = Path(sys.argv[2]).resolve()
    destination.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive) as source:
        for info in source.infolist():
            relative = Path(decoded_name(info))
            target = (destination / relative).resolve()
            if destination not in target.parents and target != destination:
                raise ValueError(f"Unsafe ZIP path: {relative}")
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with source.open(info) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)

    print(sum(1 for path in destination.rglob("*") if path.is_file()))


if __name__ == "__main__":
    main()
