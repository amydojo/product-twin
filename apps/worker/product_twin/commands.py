from pathlib import Path


def safe_child(root: Path, candidate: Path) -> Path:
    root = root.resolve()
    candidate = candidate.resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError("path escapes working directory")
    return candidate


def blender_command(
    blender_bin: str,
    spec: Path,
    output: Path,
    script: Path,
    label: Path | None = None,
) -> list[str]:
    values = [spec, output, script, *([label] if label else [])]
    if any(chr(0) in str(value) for value in values):
        raise ValueError("NUL byte in path")
    command = [
        blender_bin,
        "--background",
        "--python",
        str(script),
        "--",
        "--spec",
        str(spec),
        "--output",
        str(output),
    ]
    if label is not None:
        command.extend(["--label", str(label)])
    return command
