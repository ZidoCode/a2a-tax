"""Tests for a2a-tax — deterministic token math, no network."""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import a2a_tax as t


class TestTokenizer(unittest.TestCase):
    def test_empty_is_zero(self):
        self.assertEqual(t.est_tokens(""), 0)
        self.assertEqual(t.est_tokens(None), 0)

    def test_chars_over_four(self):
        self.assertEqual(t.est_tokens("x" * 40), 10)

    def test_floor_of_one(self):
        self.assertEqual(t.est_tokens("ab"), 1)

    def test_json_compact(self):
        self.assertEqual(t.est_json_tokens({"a": 1}), t.est_tokens('{"a":1}'))


class TestCardScan(unittest.TestCase):
    def setUp(self):
        self.card = {
            "name": "demo",
            "description": "does demo things",
            "version": "1.0.0",
            "protocolVersion": "0.2.9",
            "url": "https://demo.example.com",
            "capabilities": {"streaming": True},
            "skills": [
                {"id": "s1", "name": "Skill one", "description": "d" * 80, "tags": ["a"]},
                {"id": "s2", "name": "Skill two", "description": "e" * 40, "tags": ["b"]},
            ],
        }

    def test_total_positive(self):
        total, _ = t.scan_card(self.card)
        self.assertGreater(total, 0)

    def test_skills_dominated(self):
        _, br = t.scan_card(self.card)
        skills_t = sum(i["tokens"] for i in br["skills"]["items"])
        self.assertEqual(br["skills"]["count"], 2)
        self.assertGreater(skills_t, br["capabilities"])

    def test_longer_skill_costs_more(self):
        _, br = t.scan_card(self.card)
        a, b = br["skills"]["items"]
        self.assertGreater(a["tokens"], b["tokens"])

    def test_no_security_fields(self):
        total, br = t.scan_card(self.card)
        self.assertNotIn("securitySchemes", br)

    def test_total_is_sum(self):
        total, br = t.scan_card(self.card)
        parts = sum(v for k, v in br.items() if k != "TOTAL"
                    and k != "skills") + sum(i["tokens"] for i in br["skills"]["items"])
        self.assertEqual(total, parts)


class TestEnvelope(unittest.TestCase):
    def test_grows_with_history(self):
        card = {"name": "x"}
        short = t.envelope_tokens(card, 5)
        long = t.envelope_tokens(card, 50)
        self.assertGreater(long, short)

    def test_cap_limits_history(self):
        card = {"name": "x"}
        uncapped = t.envelope_tokens(card, 50)
        capped = t.envelope_tokens(card, 50, cap=10)
        self.assertLess(capped, uncapped)

    def test_cap_floor(self):
        card = {"name": "x"}
        self.assertEqual(
            t.envelope_tokens(card, 50, cap=10),
            t.envelope_tokens(card, 10),
        )


class TestTaskModel(unittest.TestCase):
    def setUp(self):
        self.card = {"name": "x", "description": "y" * 40, "skills": []}

    def test_total_breaks_down(self):
        m = t.model_task(self.card, polls=10, history_len=20)
        expected = m["card_tokens"] + m["first_send_tokens"] + m["poll_tokens_each"] * (m["polls"] - 1)
        self.assertEqual(m["total"], expected)

    def test_more_polls_more_tax(self):
        a = t.model_task(self.card, polls=5, history_len=20)
        b = t.model_task(self.card, polls=45, history_len=50)
        self.assertGreater(b["total"], a["total"])


class TestReport(unittest.TestCase):
    def test_report_mentions_savings(self):
        card = {"name": "x", "description": "y" * 40, "skills": []}
        out = t.report(card, polls=10, history_len=30, price_per_mtok=3.0)
        self.assertIn("savings", out)
        self.assertIn("%", out)

    def test_fix_always_saves(self):
        card = {"name": "x", "description": "y" * 40, "skills": []}
        out = t.report(card, polls=10, history_len=30, price_per_mtok=3.0)
        pct = int(out.strip().split("savings")[1].split("(")[1].rstrip(")%\n"))
        self.assertGreater(pct, 50)


class TestFetchCard(unittest.TestCase):
    def test_loads_local_file(self):
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_card.json")
        card, src = t.fetch_card(p)
        self.assertEqual(card["name"], "travel-orchestrator")


if __name__ == "__main__":
    unittest.main()
