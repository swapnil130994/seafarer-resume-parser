import re
from datetime import datetime
from calendar import monthrange

# Broad normalization dictionaries. The parser also uses keyword/regex fallbacks
# so uncommon spellings are not discarded.
RANK_ALIASES = [
    ("CHIEF ELECTRICAL OFFICER", "Chief Electrical Officer"),
    ("CHIEF ELECTRO TECHNICAL OFFICER", "Chief Electrical Officer"),
    ("ELECTRO TECHNICAL OFFICER", "ETO"),
    ("ELECTRICAL OFFICER", "Electrical Officer"),
    ("ELECTRICIAN", "Electrician"),
    ("OFFSHORE ELECTRICIAN", "Electrician"),
    ("MARINE ELECTRICIAN", "Electrician"),
    ("RIG ELECTRICIAN", "Electrician"),
    ("CHIEF ENGINEER", "Chief Engineer"),
    ("SECOND ENGINEER", "Second Engineer"),
    ("2ND ENGINEER", "Second Engineer"),
    ("THIRD ENGINEER", "Third Engineer"),
    ("3RD ENGINEER", "Third Engineer"),
    ("FOURTH ENGINEER", "Fourth Engineer"),
    ("4TH ENGINEER", "Fourth Engineer"),
    ("FIRST ENGINEER", "First Engineer"),
    ("CHIEF OFFICER", "Chief Officer"),
    ("FIRST OFFICER", "Chief Officer"),
    ("SECOND OFFICER", "Second Officer"),
    ("2ND OFFICER", "Second Officer"),
    ("THIRD OFFICER", "Third Officer"),
    ("3RD OFFICER", "Third Officer"),
    ("FOURTH OFFICER", "Fourth Officer"),
    ("4TH OFFICER", "Fourth Officer"),
    ("DECK OFFICER", "Deck Officer"),
    ("MASTER MARINER", "Master"),
    ("CAPTAIN", "Captain"),
    ("MASTER", "Master"),
    ("ETO", "ETO"),
    ("ELECTRO TECHNICAL OFFICER", "ETO"),
    ("ETR", "ETR"),
    ("ELECTRO TECHNICAL RATING", "ETR"),
    ("DECK CADET", "Deck Cadet"),
    ("ENGINE CADET", "Engine Cadet"),
    ("CADET", "Cadet"),
    ("BOSUN", "Bosun"),
    ("BOATSWAIN", "Bosun"),
    ("ABLE SEAMAN", "AB"),
    ("ABLE BODIED SEAMAN", "AB"),
    ("A/B", "AB"),
    ("O/S", "OS"),
    ("ORDINARY SEAMAN", "OS"),
    ("OS/AB", "OS/AB"),
    ("AB/OS", "AB/OS"),
    ("GENERAL PURPOSE RATING", "GP Rating"),
    ("GP RATING", "GP Rating"),
    ("TR OS", "TR OS"),
    ("TRAINEE OS", "Trainee OS"),
    ("TRAINEE", "Trainee"),
    ("FITTER", "Fitter"),
    ("MOTORMAN", "Motorman"),
    ("OILER", "Oiler"),
    ("WIPER", "Wiper"),
    ("PUMPMAN", "Pumpman"),
    ("DECK FITTER", "Deck Fitter"),
    ("ENGINE FITTER", "Engine Fitter"),
    ("COOK", "Cook"),
    ("CHIEF COOK", "Chief Cook"),
    ("MESSMAN", "Messman"),
    ("STEWARD", "Steward"),
    ("CHIEF STEWARD", "Chief Steward"),
    ("ABCOOK", "AB/Cook"),
    ("RATING", "Rating"),
    ("WATCHKEEPING", "Watchkeeping"),
]

