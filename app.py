import pandas as pd
import requests
import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="어린이기호식품 품질인증 대장", page_icon="🍏", layout="wide"
)

st.title("🍏 어린이기호식품 품질인증 대장 조회 시스템")
st.markdown(
    "공공데이터포털 오픈 API를 활용하여 실시간 어린이기호식품 품질인증 현황을 관리하는"
    " 대장입니다."
)


# API 데이터 호출 함수
@st.cache_data
def fetch_food_data(api_key, numOfRows=100, pageNo=1):
  # 식품안전정보원 어린이기호식품 품질인증 현황 및 재심사 현황 API 표준 엔드포인트
  url = "http://apis.data.go.kr/1471000/FoodCertiService01/getFoodCertiList01"

  params = {
      "serviceKey": api_key,
      "type": "json",
      "numOfRows": numOfRows,
      "pageNo": pageNo,
  }

  try:
    response = requests.get(url, params=params)
    res_json = response.json()

    # 공공데이터 표준 응답 구조에서 데이터 추출
    items = (
        res_json.get("body", {}).get("items", {}).get("item", [])
    )  # API 규격에 따른 파싱 경로
    if not items:
      # 만약 구조가 다르거나 데이터가 리스트로 바로 올 경우를 대비한 예외 처리
      if isinstance(res_json, list):
        return pd.DataFrame(res_json)
      return pd.DataFrame()

    return pd.DataFrame(items)
  except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    return pd.DataFrame()


# Streamlit Secrets에 등록된 API 키 자동 불러오기
if "API_KEY" in st.secrets:
  api_key = st.secrets["API_KEY"]
else:
  api_key = st.text_input("공공데이터 API 인증키를 입력하세요", type="password")

if api_key:
  with st.spinner("데이터를 실시간으로 불러오는 중입니다..."):
    df = fetch_food_data(api_key)

  if not df.empty:
    st.success(
        f"총 {len(df)}건의 데이터를 성공적으로 불러왔습니다! (실시간 데이터 기준)"
    )

    # 검색 및 필터 기능 (업소명, 제품명 등)
    search_query = st.text_input(
        "🔍 제품명 또는 업체명 검색", placeholder="검색어를 입력하세요"
    )

    if search_query:
      filtered_df = df[
          df.apply(
              lambda row: row.astype(str)
              .str.contains(search_query, case=False)
              .any(),
              axis=1,
          )
      ]
    else:
      filtered_df = df

    # 데이터 테이블 출력 (사용자가 보기 편하게 전체 폭으로 출력)
    st.dataframe(filtered_df, use_container_width=True)

    # 데이터 다운로드 버튼
    csv = filtered_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 대장 데이터를 CSV로 다운로드",
        data=csv,
        file_name="food_quality_cert_list.csv",
        mime="text/csv",
    )
  else:
    st.warning(
        "조회된 데이터가 없습니다. 인증키가 올바른지 또는 서비스 승인 상태를"
        " 확인해주세요."
    )
else:
  st.info("시작하려면 API 인증키를 설정해주세요.")
