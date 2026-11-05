import numpy as np, pandas as pd
from src.common import ROOT,load_config,save_csv
def haversine(a,b,c,d):
    if any(pd.isna(x) for x in (a,b,c,d)): return np.nan
    if not(-90<=a<=90 and -90<=c<=90 and -180<=b<=180 and -180<=d<=180): return np.nan
    p1,p2=np.radians(a),np.radians(c); dp=np.radians(c-a); dl=np.radians(d-b)
    h=np.sin(dp/2)**2+np.cos(p1)*np.cos(p2)*np.sin(dl/2)**2
    return 12742.0176*np.arcsin(np.sqrt(h))
def main():
    cfg=load_config(); f=ROOT/"data"/"raw"/"transaction.csv"
    if not f.exists(): raise SystemExit("Run python -m src.load_supabase first")
    d=pd.read_csv(f); c=cfg["columns"]["transaction"]
    for key in ("id","customer_id","timestamp","amount"):
        if c.get(key) not in d: raise SystemExit(f"Map transaction.{key} correctly in config/settings.json")
    ts,amt,cust=c["timestamp"],c["amount"],c["customer_id"]
    d[ts]=pd.to_datetime(d[ts],errors="coerce"); d[amt]=pd.to_numeric(d[amt],errors="coerce")
    d=d.dropna(subset=[ts,cust]).sort_values([cust,ts,c["id"]]).reset_index(drop=True)
    d["is_night"]=d[ts].dt.hour.ge(cfg["night_start_hour_inclusive"]) & d[ts].dt.hour.lt(cfg["night_end_hour_exclusive"])
    clat,clon,mlat,mlon=[c.get(k) for k in ("customer_latitude","customer_longitude","merchant_latitude","merchant_longitude")]
    if all(x in d.columns for x in (clat,clon,mlat,mlon)):
        d["customer_merchant_distance_km"]=[haversine(*x) for x in zip(d[clat],d[clon],d[mlat],d[mlon])]
    else: d["customer_merchant_distance_km"]=np.nan
    d["amount_to_average_ratio"]=np.nan; d["is_new_device"]=pd.Series(pd.NA,index=d.index,dtype="boolean")
    d["transaction_count_last_1_hour"]=0; d["transaction_amount_last_24_hours"]=0.0
    dev=c.get("device_id")
    for _,ids in d.groupby(cust,sort=False).groups.items():
        ids=list(ids)
        for pos,i in enumerate(ids):
            t=d.at[i,ts]; prior=d.loc[ids[:pos]]
            hist=prior[prior[ts]>=t-pd.Timedelta(days=cfg["history_days"])]
            avg=hist[amt].mean()
            if pd.notna(avg) and avg>0 and pd.notna(d.at[i,amt]): d.at[i,"amount_to_average_ratio"]=d.at[i,amt]/avg
            if dev and dev in d and pd.notna(d.at[i,dev]): d.at[i,"is_new_device"]=not hist[dev].eq(d.at[i,dev]).any()
            h1=prior[prior[ts]>t-pd.Timedelta(hours=1)]
            h24=prior[prior[ts]>t-pd.Timedelta(hours=24)]
            d.at[i,"transaction_count_last_1_hour"]=len(h1)
            val=h24[amt].sum()
            d.at[i,"transaction_amount_last_24_hours"]=0.0 if pd.isna(val) else val
    save_csv(d,"engineered_features.csv")
if __name__=="__main__": main()
