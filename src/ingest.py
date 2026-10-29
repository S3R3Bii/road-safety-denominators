"""Enforce fixed source, coverage, arithmetic and rounded-share gates."""
import hashlib,json
from fractions import Fraction
from config import ROOT,YEARS,STATES,SHARES,DENOMS
from source_tables import read_gz
from accounting import integer,feasible,write_csv,save_json

def main():
    manifest=json.loads((ROOT/'data/source/manifest.json').read_text());normalized=[];reconciliations=[];checks=0
    for report in manifest['reports']:
        year=report['year'];assert year in YEARS;tables={}
        for part in report['tables']:
            path=ROOT/part['subset_file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==part['subset_sha256'];rows=read_gz(path)
            assert len(rows)==53 and len({r['state'] for r in rows})==53;assert {r['state'] for r in rows}==set(STATES)|{'U.S. Total','Puerto Rico'}
            tables[part['table']]={r['state']:r for r in rows}
        for state in [*STATES,'U.S. Total']:
            a=tables[1][state];b=tables[7][state];n=integer(a['fatalities']);assert n==integer(b['fatalities']) and n>=0;checks+=1
            ds={d:integer(a[d]) for d in DENOMS};assert all(x>0 for x in ds.values());shares={s:integer(b[s+'_pct']) for s in SHARES};assert all(0<=x<=100 for x in shares.values());feasible(n,shares);checks+=6
            for denom,col,scale in [('population','rate_population',100000),('licensed_drivers','rate_licensed_drivers',100000),('vmt_millions','rate_vmt',100)]:
                displayed=Fraction(a[col]);low=displayed-Fraction(1,200);high=displayed+Fraction(1,200)
                if denom=='vmt_millions':possible_low=Fraction(2*n*scale,2*ds[denom]+1);possible_high=Fraction(2*n*scale,2*ds[denom]-1)
                else:possible_low=possible_high=Fraction(n*scale,ds[denom])
                assert possible_low<=high and possible_high>=low,(year,state,denom,'Published rate inconsistency');checks+=1
            if state in STATES:normalized.append({'year':year,'state':state,'fatalities':n,**ds,**{s+'_pct':p for s,p in shares.items()}})
        for field in ['fatalities',*DENOMS]:
            state_sum=sum(integer(tables[1][state][field]) for state in STATES);national=integer(tables[1]['U.S. Total'][field]);difference=state_sum-national
            if field=='fatalities':assert difference==0,'Fatality national reconciliation'
            reconciliations.append({'year':year,'field':field,'state_sum':state_sum,'published_national':national,'difference':difference})
    assert len(normalized)==153 and {r['year'] for r in normalized}==set(YEARS)
    write_csv(ROOT/'data/measurements.csv',normalized);write_csv(ROOT/'results/national_reconciliation.csv',reconciliations)
    cert={'status':'PASS','state_year_rows':len(normalized),'source_rows_per_table_year':53,'eligible_states_per_year':51,'excluded':'PuertoRico excluded from comparisons;U.S.total accounting only;allregistration fields excluded','source_numeric_checks':checks,'fatality_sums':'Exact across51states/DC ineachreport vintage','denominator_reconciliations':'All differences retained;no rescaling','rounding_gate':'Closed0.005displayed-rate interval;VMTplus/minus0.5million only;allreported sourcevalues unchanged'}
    save_json(ROOT/'results/SOURCE_CHECK.json',cert);print(json.dumps(cert))

if __name__=='__main__':main()
