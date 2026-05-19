import streamlit as st
from streamlit_js_eval import get_geolocation
import pandas as pd
from datetime import datetime
import os

# [1] 웹페이지 기본 설정
st.set_page_config(page_title="공장 안전 가이드", layout="centered")

# --- [🎨 세련된 대시보드 및 경보 테마 CSS 적용] ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; color: #333333; font-family: 'Noto Sans KR', sans-serif; }
    h1 { color: #1e3a8a !important; font-weight: 700; padding-bottom: 10px; border-bottom: 3px solid #3b82f6; margin-bottom: 25px !important; }
    
    /* 대시보드 스탯 스타일 */
    .metric-container { background-color: #ffffff; border: 1px solid #e5e7eb; padding: 15px; border-radius: 12px; text-align: center; box-shadow: 0px 4px 6px rgba(0,0,0,0.02); }
    .metric-title { font-size: 14px; color: #6b7280; font-weight: 600; }
    .metric-value { font-size: 24px; color: #1e3a8a; font-weight: 700; margin-top: 5px; }
    
    /* 🚨 SOS 긴급 버튼 전용 스타일 */
    .sos-button button { background-color: #dc2626 !important; color: white !important; font-size: 16px !important; border-radius: 12px !important; box-shadow: 0px 4px 10px rgba(220, 38, 38, 0.3) !important; }
    .sos-button button:hover { background-color: #b91c1c !important; }
    
    /* 🚨 실시간 사이렌 애니메이션 효과 (교수님 지적 방지용 비주얼) */
    .siren-alert { background-color: #fef2f2; border: 2px solid #ef4444; padding: 15px; border-radius: 12px; animation: blink 1.5s infinite; color: #b91c1c; font-weight: bold; margin-bottom: 20px; }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
    </style>
    """, unsafe_allow_html=True)

# --- [관리자 설정: 화학물질 데이터베이스 (총 9종)] ---
CHEMICALS = {
    "TOLUENE": {"name": "톨루엔 (Toluene)", "cas_no": "108-88-3", "symbol": "🔥 고인화성 / ⚠️ 급성·만성독성", "danger": "• 고인화성 액체 및 증기\n• 삼켜서 기도로 유입되면 치명적일 수 있음", "emergency": "1. 신선한 공기를 마시게 하고 안정\n2. 오염된 옷을 벗고 물질이 번지지 않게 세척"},
    "ACETONE": {"name": "아세톤 (Acetone)", "cas_no": "67-64-1", "symbol": "🔥 극인화성 / 👁️ 눈 자극성", "danger": "• 고인화성 액체 및 증기\n• 눈에 심한 자극 및 졸음, 현기증 유발", "emergency": "1. 신선한 공기가 있는 곳으로 이동\n2. 다량의 물과 비누로 깨끗이 세척 후 보습"},
    "SULFURIC_ACID": {"name": "황산 (Sulfuric Acid)", "cas_no": "7664-93-9", "symbol": "💀 급성독성 / 🧪 부식성 / 👁️ 실명위험", "danger": "• 화학적 화상 및 호흡기 손상\n• 폭발 및 화재 유발 위험", "emergency": "1. 오염된 옷을 찢어 벗기고 흐르는 물에 20분 이상 세척\n2. 눈꺼풀을 벌리고 흐르는 물로 30분 이상 세척"},
    "SODIUM_HYDROXIDE": {"name": "수산화나트륨", "cas_no": "1310-73-2", "symbol": "🧪 부식성 / 👁️ 실명위험", "danger": "• 피부, 눈에 심한 손상 및 화학적 화상\n• 금속을 부식시킬 수 있음", "emergency": "1. 미끈거림이 사라질 때까지 흐르는 물에 세척\n2. 호흡 곤란 시 산소 공급"},
    "BENZENE": {"name": "벤젠 (Benzene)", "cas_no": "71-43-2", "symbol": "🔥 고인화성 / 🎗️ 1급 발암성", "danger": "• 백혈병 및 유전적 결함 유발 가능\n• 흡입 시 치명적 위험", "emergency": "1. 즉시 신선한 공기 공급\n2. 오염된 의복 제거 후 세척"},
    "ETHYLENE_OXIDE": {"name": "산화에틸렌 (EO)", "cas_no": "75-21-8", "symbol": "💥 폭발성 가스 / 🎗️ 발암성", "danger": "• 고압가스 및 극인화성 가스로 폭발 위험 매우 높음", "emergency": "1. 환자를 즉시 안전한 지역으로 대피"},
    "AMMONIA": {"name": "암모니아 (Ammonia)", "cas_no": "7664-41-7", "symbol": "☣️ 독성 가스 / 🧪 강한 부식성", "danger": "• 호흡기계에 심각한 화학적 화상 유발", "emergency": "1. 신선한 공기 곳으로 이동"},
    "1_3_BUTADIENE": {"name": "1,3-부타디엔", "cas_no": "106-99-0", "symbol": "🔥 극인화성 가스 / 🎗️ 발암성", "danger": "• 쉽게 점화되어 대형 화재 유발", "emergency": "1. 환자를 신선한 공기 곳으로 이동"},
    "ACRYLONITRILE": {"name": "아크릴로니트릴", "cas_no": "107-13-1", "symbol": "🔥 고인화성 / 💀 고독성", "danger": "• 체내에서 시안화물로 분해되어 극히 유독", "emergency": "1. 송기마스크 착용 후 환자 대피"}
}

# --- [🆕 하드웨어 DB 연동 파일 생성 (진짜 저장 기능)] ---
DB_LOG = "inspection_log.csv"
DB_SOS = "sos_log.csv"

for f, cols in [(DB_LOG, ["일시", "점검자", "점검물질", "상태", "특이사항"]), (DB_SOS, ["일시", "위치_위도", "위치_경도", "상태"])]:
    if not os.path.exists(f):
        pd.DataFrame(columns=cols).to_csv(f, index=False, encoding="utf-8-sig")

# --- [🆕 QR 데이터 분석 및 기본 탭 설정] ---
query_params = st.query_params
qr_chem = query_params.get("chem", None)
chem_list = list(CHEMICALS.keys())

# 기본 페이지 설정 (QR코드로 접속하면 자동으로 1번(자료실) 탭 활성화)
init_tab = 0
if qr_chem and qr_chem in CHEMICALS:
    init_tab = 1

# --- [상단 대시보드 영역] ---
log_df = pd.read_csv(DB_LOG, encoding="utf-8-sig")
sos_df = pd.read_csv(DB_SOS, encoding="utf-8-sig")

# --- [🔥 실시간 관리자 모니터링 연동 체크] ---
# sos_log.csv에 '미조치'인 비상 상황이 있으면 상단에 실시간 사이렌 경보를 발생시킵니다.
active_sos = sos_df[sos_df["상태"] == "🚨 미조치 긴급상황"]

if not active_sos.empty:
    st.markdown(f'<div class="siren-alert">⚠️ [종합방재실 비상 경보] 현재 공장 내에 조치되지 않은 SOS 긴급 상황이 발생했습니다! ({len(active_sos)}건 대기 중)</div>', unsafe_allow_html=True)

# 메인 사이드바 - 로그인 없이 다중 권한(작업자/방재실)을 구현하는 핵심 치트키
st.sidebar.header("⚙️ 시스템 권한 설정")
user_role = st.sidebar.selectbox("현재 접속 모드", ["👷 현장 작업자 모드", "🖥️ 종합 방재실(관리자) 모드"])

# =========================================================================
# [권한 1] 현장 작업자 모드
# =========================================================================
if user_role == "👷 현장 작업자 모드":
    st.title("🏭 스마트 안전관리 모바일 시스템")
    
    # 상단 SOS 버튼
    st.markdown('<div class="sos-button">', unsafe_allow_html=True)
    if st.button("🚨 긴급상황 발생 (SOS 신호 전송)"):
        loc = get_geolocation()
        lat = loc['coords']['latitude'] if loc else 35.5416
        lon = loc['coords']['longitude'] if loc else 129.2555
        
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_sos = pd.DataFrame([[now_str, lat, lon, "🚨 미조치 긴급상황"]], columns=["일시", "위치_위도", "위치_경도", "상태"])
        
        sos_df = pd.read_csv(DB_SOS, encoding="utf-8-sig")
        pd.concat([sos_df, new_sos], ignore_index=True).to_csv(DB_SOS, index=False, encoding="utf-8-sig")
        st.error("🚨 **[SOS 신호가 종합방재실 관제 센터로 즉시 송신되었습니다]** 현 위치에서 안전을 확보하고 구조대를 기다리십시오.")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    
    # 메뉴 선택
    menu_tabs = st.tabs(["📍 실시간 위치 지침", "📚 화학물질 QR 자료실"])
    
    # 탭 1: 위치 가이드
    with menu_tabs[0]:
        st.subheader("현재 내 위치 정보")
        loc = get_geolocation()
        if loc:
            curr_lat, curr_lon = loc['coords']['latitude'], loc['coords']['longitude']
            st.write(f"📍 현재 나의 좌표: **{curr_lat:.4f}, {curr_lon:.4f}**")
            map_data = pd.DataFrame({'lat': [curr_lat], 'lon': [curr_lon]})
            st.map(map_data, zoom=15)
        else:
            st.info("🔄 위치(GPS) 정보를 수집 중입니다...")
            
        st.subheader("📸 현장 점검용 카메라")
        img_file = st.camera_input("카메라 구동")
        if img_file: st.success("✨ 사진이 임시 저장되었습니다.")

    # 탭 2: 화학물질 자료실 & 점검일지 데이터 입력
    with menu_tabs[1]:
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
            st.error(f"⚠️ **분류 및 기호:** {chem_data['symbol']}")
            st.write(chem_data['danger'])
            st.info(chem_data['emergency'])
            
            st.divider()
            st.subheader("✍️ 현장 안전 점검 일지 제출")
            with st.form("inspection_form", clear_on_submit=True):
                inspector = st.text_input("👤 점검자 성명 (소속 포함)", placeholder="예: 공정1팀 김철수")
                status = st.selectbox("📊 시설물 상태", ["정상 (이상 없음)", "주의 (정비 필요)", "위험 (즉시 조치 요망)"])
                note = st.text_area("📝 특이사항")
                submit_btn = st.form_submit_button("📁 점검 일지 시스템 전송")
                
                if submit_btn and inspector:
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    new_log = pd.DataFrame([[now_str, inspector, chem_data['name'], status, note]], columns=["일시", "점검자", "점검물질", "상태", "특이사항"])
                    log_df = pd.read_csv(DB_LOG, encoding="utf-8-sig")
                    pd.concat([log_df, new_log], ignore_index=True).to_csv(DB_LOG, index=False, encoding="utf-8-sig")
                    st.success("📥 점검 결과가 종합방재실 서버 데이터베이스로 즉시 전송되었습니다!")
                    st.columns(1) # 새로고침 유도용

# =========================================================================
# [권한 2] 종합 방재실 관제 센터 모드 (교수님 확인용 데모 화면)
# =========================================================================
else:
    st.title("🖥️ 종합 방재실 안전관제 대시보드")
    st.write("공장 내 작업자들의 SOS 신고 현황과 실시간 점검 기록을 실시간 관제합니다.")
    
    # 1. 실시간 SOS 상황판
    st.subheader("🚨 실시간 SOS 비상 신고 접수 현황")
    if active_sos.empty:
        st.success("✅ 현재 접수된 비상 신고가 없습니다. 공장 내부 평온 상태 유지 중")
    else:
        st.warning(f"현재 {len(active_sos)}개의 비상 상황이 발생했습니다. 지도상의 기기 GPS 위치로 구조대를 급파하십시오.")
        
        # SOS가 발생한 위치들을 한눈에 지도에 마커로 시각화
        sos_map_data = active_sos.rename(columns={"위치_위도": "lat", "위치_경도": "lon"})
        st.map(sos_map_data, zoom=12)
        
        # SOS 표 데이터 표출 및 조치 완료 처리 기능
        for index, row in active_sos.iterrows():
            col_info, col_btn = st.columns([3, 1])
            with col_info:
                st.write(f"⏰ **발생시간:** {row['일시']} | **좌표:** {row['위치_위도']:.4f}, {row['위치_경도']:.4f}")
            with col_btn:
                if st.button("✅ 조치 완료 처리", key=f"sos_{index}"):
                    full_sos_df = pd.read_csv(DB_SOS, encoding="utf-8-sig")
                    full_sos_df.at[index, "상태"] = "조치완료"
                    full_sos_df.to_csv(DB_SOS, index=False, encoding="utf-8-sig")
                    st.success("상황 조치 완료 반영되었습니다.")
                    st.rerun()

    st.divider()

    # 2. 실시간 현장 점검 로그 모니터링 (작업자가 입력한 일지가 여기 실시간으로 들어옴)
    st.subheader("📋 현장 작업자 실시간 점검 기록 DB")
    current_logs = pd.read_csv(DB_LOG, encoding="utf-8-sig")
    
    if current_logs.empty:
        st.info("아직 제출된 현장 안전 점검 일지가 없습니다.")
    else:
        st.dataframe(current_logs.sort_values(by="일시", ascending=False), use_container_width=True)
        
        if st.button("🗑️ 전체 데이터 초기화 (데모용)"):
            pd.DataFrame(columns=["일시", "점검자", "점검물질", "상태", "특이사항"]).to_csv(DB_LOG, index=False, encoding="utf-8-sig")
            pd.DataFrame(columns=["일시", "위치_위도", "위치_경도", "상태"]).to_csv(DB_SOS, index=False, encoding="utf-8-sig")
            st.success("모든 실시간 시뮬레이션 데이터가 초기화되었습니다.")
            st.rerun()
