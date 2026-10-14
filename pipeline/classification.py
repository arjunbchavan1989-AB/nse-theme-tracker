"""Industry metadata and official Nifty theme memberships. Never guess exposures."""
import json,logging,time
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from urllib.request import Request,urlopen
import pandas as pd
import yfinance as yf

HERE=Path(__file__).parent
PATH=HERE/"classifications.json"
THEMES={
 "Defence":"ind_niftyindiadefence_list.csv",
 "Railways PSU":"ind_niftyIndiaRailwaysPSU_list.csv",
 "EV & New-age Auto":"ind_niftyEv_NewAgeAutomotive_list.csv",
 "Tourism":"ind_niftyindiatourism_list.csv",
 "Capital Markets":"ind_niftyCapitalMarkets_list.csv",
 "Digital India":"ind_niftyindiadigital_list.csv",
 "Internet":"ind_niftyIndiaInternet_list.csv",
 "Manufacturing":"ind_niftyindiamanufacturing_list.csv",
 "Infrastructure":"ind_niftyinfralist.csv",
 "Infrastructure & Logistics":"ind_niftyIndiaInfrastructure_Logistics_list.csv",
 "Transportation & Logistics":"ind_niftytransportationandlogistics_list.csv",
 "Consumption":"ind_niftyconsumptionlist.csv",
 "New-age Consumption":"ind_niftyIndiaNewAgeConsumption_list.csv",
 "Non-cyclical Consumer":"ind_niftynon-cyclicalconsumer_list.csv",
 "Energy":"ind_niftyenergylist.csv",
 "Commodities":"ind_niftycommoditieslist.csv",
 "Housing":"ind_niftyhousing_list.csv",
 "Rural":"ind_niftyRural_list.csv",
 "Public Sector Enterprises":"ind_niftypselist.csv",
 "CPSE":"ind_niftycpselist.csv",
 "Mobility":"ind_niftymobility_list.csv",
}
LOG=logging.getLogger("classification")

def acquire(symbols,offline=False,preview=False):
    data=json.loads(PATH.read_text()) if PATH.exists() else {"industries":{},"themes":{}}
    now=datetime.now(timezone.utc);today=now.date().isoformat()
    # Provider taxonomies differ. Do not silently mix labels between providers.
    # The checked-in finance-provider taxonomy is the primary industry map.
    # Yahoo metadata fills ONLY missing mappings, with source and refresh date.
    missing=[s for s in symbols if not data["industries"].get(s,{}).get("industry")]
    def profile(s):
        try:
            p=yf.Ticker(s+".NS").get_info()
            if p.get("industry"):
                return s,dict(industry=p["industry"],sector=p.get("sector","Unclassified"),
                              source="Yahoo Finance industry (fallback)",date=today)
        except Exception:pass
        return s,None
    if not offline and missing:
        with ThreadPoolExecutor(max_workers=4) as pool:
            for s,p in pool.map(profile,missing):
                if p:data["industries"][s]=p
    def theme(item):
        name,filename=item;old=data["themes"].get(name)
        # Daily fresh official membership; last verified own cache <=14 days on failure.
        url="https://www.niftyindices.com/IndexConstituent/"+filename
        for host in ("https://www.niftyindices.com/IndexConstituent/","https://niftyindices.com/IndexConstituent/","https://nsearchives.nseindia.com/content/indices/"):
            try:
                with urlopen(Request(host+filename,headers={"User-Agent":"Mozilla/5.0"}),timeout=15) as r:raw=r.read()
                f=pd.read_csv(BytesIO(raw));f.columns=f.columns.str.strip()
                if not {"Symbol","Company Name"}.issubset(f.columns) or len(f)<3:raise ValueError("Invalid constituent CSV")
                members=sorted(set(f.Symbol.dropna().astype(str).str.strip()))
                if len(members)!=len(f):raise ValueError("Duplicate/empty members")
                return name,dict(symbols=members,url=url,date=today,status="Fresh official constituents")
            except Exception:pass
        if old and (now.date()-datetime.fromisoformat(old["date"]).date()).days<=14:
            return name,{**old,"status":"Cached official constituents"}
        return name,None
    failed=[]
    if not offline:
        with ThreadPoolExecutor(max_workers=4) as pool:
            for name,t in pool.map(theme,THEMES.items()):
                if t:data["themes"][name]=t
                else:data["themes"].pop(name,None);failed.append(name)
        if len(data["themes"])<max(10,len(THEMES)*.7):
            raise RuntimeError("Fewer than 70% of configured official themes available; retaining last good snapshot")
        PATH.write_text(json.dumps(data,indent=2,sort_keys=True))
    classified=sum(bool(data["industries"].get(s,{}).get("industry")) for s in symbols)
    health=dict(classified=classified,total=len(symbols),coverage_pct=round(100*classified/max(len(symbols),1),2),
                unclassified=[s for s in symbols if not data["industries"].get(s,{}).get("industry")],
                official_themes_available=len(data["themes"]),configured_themes=len(THEMES),
                unavailable_themes=failed,industry_source="Finance provider industry taxonomy; labelled Yahoo fallback for missing names",
                industry_maintenance="Primary classifications are versioned metadata; missing symbols enriched each run. Review primary classifications periodically.",
                taxonomy_note="Provider industry labels are not the official NSE four-tier industry classification.")
    if classified/max(len(symbols),1)<(.9 if preview else .95):raise RuntimeError("Industry classification coverage below required threshold")
    return data,health
