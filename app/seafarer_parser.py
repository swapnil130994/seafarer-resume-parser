import re
from datetime import datetime
import dateparser
RANKS=["MASTER","CAPTAIN","CHIEF OFFICER","SECOND OFFICER","THIRD OFFICER","FOURTH OFFICER","DECK CADET","CHIEF ENGINEER","SECOND ENGINEER","THIRD ENGINEER","FOURTH ENGINEER","ETO","ETR","OS","AB","O/S","COOK","FITTER","OILER","WIPER","BOSUN","RATING","TR OS","TRAINEE"]
VESSEL_TYPES=["CONTAINER","BULK CARRIER","BULKER","TANKER","CHEMICAL TANKER","OIL TANKER","LNG","LPG","MBC","NCB","NCV","FG","HARBOUR","OFFSHORE","OSV","AHTS","DREDGER","RO-RO","CAR CARRIER","GENERAL CARGO","CRUDE OIL","PRODUCT TANKER"]
def clean(s): return re.sub(r"\s+"," ",str(s or "")).strip(" \t|:")
def lines(text): return [clean(x) for x in text.splitlines() if clean(x)]
def first_match(patterns,text,flags=re.I|re.M):
    for p in patterns:
        m=re.search(p,text,flags)
        if m:return clean(m.group(1))
    return ""
def email(text):
    m=re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",text); return m.group(0) if m else ""
def phones(text):
    raw=re.findall(r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)",text); out=[]
    for p in raw:
        p=re.sub(r"[^\d+]","",p)
        if p not in out: out.append(p)
    return out
def parse_date(v):
    if not v:return None
    v=clean(v)
    for f in ("%d/%m/%Y","%d-%m-%Y","%d.%m.%Y","%d/%m/%y","%d-%m-%y","%d.%m.%y"):
        try:return datetime.strptime(v,f)
        except ValueError:pass
    try:return dateparser.parse(v,settings={"DATE_ORDER":"DMY"})
    except Exception:return None
def iso_date(v):
    d=parse_date(v); return d.strftime("%Y-%m-%d") if d else ""
def extract_name(text):
    v=first_match([r"\bNAME\s*[:\-]\s*([^\n]+)",r"\bNAME\s+([A-Z][A-Z .]{2,})"],text)
    if v:return v
    for x in lines(text)[:12]:
        if len(x)<=50 and not any(k in x.upper() for k in ["RESUME","CURRICULUM","CURRICULUM VITAE"]):return x
    return ""
def extract_rank(text): return first_match([r"POST\s+APPLIED\s+FOR\s*[:\-]\s*([^\n]+)",r"\bRANK\s*[:\-]\s*([^\n]+)",r"\bPOSITION\s*[:\-]\s*([^\n]+)"],text)
def extract_indos(text): return first_match([r"\bINDOS\s*(?:NO|NUMBER)?\s*[:\-]?\s*([A-Z0-9]{5,})",r"\bINDoS\s*(?:No)?\s*[:\-]?\s*([A-Z0-9]{5,})"],text)
def extract_passport(text): return first_match([r"\b(?:INDIAN\s+)?PASSPORT\s*[:\-]?\s*([A-Z][A-Z0-9]{5,})"],text)
def extract_cdc(text): return first_match([r"\bCDC\s*(?:\([^)]+\))?\s*[:\-]?\s*([A-Z0-9]{5,})",r"\bINDIAN\s+CDC\s*[:\-]?\s*([A-Z0-9]{5,})"],text)
def extract_coc(text): return first_match([r"\bCOC\s*(?:NO|NUMBER)?\s*[:\-]?\s*([A-Z0-9/\-]{5,})"],text)
def extract_sid(text): return first_match([r"\bSID\s*(?:NO|NUMBER)?\s*[:\-]?\s*([A-Z0-9/\-]{5,})",r"\bSEAFARERS?\s+IDENTITY\s+DOC(?:UMENT)?\s*[:\-]?\s*([A-Z0-9/\-]{5,})"],text)
def extract_languages(text): return first_match([r"LANGUAGES?\s*(?:KNOWN)?\s*[:\-]\s*([^\n]+)",r"LANGUASE\s*(?:KNOWN)?\s*[:\-]\s*([^\n]+)"],text)
def extract_address(text): return clean(first_match([r"\bADDRESS\s*[:\-]\s*(.+?)(?=\n(?:DOCUMENT|PERSONAL|PROFESSIONAL|ACADEMIC|STATUTORY|COURSE|SEA\s+SERVICE|DECLARATION)\b)",r"\bPRESENT\s+ADDRESS\s+(.+?)(?=\n(?:PERMANENT|DOCUMENT|COURSE|SEA\s+SERVICE)\b)"],text,re.I|re.S))
def extract_nationality(text): return first_match([r"NATIONALITY\s*[:\-]\s*([^\n]+)"],text)
def extract_gender(text): return first_match([r"GENDER\s*[:\-]\s*([^\n]+)",r"SEX\s*[:\-]\s*([^\n]+)"],text)
def extract_religion(text): return first_match([r"RELIGION\s*[:\-]\s*([^\n]+)"],text)
def extract_marital(text): return first_match([r"MARITAL\s*STATUS\s*[:\-]\s*([^\n]+)",r"MARITALSTATUS\s*[:\-]\s*([^\n]+)"],text)
def document_dates(text,label):
    ls=lines(text)
    for i,line in enumerate(ls):
        if label.upper() in line.upper():
            ctx=" ".join(ls[i:i+3]); ds=re.findall(r"\b\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4}\b",ctx)
            return (iso_date(ds[0]) if ds else "",iso_date(ds[1]) if len(ds)>1 else "")
    return "",""