VESSEL_ALIASES = [
    ("ULTRA LARGE CONTAINER VESSEL", "Container"),
    ("CONTAINER VESSEL", "Container"),
    ("CONTAINER SHIP", "Container"),
    ("CONTAINER", "Container"),
    ("VERY LARGE CRUDE CARRIER", "VLCC"),
    ("VLCC", "VLCC"),
    ("SUEZMAX", "Suezmax"),
    ("AFRAMAX", "Aframax"),
    ("CRUDE OIL TANKER", "Crude Oil Tanker"),
    ("PRODUCT TANKER", "Product Tanker"),
    ("OIL TANKER", "Oil Tanker"),
    ("CHEMICAL TANKER", "Chemical Tanker"),
    ("LNG CARRIER", "LNG"),
    ("LNG", "LNG"),
    ("LPG CARRIER", "LPG"),
    ("LPG", "LPG"),
    ("BITUMEN TANKER", "Bitumen Tanker"),
    ("TANKER", "Tanker"),
    ("BULK CARRIER", "Bulk Carrier"),
    ("BULK CARRIER VESSEL", "Bulk Carrier"),
    ("BULKER", "Bulker"),
    ("ORE CARRIER", "Ore Carrier"),
    ("GENERAL CARGO", "General Cargo"),
    ("MULTIPURPOSE", "Multipurpose Vessel"),
    ("MPP", "Multipurpose Vessel"),
    ("RO-RO", "Ro-Ro"),
    ("RORO", "Ro-Ro"),
    ("CAR CARRIER", "Car Carrier"),
    ("PCTC", "Car Carrier"),
    ("HEAVY LIFT PIPELAY VESSEL", "Heavy Lift Pipelay Vessel"),
    ("HEAVY LIFT PIPELAY", "Heavy Lift Pipelay Vessel"),
    ("PIPELAY VESSEL", "Pipelay Vessel"),
    ("PIPE LAY VESSEL", "Pipelay Vessel"),
    ("HEAVY LIFT", "Heavy Lift"),
    ("DP3 ACCOMMODATION VESSEL", "Accommodation Vessel"),
    ("ACCOMMODATION VESSEL", "Accommodation Vessel"),
    ("ACCOMMODATION BARGE", "Accommodation Barge"),
    ("ACCOMMODATION", "Accommodation Vessel"),
    ("AHTS VESSEL", "AHTS"),
    ("AHTS", "AHTS"),
    ("ANCHOR HANDLING", "AHTS"),
    ("PLATFORM SUPPLY VESSEL", "PSV"),
    ("PLATFORM SUPPLY", "PSV"),
    ("PSV", "PSV"),
    ("OFFSHORE SUPPLY VESSEL", "OSV"),
    ("OFFSHORE SUPPLY", "OSV"),
    ("OSV", "OSV"),
    ("OFFSHORE SUPPORT VESSEL", "OSV"),
    ("CREW BOAT", "Crew Boat"),
    ("FAST CREW", "Crew Boat"),
    ("DIVE SUPPORT VESSEL", "DSV"),
    ("DSV", "DSV"),
    ("CONSTRUCTION SUPPORT VESSEL", "CSV"),
    ("CSV", "CSV"),
    ("WIND FARM SUPPORT", "Wind Farm Support Vessel"),
    ("WIND TURBINE INSTALLATION", "WTIV"),
    ("WTIV", "WTIV"),
    ("JACK UP RIG", "Jack Up Rig"),
    ("JACK-UP RIG", "Jack Up Rig"),
    ("JACKUP RIG", "Jack Up Rig"),
    ("DRILL SHIP", "Drillship"),
    ("DRILLSHIP", "Drillship"),
    ("SEMI SUBMERSIBLE", "Semi-Submersible Rig"),
    ("SEMI-SUBMERSIBLE", "Semi-Submersible Rig"),
    ("OFFSHORE RIG", "Offshore Rig"),
    ("DRILLING RIG", "Drilling Rig"),
    ("DRILLING VESSEL", "Drilling Vessel"),
    ("RIG", "Rig"),
    ("DREDGER", "Dredger"),
    ("HOPPER DREDGER", "Hopper Dredger"),
    ("CABLE LAYER", "Cable Layer"),
    ("CABLE LAYING", "Cable Layer"),
    ("RESEARCH VESSEL", "Research Vessel"),
    ("SURVEY VESSEL", "Survey Vessel"),
    ("FERRY", "Ferry"),
    ("PASSENGER SHIP", "Passenger Ship"),
    ("CRUISE SHIP", "Cruise Ship"),
    ("YACHT", "Yacht"),
    ("TUG", "Tug"),
    ("TUG BOAT", "Tug"),
    ("BARGE", "Barge"),
    ("LAND RIG", "Land Rig"),
    ("OFFSHORE", "Offshore"),
]

DATE_WORD_MONTHS = {
    "JAN": 1, "JANUARY": 1, "FEB": 2, "FEBRUARY": 2, "MAR": 3, "MARCH": 3,
    "APR": 4, "APRIL": 4, "MAY": 5, "JUN": 6, "JUNE": 6, "JUL": 7, "JULY": 7,
    "AUG": 8, "AUGUST": 8, "SEP": 9, "SEPT": 9, "SEPTEMBER": 9, "OCT": 10,
    "OCTOBER": 10, "NOV": 11, "NOVEMBER": 11, "DEC": 12, "DECEMBER": 12,
}

UNLIMITED_WORDS = re.compile(r"\b(?:UNLIMITED|LIFE\s*TIME|LIFETIME|LIFE\s*LONG|VALID\s*FOR\s*LIFE|PERMANENT|NO\s*EXPIRY|N/?A)\b", re.I)
PRESENT_WORDS = re.compile(r"\b(?:TILL\s*NOW|TILL\s*DATE|PRESENT|CURRENT|ONGOING|CONTINUING|UP\s*TO\s*PRESENT)\b", re.I)


