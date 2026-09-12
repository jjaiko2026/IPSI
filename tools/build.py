#!/usr/bin/env python3
"""data/대학/*/ 의 모집요강·입시결과를 하나로 합쳐 bundle.json / index.json 을 만든다.

사용법:  python3 tools/build.py
결과:    data/bundle.json  ← 웹페이지(전략판)에서 '파일 불러오기'로 받는 파일
         data/index.json   ← 대학별 입력 진행 상황
"""
import json, os, sys, glob, datetime

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
UNI = os.path.join(ROOT, "대학")

def read(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8-sig") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            print("  ! JSON 오류 %s: %s" % (path, e), file=sys.stderr)
            return None

def main():
    bundle, index = [], []
    for d in sorted(glob.glob(os.path.join(UNI, "*"))):
        if not os.path.isdir(d):
            continue
        name = os.path.basename(d)
        mo = read(os.path.join(d, "모집요강.json")) or {}
        gy = read(os.path.join(d, "입시결과.json")) or {}
        jh = mo.get("전형") or []
        gs = gy.get("결과") or []
        wonmun = len(glob.glob(os.path.join(d, "원문", "*")))
        chuchul = len(glob.glob(os.path.join(d, "추출", "*")))
        if jh or gs:
            bundle.append({
                "대학명": mo.get("대학명") or name,
                "지역": mo.get("지역") or gy.get("지역") or "",
                "학년도": mo.get("학년도", 2028),
                "갱신일": mo.get("갱신일") or "",
                "전형": jh,
                "입시결과": gs,
            })
        index.append({
            "대학명": name, "지역": mo.get("지역") or gy.get("지역") or "",
            "폴더": os.path.relpath(d, os.path.dirname(ROOT)).replace(os.sep, "/"),
            "전형수": len(jh), "결과수": len(gs), "원문": wonmun, "추출": chuchul,
            "확인완료": sum(1 for x in jh if x.get("확인") == "확인됨"),
        })

    out = {"학년도": 2028, "만든날짜": datetime.date.today().isoformat(),
           "대학수": len(bundle), "대학": bundle}
    with open(os.path.join(ROOT, "bundle.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    with open(os.path.join(ROOT, "index.json"), "w", encoding="utf-8") as f:
        json.dump({"학년도": 2028, "대학수": len(index), "대학": index}, f, ensure_ascii=False, indent=2)

    done = sum(x["확인완료"] for x in index)
    tot = sum(x["전형수"] for x in index)
    print("bundle.json: 대학 %d · 전형 %d · 입시결과 %d"
          % (len(bundle), tot, sum(x["결과수"] for x in index)))
    print("확인 완료 전형 %d / %d" % (done, tot))

if __name__ == "__main__":
    main()
