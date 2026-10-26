import pandas as pd
import requests
import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="어린이기호식품 품질인증 대장", page_icon="🍏", layout="wide"
)

st.title("🍏 어린이기호식품 품질인증 대장 조회 시스템 (디버깅 모드)")
st.markdown("API 응답 상태를 확인하는 진단용 화면입니다.")

# Streamlit Secrets에서 API 키 불러오기
if "API_KEY" in st.secrets:
  api_key = st.secrets["API_KEY"]
else:
  api_key = st.text_input("공공데이터 API 인증키를 입력하세요", type="password")

if api_key:
  url = "http://apis.data.go.kr/1471000/FoodCertiService01/getFoodCertiList01"

  params = {"serviceKey": api_key, "numOfRows": "10", "pageNo": "1"}

  try:
    with st.spinner("API 서버와 통신 중..."):
      response = requests.get(url, params=params)

    st.subheader("🔍 API 서버 응답 상태 및 원문 진단")
    st.write(f"**HTTP 상태 코드:** {response.status_code}")

    # 서버가 반환한 원본 텍스트를 화면에 그대로 출력
    with st.expander("API 서버 원본 응답 보기 (클릭하여 펼치기)"):
      st.text(response.text)

    # 데이터 파싱 시도
    if "<item>" in response.text:
      import xml.etree.ElementTree as ET

      root = ET.fromstring(response.text.strip())
      items = []
      for item_elem in root.findall(".//item"):
        item_dict = {}
        for child in item_elem:
          item_dict[child.tag] = child.text
        items.append(item_dict)

      df = pd.DataFrame(items)
      if not df.empty:
        st.success(f"데이터 {len(df)}건을 성공적으로 불러왔습니다!")
        st.dataframe(df, use_container_width=True)
      else:
        st.warning(
            "XML 구조 내에 <item> 데이터가 없습니다. 원본 응답을 확인해주세요."
        )
    else:
      st.error(
          "API가 정상적인 데이터 구조를 반환하지 않았습니다. 위의 '원본 응답'을"
          " 확인해주세요."
      )

  except Exception as e:
    st.error(f"통신 중 에러 발생: {e}")
else:
    st.info("인증키를 설정해주세요.")
