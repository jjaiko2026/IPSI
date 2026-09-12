#!/usr/bin/env python3
"""data/대학/*/원문/*.pdf 를 읽어 텍스트로 풀고, 전형 자료가 있을 만한 대목을 뽑아낸다.

사용법:  python3 tools/pdf_scan.py            전체
         python3 tools/pdf_scan.py 경북대학교   한 대학만

만드는 파일 (대학 폴더 안):
  원문/<파일이름>.txt   페이지 번호가 붙은 전체 텍스트 (검색용)
  단서.json             항목별로 찾은 대목 + 페이지 번호

모집요강 표는 대학마다 생김새가 달라 값을 자동으로 확정하지 않는다.
어디를 봐야 하는지까지만 좁혀 주고, 값은 사람이 원문을 보고 적는다.
"""
import json, os, re, sys, glob

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "대학")

CATS = [
    ("반영비율", r"전형요소별\s*배점|전형요소\s*및\s*반영|반영비율|일괄합산|단계별\s*전형|사정단계"),
    ("교과반영", r"교과\s*성적\s*반영|학생부\s*반영|등급\s*환산|환산\s*점수|반영\s*교과|학년별\s*반영|이수\s*단위|석차등급"),
    ("수능최저", r"수능\s*최저|최저학력기준|등급\s*합"),
    ("수능반영", r"영역별\s*반영|수능\s*반영|백분위|표준점수|변환점수"),
    ("실기", r"실기고사|실기\s*종목|실기\s*배점|실기\s*평가"),
    ("입시결과", r"입시\s*결과|입학\s*결과|합격자\s*성적|등록자\s*성적|경쟁률|충원|추가\s*합격|70\s*%|50\s*%\s*컷"),
]
PCT = re.compile(r"\d{1,3}\s*%")
GRADE_SUM = re.compile(r"(\d)\s*개\s*영역\s*(?:등급\s*)?합\s*(\d{1,2})")
WINDOW = 240
MAX_PER_CAT = 8


def score(s):
    """값이 적혀 있을 법한 대목을 앞으로 보낸다."""
    return (3 * len(re.findall(r"\d{1,3}\s*%", s)) + 2 * s.count("점")
            + len(re.findall(r"\d", s)) // 4)


def clean(s):
    return re.sub(r"[ \t ]+", " ", s.replace("　", " ")).strip()


def scan(text_pages):
    out = {}
    seen = set()
    for name, pat in CATS:
        rx = re.compile(pat)
        hits = []
        for pno, page in text_pages:
            for m in rx.finditer(page):
                a = max(0, m.start() - WINDOW // 3)
                b = min(len(page), m.end() + WINDOW)
                snip = clean(page[a:b])
                key = snip[:60]
                if key in seen:
                    continue
                seen.add(key)
                hits.append({"쪽": pno, "발췌": snip})
                if len(hits) >= MAX_PER_CAT:
                    break
            if len(hits) >= MAX_PER_CAT:
                break
        if hits:
            hits.sort(key=lambda h: -score(h["발췌"]))
            out[name] = hits
    return out


def numbers(text):
    pct = sorted({int(x.rstrip("%").strip()) for x in PCT.findall(text)
                  if 0 < int(x.rstrip("%").strip()) <= 100})
    cj = [{"영역수": int(a), "등급합": int(b)} for a, b in GRADE_SUM.findall(text)]
    uniq, seen = [], set()
    for c in cj:
        k = (c["영역수"], c["등급합"])
        if k not in seen:
            seen.add(k); uniq.append(c)
    return {"등장한_비율": pct[:40], "등급합_조건": uniq[:12]}


def main():
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz
        except ImportError:
            print("PyMuPDF가 필요합니다:  pip install pymupdf", file=sys.stderr)
            return 1

    only = sys.argv[1] if len(sys.argv) > 1 else None
    dirs = sorted(glob.glob(os.path.join(ROOT, only or "*")))
    total = done = 0
    for d in dirs:
        if not os.path.isdir(d):
            continue
        pdfs = sorted(glob.glob(os.path.join(d, "원문", "*.pdf")))
        if not pdfs:
            continue
        total += 1
        uni = os.path.basename(d)
        clues = {"대학명": uni, "만든날짜": "", "원문": []}
        for pdf in pdfs:
            try:
                doc = fitz.open(pdf)
            except Exception as e:
                print("  ! 열지 못함 %s: %s" % (os.path.basename(pdf), e), file=sys.stderr)
                continue
            pages = [(i + 1, p.get_text()) for i, p in enumerate(doc)]
            doc.close()
            whole = "\n".join(t for _, t in pages)
            txt_path = os.path.splitext(pdf)[0] + ".txt"
            with open(txt_path, "w", encoding="utf-8") as f:
                for pno, t in pages:
                    f.write("\n===== %d쪽 =====\n" % pno)
                    f.write(t)
            clues["원문"].append({
                "파일": os.path.basename(pdf), "쪽수": len(pages), "글자수": len(whole),
                "텍스트없음": len(whole.strip()) < 200,
                "숫자": numbers(whole), "단서": scan(pages),
            })
        if clues["원문"]:
            import datetime
            clues["만든날짜"] = datetime.date.today().isoformat()
            with open(os.path.join(d, "단서.json"), "w", encoding="utf-8") as f:
                json.dump(clues, f, ensure_ascii=False, indent=1)
            done += 1
            empty = [o["파일"] for o in clues["원문"] if o["텍스트없음"]]
            print("%-22s 원문 %d건%s" % (uni, len(clues["원문"]),
                  "  ← 텍스트가 없는 스캔본: " + ", ".join(empty) if empty else ""))
    print("\n%d / %d 개 대학 처리" % (done, total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
