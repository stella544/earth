import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="국내 지진 발생 분석", layout="wide")

# =============================
# 데이터 로드
# =============================
file_path = "/mnt/data/최근10년간 국내지진목록.xlsx"
df = pd.read_excel(file_path)

# =============================
# 데이터 전처리
# =============================
df['발생시각'] = pd.to_datetime(df['발생시각'], errors='coerce')
df['연도'] = df['발생시각'].dt.year

# 규모 구간을 구분
df['규모_구간'] = pd.cut(
    df['규모'],
    bins=[0,2,3,4,5,6,10],
    labels=["0~2","2~3","3~4","4~5","5~6","6 이상"]
)

# =============================
# 페이지 타이틀
# =============================
st.title("📊 국내 지진 발생 분석 Dashboard (최근 10년)")

st.markdown("데이터 필터링과 지도로 확인할 수 있는 종합 지진 데이터 분석 도구입니다.")
st.markdown("---")

# =============================
# 🔍 사이드바 필터
# =============================
st.sidebar.header("🔍 필터")

지역_목록 = ["전체"] + sorted(df['지역'].dropna().unique().tolist())
선택_지역 = st.sidebar.selectbox("지역 선택", 지역_목록)

규모_선택 = st.sidebar.slider("규모 범위 선택", float(df['규모'].min()), float(df['규모'].max()), (2.0, 5.0))

연도_선택 = st.sidebar.slider("연도 범위 선택", int(df['연도'].min()), int(df['연도'].max()), (int(df['연도'].min()), int(df['연도'].max())))

# =============================
# 필터 적용
# =============================
filtered_df = df.copy()

# 지역 필터
if 선택_지역 != "전체":
    filtered_df = filtered_df[filtered_df['지역'] == 선택_지역]

# 규모 필터
filtered_df = filtered_df[(filtered_df['규모'] >= 규모_선택[0]) & (filtered_df['규모'] <= 규모_선택[1])]

# 연도 필터
filtered_df = filtered_df[(filtered_df['연도'] >= 연도_선택[0]) & (filtered_df['연도'] <= 연도_선택[1])]

# =============================
# 1️⃣ 지도 시각화
# =============================
st.header("1️⃣ 지진 발생 위치 지도")

if {'위도','경도'}.issubset(filtered_df.columns):
    st.map(filtered_df[['위도','경도']].dropna())
else:
    st.warning("⚠️ 지도 시각화를 위해 '위도', '경도' 컬럼이 필요합니다.")

st.markdown("---")

# =============================
# 2️⃣ 지역별 지진 발생 횟수
# =============================
st.header("2️⃣ 지역별 지진 발생 횟수")

region_count = filtered_df['지역'].value_counts().reset_index()
region_count.columns = ['지역', '발생횟수']

chart_region = alt.Chart(region_count).mark_bar().encode(
    x='지역:N',
    y='발생횟수:Q',
    tooltip=['지역', '발생횟수']
).properties(width=800, height=400)

st.altair_chart(chart_region, use_container_width=True)
st.markdown("---")

# =============================
# 3️⃣ 규모 구간별 연도별 지진 발생 추이
# =============================
st.header("3️⃣ 규모 구간별 지진 발생 변화")

mag_year = filtered_df.groupby(['연도', '규모_구간']).size().reset_index(name='발생횟수')

chart_mag = alt.Chart(mag_year).mark_line(point=True).encode(
    x='연도:O',
    y='발생횟수:Q',
    color='규모_구간:N',
    tooltip=['연도', '규모_구간', '발생횟수']
).properties(width=800, height=450)

st.altair_chart(chart_mag, use_container_width=True)
st.markdown("---")

# =============================
# 4️⃣ 연도별 지진 발생 총량
# =============================
st.header("4️⃣ 연도별 지진 총 발생 추이")

year_count = filtered_df['연도'].value_counts().sort_index().reset_index()
year_count.columns = ['연도', '발생횟수']

chart_year = alt.Chart(year_count).mark_area().encode(
    x='연도:O',
    y='발생횟수:Q',
    tooltip=['연도', '발생횟수']
).properties(width=800, height=400)

st.altair_chart(chart_year, use_container_width=True)

st.markdown("---")

# =============================
# 📄 원본 데이터 보기
# =============================
with st.expander("📄 필터 적용된 데이터 보기"):
    st.dataframe(filtered_df)
