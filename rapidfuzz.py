import pandas as pd
from rapidfuzz import fuzz
from pathlib import Path
import unicodedata
import re
import json
import tabulate
from sklearn.metrics import precision_score, recall_score, f1_score


BASE = Path("C:/Users/XQ233LE/OneDrive - EY/IT/financial_json_dir")

# 주소 Alias 설정
REGION_ALIAS_GROUPS = {
    "서울": ["서울특별시", "서울시", "서울"],
    "부산": ["부산광역시", "부산시", "부산","부산직할시"],
    "대구": ["대구광역시", "대구시", "대구"],
    "인천": ["인천광역시", "인천시", "인천"],
    "광주": ["광주광역시", "광주"],
    "대전": ["대전광역시", "대전시", "대전"],
    "울산": ["울산광역시", "울산시", "울산"],
    "세종": ["세종특별자치시", "세종시", "세종"],
    "경기": ["경기도", "경기"],
    "강원": ["강원특별자치도", "강원도", "강원"],
    "충북": ["충청북도", "충북도", "충북"],
    "충남": ["충청남도", "충남도", "충남"],
    "전북": ["전북특별자치도", "전라북도", "전북도", "전북"],
    "전남": ["전라남도", "전남도", "전남"],
    "경북": ["경상북도", "경북도", "경북"],
    "경남": ["경상남도", "경남도", "경남"],
    "제주": ["제주특별자치도", "제주도", "제주"],
    "전남광주": ["전남광주통합특별시", "전남광주"],
}

# 주소 정규화 함수
def normalize_address(address):
    address = str(address).strip()

    for standard, aliases in REGION_ALIAS_GROUPS.items():
        for alias in sorted(aliases, key=len, reverse=True):  # 긴 별칭부터 치환
            address = re.sub(
            rf"^{re.escape(alias)}(?=\s|$)",
            standard,
            address
            )
    address = re.sub(r"\s+", " ", address)

    return address


# 회사별 별칭 json 불러오기
with open(BASE/"company_alias.json",encoding="utf-8") as f:
    company_alias = json.load(f)

# 회사명 정규화 함수
def norm_company(company_name):
    company_name = str(company_name).strip()

    for bank_name, company_info in company_alias.items():
        bank_name = company_info["name"]

        for alias in sorted(company_info["aliases"], key=len, reverse=True):  # 긴 별칭부터 치환
            company_name = re.sub(
            rf"^{re.escape(alias)}(?=\s|$)",
            bank_name,
            company_name
            )

    company_name = re.sub(r"\s+", " ", company_name)

    return company_name


df = pd.read_csv(Path(__file__).parent / "address_similarity_dataset.csv", encoding="utf-8",)

df["rapidfuzz_score"] = df.apply(lambda row:fuzz.ratio(normalize_address(row["input_address"]), normalize_address(row["reference_address"])), axis=1)
# df["norm_bank_nm"] = df.apply(lambda row: norm_company(row["input_bank_name"]), axis=1)

# df.to_csv(Path(__file__).parent / "rapidfuzz_test_result.csv", index=False, encoding="utf-8-sig")

result_csv = pd.read_csv(Path(__file__).parent / "rapidfuzz_test_result.csv", encoding="utf-8-sig")
result_head = result_csv.head()

print(result_csv.groupby("actual_match")["rapidfuzz_score"].describe())
print()

# Precision, Recall, F1 Score 계산

for threshold in [80,85,90,95,98]:
    pred = (result_csv["rapidfuzz_score"] >= threshold).astype(int)

    print(f"Threshold: {threshold}")
    print(f"Precision: {precision_score(result_csv['actual_match'], pred)}")
    print(f"Recall: {recall_score(result_csv['actual_match'], pred)}")
    print(f"F1 Score: {f1_score(result_csv['actual_match'], pred)}")
    print()