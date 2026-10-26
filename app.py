import math
import pandas as pd
import requests
import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="어린이기호식품 품질인증 대장", page_icon="🍏", layout="wide"
)

st.title("🍏 어린이기호식품 품질인증 대장 조회 시스템 (전체 데이터 연동)")
st.markdown(
    "식품안전나라 오픈 API에서 전체 인증 데이터를 누락 없이 실시간으로 불러옵니다."
)


# 전체 데이터를 페이지별로 모두 끌어오는 함수
@st.cache_data
def fetch_all_food_data(api_key):
  all_rows = []
  display_count = 100  # 한 번에 요청할 단위 수
  start_idx = 1
  end_idx = display_count
  total_count = 0

  # 1. 먼저 첫 페이지를 호출하여 전체 데이터 건수(total_count) 확인
  first_url = (
      f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/I0080/json/{start_idx}/{end_idx}"
  )
  try:
    res = requests.get(first_url).json()
    service_data = res.get("I0080", {})
    total_count = int(service_data.get("total_count", 0))
    rows = service_data.get("row", [])
    all_rows.extend(rows)
  except Exception as e:
    st.error(f"초기 데이터 통신 중 오류 발생: {e}")
    return pd.DataFrame(), 0

  # 2. 전체 데이터가 100건보다 많다면 반복문으로 나머지 데이터 모두 가져오기
  if total_count > display_count:
    total_pages = math.ceil(total_count / display_count)

    for page in range(2, total_pages + 1):
      start_idx = ((page - 1) * display_count) + 1
      end_idx = page * display_count
      url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/I0080/json/{start_idx}/{end_idx}"

      try:
        response = requests.get(url)
        data = response.json().get("I0080", {}).get("row", [])
        if data:
          all_rows.extend(data)
      except:
        break

  df = pd.DataFrame(all_rows)

  if not df.empty:
    column_mapping = {
        "PRDLST_NM": "제품명",
        "BSSH_NM": "업소명",
        "LCNS_NO": "인허가번호",
        "PRDLST_REPORT_NO": "품목보고번호",
        "APPN_BGN_DT": "인증일자",
        "APPN_END_DT": "만료일자",
        "CN_WT": "제품용량",
        "PRDLST_CD_NM": "식품유형",
        "CHILD_FFQ_CRTFC_NO": "인증번호",
        "CHILD_FAVOR_FOOD_TYPE_NM": "어린이기호식품유형",
    }
    df = df.rename(columns=column_mapping)

  return df, total_count


# Streamlit Secrets에 등록된 API 키 불러오기
if "API_KEY" in st.secrets:
  api_key = st.secrets["API_KEY"]
else:
  api_key = st.text_input("공공데이터 API 인증키를 입력하세요", type="password")

if api_key:
  with st.spinner("서버에서 전체 데이터를 완전히 불러오는 중입니다..."):
    df, total_count = fetch_all_food_data(api_key)

  if not df.empty:
    st.success(
        f"🎉 총 {total_count}건의 전체 데이터를 빠짐없이 성공적으로"
        f" 불러왔습니다! (현재 수집된 데이터: {len(df)}건)"
    )

    # 검색 및 필터 기능
    search_query = st.text_input(
        "🔍 제품명 또는 업체명 검색",
        placeholder="찾으시는 회사명이나 제품명을 입력하세요",
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
        label="📥 전체 대장 데이터를 CSV로 다운로드",
        data=csv,
        file_name="food_quality_cert_all_list.csv",
        mime="text/csv",
    )
  else:
    st.warning("조회된 데이터가 없습니다.")
else:
  st.info("시작하려면 API 인증키를 설정해주세요.")
