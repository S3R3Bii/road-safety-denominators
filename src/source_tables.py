"""Select factual cells from fixed NHTSA tables; keep report expression outside Git."""
import csv,gzip,io,re,unicodedata
from email.parser import BytesParser
from email.policy import default
from config import STATES
ALIASES={**{s:s for s in STATES},'Dist of Columbia':'District of Columbia','Dist. of Columbia':'District of Columbia','U.S. Total':'U.S. Total','Puerto Rico':'Puerto Rico'}
T1=['fatalities','population','licensed_drivers','vmt_millions','rate_population','rate_licensed_drivers','rate_vmt']
T7=['fatalities','drivers_pct','passengers_pct','motorcyclists_pct','pedestrians_pct','pedalcyclists_pct']

def decode(data):
    if data.startswith(b'%PDF'):return data,'direct-pdf'
    first=data.splitlines()[0];assert first.startswith(b'--') and b'WebKitFormBoundary' in first,'Unknown source wrapper'
    boundary=first[2:];message=BytesParser(policy=default).parsebytes(b'Content-Type: multipart/form-data; boundary="'+boundary+b'"\r\nMIME-Version: 1.0\r\n\r\n'+data)
    parts=[p for p in message.walk() if not p.is_multipart()];assert len(parts)==1
    payload=parts[0].get_payload(decode=True);assert payload.startswith(b'%PDF')
    return payload,'single-part-multipart-pdf'

def parse_lines(text,year,table,page):
    rows=[]
    for line in unicodedata.normalize('NFKC',text).splitlines():
        line=re.sub(r'\s+',' ',line).strip()
        for label in sorted(ALIASES,key=len,reverse=True):
            if not re.match(re.escape(label)+r'\*?\s+[0-9]',line):continue
            body=re.sub('^'+re.escape(label)+r'\*?\s+','',line)
            tokens=body.split();wanted=[9] if table==1 else [6,11]
            assert len(tokens) in wanted,(year,table,page,label,'Unexpected column count',len(tokens))
            fields=T1 if table==1 else T7;values=[tokens[i] for i in [0,1,2,4,5,6,8]] if table==1 else tokens
            if table==7:
                values=[tokens[0],*[tokens[i] for i in [2,4,6,8,10]]] if len(tokens)==11 else tokens
            selected=dict(zip(fields,values))
            if table==7:selected.update({name+'_count':tokens[1+2*i] if len(tokens)==11 else '' for i,name in enumerate(['drivers','passengers','motorcyclists','pedestrians','pedalcyclists'])})
            rows.append(dict(year=str(year),state=ALIASES[label],source_label=label,page=str(page),**selected))
            break
    return rows

def select_pages(reader,table,year):
    selected=[]
    for i,page in enumerate(reader.pages):
        text=page.extract_text() or ''
        if re.search(r'\bTable\s+'+str(table)+r'\b',text) and 'Alabama' in text and ('Traffic Fatalities and Fatality Rates' if table==1 else 'Person Type') in text:selected.append((i+1,text))
    assert len(selected)==1,(year,table,'Expected one complete table page',len(selected))
    return selected

def write_gz(path,rows):
    buf=io.StringIO(newline='');w=csv.DictWriter(buf,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows);path.write_bytes(gzip.compress(buf.getvalue().encode('utf-8'),mtime=0))

def read_gz(path):
    with gzip.open(path,'rt',encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
