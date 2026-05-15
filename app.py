import streamlit as st
from streamlit_js_eval import get_geolocation

# 앱 화면 설정
st.set_page_config(page_title="공장 안전 가이드", layout="centered")

# --- [관리자 설정: 여기서 정보를 수정하세요] ---
# 구역 이름, 위도, 경도, 안내 문구를 여기서 직접 관리합니다.
AREAS = [
    {
        "name": "화학물 저장소 (A구역)",
        "lat": 35.1234,  # 나중에 실제 위치 위도로 수정
        "lon": 129.1234, # 나중에 실제 위치 경도로 수정
        "info": "방독면 착용 필수 및 화기 엄금!"
    },
    {
        "name": "제조 라인 (B구역)",
        "lat": 35.5678,
        "lon": 129.5678,
        "info": "지게차 이동 주의, 안전화 착용 확인."
    }
]
# ------------------------------------------

st.title("🏭 화학공장 안전관리 웹")
st.write("로그인 없이 위치 권한만으로 사용 가능합니다.")

# 사용자의 현재 GPS 위치 가져오기
loc = get_geolocation()

if loc:
    curr_lat = loc['coords']['latitude']
    curr_lon = loc['coords']['longitude']
    
    st.write(f"📍 현재 나의 좌표: {curr_lat:.4f}, {curr_lon:.4f}")
    
    found = False
    for area in AREAS:
        # 내 위치와 설정된 위치가 약 50m~100m 이내면 인식
        if abs(curr_lat - area['lat']) < 0.0008 and abs(curr_lon - area['lon']) < 0.0008:
            st.success(f"✅ 현재 위치 인식됨: {area['name']}")
            st.warning(f"⚠️ 안전 수칙: {area['info']}")
            found = True
            break
            
    if not found:
        st.info("현재 등록된 안전 구역 밖에 있습니다.")

st.divider()
st.subheader("📸 QR 코드 스캔")
if st.button("카메라 켜기"):
    st.write("브라우저 상단의 '카메라 허용'을 눌러주세요.")
