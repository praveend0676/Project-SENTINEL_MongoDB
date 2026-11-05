import pandas as pd
from src.common import ROOT
def main():
    rows=[]
    for p in (ROOT/"data"/"raw").glob("*.csv"):
        d=pd.read_csv(p)
        for col in d:
            rows.append({"table":p.stem,"column":col,"dtype":str(d[col].dtype),"nulls":int(d[col].isna().sum()),"null_pct":round(d[col].isna().mean()*100,3),"distinct":int(d[col].nunique(dropna=True)),"duplicate_rows":int(d.duplicated().sum())})
    report=pd.DataFrame(rows)
    with pd.ExcelWriter(ROOT/"outputs"/"data_quality_report.xlsx",engine="openpyxl") as w: report.to_excel(w,index=False,sheet_name="Quality")
    print(report.to_string(index=False))
if __name__=="__main__": main()
