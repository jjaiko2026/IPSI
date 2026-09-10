#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2028학년도 대학입학전형시행계획 PDF 전체 분석 스크립트
- 수시: 학생부교과 일반학생 전형 위주
- 정시: 전체 (의학계열, 무도계열 제외)
- 성적 계산 가능한 표 형태로 출력
"""

import os
import re
import csv
import pdfplumber

PDF_DIR = r"C:\Users\Owner\Downloads\2028학년도 대학입학전형시행계획"
OUTPUT_SUSI = os.path.join(PDF_DIR, "결과_수시_학생부교과.csv")
OUTPUT_JEONGSI = os.path.join(PDF_DIR, "결과_정시.csv")
OUTPUT_ALL = os.path.join(PDF_DIR, "결과_전체통합.csv")

# 제외 키워드 (의학계열, 무도계열)
EXCLUDE_DEPT = [
    "의학", "의예", "치의학", "치의예", "한의학", "한의예", "수의학", "수의예",
    "약학", "약대", "의대", "치대", "한의대",
    "유도", "태권도", "권투", "복싱", "레슬링", "씨름", "검도", "무도", "격투",
    "경호무도", "무술"
]

# 수시 학생부교과 관련 키워드
SUSI_KEYWORD = ["학생부교과", "교과전형", "교과우수", "학생부 교과", "일반전형", "지역인재",
                "교과성적우수", "학교장추천"]

# 수시 제외 전형 (종합, 논술, 실기, 특기자 등)
SUSI_EXCLUDE = ["학생부종합", "종합전형", "논술", "실기", "특기자", "어학", "사회배려",
                "농어촌", "특성화고", "기회균형", "장애인", "만학도", "재직자",
                "군인", "기초생활", "차상위"]

# 정시 관련 키워드
JEONGSI_KEYWORD = ["정시", "가군", "나군", "다군", "수능위주", "수능100"]

def get_univ_region(filename):
    """파일명에서 대학명, 지역 추출"""
    name = filename.replace(".pdf", "")
    # 지역 추출 [지역]
    region_match = re.search(r'\[([^\]]+)\]', name)
    region = region_match.group(1) if region_match else "미상"
    # 대학명 추출
    univ = re.sub(r'\[.*?\]', '', name)
    univ = re.sub(r'_국립_?', '', univ)
    univ = re.sub(r'_\d{4}$', '', univ)
    univ = univ.strip().rstrip('_ ')
    return univ, region

def is_excluded_dept(dept_name):
    """제외 학과인지 확인"""
    for kw in EXCLUDE_DEPT:
        if kw in dept_name:
            return True
    return False

def extract_text_all_pages(pdf_path):
    """PDF 전체 텍스트 추출"""
    texts = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    texts.append(t)
    except Exception as e:
        print(f"  [오류] {os.path.basename(pdf_path)}: {e}")
    return "\n".join(texts)

def find_susi_gyogwa(text, univ, region):
    """수시 학생부교과 전형 정보 추출"""
    results = []
    lines = text.split("\n")

    # 전형별 섹션 파악
    current_jeonhyung = None
    current_dept = None
    current_incount = None
    current_ratio = None
    capture = False

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        # 수시 학생부교과 전형 감지
        is_susi = any(kw in line for kw in SUSI_KEYWORD)
        is_excluded = any(kw in line for kw in SUSI_EXCLUDE)

        if is_susi and not is_excluded:
            current_jeonhyung = line[:80]
            capture = True
        elif any(kw in line for kw in ["정시모집", "Ⅲ.", "III.", "◆ 정시"]):
            capture = False

        if not capture:
            continue

        # 모집인원 패턴
        incount_match = re.search(r'(\d+)\s*명', line)

        # 반영비율 패턴 (학생부 OO%)
        ratio_match = re.search(r'학생부\s*교과[^\d]*(\d+)[^\d]*%', line)
        if not ratio_match:
            ratio_match = re.search(r'교과\s*(\d+)\s*%', line)

        # 학과명 패턴 (줄에 학과/전공/부/학부 포함)
        dept_match = re.search(r'[가-힣A-Za-z\s]+(?:학과|전공|학부|대학|계열|과|부)', line)

        if dept_match:
            dept_candidate = dept_match.group(0).strip()
            if len(dept_candidate) > 2 and not is_excluded_dept(dept_candidate):
                current_dept = dept_candidate[:50]

        if incount_match:
            current_incount = incount_match.group(1)

        if ratio_match:
            current_ratio = ratio_match.group(0)[:60]

        # 충분한 정보가 모이면 레코드 추가
        if current_jeonhyung and current_dept and current_incount:
            record = {
                "대학명": univ,
                "지역": region,
                "전형구분": "수시",
                "전형명": current_jeonhyung,
                "학과명": current_dept,
                "모집인원": current_incount,
                "전형요소_반영비율": current_ratio or "확인필요",
                "수능최저": "",
                "원서접수": "",
                "비고": ""
            }
            results.append(record)
            current_incount = None
            current_dept = None

    return results

def find_jeongsi(text, univ, region):
    """정시 수능 반영비율 추출"""
    results = []
    lines = text.split("\n")
    capture = False
    current_group = ""
    current_dept = None
    current_incount = None
    subj_ratio = {"국어": "", "수학": "", "영어": "", "탐구": "", "한국사": ""}

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        if any(kw in line for kw in ["정시모집", "Ⅲ. 정시", "◆ 정시", "III. 정시"]):
            capture = True

        if not capture:
            continue

        # 군 구분
        group_match = re.search(r'([가나다])\s*군', line)
        if group_match:
            current_group = group_match.group(1) + "군"

        # 과목별 반영비율
        for subj in ["국어", "수학", "영어", "탐구", "한국사"]:
            match = re.search(subj + r'[^%\d]*(\d+)\s*%', line)
            if match:
                subj_ratio[subj] = match.group(1) + "%"

        # 모집인원
        incount_match = re.search(r'(\d+)\s*명', line)
        if incount_match:
            current_incount = incount_match.group(1)

        # 학과명
        dept_match = re.search(r'[가-힣A-Za-z\s]+(?:학과|전공|학부|계열|과|부)', line)
        if dept_match:
            dept_candidate = dept_match.group(0).strip()
            if len(dept_candidate) > 2 and not is_excluded_dept(dept_candidate):
                current_dept = dept_candidate[:50]

        if current_dept and current_incount and any(subj_ratio.values()):
            ratio_str = " | ".join(f"{k}:{v}" for k, v in subj_ratio.items() if v)
            record = {
                "대학명": univ,
                "지역": region,
                "전형구분": "정시",
                "군": current_group,
                "학과명": current_dept,
                "모집인원": current_incount,
                "국어비율": subj_ratio["국어"],
                "수학비율": subj_ratio["수학"],
                "영어비율": subj_ratio["영어"],
                "탐구비율": subj_ratio["탐구"],
                "한국사비율": subj_ratio["한국사"],
                "과목별반영비율": ratio_str,
                "비고": ""
            }
            results.append(record)
            current_incount = None
            current_dept = None

    return results


def main():
    pdf_files = sorted([f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")])
    print(f"총 {len(pdf_files)}개 PDF 파일 처리 시작\n")

    all_susi = []
    all_jeongsi = []

    for idx, fname in enumerate(pdf_files, 1):
        fpath = os.path.join(PDF_DIR, fname)
        univ, region = get_univ_region(fname)
        print(f"[{idx:3d}/{len(pdf_files)}] {univ} ({region}) 처리 중...")

        text = extract_text_all_pages(fpath)
        if not text:
            print(f"  → 텍스트 추출 실패, 건너뜀")
            continue

        susi = find_susi_gyogwa(text, univ, region)
        jeongsi = find_jeongsi(text, univ, region)
        all_susi.extend(susi)
        all_jeongsi.extend(jeongsi)
        print(f"  → 수시 {len(susi)}건 / 정시 {len(jeongsi)}건")

    # 수시 CSV 저장
    susi_fields = ["대학명","지역","전형구분","전형명","학과명","모집인원",
                   "전형요소_반영비율","수능최저","원서접수","비고"]
    with open(OUTPUT_SUSI, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=susi_fields)
        writer.writeheader()
        writer.writerows(all_susi)

    # 정시 CSV 저장
    jeongsi_fields = ["대학명","지역","전형구분","군","학과명","모집인원",
                      "국어비율","수학비율","영어비율","탐구비율","한국사비율",
                      "과목별반영비율","비고"]
    with open(OUTPUT_JEONGSI, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=jeongsi_fields)
        writer.writeheader()
        writer.writerows(all_jeongsi)

    print(f"\n✅ 완료!")
    print(f"  수시 학생부교과: {len(all_susi)}건 → {OUTPUT_SUSI}")
    print(f"  정시: {len(all_jeongsi)}건 → {OUTPUT_JEONGSI}")


if __name__ == "__main__":
    main()
