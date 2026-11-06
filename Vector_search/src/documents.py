from pathlib import Path
import re, hashlib
from pypdf import PdfReader
from docx import Document
from src.config import CORPUS,CHUNK,OVERLAP

def clean(s):
    s=s.replace("\x00"," ")
    s=re.sub(r"[\r\t]+"," ",s)
    s=re.sub(r" {2,}"," ",s)
    s=re.sub(r"\n{3,}","\n\n",s)
    s=re.sub(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b","[EMAIL_REDACTED]",s)
    s=re.sub(r"\b(?:\+?91[-\s]?)?[6-9]\d{9}\b","[PHONE_REDACTED]",s)
    s=re.sub(r"\b\d{12,19}\b","[LONG_NUMBER_REDACTED]",s)
    return s.strip()

def extract(p):
    if p.suffix.lower() in (".txt",".md"): return p.read_text(encoding="utf-8",errors="ignore")
    if p.suffix.lower()==".pdf": return "\n".join(x.extract_text() or "" for x in PdfReader(str(p)).pages)
    if p.suffix.lower()==".docx": return "\n".join(x.text for x in Document(str(p)).paragraphs)
    return ""

def dtype(path):
    s=str(path).lower()
    if any(x in s for x in ["rbi","npci","circular","guideline"]): return "rbi_npci_guideline"
    if any(x in s for x in ["playbook","rule"]): return "fraud_playbook"
    if any(x in s for x in ["chargeback","dispute"]): return "chargeback_narrative"
    if any(x in s for x in ["investigator","case_note","notes"]): return "investigator_note"
    return "other"

def load_docs():
    docs=[]; seen=set()
    for p in Path(CORPUS).rglob("*"):
        if p.suffix.lower() not in {".pdf",".docx",".txt",".md"}: continue
        txt=clean(extract(p))
        if len(txt)<80: continue
        h=hashlib.sha256(txt.encode()).hexdigest()
        if h in seen: continue
        seen.add(h)
        docs.append({"source_document":p.relative_to(CORPUS).as_posix(),"document_type":dtype(p),"text":txt})
    return docs

def make_chunks(docs):
    result=[]; step=CHUNK-OVERLAP
    for d in docs:
        start=0; n=0
        while start<len(d["text"]):
            part=d["text"][start:start+CHUNK].strip()
            if part: result.append({**{k:d[k] for k in ("source_document","document_type")},"chunk_number":n,"text":part})
            if start+CHUNK>=len(d["text"]): break
            start+=step; n+=1
    return result