def clean(value):
    value = str(value or "").replace("\xa0", " ").replace("&amp;", "&")
    value = re.sub(r"[\u200b\ufeff]", "", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip(" \t|:")


def lines(text):
    return [clean(x) for x in str(text or "").splitlines() if clean(x)]


def first_match(patterns, text, flags=re.I | re.M):
    for pattern in patterns:
        m = re.search(pattern, text or "", flags)
        if m:
            return clean(m.group(1))
    return ""


def email(text):
    m = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text or "")
    return m.group(0) if m else ""


def phones(text):
    candidates = re.findall(r"(?<!\d)(?:\+?\d[\d ()\-]{7,}\d)(?!\d)", text or "")
    out = []
    for value in candidates:
        digits = re.sub(r"\D", "", value)
        if digits.startswith("91") and len(digits) == 12:
            normalized = "+" + digits
        elif len(digits) == 10 and digits[0] in "6789":
            normalized = digits
        else:
            continue
        if normalized not in out:
            out.append(normalized)
    return out


def normalize_date_text(value):
    value = clean(value)
    value = re.sub(r"(?<=\d)\s+(?=\d)", "", value)
    value = re.sub(r"\s*([./-])\s*", r"\1", value)
    return value


def date_candidates(text):
    text = str(text or "")
    patterns = [
        r"(?<!\d)(?:\d\s*){1,2}\s*[./-]\s*(?:\d\s*){1,2}\s*[./-]\s*(?:\d\s*){2,4}(?!\d)",
        r"\b(?:\d{1,2}\s+)?(?:JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUN(?:E)?|JUL(?:Y)?|AUG(?:UST)?|SEP(?:TEMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?)\s+\d{2,4}\b",
        r"\b(?:JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUN(?:E)?|JUL(?:Y)?|AUG(?:UST)?|SEP(?:TEMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?)\s+\d{2,4}\b",
    ]
    result = []
    for pattern in patterns:
        for value in re.findall(pattern, text, re.I):
            value = normalize_date_text(value)
            if value not in result:
                result.append(value)
    return result


def parse_date(value):
    value = normalize_date_text(value)
    if not value:
        return None
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d/%m/%y", "%d-%m-%y", "%d.%m.%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    m = re.match(r"^(\d{1,2})\s+([A-Za-z]+)\s+(\d{2,4})$", value)
    if m:
        month = DATE_WORD_MONTHS.get(m.group(2).upper())
        if month:
            year = int(m.group(3))
            if year < 100:
                year += 2000 if year < 50 else 1900
            try:
                return datetime(year, month, int(m.group(1)))
            except ValueError:
                return None
    m = re.match(r"^([A-Za-z]+)\s+(\d{2,4})$", value)
    if m:
        month = DATE_WORD_MONTHS.get(m.group(1).upper())
        if month:
            year = int(m.group(2))
            if year < 100:
                year += 2000 if year < 50 else 1900
            try:
                return datetime(year, month, 1)
            except ValueError:
                return None
    return None


def iso_date(value):
    d = parse_date(value)
    return d.strftime("%Y-%m-%d") if d else ""


def is_unlimited(value):
    return bool(UNLIMITED_WORDS.search(str(value or "")))


def is_present(value):
    return bool(PRESENT_WORDS.search(str(value or "")))


def extract_name(text):
    value = first_match([
        r"(?m)^\s*(?:FULL\s+)?NAME\s*[:\-]\s*([^\n]+)",
        r"(?m)^\s*CANDIDATE\s+NAME\s*[:\-]\s*([^\n]+)",
    ], text)
    if value:
        return value.title()
    first = lines(text)[:30]
    if first:
        m = re.match(r"^([A-Za-z][A-Za-z .'-]{2,})\s*(?:\||-)\s*(?:CURRICULUM\s+VITAE|RESUME|CV)\b", first[0], re.I)
        if m:
            return m.group(1).strip().title()
        m = re.match(r"^([A-Za-z][A-Za-z .'-]{2,})\s+(?:CURRICULUM\s+VITAE|RESUME|CV)\b", first[0], re.I)
        if m:
            return m.group(1).strip().title()
    for i, value in enumerate(first):
        if re.search(r"\b(?:NAME|EMAIL|PHONE|MOBILE|RANK|POST|ADDRESS|NATIONALITY|OBJECTIVE|CURRICULUM|RESUME|CV)\b", value, re.I):
            continue
        if re.match(r"^[A-Za-z][A-Za-z .'-]{2,}$", value) and 1 <= len(value.split()) <= 5:
            if not detect_rank(value) and value.upper() not in {"RESUME", "CURRICULUM", "VITAE", "CV"}:
                return value.title()
        if i + 1 < len(first) and re.search(r"[-–—]", value):
            candidate = first[i + 1]
            if re.fullmatch(r"[A-Za-z][A-Za-z .'-]{2,}", candidate) and 2 <= len(candidate.split()) <= 5:
                return candidate.title()
    return ""


