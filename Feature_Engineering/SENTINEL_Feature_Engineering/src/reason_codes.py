import pandas as pd
from src.common import ROOT,load_config,save_csv
def main():
    cfg=load_config(); p=ROOT/"outputs"/"engineered_features.csv"
    if not p.exists(): raise SystemExit("Run feature engineering first")
    d=pd.read_csv(p); th=cfg["reason_code_thresholds"]; out=[]
    for _,r in d.iterrows():
        codes=[]
        if pd.notna(r.get("is_new_device")) and bool(r["is_new_device"]): codes.append("R01_NEW_DEVICE")
        x=th.get("R02_distance_km")
        if x is not None and pd.notna(r.get("customer_merchant_distance_km")) and r["customer_merchant_distance_km"]>=x: codes.append("R02_GEO_MISMATCH")
        if bool(r.get("is_night",False)): codes.append("R03_ODD_HOUR")
        x=th.get("R05_amount_to_average_ratio")
        if x is not None and pd.notna(r.get("amount_to_average_ratio")) and r["amount_to_average_ratio"]>=x: codes.append("R05_AMOUNT_SPIKE")
        x=th.get("R07_transaction_count_last_1_hour")
        y=th.get("R07_transaction_amount_last_24_hours")
        if (x is not None and r.get("transaction_count_last_1_hour",0)>=x) or (y is not None and r.get("transaction_amount_last_24_hours",0)>=y): codes.append("R07_VELOCITY")
        mcc=cfg["columns"]["transaction"].get("mcc"); vals=th.get("R08_high_risk_mcc_values") or []
        if vals and mcc in d and r.get(mcc) in vals: codes.append("R08_HIGH_RISK_MCC")
        # R04/R06 need configured source fields and class thresholds; add exact source mappings before enabling.
        out.append("|".join(codes))
    d["reason_codes"]=out; save_csv(d,"reason_codes.csv")
    print("Unconfigured rules are skipped, not guessed.")
if __name__=="__main__": main()
