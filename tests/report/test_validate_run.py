#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools" / "report"))

import validate_run


FIXTURE = REPO_ROOT / "tests" / "fixtures" / "artifacts" / "transport-smoke"


class ValidateRunTests(unittest.TestCase):
    def copy_fixture(self, tmp: Path) -> Path:
        run_dir = tmp / "transport-smoke"
        shutil.copytree(FIXTURE, run_dir)
        return run_dir

    def mutate_run_json(self, run_dir: Path, mutator) -> None:
        path = run_dir / "run.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        mutator(data)
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def test_fixture_is_valid(self) -> None:
        validate_run.validate_artifact_set(FIXTURE)

    def test_missing_network_path_is_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_raw:
            run_dir = self.copy_fixture(Path(tmp_raw))
            self.mutate_run_json(run_dir, lambda data: data["environment"].pop("network_path"))
            with self.assertRaises(validate_run.ValidationError):
                validate_run.validate_artifact_set(run_dir)

    def test_localhost_cannot_be_hardware_interpretable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_raw:
            run_dir = self.copy_fixture(Path(tmp_raw))

            def mutate(data):
                data["environment"]["network_path"] = "socket_localhost"
                data["environment"]["transport_mode"] = "socket_localhost"
                data["environment"]["socket_mode"] = "tcp_localhost"
                data["environment"]["hardware_interpretable"] = True
                data["scenario"]["kind"] = "socket_localhost"

            self.mutate_run_json(run_dir, mutate)
            with self.assertRaises(validate_run.ValidationError):
                validate_run.validate_artifact_set(run_dir)

    def test_socket_localhost_kind_is_allowed_when_marked_non_hardware(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_raw:
            run_dir = self.copy_fixture(Path(tmp_raw))

            def mutate(data):
                data["environment"]["network_path"] = "socket_localhost"
                data["environment"]["transport_mode"] = "socket_localhost"
                data["environment"]["socket_mode"] = "tcp_localhost"
                data["environment"]["hardware_interpretable"] = False
                data["scenario"]["kind"] = "socket_localhost"

            self.mutate_run_json(run_dir, mutate)
            validate_run.validate_artifact_set(run_dir)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
