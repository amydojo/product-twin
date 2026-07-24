from pathlib import Path
from unittest.mock import patch

from product_twin.cli import main


def test_render_fixture_cli_forwards_label(tmp_path: Path, monkeypatch) -> None:
    spec = tmp_path / "spec.json"
    label = tmp_path / "label.png"
    output = tmp_path / "output"
    spec.write_text("{}")
    label.write_bytes(b"png")
    monkeypatch.setattr(
        "sys.argv",
        [
            "product-twin",
            "render-fixture",
            "--spec",
            str(spec),
            "--label",
            str(label),
            "--output",
            str(output),
            "--no-fallback",
        ],
    )
    with patch("product_twin.cli.render_fixture", return_value={"ok": True}) as render:
        main()
    render.assert_called_once_with(spec, output, label=label, allow_fallback=False)
