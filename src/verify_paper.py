"""Check every manuscript table, headline, approved byte and bounded PDF exclusion."""
import csv,hashlib,json,re,unicodedata
from pypdf import PdfReader
from config import ROOT

def read(name):
    with (ROOT/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def main():
    scope=json.loads((ROOT/'paper/PUBLICATION_SCOPE.json').read_text());assert scope['scope']=='independent-program-study' and scope['formal_submission_target'] is False and len(scope['public_files'])==5
    for n,digest in scope['public_files'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==digest,n
    tex=(ROOT/'paper/main.tex').read_text(encoding='utf-8');checks=0
    def require(text):
        nonlocal checks
        assert text in tex,text;checks+=1
    source=json.loads((ROOT/'results/SOURCE_CHECK.json').read_text());indsource=json.loads((ROOT/'results/INDEPENDENT_SOURCE_CHECK.json').read_text());dev=json.loads((ROOT/'results/development/INDEPENDENT_CHECK.json').read_text());ev=json.loads((ROOT/'results/evaluation/INDEPENDENT_CHECK.json').read_text());sub=json.loads((ROOT/'results/evaluation/EXACT_SUBGROUP_CHECK.json').read_text());replay=json.loads((ROOT/'results/REPRODUCTION.json').read_text());fig=json.loads((ROOT/'results/FIGURE_CHECK.json').read_text())
    assert all(j['status']=='PASS' for j in [source,indsource,dev,ev,sub,replay,fig])
    for v in [source['state_year_rows'],source['source_numeric_checks'],indsource['independent_selected_cell_and_locator_checks'],dev['independent_value_checks'],ev['independent_value_checks'],sub['independent_value_checks'],replay['exact_fields_or_json_documents'],replay['floating_fields'],fig['plotted_values']]:require(f'{v:,}')
    labels={'population':'Population','licensed_drivers':'Licensed drivers','vmt_millions':'Vehicle miles'}
    exact=[r for phase in ['development','evaluation'] for r in read(f'results/{phase}/exact_summary.csv')]
    assert len(exact)==9
    for r in exact:require(' & '.join([r['year'],labels[r['denominator_a']]+' / '+labels[r['denominator_b']],r['reversal'],str(int(float(r['max_abs_midrank_movement']))),r['top5_overlap'],r['top10_overlap']]))
    for r in read('results/evaluation/exact_subgroup_summary.csv'):
        if r['denominator_a']=='population' and r['denominator_b']=='vmt_millions':require(' & '.join([r['group'].capitalize(),r['reversal'],r['guaranteed_reversal'],r['unresolved'],r['unresolved_actual_reversals'],r['tie_in_either']]))
    ranks=read('results/evaluation/exact_ranks.csv');lookup={(r['state'],r['denominator']):float(r['midrank']) for r in ranks};states=sorted({r['state'] for r in ranks});selected=sorted(states,key=lambda s:(-abs(lookup[s,'population']-lookup[s,'vmt_millions']),s))[:5]
    for s in selected:require(f"{s} & {lookup[s,'population']:.0f} & {lookup[s,'vmt_millions']:.0f} & {lookup[s,'vmt_millions']-lookup[s,'population']:+.0f}")
    for year,month,pub,total in [(2019,'October 2021','183',36096),(2021,'September 2023','509',42939),(2023,'August 2025','743',40901)]:require(f'{year} & {month}; DOT HS 813 {pub} & {total:,} & 51')
    reconcile=read('results/national_reconciliation.csv')
    for r in reconcile:
        if r['field']!='vmt_millions':assert int(r['difference'])==0
    assert [int(r['difference']) for r in reconcile if r['field']=='vmt_millions']==[2,2,1]
    for token in ['222 / 1,275','21 places','2 / 6 states',r'17.4\%','from rank 47','rank 26','only 7 of the 126','119 of those reversals','461 pairs','262 exact reversals','186 compare with 128','nineteen-dependency freeze','source cells were not blinded','not confidence intervals','not estimate resident death risk','not a model search','not person-level','2023 coarsening','exact comparator','Registered-vehicle counts/rates are excluded']:
        require(token)
    for command in ['python -m pip install -r requirements.txt','python -m unittest discover -s tests -v','python src/check_reproduction.py','python src/verify_figures.py','python src/verify_paper.py','python src/verify_public_package.py']:require(command)
    reader=PdfReader(ROOT/'paper/manuscript.pdf');assert len(reader.pages)==8 and not reader.is_encrypted
    page_text=[unicodedata.normalize('NFKC',p.extract_text() or '') for p in reader.pages]
    titles=['Decision and verified finding','1. Fixed source panel and boundaries','2. Exact rates and conditional precision ranges','3. The primary state comparison','4. Complete all-fatality contrasts','5. Rounded shares and the fair exact-count comparator','6. Interpretation, limitations and next evidence','7. Reproduction and independent checks']
    for page,title in zip(page_text,titles):assert title in re.sub(r'\s+',' ',page),title
    text='\n'.join(page_text)
    normalized=re.sub(r'\s+',' ',text)
    for command in ['python -m pip install -r requirements.txt','python -m unittest discover -s tests -v','python src/check_reproduction.py','python src/verify_figures.py','python src/verify_paper.py','python src/verify_public_package.py']:assert command in normalized;checks+=1
    assert not re.search(r'(?:[Cc]:\\[Uu]sers\\|/[Uu]sers/|/[Hh]ome/|github_pat_|ghp_[A-Za-z0-9]{20,})',text)
    catalog=reader.trailer['/Root'];assert not any(k in catalog for k in ['/AA','/AcroForm','/Collection'])
    assert not reader.attachments
    names=catalog.get('/Names',{});names=names.get_object() if hasattr(names,'get_object') else names;assert '/JavaScript' not in names
    if '/OpenAction' in catalog:
        action=catalog['/OpenAction'];assert isinstance(action,list),'Active open action rejected'
    for page in reader.pages:
        assert '/AA' not in page
        for ref in page.get('/Annots',[]):
            annot=ref.get_object();assert '/AA' not in annot
            action=annot.get('/A')
            if action:
                action=action.get_object();assert action['/S'] in ['/URI','/GoTo']
                if action['/S']=='/URI':assert str(action['/URI']).startswith('https://')

    result={'status':'PASS','manuscript_pages':8,'numeric_table_and_text_checks':checks,'public_file_hashes_checked':5,'pdf_security':'No activecode,attachments,forms oradditionalactions;ordinaryHTTPSlinks/navigationonly','scope':'Allnineall-fatalitycontrasts;allheadlinetables;sourceversion/reconciliation/checkcounts;primaryexactsubgroupcomparator;requiredsectionsandcommands;boundedpath/tokenscan'}
    (ROOT/'results/PAPER_CHECK.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))

if __name__=='__main__':main()
