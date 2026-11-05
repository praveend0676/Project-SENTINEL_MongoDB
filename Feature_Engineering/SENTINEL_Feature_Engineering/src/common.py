import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load_config():
    return json.loads((ROOT/"config"/"settings.json").read_text(encoding="utf-8"))
def save_csv(df,name):
    p=ROOT/"outputs"/name
    p.parent.mkdir(exist_ok=True)
    df.to_csv(p,index=False)
    print("Saved",p)
