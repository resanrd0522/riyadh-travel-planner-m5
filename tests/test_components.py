
"""Offline component tests for the preserved baseline tools and datasets.

These tests do not execute the baseline notebook or call Gemini.
"""

import hashlib
import unittest

import pandas as pd

from m5eval import baseline_tools as tools
from m5eval.evaluate import ROOT


# SHA-256 hashes of the original CSV files recorded in
# audit/import_manifest.json.
EXPECTED_DATASET_HASHES = {
    "activities": (
        "df5abb1fbb5fe13e0e8f20776fc83f707"
        "f2d7bf5e610a36acedb06cffa76d01f"
    ),
    "restaurants": (
        "2f808d6007d026b3c11b38ea9c92256"
        "0b97920f3da82020b3662b24313c63cbc"
    ),
    "hotels": (
        "910e7b6055b37fd76c0aec254e4e8f5c"
        "f9a6028735096a112f512f3c715ae878"
    ),
}


class ComponentTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Load the original datasets for offline component testing."""
        cls.dataset_paths = {}

        for name in ("activities", "restaurants", "hotels"):
            path = ROOT / "data" / f"{name}.csv"

            if not path.is_file():
                raise FileNotFoundError(
                    f"Required dataset is missing: {path}. "
                    "Restore the unchanged original CSV before testing."
                )

            cls.dataset_paths[name] = path

            setattr(
                tools,
                name,
                pd.read_csv(path)
            )

    def test_activity_exclusion_and_zero_candidates(self):
        ids = tools.activities.loc[
            tools.activities["interest_group"] == "Sports",
            "place_id"
        ].tolist()

        self.assertEqual(len(ids), 4)

        self.assertEqual(
            tools.search_activities(
                ["Sports"],
                limit=30,
                exclude_ids=ids
            ),
            []
        )

        remaining = tools.search_activities(
            ["Sports"],
            limit=30,
            exclude_ids=ids[:1]
        )

        self.assertEqual(
            {row["place_id"] for row in remaining},
            set(ids[1:])
        )

    def test_budget_exclusion(self):
        rows = tools.find_restaurants("Low")

        excluded = [
            row["place_id"]
            for row in rows
        ]

        result = tools.search_restaurants(
            "Low",
            limit=10,
            exclude_ids=excluded
        )

        self.assertEqual(len(result), 10)

        self.assertFalse(
            set(excluded)
            & {row["place_id"] for row in result}
        )

        self.assertTrue(
            all(
                row["budget_level"] == "Low"
                for row in result
            )
        )

    def test_invalid_tool_inputs(self):
        invalid_calls = (
            lambda: tools.find_hotels("Unknown"),
            lambda: tools.find_restaurants("Unknown"),
            lambda: tools.find_activities(["Unknown"]),
            lambda: tools.find_activities([]),
            lambda: tools.find_hotels("Low", limit=0),
        )

        for call in invalid_calls:
            with self.subTest(call=call):
                with self.assertRaises(ValueError):
                    call()

    def test_original_dataset_file_hashes(self):
        """Verify original CSV bytes, not reconstructed DataFrame hashes."""

        for name, expected_hash in EXPECTED_DATASET_HASHES.items():
            with self.subTest(dataset=name):
                path = self.dataset_paths[name]

                digest = hashlib.sha256(
                    path.read_bytes()
                ).hexdigest()

                self.assertEqual(
                    digest,
                    expected_hash,
                    f"Dataset integrity mismatch: {name}"
                )

    def test_activity_search_respects_limit_and_interests(self):
        results = tools.search_activities(
            ["Shopping"],
            limit=5
        )

        self.assertLessEqual(len(results), 5)

        self.assertTrue(
            all(
                row["interest_group"] == "Shopping"
                for row in results
            )
        )

        self.assertEqual(
            len({row["place_id"] for row in results}),
            len(results)
        )

    def test_restaurant_search_respects_budget_and_limit(self):
        for budget in tools.BUDGET_OPTIONS:
            with self.subTest(budget=budget):
                results = tools.search_restaurants(
                    budget,
                    limit=5
                )

                self.assertLessEqual(len(results), 5)

                self.assertTrue(
                    all(
                        row["budget_level"] == budget
                        for row in results
                    )
                )

    def test_hotel_search_respects_budget_and_limit(self):
        for budget in tools.BUDGET_OPTIONS:
            with self.subTest(budget=budget):
                results = tools.search_hotels(
                    budget,
                    limit=5
                )

                self.assertLessEqual(len(results), 5)

                self.assertTrue(
                    all(
                        row["budget_level"] == budget
                        for row in results
                    )
                )

    def test_search_results_are_deterministic(self):
        """Identical inputs must produce identical ordered results."""

        first_activities = tools.search_activities(
            ["Culture & History"],
            limit=10
        )
        second_activities = tools.search_activities(
            ["Culture & History"],
            limit=10
        )

        pd.testing.assert_frame_equal(
            pd.DataFrame(first_activities),
            pd.DataFrame(second_activities),
            check_exact=True,
            check_like=False
        )

        first_restaurants = tools.search_restaurants(
            "Medium",
            limit=10
        )
        second_restaurants = tools.search_restaurants(
            "Medium",
            limit=10
        )

        self.assertEqual(
            first_restaurants,
            second_restaurants
        )

        first_hotels = tools.search_hotels(
            "High",
            limit=5
        )
        second_hotels = tools.search_hotels(
            "High",
            limit=5
        )

        self.assertEqual(
            first_hotels,
            second_hotels
        )

if __name__ == "__main__":
    unittest.main()

