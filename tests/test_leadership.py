import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"pipeline"))
from leadership import groups,aggregate,pct,stocks,above_sma50
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
        self.assertEqual(groups([row("A")],{"themes":{}},{}),[])
    def test_two_stock_industry_ranked(self):
        self.assertEqual(groups([row("A"),row("B")],{"themes":{}},{})[0]["rank"],1)
    def test_two_stock_theme_still_unranked(self):
        gs=groups([row("A"),row("B")],{"themes":{"Defence":{"url":"https://example.com","date":"2026-10-14"}}},{})
        self.assertIsNone(next(g for g in gs if g["kind"]=="theme")["rank"])
    def test_below_and_unknown_sma50_excluded(self):
        rs=[row("A"),row("B"),row("C"),row("D")]
        rs[2]["above50"]=0;rs[3]["above50"]=None
        self.assertEqual([r["symbol"] for r in above_sma50(rs)],["A","B"])
        g=groups(rs,{"themes":{}},{})[0]
        self.assertEqual(g["members"],["A","B"])
        self.assertAlmostEqual(g["above50"],66.6667,places=4)
        self.assertEqual(g["base_count"],4)
    def test_filtering_can_remove_one_stock_industry(self):
        rs=[row("A"),row("B")];rs[1]["above50"]=0
        self.assertEqual(groups(rs,{"themes":{}},{}),[])
    def test_trend_selection_reranks_only_qualified_stocks(self):
        rs=[row("A"),row("B")];rs[0]["above50"]=0
        selected=above_sma50(rs)
        self.assertEqual(len(selected),1)
        self.assertEqual(selected[0]["score"],100)
    def test_equal_close_to_sma50_fails(self):
        dates=pd.bdate_range("2026-01-01",periods=64)
        f=pd.DataFrame({"Close":[100]*64,"High":[105]*64,"Volume":[100000]*64},index=dates)
        b=pd.DataFrame({"close":[1000]*64},index=dates)
        rs=stocks({"rows":[{"symbol":"FLAT"}]},{"FLAT":f},b,{"industries":{},"themes":{}})
        self.assertEqual(rs[0]["above50"],0)
        self.assertEqual(above_sma50(rs),[])
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
    def test_short_history_stock_retained_unscored(self):
        dates=pd.bdate_range("2026-01-01",periods=30)
        f=pd.DataFrame({"Close":[100+i for i in range(30)],"High":[105+i for i in range(30)],"Volume":[100000]*30},index=dates)
        b=pd.DataFrame({"close":[1000+i for i in range(30)]},index=dates)
        rs=stocks({"rows":[{"symbol":"NEWIPO"}]},{"NEWIPO":f},b,{"industries":{},"themes":{}})
        self.assertEqual(len(rs),1)
        self.assertIsNone(rs[0]["score"])
        self.assertIsNone(rs[0]["m3"])
        self.assertEqual(rs[0]["industry"],"Unclassified")
    def test_stale_benchmark_rejected(self):
        dates=pd.bdate_range("2026-01-01",periods=30)
        f=pd.DataFrame({"Close":[100]*30,"High":[105]*30,"Volume":[100000]*30},index=dates)
        b=pd.DataFrame({"close":[1000]*29},index=dates[:-1])
        with self.assertRaises(ValueError):stocks({"rows":[{"symbol":"A"}]},{"A":f},b,{"industries":{},"themes":{}})
    def test_leader_score_ties_alphabetical(self):
        g=aggregate([row("Z"),row("A")],"industry","Steel",{})
        self.assertEqual(g["leaders"],["A","Z"])
    def test_group_score_bounds(self):
        rows=[row("A"),row("B"),row("C")]
        gs=groups(rows,{"themes":{}},{})
        self.assertTrue(0<=gs[0]["score"]<=100)
