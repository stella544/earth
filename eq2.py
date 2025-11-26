import streamlit as st
import pandas as pd
import altair as alt
import os

st.set_page_config(page_title="국내 지진 분석", layout="wide")
st.title("📊 국내 지진 발생 분석 Dashboard")

file_name = "최근10년간 국내지진목록.xlsx"

if not os.path.exists(file_name):
    st.error(f"❌ 동일 폴더에 `{file_name}` 파일이 없습니다.")
    st.stop()

########################################
# 🔍 1) 엑셀의 실제 헤더가 있는 행 자동 감지
########################################
raw = pd.read_excel(file_name, header=None)

header_row = None

for i in range(5):  # 첫 5행 정도만 검사
    row = raw.iloc[i]
    # 숫자가 하나라도 있으면 헤더로 볼 수 있음
    has_number = any(pd.to_numeric(row, errors='coerce').notnull())
    if has_number:
        # 바로 위 행이 컬럼명일 가능성이 높음
        header_row = i - 1 if i > 0 else i
        break

if header_row is None:
    st.error("⚠ 헤더 행을 자동으로 찾지 못했습니다.")
    st.stop()

df = pd.read_excel(file_name, header=header_row)

########################################
# 🔍 2) 컬럼명 정리 (양쪽 공백 제거)
########################################
df.columns = df.columns.map(lambda x: str(x).strip())

########################################
# 🔍 3) 컬럼 자동 감지
########################################
# 한국지진 목록 표의 일반적인 컬럼 후보
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

########################################
# 🔍 4) 사용자 선택 (자동 감지된 값이 기본값)
########################################
st.sidebar.subheader("📌 자동으로 감지된 컬럼")
st.sidebar.write(df.columns.tolist())

st.sidebar.subheader("📌 컬럼 선택")

col_time = st.sidebar.selectbox("발생시각 컬럼", df.columns, 
                                index=df.columns.get_loc(col_time_auto) if col_time_auto in df.columns else 0)

col_mag = st.sidebar.selectbox("규모 컬럼", df.columns,
                               index=df.columns.get_loc(col_mag_auto) if col_mag_auto in df.columns else 0)

col_region = st.sidebar.selectbox("지역 컬럼", df.columns,
                                  index=df.columns.get_loc(col_region_auto) if col_region_auto in df.columns else 0)

col_lat = st.sidebar.selectbox("위도 컬럼", ["없음"] + df.columns.tolist(),
                               index=(df.columns.get_loc(col_lat_auto) + 1) if col_lat_auto in df.columns else 0)

col_lon = st.sidebar.selectbox("경도 컬럼", ["없음"] + df.columns.tolist(),
                               index=(df.columns.get_loc(col_lon_auto) + 1) if col_lon_auto in df.columns else 0)

########################################
# 🔍 5) 전처리
########################################
df['발생시각_변환'] = pd.to_datetime(df[col_time], errors='coerce')
df['연도'] = df['발생시각_변환'].dt.year

# 👉 규모는 반드시 숫자로 변환
df[col_mag] = pd.to_numeric(df[col_mag], errors='coerce')

df['규모_구간'] = pd.cut(
    df[col_mag],
    bins=[0, 2, 3, 4, 5, 6, 10],
    labels=["0~2", "2~3", "3~4", "4~5", "5~6", "6 이상"]
)

########################################
# 🔍 이후 코드는 기존대로 (지도, 그래프 등)
########################################
st.success("엑셀 헤더 자동 감지 성공 ✓ 데이터 정상 로딩 완료!")

st.write("### 데이터 미리보기")
st.dataframe(df.head())
