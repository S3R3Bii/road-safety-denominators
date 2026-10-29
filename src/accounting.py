"""Exact finite-table arithmetic and conservative closed-rounding feasibility."""
import csv,json
from fractions import Fraction
from config import ROOT,SHARES,DENOMS

def integer(token):return int(token.replace(',','').replace('%',''))
def ceil(x):return -((-x.numerator)//x.denominator)

def feasible(total,percentages):
    bounds={k:(ceil(Fraction(total*max(0,2*p-1),200)),(total*min(200,2*p+1))//200) for k,p in percentages.items()}
    assert all(0<=lo<=hi<=total for lo,hi in bounds.values()),'Empty percentage interval'
    minimum=sum(lo for lo,_ in bounds.values());assert minimum<=total,'Rounded shares cannot fit total'
    return {k:(lo,min(hi,total-(minimum-lo))) for k,(lo,hi) in bounds.items()}

def read():
    with (ROOT/'data/measurements.csv').open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    for r in rows:
        for k in ['year','fatalities',*DENOMS,*[s+'_pct' for s in SHARES]]:r[k]=int(r[k])
    return rows

def write_csv(path,rows):
    with path.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)

def save_json(path,data):path.write_text(json.dumps(data,indent=2,ensure_ascii=True)+'\n',encoding='utf-8')
