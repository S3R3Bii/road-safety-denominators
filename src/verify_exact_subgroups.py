"""Independent SQL/integer comparator for the source's supplied2023subgroup counts."""
import csv,json,sqlite3
from decimal import Decimal
from config import ROOT,STATES,DENOMS,GROUPS
from source_tables import read_gz

def load(path):
    with (ROOT/path).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def main():
    report=next(r for r in json.loads((ROOT/'data/source/manifest.json').read_text())['reports'] if r['year']==2023);t1={r['state']:r for r in read_gz(ROOT/next(t['subset_file'] for t in report['tables'] if t['table']==1))};t7={r['state']:r for r in read_gz(ROOT/next(t['subset_file'] for t in report['tables'] if t['table']==7))}
    original={s:{**{d:int(t1[s][d].replace(',','')) for d in DENOMS},**{g:int(t7[s][g+'_count'].replace(',','')) for g in GROUPS[1:]}} for s in STATES}
    db=sqlite3.connect(':memory:');db.execute('CREATE TABLE r(state TEXT,g TEXT,n INTEGER,population INTEGER,licensed_drivers INTEGER,vmt_millions INTEGER)');db.executemany('INSERT INTO r VALUES(?,?,?,?,?,?)',[(s,g,r[g],*[r[d] for d in DENOMS]) for s,r in original.items() for g in GROUPS[1:]])
    checks=0;ranks={};rates={}
    for g in GROUPS[1:]:
        for d in DENOMS:
            query=f'SELECT a.state,2*SUM(CASE WHEN b.n*a.{d}>a.n*b.{d} THEN 1 ELSE 0 END)+SUM(CASE WHEN b.n*a.{d}=a.n*b.{d} THEN 1 ELSE 0 END)+1 FROM r a JOIN r b ON a.g=b.g WHERE a.g=? GROUP BY a.state'
            for s,num in db.execute(query,(g,)):ranks[s,g,d]=Decimal(num)/2
            for s,r in original.items():rates[s,g,d]=Decimal(r[g])*(100 if d=='vmt_millions' else 100000)/Decimal(r[d])
    rows=load('results/evaluation/exact_subgroup_ranks.csv');assert len(rows)==459 and len({(r['state'],r['group'],r['denominator']) for r in rows})==459
    bounds={(r['state'],r['group'],r['denominator']):r for r in load('results/evaluation/rate_placement_bounds.csv')}
    for r in rows:
        s,g,d=r['state'],r['group'],r['denominator'];rank=ranks[s,g,d];value=rates[s,g,d];assert int(r['observed_subgroup_fatalities'])==original[s][g];assert Decimal(r['rate_numerator'])/Decimal(r['rate_denominator'])==value;assert Decimal(r['midrank_numerator'])/Decimal(r['midrank_denominator'])==rank;checks+=3
        for n in [5,10]:cut=sorted([rates[x,g,d] for x in STATES],reverse=True)[n-1];assert int(r['top'+str(n)])==int(value>=cut);checks+=1
        b=bounds[s,g,d];assert int(b['count_lower'])<=original[s][g]<=int(b['count_upper']);assert Decimal(b['best_ordinal_placement'])<=rank<=Decimal(b['worst_ordinal_placement']);checks+=2
    conditional={(r['group'],r['denominator_a'],r['denominator_b'],r['state_a'],r['state_b']):r['category'] for r in load('results/evaluation/bounded_pairs.csv')};pairs=load('results/evaluation/exact_subgroup_pairs.csv');assert len(pairs)==11475 and len({(r['group'],r['denominator_a'],r['denominator_b'],r['state_a'],r['state_b']) for r in pairs})==11475;hist={}
    for r in pairs:
        g=r['group'];s=r['state_a'];t=r['state_b'];orders=[]
        for d,k in [(r['denominator_a'],'order_a'),(r['denominator_b'],'order_b')]:
            cross=original[s][g]*original[t][d]-original[t][g]*original[s][d];v=(cross>0)-(cross<0);assert int(r[k])==v;orders.append(v);checks+=1
        x,y=orders;category='tie_in_either' if x*y==0 else 'same' if x==y else 'reversal';assert r['exact_category']==category;key=g,r['denominator_a'],r['denominator_b'];condition=conditional[key+(s,t)];assert r['rounded_range_category']==condition
        assert condition!='guaranteed_same' or category=='same';assert condition!='guaranteed_reversal' or category=='reversal';checks+=4
        h=hist.setdefault(key,{'same':0,'reversal':0,'tie_in_either':0,'guaranteed_same':0,'guaranteed_reversal':0,'unresolved':0,'unresolved_actual_reversals':0});h[category]+=1;h[condition]+=1;h['unresolved_actual_reversals']+=condition=='unresolved' and category=='reversal'
    summary=load('results/evaluation/exact_subgroup_summary.csv');assert len(summary)==9
    for r in summary:
        for k,v in hist[r['group'],r['denominator_a'],r['denominator_b']].items():assert int(r[k])==v;checks+=1
        assert int(r['pairs'])==1275
    cert={'status':'PASS','independent_value_checks':checks,'exact_source_subgroup_counts_checked':153,'exact_rank_cells':459,'exact_pair_cells':11475,'all_conditional_guarantees_and_placements_contain_supplied_counts':'PASS','scope':'2023sourcecounts areafairpoint comparator;olderyears haveonlyroundedshares inthesetables;notatrue-exposureorclassification-lineagecertificate'}
    (ROOT/'results/evaluation/EXACT_SUBGROUP_CHECK.json').write_text(json.dumps(cert,indent=2)+'\n',encoding='utf-8');print(json.dumps(cert))

if __name__=='__main__':main()
