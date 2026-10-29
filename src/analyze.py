"""All prespecified exact comparisons and conservative precision classifications."""
import argparse
from fractions import Fraction
from itertools import combinations
from config import ROOT,DENOMS,GROUPS,SHARES,DEV_YEARS,EVAL_YEARS
from accounting import read,feasible,midranks,top_set,dominance,placement,write_csv,save_json

def analyze(phase):
    years=DEV_YEARS if phase=='development' else EVAL_YEARS;source=[r for r in read() if r['year'] in years]
    out=ROOT/'results'/phase;out.mkdir(exist_ok=True);ranks=[];pairs=[];summaries=[];bounds_rows=[];bound_pairs=[];bound_summaries=[]
    for year in years:
        rows={r['state']:r for r in source if r['year']==year};states=sorted(rows);rates={};rankmap={};ranges={}
        for denom in DENOMS:
            scale=100 if denom=='vmt_millions' else 100000
            values={s:Fraction(r['fatalities']*scale,r[denom]) for s,r in rows.items()};rates[denom]=values;rm=midranks(values);rankmap[denom]=rm
            for s in states:ranks.append({'year':year,'state':s,'denominator':denom,'rate_numerator':values[s].numerator,'rate_denominator':values[s].denominator,'rate':float(values[s]),'midrank_numerator':rm[s].numerator,'midrank_denominator':rm[s].denominator,'midrank':float(rm[s]),'top5':int(s in top_set(values,5)),'top10':int(s in top_set(values,10))})
        for a,b in combinations(DENOMS,2):
            group=[]
            for s,t in combinations(states,2):
                x=(rates[a][s]>rates[a][t])-(rates[a][s]<rates[a][t]);y=(rates[b][s]>rates[b][t])-(rates[b][s]<rates[b][t]);category='tie_in_either' if x*y==0 else 'reversal' if x!=y else 'same'
                result={'year':year,'denominator_a':a,'denominator_b':b,'state_a':s,'state_b':t,'order_a':x,'order_b':y,'category':category};pairs.append(result);group.append(result)
            summaries.append({'year':year,'denominator_a':a,'denominator_b':b,'pairs':len(group),**{key:sum(r['category']==key for r in group) for key in ['same','reversal','tie_in_either']},'max_abs_midrank_movement':float(max(abs(rankmap[a][s]-rankmap[b][s]) for s in states)),'top5_a_size':len(top_set(rates[a],5)),'top5_b_size':len(top_set(rates[b],5)),'top5_overlap':len(top_set(rates[a],5)&top_set(rates[b],5)),'top10_a_size':len(top_set(rates[a],10)),'top10_b_size':len(top_set(rates[b],10)),'top10_overlap':len(top_set(rates[a],10)&top_set(rates[b],10))})
        for group in GROUPS:
            for denom in DENOMS:
                values={};stored={}
                for s,r in rows.items():
                    lo,hi=(r['fatalities'],r['fatalities']) if group=='all' else feasible(r['fatalities'],{k:r[k+'_pct'] for k in SHARES})[group]
                    dl=Fraction(r[denom])-Fraction(1,2) if denom=='vmt_millions' else Fraction(r[denom]);dh=Fraction(r[denom])+Fraction(1,2) if denom=='vmt_millions' else Fraction(r[denom]);assert dl>0
                    scale=100 if denom=='vmt_millions' else 100000;lrate=lo*scale/dh;hrate=hi*scale/dl;values[s]=(lrate,hrate);stored[s]=(lo,hi,lrate,hrate)
                ranges[group,denom]=values
                for s in states:
                    lo,hi,lrate,hrate=stored[s];best,worst=placement(values,s)
                    bounds_rows.append({'year':year,'state':s,'group':group,'denominator':denom,'count_lower':lo,'count_upper':hi,'rate_lower_numerator':lrate.numerator,'rate_lower_denominator':lrate.denominator,'rate_upper_numerator':hrate.numerator,'rate_upper_denominator':hrate.denominator,'rate_lower':float(lrate),'rate_upper':float(hrate),'best_ordinal_placement':best,'worst_ordinal_placement':worst})
            for a,b in combinations(DENOMS,2):
                collection=[]
                for s,t in combinations(states,2):
                    x=dominance(ranges[group,a][s],ranges[group,a][t]);y=dominance(ranges[group,b][s],ranges[group,b][t]);category='unresolved' if x*y==0 else 'guaranteed_reversal' if x!=y else 'guaranteed_same'
                    result={'year':year,'group':group,'denominator_a':a,'denominator_b':b,'state_a':s,'state_b':t,'dominance_a':x,'dominance_b':y,'category':category};bound_pairs.append(result);collection.append(result)
                bound_summaries.append({'year':year,'group':group,'denominator_a':a,'denominator_b':b,'pairs':len(collection),**{key:sum(r['category']==key for r in collection) for key in ['guaranteed_same','guaranteed_reversal','unresolved']}})
    for name,data in [('exact_ranks.csv',ranks),('exact_pairs.csv',pairs),('exact_summary.csv',summaries),('rate_placement_bounds.csv',bounds_rows),('bounded_pairs.csv',bound_pairs),('bounded_summary.csv',bound_summaries)]:write_csv(out/name,data)
    save_json(out/'summary.json',{'phase':phase,'years':years,'states':51,'all_fatality_rank_cells':len(ranks),'exact_pair_comparisons':len(pairs),'conditional_rate_bound_cells':len(bounds_rows),'bounded_pair_comparisons':len(bound_pairs),'groups':GROUPS,'limits':'Within-report-year comparisons;printed precision ranges only;no harmonized subgroup trend,person-distance,individual risk or causal claim'})
    print({'phase':phase,'rank_cells':len(ranks),'exact_pairs':len(pairs),'bounds':len(bounds_rows),'bounded_pairs':len(bound_pairs)})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['development','evaluation']);analyze(p.parse_args().phase)
