import os, pandas as pd
from dotenv import load_dotenv
from supabase import create_client
from src.common import load_config,ROOT
def fetch(sb,table,page,limit):
    out=[]; start=0
    while len(out)<limit:
        end=min(start+page,limit)-1
        batch=sb.table(table).select("*").range(start,end).execute().data or []
        if not batch: break
        out.extend(batch)
        if len(batch)<end-start+1: break
        start+=page
    return out[:limit]
def main():
    load_dotenv()
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"): raise SystemExit("Configure .env first")
    sb=create_client(os.getenv("SUPABASE_URL"),os.getenv("SUPABASE_KEY")); cfg=load_config()
    for name,table in cfg["tables"].items():
        try:
            rows=fetch(sb,table,cfg["page_size"],cfg["sample_limit_per_table"])
            if rows:
                pd.DataFrame(rows).to_csv(ROOT/"data"/"raw"/f"{name}.csv",index=False)
                print(name,len(rows),"rows exported")
            else: print(name,"no rows returned; check table and RLS")
        except Exception as e: print(name,"FAILED:",e)
if __name__=="__main__": main()
