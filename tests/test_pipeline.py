import json
import tempfile
import unittest
from pathlib import Path

from writing_zero_pipeline.genrm import evaluate_samples, predict_preference
from writing_zero_pipeline.handoff import build_handoff_plan, write_handoff_plan
from writing_zero_pipeline.learning_loop import build_learning_loop_report, write_learning_loop_report
from writing_zero_pipeline.sample_generator import generate_samples, read_jsonl, write_jsonl


class PipelineTest(unittest.TestCase):
    def test_generation_is_deterministic(self) -> None:
        first = generate_samples()
        second = generate_samples()
        self.assertEqual([sample.id for sample in first], [sample.id for sample in second])
        self.assertEqual(len(first), 6)

    def test_generated_samples_have_required_contract(self) -> None:
        sample = generate_samples()[0]
        self.assertIn(sample.preferred, {"a", "b"})
        self.assertTrue(sample.prompt)
        self.assertTrue(sample.rubric_id)
        self.assertEqual(sample.provenance["source"], "deterministic_mock_generator")

    def test_jsonl_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "samples.jsonl"
            write_jsonl(generate_samples(), path)
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual(len(rows), 6)
            self.assertEqual(len(read_jsonl(path)), 6)

    def test_mock_scorer_matches_reference_labels(self) -> None:
        samples = generate_samples()
        result = evaluate_samples(samples)
        self.assertEqual(result.correct_count, result.sample_count)
        self.assertEqual(result.accuracy, 1.0)
        self.assertTrue(all(predict_preference(sample) == sample.preferred for sample in samples))

    def test_handoff_plan_names_compute_gate(self) -> None:
        plan = build_handoff_plan()
        self.assertIn("paid compute", plan.compute_gate)
        self.assertIn("artifacts/samples.jsonl", plan.artifacts)
        self.assertGreaterEqual(len(plan.failure_modes), 3)

    def test_handoff_plan_json_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "compute_handoff.json"
            write_handoff_plan(path)
            data = json.loads(path.read_text())
            self.assertEqual(data["milestone"], "replace-mock-genrm-with-agreed-public-sources")
            self.assertIn("GenRM validation accuracy", data["metrics"])

    def test_learning_loop_covers_memory_kinds_and_dedups(self) -> None:
        samples = generate_samples()
        report = build_learning_loop_report(samples)
        self.assertEqual(
            report.memory_kinds,
            ["agent", "episodic", "fact", "procedural", "skill", "workflow"],
        )
        self.assertEqual(report.raw_event_count, len(samples) * 6)
        self.assertLess(report.deduped_event_count, report.raw_event_count)
        self.assertGreater(len(report.update_candidate_ids), 0)
        self.assertGreater(len(report.rejected_update_ids), 0)

    def test_learning_loop_json_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "learning_loop.json"
            write_learning_loop_report(generate_samples(), path)
            data = json.loads(path.read_text())
            self.assertEqual(
                set(data["memory_kinds"]),
                {"fact", "episodic", "procedural", "skill", "agent", "workflow"},
            )
            self.assertGreater(data["deduped_event_count"], 0)
            self.assertGreater(len(data["events"]), 0)


if __name__ == "__main__":
    unittest.main()
