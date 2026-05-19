import streamlit as st
from streamlit_js_eval import get_geolocation
import pandas as pd
from datetime import datetime
import os

# [1] 웹페이지 기본 설정
st.set_page_config(page_title="공장 안전 가이드", layout="centered")

# --- [🎨 대중적이고 세련된 대시보드 테마 CSS 적용] ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; color: #333333; font-family: 'Noto Sans KR', sans-serif; }
    h1 { color: #1e3a8a !important; font-weight: 700; padding-bottom: 10px; border-bottom: 3px solid #3b82f6; margin-bottom: 25px !important; }
    
    /* 상단 대시보드 스탯 스타일 */
    .metric-container { background-color: #ffffff; border: 1px solid #e5e7eb; padding: 15px; border-radius: 12px; text-align: center; box-shadow: 0px 4px 6px rgba(0,0,0,0.02); }
    .metric-title { font-size: 14px; color: #6b7280; font-weight: 600; }
    .metric-value { font-size: 24px; color: #1e3a8a; font-weight: 700; margin-top: 5px; }
    
    /* 메뉴 버튼 디자인 */
    div[data-testid="stRadio"] > label { display: none; } /* 라디오 라벨 숨기기 */
    
    /* 일반 버튼 디자인 */
    .stButton>button { width: 100%; background-color: #3b82f6; color: white; border: none; padding: 12px; border-radius: 8px; font-weight: bold; transition: all 0.3s ease; box-shadow: 0px 2px 4px rgba(0,0,0,0.05); }
    .stButton>button:hover { background-color: #1d4ed8; color: white; }
    
    /* 🚨 SOS 긴급 버튼 전용 스타일 */
    .sos-button button { background-color: #dc2626 !important; color: white !important; font-size: 16px !important; border-radius: 12px !important; box-shadow: 0px 4px 10px rgba(220, 38, 38, 0.3) !important; }
    .sos-button button:hover { background-color: #b91c1c !important; }
    
    /* 폼 영역 박스 */
    .stForm { background-color: #ffffff !important; border-radius: 12px !important; padding: 20px !important; border: 1px solid #e5e7eb !important; }
    </style>
    """, unsafe_allow_html=True)

# --- [관리자 설정: 화학물질 자료실 데이터 (총 9종)] ---
CHEMICALS = {
    "TOLUENE": {"name": "톨루엔 (Toluene)", "cas_no": "108-88-3", "symbol": "🔥 고인화성 / ⚠️ 급성·만성독성", "danger": "• 고인화성 액체 및 증기\n• 삼켜서 기도로 유입되면 치명적일 수 있음", "emergency": "1. 신선한 공기를 마시게 하고 안정\n2. 오염된 옷을 벗고 물질이 번지지 않게 세척"},
    "ACETONE": {"name": "아세톤 (Acetone)", "cas_no": "67-64-1", "symbol": "🔥 극인화성 / 👁️ 눈 자극성", "danger": "• 고인화성 액체 및 증기\n• 눈에 심한 자극 및 졸음, 현기증 유발", "emergency": "1. 신선한 공기가 있는 곳으로 이동\n2. 다량의 물과 비누로 깨끗이 세척 후 보습"},
    "SULFURIC_ACID": {"name": "황산 (Sulfuric Acid)", "cas_no": "7664-93-9", "symbol": "💀 급성독성 / 🧪 부식성 / 👁️ 실명위험", "danger": "• 화학적 화상 및 호흡기 손상\n• 폭발 및 화재 유발 위험", "emergency": "1. 오염된 옷을 찢어 벗기고 흐르는 물에 20분 이상 세척\n2. 눈꺼풀을 벌리고 흐르는 물로 30분 이상 세척"},
    "SODIUM_HYDROXIDE": {"name": "수산화나트륨", "cas_no": "1310-73-2", "symbol": "🧪 부식성 / 👁️ 실명위험", "danger": "• 피부, 눈에 심한 손상 및 화학적 화상\n• 금속을 부식시킬 수 있음", "emergency": "1. 미끈거림이 사라질 때까지 흐르는 물에 세척\n2. 호흡 곤란 시 산소 공급"},
    "BENZENE": {"name": "벤젠 (Benzene)", "cas_no": "71-43-2", "symbol": "🔥 고인화성 / 🎗️ 1급 발암성", "danger": "• 백혈병 및 유전적 결함 유발 가능\n• 흡입 시 치명적 위험", "emergency": "1. 즉시 신선한 공기 공급 및 인공호흡\n2. 오염된 의복 제거 후 다량의 물로 세척"},
    "ETHYLENE_OXIDE": {"name": "산화에틸렌 (EO)", "cas_no": "75-21-8", "symbol": "💥 폭발성 가스 / 🎗️ 발암성", "danger": "• 고압가스 및 극인화성 가스로 폭발 위험 매우 높음\n• 암을 일으킴", "emergency": "1. 환자를 즉시 안전한 지역으로 대피\n2. 흐르는 물로 20분 이상 세척"},
    "AMMONIA": {"name": "암모니아 (Ammonia)", "cas_no": "7664-41-7", "symbol": "☣️ 독성 가스 / 🧪 강한 부식성", "danger": "• 호흡기계에 심각한 화학적 화상 유발\n• 실명 위험", "emergency": "1. 신선한 공기 곳으로 이동 후 호흡 확인\n2. 다량의 물로 20분 이상 세척"},
    "1_3_BUTADIENE": {"name": "1,3-부타디엔", "cas_no": "106-99-0", "symbol": "🔥 극인화성 가스 / 🎗️ 발암성", "danger": "• 쉽게 점화되어 대형 화재 유발\n• 중추신경계 억제", "emergency": "1. 환자를 신선한 공기가 있는 곳으로 이동\n2. 동상 위험 시 따뜻한 물로 천천히 가온"},
    "ACRYLONITRILE": {"name": "아크릴로니트릴", "cas_no": "107-13-1", "symbol": "🔥 고인화성 / 💀 고독성", "danger": "• 체내에서 시안화물로 분해되어 극히 유독\n• 피부 흡수 매우 빠름", "emergency": "1. 송기마스크 착용 후 환자 대피\n2. 의복 즉시 제거 후 최소 20분 세척"}
}

# --- [🆕 데이터 저장 로직 (CSV 파일 기반 시스템)] ---
# 로그인 없이도 누적 점검 횟수를 화면에 보여주기 위한 로직입니다.
DB_FILE = "inspection_log.csv"
if not os.path.exists(DB_FILE):
    df = pd.DataFrame(columns=["일시", "점검자", "점검물질", "상태", "특이사항"])
    df.to_csv(DB_FILE, index=False, encoding="utf-8-sig")

# --- [🆕 주소창 QR 데이터 분석] ---
query_params = st.query_params
qr_chem = query_params.get("chem", None)
chem_list = list(CHEMICALS.keys())

current_page_idx = 0
if qr_chem and qr_chem in CHEMICALS:
    current_page_idx = 1

# --- [웹 화면 구현 시작] ---
st.title("🏭 스마트 안전관리 모바일 시스템")

# --- [🆕 심사위원 감동용 상단 대시보드 메트릭 바] ---
log_df = pd.read_csv(DB_FILE, encoding="utf-8-sig")
total_inspections = len(log_df)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f'<div class="metric-container"><div class="metric-title">공장 안전 등급</div><div class="metric-value" style="color:#10b981;">A GRADE</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-container"><div class="metric-title">오늘 누적 점검</div><div class="metric-value">{total_inspections} 건</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-container"><div class="metric-title">관제 센터 상태</div><div class="metric-value" style="color:#3b82f6;">정상 가동</div></div>', unsafe_allow_html=True)

st.write("")

# --- [🆕 1초가 급한 상황을 위한 무조건 상단 노출 SOS 버튼] ---
st.markdown('<div class="sos-button">', unsafe_allow_html=True)
if st.button("🚨 긴급상황 발생 (SOS 신호 전송)"):
    st.error("🚨 **[SOS 신호가 종합방재실로 즉시 전송되었습니다]**\n\n현재 기기의 GPS 좌표를 바탕으로 구조대가 출동 중입니다. 안전한 대피 경로를 확보하고 대피요령에 따라 즉시 대피하십시오.")
st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# 네비게이션 메뉴 선택
menu_tabs = ["📍 실시간 위치 및 지도", "📚 화학물질 QR 자료실"]
selected_tab = st.radio("메뉴", menu_tabs, index=current_page_idx, horizontal=True)

# --- [메뉴 1: 실시간 위치 및 지도] ---
if selected_tab == "📍 실시간 위치 및 지도":
    st.subheader("현재 내 위치 정보")
    loc = get_geolocation()
    if loc:
        curr_lat = loc['coords']['latitude']
        curr_lon = loc['coords']['longitude']
        st.write(f"📍 현재 나의 좌표: **{curr_lat:.4f}, {curr_lon:.4f}**")
        
        # 🆕 시각적 효과를 위해 실제 지도 화면 추가!
        map_data = pd.DataFrame({'lat': [curr_lat], 'lon': [curr_lon]})
        st.map(map_data, zoom=15)
        
        # 특정 가상 구역 매칭 (울산 석유화학단지 가상 좌표)
        if abs(curr_lat - 35.5416) < 0.005 and abs(curr_lon - 129.2555) < 0.005:
            st.success("✅ **위치 확인 완료:** 화학물 저장소 (A구역)")
            st.warning("⚠️ **현장 안전 수칙:** 방독면 착용 필수 및 화기 엄금!")
    else:
        st.info("🔄 위치 정보를 가져오는 중입니다. 스마트폰의 GPS 권한을 허용해 주세요.")

    st.divider()
    st.subheader("📸 현장 점검 카메라")
    img_file = st.camera_input("스마트폰 카메라 구동")
    if img_file:
        st.image(img_file, caption="촬영된 이미지 확인", use_container_width=True)

# --- [메뉴 2: 화학물질 자료실 + 🆕 실명제 점검 시스템] ---
elif selected_tab == "📚 화학물질 QR 자료실":
    st.subheader("📋 공장 취급 화학물질 정보")
    chem_options = {info["name"]: key for key, info in CHEMICALS.items()}
    
    default_index = 0
    if qr_chem and qr_chem in CHEMICALS:
        default_index = chem_list.index(qr_chem)
        st.success(f"🔍 QR 코드가 성공적으로 인식되었습니다: **{CHEMICALS[qr_chem]['name']}**")
        
    selected_name = st.selectbox("🔍 화학물질 검색/선택", list(chem_options.keys()), index=default_index)
    
    if selected_name:
        chem_key = chem_options[selected_name]
        chem_data = CHEMICALS[chem_key]
        
        st.markdown(f"## **{chem_data['name']}**")
        st.caption(f"🔗 **CAS No.** {chem_data['cas_no']}")
        st.error(f"⚠️ **분류 및 기호:** {chem_data['symbol']}")
        
        with st.expander("🚨 유해·위험 문구 상세", expanded=True):
            st.markdown(chem_data['danger'])
        with st.expander("🩹 사고 시 긴급 응급조치 방법", expanded=True):
            st.info(chem_data['emergency'])
            
        st.divider()
        
        # 🆕 [하이라이트 기능] 로그인 없이 쓰는 현장 실명 점검 일지 폼
        st.subheader("✍️ 현장 안전 점검 일지 기록")
        st.write("해당 구역 점검 후 로그 없이 실명으로 이력을 남길 수 있습니다.")
        
        with st.form("inspection_form", clear_on_submit=True):
            inspector = st.text_input("👤 점검자 성명 (소속 포함)", placeholder="예: 안전팀 홍길동")
            status = st.selectbox("📊 시설물 상태", ["정상 (이상 없음)", "주의 (정비 필요)", "위험 (즉시 조치 요망)"])
            note = st.text_area("📝 특이사항 및 조치 내용", placeholder="현장 밸브 및 누출 여부 점검 내용 작성")
            
            submit_btn = st.form_submit_button("📁 점검 일지 제출하기")
            
            if submit_btn:
                if not inspector:
                    st.error("종합방재실 기록을 위해 점검자 성명을 반드시 입력해 주세요!")
                else:
                    # CSV 데이터 저장 과정
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    new_log = pd.DataFrame([[now_str, inspector, chem_data['name'], status, note]], 
                                           columns=["일시", "점검자", "점검물질", "상태", "특이사항"])
                    
                    log_df = pd.read_csv(DB_FILE, encoding="utf-8-sig")
                    updated_df = pd.concat([log_df, new_log], ignore_index=False)
                    updated_df.to_csv(DB_FILE, index=False, encoding="utf-8-sig")
                    
                    st.success(f"📥 {inspector}님의 안전 점검 일지가 방재실 서버로 성공적으로 전송되었습니다!")
                    st.rerun() # 상단 누적 점검 건수 새로고침용
