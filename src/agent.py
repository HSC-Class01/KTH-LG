import os, io, json, time, zipfile
from pathlib import Path
from datetime import datetime
import requests, pandas as pd
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/"config.json").read_text(encoding="utf-8"))
KEY=os.getenv("DART_API_KEY","").strip()
if not KEY: raise SystemExit("Set DART_API_KEY in GitHub Actions repository secrets.")
API="https://opendart.fss.or.kr/api"; RAW=ROOT/"data/raw"; REPORTS=RAW/"reports"; OUT=ROOT/"data/processed"
REPORTS.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True)

def call(endpoint,params=None):
    q=dict(params or {}); q["crtfc_key"]=KEY
    r=requests.get(API+"/"+endpoint,params=q,timeout=120); r.raise_for_status(); return r

def corp_code():
    if CFG.get("corp_code"): return CFG["corp_code"]
    data=call("corpCode.xml").content
    with zipfile.ZipFile(io.BytesIO(data)) as z: root=ET.fromstring(z.read(z.namelist()[0]))
    for node in root.findall("list"):
        if (node.findtext("stock_code") or "").strip()==CFG["stock_code"]:
            CFG["corp_code"]=(node.findtext("corp_code") or "").strip()
            (ROOT/"config.json").write_text(json.dumps(CFG,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            return CFG["corp_code"]
    raise RuntimeError("Could not find DART corp_code for LG전자 / 066570")

def kind(title):
    if "사업보고서" in title: return "annual"
    if "반기보고서" in title: return "half-year"
    if "분기보고서" in title: return "quarterly"
    return None

def filings(code):
    result={}
    for year in range(int(CFG["start_year"]),datetime.now().year+1):
        page=1
        while True:
            obj=call("list.json",{"corp_code":code,"bgn_de":str(year)+"0101","end_de":str(year)+"1231","pblntf_ty":"A","page_no":page,"page_count":100}).json()
            if obj.get("status")=="013": break
            if obj.get("status")!="000": raise RuntimeError("DART list error: "+str(obj))
            for f in obj.get("list",[]):
                t=kind(f.get("report_nm",""))
                if t and f.get("rcept_no"): result[f["rcept_no"]]=dict(f,report_type=t)
            if page>=int(obj.get("total_page",1)): break
            page+=1; time.sleep(.1)
    return list(result.values())

def main():
    code=corp_code(); fs=filings(code); facts=[]
    for f in sorted(fs,key=lambda x:x.get("rcept_dt","")):
        receipt=f["rcept_no"]; title=f.get("report_nm",""); typ=f["report_type"]
        archive=REPORTS/(receipt+".zip")
        if not archive.exists():
            try:
                response=call("document.xml",{"rcept_no":receipt})
                if response.content[:2]==b"PK": archive.write_bytes(response.content)
                else: (REPORTS/(receipt+".response.xml")).write_bytes(response.content)
            except Exception as e: print("Document archive warning",receipt,e)
        year=int(f.get("rcept_dt","00000000")[:4])
        file_month=int(f.get("rcept_dt","00000000")[4:6] or 0)
        reprt="11011" if typ=="annual" else "11012" if typ=="half-year" else ("11013" if file_month in (4,5) else "11014")
        data=call("fnlttSinglAcntAll.json",{"corp_code":code,"bsns_year":year,"reprt_code":reprt,"fs_div":"CFS"}).json()
        if data.get("status")=="000":
            (RAW/(receipt+".json")).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
            for a in data.get("list",[]):
                facts.append({"receipt_no":receipt,"filing_date":f.get("rcept_dt"),"report_name":title,"report_type":typ,
                "bsns_year":a.get("bsns_year"),"reprt_code":a.get("reprt_code"),"fs_div":a.get("fs_div"),"sj_div":a.get("sj_div"),
                "account_id":a.get("account_id"),"account_nm":a.get("account_nm"),"thstrm_nm":a.get("thstrm_nm"),
                "thstrm_amount":a.get("thstrm_amount"),"frmtrm_nm":a.get("frmtrm_nm"),"frmtrm_amount":a.get("frmtrm_amount"),
                "bfefrmtrm_nm":a.get("bfefrmtrm_nm"),"bfefrmtrm_amount":a.get("bfefrmtrm_amount"),"currency":a.get("currency")})
        elif data.get("status") not in ("013",): print("Financial API notice",receipt,data.get("status"),data.get("message"))
        time.sleep(.12)
    pd.DataFrame(fs).drop_duplicates("rcept_no").to_csv(OUT/"filings.csv",index=False,encoding="utf-8-sig")
    pd.DataFrame(facts).drop_duplicates(["receipt_no","account_id","sj_div"]).to_csv(OUT/"financial_facts.csv",index=False,encoding="utf-8-sig")
    print("Collected filings:",len(fs),"financial rows:",len(facts))
if __name__=="__main__": main()
