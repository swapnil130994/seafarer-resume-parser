import re
from datetime import datetime

# Common seafarer / crew ranks. Output is normalized to a clean database value.
RANK_ALIASES = [
    ("CHIEF ELECTRICAL OFFICER", "Chief Electrical Officer"),
    ("ELECTRICAL OFFICER", "Electrical Officer"),
    ("OFFSHORE ELECTRICIAN", "Electrician"),
    ("RIG ELECTRICIAN", "Electrician"),
    ("MARINE ELECTRICIAN", "Electrician"),
    ("ELECTRICIAN", "Electrician"),
    ("CHIEF ENGINEER", "Chief Engineer"),
    ("SECOND ENGINEER", "Second Engineer"),
    ("THIRD ENGINEER", "Third Engineer"),
    ("FOURTH ENGINEER", "Fourth Engineer"),
    ("CHIEF OFFICER", "Chief Officer"),
    ("SECOND OFFICER", "Second Officer"),
    ("THIRD OFFICER", "Third Officer"),
    ("FOURTH OFFICER", "Fourth Officer"),
    ("DECK CADET", "Deck Cadet"),
    ("ENGINE CADET", "Engine Cadet"),
    ("CAPTAIN", "Captain"),
    ("MASTER", "Master"),
    ("ETO", "ETO"),
    ("ETR", "ETR"),
    ("BOSUN", "Bosun"),
    ("ABLE SEAMAN", "AB"),
    ("AB", "AB"),
    ("O/S", "OS"),
    ("OS", "OS"),
    ("COOK", "Cook"),
    ("FITTER", "Fitter"),
    ("OILER", "Oiler"),
    ("WIPER", "Wiper"),
    ("RATING", "Rating"),
    ("TRAINEE", "Trainee"),
]

VESSEL_ALIASES = [
    ("DP3 HEAVY LIFT PIPELAY VESSEL", "Heavy Lift Pipelay Vessel"),
    ("HEAVY LIFT PIPELAY VESSEL", "Heavy Lift Pipelay Vessel"),
    ("DP3 ACCOMMODATION VESSEL", "Accommodation Vessel"),
    ("ACCOMMODATION VESSEL", "Accommodation Vessel"),
    ("ACCOMMODATION BARGE", "Accommodation Barge"),
    ("JACK UP RIG", "Jack Up Rig"),
    ("OFFSHORE RIG", "Offshore Rig"),
    ("DRILLING RIG", "Drilling Rig"),
    ("PIPELAY VESSEL", "Pipelay Vessel"),
    ("HEAVY LIFT", "Heavy Lift"),
    ("AHTS VESSEL", "AHTS"),
    ("AHTS", "AHTS"),
    ("OFFSHORE SUPPLY VESSEL", "OSV"),
    ("OSV", "OSV"),
    ("CONTAINER", "Container"),
    ("BULK CARRIER", "Bulk Carrier"),
    ("BULKER", "Bulker"),
    ("CHEMICAL TANKER", "Chemical Tanker"),
    ("OIL TANKER", "Oil Tanker"),
    ("TANKER", "Tanker"),
    ("LNG", "LNG"),
    ("LPG", "LPG"),
    ("MBC", "MBC"),
    ("NCB", "NCB"),
    ("NCV", "NCV"),
    ("DREDGER", "Dredger"),
    ("RO-RO", "Ro-Ro"),
    ("CAR CARRIER", "Car Carrier"),
    ("GENERAL CARGO", "General Cargo"),
    ("CRUDE OIL", "Crude Oil"),
    ("PRODUCT TANKER", "Product Tanker"),
    ("OFFSHORE", "Offshore"),
    ("RIG", "Rig"),
]

DATE_PATTERN = r"\b\d{1,2}\s*[/.-]\s*\d{1,2}\s*[/.-]\s*\d{2}\s*\d{0,2}\b"


def clean(value):
    value = str(value or "")
    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip(" \t|:")


def lines(text):
    return [clean(x) for x in text.splitlines() if clean(x)]


def first_match(patterns, text, flags=re.I | re.M):
    for pattern in patterns:
        match = re.search(pattern, text, flags)
        if match:
            return clean(match.group(1))
    return ""


def email(text):
    match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text)
    return match.group(0) if match else ""


def phones(text):
    raw = re.findall(r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)", text)
    out = []
    for value in raw:
        value = re.sub(r"[^\d+]", "", value)
        if value not in out:
            out.append(value)
    return out


