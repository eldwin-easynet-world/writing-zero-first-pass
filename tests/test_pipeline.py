import json
import tempfile
import unittest
from pathlib import Path

from writing_zero_pipeline.genrm import evaluate_samples, predict_preference
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


if __name__ == "__main__":
    unittest.main()

