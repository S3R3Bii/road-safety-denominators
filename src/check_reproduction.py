"""Offline replay from selected factual cells; fullPDFs andlive services are excluded."""
import csv,hashlib,json,math,shutil,subprocess,sys,tempfile
from pathlib import Path
from config import ROOT

def read(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def main():
    freeze=json.loads((ROOT/'results/CODE_FREEZE.json').read_text())
    for name,digest in freeze['sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==digest,name
    exact=floating=0
    with tempfile.TemporaryDirectory(prefix='road-replay-') as temp:
        out=Path(temp)
        for name in ['src','data']:shutil.copytree(ROOT/name,out/name)
        (out/'results').mkdir()
        commands=[['ingest.py'],['analyze.py','development'],['verify_analysis.py','development'],['analyze.py','evaluation'],['verify_analysis.py','evaluation'],['analyze_exact_subgroups.py'],['verify_exact_subgroups.py']]
        for args in commands:subprocess.run([sys.executable,str(out/'src'/args[0]),*args[1:]],check=True,capture_output=True,text=True)
        targets=['data/measurements.csv','results/national_reconciliation.csv','results/SOURCE_CHECK.json',*[f'results/{phase}/{name}' for phase in ['development','evaluation'] for name in ['exact_ranks.csv','exact_pairs.csv','exact_summary.csv','rate_placement_bounds.csv','bounded_pairs.csv','bounded_summary.csv','summary.json']],*[f'results/evaluation/{name}' for name in ['exact_subgroup_ranks.csv','exact_subgroup_pairs.csv','exact_subgroup_summary.csv']]]
        float_columns={'rate','midrank','rate_lower','rate_upper','max_abs_midrank_movement'}
        for name in targets:
            a=ROOT/name;b=out/name
            if a.suffix=='.csv':
                left=read(a);right=read(b);assert len(left)==len(right),name
                for x,y in zip(left,right):
                    assert x.keys()==y.keys()
                    for k in x:
                        if k in float_columns:assert math.isclose(float(x[k]),float(y[k]),rel_tol=0,abs_tol=1e-12);floating+=1
                        else:assert x[k]==y[k],(name,k);exact+=1
            else:assert json.loads(a.read_text())==json.loads(b.read_text()),name;exact+=1
        for name in ['development/INDEPENDENT_CHECK.json','evaluation/INDEPENDENT_CHECK.json','evaluation/EXACT_SUBGROUP_CHECK.json']:assert json.loads((out/'results'/name).read_text())['status']=='PASS'
    result={'status':'PASS','exact_fields_or_json_documents':exact,'floating_fields':floating,'frozen_dependencies':len(freeze['sha256']),'scope':'Isolatedselected-factsourcejoin,all exact/conditional/exact-subgroupoutputs andindependent reconstructions;noPDF,network orprivateoriginalrequired'}
    (ROOT/'results/REPRODUCTION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))

if __name__=='__main__':main()
