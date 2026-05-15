import streamlit as st
from streamlit_js_eval import get_geolocation
from camera_input_live import camera_input_live

st.set_page_config(page_title="공장 안전 가이드", layout="centered")

# --- [관리자 설정: 좌표 및 안내문구] ---
AREAS = [
    {
        "name": "화학물 저장소 (A구역)",
        "lat": 35.5416,  
        "lon": 129.2555, 
        "info": "방독면 착용 필수 및 화기 엄금! 내부 진입 시 관리자 승인 요망."
    }
]
# ------------------------------------------

st.title("🏭 화학공장 안전관리 웹")

# [1] 위치 정보 가져오기
loc = get_geolocation()
if loc:
    curr_lat = loc['coords']['latitude']
    curr_lon = loc['coords']['longitude']
    st.write(f"📍 현재 나의 좌표: {curr_lat:.4f}, {curr_lon:.4f}")
    
    found = False
    for area in AREAS:
        if abs(curr_lat - area['lat']) < 0.0008 and abs(curr_lon - area['lon']) < 0.0008:
            st.success(f"✅ 현재 위치 인식됨: {area['name']}")
            st.warning(f"⚠️ 안전 수칙: {area['info']}")
            found = True
            break
    if not found:
        st.info("현재 등록된 안전 구역 밖에 있습니다.")

st.divider()

# [2] 실시간 QR 스캔/카메라 기능
st.subheader("📸 장비/물질 QR 코드 스캔")
st.write("아래 카메라 화면에 QR 코드를 비추어 주세요.")

# 실시간 카메라 입력창 (스마트폰 카메라가 웹 안에서 바로 켜집니다)
image = camera_input_live()

if image:
    st.image(image, caption="인식 중...", use_container_width=True)
    # 팁: 현장 장비에 붙은 QR 코드에 '웹사이트 주소'나 '장비 번호'를 담아두면
    # 여기에 그 데이터 내용이 문자열로 표시되도록 연동할 수 있습니다.
    st.info("💡 카메라가 정상 작동 중입니다. QR 코드 분석 기능 준비 완료.")
