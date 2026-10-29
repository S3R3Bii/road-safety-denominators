"""Fair exact-count comparator available only in the enhanced2023source table."""
import json,csv
from fractions import Fraction
from itertools import combinations
from config import ROOT,DENOMS,GROUPS,SHARES,STATES
from accounting import read,midranks,top_set,write_csv,save_json

def load(path):
    with (ROOT/path).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def main():
    rows={r['state']:r for r in read() if r['year']==2023};assert set(rows)==set(STATES) and all(r[s+'_count'] is not None for r in rows.values() for s in SHARES)
    bounds={(r['state'],r['group'],r['denominator']):r for r in load('results/evaluation/rate_placement_bounds.csv')};conditional={(r['group'],r['denominator_a'],r['denominator_b'],r['state_a'],r['state_b']):r['category'] for r in load('results/evaluation/bounded_pairs.csv')}
    ranks=[];pairs=[];summary=[]
    for group in GROUPS[1:]:
        rates={};rankmap={}
        for d in DENOMS:
            scale=100 if d=='vmt_millions' else 100000;rates[d]={s:Fraction(r[group+'_count']*scale,r[d]) for s,r in rows.items()};rankmap[d]=midranks(rates[d])
            for s in STATES:
                value=rates[d][s];rank=rankmap[d][s];b=bounds[s,group,d];assert int(b['count_lower'])<=rows[s][group+'_count']<=int(b['count_upper']);assert int(b['best_ordinal_placement'])<=rank<=int(b['worst_ordinal_placement'])
                ranks.append({'year':2023,'state':s,'group':group,'denominator':d,'observed_subgroup_fatalities':rows[s][group+'_count'],'rate_numerator':value.numerator,'rate_denominator':value.denominator,'rate':float(value),'midrank_numerator':rank.numerator,'midrank_denominator':rank.denominator,'midrank':float(rank),'top5':int(s in top_set(rates[d],5)),'top10':int(s in top_set(rates[d],10))})
        for a,b in combinations(DENOMS,2):
            collection=[]
            for s,t in combinations(sorted(STATES),2):
                x=(rates[a][s]>rates[a][t])-(rates[a][s]<rates[a][t]);y=(rates[b][s]>rates[b][t])-(rates[b][s]<rates[b][t]);category='tie_in_either' if x*y==0 else 'reversal' if x!=y else 'same';condition=conditional[group,a,b,s,t]
                if condition=='guaranteed_same':assert category=='same'
                if condition=='guaranteed_reversal':assert category=='reversal'
                row={'year':2023,'group':group,'denominator_a':a,'denominator_b':b,'state_a':s,'state_b':t,'order_a':x,'order_b':y,'exact_category':category,'rounded_range_category':condition};pairs.append(row);collection.append(row)
            summary.append({'year':2023,'group':group,'denominator_a':a,'denominator_b':b,'pairs':len(collection),**{key:sum(r['exact_category']==key for r in collection) for key in ['same','reversal','tie_in_either']},'guaranteed_same':sum(r['rounded_range_category']=='guaranteed_same' for r in collection),'guaranteed_reversal':sum(r['rounded_range_category']=='guaranteed_reversal' for r in collection),'unresolved':sum(r['rounded_range_category']=='unresolved' for r in collection),'unresolved_actual_reversals':sum(r['rounded_range_category']=='unresolved' and r['exact_category']=='reversal' for r in collection)})
    for name,data in [('exact_subgroup_ranks.csv',ranks),('exact_subgroup_pairs.csv',pairs),('exact_subgroup_summary.csv',summary)]:write_csv(ROOT/'results/evaluation'/name,data)
    print(json.dumps({'phase':'evaluation','exact_subgroup_rank_cells':len(ranks),'exact_subgroup_pair_cells':len(pairs),'all_count_rank_and_guarantee_containment':'PASS'}))

if __name__=='__main__':main()
