import streamlit as st
from streamlit_js_eval import get_geolocation
from camera_input_live import camera_input_live

st.set_page_config(page_title="공장 안전 가이드", layout="centered")

# --- [관리자 설정] ---
AREAS = [
    {
        "name": "화학물 저장소 (A구역)",
        "lat": 35.5416,  
        "lon": 129.2555, 
        "info": "방독면 착용 필수 및 화기 엄금!"
    }
]

st.title("🏭 화학공장 안전관리 웹")

# [1] 위치 정보 확인
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
        st.info("안전 구역 외부에 있습니다.")

st.divider()

# [2] 가장 안정적인 기본 카메라 설정
st.subheader("📸 QR 스캔 / 카메라")
st.write("카메라 화면이 나오면 QR 코드를 비추어 주세요.")

# 에러 유발 옵션을 모두 제거한 기본 호출입니다.
image = camera_input_live()

if image:
    st.image(image, caption="스캔된 화면", use_container_width=True)
