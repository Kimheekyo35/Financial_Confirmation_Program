from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from pathlib import Path
import json
import pandas as pd
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

df = pd.read_csv(Path(__file__).parent / "address_similarity_dataset.csv", encoding="utf-8")

# 주소 정규화
df["normalized_input_address"] = df.apply(lambda x: normalize_address(x["input_address"]), axis=1)
df["normalized_reference_address"] = df.apply(lambda x: normalize_address(x["reference_address"]), axis=1)

# TF-IDF 벡터화
vectorizer = TfidfVectorizer(
    analyzer='char',  # 문자 단위로 분석
    ngram_range=(3, 4),  # 연속된 3~4글자 단위로 분석
)

# 기존 주소를 이용해 tf-idf 학습
reference_addresses = vectorizer.fit_transform(df["normalized_reference_address"])

# 기존 주소에 등장하는 문자 패턴의 중요도 계산
vectorizer.fit(df["normalized_input_address"])

# 정규화 적용한 열의 유사도 계산
input_vectors = vectorizer.transform(df["normalized_input_address"])
reference_vectors = vectorizer.transform(df["normalized_reference_address"])

df["tfidf_similarity"] = (input_vectors.multiply(reference_vectors).sum(axis=1).A1*100)

# df.to_csv(Path(__file__).parent / "address_similarity_dataset_with_tfidf.csv", index=False, encoding="utf-8-sig")

print(df.groupby("actual_match")["tfidf_similarity"].describe())

for threshold in [70, 75, 80, 85, 90, 95]:
    pred = (df["tfidf_similarity"] >= threshold).astype(int)

    print(f"Threshold: {threshold}")
    print(f"Precision: {precision_score(df['actual_match'], pred)}")
    print(f"Recall: {recall_score(df['actual_match'], pred)}")
    print(f"F1-Score: {f1_score(df['actual_match'], pred)}")
    print()