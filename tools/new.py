#!/usr/bin/env python3
"""새 대학 폴더를 만든다.   python3 tools/new.py 서울대학교 서울"""
import json, os, sys

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "대학")

TEMPLATE_전형 = {
    "전형명": "", "학과": "", "구분": "수시 · 교과", "모집인원": None,
    "반영비율": {"교과": 100, "수능": 0, "실기": 0, "면접": 0},
    "교과반영": {"교과군": ["국어", "수학", "영어", "사회", "과학"],
                "학년가중치": {"1": 1, "2": 1, "3": 1},
                "등급점수": [100, 96, 88, 76, 60]},
    "수능반영": {"국어": 0, "수학": 0, "영어": 0, "탐구": 0,
                "영어등급점수": [100, 95, 88, 80, 70, 58, 44, 28, 10]},
    "수능최저": {"적용": False, "상위영역수": 2, "등급합": 6},
    "실기": {"종목": ""}, "확인": "미확인", "메모": "",
}
TEMPLATE_결과 = {
    "학년도": 2027, "전형명": "", "학과": "", "기준": "등급",
    "컷70": None, "컷50": None, "경쟁률": None, "충원율": None, "메모": "",
}

def main():
    if len(sys.argv) < 2:
        print(__doc__); return 1
    name, region = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "")
    d = os.path.join(ROOT, name)
    os.makedirs(os.path.join(d, "원문"), exist_ok=True)
    for fn, body in (("모집요강.json", {"대학명": name, "지역": region, "학년도": 2028,
                                       "출처": "", "갱신일": "", "전형": [TEMPLATE_전형]}),
                     ("입시결과.json", {"대학명": name, "지역": region, "갱신일": "",
                                       "결과": [TEMPLATE_결과]})):
        p = os.path.join(d, fn)
        if os.path.exists(p):
            print("건너뜀 (이미 있음):", p); continue
        with open(p, "w", encoding="utf-8") as f:
            json.dump(body, f, ensure_ascii=False, indent=2)
        print("만듦:", p)
    print("원문 PDF는", os.path.join(d, "원문"), "에 넣으세요.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