def detect_rank(value):
    upper = clean(value).upper()
    for source, output in sorted(RANK_ALIASES, key=lambda x: len(x[0]), reverse=True):
        if re.search(r"(?<![A-Z0-9])" + re.escape(source) + r"(?![A-Z0-9])", upper):
            return output
    # Common compact variants
    if re.search(r"\bCHIEF\s+COOK\b", upper): return "Chief Cook"
    if re.search(r"\bCOOK\b", upper): return "Cook"
    if re.search(r"\bELECTR(?:O|ICAL)\s+TECHNICAL\b", upper): return "ETO"
    return ""


def extract_rank(text):
    value = first_match([
        r"(?:APPLYING\s+FOR\s+THE\s+ROLE\s+OF|POST\s+APPLIED\s+FOR|RANK|POSITION|DESIGNATION)\s*[:\-]\s*([^\n]+)",
    ], text)
    if value:
        value = re.sub(r"\(.*?\b(?:YEAR|YEARS|EXP|EXPERIENCE).*?\)", "", value, flags=re.I)
        return detect_rank(value) or clean(value)
    return detect_rank(text)


def extract_indos(text):
    return first_match([
        r"\bIN[Dd][Oo][Ss]\s*(?:NO|NUMBER)?\s*[:\-]?\s*([A-Z0-9]{5,})",
        r"\bINDOS\s+NO\s*([A-Z0-9]{5,})",
    ], text)


def extract_passport(text):
    return first_match([r"\b(?:INDIAN\s+)?PASSPORT\s*(?:NO|NUMBER)?\s*[:\-]?\s*([A-Z][A-Z0-9]{5,})"], text)


def extract_cdc(text):
    return first_match([r"\b(?:INDIAN\s+)?CDC\s*(?:NO|NUMBER)?\s*[:\-]?\s*([A-Z0-9]{5,})"], text)


def extract_coc(text):
    return first_match([r"\b(?:COC|CERTIFICATE\s+OF\s+COMPETENCY)\s*(?:NO|NUMBER)?\s*[:\-]?\s*([A-Z0-9/\-]{5,})"], text)


def extract_sid(text):
    return first_match([r"\bSID\s*(?:NO|NUMBER)?\s*[:\-]?\s*([A-Z0-9/\-]{5,})", r"\bSEAFARER'?S\s+IDENTITY\s+(?:DOCUMENT|CARD)\s*[:\-]?\s*([A-Z0-9/\-]{5,})"], text)


def extract_languages(text):
    return first_match([r"LANGU(?:AGES?|ASE)\s*(?:KNOWN)?\s*[:\-]\s*([^\n]+)"], text)


def extract_address(text):
    return first_match([
        r"\b(?:PRESENT\s+)?ADDRESS\s*[:\-]\s*(.+?)(?=\n(?:CAREER|OBJECTIVE|EDUCATIONAL|ACADEMIC|KEY\s+SKILLS|EMPLOYMENT|PROFESSIONAL|DOCUMENT|COURSE|SEA\s+SERVICE|PERSONAL|DECLARATION)\b)",
    ], text, re.I | re.S)


def extract_location_from_address(address):
    state_aliases = {
        "andhra pradesh":"Andhra Pradesh", "arunachal pradesh":"Arunachal Pradesh", "assam":"Assam",
        "bihar":"Bihar", "chhattisgarh":"Chhattisgarh", "goa":"Goa", "gujarat":"Gujarat",
        "haryana":"Haryana", "himachal pradesh":"Himachal Pradesh", "jharkhand":"Jharkhand",
        "karnataka":"Karnataka", "kerala":"Kerala", "madhya pradesh":"Madhya Pradesh",
        "maharashtra":"Maharashtra", "manipur":"Manipur", "meghalaya":"Meghalaya", "mizoram":"Mizoram",
        "nagaland":"Nagaland", "odisha":"Odisha", "orissa":"Odisha", "punjab":"Punjab",
        "rajasthan":"Rajasthan", "sikkim":"Sikkim", "tamil nadu":"Tamil Nadu", "tamilnadu":"Tamil Nadu",
        "telangana":"Telangana", "tripura":"Tripura", "uttar pradesh":"Uttar Pradesh",
        "uttarakhand":"Uttarakhand", "west bengal":"West Bengal", "delhi":"Delhi",
        "new delhi":"Delhi", "chandigarh":"Chandigarh", "ladakh":"Ladakh", "puducherry":"Puducherry",
        "pondicherry":"Puducherry", "jammu and kashmir":"Jammu and Kashmir",
    }
    state = ""
    lower = address.lower()
    for key, output in sorted(state_aliases.items(), key=lambda x: len(x[0]), reverse=True):
        if re.search(r"(?<![a-z])" + re.escape(key) + r"(?![a-z])", lower):
            state = output
            break
    city = ""
    m = re.search(r"(?:,|\b)\s*([A-Za-z .'-]+?)\s+(?:Dist(?:rict)?\.?|Dt\.?|Tal(?:uka)?\.?|TK)\b", address, re.I)
    if m:
        city = clean(m.group(1))
    elif state:
        chunks = [clean(x) for x in re.split(r",|\n", address) if clean(x)]
        candidates = [x for x in chunks if x.lower() != state.lower() and not re.search(r"\b\d{5,6}\b", x)]
        if candidates:
            city = candidates[-1].split("-")[0].strip()
    return city, state