def normalize_date_text(value):
    """Repair one extracted date, e.g. `13.07.202 5` or `1 4 . 07 . 2026`."""
    value = clean(value)
    value = re.sub(r"\s+", "", value)
    return value


def date_candidates(text):
    """Find dates even when Word/PDF inserted spaces inside date digits."""
    pattern = r"(?<!\d)(?:\d\s*){1,2}[/.-](?:\s*\d){1,2}\s*[/.-](?:\s*\d){2,4}(?!\d)"
    return [normalize_date_text(x) for x in re.findall(pattern, text)]

def parse_date(value):
    if not value:
        return None
    value = normalize_date_text(value)
    value = re.sub(r"\s+", "", value)
    for fmt in (
        "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
        "%d/%m/%y", "%d-%m-%y", "%d.%m.%y",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    return None


def iso_date(value):
    parsed = parse_date(value)
    return parsed.strftime("%Y-%m-%d") if parsed else ""


def extract_name(text):
    # Only accept an explicit Name: label, not phrases such as College Name.
    value = first_match([
        r"(?m)^\s*NAME\s*[:\-]\s*([^\n]+)",
        r"(?m)^\s*FULL\s+NAME\s*[:\-]\s*([^\n]+)",
    ], text)
    if value:
        return value

    first_lines = lines(text)[:25]

    # Some DOCX readers flatten visual line breaks into one paragraph.
    # Recover the name before common qualification/contact text.
    if first_lines:
        first = first_lines[0]
        match = re.match(
            r"^([A-Za-z][A-Za-z .'-]{2,}?)(?:\s+Electrical\s+and\s+Electronics\s+Engineering|\s+Applying\s+for\s+the\s+Role\s+Of|\s+Email\s*:|\s+Phone\s*:)",
            first,
            re.I,
        )
        if match:
            candidate = clean(match.group(1))
            if len(candidate.split()) >= 2:
                return candidate.title()

    # CVs sometimes use ROLE-NAME on the first line and the clean name on the next.
    for index, value in enumerate(first_lines):
        if re.search(r"^[A-Za-z][A-Za-z /&.]+[-–—]", value):
            if index + 1 < len(first_lines):
                candidate = first_lines[index + 1]
                if (
                    re.fullmatch(r"[A-Za-z][A-Za-z .'-]{2,}", candidate)
                    and 2 <= len(candidate.split()) <= 5
                    and not any(k in candidate.upper() for k in [
                        "ENGINEERING", "COLLEGE", "ROLE", "EXPERIENCE", "ADDRESS"
                    ])
                ):
                    return candidate.title()

    # Prefer a standalone all-caps two-to-five-word line.
    for value in first_lines:
        upper = value.upper()
        if (
            2 <= len(value.split()) <= 5
            and re.fullmatch(r"[A-Z][A-Z .'-]{2,}", value)
            and not any(k in upper for k in [
                "RESUME", "CURRICULUM", "VITAE", "ELECTRICIAN", "ENGINEERING",
                "APPLYING", "EDUCATIONAL", "ATTAINMENT", "COLLEGE", "PHONE", "EMAIL"
            ])
        ):
            return value.title()

    return ""

def detect_rank(value):
    upper = clean(value).upper()
    for source, output in sorted(RANK_ALIASES, key=lambda x: len(x[0]), reverse=True):
        if re.search(r"\b" + re.escape(source) + r"\b", upper):
            return output
    return ""


def extract_rank(text):
    value = first_match([
        r"APPLYING\s+FOR\s+THE\s+ROLE\s+OF\s*[:\-]\s*([^\n]+)",
        r"POST\s+APPLIED\s+FOR\s*[:\-]\s*([^\n]+)",
        r"\bRANK\s*[:\-]\s*([^\n]+)",
        r"\bPOSITION\s*[:\-]\s*([^\n]+)",
    ], text)
    if value:
        value = re.sub(r"\s*\(\s*\d+\s*Years?\s+of\s+Experience\s*\)", "", value, flags=re.I)
        return detect_rank(value) or clean(value)
    return detect_rank(text)


def extract_indos(text):
    return first_match([
        r"\bINDOS\s*(?:NO|NUMBER)?\s*[:\-]?\s*([A-Z0-9]{5,})",
        r"\bINDoS\s*(?:No)?\s*[:\-]?\s*([A-Z0-9]{5,})",
    ], text)


def extract_passport(text):
    return first_match([
        r"\b(?:INDIAN\s+)?PASSPORT\s*[:\-]?\s*([A-Z][A-Z0-9]{5,})",
    ], text)


def extract_cdc(text):
    return first_match([
        r"\bCDC\s*(?:\([^)]+\))?\s*[:\-]?\s*([A-Z0-9]{5,})",
        r"\bINDIAN\s+CDC\s*[:\-]?\s*([A-Z0-9]{5,})",
    ], text)


def extract_coc(text):
    return first_match([
        r"\bCOC\s*(?:NO|NUMBER)?\s*[:\-]?\s*([A-Z0-9/\-]{5,})",
    ], text)


def extract_sid(text):
    return first_match([
        r"\bSID\s*(?:NO|NUMBER)?\s*[:\-]?\s*([A-Z0-9/\-]{5,})",
        r"\bSEAFARERS?\s+IDENTITY\s+DOC(?:UMENT)?\s*[:\-]?\s*([A-Z0-9/\-]{5,})",
    ], text)


def extract_languages(text):
    return first_match([
        r"LANGUAGES?\s*(?:KNOWN)?\s*[:\-]\s*([^\n]+)",
        r"LANGUASE\s*(?:KNOWN)?\s*[:\-]\s*([^\n]+)",
    ], text)


def extract_address(text):
    value = first_match([
        r"\bADDRESS\s*[:\-]\s*(.+?)(?=\n(?:CAREER|OBJECTIVE|EDUCATIONAL|MAJOR|KEY\s+SKILLS|EMPLOYMENT|PROFESSIONAL|TRAVELLING|PERSONAL|DECLARATION)\b)",
        r"\bPRESENT\s+ADDRESS\s*[:\-]?\s*(.+?)(?=\n(?:PERMANENT|DOCUMENT|COURSE|SEA\s+SERVICE|EMPLOYMENT)\b)",
    ], text, re.I | re.S)
    return clean(value)


def extract_location_from_address(address):
    city = ""
    state = ""
    if not address:
        return city, state

    states = [
        # --- States ---
        # Andhra Pradesh
        "Andhra Pradesh", "AndhraPradesh", "Andhra", "AP",
        
        # Arunachal Pradesh
        "Arunachal Pradesh", "ArunachalPradesh", "Arunachal",
        
        # Assam
        "Assam", "Asom",
        
        # Bihar
        "Bihar",
        
        # Chhattisgarh
        "Chhattisgarh", "Chhatisgarh", "Chattisgarh", "CG",
        
        # Goa
        "Goa",
        
        # Gujarat
        "Gujarat", "Gujrat",
        
        # Haryana
        "Haryana", "Hariyana",
        
        # Himachal Pradesh
        "Himachal Pradesh", "HimachalPradesh", "Himachal", "HP",
        
        # Jharkhand
        "Jharkhand", "Jarkhand",
        
        # Karnataka
        "Karnataka", "Karntaka",
        
        # Kerala
        "Kerala", "Keralam",
        
        # Madhya Pradesh
        "Madhya Pradesh", "MadhyaPradesh", "MP",
        
        # Maharashtra
        "Maharashtra", "Maharasthra", "MH",
        
        # Manipur
        "Manipur",
        
        # Meghalaya
        "Meghalaya", "Meghalay",
        
        # Mizoram
        "Mizoram",
        
        # Nagaland
        "Nagaland",
        
        # Odisha
        "Odisha", "Orissa",
        
        # Punjab
        "Punjab", "Panjab",
        
        # Rajasthan
        "Rajasthan", "Rajsthan",
        
        # Sikkim
        "Sikkim",
        
        # Tamil Nadu
        "Tamil Nadu", "Tamilnadu", "TN",
        
        # Telangana
        "Telangana", "Telengana", "TS",
        
        # Tripura
        "Tripura",
        
        # Uttar Pradesh
        "Uttar Pradesh", "UttarPradesh", "UP",
        
        # Uttarakhand
        "Uttarakhand", "Uttaranchal", "UK",
        
        # West Bengal
        "West Bengal", "WestBengal", "WB", "Paschim Banga", "Bengal",

        # --- Union Territories ---
        # Andaman and Nicobar Islands
        "Andaman and Nicobar Islands", "Andaman & Nicobar", "Andaman and Nicobar", "A&N Islands",
        
        # Chandigarh
        "Chandigarh",
        
        # Dadra and Nagar Haveli and Daman and Diu
        "Dadra and Nagar Haveli and Daman and Diu", "Dadra and Nagar Haveli", "Daman and Diu", "Daman & Diu",
        
        # Delhi
        "Delhi", "NCT of Delhi", "National Capital Territory of Delhi", "New Delhi", "DL",
        
        # Jammu and Kashmir
        "Jammu and Kashmir", "Jammu & Kashmir", "Jammu and Kashmir (UT)", "J&K", "JK",
        
        # Ladakh
        "Ladakh",
        
        # Lakshadweep
        "Lakshadweep", "Laccadives",
        
        # Puducherry
        "Puducherry", "Pondicherry", "PY"
    ]
    for state_name in states:
        if re.search(r"\b" + re.escape(state_name) + r"\b", address, re.I):
            state = state_name
            if state.lower() == "tamilnadu":
                state = "Tamil Nadu"
            break

    match = re.search(r",\s*([A-Za-z .'-]+?)\s+(?:Dist|District)\b", address, re.I)
    if match:
        city = clean(match.group(1))

    return city, state


def extract_nationality(text):
    return first_match([r"NATIONALITY\s*[:\-]\s*([^\n]+)"], text)


def extract_gender(text):
    return first_match([r"GENDER\s*[:\-]\s*([^\n]+)", r"SEX\s*[:\-]\s*([^\n]+)"], text)


def extract_religion(text):
    return first_match([r"RELIGION\s*[:\-]\s*([^\n]+)"], text)


def extract_marital(text):
    return first_match([
        r"MARITAL\s*STATUS\s*[:\-]\s*([^\n]+)",
        r"MARITALSTATUS\s*[:\-]\s*([^\n]+)",
        r"CIVIL\s*STATUS\s*[:\-]\s*([^\n]+)",
    ], text)


def detect_vessel_type(value):
    upper = clean(value).upper()
    for source, output in sorted(VESSEL_ALIASES, key=lambda x: len(x[0]), reverse=True):
        if source in upper:
            return output
    return ""


def detect_grt(value):
    match = re.search(r"\bGRT\s*[:\-]?\s*(\d{2,7}(?:\.\d+)?)", value, re.I)
    return match.group(1) if match else ""


def detect_company(value):
    for part in value.split("|"):
        part = clean(part)
        upper = part.upper()
        if any(k in upper for k in [
            "LTD", "PVT", "PRIVATE", "SHIPPING", "MARINE",
            "MARITIME", "SHIP MANAGEMENT", "DRILLING"
        ]):
            return part
    return ""


def date_pair(value):
    dates = date_candidates(value)
    if len(dates) >= 2:
        first = parse_date(dates[-2])
        second = parse_date(dates[-1])
        if first and second:
            return first, second
    return None, None


def parse_table_row(line):
    """Parse pipe-separated Word table rows. Returns None when it is not a row."""
    if "|" not in line:
        return None
    parts = [clean(x) for x in line.split("|")]
    if len(parts) < 4:
        return None
    return parts


def sea_records_from_tables(text):
    records = []
    for line in lines(text):
        parts = parse_table_row(line)
        if not parts or len(parts) < 5:
            continue

        joined = " ".join(parts).upper()
        if any(k in joined for k in [
            "ORGANIZATION NAME", "NAME OF THE UNIT", "POSITION HELD", "SIGN ON / OFF"
        ]):
            continue

        dates = date_candidates(parts[-1])
        if not dates:
            continue

        start = parse_date(dates[0])
        if not start:
            continue

        if re.search(r"\b(TILL\s+NOW|PRESENT|CURRENT|ONGOING)\b", parts[-1], re.I):
            end = datetime.today()
        elif len(dates) >= 2:
            end = parse_date(dates[1])
        else:
            continue

        if not end or end < start:
            continue

        company = parts[0]
        vessel_name = parts[1]
        vessel_type = detect_vessel_type(parts[2]) or clean(parts[2])
        rank = detect_rank(parts[3]) or clean(parts[3])

        records.append({
            "indos": "",
            "rank": rank,
            "company_name": company,
            "vessel_name": vessel_name,
            "vessel_type": vessel_type,
            "grt": detect_grt(" | ".join(parts)),
            "from_date": start.strftime("%Y-%m-%d"),
            "to_date": end.strftime("%Y-%m-%d"),
        })
    return records


def sea_records_from_text(text):
    ls = lines(text)
    records = []
    inside = False

    for i, line in enumerate(ls):
        upper = line.upper()
        if any(k in upper for k in [
            "SEA SERVICE", "SEA EXPERIENCE", "EMPLOYMENT RECORD", "EMPLOYMENT HISTORY"
        ]):
            inside = True
            continue
        if inside and any(k in upper for k in [
            "DECLARATION", "YOURS FAITHFULLY", "SIGNATURE", "TRAVELLING DOCUMENTS",
            "TRAVELLING DOCUMENT", "PERSONAL PARTICULARS"
        ]):
            break
        if not inside:
            continue

        start, end = date_pair(line)
        if not start:
            continue
        if re.search(r"\b(TILL\s+NOW|PRESENT|CURRENT|ONGOING)\b", line, re.I):
            end = datetime.today()
        if not end:
            continue

        context = " | ".join(ls[max(0, i - 6):i + 1])
        records.append({
            "indos": "",
            "rank": detect_rank(context),
            "company_name": detect_company(context),
            "vessel_name": "",
            "vessel_type": detect_vessel_type(context),
            "grt": detect_grt(context),
            "from_date": start.strftime("%Y-%m-%d"),
            "to_date": end.strftime("%Y-%m-%d"),
        })
    return records


def sea_records(text):
    # Table-first is critical for Word resumes such as the Antony Allan CV.
    records = sea_records_from_tables(text)
    if records:
        return records
    return sea_records_from_text(text)


def total_months(records):
    periods = []
    for record in records:
        start = parse_date(record.get("from_date"))
        end = parse_date(record.get("to_date"))
        if start and end and end >= start:
            periods.append((start, end))

    if not periods:
        return 0.0

    periods.sort()
    merged = [list(periods[0])]
    for start, end in periods[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])

    days = sum((end - start).days + 1 for start, end in merged)
    return round(days / 30.4375, 2)


