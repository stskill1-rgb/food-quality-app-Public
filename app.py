import xml.etree.ElementTree as ET
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


# API 데이터 호출 함수 (XML 및 JSON 공용 처리)
@st.cache_data
def fetch_food_data(api_key, numOfRows=100, pageNo=1):
  url = "http://apis.data.go.kr/1471000/FoodCertiService01/getFoodCertiList01"

  params = {
      "serviceKey": api_key,
      "numOfRows": numOfRows,
      "pageNo": pageNo,
  }

  try:
    response = requests.get(url, params=params)
    text = response.text.strip()

    # 응답이 XML 형식인 경우 (공공데이터포털 기본값)
    if text.startswith("<"):
      root = ET.fromstring(text)
      items = []
      # XML 내부의 <item> 태그들을 찾아 딕셔너리 형태로 변환
      for item_elem in root.findall(".//item"):
        item_dict = {}
        for child in item_elem:
          item_dict[child.tag] = child.text
        items.append(item_dict)
      return pd.DataFrame(items)

    else:
      # JSON 형식인 경우
      res_json = response.json()
      items = res_json.get("body", {}).get("items", {}).get("item", [])
      if isinstance(items, list):
        return pd.DataFrame(items)
      return pd.DataFrame()

  except Exception as e:
    st.error(f"데이터를 처리하는 중 오류가 발생했습니다: {e}")
    return pd.DataFrame()


# Streamlit Secrets에 등록된 API 키 불러오기
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
    st.warning(
        "조회된 데이터가 없습니다. 인증키가 올바른지 또는 서비스 승인 상태를"
        " 확인해주세요."
    )
else:
  st.info("시작하려면 API 인증키를 설정해주세요.")
