from pathlib import Path
from pypdf import PdfReader

folder = Path(r'c:\Users\Owner\Downloads\2028학년도 대학입학전형시행계획')
files = sorted(folder.glob('*.pdf'))
keywords = ['스포츠', '체육', '무용', '태권도']

for p in files:
    try:
        text = '\n'.join(page.extract_text() or '' for page in PdfReader(str(p)).pages)
    except Exception as e:
        print(f'ERROR {p.name}: {e}')
        continue

    if not any(kw in text for kw in keywords):
        continue

    lines = []
    for line in text.splitlines():
        if any(kw in line for kw in keywords) and any(k in line for k in ('학과', '학부', '전공')):
            line = line.strip()
            if line:
                lines.append(line)

    if lines:
        print(f'=== {p.name} ===')
        for line in lines[:80]:
            print(line[:500])
        print()
