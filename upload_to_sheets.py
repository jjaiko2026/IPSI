#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV 결과물을 구글시트에 자동 업로드
실행 전: Google Cloud Console에서 OAuth 자격증명 필요
  1. https://console.cloud.google.com
  2. 새 프로젝트 생성
  3. Google Sheets API + Google Drive API 활성화
  4. OAuth 2.0 클라이언트 ID (데스크톱 앱) 생성
  5. credentials.json 다운로드 → 이 스크립트와 같은 폴더에 저장
"""

import csv
import os
import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

BASE_DIR = r"C:\Users\Owner\Downloads\2028학년도 대학입학전형시행계획"
SUSI_CSV = os.path.join(BASE_DIR, "결과_수시_학생부교과.csv")
JEONGSI_CSV = os.path.join(BASE_DIR, "결과_정시.csv")
CREDS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.pickle")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)
    return creds

def read_csv(filepath):
    rows = []
    with open(filepath, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            rows.append(row)
    return rows

def upload_csv_to_sheet(gc, spreadsheet, sheet_name, csv_path):
    data = read_csv(csv_path)
    if not data:
        print(f"  [{sheet_name}] 데이터 없음")
        return

    try:
        ws = spreadsheet.worksheet(sheet_name)
        ws.clear()
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=sheet_name, rows=len(data)+10, cols=len(data[0])+2)

    # 헤더 스타일 (굵게)
    ws.update(range_name="A1", values=data)
    ws.format("1:1", {
        "backgroundColor": {"red": 0.2, "green": 0.4, "blue": 0.8},
        "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
        "horizontalAlignment": "CENTER"
    })
    print(f"  [{sheet_name}] {len(data)-1}행 업로드 완료")

def main():
    if not os.path.exists(CREDS_FILE):
        print("❌ credentials.json 파일이 없습니다.")
        print("   Google Cloud Console에서 OAuth 자격증명을 만들고")
        print(f"   {CREDS_FILE} 경로에 저장하세요.")
        return

    if not os.path.exists(SUSI_CSV) or not os.path.exists(JEONGSI_CSV):
        print("❌ CSV 결과 파일이 없습니다. extract_all.py를 먼저 실행하세요.")
        return

    print("🔐 구글 계정 인증 중...")
    creds = get_credentials()
    gc = gspread.authorize(creds)

    print("📊 구글시트 생성 중...")
    spreadsheet = gc.create("2028학년도 대학입학전형시행계획 - 성적계산 자료")

    # 공유 설정 (링크 있으면 누구나 보기)
    spreadsheet.share(None, perm_type="anyone", role="reader")

    print("📤 데이터 업로드 중...")
    upload_csv_to_sheet(gc, spreadsheet, "수시_학생부교과", SUSI_CSV)
    upload_csv_to_sheet(gc, spreadsheet, "정시_수능반영비율", JEONGSI_CSV)

    # 기본 시트(Sheet1) 삭제
    try:
        default_sheet = spreadsheet.worksheet("Sheet1")
        spreadsheet.del_worksheet(default_sheet)
    except:
        pass

    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}"
    print(f"\n✅ 구글시트 업로드 완료!")
    print(f"🔗 링크: {url}")

    # 링크를 파일로도 저장
    with open(os.path.join(BASE_DIR, "구글시트_링크.txt"), "w", encoding="utf-8") as f:
        f.write(url + "\n")

if __name__ == "__main__":
    main()
