import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"pipeline"))
from leadership import groups,aggregate,pct
import pandas as pd

def row(s,i="Steel",value=10):
    return dict(symbol=s,industry=i,themes=["Defence"],d1=1,w1=2,m1=value,m3=20,rs_excess=5,
                above50=100,near_high=0,rvol=2,spark=[100]*64,score=80)

class LeadershipTests(unittest.TestCase):
    def test_missing_not_zero(self):
        self.assertIsNone(pct(pd.Series([10]*21),21))
    def test_exact_return(self):
        self.assertEqual(pct(pd.Series([100]*21+[110]),21),10)
    def test_small_unranked(self):
        gs=groups([row("A"),row("B")],{"themes":{}},{})
        self.assertIsNone(gs[0]["rank"])
    def test_three_ranked(self):
        gs=groups([row("A"),row("B"),row("C")],{"themes":{}},{})
        self.assertEqual(gs[0]["rank"],1)
    def test_equal_weight_not_cap_weighted(self):
        g=aggregate([row("A",value=0),row("B",value=20)],"industry","Steel",{})
        self.assertEqual(g["m1"],10)
    def test_max_ten_leaders(self):
        g=aggregate([row(str(i)) for i in range(20)],"industry","Steel",{})
        self.assertEqual(len(g["leaders"]),10)
    def test_unknown_not_grouped(self):
        self.assertEqual(groups([row("A","Unclassified")],{"themes":{}},{}),[])
    def test_short_history_coverage(self):
        rows=[row(str(i)) for i in range(5)]
        for r in rows[:2]:r["m3"]=None;r["rs_excess"]=None
        self.assertIsNone(groups(rows,{"themes":{}},{})[0]["rank"])
    def test_rank_delta(self):
        old={"groups":[{"id":"industry:Steel","rank":4}]}
        g=groups([row("A"),row("B"),row("C")],{"themes":{}},{},old)[0]
        self.assertEqual(g["rank_change"],3)
    def test_theme_members_can_overlap(self):
        rs=[row(str(i)) for i in range(3)]
        for r in rs:r["themes"].append("Energy")
        m={"themes":{k:{"url":"https://example.com","date":"2026-10-14"} for k in ("Defence","Energy")}}
        gs=groups(rs,m,{})
        self.assertEqual(len([g for g in gs if g["kind"]=="theme"]),2)
    def test_empty_official_theme_visible(self):
        gs=groups([],{"themes":{"Energy":{"url":"https://example.com","date":"2026-10-14"}}},{})
        self.assertEqual(gs[0]["count"],0)
        self.assertIsNone(gs[0]["score"])
