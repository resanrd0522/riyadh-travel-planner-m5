import json
import unittest

from m5eval.scoring import score_itinerary, tool_coverage


def fixture():
    datasets = {
        "activities": {"A1": {"interest_group": "Shopping"}, "A2": {"interest_group": "Shopping"},
                       "A3": {"interest_group": "Sports"}, "A4": {"interest_group": "Sports"}},
        "restaurants": {"R1": {"budget_level": "Low"}, "R2": {"budget_level": "High"}},
        "hotels": {"H1": {"budget_level": "Low"}, "H2": {"budget_level": "High"}},
    }
    case = {"case_id": "T1", "trip_duration": 1, "interests": ["Shopping"], "budget_level": "Low"}
    trip = {"hotel_id": "H1", "days": [{"day": 1, "activities": ["A1", "A2"], "restaurants": ["R1", "R1"]}]}
    return datasets, case, trip


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.datasets, self.case, self.trip = fixture()

    def score(self, value=None):
        return score_itinerary(self.trip if value is None else value, self.case, self.datasets)

    def test_valid_and_repeated_restaurants(self):
        result = self.score()
        self.assertEqual([result[k] for k in ("APM", "RBM", "HBM", "IFR")], [100]*4)

    def test_missing_activity_uses_required_denominator(self):
        self.trip["days"][0]["activities"].pop()
        result = self.score()
        self.assertEqual((result["APM"], result["RBM"], result["IFR"]), (50, 100, 0))

    def test_missing_day_uses_requested_duration(self):
        self.case["trip_duration"] = 2
        result = self.score()
        self.assertEqual((result["APM"], result["RBM"], result["IFR"]), (50, 50, 0))

    def test_wrong_budget(self):
        self.trip["hotel_id"] = "H2"
        self.trip["days"][0]["restaurants"] = ["R2", "R2"]
        result = self.score()
        self.assertEqual((result["RBM"], result["HBM"], result["IFR"]), (0, 0, 100))

    def test_nonmatching_activities_can_be_structurally_valid(self):
        self.trip["days"][0]["activities"] = ["A3", "A4"]
        result = self.score()
        self.assertEqual((result["APM"], result["IFR"]), (0, 100))

    def test_duplicate_activity_does_not_earn_double_credit(self):
        self.trip["days"][0]["activities"] = ["A1", "A1"]
        result = self.score()
        self.assertEqual((result["APM"], result["IFR"]), (50, 0))

    def test_duplicates_across_days(self):
        self.case["trip_duration"] = 2
        self.trip["days"].append({"day": 2, "activities": ["A1", "A2"], "restaurants": ["R1", "R1"]})
        result = self.score()
        self.assertEqual((result["APM"], result["IFR"]), (50, 0))

    def test_unknown_and_wrong_dataset_id(self):
        self.trip["days"][0]["activities"] = ["UNKNOWN", "R1"]
        result = self.score()
        self.assertEqual((result["APM"], result["IFR"]), (0, 0))

    def test_malformed_activity_ids_never_throw(self):
        for value in ({}, [], None, True, 7):
            with self.subTest(value=value):
                self.trip["days"][0]["activities"] = [value, "A1"]
                result = self.score()
                self.assertEqual((result["APM"], result["IFR"]), (50, 0))

    def test_extra_slots_cannot_replace_earlier_failures(self):
        self.trip["days"][0]["activities"] = ["UNKNOWN", "A1", "A2"]
        result = self.score()
        self.assertEqual((result["APM"], result["IFR"]), (50, 0))

    def test_extra_days_cannot_replace_earlier_failures(self):
        self.trip["days"][0]["activities"] = []
        self.trip["days"].append({"day": 2, "activities": ["A1", "A2"], "restaurants": ["R1", "R1"]})
        result = self.score()
        self.assertEqual((result["APM"], result["IFR"]), (0, 0))

    def test_bad_day_number_including_boolean(self):
        for number in (True, "1", 2, 1.0, None):
            with self.subTest(number=number):
                self.trip["days"][0]["day"] = number
                self.assertEqual(self.score()["IFR"], 0)

    def test_blank_malformed_and_wrong_top_level(self):
        for value in (None, "", "bad", "[]", [], 1, 'NaN', '{"days":NaN}', '{"hotel_id":"H1","hotel_id":"H2"}'):
            with self.subTest(value=value):
                result = score_itinerary(value, self.case, self.datasets)
                self.assertTrue(all(result[k] == 0 for k in ("APM", "RBM", "HBM", "IFR")))

    def test_bad_containers(self):
        for value in ({"days": None}, {"days": [None]}, {"days": [{"activities": {}, "restaurants": "R1"}]}):
            self.assertEqual(self.score(value)["IFR"], 0)

    def test_json_input_and_single_hotel(self):
        self.assertEqual(self.score(json.dumps(self.trip))["IFR"], 100)
        self.trip["hotel_id"] = ["H1", "H2"]
        self.assertEqual(self.score()["HBM"], 0)
        self.assertEqual(self.score()["IFR"], 0)

    def test_invalid_cases_are_configuration_errors(self):
        for duration in (0, -1, True, 1.5):
            self.case["trip_duration"] = duration
            with self.assertRaises(ValueError):
                self.score()

    def test_tool_coverage_is_not_call_count(self):
        self.assertEqual(tool_coverage(["find_hotels"]*5), 33.33)
        self.assertEqual(tool_coverage(["find_hotels", "find_activities", "find_restaurants", "unknown"]), 100)
        self.assertEqual(tool_coverage([{}, None]), 0)
        self.assertEqual(tool_coverage(None), 0)


if __name__ == "__main__":
    unittest.main()
