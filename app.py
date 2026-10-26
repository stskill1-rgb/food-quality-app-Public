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
  # 주의: 실제 공공데이터포털의 API 엔드포인트 URL로 변경해야 합니다.
  url = "http://apis.data.go.kr/1471000/FoodCertiService01/getFoodCertiList01"

  params = {
      "serviceKey": api_key,
      "type": "json",
      "numOfRows": numOfRows,
      "pageNo": pageNo,
  }

  try:
    response = requests.get(url, params=params)
    # 데이터 구조에 맞게 파싱 (JSON 기준 예시)
    res_json = response.json()
    items = (
        res_json.get("body", {}).get("items", {}).get("item", [])
    )  # API 구조에 따라 수정 필요
    return pd.DataFrame(items)
  except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    return pd.DataFrame()


# API 키 가져오기 (Streamlit Secrets 활용)
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

    # 검색 및 필터 기능
    search_query = st.text_input(
        "🔍 제품명 또는 업체명 검색", placeholder="검색어를 입력하세요"
    )

    if search_query:
      # 컬럼명은 실제 API 응답 필드명에 맞게 수정 필요
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

    # 데이터 테이블 출력
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
    st.warning("조회된 데이터가 없거나 API 응답을 확인해주세요.")
else:
  st.info("시작하려면 API 인증키를 입력하거나 설정해주세요.")
