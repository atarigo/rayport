import os
import shutil
import subprocess
from pathlib import Path

SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules", "build", ".mypy_cache", ".pytest_cache"}
PNG_EXTENSIONS = {".png"}
AUDIO_EXTENSIONS = {".wav", ".mp3"}

_warned_pngquant = False
_warned_ffmpeg = False


def _has_tool(name):
    return shutil.which(name) is not None


def _optimize_png(src: Path, dst: Path) -> bool:
    global _warned_pngquant
    if not _has_tool("pngquant"):
        if not _warned_pngquant:
            print("Warning: pngquant not found, PNG files will not be optimized")
            _warned_pngquant = True
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["pngquant", "--quality=65-80", "--force", "--output", str(dst), str(src)],
        capture_output=True,
    )
    if result.returncode != 0:
        shutil.copy2(src, dst)
    return result.returncode == 0


def _convert_audio(src: Path, dst: Path) -> bool:
    global _warned_ffmpeg
    if not _has_tool("ffmpeg"):
        if not _warned_ffmpeg:
            print("Warning: ffmpeg not found, audio files will not be converted")
            _warned_ffmpeg = True
        return False
    dst = dst.with_suffix(".ogg")
    dst.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["ffmpeg", "-i", str(src), "-c:a", "libvorbis", "-ar", "44100", "-ac", "1", "-q:a", "4", str(dst), "-y"],
        capture_output=True,
    )
    if result.returncode != 0:
        shutil.copy2(src, dst.with_suffix(src.suffix))
    return result.returncode == 0


def optimize_assets(source_dir: str, output_dir: str) -> None:
    source_path = Path(source_dir).resolve()
    output_path = Path(output_dir).resolve()

    for root, dirs, files in os.walk(source_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for filename in sorted(files):
            src = Path(root) / filename
            rel = src.relative_to(source_path)
            dst = output_path / rel
            ext = src.suffix.lower()

            if ext in PNG_EXTENSIONS:
                if not _optimize_png(src, dst):
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
            elif ext in AUDIO_EXTENSIONS:
                if not _convert_audio(src, dst):
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
