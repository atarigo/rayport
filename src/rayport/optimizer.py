import shutil
import subprocess
from pathlib import Path

from rayport.packager import inspect_game

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


def optimize_assets(source_dir: str, output_dir: str, exclude=(), include=()) -> None:
    source_path = Path(source_dir).resolve()
    output_path = Path(output_dir).resolve()

    for decision in inspect_game(str(source_path), exclude=exclude, include=include):
        if not decision.included:
            continue
        src = source_path / decision.path
        dst = output_path / decision.path
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
