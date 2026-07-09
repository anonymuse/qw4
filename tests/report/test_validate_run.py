#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools" / "report"))

import validate_run
import summarize_phase0


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

    def mutate_events_jsonl(self, run_dir: Path, mutator) -> None:
        path = run_dir / "events.jsonl"
        events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        events = mutator(events)
        path.write_text("\n".join(json.dumps(event, sort_keys=True) for event in events) + "\n", encoding="utf-8")

    def mutate_csv(self, run_dir: Path, name: str, mutator) -> None:
        path = run_dir / name
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = list(reader.fieldnames or [])
            rows = list(reader)
        rows = mutator(rows)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def test_fixture_is_valid(self) -> None:
        validate_run.validate_artifact_set(FIXTURE)

    def test_summary_marks_fixture_predictions_as_local_report_plumbing(self) -> None:
        summary, exit_code = summarize_phase0.run_summary(FIXTURE)
        self.assertEqual(exit_code, 0)
        self.assertIn("| Validity | loopback-only |", summary)
        self.assertIn("transport-derived upper-bound simulations", summary)
        self.assertIn("not final model throughput claims", summary)
        self.assertIn("not target A/B/C hardware evidence", summary)
        self.assertIn("report-plumbing signals only", summary)

    def test_summary_requires_confirmed_hardware_interpretation_for_cluster_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_raw:
            run_dir = self.copy_fixture(Path(tmp_raw))

            def mutate(data):
                data["environment"]["network_path"] = "Thunderbolt Bridge"
                data["environment"]["transport_mode"] = "real_cluster"
                data["environment"]["socket_mode"] = "tcp_network"
                data["environment"]["loopback"] = False
                data["environment"]["hardware_interpretable"] = False
                data["environment"]["confirmed_network_path"] = ""
                data["scenario"]["kind"] = "real_cluster"

            self.mutate_run_json(run_dir, mutate)
            summary, exit_code = summarize_phase0.run_summary(run_dir)
            self.assertEqual(exit_code, 0)
            self.assertIn("| Validity | not hardware-interpretable |", summary)
            self.assertIn("not hardware-interpretable target A/B/C evidence", summary)

            def mark_confirmed(data):
                data["environment"]["hardware_interpretable"] = True
                data["environment"]["confirmed_network_path"] = "Thunderbolt Bridge"

            self.mutate_run_json(run_dir, mark_confirmed)
            summary, exit_code = summarize_phase0.run_summary(run_dir)
            self.assertEqual(exit_code, 0)
            self.assertIn("| Validity | hardware-cluster |", summary)
            self.assertIn("does not measure final model performance", summary)

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

    def test_concurrent_link_interference_requires_degradation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_raw:
            run_dir = self.copy_fixture(Path(tmp_raw))

            def mutate(data):
                data["metrics"]["concurrent_link_interference"][0].pop("degradation_pct")

            self.mutate_run_json(run_dir, mutate)
            with self.assertRaises(validate_run.ValidationError):
                validate_run.validate_artifact_set(run_dir)

    def test_latency_metrics_must_cover_each_worker_pair_and_message_size(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_raw:
            run_dir = self.copy_fixture(Path(tmp_raw))

            def mutate(data):
                data["metrics"]["latency_by_message_size"] = [
                    row
                    for row in data["metrics"]["latency_by_message_size"]
                    if not (row["node_pair"] == "A-C" and row["message_size_bytes"] == 65536)
                ]

            self.mutate_run_json(run_dir, mutate)
            with self.assertRaises(validate_run.ValidationError):
                validate_run.validate_artifact_set(run_dir)

    def test_throughput_csv_requires_concurrent_a_b_a_c_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_raw:
            run_dir = self.copy_fixture(Path(tmp_raw))

            self.mutate_csv(
                run_dir,
                "throughput.csv",
                lambda rows: [row for row in rows if row["concurrent_links"] == "none"],
            )
            with self.assertRaises(validate_run.ValidationError):
                validate_run.validate_artifact_set(run_dir)

    def test_decode_projection_requires_formula_inputs_for_each_remote_rate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_raw:
            run_dir = self.copy_fixture(Path(tmp_raw))

            def mutate(data):
                data["metrics"]["predicted_upper_bound_tokens_per_sec"][2].pop("simulated_transport_time_us_per_token")

            self.mutate_run_json(run_dir, mutate)
            with self.assertRaises(validate_run.ValidationError):
                validate_run.validate_artifact_set(run_dir)

    def test_checksum_failure_count_requires_failed_checksum_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_raw:
            run_dir = self.copy_fixture(Path(tmp_raw))

            def mutate(data):
                data["checksums"]["passed"] = 79
                data["checksums"]["failed"] = 1
                data["checksums"]["status"] = "fail"

            self.mutate_run_json(run_dir, mutate)
            with self.assertRaises(validate_run.ValidationError):
                validate_run.validate_artifact_set(run_dir)

    def test_worker_health_is_required_for_each_worker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_raw:
            run_dir = self.copy_fixture(Path(tmp_raw))

            self.mutate_events_jsonl(
                run_dir,
                lambda events: [
                    event
                    for event in events
                    if not (event["event_type"] == "worker_health" and event.get("node_id") == "C")
                ],
            )
            with self.assertRaises(validate_run.ValidationError):
                validate_run.validate_artifact_set(run_dir)

    def test_hardware_interpretable_run_requires_confirmed_real_cluster_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_raw:
            run_dir = self.copy_fixture(Path(tmp_raw))

            def mutate(data):
                data["environment"]["network_path"] = "Thunderbolt Bridge"
                data["environment"]["transport_mode"] = "real_cluster"
                data["environment"]["socket_mode"] = "tcp_network"
                data["environment"]["hardware_interpretable"] = True
                data["environment"].pop("confirmed_network_path", None)
                data["scenario"]["kind"] = "real_cluster"

            self.mutate_run_json(run_dir, mutate)
            with self.assertRaises(validate_run.ValidationError):
                validate_run.validate_artifact_set(run_dir)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
