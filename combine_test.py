from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from pathlib import Path
import json
import pandas as pd

BASE = Path("C:/Users/XQ233LE/OneDrive - EY/IT/financial_address")

# TF-IDF 기반 주소 유사도 계산
tfidf_df = pd.read_csv(BASE/"address_similarity_dataset_with_tfidf.csv", encoding="utf-8")

# RapidFuzz 기반 주소 유사도 계산
rapid_df = pd.read_csv(BASE/"rapidfuzz_test_result.csv", encoding="utf-8")

# 1. 두 데이터셋 병합
keys = [
    "bank_name",
    "input_address",
    "reference_address",
    "actual_match",
    "error_type"
]

df = pd.merge(
    rapid_df,
    tfidf_df[keys + ["tfidf_similarity"]],
    on = keys,
    how = "inner",
    validate="one_to_one"
)

# 2. 임계값 적용
df["rapid_pred"] = (df["rapidfuzz_score"] >= 85).astype(int) # 85점 이상이면 1, 아니면 0
df["tfidf_pred"] = (df["tfidf_similarity"] >= 70).astype(int) # 70점 이상이면 1, 아니면 0

# 3. 정답 확인
df["rapid_answer"] = (df["rapid_pred"] == df["actual_match"])
df["tfidf_answer"] = (df["tfidf_pred"] == df["actual_match"])

# 4. 오류 유형 분류
def classify_error(row):

    rf = row["rapid_answer"]
    tf = row["tfidf_answer"]

    if rf == tf:
        return "Both correct"

    elif rf and not tf:
        return "Rapidfuzz Only"

    elif tf and not rf:
        return "TF-IDF Only"

    else:
        return "Both incorrect"

df["comparison_result"] = df.apply(
    classify_error,
    axis=1
)

# 5. 결과 확인
print(df["comparison_result"].value_counts())

# 6. csv.저장
df.to_csv(
    BASE / "similarity_error_analysis.csv",
    index=False,
    encoding="utf-8-sig"
)