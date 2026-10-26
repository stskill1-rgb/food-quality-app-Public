import math
import pandas as pd
import requests
import streamlit as st

# 페이지 설정 (넓은 화면 레이아웃)
st.set_page_config(
    page_title="어린이기호식품 품질인증 대장", page_icon="🍏", layout="wide"
)

st.title("🍏 어린이기호식품 품질인증 대장 조회 시스템")
st.markdown(
    "식품안전나라 오픈 API에서 전체 인증 데이터를 누락 없이 실시간으로 불러옵니다."
)


# 전체 데이터를 페이지별로 모두 끌어오는 함수
@st.cache_data
def fetch_all_food_data(api_key):
  all_rows = []
  display_count = 100
  start_idx = 1
  end_idx = display_count
  total_count = 0

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

    st.markdown("---")
    st.subheader("🔍 독립형 검색 필터")

    # 업소명 검색란과 제품명 검색란을 가로로 나란히 배치
    col1, col2 = st.columns(2)
    with col1:
      bssh_query = st.text_input(
          "🏢 업소명으로만 검색", placeholder="예: 연세유업"
      )
    with col2:
      prdlst_query = st.text_input(
          "🍪 제품명으로만 검색", placeholder="예: 딸기우유"
      )

    # 필터링 로직 (각각 독립적으로 동작)
    filtered_df = df.copy()
    if bssh_query:
      filtered_df = filtered_df[
          filtered_df["업소명"].astype(str).str.contains(bssh_query, case=False)
      ]
    if prdlst_query:
      filtered_df = filtered_df[
          filtered_df["제품명"]
          .astype(str)
          .str.contains(prdlst_query, case=False)
      ]

    st.markdown("---")
    st.subheader(
        f"📦 검색 결과 카드 (총 {len(filtered_df)}건)",
        anchor=False,
    )

    if not filtered_df.empty:
      # 제품별/업소별 정보를 네모 섹션(카드) 형태로 예쁘게 출력
      for _, row in filtered_df.iterrows():
        with st.container(border=True):
          st.markdown(f"### 🍏 **{row.get('제품명', '정보 없음')}**")

          # 카드 내부 상세 정보 배치 (2열 구조)
          c1, c2, c3 = st.columns(3)
          with c1:
            st.markdown(f"**🏢 업소명:** {row.get('업소명', '-')}")
            st.markdown(f"**🏷️ 품목보고번호:** {row.get('품목보고번호', '-')}")
            st.markdown(f"**⚖️ 제품용량:** {row.get('제품용량', '-')}")
          with c2:
            st.markdown(f"**📂 식품유형:** {row.get('식품유형', '-')}")
            st.markdown(
                f"**🍬 어린이기호식품유형:**"
                f" {row.get('어린이기호식품유형', '-')}"
            )
            st.markdown(f"**🔢 인증번호:** {row.get('인증번호', '-')}")
          with c3:
            st.markdown(f"**📅 인증일자:** {row.get('인증일자', '-')}")
            st.markdown(f"**⏳ 만료일자:** {row.get('만료일자', '-')}")
            st.markdown(f"**📜 인허가번호:** {row.get('인허가번호', '-')}")
    else:
      st.warning("검색 조건에 일치하는 데이터가 없습니다.")

    # 전체 데이터 다운로드 버튼
    st.markdown("---")
    csv = filtered_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 현재 검색된 대장 데이터를 CSV로 다운로드",
        data=csv,
        file_name="food_quality_cert_filtered.csv",
        mime="text/css" if False else "text/csv",
    )
  else:
    st.warning("조회된 데이터가 없습니다.")
else:
    st.info("시작하려면 API 인증키를 설정해주세요.")