def detect_rank(c):
    u=c.upper()
    for r in sorted(RANKS,key=len,reverse=True):
        if re.search(r"\b"+re.escape(r)+r"\b",u):return r
    return ""
def detect_vessel_type(c):
    u=c.upper()
    for v in sorted(VESSEL_TYPES,key=len,reverse=True):
        if v in u:return v
    return ""
def detect_grt(c):
    m=re.search(r"\bGRT\s*[:\-]?\s*(\d{2,7}(?:\.\d+)?)",c,re.I); return m.group(1) if m else ""
def detect_company(c):
    for x in c.split("|"):
        x=clean(x); u=x.upper()
        if any(k in u for k in ["LTD","PVT","PRIVATE","SHIPPING","MARINE","MARITIME","SHIP MANAGEMENT"]):return x
    return ""
def date_pair(line):
    ds=re.findall(r"\b\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4}\b",line)
    if len(ds)>=2:
        a,b=parse_date(ds[-2]),parse_date(ds[-1])
        if a and b:return a,b
    return None,None
def sea_records(text):
    ls=lines(text); recs=[]; inside=False
    for i,line in enumerate(ls):
        u=line.upper()
        if "SEA SERVICE" in u or "SEA EXPERIENCE" in u: inside=True; continue
        if inside and any(k in u for k in ["DECLARATION","YOURS FAITHFULLY","SIGNATURE"]): break
        if not inside: continue
        a,b=date_pair(line)
        if not a or not b: continue
        ctx=" | ".join(ls[max(0,i-5):i+1])
        rec={"indos":"","rank":detect_rank(ctx),"company_name":detect_company(ctx),"vessel_name":"","vessel_type":detect_vessel_type(ctx),"grt":detect_grt(ctx),"from_date":a.strftime("%Y-%m-%d"),"to_date":b.strftime("%Y-%m-%d")}
        pieces=[clean(x) for x in ctx.split("|") if clean(x)]
        for p in reversed(pieces):
            pu=p.upper()
            if re.search(r"\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4}",p):continue
            if p==rec["company_name"] or pu in {rec["rank"],rec["vessel_type"]}:continue
            if re.fullmatch(r"\d{2,7}",p):continue
            if len(p)<=80:rec["vessel_name"]=p;break
        recs.append(rec)
    return recs
def total_months(records):
    ps=[]
    for r in records:
        a,b=parse_date(r.get("from_date")),parse_date(r.get("to_date"))
        if a and b and b>=a:ps.append((a,b))
    if not ps:return 0.0
    ps.sort(); merged=[list(ps[0])]
    for a,b in ps[1:]:
        if a<=merged[-1][1]: merged[-1][1]=max(merged[-1][1],b)
        else: merged.append([a,b])
    return round(sum((b-a).days+1 for a,b in merged)/30.4375,2)
def unique_types(records):
    out=[]; seen=set()
    for r in records:
        x=clean(r.get("vessel_type"))
        if x and x.upper() not in seen:seen.add(x.upper());out.append(x)
    return ", ".join(out)
def course_details(text):
    ls=lines(text); out=[]; inside=False
    for line in ls:
        u=line.upper()
        if "COURSE DETAILS" in u or "STCW COURSE DETAILS" in u or "COURSE NAME" in u:inside=True;continue
        if inside and any(k in u for k in ["SEA SERVICE","STATUTORY DOCUMENT","DECLARATION"]):break
        if not inside:continue
        dm=re.search(r"\b\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4}\b",line)
        cm=re.search(r"\b[A-Z0-9][A-Z0-9/\-.]{7,}\b",line,re.I)
        if not dm and not cm:continue
        course=line
        if cm:course=course.replace(cm.group(0)," ")
        if dm:course=course.replace(dm.group(0)," ")
        course=clean(course)
        if not course or course.upper() in {"COURSE","CERTIFICATE NO","PLACE OF ISSUE"}:continue
        out.append({"course_name":course,"company_name":"","certificate_no":cm.group(0) if cm else "","from_date":iso_date(dm.group(0)) if dm else "","to_date":""})
    return out
def parse_resume(text,filename):
    p=phones(text); addr=extract_address(text); pf,pt=document_dates(text,"PASSPORT"); cf,ct=document_dates(text,"CDC"); cof,cot=document_dates(text,"COC")
    recs=sea_records(text); indos=extract_indos(text)
    for r in recs:r["indos"]=indos
    return {"personal_details":{"name":extract_name(text),"indos":indos,"email":email(text),"rank":extract_rank(text),"mobile_no":p[0] if p else "","alternate_mobile_no":p[1] if len(p)>1 else "","city":"","state":"","address":addr,"nationality":extract_nationality(text),"gender":extract_gender(text),"religion":extract_religion(text),"married_status":extract_marital(text),"passport_no":extract_passport(text),"passport_from_date":pf,"passport_to_date":pt,"sid_no":extract_sid(text),"coc_no":extract_coc(text),"coc_country":"","coc_from_date":cof,"coc_to_date":cot,"cdc_country":"","cdc_no":extract_cdc(text),"cdc_from_date":cf,"cdc_to_date":ct,"language_knows":extract_languages(text)},"sea_experience":{"indos":indos,"total_experience_month":total_months(recs),"vessel_types":unique_types(recs),"records":recs},"course_details":course_details(text),"uploaded_file_name":filename}
