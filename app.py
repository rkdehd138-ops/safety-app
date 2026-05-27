import streamlit as st
from streamlit_js_eval import get_geolocation
import pandas as pd
from datetime import datetime, timedelta
import os
import time

st.set_page_config(page_title="스마트 공장 안전관리 시스템", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f1f5f9; color: #1e293b; font-family: 'Noto Sans KR', sans-serif; }
    .main-title-banner { background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 24px; border-radius: 16px; color: white; margin-bottom: 30px; box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.3); }
    .content-card { background-color: #ffffff; border: 1px solid #e2e8f0; padding: 25px; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); margin-bottom: 20px; height: 100%; }
    .sos-container button { background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%) !important; color: white !important; font-size: 22px !important; font-weight: 800 !important; padding: 20px 0px !important; width: 100% !important; border-radius: 14px !important; border: none !important; box-shadow: 0px 8px 20px rgba(239, 68, 68, 0.4) !important; }
    .siren-alert { background-color: #fef2f2; border: 2px solid #ef4444; padding: 18px; border-radius: 12px; animation: blink 1.5s infinite; color: #b91c1c; font-weight: 800; text-align: center; margin-bottom: 25px; }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.6; } 100% { opacity: 1; } }
    </style>
    """, unsafe_allow_html=True)

ADMIN_PASSWORD_PLAIN = "admin1234"
def verify_password(input_password): return input_password.strip() == ADMIN_PASSWORD_PLAIN.strip()

# 20종 유해 화학물질 DB
CHEMICALS = {
    "TOLUENE": {"name": "톨루엔", "cas_no": "108-88-3", "symbol": "🔥 고인화성/독성", "danger": "중추신경계 억제, 생식독성", "emergency": "신선한 공기, 오염 의복 제거"},
    "ACETONE": {"name": "아세톤", "cas_no": "67-64-1", "symbol": "🔥 극인화성", "danger": "눈 자극, 졸음 유발", "emergency": "다량의 물로 세척"},
    "SULFURIC_ACID": {"name": "황산", "cas_no": "7664-93-9", "symbol": "🧪 부식성", "danger": "심각한 화상", "emergency": "20분 이상 흐르는 물 세척"},
    "BENZENE": {"name": "벤젠", "cas_no": "71-43-2", "symbol": "🎗️ 1급 발암물질", "danger": "백혈병 유발", "emergency": "즉시 안전지역 대피"},
    "AMMONIA": {"name": "암모니아", "cas_no": "7664-41-7", "symbol": "☣️ 독성가스", "danger": "호흡기 화상", "emergency": "신선한 공기 공급"},
    "METHANOL": {"name": "메탄올", "cas_no": "67-56-1", "symbol": "💀 고독성/인화성", "danger": "중추신경계 손상, 실명", "emergency": "즉시 병원 이송"},
    "HYDROCHLORIC_ACID": {"name": "염산", "cas_no": "7647-01-0", "symbol": "🧪 부식성", "danger": "점막 부식, 호흡곤란", "emergency": "다량의 물로 세척"},
    "NITRIC_ACID": {"name": "질산", "cas_no": "7697-37-2", "symbol": "🧪 강한 부식성", "danger": "강력한 산화제", "emergency": "피부 세척 및 진료"},
    "CHLORINE": {"name": "염소", "cas_no": "7782-50-5", "symbol": "☣️ 독성가스", "danger": "폐부종 유발", "emergency": "환자 안정 및 병원 이송"},
    "ETHYLENE_OXIDE": {"name": "산화에틸렌", "cas_no": "75-21-8", "symbol": "💥 폭발성/발암성", "danger": "폭발 위험", "emergency": "안전 지역 대피"},
    "HYDROGEN_FLUORIDE": {"name": "불산", "cas_no": "7664-39-3", "symbol": "💀 치명적 독성", "danger": "뼈 조직 손상", "emergency": "글루콘산 칼슘 도포"},
    "XYLENE": {"name": "자일렌", "cas_no": "1330-20-7", "symbol": "🔥 인화성", "danger": "마취성 증기", "emergency": "신선한 공기 공급"},
    "FORMALDEHYDE": {"name": "포름알데히드", "cas_no": "50-00-0", "symbol": "🎗️ 발암성", "danger": "알레르기 반응", "emergency": "눈/피부 세척"},
    "SODIUM_HYDROXIDE": {"name": "수산화나트륨", "cas_no": "1310-73-2", "symbol": "🧪 부식성", "danger": "심한 피부 화상", "emergency": "흐르는 물 세척"},
    "BUTADIENE": {"name": "1,3-부타디엔", "cas_no": "106-99-0", "symbol": "🔥 극인화성", "danger": "대형 화재 위험", "emergency": "즉시 대피"},
    "ACRYLONITRILE": {"name": "아크릴로니트릴", "cas_no": "107-13-1", "symbol": "💀 고독성", "danger": "시안화물 독성", "emergency": "산소 공급 및 진료"},
    "HYDROGEN_CYANIDE": {"name": "시안화수소", "cas_no": "74-90-8", "symbol": "💀 극독성", "danger": "즉사 위험", "emergency": "즉시 전문의 진료"},
    "PHOSPHINE": {"name": "포스핀", "cas_no": "7803-51-2", "symbol": "💀 급성독성", "danger": "폐 손상", "emergency": "환자 대피"},
    "CARBON_MONOXIDE": {"name": "일산화탄소", "cas_no": "630-08-0", "symbol": "☣️ 질식독성", "danger": "의식 불명", "emergency": "신선한 공기 공급"},
    "VINYL_CHLORIDE": {"name": "염화비닐", "cas_no": "75-01-4", "symbol": "🎗️ 발암성", "danger": "간 손상", "emergency": "증기 흡입 차단"}
}
# --- [데이터 저장 파일 생성 및 컬럼 정의] ---
DB_LOG = "inspection_log.csv"
DB_SOS = "sos_log.csv"
LOG_COLS = ["일시", "점검자", "점검물질", "상태", "특이사항"]
SOS_COLS = ["일시", "위치_위도", "위치_경도", "상태"]

def init_databases(force=False):
    if force or not os.path.exists(DB_LOG):
        pd.DataFrame(columns=LOG_COLS).to_csv(DB_LOG, index=False, encoding="utf-8-sig")
    if force or not os.path.exists(DB_SOS):
        pd.DataFrame(columns=SOS_COLS).to_csv(DB_SOS, index=False, encoding="utf-8-sig")

init_databases()

# --- [시간 연산] ---
now_kst = datetime.utcnow() + timedelta(hours=9)

# --- https://www.calluscompany.com/blog/kr/what-is-parameter ---
qr_chem = st.query_params.get("chem", None)
admin_bypass = st.query_params.get("admin", None) 
chem_list = list(CHEMICALS.keys())
if isinstance(qr_chem, list) and len(qr_chem) > 0: qr_chem = qr_chem[0]
if qr_chem: qr_chem = str(qr_chem).strip().upper()

init_menu_idx = 1 if (qr_chem and qr_chem in CHEMICALS) else 0

# --- [실시간 알림] ---
sos_df = pd.read_csv(DB_SOS, encoding="utf-8-sig")
active_sos = sos_df[sos_df["상태"] == "🚨 미조치 긴급상황"]
if not active_sos.empty:
    st.markdown(f'<div class="siren-alert">⚠️ [종합방재실] 긴급 상황 발생: {len(active_sos)}건 대기 중</div>', unsafe_allow_html=True)

# --- [사이드바] ---
user_role = st.sidebar.selectbox("접속 모드", ["👷 현장 작업자 모드", "🖥️ 종합 방재실 모드"])
# =========================================================================
# [권한 1] 👷 현장 작업자 모드 (사진 촬영 및 데이터 전송 포함)
# =========================================================================
if user_role == "👷 현장 작업자 모드":
    st.markdown("""
        <div class="main-title-banner">
            <h1 style='color: white !important; margin:0; border:none; padding:0; font-size:32px;'>🏭 스마트 안전관리 모바일 시스템</h1>
            <p style='margin: 8px 0 0 0; opacity: 0.9; font-size:16px;'>실시간 GPS 위치 관제 및 모바일 현장 QR 안전 점검 인프라</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_left, col_right = st.columns([1, 2], gap="large")
    
    with col_left:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("<h3 style='margin-top:0; color:#1e3a8a;'>🚨 긴급 구조 제어 센터</h3>", unsafe_allow_html=True)
        
        if st.button("🚨 긴급상황 발생 (SOS 신호 즉시 전송)"):
            loc = get_geolocation()
            lat = loc['coords']['latitude'] if loc else 35.5416
            lon = loc['coords']['longitude'] if loc else 129.2555
            new_sos = pd.DataFrame([[now_kst.strftime("%Y-%m-%d %H:%M:%S"), lat, lon, "🚨 미조치 긴급상황"]], columns=SOS_COLS)
            sos_df = pd.read_csv(DB_SOS, encoding="utf-8-sig")
            pd.concat([sos_df, new_sos], ignore_index=True).to_csv(DB_SOS, index=False, encoding="utf-8-sig")
            st.error("🚨 **[방재실 관제 센터로 SOS 송신 완료!]**")
        
        st.subheader("📸 현장 이상 부위 사진 촬영")
        uploaded_file = st.camera_input("스마트폰 카메라 구동")
        if uploaded_file is not None:
            if not os.path.exists("uploads"): os.makedirs("uploads")
            file_name = f"uploads/IMG_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            with open(file_name, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"✨ 사진 데이터 서버 저장 완료: {file_name}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.subheader("📚 화학물질 QR 안전 자료실")
        
        chem_options = {info["name"]: key for key, info in CHEMICALS.items()}
        selected_name = st.selectbox("🔍 화학물질 선택", list(chem_options.keys()))
        
        if selected_name:
            chem_data = CHEMICALS[chem_options[selected_name]]
            st.markdown(f"### 🧪 {chem_data['name']}")
            st.error(f"**위험 기호:** {chem_data['symbol']}")
            with st.expander("🚨 자세한 위험성", expanded=True): st.write(chem_data['danger'])
            with st.expander("🚑 긴급 응급조치", expanded=True): st.info(chem_data['emergency'])
            
            with st.form("log_form"):
                inspector = st.text_input("👤 검사자 성명")
                note = st.text_area("📝 특이사항")
                if st.form_submit_button("📁 점검 일지 전송"):
                    new_log = pd.DataFrame([[now_kst.strftime("%Y-%m-%d %H:%M:%S"), inspector, chem_data['name'], "정상", note]], columns=LOG_COLS)
                    pd.concat([pd.read_csv(DB_LOG, encoding="utf-8-sig"), new_log], ignore_index=True).to_csv(DB_LOG, index=False, encoding="utf-8-sig")
                    st.success("📥 데이터 기록 완료")
        st.markdown('</div>', unsafe_allow_html=True)
        # =========================================================================
# [권한 2] 🖥️ 종합 방재실(관리자) 모드
# =========================================================================
else:
    st.title("🖥️ 종합 방재실 안전관제 최고 대시보드")
    
    if "admin_authenticated" not in st.session_state: st.session_state["admin_authenticated"] = False
    
    if not st.session_state["admin_authenticated"]:
        with st.form("admin_auth_form"):
            if st.form_submit_button("🔑 관제 센터 시스템 기동") and verify_password(st.text_input("암호", type="password")):
                st.session_state["admin_authenticated"] = True; st.rerun()
    else:
        st.success("🟢 관리자 인증 완료")
        if st.button("🔒 로그아웃"): st.session_state["admin_authenticated"] = False; st.rerun()
        
        # 1. 비상 신고 및 점검 기록 출력
        col_data1, col_data2 = st.columns(2)
        with col_data1:
            st.subheader("🚨 비상 신고 접수 현황")
            st.dataframe(pd.read_csv(DB_SOS, encoding="utf-8-sig"), use_container_width=True)
        with col_data2:
            st.subheader("📋 현장 점검 기록")
            st.dataframe(pd.read_csv(DB_LOG, encoding="utf-8-sig"), use_container_width=True)
        
        st.divider()
        
        # 2. 현장 촬영 사진 보관소 (현장 작업자가 찍은 사진 확인)
        st.subheader("🖼️ 현장 촬영 사진 보관소 (종합 방재실 검토)")
        if os.path.exists("uploads"):
            files = [f for f in os.listdir("uploads") if f.endswith(".jpg")]
            if files:
                col_img_list, col_img_view = st.columns([1, 2])
                with col_img_list:
                    selected_img = st.selectbox("확인할 현장 사진 선택", sorted(files, reverse=True))
                with col_img_view:
                    st.image(f"uploads/{selected_img}", caption=f"현장 촬영 데이터: {selected_img}", use_container_width=True)
            else:
                st.info("현재 서버에 업로드된 현장 사진 데이터가 없습니다.")
        else:
            st.warning("사진 저장 디렉토리가 존재하지 않습니다.")

        # 3. 데이터 초기화 버튼
        if st.button("🔄 시스템 전체 로그 및 사진 데이터 초기화"):
            init_databases(force=True)
            if os.path.exists("uploads"):
                for f in os.listdir("uploads"): os.remove(os.path.join("uploads", f))
            st.warning("모든 데이터가 초기화되었습니다.")
            st.rerun()
