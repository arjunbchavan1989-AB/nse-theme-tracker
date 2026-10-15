import type {Snapshot} from "../../shared/schema";

export function assertCurrentSnapshot(value:unknown):asserts value is Snapshot{
 const p=value as Snapshot;
 if(!p||p.schema_version!==1||!Array.isArray(p.stocks)||!Array.isArray(p.groups))throw Error("Invalid snapshot format");
 if(p.selection_policy?.id!=="above_sma50_industry2_v1"||
    p.selection_policy.close_above_sma50!==true||
    p.selection_policy.industry_min_members!==2||
    p.selection_policy.theme_min_members!==3)
   throw Error("This snapshot predates the enforced SMA50 rules. The current-rule refresh has not reached this host yet.");
 if(p.stocks.some(r=>r.above50!==100||r.history_bars<50))
   throw Error("Snapshot contains a stock outside the enforced SMA50 selection.");
 if(p.groups.some(g=>g.kind==="industry"&&g.count<2))
   throw Error("Snapshot contains an industry with fewer than two qualifying stocks.");
}