def unique_types(records):
    output = []
    seen = set()
    for record in records:
        value = clean(record.get("vessel_type"))
        if value and value.upper() not in seen:
            seen.add(value.upper())
            output.append(value)
    return ", ".join(output)


def document_table(text):
    result = {
        "indos": "",
        "passport_no": "",
        "passport_from_date": "",
        "passport_to_date": "",
        "cdc_no": "",
        "cdc_from_date": "",
        "cdc_to_date": "",
        "cdc_country": "",
        "coc_no": "",
        "coc_from_date": "",
        "coc_to_date": "",
        "coc_country": "",
        "sid_no": "",
    }

    for line in lines(text):
        parts = parse_table_row(line)
        if not parts or len(parts) < 3:
            continue

        document = parts[0].upper()
        dates = date_candidates(" ".join(parts))

        if document == "INDOS":
            result["indos"] = parts[1]
            continue

        if "PASSPORT" in document:
            result["passport_no"] = parts[1]
            if len(dates) >= 2:
                result["passport_from_date"] = iso_date(dates[0])
                result["passport_to_date"] = iso_date(dates[1])
            continue

        if "CDC" in document:
            result["cdc_no"] = parts[1]
            result["cdc_country"] = "India" if "INDIAN" in document else ""
            if len(dates) >= 2:
                result["cdc_from_date"] = iso_date(dates[0])
                result["cdc_to_date"] = iso_date(dates[1])
            continue

        if "SID" in document or "SEAFARER ID" in document:
            result["sid_no"] = parts[1]
            continue

        if "COC" in document or "CERTIFICATE OF COMPETENCY" in document:
            result["coc_no"] = parts[1]
            if len(dates) >= 2:
                result["coc_from_date"] = iso_date(dates[0])
                result["coc_to_date"] = iso_date(dates[1])
            if len(parts) >= 5:
                result["coc_country"] = parts[4]

    return result


