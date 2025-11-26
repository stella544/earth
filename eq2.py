import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="국내 지진 분석", layout="wide")
st.title("📊 국내 지진 발생 분석 Dashboard")

st.sidebar.header("📂 데이터 업로드")
uploaded_file = st.sidebar.file_uploader("지진 목록 엑셀 파일 업로드", type=["xlsx"])

if uploaded_file is None:
    st.warning("엑셀 파일을 업로드하면 분석이 시작됩니다.")
    st.stop()

df = pd.read_excel(uploaded_file)

st.sidebar.subheader("📌 파일에서 자동 감지된 컬럼 목록")
st.sidebar.write(list(df.columns))

# --------------------------
# 🔍 사용자에게 컬럼 직접 선택시키기
# --------------------------

st.sidebar.subheader("📌 컬럼 선택")

col_time = st.sidebar.selectbox("발생시각 컬럼 선택", df.columns)
col_mag = st.sidebar.selectbox("규모 컬럼 선택", df.columns)
col_region = st.sidebar.selectbox("지역 컬럼 선택", df.columns)
col_lat = st.sidebar.selectbox("위도 컬럼 선택 (없으면 선택 안 함)", ["없음"] + list(df.columns))
col_lon = st.sidebar.selectbox("경도 컬럼 선택 (없으면 선택 안 함)", ["없음"] + list(df.columns))

# --------------------------
# 🔧 데이터 전처리
# --------------------------

# 날짜 변환
df['연도'] = pd.to_datetime(df[col_time], errors='coerce').dt.year

# 규모 구간
df['규모_구간'] = pd.cut(
    df[col_mag],
    bins=[0, 2, 3, 4, 5, 6, 10],
    labels=["0~2", "2~3", "3~4", "4~5", "5~6", "6 이상"]
)

# --------------------------
# 🔍 필터
# --------------------------
st.sidebar.header("🔍 데이터 필터")

지역_목록 = ["전체"] + sorted(df[col_region].dropna().unique().tolist())
선택_지역 = st.sidebar.selectbox("지역 선택", 지역_목록)

규모_선택 = st.sidebar.slider(
    "규모 범위 선택",
    float(df[col_mag].min()),
    float(df[col_mag].max()),
    (float(df[col_mag].min()), float(df[col_mag].max()))
)

연도_선택 = st.sidebar.slider(
    "연도 선택",
    int(df['연도'].min()),
    int(df['연도'].max()),
    (int(df['연도'].min()), int(df['연도'].max()))
)

# --------------------------
# 필터 적용
# --------------------------
filtered_df = df.copy()

if 선택_지역 != "전체":
    filtered_df = filtered_df[filtered_df[col_region] == 선택_지역]

filtered_df = filtered_df[
    (filtered_df[col_mag] >= 규모_선택[0]) &
    (filtered_df[col_mag] <= 규모_선택[1])
]

filtered_df = filtered_df[
    (filtered_df['연도'] >= 연도_선택[0]) &
    (filtered_df['연도'] <= 연도_선택[1])
]

# --------------------------
# 1️⃣ 지도 표시(선택된 경우)
# --------------------------
st.header("1️⃣ 지진 발생 지도")

if col_lat != "없음" and col_lon != "없음":
    try:
        st.map(filtered_df[[col_lat, col_lon]].dropna())
    except:
        st.warning("⚠️ 위도/경도 값이 숫자가 아닙니다. 지도 표시 불가.")
else:
    st.info("ℹ️ 위도/경도 컬럼이 선택되지 않아 지도 표시를 건너뜁니다.")

# --------------------------
# 2️⃣ 지역별 통계
# --------------------------
st.header("2️⃣ 지역별 지진 횟수")

region_count = filtered_df[col_region].value_counts().reset_index()
region_count.columns = ["지역", "발생횟수"]

chart_region = alt.Chart(region_count).mark_bar().encode(
    x='지역:N',
    y='발생횟수:Q'
)

st.altair_chart(chart_region, use_container_width=True)

# --------------------------
# 3️⃣ 규모별 추세
# --------------------------
st.header("3️⃣ 규모 구간별 연도별 발생 추이")

mag_year = filtered_df.groupby(['연도', '규모_구간']).size().reset_index(name='발생횟수')

chart_mag = alt.Chart(mag_year).mark_line(point=True).encode(
    x='연도:O',
    y='발생횟수:Q',
    color='규모_구간:N'
)

st.altair_chart(chart_mag, use_container_width=True)

# --------------------------
# 4️⃣ 연도별 발생량
# --------------------------
st.header("4️⃣ 연도별 총 지진 발생")

year_count = filtered_df['연도'].value_counts().sort_index().reset_index()
year_count.columns = ['연도', '발생횟수']

chart_year = alt.Chart(year_count).mark_area().encode(
    x='연도:O',
    y='발생횟수:Q'
)

st.altair_chart(chart_year, use_container_width=True)

# --------------------------
# 데이터 확인
# --------------------------
with st.expander("📄 필터 적용된 데이터 보기"):
    st.dataframe(filtered_df)
