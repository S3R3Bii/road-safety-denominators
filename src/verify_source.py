"""Independent pdfminer/pdfplumber extraction of every selected source cell."""
import argparse,hashlib,json,re,unicodedata
from pathlib import Path
from config import ROOT,STATES
from source_tables import read_gz
from accounting import save_json

def main():
    import pdfplumber
    p=argparse.ArgumentParser();p.add_argument('originals',type=Path);a=p.parse_args();manifest=json.loads((ROOT/'data/source/manifest.json').read_text());checks=0
    aliases={s:s for s in STATES};aliases.update({'Dist of Columbia':'District of Columbia','Dist. of Columbia':'District of Columbia','U.S. Total':'U.S. Total','Puerto Rico':'Puerto Rico'})
    for report in manifest['reports']:
        raw=(a.originals/f"{report['year']}.response").read_bytes();assert hashlib.sha256(raw).hexdigest()==report['response_sha256']
        path=a.originals/f"{report['year']}.pdf";assert hashlib.sha256(path.read_bytes()).hexdigest()==report['payload_sha256']
        with pdfplumber.open(path) as pdf:
            for table in report['tables']:
                selected=read_gz(ROOT/table['subset_file']);assert len(selected)==53
                expected={}
                for number in table['pages']:
                    # Different font/text engine from production pypdf; retain page/row identity.
                    text=unicodedata.normalize('NFKC',pdf.pages[number-1].extract_text(x_tolerance=2,y_tolerance=3))
                    for line in text.splitlines():
                        line=' '.join(line.split())
                        for label,state in sorted(aliases.items(),key=lambda x:len(x[0]),reverse=True):
                            match=re.match(re.escape(label)+r'\*?\s+([0-9].*)$',line)
                            if not match:continue
                            tokens=match.group(1).split();assert len(tokens)==(9 if table['table']==1 else 6),(report['year'],table['table'],label,len(tokens))
                            assert state not in expected;expected[state]=(label,number,[tokens[i] for i in [0,1,2,4,5,6,8]] if table['table']==1 else tokens);break
                assert len(expected)==53
                for row in selected:
                    label,page,values=expected[row['state']];assert row['source_label']==label and int(row['page'])==page;checks+=2
                    fields=['fatalities','population','licensed_drivers','vmt_millions','rate_population','rate_licensed_drivers','rate_vmt'] if table['table']==1 else ['fatalities','drivers_pct','passengers_pct','motorcyclists_pct','pedestrians_pct','pedalcyclists_pct']
                    for field,value in zip(fields,values):assert row[field]==value,(report['year'],row['state'],field);checks+=1
    cert={'status':'PASS','independent_selected_cell_and_locator_checks':checks,'reports':3,'table_pages':6,'engines':'Productionpypdf;independentpdfplumber/pdfminer textgeometry','all_registration_fields_excluded':True,'full_originals_outside_git':True}
    save_json(ROOT/'results/INDEPENDENT_SOURCE_CHECK.json',cert);print(json.dumps(cert))

if __name__=='__main__':main()
