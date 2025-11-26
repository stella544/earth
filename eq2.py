import streamlit as st
import pandas as pd
import altair as alt
import os

st.set_page_config(page_title="국내 지진 분석", layout="wide")
st.title("📊 국내 지진 발생 분석 Dashboard")

file_name = "최근10년간 국내지진목록.xlsx"

# ==============================================
# 1) 파일 존재 체크
# ==============================================
if not os.path.exists(file_name):
    st.error(f"❌ 동일 폴더에 `{file_name}` 파일이 없습니다.")
    st.stop()

# ==============================================
# 2) 헤더 자동 감지
# ==============================================
raw = pd.read_excel(file_name, header=None)

header_row = None
for i in range(5):  
    row = raw.iloc[i]
    has_number = any(pd.to_numeric(row, errors='coerce').notnull())
    if has_number:
        header_row = i - 1 if i > 0 else i
        break

if header_row is None:
    st.error("⚠ 헤더 행을 자동으로 찾지 못했습니다.")
    st.stop()

df = pd.read_excel(file_name, header=header_row)

# 컬럼 정리
df.columns = df.columns.map(lambda x: str(x).strip())

# ==============================================
# 3) 컬럼 자동 감지
# ==============================================
time_candidates = ["발생시각", "시각", "date", "time"]
mag_candidates = ["규모", "M", "Mag", "Magnitude"]
region_candidates = ["위치", "지역"]
lat_candidates = ["위도", "lat", "latitude"]
lon_candidates = ["경도", "lon", "longitude"]

def find_col(candidates):
    for c in df.columns:
        for key in candidates:
            if key in str(c):
                return c
    return None

col_time_auto = find_col(time_candidates)
col_mag_auto = find_col(mag_candidates)
col_region_auto = find_col(region_candidates)
col_lat_auto = find_col(lat_candidates)
col_lon_auto = find_col(lon_candidates)

# ==============================================
# 4) 사용자 선택 옵션
# ==============================================
st.sidebar.subheader("📌 감지된 컬럼")
st.sidebar.write(df.columns.tolist())

st.sidebar.subheader("📌 분석에 사용할 컬럼 지정")

col_time = st.sidebar.selectbox(
    "발생시각 컬럼", df.columns,
    index=df.columns.get_loc(col_time_auto) if col_time_auto in df.columns else 0
)

col_mag = st.sidebar.selectbox(
    "규모 컬럼", df.columns,
    index=df.columns.get_loc(col_mag_auto) if col_mag_auto in df.columns else 0
)

col_region = st.sidebar.selectbox(
    "지역 컬럼", df.columns,
    index=df.columns.get_loc(col_region_auto) if col_region_auto in df.columns else 0
)

col_lat = st.sidebar.selectbox(
    "위도 컬럼(없으면 없음 선택)", ["없음"] + df.columns.tolist(),
    index=(df.columns.get_loc(col_lat_auto) + 1) if col_lat_auto in df.columns else 0
)

col_lon = st.sidebar.selectbox(
    "경도 컬럼(없으면 없음 선택)", ["없음"] + df.columns.tolist(),
    index=(df.columns.get_loc(col_lon_auto) + 1) if col_lon_auto in df.columns else 0
)

# ==============================================
# 5) 데이터 전처리
# ==============================================
df["발생시각_변환"] = pd.to_datetime(df[col_time], errors="coerce")
df["연도"] = df["발생시각_변환"].dt.year

df[col_mag] = pd.to_numeric(df[col_mag], errors="coerce")

df["규모_구간"] = pd.cut(
    df[col_mag],
    bins=[0, 2, 3, 4, 5, 6, 10],
    labels=["0~2", "2~3", "3~4", "4~5", "5~6", "6 이상"]
)

st.success("엑셀 헤더 자동 감지 성공 ✓ 데이터 정상 로딩 완료!")

st.write("### 🔎 데이터 미리보기")
st.dataframe(df.head())

# ==============================================
# 6) 시각화: 연도별 지진 발생 추이
# ==============================================
st.subheader("📈 연도별 지진 발생 추이")

year_count = df.groupby("연도").size().reset_index(name="발생횟수")

chart_year = (
    alt.Chart(year_count)
    .mark_line(point=True)
    .encode(
        x="연도:O",
        y="발생횟수:Q",
        tooltip=["연도", "발생횟수"]
    )
)

st.altair_chart(chart_year, use_container_width=True)

# ==============================================
# 7) 지역별 지진 발생 수
# ==============================================
st.subheader("📍 지역별 지진 발생 횟수")

region_count = df.groupby(col_region).size().reset_index(name="발생횟수")

chart_region = (
    alt.Chart(region_count)
    .mark_bar()
    .encode(
        x=alt.X(col_region, sort="-y"),
        y="발생횟수:Q",
        tooltip=[col_region, "발생횟수"]
    )
)

st.altair_chart(chart_region, use_container_width=True)

# ==============================================
# 8) 규모 구간별 지진 비율
# ==============================================
st.subheader("📊 규모 구간별 지진 분포")

mag_count = df["규모_구간"].value_counts().reset_index()
mag_count.columns = ["규모구간", "건수"]

chart_mag = (
    alt.Chart(mag_count)
    .mark_bar()
    .encode(
        x="규모구간:N",
        y="건수:Q",
        tooltip=["규모구간", "건수"]
    )
)

st.altair_chart(chart_mag, use_container_width=True)

# ==============================================
# 9) 지도 시각화 (위도/경도 있을 때만)
# ==============================================
if col_lat != "없음" and col_lon != "없음":
    st.subheader("🗺 지진 발생 위치 지도")

    df["lat"] = pd.to_numeric(df[col_lat], errors="coerce")
    df["lon"] = pd.to_numeric(df[col_lon], errors="coerce")

    st.map(df[["lat", "lon"]].dropna())
else:
    st.info("📌 위도/경도 컬럼이 없어 지도는 표시하지 않습니다.")
