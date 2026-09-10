from pathlib import Path
import re
from collections import OrderedDict
from pypdf import PdfReader

base = Path(r"c:\Users\Owner\Downloads\2028학년도 대학입학전형시행계획")
output = base / "sports_departments_found.csv"

EXCLUDED = {
    '체육교육과',
    '사범대학',
    '대학원',
    '교직과정',
    '특수체육교육과',
}

# Keep sports-related department names broad enough to catch actual department labels
SPORT_KEYWORDS = [
    '체육', '스포츠', '운동', '레저', '골프', '태권도', '무도', 'e스포츠', '게임',
    '재활', '심리', '복지', '산업', '경영', '마케팅', '청소년지도', '생활체육', '건강',
    '예술', '지도', '문화', '관광', '대학', '학과', '학부', '전공', '트랙'
]


def parse_filename(path: Path):
    stem = path.stem
    m = re.search(r'^(.*)\[(.*)\]_(\d{4})$', stem)
    if m:
        return m.group(1).strip(), m.group(2).strip()

    # fallback for files like 경국대학교_국립_[경북]_2028.pdf
    m = re.search(r'^(.*)_국립_\[(.*)\]_(\d{4})$', stem)
    if m:
        return m.group(1).strip(), m.group(2).strip()

    if stem.endswith('_2028'):
        return stem[:-5].strip(), ''

    return stem.strip(), ''


def extract_text(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ''
        pages.append(text)
    return '\n'.join(pages)


def candidate_depts(text: str):
    # capture strings ending in 학과/학부/전공/트랙, with a reasonable amount of content
    # also catches variants like '스포츠산업학과', '무용전공', 'e스포츠학과'
    pattern = r'([가-힣A-Za-z0-9\-\+\(\)\s]+(?:학과|학부|전공|트랙))'
    matches = re.findall(pattern, text)
    results = []
    for m in matches:
        dept = re.sub(r'\s+', '', m).strip()
        if len(dept) < 3:
            continue
        if dept in EXCLUDED:
            continue
        results.append(dept)
    return results


def is_relevant(dept: str):
    # skip obvious non-sports departments
    if dept in EXCLUDED:
        return False
    if dept.endswith('교육과'):
        return False
    # allow only dept names that contain a sports-related term
    if any(term in dept for term in ['체육', '스포츠', '운동', '레저', '골프', '태권도', '무도', 'e스포츠', '게임', '재활', '심리', '복지', '산업', '경영', '마케팅', '지도', '청소년', '생활체육', '운동건강', '예술']):
        return True
    return False


def normalize_name(name: str):
    name = re.sub(r'\s+', '', name)
    if name.endswith('학과') or name.endswith('학부') or name.endswith('전공') or name.endswith('트랙'):
        return name
    return name

files = sorted(base.glob('*.pdf'))
rows = []

for f in files:
    school, region = parse_filename(f)
    text = extract_text(f)

    depts = OrderedDict()
    for dept in candidate_depts(text):
        dept = normalize_name(dept)
        if is_relevant(dept):
            depts[dept] = True

    if not depts:
        continue

    for dept in depts.keys():
        rows.append((school, region, dept))

# write CSV
with output.open('w', encoding='utf-8', newline='') as fp:
    fp.write('대학명,지역,학과명\n')
    for school, region, dept in rows:
        fp.write(f'{school},{region},{dept}\n')

print(f'WROTE {len(rows)} rows to {output}')
