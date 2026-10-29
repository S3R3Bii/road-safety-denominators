"""Capture exact official report responses privately and publish selected facts only."""
import argparse,hashlib,json,shutil
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from pypdf import PdfReader
from config import ROOT,YEARS,REPORTS
from source_tables import decode,parse_lines,select_pages,write_gz

def main():
    p=argparse.ArgumentParser();p.add_argument('originals',type=Path);p.add_argument('--reuse-2019',type=Path);a=p.parse_args();raw=a.originals.resolve();assert not raw.is_relative_to(ROOT);raw.mkdir(parents=True,exist_ok=False)
    manifest=[]
    for year in YEARS:
        url='https://crashstats.nhtsa.dot.gov/Api/Public/ViewPublication/'+REPORTS[year]
        if year==2019 and a.reuse_2019:
            data=a.reuse_2019.read_bytes();captured=datetime.fromtimestamp(a.reuse_2019.stat().st_mtime,timezone.utc).isoformat();time_basis='Original discovery response file modification timestamp; no response header time asserted'
        else:
            with urlopen(Request(url,headers={'User-Agent':'IndependentDenominatorResearch/1.0'}),timeout=90) as response:assert response.status==200;data=response.read()
            captured=datetime.now(timezone.utc).isoformat();time_basis='UTC immediately after response read'
        (raw/f'{year}.response').write_bytes(data);pdf,wrapper=decode(data);path=raw/f'{year}.pdf';path.write_bytes(pdf);reader=PdfReader(path);tables=[]
        for table in [1,7]:
            pages=select_pages(reader,table,year);rows=[]
            for page,text in pages:rows.extend(parse_lines(text,year,table,page))
            out=ROOT/f'data/source/{year}-table{table}.csv.gz';write_gz(out,rows);tables.append({'table':table,'pages':[x[0] for x in pages],'rows':len(rows),'subset_file':out.relative_to(ROOT).as_posix(),'subset_sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
        manifest.append({'year':year,'publication':REPORTS[year],'url':url,'captured_utc':captured,'timestamp_basis':time_basis,'response_sha256':hashlib.sha256(data).hexdigest(),'response_bytes':len(data),'payload_sha256':hashlib.sha256(pdf).hexdigest(),'payload_bytes':len(pdf),'wrapper':wrapper,'pages':len(reader.pages),'tables':tables,'version':'Published report-year ARF snapshot;not latest FARS'})
        print(json.dumps({'year':year,'report_pages':len(reader.pages),'table_rows':[(t['table'],t['rows']) for t in tables],'wrapper':wrapper}),flush=True)
    (ROOT/'data/source/manifest.json').write_text(json.dumps({'reports':manifest,'excluded_fields':'All registered-vehicle count/rate fields and source-report expression;no source PDFs inGit'},indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
