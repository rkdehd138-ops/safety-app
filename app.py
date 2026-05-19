import streamlit as st
from streamlit_js_eval import get_geolocation

# [1] 웹페이지 기본 설정
st.set_page_config(page_title="공장 안전 가이드", layout="centered")

# --- [관리자 설정: 안전 구역 좌표 데이터] ---
AREAS = [
    {
        "name": "화학물 저장소 (A구역)",
        "lat": 35.5416,  
        "lon": 129.2555, 
        "info": "방독면 착용 필수 및 화기 엄금!"
    }
]

# --- [관리자 설정: 화학물질 자료실 데이터] ---
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
    }
}

# --- [웹 화면 구현 시작] ---
st.title("🏭 화학공장 안전관리 웹")

# 탭 메뉴 구성 (홈/카메라와 화학물질 자료실 분리)
tab1, tab2 = st.tabs(["📍 실시간 안전 가이드", "📚 화학물질 자료실"])

# --- [탭 1: 위치 확인 및 카메라 기능] ---
with tab1:
    st.subheader("현재 내 위치 확인")
    loc = get_geolocation()
    if loc:
        curr_lat = loc['coords']['latitude']
        curr_lon = loc['coords']['longitude']
        st.write(f"📍 현재 나의 좌표: {curr_lat:.4f}, {curr_lon:.4f}")
        
        found = False
        for area in AREAS:
            if abs(curr_lat - area['lat']) < 0.0008 and abs(curr_lon - area['lon']) < 0.0008:
                st.success(f"✅ 위치 확인: {area['name']}")
                st.warning(f"⚠️ 지침: {area['info']}")
                found = True
                break
        if not found:
            st.info("현재 등록된 안전 구역 외부에 있습니다.")
    else:
        st.info("위치 정보를 불러오는 중이거나 권한이 차단되었습니다.")

    st.divider()

    st.subheader("📸 장비/물질 촬영")
    st.write("카메라가 켜지면 전/후면 카메라를 전환하여 촬영할 수 있습니다.")
    img_file = st.camera_input("카메라 작동")
    if img_file:
        st.image(img_file, caption="촬영된 이미지", use_container_width=True)
        st.success("사진이 정상적으로 캡처되었습니다.")

# --- [탭 2: 화학물질 자료실 메뉴] ---
with tab2:
    st.subheader("📋 현장 취급 화학물질 정보")
    st.write("조회하고 싶은 화학물질을 선택하세요.")
    
    # 딕셔너리의 이름들을 리스트로 만들어 선택박스 제공
    chem_options = {info["name"]: key for key, info in CHEMICALS.items()}
    selected_name = st.selectbox("화학물질 선택", list(chem_options.keys()))
    
    if selected_name:
        chem_key = chem_options[selected_name]
        chem_data = CHEMICALS[chem_key]
        
        st.markdown(f"### **{chem_data['name']}**")
        st.caption(f"**CAS No.** {chem_data['cas_no']}")
        st.error(f"**분류/분류기호:** {chem_data['symbol']}")
        
        with st.expander("🚨 유해·위험 문구", expanded=True):
            st.write(chem_data['danger'])
            
        with st.expander("🩹 사고 시 응급조치 방법", expanded=True):
            st.info(chem_data['emergency'])