def document_dates(text, label):
    """Fallback for non-table document layouts."""
    for i, line in enumerate(lines(text)):
        if label.upper() in line.upper():
            dates = date_candidates(" ".join(lines(text)[i:i + 4]))
            return (
                iso_date(dates[0]) if dates else "",
                iso_date(dates[1]) if len(dates) > 1 else "",
            )
    return "", ""


def extract_document_fallback(text):
    docs = document_table(text)
    pf, pt = document_dates(text, "PASSPORT")
    cf, ct = document_dates(text, "CDC")
    cof, cot = document_dates(text, "COC")

    return {
        "indos": docs["indos"] or extract_indos(text),
        "passport_no": docs["passport_no"] or extract_passport(text),
        "passport_from_date": docs["passport_from_date"] or pf,
        "passport_to_date": docs["passport_to_date"] or pt,
        "cdc_no": docs["cdc_no"] or extract_cdc(text),
        "cdc_from_date": docs["cdc_from_date"] or cf,
        "cdc_to_date": docs["cdc_to_date"] or ct,
        "cdc_country": docs["cdc_country"],
        "coc_no": docs["coc_no"] or extract_coc(text),
        "coc_from_date": docs["coc_from_date"] or cof,
        "coc_to_date": docs["coc_to_date"] or cot,
        "coc_country": docs["coc_country"],
        "sid_no": docs["sid_no"] or extract_sid(text),
    }