def extract_nationality(text):
    return first_match([r"NATIONALITY\s*[:\-]\s*([^\n]+)"], text)


def extract_gender(text):
    return first_match([r"(?:GENDER|SEX)\s*[:\-]\s*([^\n]+)"], text)


def extract_religion(text):
    return first_match([r"RELIGION\s*[:\-]\s*([^\n]+)"], text)


def extract_marital(text):
    return first_match([r"(?:MARITAL\s*STATUS|MARITALSTATUS|CIVIL\s*STATUS)\s*[:\-]\s*([^\n]+)"], text)


def is_candidate_indian(text, nationality, cdc_country="", address=""):
    # Explicit nationality is the strongest signal. Do not override an explicit
    # non-Indian nationality just because the candidate has a current Indian address.
    if nationality:
        return "yes" if re.search(r"\bindian\b", nationality, re.I) else "no"
    if cdc_country and re.search(r"\bindia\b", cdc_country, re.I):
        return "yes"
    evidence = " ".join([address, text[:3000]]).upper()
    if re.search(r"\bINDIAN\s+CDC\b", evidence) or re.search(r"\bINDIA\b", evidence):
        return "yes"
    if any(p.startswith("+91") or (len(p) == 10 and p[0] in "6789") for p in phones(text)):
        return "yes"
    return "no"


def detect_vessel_type(value):
    upper = re.sub(r"\s+", " ", clean(value)).upper()
    for source, output in sorted(VESSEL_ALIASES, key=lambda x: len(x[0]), reverse=True):
        if source in upper:
            return output
    # Generic keyword fallback for combinations not in the dictionary.
    if "VESSEL" in upper:
        return clean(re.sub(r"\bDP\s*\d+\b", "", value, flags=re.I))
    if "BARGE" in upper:
        return "Barge"
    if "RIG" in upper:
        return "Rig"
    return ""


def detect_grt(value):
    m = re.search(r"\b(?:GRT|GT|GROSS\s+TONNAGE)\s*[:\-]?\s*([\d,.]+)", value or "", re.I)
    return m.group(1).replace(",", "") if m else ""


def parse_table_row(line):
    if "|" not in line:
        return None
    parts = [clean(x) for x in line.split("|")]
    return parts if len(parts) >= 3 else None


def header_indexes(parts):
    mapping = {}
    for i, cell in enumerate(parts):
        h = re.sub(r"[^A-Z0-9 ]", " ", cell.upper())
        if re.search(r"ORGANIZATION|COMPANY|EMPLOYER|OWNER|SHIPPING", h): mapping.setdefault("company", i)
        elif re.search(r"VESSEL\s*TYPE|TYPE\s+OF\s+VESSEL", h): mapping.setdefault("vessel_type", i)
        elif re.search(r"VESSEL\s*(?:NAME|UNIT)?$|VESSEL\s+(?:NAME|UNIT)|NAME\s+OF\s+THE\s+UNIT|SHIP\s*NAME", h): mapping.setdefault("vessel", i)
        elif re.search(r"POSITION|RANK|DESIGNATION|CAPACITY", h): mapping.setdefault("rank", i)
        elif re.search(r"^(?:TYPE|VESSEL TYPE)$|TYPE\s+OF\s+VESSEL", h): mapping.setdefault("vessel_type", i)
        elif re.search(r"GRT|GT|GROSS", h): mapping.setdefault("grt", i)
        elif re.search(r"SIGN\s*ON|FROM|JOINING|DATE\s+FROM|START", h): mapping.setdefault("from", i)
        elif re.search(r"SIGN\s*OFF|TO|RELIEVING|DATE\s+TO|END", h): mapping.setdefault("to", i)
    return mapping


