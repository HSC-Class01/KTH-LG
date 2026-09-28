import json
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/"docs"; DOCS.mkdir(exist_ok=True)
cfg=json.loads((ROOT/"config.json").read_text(encoding="utf-8"))
f=ROOT/"data/processed/financial_facts.csv"
data=pd.read_csv(f) if f.exists() and f.stat().st_size else pd.DataFrame()
metrics=pd.DataFrame()
if not data.empty:
    data=data[data.fs_div.astype(str)=="CFS"].copy()
    data["year"]=pd.to_numeric(data.bsns_year,errors="coerce")
    data["amount"]=pd.to_numeric(data.thstrm_amount.astype(str).str.replace(",","",regex=False),errors="coerce")
    data=data.sort_values(["filing_date","receipt_no"]).drop_duplicates(["year","report_type","account_id","sj_div"],keep="last")
    aliases={"매출액":["Revenue","Sales","매출액"],"매출원가":["CostOfSales","Cost of sales","매출원가"],
    "매출총이익":["GrossProfit","Gross profit","매출총이익"],"영업이익":["OperatingIncomeLoss","Operating profit","영업이익"],
    "당기순이익":["ProfitLoss","Profit (Loss)","당기순이익"],"자산총계":["Assets","자산총계"],"부채총계":["Liabilities","부채총계"],
    "자본총계":["Equity","자본총계"],"유동자산":["CurrentAssets","유동자산"],"유동부채":["CurrentLiabilities","유동부채"],
    "영업활동현금흐름":["CashFlowsFromUsedInOperatingActivities","영업활동현금흐름"]}
    periods=data[["year","report_type"]].drop_duplicates().sort_values(["year","report_type"]); rows=[]
    for _,p in periods.iterrows():
        sub=data[(data.year==p.year)&(data.report_type==p.report_type)]; row={"연도":int(p.year),"구분":p.report_type}
        for label,terms in aliases.items():
            hit=pd.DataFrame()
            for term in terms:
                hit=sub[sub.account_id.fillna("").astype(str).str.contains(term,case=False,regex=False)|sub.account_nm.fillna("").astype(str).str.contains(term,case=False,regex=False)]
                if len(hit): break
            row[label]=hit.iloc[0].amount if len(hit) else None
        def pct(a,b): return row[a]/row[b]*100 if pd.notna(row.get(a)) and pd.notna(row.get(b)) and row[b]!=0 else None
        row["매출총이익률(%)"]=pct("매출총이익","매출액"); row["영업이익률(%)"]=pct("영업이익","매출액")
        row["순이익률(%)"]=pct("당기순이익","매출액"); row["유동비율(%)"]=pct("유동자산","유동부채")
        row["부채비율(%)"]=pct("부채총계","자본총계"); row["자기자본비율(%)"]=pct("자본총계","자산총계")
        rows.append(row)
    metrics=pd.DataFrame(rows)
metrics.to_csv(ROOT/"data/processed/dashboard_metrics.csv",index=False,encoding="utf-8-sig")
cols=["연도","매출액","매출원가","매출총이익","영업이익","당기순이익","자산총계","부채총계","자본총계","유동자산","유동부채","영업활동현금흐름","매출총이익률(%)","영업이익률(%)","순이익률(%)","유동비율(%)","부채비율(%)","자기자본비율(%)"]
def table(frame):
    if frame.empty: return "<p>데이터가 없습니다. Actions에서 workflow_dispatch로 실행하세요.</p>"
    return frame[[c for c in cols if c in frame]].to_html(index=False,classes="tbl",border=0,na_rep="—",float_format=lambda x:f"{x:,.2f}")
def block(title,typ):
    frame=metrics[metrics["구분"]==typ] if not metrics.empty else metrics
    return "<section><h2>"+title+"</h2><div class='scroll'>"+table(frame)+"</div></section>"
peers="".join("<tr><td>"+x["name"]+"</td><td>"+x["ticker"]+"</td><td>"+x["note"]+"</td></tr>" for x in cfg["peer_firms"])
annual=metrics[metrics["구분"]=="annual"] if not metrics.empty else metrics
chart=annual[["연도","매출액","영업이익","당기순이익"]].to_json(orient="records",force_ascii=False) if not annual.empty else "[]"
page="""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>LG전자 DART Dashboard</title><script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>body{margin:0;background:#f7fbfe;color:#18334a;font:14px/1.55 Arial,sans-serif}header{background:linear-gradient(120deg,#d9efff,#f4faff);padding:38px 5vw}main{max-width:1200px;margin:auto;padding:20px}section,.card{background:white;border:1px solid #e5eef5;border-radius:15px;padding:18px;margin:16px 0;box-shadow:0 8px 26px #244c6a0a}h1{font-size:38px;margin:0}h2{font-size:20px;margin:0 0 12px}.muted{color:#688096}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}.card b{display:block;font-size:22px}.chart{height:330px}.scroll{overflow-x:auto}.tbl{border-collapse:collapse;width:100%;font-size:12px;white-space:nowrap}.tbl th{background:#eef7fd;text-align:left}.tbl th,.tbl td{padding:9px;border-bottom:1px solid #edf2f6}footer{text-align:center;padding:25px;color:#688096}</style></head><body>
<header><p class="muted">DART OpenAPI · 연결재무제표 우선 · 2010년부터</p><h1>LG전자 Financial Dashboard</h1><p>사업보고서 · 반기보고서 · 분기보고서 | 매월 1일 자동 업데이트</p></header><main>
<div class="cards"><div class="card">기업<b>LG전자 · 066570</b></div><div class="card">수집 시작<b>2010년</b></div><div class="card">보고서 유형<b>Annual / Half-year / Quarterly</b></div><div class="card">자동 실행<b>매월 1일 09:17 KST</b></div></div>
<section><h2>Annual 주요 재무 추이</h2><div id="chart" class="chart"></div><p class="muted">금액은 DART 원자료 단위입니다. 계정명 매핑이 확인되지 않는 항목은 공란으로 둡니다.</p></section>
__ANNUAL____HALF____QUARTER__
<section><h2>국내 Peer Firms</h2><div class="scroll"><table class="tbl"><thead><tr><th>기업</th><th>종목코드</th><th>비교 범위</th></tr></thead><tbody>__PEERS__</tbody></table></div><p class="muted">참고용 peer 목록이며 자동 수집은 LG전자 공시에 한정됩니다.</p></section>
<footer>Source: <a href="https://opendart.fss.or.kr/">Open DART</a> · GitHub Actions</footer></main>
<script>const rows=__CHART__;Plotly.newPlot("chart",["매출액","영업이익","당기순이익"].map(k=>({x:rows.map(r=>r["연도"]),y:rows.map(r=>r[k]),name:k,type:"scatter",mode:"lines+markers"})),{margin:{t:10,r:15,b:40,l:60},legend:{orientation:"h"},xaxis:{title:"연도"},yaxis:{title:"원자료 단위"}},{responsive:true,displayModeBar:false});</script></body></html>"""
page=page.replace("__ANNUAL__",block("Annual · 사업보고서","annual")).replace("__HALF__",block("Half-year · 반기보고서","half-year")).replace("__QUARTER__",block("Quarterly · 분기보고서","quarterly")).replace("__PEERS__",peers).replace("__CHART__",chart)
(DOCS/"index.html").write_text(page,encoding="utf-8")
print("Dashboard generated",len(metrics),"period rows")