def course_details_from_tables(text):
    courses = []
    in_course_table = False

    for line in lines(text):
        parts = parse_table_row(line)
        if not parts:
            continue

        header = " ".join(parts).upper()
        if "COURSE NAME" in header and "CERTIFICATE" in header:
            in_course_table = True
            continue

        # A new document/employment table means the course table is over.
        if any(k in header for k in [
            "DOCUMENT TYPE", "ORGANIZATION NAME", "NAME OF THE UNIT", "SIGN ON / OFF"
        ]):
            in_course_table = False
            continue

        if not in_course_table or len(parts) < 4:
            continue

        dates = date_candidates(" ".join(parts))
        if not dates:
            continue

        course_name = clean(parts[0])
        certificate_no = clean(parts[1]) if len(parts) > 1 else ""
        # The fifth column in this CV is Place of Issue, not company name.
        # Keep company_name blank unless a future table explicitly supplies a company field.
        company_name = ""

        courses.append({
            "course_name": course_name,
            "company_name": company_name,
            "certificate_no": certificate_no,
            "from_date": iso_date(dates[0]),
            "to_date": iso_date(dates[1]) if len(dates) > 1 else "",
        })

    return courses

def course_details_fallback(text):
    ls = lines(text)
    out = []
    inside = False

    for line in ls:
        upper = line.upper()
        if any(k in upper for k in ["COURSE DETAILS", "STCW COURSE DETAILS", "STCW & MODULAR COURSES"]):
            inside = True
            continue
        if inside and any(k in upper for k in ["SEA SERVICE", "STATUTORY DOCUMENT", "DECLARATION", "PERSONAL PARTICULARS"]):
            break
        if not inside:
            continue

        dates = date_candidates(line)
        certificate = re.search(r"\b[A-Z0-9][A-Z0-9/\-.]{7,}\b", line, re.I)
        if not dates and not certificate:
            continue

        course = line
        if certificate:
            course = course.replace(certificate.group(0), " ")
        for date in dates:
            course = course.replace(date, " ")
        course = clean(course)
        if not course or course.upper() in {"COURSE", "CERTIFICATE NO", "PLACE OF ISSUE"}:
            continue

        out.append({
            "course_name": course,
            "company_name": "",
            "certificate_no": certificate.group(0) if certificate else "",
            "from_date": iso_date(dates[0]) if dates else "",
            "to_date": iso_date(dates[1]) if len(dates) > 1 else "",
        })

    return out