def build_sea_record(parts, mapping=None, default_indos=""):
    mapping = mapping or {}
    joined = " | ".join(parts)
    dates = date_candidates(joined)
    if not dates:
        return None
    start = parse_date(dates[0])
    if not start:
        return None
    unlimited = False
    present = False
    end = None
    if len(dates) >= 2:
        end = parse_date(dates[1])
    tail = " ".join(parts[max(0, len(parts)-2):])
    if is_unlimited(tail):
        unlimited = True
    elif is_present(tail):
        present = True
        end = datetime.today()
    if not end and not unlimited:
        # Some rows have only one date and a separate Present cell.
        if any(is_present(p) for p in parts):
            present = True
            end = datetime.today()
        else:
            return None
    if end and end < start:
        return None

    def cell(key):
        idx = mapping.get(key)
        return clean(parts[idx]) if idx is not None and idx < len(parts) else ""

    company = cell("company")
    vessel = cell("vessel")
    vessel_type = cell("vessel_type")
    rank = cell("rank")
    grt = cell("grt")

    if not mapping:
        company = parts[0] if len(parts) >= 5 else ""
        vessel = parts[1] if len(parts) >= 5 else ""
        vessel_type = parts[2] if len(parts) >= 5 else ""
        rank = parts[3] if len(parts) >= 5 else ""
        grt = detect_grt(joined)
    if not grt:
        grt = detect_grt(joined)

    normalized_type = detect_vessel_type(vessel_type) or detect_vessel_type(vessel) or clean(vessel_type)
    normalized_rank = detect_rank(rank) or detect_rank(joined)

    return {
        "indos": default_indos,
        "rank": normalized_rank or clean(rank),
        "company_name": company,
        "vessel_name": vessel,
        "vessel_type": normalized_type,
        "grt": grt,
        "from_date": start.strftime("%Y-%m-%d"),
        "to_date": end.strftime("%Y-%m-%d") if end else "",
        "is_unlimited": "yes" if unlimited else "no",
    }


def sea_records_from_tables(text, indos=""):
    records = []
    current_header = None
    table_mode = False
    for line in lines(text):
        parts = parse_table_row(line)
        if not parts:
            continue
        joined_upper = " ".join(parts).upper()
        if "DOCUMENT TYPE" in joined_upper or ("DOCUMENTS" in joined_upper and "DATE OF ISSUE" in joined_upper):
            current_header = None
            table_mode = False
            continue
        if "COURSE NAME" in joined_upper or ("COURSE" in joined_upper and "CERTIFICATE" in joined_upper):
            current_header = None
            table_mode = False
            continue
        if any(k in joined_upper for k in ["ORGANIZATION NAME", "NAME OF THE UNIT", "VESSEL TYPE", "POSITION HELD", "SIGN ON / OFF", "SIGN ON", "SIGN OFF"]):
            idx = header_indexes(parts)
            # Require employment-specific columns. This prevents document/course tables
            # from being interpreted as sea-service records.
            if any(k in idx for k in ("company", "vessel", "vessel_type", "rank")) and ("from" in idx or "to" in idx):
                current_header = idx
                table_mode = True
            else:
                current_header = None
                table_mode = False
            continue
        if not table_mode and current_header is None:
            continue
        rec = build_sea_record(parts, current_header, indos)
        if rec:
            # Do not accept rows whose mapped fields are clearly document/course rows.
            if rec["rank"] and rec["rank"].upper() in {"PASSPORT", "CDC", "INDOS", "COC", "COURSE"}:
                continue
            if rec["company_name"] or rec["vessel_name"] or rec["vessel_type"] or rec["rank"]:
                if rec["rank"] or rec["vessel_type"] or len(parts) >= 5:
                    records.append(rec)
    unique = []
    seen = set()
    for r in records:
        key = tuple(r.get(k, "") for k in ("company_name", "vessel_name", "from_date", "to_date"))
        if key not in seen:
            seen.add(key); unique.append(r)
    return unique


def extract_context_records(text, indos=""):
    ls = lines(text)
    records = []
    inside = False
    for i, line in enumerate(ls):
        u = line.upper()
        if any(k in u for k in ["SEA SERVICE", "SEA EXPERIENCE", "EMPLOYMENT RECORD", "EMPLOYMENT HISTORY", "VESSEL EXPERIENCE", "SEA GOING EXPERIENCE", "PROFESSIONAL EXPERIENCE"]):
            inside = True
            continue
        if inside and any(k in u for k in ["DECLARATION", "YOURS FAITHFULLY", "TRAVELLING DOCUMENT", "PERSONAL PARTICULARS", "COURSE DETAILS"]):
            break
        if not inside:
            continue
        window = " | ".join(ls[max(0, i-4):min(len(ls), i+5)])
        dates = date_candidates(window)
        if not dates:
            continue
        start = parse_date(dates[0])
        if not start:
            continue
        end = parse_date(dates[1]) if len(dates) > 1 else None
        unlimited = is_unlimited(window)
        if is_present(window):
            end = datetime.today()
        if not end and not unlimited:
            continue
        rank = detect_rank(window)
        vessel_type = detect_vessel_type(window)
        if not rank and not vessel_type:
            continue
        records.append({
            "indos": indos,
            "rank": rank,
            "company_name": "",
            "vessel_name": "",
            "vessel_type": vessel_type,
            "grt": detect_grt(window),
            "from_date": start.strftime("%Y-%m-%d"),
            "to_date": end.strftime("%Y-%m-%d") if end else "",
            "is_unlimited": "yes" if unlimited else "no",
        })
    return records


