import streamlit as st
import pandas as pd
import altair as alt
import os

st.set_page_config(page_title="국내 지진 분석", layout="wide")
st.title("📊 국내 지진 발생 분석 Dashboard")

file_name = "최근10년간 국내지진목록.xlsx"

# ------------------------------
# 1) 파일 존재 여부 확인
# ------------------------------
if not os.path.exists(file_name):
    st.error(f"❌ 동일 폴더에 `{file_name}` 파일이 없습니다.")
    st.stop()

# ------------------------------
# 2) 헤더 자동 감지
# ------------------------------
raw = pd.read_excel(file_name, header=None)

header_row = None

for i in range(10):  # 첫 10행 검사
    row = raw.iloc[i]

    # 숫자 포함하면 데이터 행으로 볼 가능성
    numeric_count = pd.to_numeric(row, errors="coerce").notnull().sum()

    # 보통 데이터 행은 숫자가 2개 이상 있음
    if numeric_count >= 2:
        header_row = i - 1 if i > 0 else i
        break

if header_row is None:
    header_row = 0

df = pd.read_excel(file_name, header=header_row)
df.columns = df.columns.map(lambda x: str(x).strip())

# ------------------------------
# 3) 완전 자동 컬럼 감지 함수
# ------------------------------

time_candidates = ["발생시각", "시각", "발생 일시", "date", "time"]
mag_candidates = ["규모", "M", "MAG", "Magnitude", "진도"]
region_candidates = ["위치", "지역", "발생지", "발생 장소"]
lat_candidates = ["위도", "lat", "latitude"]
lon_candidates = ["경도", "lon", "longitude"]

def find_col(candidates):
    for c in df.columns:
        c_low = str(c).lower().replace(" ", "")
        for key in candidates:
            if key.lower().replace(" ", "") in c_low:
                return c
    return None

col_time_auto = find_col(time_candidates)
col_mag_auto = find_col(mag_candidates)
col_region_auto = find_col(region_candidates)
col_lat_auto = find_col(lat_candidates)
col_lon_auto = find_col(lon_candidates)

# ------------------------------
# 4) 사이드바에서 사용자 선택
# ------------------------------
st.sidebar.subheader("📌 감지된 컬럼")
st.sidebar.write(df.columns.tolist())

st.sidebar.subheader("📌 분석에 사용할 컬럼 지정")

col_time = st.sidebar.selectbox(
    "발생시각 컬럼",
    df.columns,
    index=df.columns.get_loc(col_time_auto) if col_time_auto in df.columns else 0
)

col_mag = st.sidebar.selectbox(
    "규모 컬럼",
    df.columns,
    index=df.columns.get_loc(col_mag_auto) if col_mag_auto in df.columns else 0
)

col_region = st.sidebar.selectbox(
    "지역 컬럼",
    df.columns,
    index=df.columns.get_loc(col_region_auto) if col_region_auto in df.columns else 0
)

col_lat = st.sidebar.selectbox(
    "위도 컬럼(없으면 없음)",
    ["없음"] + df.columns.tolist(),
    index=(df.columns.get_loc(col_lat_auto) + 1) if col_lat_auto in df.columns else 0
)

col_lon = st.sidebar.selectbox(
    "경도 컬럼(없으면 없음)",
    ["없음"] + df.columns.tolist(),
    index=(df.columns.get_loc(col_lon_auto) + 1) if col_lon_auto in df.columns else 0
)

# ------------------------------
# 5) 데이터 전처리
# ------------------------------

# 발생 시각 처리
df["발생시각_변환"] = pd.to_datetime(df[col_time], errors="coerce")
df["연도"] = df["발생시각_변환"].dt.year

# 규모 숫자 변환
df[col_mag] = pd.to_numeric(df[col_mag], errors="coerce")

# 구간화
df["규모_구간"] = pd.cut(
    df[col_mag],
    bins=[0, 2, 3, 4, 5, 6, 10],
    labels=["0~2", "2~3", "3~4", "4~5", "5~6", "6 이상"],
    include_lowest=True
)

st.success("엑셀 헤더 자동 감지 성공 ✓ 데이터 정상 로딩 완료!")

# ------------------------------
# 6) 데이터 미리보기
# ------------------------------
st.write("### 🔎 데이터 미리보기")
st.dataframe(df.head())

# ------------------------------
# 7) 연도별 지진 횟수
# ------------------------------
st.write("### 📈 연도별 지진 발생 추이")

year_count = df.groupby("연도")[col_mag].count().reset_index().rename(columns={col_mag: "발생횟수"})

chart_year = (
    alt.Chart(year_count)
    .mark_line(point=True)
    .encode(
        x="연도:O",
        y="발생횟수:Q"
    )
)
st.altair_chart(chart_year, use_container_width=True)

# ------------------------------
# 8) 지역별 발생 횟수
# ------------------------------
st.write("### 📍 지역별 지진 발생 횟수")

region_count = df[col_region].value_counts().reset_index()
region_count.columns = ["지역", "발생횟수"]

chart_region = (
    alt.Chart(region_count)
    .mark_bar()
    .encode(
        x="지역:N",
        y="발생횟수:Q"
    )
)

st.altair_chart(chart_region, use_container_width=True)

# ------------------------------
# 9) 위도·경도 있을 때 지도 표시
# ------------------------------
if col_lat != "없음" and col_lon != "없음":
    st.write("### 🗺 지진 위치 지도")
    map_df = df[[col_lat, col_lon]].dropna()
    map_df.columns = ["lat", "lon"]
    st.map(map_df)
