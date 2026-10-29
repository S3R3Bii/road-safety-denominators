"""Independent source join, decimal feasibility, SQL ranks and integer cross-products."""
import argparse,csv,json,sqlite3
from decimal import Decimal,ROUND_CEILING,ROUND_FLOOR
from itertools import combinations
from config import ROOT,DEV_YEARS,EVAL_YEARS,STATES,DENOMS,GROUPS,SHARES
from source_tables import read_gz

def load(name):
    with (ROOT/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def main(phase):
    years=DEV_YEARS if phase=='development' else EVAL_YEARS;manifest=json.loads((ROOT/'data/source/manifest.json').read_text());original={};checks=0;maximum=0.0
    # Filter years before constructing any ranking or subgroup outcomes.
    for report in manifest['reports']:
        if report['year'] not in years:continue
        tables={t['table']:{r['state']:r for r in read_gz(ROOT/t['subset_file'])} for t in report['tables']}
        for state in STATES:
            a=tables[1][state];b=tables[7][state];d={'year':report['year'],'state':state}
            for k in ['fatalities',*DENOMS]:d[k]=int(a[k].replace(',',''))
            for k in SHARES:d[k+'_pct']=int(b[k+'_pct'].replace('%',''))
            for k in SHARES:d[k+'_count']=int(b[k+'_count'].replace(',','')) if b[k+'_count']!='' else ''
            original[report['year'],state]=d
    data=[r for r in load('data/measurements.csv') if int(r['year']) in years];assert len(data)==len(original)
    for r in data:
        expected=original[int(r['year']),r['state']]
        for k,v in expected.items():assert r[k]==str(v);checks+=1
    db=sqlite3.connect(':memory:');db.execute('CREATE TABLE r(year INTEGER,state TEXT,n INTEGER,population INTEGER,licensed_drivers INTEGER,vmt_millions INTEGER)');db.executemany('INSERT INTO r VALUES(?,?,?,?,?,?)',[(r['year'],r['state'],r['fatalities'],*[r[d] for d in DENOMS]) for r in original.values()])
    rank_expected={};rate_expected={}
    for year in years:
        for denom in DENOMS:
            sql=f'SELECT a.state,2*SUM(CASE WHEN b.n*a.{denom}>a.n*b.{denom} THEN 1 ELSE 0 END)+SUM(CASE WHEN b.n*a.{denom}=a.n*b.{denom} THEN 1 ELSE 0 END)+1 FROM r a JOIN r b ON a.year=b.year WHERE a.year=? GROUP BY a.state'
            for state,num in db.execute(sql,(year,)):rank_expected[year,state,denom]=Decimal(num)/2
            rs=[r for (y,_),r in original.items() if y==year];scale=100 if denom=='vmt_millions' else 100000
            for r in rs:rate_expected[year,r['state'],denom]=Decimal(r['fatalities'])*scale/Decimal(r[denom])
    folder='results/'+phase+'/';ranks=load(folder+'exact_ranks.csv');assert len(ranks)==len(years)*153;assert len({(r['year'],r['state'],r['denominator']) for r in ranks})==len(ranks)
    for r in ranks:
        key=int(r['year']),r['state'],r['denominator'];value=rate_expected[key];rank=rank_expected[key]
        assert Decimal(r['rate_numerator'])/Decimal(r['rate_denominator'])==value;assert Decimal(r['midrank_numerator'])/Decimal(r['midrank_denominator'])==rank
        for col,v in [('rate',value),('midrank',rank)]:delta=abs(float(r[col])-float(v));assert delta<=1e-12;maximum=max(maximum,delta);checks+=1
        group=sorted([v for (y,_,d),v in rate_expected.items() if (y,d)==(key[0],key[2])],reverse=True)
        for n in [5,10]:assert int(r['top'+str(n)])==int(value>=group[n-1]);checks+=1
    exact=load(folder+'exact_pairs.csv');assert len(exact)==len(years)*1275*3;exact_hist={}
    assert len({(r['year'],r['denominator_a'],r['denominator_b'],r['state_a'],r['state_b']) for r in exact})==len(exact)
    for row in exact:
        year=int(row['year']);a=original[year,row['state_a']];b=original[year,row['state_b']];orders=[]
        for d,col in [(row['denominator_a'],'order_a'),(row['denominator_b'],'order_b')]:
            delta=a['fatalities']*b[d]-b['fatalities']*a[d];v=(delta>0)-(delta<0);assert int(row[col])==v;checks+=1;orders.append(v)
        x,y=orders;expected='tie_in_either' if x*y==0 else 'same' if x==y else 'reversal';assert row['category']==expected;checks+=1
        key=year,row['denominator_a'],row['denominator_b'];hist=exact_hist.setdefault(key,{'same':0,'reversal':0,'tie_in_either':0});hist[expected]+=1
    for row in load(folder+'exact_summary.csv'):
        y=int(row['year']);a=row['denominator_a'];b=row['denominator_b'];hist=exact_hist[y,a,b]
        for k,n in hist.items():assert int(row[k])==n;checks+=1
        assert int(row['pairs'])==sum(hist.values())==1275
        moves=[abs(rank_expected[y,s,a]-rank_expected[y,s,b]) for s in STATES];assert Decimal(row['max_abs_midrank_movement'])==max(moves);checks+=1
        for n in [5,10]:
            sets=[]
            for d in [a,b]:
                values={s:rate_expected[y,s,d] for s in STATES};cut=sorted(values.values(),reverse=True)[n-1];sets.append({s for s,v in values.items() if v>=cut})
            for k,v in [('a_size',len(sets[0])),('b_size',len(sets[1])),('overlap',len(sets[0]&sets[1]))]:assert int(row[f'top{n}_{k}'])==v;checks+=1
    interval={};bound_numerics={}
    for (year,state),r in original.items():
        n=r['fatalities'];raw={}
        for share in SHARES:
            p=Decimal(r[share+'_pct']);lo=int((Decimal(n)*max(Decimal(),p-Decimal('.5'))/100).to_integral_value(rounding=ROUND_CEILING));hi=int((Decimal(n)*min(Decimal(100),p+Decimal('.5'))/100).to_integral_value(rounding=ROUND_FLOOR));raw[share]=(lo,hi)
        minimum=sum(x[0] for x in raw.values())
        for group in GROUPS:
            lo,hi=(n,n) if group=='all' else (raw[group][0],min(raw[group][1],n-minimum+raw[group][0]))
            for d in DENOMS:
                if d=='vmt_millions':lower=(lo*200,2*r[d]+1);upper=(hi*200,2*r[d]-1)
                else:lower=(lo*100000,r[d]);upper=(hi*100000,r[d])
                key=year,state,group,d;interval[key]=(lo,hi);bound_numerics[key]=(lower,upper)
    bounds=load(folder+'rate_placement_bounds.csv');assert len(bounds)==len(years)*51*4*3;stored={}
    for row in bounds:
        key=int(row['year']),row['state'],row['group'],row['denominator'];assert key not in stored;stored[key]=row
        assert (int(row['count_lower']),int(row['count_upper']))==interval[key];checks+=2
        for prefix,(num,den) in zip(['lower','upper'],bound_numerics[key]):
            assert int(row[f'rate_{prefix}_numerator'])*den==num*int(row[f'rate_{prefix}_denominator']);checks+=1
            delta=abs(float(row['rate_'+prefix])-float(Decimal(num)/Decimal(den)));assert delta<=1e-12;maximum=max(maximum,delta);checks+=1
        ownlow,ownhigh=bound_numerics[key];definitely_higher=definitely_lower=0
        for s in STATES:
            if s==key[1]:continue
            low,high=bound_numerics[key[0],s,key[2],key[3]]
            definitely_higher+=low[0]*ownhigh[1]>ownhigh[0]*low[1];definitely_lower+=high[0]*ownlow[1]<ownlow[0]*high[1]
        assert int(row['best_ordinal_placement'])==1+definitely_higher and int(row['worst_ordinal_placement'])==51-definitely_lower;checks+=2
    bounded=load(folder+'bounded_pairs.csv');assert len(bounded)==len(years)*4*3*1275;histograms={}
    assert len({(r['year'],r['group'],r['denominator_a'],r['denominator_b'],r['state_a'],r['state_b']) for r in bounded})==len(bounded)
    for row in bounded:
        year=int(row['year']);g=row['group'];values=[]
        for d,col in [(row['denominator_a'],'dominance_a'),(row['denominator_b'],'dominance_b')]:
            (al,ah)=bound_numerics[year,row['state_a'],g,d];(bl,bh)=bound_numerics[year,row['state_b'],g,d]
            v=1 if al[0]*bh[1]>bh[0]*al[1] else -1 if ah[0]*bl[1]<bl[0]*ah[1] else 0;assert int(row[col])==v;checks+=1;values.append(v)
        x,y=values;category='unresolved' if x*y==0 else 'guaranteed_same' if x==y else 'guaranteed_reversal';assert row['category']==category;checks+=1
        key=year,g,row['denominator_a'],row['denominator_b'];hist=histograms.setdefault(key,{'guaranteed_same':0,'guaranteed_reversal':0,'unresolved':0});hist[category]+=1
    sums=load(folder+'bounded_summary.csv');assert len(sums)==len(years)*4*3
    for r in sums:
        expected=histograms[int(r['year']),r['group'],r['denominator_a'],r['denominator_b']]
        for k,v in expected.items():assert int(r[k])==v;checks+=1
        assert sum(expected.values())==int(r['pairs'])==1275
    cert={'status':'PASS','phase':phase,'independent_value_checks':checks,'max_float_delta':maximum,'methods':'Independent source-tokenjoin;SQLite integer midranks;integer pair crossproducts;Decimalclosedrounding bounds;separate contingency reconstruction','tolerance':'Exact integers,rank halves,count bounds,ratio crossproducts andpaircategories;1e-12absolute onlyforfloatdisplay'}
    (ROOT/(folder+'INDEPENDENT_CHECK.json')).write_text(json.dumps(cert,indent=2)+'\n',encoding='utf-8');print(json.dumps(cert))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['development','evaluation']);main(p.parse_args().phase)
