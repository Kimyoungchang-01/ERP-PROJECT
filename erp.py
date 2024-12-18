import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rc
import pyodbc  # SQL Server 연결을 위한 라이브러리

# 한글 폰트 설정 (Windows: Malgun Gothic, Mac: AppleGothic)
rc('font', family='Malgun Gothic')
plt.rcParams['axes.unicode_minus'] = False

# 데이터 불러오기 함수 (SSMS 연동)
@st.cache_data
def load_data_from_sql():
    # SQL Server 연결 설정
    conn =  pyodbc.connect(
        driver='{ODBC Driver 17 for SQL Server}',  # 설치된 ODBC 드라이버 버전
        server='DESKTOP-COFOF9U\DUZON_CORE',  # 예: 'localhost' 또는 '192.168.x.x'
        database='DZCORECUBE',  # 사용하려는 데이터베이스 이름
        uid='CORECUBE',  # SQL Server 로그인 사용자명
        pwd='ejwhs123$'  # 로그인 비밀번호
    )

    # SQL 쿼리 작성
    query = """
    SELECT ITEM_CD, QCBAD_QT, QCRCV_QT, DOC_DT
    FROM dbo.LQC_INSP
    """
    
    # SQL 쿼리 실행 후 데이터 가져오기
    data = pd.read_sql(query, conn)  # SQL 쿼리와 연결 객체 전달

    # 불량률 계산
    data['BAD_RATE'] = data['QCBAD_QT'] / (data['QCRCV_QT'] + 1e-5) * 100  # 불량률 계산
    data['DOC_DT'] = pd.to_datetime(data['DOC_DT'], format='%Y%m%d')  # 날짜 변환
    
    return data

# 데이터 로드
data = load_data_from_sql()

# Streamlit 앱 시작
st.title("품질 검사 데이터 시각화")

# 날짜별 품질 검사 결과 시각화
st.header("연도별 품질 검사 결과")
date_inspection = data.groupby('DOC_DT')[['QCRCV_QT', 'QCBAD_QT']].sum()

fig2, ax2 = plt.subplots(figsize=(12, 6))
date_inspection.plot(ax=ax2)
ax2.set_title("날짜별 품질 검사 결과")
ax2.set_ylabel("수량")
ax2.set_xlabel("날짜")
st.pyplot(fig2)

# 사용자 입력 연도
st.header("연도별 품목별 불량 수 분석")

# 연도 입력 위젯
selected_year = st.number_input("연도를 입력하세요 (예: 2023)", min_value=2000, max_value=2100, step=1, value=2023)

# 선택한 연도로 데이터 필터링
year_data = data[data['DOC_DT'].dt.year == selected_year]

col1, col2 = st.columns(2)

if not year_data.empty:
    with col1:
        # 품목별 불량 수 계산
        item_bad_count = year_data.groupby('ITEM_CD')['QCBAD_QT'].sum().sort_values(ascending=False)

        # 상위 10개 품목 시각화
        st.subheader(f"{selected_year}년 품목별 불량 수 (상위 10개)")
        fig, ax = plt.subplots(figsize=(10, 6))
        item_bad_count.head(10).plot(kind='bar', ax=ax, color='salmon')
        ax.set_title(f"{selected_year}년 품목별 불량 수 (상위 10개)")
        ax.set_ylabel("불량 수량")
        ax.set_xlabel("품목 코드")
        st.pyplot(fig)

    with col2:
        # 전체 품목별 불량 수 테이블 표시
        st.subheader(f"{selected_year}년 전체 품목별 불량 수")
        st.dataframe(item_bad_count.reset_index().rename(columns={'ITEM_CD': '품목 코드', 'QCBAD_QT': '불량 수량'}))
else:
    st.warning(f"{selected_year}년 데이터가 없습니다. 다른 연도를 입력해주세요.")

# 사용자 입력 연도
st.header("연도별 데이터 필터링 및 시각화")

# 입력 위젯
selected_year = st.number_input("연도를 입력하세요 (예: 2023)", min_value=2000, max_value=2100, step=1, value=2023, key="unique_year_key")

# 선택한 연도로 데이터 필터링
year_data = data[data['DOC_DT'].dt.year == selected_year]

if not year_data.empty:
    # 연-월로 그룹화
    year_data['YearMonth'] = year_data['DOC_DT'].dt.to_period('M')
    month_inspection = year_data.groupby('YearMonth')[['QCRCV_QT', 'QCBAD_QT']].sum()

    # 월별 시각화
    st.subheader(f"{selected_year}년 월별 품질 검사 결과")
    fig, ax = plt.subplots(figsize=(10, 6))
    month_inspection.plot(ax=ax)
    ax.set_title(f"{selected_year}년 월별 품질 검사 결과")
    ax.set_ylabel("수량")
    ax.set_xlabel("월")
    ax.grid(True)
    st.pyplot(fig)
else:
    st.warning(f"{selected_year}년 데이터가 없습니다. 다른 연도를 입력해주세요.")


# 사용자 입력 연도
st.header("연도별 관리도 시각화")

# 연도 입력 위젯
selected_year = st.number_input("연도를 입력하세요 (예: 2023)", min_value=2000, max_value=2100, step=1, value=2023, key="control_chart")

# 선택한 연도의 데이터 필터링
year_data = data[data['DOC_DT'].dt.year == selected_year]

if not year_data.empty:
    # 날짜별 평균 계산
    year_data = year_data.groupby('DOC_DT')['QCBAD_QT'].mean().reset_index()
    mean = year_data['QCBAD_QT'].mean()  # 전체 평균
    sigma = year_data['QCBAD_QT'].std()  # 표준편차

    # 관리 한계선 설정 (UCL, LCL)
    UCL = mean + 3 * sigma  # 상한
    LCL = mean - 3 * sigma  # 하한

    # 관리도 그리기
    st.subheader(f"{selected_year}년 관리도 (Control Chart)")
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(year_data['DOC_DT'], year_data['QCBAD_QT'], marker='o', linestyle='-', label='불량 수량 평균')
    ax.axhline(mean, color='green', linestyle='--', label='평균')
    ax.axhline(UCL, color='red', linestyle='--', label='UCL (+3σ)')
    ax.axhline(LCL, color='red', linestyle='--', label='LCL (-3σ)')

    ax.set_title(f"{selected_year}년 관리도")
    ax.set_ylabel("평균 불량 수량")
    ax.set_xlabel("날짜")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)
else:
    st.warning(f"{selected_year}년 데이터가 없습니다. 다른 연도를 입력해주세요.")

# 데이터 다운로드
st.header("데이터 다운로드")
csv_data = data.to_csv(index=False).encode('utf-8')
st.download_button(
    label="데이터 다운로드 (CSV)",
    data=csv_data,
    file_name='inspection_data.csv',
    mime='text/csv'
)

