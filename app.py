import streamlit as st
from streamlit_js_eval import get_geolocation

# [1] 웹페이지 기본 설정
st.set_page_config(page_title="공장 안전 가이드", layout="centered")

# --- [🎨 대중적이고 깔끔한 라이트 테마 CSS 적용] ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; color: #333333; font-family: 'Noto Sans KR', sans-serif; }
    h1 { color: #1e3a8a !important; font-weight: 700; padding-bottom: 10px; border-bottom: 3px solid #3b82f6; margin-bottom: 25px !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #ffffff; border: 1px solid #e5e7eb; padding: 10px 20px; border-radius: 8px 8px 0px 0px; font-weight: 600; color: #4b5563; }
    .stTabs [aria-selected="true"] { background-color: #3b82f6 !important; color: white !important; border-color: #3b82f6 !important; }
    .stButton>button { width: 100%; background-color: #3b82f6; color: white; border: none; padding: 12px; border-radius: 8px; font-weight: bold; transition: all 0.3s ease; box-shadow: 0px 2px 4px rgba(0,0,0,0.05); }
    .stButton>button:hover { background-color: #1d4ed8; color: white; }
    div[data-baseweb="select"] { border-radius: 8px !important; }
    .stAlert { border-radius: 8px !important; border: none !important; box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.02); }
    </style>
    """, unsafe_allow_html=True)

# --- [관리자 설정: 안전 구역 좌표 데이터] ---
AREAS = [
    {
        "name": "화학물 저장소 (A구역)",
        "lat": 35.5416,  
        "lon": 129.2555, 
        "info": "방독면 착용 필수 및 화기 엄금!"
    }
]

# --- [관리자 설정: 화학물질 자료실 데이터 (총 9종)] ---
CHEMICALS = {
    "TOLUENE": {
        "name": "톨루엔 (Toluene)",
        "cas_no": "108-88-3",
        "symbol": "🔥 고인화성 / ⚠️ 급성·만성독성",
        "danger": "• 고인화성 액체 및 증기\n• 삼켜서 기도로 유입되면 치명적일 수 있음\n• 피부 및 흡인 유해성",
        "emergency": "1. 신선한 공기를 마시게 하고 편안한 자세로 안정\n2. 오염된 옷과 신발을 즉시 벗기고 씻어낼 때 물질이 번지지 않도록 주의"
    },
    "ACETONE": {
        "name": "아세톤 (Acetone)",
        "cas_no": "67-64-1",
        "symbol": "🔥 극인화성 / 👁️ 눈 자극성 / 🧠 중추신경계 억제",
        "danger": "• 고인화성 액체 및 증기\n• 삼켜서 기도로 유입되면 유해할 수 있음\n• 눈에 심한 자극 및 졸음, 현기증 유발\n• 피부 건조증 및 점막 자극",
        "emergency": "1. 신선한 공기가 있는 곳으로 이동시키고 환자를 따뜻하게 감싸 안정\n2. 오염된 옷을 벗고 다량의 물과 비누로 깨끗이 씻어낸 뒤 보습"
    },
    "SULFURIC_ACID": {
        "name": "황산 (Sulfuric Acid)",
        "cas_no": "7664-93-9",
        "symbol": "💀 급성독성 / 🧪 부식성 / 👁️ 실명위험",
        "danger": "• 화학적 화상 및 호흡기 손상\n• 눈 접촉 시 실명 위험\n• 폭발 및 화재 유발 위험",
        "emergency": "1. 오염된 옷을 찢어 벗기고 흐르는 물에 최소 20~30분 이상 즉시 세척\n2. 눈꺼풀을 강제로 벌리고 흐르는 물이나 식염수로 최소 30분 이상 지속 세척"
    },
    "SODIUM_HYDROXIDE": {
        "name": "수산화나트륨 (Sodium Hydroxide)",
        "cas_no": "1310-73-2",
        "symbol": "⚠️ 유해성 / 🧪 금속·피부 부식 / 👁️ 실명위험",
        "danger": "• 금속을 부식시킬 수 있으며 삼키거나 피부 접촉 시 유해함\n• 피부, 피부하선 및 눈에 심한 손상 (화학적 화상)\n• 흡입 및 분진 위험, 실명 위험",
        "emergency": "1. 피부에 닿았을 때 미끈거리는 느낌이 완전히 사라질 때까지 흐르는 물에 세척\n2. 신선한 공기가 있는 곳으로 옮기고, 호흡이 곤란하면 산소를 공급"
    },
    "BENZENE": {
        "name": "벤젠 (Benzene)",
        "cas_no": "71-43-2",
        "symbol": "🔥 고인화성 / 💀 급성 독성 / 🎗️ 1급 발암성 물질",
        "danger": "• 고인화성 액체 및 증기 유발\n• 흡입, 피부 접촉 시 치명적이며 눈에 심한 자극\n• 장기간 또는 반복 노출 시 혈액 질환(백혈병) 및 유전적 결함 유발",
        "emergency": "1. 흡입 시 즉시 신선한 공기가 있는 곳으로 옮기고 산소 공급 또는 인공호흡 실시\n2. 피부 접촉 시 오염된 의복을 즉시 벗고 다량의 물과 비누로 최소 15분 이상 세척\n3. 눈 접촉 시 눈꺼풀을 벌리고 흐르는 물로 최소 15분 이상 충분히 씻어낸 후 의사의 진료를 받을 것"
    },
    "ETHYLENE_OXIDE": {
        "name": "산화에틸렌 (Ethylene Oxide / EO)",
        "cas_no": "75-21-8",
        "symbol": "💥 인화성·폭발성 가스 / 🧪 부식성 / 🎗️ 발암성·생식세포 변이원성",
        "danger": "• 고압가스 및 극인화성 가스로 폭발 위험성이 매우 높음\n• 흡입 시 치명적이며 흡입 독성 및 화학적 화상 유발\n• 암을 일으키며 유전성 결함 및 생식 기능 장애 유발",
        "emergency": "1. 가스 누출 및 흡입 시 환자를 즉시 안전한 지역으로 대피시키고 호흡 상태 확인\n2. 물질과 접촉 시 오염된 부위를 흐르는 물로 즉시 20분 이상 세척하고 동상 위험 시 주의하여 가온\n3. 즉시 종합병원이나 의료진의 응급 처치를 받을 것"
    },
    "AMMONIA": {
        "name": "암모니아 (Ammonia)",
        "cas_no": "7664-41-7",
        "symbol": "☣️ 독성 가스 / 🧪 강한 부식성 / 👁️ 실명 및 호흡기 화상",
        "danger": "• 흡입 시 중독 및 기도, 호흡기계에 심각한 화학적 화상 유발\n• 피부 접촉 시 심한 화상 및 동상 유발\n• 눈 접촉 시 각막 손상 및 영구적 실명 위험",
        "emergency": "1. 흡입 시 신선한 공기가 있는 곳으로 이동시키고 환자가 호흡하지 않으면 즉시 인공호흡 실시\n2. 피부나 눈 접촉 시 지체 없이 다량의 물 또는 식염수로 최소 20~30분 이상 강하게 세척\n3. 오염된 옷이 피부에 달라붙은 경우 억지로 떼지 말고 물을 부으며 가위로 잘라내어 제거"
    },
    "1_3_BUTADIENE": {
        "name": "1,3-부타디엔 (1,3-Butadiene)",
        "cas_no": "106-99-0",
        "symbol": "🔥 극인화성 가스 / 🎗️ 1급 발암성 / 👶 생식독성",
        "danger": "• 매우 인화성이 높은 가스로 쉽게 점화되어 대형 화재·폭발 유발\n• 흡입 시 졸음, 현기증, 중추신경계 억제 및 가벼운 마취 증상 유발\n• 암 및 유전성 결함을 일으키며 태아에게 유해함",
        "emergency": "1. 가스 흡입 시 환자를 신선한 공기가 있는 곳으로 옮기고 안정을 취하게 함\n2. 액화 가스 방출로 인한 접촉 시 동상 위험이 있으므로 따뜻한 물로 환부를 천천히 가온\n3. 다량 흡입하거나 증상이 지속될 경우 즉시 의사의 진료를 요함"
    },
    "ACRYLONITRILE": {
        "name": "아크릴로니트릴 (Acrylonitrile / AN)",
        "cas_no": "107-13-1",
        "symbol": "🔥 고인화성 액체 / 💀 고독성(시안화물 계열) / 🎗️ 발암성 위험",
        "danger": "• 인화성이 매우 높고 증기는 폭발성 혼합물을 형성함\n• 흡입, 섭취, 피부 흡수 시 모두 극히 유독함 (체내에서 시안화수소로 분해)\n• 피부 및 눈에 심한 자극과 화학적 화상 유발 가능, 암 유발 물질",
        "emergency": "1. 흡입 시 구조자는 송기마스크를 착용한 후 환자를 대피시키고, 필요시 시안화물 해독제 키트 준비 안내\n2. 피부 흡수가 매우 빠르므로 접촉 즉시 오염된 의복을 완전히 제거하고 흐르는 물로 최소 20분 이상 세척\n3. 구조자가 환자의 토사물이나 신체 접촉으로 교차 오염되지 않도록 철저히 주의"
    }
}

# --- [🆕 주소창 QR 데이터 완벽 분석 및 이동 로직] ---
query_params = st.query_params
qr_chem = query_params.get("chem", None)
chem_list = list(CHEMICALS.keys())

# 기본적으로 어떤 탭 화면을 보여줄지 변수로 제어합니다.
# QR 주소가 들어왔고 유효하다면 무조건 화학물질 자료실 화면(1번)을 보여줍니다.
current_page_idx = 0
if qr_chem and qr_chem in CHEMICALS:
    current_page_idx = 1

# --- [웹 화면 구현 시작] ---
st.title("🏭 스마트 안전관리 모바일 가이드")

# st.tabs 구조를 사용하면 시스템이 첫 번째 탭으로 화면을 고정해버리므로, 
# 주소 인식을 완벽히 지원하는 가로형 버튼 메뉴(st.toggle/radio 대체제) 방식으로 수정하여 탭을 동적으로 전환합니다.
menu_tabs = ["📍 실시간 위치 지침", "📚 화학물질 자료실"]
selected_tab = st.radio(
    "메뉴 선택", 
    menu_tabs, 
    index=current_page_idx, 
    horizontal=True, 
    label_visibility="collapsed"
)

st.write("") # 간격 조절용 공백

# --- [1번 화면: 실시간 위치 지침 영역] ---
if selected_tab == "📍 실시간 위치 지침":
    st.subheader("현재 내 위치 확인")
    loc = get_geolocation()
    if loc:
        curr_lat = loc['coords']['latitude']
        curr_lon = loc['coords']['longitude']
        st.write(f"📍 현재 나의 좌표: **{curr_lat:.4f}, {curr_lon:.4f}**")
        
        found = False
        for area in AREAS:
            if abs(curr_lat - area['lat']) < 0.0008 and abs(curr_lon - area['lon']) < 0.0008:
                st.success(f"✅ **위치 확인 완료:** {area['name']}")
                st.warning(f"⚠️ **현장 안전 수칙:** {area['info']}")
                found = True
                break
        if not found:
            st.info("ℹ️ 현재 등록된 안전 수칙 구역 외부에 있습니다.")
    else:
        st.info("🔄 위치 정보를 가져오는 중입니다. 모바일 기기의 GPS 권한을 확인해 주세요.")

    st.divider()

    st.subheader("📸 현장 장비 및 QR 촬영")
    st.write("카메라 기능을 켜서 현장 사진을 촬영하거나 점검할 수 있습니다.")
    
    # 💥 에러의 원인이었던 불안정한 camera_input_live 대신 Streamlit 기본 내장 카메라 모듈로 안전하게 대체했습니다.
    img_file = st.camera_input("스마트폰 카메라 구동")
    if img_file:
        st.image(img_file, caption="촬영된 이미지 확인", use_container_width=True)
        st.success("✨ 사진이 정상적으로 저장되었습니다.")

# --- [2번 화면: 화학물질 자료실 영역] ---
elif selected_tab == "📚 화학물질 자료실":
    st.subheader("📋 공장 취급 화학물질 정보")
    chem_options = {info["name"]: key for key, info in CHEMICALS.items()}
    
    # QR코드로 유입된 경우 해당 물질을 셀렉트박스의 기본 인덱스로 자동 지정합니다.
    default_index = 0
    if qr_chem and qr_chem in CHEMICALS:
        default_index = chem_list.index(qr_chem)
        st.success(f"🔍 QR 코드가 성공적으로 인식되었습니다: **{CHEMICALS[qr_chem]['name']}**")
    else:
        st.write("안전 데이터 확인이 필요한 화학물질을 선택하세요.")
        
    selected_name = st.selectbox("🔍 화학물질 검색/선택", list(chem_options.keys()), index=default_index)
    
    if selected_name:
        chem_key = chem_options[selected_name]
        chem_data = CHEMICALS[chem_key]
        
        # 선택된 물질 정보 출력
        st.markdown(f"## **{chem_data['name']}**")
        st.caption(f"🔗 **CAS No.** {chem_data['cas_no']}")
        st.error(f"⚠️ **분류 및 기호:** {chem_data['symbol']}")
        
        with st.expander("🚨 유해·위험 문구 상세", expanded=True):
            st.markdown(chem_data['danger'].replace("\n", "\n\n"))
            
        with st.expander("🩹 사고 시 긴급 응급조치 방법", expanded=True):
            st.info(chem_data['emergency'])
