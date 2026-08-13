import json

from flask_operations_dashboard_lab.cli import main


def test_cli_prints_summary(tmp_path, capsys) -> None:
    main(["--database", str(tmp_path / "ops.sqlite3")])

    payload = json.loads(capsys.readouterr().out)

    assert payload["open_total"] == 10
    assert payload["status_counts"]["resolved"] == 2

