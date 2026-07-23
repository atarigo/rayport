from __future__ import annotations

import argparse
from email.parser import BytesParser
from email.policy import default
from pathlib import Path
import tarfile
import zipfile


RUNTIME_FILENAMES = ("main.wasm", "main.js", "main.data")


def matching_paths(paths: list[str], filenames: tuple[str, ...]) -> list[str]:
    return sorted(path for path in paths if path.endswith(tuple(f"/{name}" for name in filenames)))


def expected_license_names(repository: Path) -> set[str]:
    return {
        "LICENSE",
        "THIRD_PARTY_NOTICES.md",
        *(f"third_party_licenses/{path.name}" for path in (repository / "third_party_licenses").glob("*.txt")),
    }


def check_wheel(path: Path, expected_licenses: set[str]) -> None:
    with zipfile.ZipFile(path) as archive:
        corrupt_member = archive.testzip()
        if corrupt_member is not None:
            raise AssertionError(f"Corrupt wheel member: {corrupt_member}")
        names = archive.namelist()
        runtime = matching_paths(names, RUNTIME_FILENAMES)
        expected_runtime = [f"rayport/runtime/{name}" for name in sorted(RUNTIME_FILENAMES)]
        if runtime != expected_runtime:
            raise AssertionError(f"Unexpected wheel runtime files: {runtime}")

        packaged_licenses = {
            name.split(".dist-info/licenses/", 1)[1]
            for name in names
            if ".dist-info/licenses/" in name
        }
        if packaged_licenses != expected_licenses:
            raise AssertionError(
                f"Unexpected wheel licenses: {sorted(packaged_licenses ^ expected_licenses)}"
            )

        metadata_name = next(name for name in names if name.endswith(".dist-info/METADATA"))
        metadata = BytesParser(policy=default).parsebytes(archive.read(metadata_name))
        if metadata["Name"] != "rayport":
            raise AssertionError(f"Unexpected package name: {metadata['Name']}")
        if metadata["Author"] != "wenke.studio":
            raise AssertionError(f"Unexpected author: {metadata['Author']}")
        if metadata.get_all("Requires-Dist"):
            raise AssertionError(f"Unexpected runtime dependencies: {metadata.get_all('Requires-Dist')}")


def check_sdist(path: Path, expected_licenses: set[str]) -> None:
    with tarfile.open(path, "r:gz") as archive:
        names = archive.getnames()
        root = names[0].split("/", 1)[0]
        runtime = matching_paths(names, RUNTIME_FILENAMES)
        expected_runtime = [
            f"{root}/src/rayport/runtime/{name}"
            for name in sorted(RUNTIME_FILENAMES)
        ]
        if runtime != expected_runtime:
            raise AssertionError(f"Unexpected sdist runtime files: {runtime}")

        packaged_licenses = {
            name.removeprefix(f"{root}/")
            for name in names
            if name.removeprefix(f"{root}/") in expected_licenses
        }
        if packaged_licenses != expected_licenses:
            raise AssertionError(
                f"Unexpected sdist licenses: {sorted(packaged_licenses ^ expected_licenses)}"
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("wheel", type=Path)
    parser.add_argument("sdist", type=Path)
    args = parser.parse_args()

    repository = Path(__file__).resolve().parent.parent
    licenses = expected_license_names(repository)
    check_wheel(args.wheel, licenses)
    check_sdist(args.sdist, licenses)
    print(f"Distribution contents verified: {args.wheel.name}, {args.sdist.name}")


if __name__ == "__main__":
    main()
