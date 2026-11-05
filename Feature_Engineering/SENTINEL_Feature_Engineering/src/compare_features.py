import pandas as pd
from src.common import ROOT,load_config
def main():
    cfg=load_config(); a=ROOT/"outputs"/"engineered_features.csv"; b=ROOT/"data"/"raw"/"client_features.csv"
    if not a.exists() or not b.exists(): raise SystemExit("Need engineered_features.csv and client_features.csv")
    ours=pd.read_csv(a); client=pd.read_csv(b); key=cfg["columns"]["transaction"]["id"]
    m=ours.merge(client,on=key,how="inner",suffixes=("_ours","_client")); reports=[]; bad=[]
    for feature,refcol in cfg["feature_columns"].items():
        if feature not in m or refcol not in m:
            reports.append({"feature":feature,"compared":0,"matches":0,"match_rate_pct":None,"note":"Check feature_columns mapping"}); continue
        x,y=m[feature],m[refcol]
        if pd.api.types.is_numeric_dtype(x) and pd.api.types.is_numeric_dtype(y): eq=(x.isna()&y.isna())|((x-y).abs()<=1e-6)
        else: eq=x.fillna("<NULL>").astype(str).eq(y.fillna("<NULL>").astype(str))
        reports.append({"feature":feature,"compared":len(m),"matches":int(eq.sum()),"match_rate_pct":round(eq.mean()*100,3) if len(eq) else None,"note":""})
        z=m.loc[~eq,[key,feature,refcol]].copy().rename(columns={feature:"our_value",refcol:"client_value"}); z.insert(1,"feature_name",feature); bad.append(z)
    mismatches=pd.concat(bad,ignore_index=True) if bad else pd.DataFrame()
    with pd.ExcelWriter(ROOT/"outputs"/"feature_match_report.xlsx",engine="openpyxl") as w:
        pd.DataFrame(reports).to_excel(w,index=False,sheet_name="Match_Rates"); mismatches.to_excel(w,index=False,sheet_name="Mismatches")
    mismatches.to_csv(ROOT/"outputs"/"mismatch_details.csv",index=False)
    print(pd.DataFrame(reports).to_string(index=False))
if __name__=="__main__": main()