def sea_records(text, indos=""):
    records = sea_records_from_tables(text, indos)
    if records:
        return records
    return extract_context_records(text, indos)


def total_months(records):
    periods = []
    for r in records:
        start = parse_date(r.get("from_date"))
        end = parse_date(r.get("to_date"))
        if start and end and end >= start:
            periods.append((start, end))
    if not periods:
        return 0.0
    periods.sort(key=lambda x: x[0])
    merged = [list(periods[0])]
    for start, end in periods[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    days = sum((end - start).days + 1 for start, end in merged)
    return round(days / 30.4375, 2)


def unique_types(records):
    result = []
    seen = set()
    for r in records:
        value = clean(r.get("vessel_type"))
        if value and value.upper() not in seen:
            seen.add(value.upper()); result.append(value)
    return ", ".join(result)


def document_table(text):
    result = {k: "" for k in [
        "indos", "passport_no", "passport_from_date", "passport_to_date",
        "cdc_no", "cdc_from_date", "cdc_to_date", "cdc_country",
        "coc_no", "coc_from_date", "coc_to_date", "coc_country", "sid_no"
    ]}
    for line in lines(text):
        parts = parse_table_row(line)
        if not parts or len(parts) < 2:
            continue
        doc = parts[0].upper()
        dates = date_candidates(" ".join(parts))
        if "INDOS" in doc:
            result["indos"] = parts[1]
        elif "PASSPORT" in doc:
            result["passport_no"] = parts[1]
            if len(dates) >= 2:
                result["passport_from_date"], result["passport_to_date"] = iso_date(dates[0]), iso_date(dates[1])
        elif "CDC" in doc:
            result["cdc_no"] = parts[1]
            result["cdc_country"] = "India" if "INDIAN" in doc else ""
            if len(dates) >= 2:
                result["cdc_from_date"], result["cdc_to_date"] = iso_date(dates[0]), iso_date(dates[1])
        elif "SID" in doc or "SEAFARER ID" in doc:
            result["sid_no"] = parts[1]
        elif "COC" in doc or "CERTIFICATE OF COMPETENCY" in doc:
            result["coc_no"] = parts[1]
            if len(dates) >= 2:
                result["coc_from_date"], result["coc_to_date"] = iso_date(dates[0]), iso_date(dates[1])
            if is_unlimited(" ".join(parts)):
                result["coc_to_date"] = ""
                result["coc_unlimited"] = "yes"
            if len(parts) >= 5:
                result["coc_country"] = parts[4]
    return result


def document_fallback(text):
    docs = document_table(text)
    ls = lines(text)
    def nearby(label):
        for i, line in enumerate(ls):
            if label in line.upper():
                chunk = " ".join(ls[i:i+4])
                dates = date_candidates(chunk)
                return dates
        return []
    for label, no_key, f_key, t_key in [
        ("PASSPORT", "passport_no", "passport_from_date", "passport_to_date"),
        ("CDC", "cdc_no", "cdc_from_date", "cdc_to_date"),
        ("COC", "coc_no", "coc_from_date", "coc_to_date"),
    ]:
        dates = nearby(label)
        if not docs[f_key] and dates: docs[f_key] = iso_date(dates[0])
        if not docs[t_key] and len(dates) > 1: docs[t_key] = iso_date(dates[1])
    docs["indos"] = docs.get("indos") or extract_indos(text)
    docs["passport_no"] = docs.get("passport_no") or extract_passport(text)
    docs["cdc_no"] = docs.get("cdc_no") or extract_cdc(text)
    docs["coc_no"] = docs.get("coc_no") or extract_coc(text)
    docs["sid_no"] = docs.get("sid_no") or extract_sid(text)
    if not docs.get("cdc_country") and re.search(r"\bINDIAN\s+CDC\b", text, re.I): docs["cdc_country"] = "India"
    return docs


def course_details(text):
    courses = []
    in_course = False
    for line in lines(text):
        parts = parse_table_row(line)
        if parts:
            header = " ".join(parts).upper()
            if "COURSE NAME" in header or ("COURSE" in header and "CERTIFICATE" in header):
                in_course = True; continue
            if any(k in header for k in ["DOCUMENT TYPE", "ORGANIZATION NAME", "SIGN ON / OFF"]):
                in_course = False
            if in_course and len(parts) >= 3:
                dates = date_candidates(" ".join(parts))
                if dates:
                    course_name = clean(parts[0])
                    cert = clean(parts[1]) if len(parts) > 1 else ""
                    courses.append({
                        "course_name": course_name,
                        "company_name": "",
                        "certificate_no": cert,
                        "from_date": iso_date(dates[0]),
                        "to_date": iso_date(dates[1]) if len(dates) > 1 and not is_unlimited(" ".join(parts)) else "",
                        "is_unlimited": "yes" if is_unlimited(" ".join(parts)) else "no",
                    })
    if courses:
        return dedupe_courses(courses)
    # Text fallback: one line per course with certificate/date(s).
    for line in lines(text):
        if not re.search(r"\b(?:COURSE|STCW|BST|PSSR|PSCRB|FPFF|EFA|PST|STSDSD|OPITO|BOSIET|H2S|COC)\b", line, re.I):
            continue
        dates = date_candidates(line)
        if not dates: continue
        cert = re.search(r"\b[A-Z0-9][A-Z0-9/._\-]{7,}\b", line, re.I)
        course = line
        if cert: course = course.replace(cert.group(0), " ")
        for d in dates: course = course.replace(d, " ")
        course = re.sub(r"\b(?:DATE\s+OF\s+ISSUE|DATE\s+OF\s+EXPIRY|PLACE\s+OF\s+ISSUE)\b", " ", course, flags=re.I)
        course = clean(course)
        if course:
            courses.append({
                "course_name": course,
                "company_name": "",
                "certificate_no": cert.group(0) if cert else "",
                "from_date": iso_date(dates[0]),
                "to_date": iso_date(dates[1]) if len(dates) > 1 and not is_unlimited(line) else "",
                "is_unlimited": "yes" if is_unlimited(line) else "no",
            })
    return dedupe_courses(courses)


def dedupe_courses(courses):
    out = []; seen = set()
    for c in courses:
        key = (c.get("course_name", "").upper(), c.get("certificate_no", "").upper(), c.get("from_date", ""))
        if key not in seen:
            seen.add(key); out.append(c)
    return out


def global_unlimited(text, documents, courses, records):
    if documents.get("coc_unlimited") == "yes": return "yes"
    if is_unlimited(text):
        # Avoid treating every occurrence of "N/A" as unlimited. Explicit lifetime words are strong evidence.
        if re.search(r"\b(?:UNLIMITED|LIFE\s*TIME|LIFETIME|VALID\s+FOR\s+LIFE|NO\s+EXPIRY)\b", text, re.I):
            return "yes"
    if any(c.get("is_unlimited") == "yes" for c in courses): return "yes"
    if any(r.get("is_unlimited") == "yes" for r in records): return "yes"
    return "no"


def parse_resume(text, filename):
    text = str(text or "")
    phones_found = phones(text)
    address = extract_address(text)
    city, state = extract_location_from_address(address)
    nationality = extract_nationality(text)
    documents = document_fallback(text)
    indos = documents.get("indos", "")
    records = sea_records(text, indos)
    for r in records: r["indos"] = indos
    courses = course_details(text)
    unlimited = global_unlimited(text, documents, courses, records)

    return {
        "personal_details": {
            "name": extract_name(text),
            "indos": indos,
            "email": email(text),
            "rank": extract_rank(text),
            "mobile_no": phones_found[0] if phones_found else "",
            "alternate_mobile_no": phones_found[1] if len(phones_found) > 1 else "",
            "city": city,
            "state": state,
            "address": address,
            "nationality": nationality,
            "gender": extract_gender(text),
            "religion": extract_religion(text),
            "married_status": extract_marital(text),
            "passport_no": documents.get("passport_no", ""),
            "passport_from_date": documents.get("passport_from_date", ""),
            "passport_to_date": documents.get("passport_to_date", ""),
            "sid_no": documents.get("sid_no", ""),
            "coc_no": documents.get("coc_no", ""),
            "coc_country": documents.get("coc_country", ""),
            "coc_from_date": documents.get("coc_from_date", ""),
            "coc_to_date": documents.get("coc_to_date", ""),
            "cdc_country": documents.get("cdc_country", ""),
            "cdc_no": documents.get("cdc_no", ""),
            "cdc_from_date": documents.get("cdc_from_date", ""),
            "cdc_to_date": documents.get("cdc_to_date", ""),
            "language_knows": extract_languages(text),
        },
        "is_candidate_indian": is_candidate_indian(text, nationality, documents.get("cdc_country", ""), address),
        "is_unlimited": unlimited,
        "sea_experience": {
            "indos": indos,
            "total_experience_month": total_months(records),
            "vessel_types": unique_types(records),
            "is_unlimited": "yes" if any(r.get("is_unlimited") == "yes" for r in records) else "no",
            "records": records,
        },
        "course_details": courses,
        "uploaded_file_name": filename,
    }
