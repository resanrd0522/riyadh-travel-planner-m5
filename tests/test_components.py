import hashlib
import unittest

import pandas as pd

from m5eval import baseline_tools as tools
from m5eval.evaluate import ROOT, V2, read_json


class ComponentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for name in ("activities", "restaurants", "hotels"):
            setattr(tools, name, pd.read_csv(ROOT / "data" / f"{name}.csv"))

    def test_activity_exclusion_and_zero_candidates(self):
        ids = tools.activities.loc[tools.activities.interest_group == "Sports", "place_id"].tolist()
        self.assertEqual(len(ids), 4)
        self.assertEqual(tools.search_activities(["Sports"], limit=30, exclude_ids=ids), [])
        remaining = tools.search_activities(["Sports"], limit=30, exclude_ids=ids[:1])
        self.assertEqual({r["place_id"] for r in remaining}, set(ids[1:]))

    def test_budget_exclusion(self):
        rows = tools.find_restaurants("Low")
        excluded = [r["place_id"] for r in rows]
        result = tools.search_restaurants("Low", limit=10, exclude_ids=excluded)
        self.assertEqual(len(result), 10)
        self.assertFalse(set(excluded) & {r["place_id"] for r in result})
        self.assertTrue(all(r["budget_level"] == "Low" for r in result))

    def test_invalid_tool_inputs(self):
        for call in (lambda: tools.find_hotels("Unknown"), lambda: tools.find_restaurants("Unknown"),
                     lambda: tools.find_activities(["Unknown"]), lambda: tools.find_activities([]),
                     lambda: tools.find_hotels("Low", limit=0)):
            with self.assertRaises(ValueError):
                call()

    def test_round_trip_reader_reproduces_all_frozen_dataframe_hashes(self):
        reference = read_json(V2 / "baseline_v2_implementation_reference.json")
        for name in ("activities", "restaurants", "hotels"):
            with self.subTest(dataset=name):
                frame = pd.read_csv(ROOT / "data" / f"{name}.csv", float_precision="round_trip")
                digest = hashlib.sha256(frame.to_json(orient="split", date_format="iso", double_precision=15).encode()).hexdigest()
                self.assertEqual(digest, reference["datasets"][name]["sha256"])