def course_details(text):
    courses = course_details_from_tables(text)
    return courses if courses else course_details_fallback(text)


def parse_resume(text, filename):
    phones_found = phones(text)
    address = extract_address(text)
    city, state = extract_location_from_address(address)
    documents = extract_document_fallback(text)

    records = sea_records(text)
    indos = documents["indos"]
    for record in records:
        record["indos"] = indos

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
            "nationality": extract_nationality(text),
            "gender": extract_gender(text),
            "religion": extract_religion(text),
            "married_status": extract_marital(text),
            "passport_no": documents["passport_no"],
            "passport_from_date": documents["passport_from_date"],
            "passport_to_date": documents["passport_to_date"],
            "sid_no": documents["sid_no"],
            "coc_no": documents["coc_no"],
            "coc_country": documents["coc_country"],
            "coc_from_date": documents["coc_from_date"],
            "coc_to_date": documents["coc_to_date"],
            "cdc_country": documents["cdc_country"],
            "cdc_no": documents["cdc_no"],
            "cdc_from_date": documents["cdc_from_date"],
            "cdc_to_date": documents["cdc_to_date"],
            "language_knows": extract_languages(text),
        },
        "sea_experience": {
            "indos": indos,
            "total_experience_month": total_months(records),
            "vessel_types": unique_types(records),
            "records": records,
        },
        "course_details": course_details(text),
        "uploaded_file_name": filename,
    }
