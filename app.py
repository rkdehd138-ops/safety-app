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

# [2] 카메라 전환 기능 구현
st.subheader("📸 QR 스캔 / 카메라")

# 카메라 모드 상태 저장 (기본값은 후면 'environment')
if 'camera_mode' not in st.session_state:
    st.session_state.camera_mode = "environment"

# 전환 버튼
if st.button("🔄 카메라 전/후면 전환"):
    if st.session_state.camera_mode == "environment":
        st.session_state.camera_mode = "user" # 전면으로 변경
    else:
        st.session_state.camera_mode = "environment" # 후면으로 변경
    st.rerun() # 앱 재실행하여 카메라 모드 적용

st.write(f"현재 설정: {'후면(외측)' if st.session_state.camera_mode == 'environment' else '전면(내측)'} 카메라")

# 카메라 실행 (에러 방지를 위해 최소한의 설정만 사용)
image = camera_input_live(
    constraints={"video": {"facingMode": st.session_state.camera_mode}}
)

if image:
    st.image(image, caption="스캔된 화면", use_container_width=True)
