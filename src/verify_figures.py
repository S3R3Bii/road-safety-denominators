"""Every plotted value independently matches verified row-level evidence."""
import csv,json
from collections import Counter
from config import ROOT,STATES

def read(path):
    with (ROOT/path).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def main():
    # Source cross-products reconstruct scatter ranks without production rank helpers.
    source={r['state']:r for r in read('data/measurements.csv') if r['year']=='2023'};rank={}
    for s,r in source.items():
        for d in ['population','vmt_millions']:
            higher=sum(int(t['fatalities'])*int(r[d])>int(r['fatalities'])*int(t[d]) for t in source.values());equal=sum(int(t['fatalities'])*int(r[d])==int(r['fatalities'])*int(t[d]) for t in source.values());rank[s,d]=(2*higher+equal+1)/2
    exact=Counter();bounded=Counter()
    for phase in ['development','evaluation']:
        for r in read(f'results/{phase}/exact_pairs.csv'):
            if r['category']=='reversal':exact[r['year'],r['denominator_a'],r['denominator_b']]+=1
        for r in read(f'results/{phase}/bounded_pairs.csv'):
            if r['denominator_a']=='population' and r['denominator_b']=='vmt_millions' and r['group']!='all':bounded[r['year'],r['group'],r['category']]+=1
    plot=read('figures/PLOT_DATA.csv');assert len(plot)==138;seen=set()
    for r in plot:
        key=tuple(r[k] for k in ['figure','year','group','denominator_a','denominator_b','state','series']);assert key not in seen;seen.add(key)
        if r['figure']=='rank-scatter':value=rank[r['state'],'population' if r['series']=='population_midrank' else 'vmt_millions']
        elif r['figure']=='exact-reversals':value=exact[r['year'],r['denominator_a'],r['denominator_b']]
        else:value=bounded[r['year'],r['group'],r['series']]
        assert float(r['value'])==value
    cert={'status':'PASS','plotted_values':len(plot),'scope':'Independent source crossproducts for51scatter points;row-levelexact andboundedpaircontingencies for everybar;visualinspection separate'}
    (ROOT/'results/FIGURE_CHECK.json').write_text(json.dumps(cert,indent=2)+'\n',encoding='utf-8');print(json.dumps(cert))

if __name__=='__main__':main()
