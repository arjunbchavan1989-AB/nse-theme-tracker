import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"pipeline"))
from classification import parse_members

class ClassificationTests(unittest.TestCase):
    def test_modern_csv(self):
        self.assertEqual(parse_members(b"Company Name,Symbol\nA,ABC\nB,M&M\nC,BAJAJ-AUTO\n"),["ABC","BAJAJ-AUTO","M&M"])
    def test_legacy_housing_csv(self):
        self.assertEqual(len(parse_members(b"Company,Industry,Symbol\nA,Cement,ABC\nB,Power,BBC\nC,Housing,CCC\n")),3)
    def test_duplicates_rejected(self):
        with self.assertRaises(ValueError):parse_members(b"Company,Symbol\nA,ABC\nB,ABC\nC,CCC\n")
    def test_html_rejected(self):
        with self.assertRaises(ValueError):parse_members(b"<html>Access denied</html>")
    def test_invalid_symbol_rejected(self):
        with self.assertRaises(ValueError):parse_members(b"Company,Symbol\nA,<script>\nB,BBB\nC,CCC\n")
