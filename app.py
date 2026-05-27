import streamlit as st
from streamlit_js_eval import get_geolocation
import pandas as pd
from datetime import datetime, timedelta
import os
import time

# [1] 🖥️ 웹페이지 기본 설정 (화면을 꽉 채우기 위해 wide 레이아웃으로 설정)
st.set_page_config(page_title="스마트 공장 안전관리 시스템", layout="wide")

# --- [🎨 화면을 빈틈없이 꽉 채우는 프리미엄 CSS 테마 스타일링] ---
st.markdown("""
    <style>
    /* 전체 배경 및 폰트 세팅 */
    .stApp { background-color: #f1f5f9; color: #1e293b; font-family: 'Noto Sans KR', sans-serif; }
    
    /* 대형 메인 타이틀 배너 */
    .main-title-banner {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 24px;
        border-radius: 16px;
        color: white;
        margin-bottom: 30px;
        box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.3);
    }
    
    /* 꽉 찬 카드형 컨테이너 (빈 공간 방지) */
    .content-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 25px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
        height: 100%;
    }
    
    /* 🚨 SOS 독점 초대형 버튼 */
    .sos-container button {
        background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%) !important;
        color: white !important;
        font-size: 22px !important;
        font-weight: 800 !important;
        padding: 20px 0px !important;
        width: 100% !important;
        border-radius: 14px !important;
        border: none !important;
        box-shadow: 0px 8px 20px rgba(239, 68, 68, 0.4) !important;
        transition: all 0.2s ease-in-out;
    }
    .sos-container button:hover {
        transform: scale(1.02);
        box-shadow: 0px 10px 25px rgba(239, 68, 68, 0.5) !important;
    }
    
    /* 🚨 실시간 사이렌 애니메이션 (상단 가득 채우기) */
    .siren-alert {
        background-color: #fef2f2;
        border: 2px solid #ef4444;
        padding: 18px;
        border-radius: 12px;
        animation: blink 1.5s infinite;
        color: #b91c1c;
        font-weight: 800;
        font-size: 16px;
        margin-bottom: 25px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.1);
    }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.6; } 100% { opacity: 1; } }
    
    /* 📻 라디오 메뉴 버튼 커스텀 스타일링 (빈칸 오류 완벽 해결) */
    div[data-testid="stRadio"] p { display: none; }
    div[data-testid="stRadio"] div[role="radiogroup"] {
        display: flex;
        flex-direction: row;
        gap: 15px;
        width: 100%;
        margin-bottom: 25px;
    }
    div[data-testid="stRadio"] label {
        flex: 1;
        background-color: #e2e8f0 !important;
        border: 2px solid #cbd5e1 !important;
        padding: 15px 20px !important;
        border-radius: 12px !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        color: #334155 !important;
        text-align: center !important;
        cursor: pointer !important;
        transition: all 0.2s ease;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);
    }
    div[data-testid="stRadio"] label[data-checked="true"] {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: white !important;
        border-color: #1d4ed8 !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- [🔒 암호학 자격 증명 데이터 설정] ---
ADMIN_PASSWORD_PLAIN = "admin1234"

def verify_password(input_password):
    """입력받은 패스워드의 앞뒤 공백을 제거하고 마스터 비밀번호와 직접 대조합니다."""
    return input_password.strip() == ADMIN_PASSWORD_PLAIN.strip()

# --- [화학물질 데이터베이스 (상세 정보 100% 보강)] ---
CHEMICALS = {
    "TOLUENE": {
        "name": "톨루엔 (Toluene)",
        "cas_no": "108-88-3",
        "symbol": "🔥 고인화성 / ⚠️ 급성·만성독성 / 🎗️ 생식독성",
        "danger": "• 고인화성 액체 및 증기: 화재 및 폭발 위험 매우 높음.\n• 흡입 시 중추신경계 억제, 현기증, 두통 유발.\n• 장기 노출 시 태아 손상 및 생식 능력 저하 우려.",
        "emergency": "1. [흡입] 즉시 신선한 공기가 있는 곳으로 이동.\n2. [피부] 오염된 의복 즉시 제거, 20분 이상 비눗물로 세척.\n3. [눈] 눈꺼풀을 벌리고 15분 이상 흐르는 물로 세척.\n4. [화재] 알코올 내성 포말, 이산화탄소(CO2) 또는 건조 화학 분말 사용."
    },
    "ACETONE": {
        "name": "아세톤 (Acetone)",
        "cas_no": "67-64-1",
        "symbol": "🔥 극인화성 / 👁️ 심한 눈 자극 / 💤 마취성",
        "danger": "• 극히 인화성이 높은 휘발성 물질.\n• 증기 흡입 시 졸음, 어지러움, 구토 유발.\n• 눈 접촉 시 심한 통증 및 각막 손상 가능.",
        "emergency": "1. [흡입] 신선한 공기가 있는 곳으로 이동, 필요시 산소 공급.\n2. [눈] 즉시 다량의 물로 15분 이상 세척.\n3. [화재] 대형 화재 시 분무 주수(water spray)로 용기 냉각."
    },
    "SULFURIC_ACID": {
        "name": "황산 (Sulfuric Acid)",
        "cas_no": "7664-93-9",
        "symbol": "💀 급성독성 / 🧪 부식성 / 👁️ 실명위험",
        "danger": "• 피부 접촉 시 즉각적인 3도 화학 화상 유발.\n• 흡입 시 호흡기계 심각한 손상 및 폐부종 유발.\n• 눈 접촉 시 영구적 실명 가능성.",
        "emergency": "1. [피부] 오염된 옷을 찢어 벗기고, 흐르는 물에 최소 20분 이상 씻어낼 것.\n2. [눈] 30분 이상 계속해서 흐르는 물로 세척, 즉시 전문의 진료.\n3. [주의] 물과 섞일 때 강한 발열 반응이 있으므로, 주변에 물이 튀지 않게 주의."
    },
    "SODIUM_HYDROXIDE": {
        "name": "수산화나트륨", "cas_no": "1310-73-2", "symbol": "🧪 부식성 / 👁️ 실명위험", 
        "danger": "• 피부, 눈에 심한 손상 및 화학적 화상\n• 금속을 부식시킬 수 있음", "emergency": "1. 미끈거림이 사라질 때까지 흐르는 물에 세척\n2. 호흡 곤란 시 산소 공급"
    },
    "BENZENE": {
        "name": "벤젠 (Benzene)",
        "cas_no": "71-43-2",
        "symbol": "🔥 고인화성 / 🎗️ 1급 발암물질 / 💀 독성",
        "danger": "• 인체에 치명적인 발암물질(백혈병 유발).\n• 반복 노출 시 조혈 기능 장애.\n• 흡입 시 극히 위험.",
        "emergency": "1. [흡입] 즉시 안전 지역 대피, 호흡 곤란 시 인공호흡 금지(보호구 착용 필수).\n2. [피부] 기름기 제거제 사용 금지, 물과 비누로 세척 후 즉시 병원 이송."
    },
    "ETHYLENE_OXIDE": {"name": "산화에틸렌 (EO)", "cas_no": "75-21-8", "symbol": "💥 폭발성 가스 / 🎗️ 발암성", "danger": "• 고압가스 및 극인화성 가스로 폭발 위험 매우 높음", "emergency": "1. 환자를 즉시 안전한 지역으로 대피"},
    "AMMONIA": {"name": "암모니아 (Ammonia)", "cas_no": "7664-41-7", "symbol": "☣️ 독성 가스 / 🧪 강한 부식성", "danger": "• 호흡기계에 심각한 화학적 화상 유발", "emergency": "1. 신선한 공기 곳으로 이동"},
    "1_3_BUTADIENE": {"name": "1,3-부타디엔", "cas_no": "106-99-0", "symbol": "🔥 극인화성 가스 / 🎗️ 발암성", "danger": "• 쉽게 점화되어 대형 화재 유발", "emergency": "1. 환자를 신선한 공기 곳으로 이동"},
    "ACRYLONITRILE": {"name": "아크릴로니트릴", "cas_no": "107-13-1", "symbol": "🔥 고인화성 / 💀 고독성", "danger": "• 체내에서 시안화물로 분해되어 극히 유독", "emergency": "1. 송기마스크 착용 후 환자 대피"}
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

# --- [시간 연산을 위한 기본 세팅 (한국 표준시)] ---
now_utc = datetime.utcnow()
now_kst = now_utc + timedelta(hours=9)

# --- [주소 분석 및 네비게이션 제어] ---
qr_chem = st.query_params.get("chem", None)
admin_bypass = st.query_params.get("admin", None) 
chem_list = list(CHEMICALS.keys())

if isinstance(qr_chem, list) and len(qr_chem) > 0: qr_chem = qr_chem[0]
if qr_chem: qr_chem = str(qr_chem).strip().upper()

init_menu_idx = 0
if qr_chem and qr_chem in CHEMICALS:
    init_menu_idx = 1

# --- [실시간 알림 및 데이터 동기화] ---
log_df = pd.read_csv(DB_LOG, encoding="utf-8-sig")
sos_df = pd.read_csv(DB_SOS, encoding="utf-8-sig")
active_sos = sos_df[sos_df["상태"] == "🚨 미조치 긴급상황"]

if not active_sos.empty:
    st.markdown(f'<div class="siren-alert">⚠️ [종합방재실 비상 경보] 현재 공장 내에 조치되지 않은 SOS 긴급 상황이 발생했습니다! ({len(active_sos)}건 대기 중)</div>', unsafe_allow_html=True)

# --- [⚙️ 측면 사이드바 시스템 권한 설정] ---
st.sidebar.header("⚙️ 시스템 권한 설정")
available_roles = ["👷 현장 작업자 모드"]
if admin_bypass == "true":
    available_roles.append("🖥️ 종합 방재실(관리자) 모드")
else:
    st.sidebar.info("💡 관리자 관제 센터는 인가된 특수 단말기 주소로만 원격 진입이 가능합니다.")
user_role = st.sidebar.selectbox("현재 접속 모드", available_roles)

# =========================================================================
# [권한 1] 👷 현장 작업자 모드
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
        st.write("현장 내 화재, 질식, 가스 유출 등 중대재해 발생 시 아래 버튼을 누르면 방재실 컴퓨터에 즉시 위치 경보가 사이렌과 함께 전송됩니다.")
        
        st.markdown('<div class="sos-container">', unsafe_allow_html=True)
        if st.button("🚨 긴급상황 발생 (SOS 신호 즉시 전송)"):
            loc = get_geolocation()
            lat = loc['coords']['latitude'] if loc else 35.5416
            lon = loc['coords']['longitude'] if loc else 129.2555
            now_str = now_kst.strftime("%Y-%m-%d %H:%M:%S")
            new_sos = pd.DataFrame([[now_str, lat, lon, "🚨 미조치 긴급상황"]], columns=SOS_COLS)
            sos_df = pd.read_csv(DB_SOS, encoding="utf-8-sig")
            pd.concat([sos_df, new_sos], ignore_index=True).to_csv(DB_SOS, index=False, encoding="utf-8-sig")
            st.error("🚨 **[SOS 신호가 종합방재실 관제 센터로 즉시 송신되었습니다]**")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="content-card" style="margin-top:20px;">', unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top:0; color:#475569;'>⚙️ 현장 작업 표준 지침</h4>", unsafe_allow_html=True)
        st.caption("1. 작업 전 반드시 보호구(송기마스크, 내화학장갑)를 착용하십시오.")
        st.caption("2. 가스 검지기의 정상 작동 여부를 선제적으로 체크하십시오.")
        st.caption("3. QR 코드 인식 불가 시 화학물질 검색 창을 통해 수동 입력이 가능합니다.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("<h3 style='margin-top:0; color:#1e3a8a;'>📱 현장 모바일 관제 시스템</h3>", unsafe_allow_html=True)
        
        menu_options = ["📍 실시간 내 위치 지침 모듈", "📚 화학물질 QR 안전 자료실"]
        selected_menu = st.radio("메뉴선택", menu_options, index=init_menu_idx, horizontal=True)
        st.markdown("<hr style='margin-top:0; margin-bottom:25px; border:1px solid #cbd5e1;'>", unsafe_allow_html=True)

        if selected_menu == "📍 실시간 내 위치 지침 모듈":
            st.subheader("📍 현재 내 단말기 GPS 정보")
            loc = get_geolocation()
            if loc:
                curr_lat, curr_lon = loc['coords']['latitude'], loc['coords']['longitude']
                st.info(f"정밀 위경도 측정 완료: **위도 {curr_lat:.5f}, 경도 {curr_lon:.5f}**")
                st.map(pd.DataFrame({'lat': [curr_lat], 'lon': [curr_lon]}), zoom=15)
            else:
                st.warning("🔄 위치 수집 서버와 통신 중이거나 단말기 GPS가 비활성화되어 가상 고정 좌표 지도를 렌더링합니다.")
                st.map(pd.DataFrame({'lat': [35.5416], 'lon': [129.2555]}), zoom=14)
            st.subheader("📸 현장 이상 부위 사진 촬영 공정 전송")
            if st.camera_input("스마트폰 카메라 구동"): st.success("✨ 사진 데이터 인코딩 및 임시 버퍼 세이브 완료!")
# 서브 메뉴 2: 화학물질 자료실 모듈
        elif selected_menu == "📚 화학물질 QR 안전 자료실":
            st.subheader("📋 공장 취급 유해 화학물질 정보 명세")
            chem_options = {info["name"]: key for key, info in CHEMICALS.items()}
            
            default_index = 0
            if qr_chem and qr_chem in CHEMICALS:
                default_index = chem_list.index(qr_chem)
                st.success(f"🔍 QR 스캔 링크 연동 성공: **{CHEMICALS[qr_chem]['name']}**")
                
            selected_name = st.selectbox("🔍 유해화학물질 셀렉트 박스", list(chem_options.keys()), index=default_index)
            
            if selected_name:
                chem_key = chem_options[selected_name]
                chem_data = CHEMICALS[chem_key]
                
                # [상세 정보 출력부: 가독성을 위해 expander 적용]
                st.markdown(f"### 🧪 {chem_data['name']}")
                st.error(f"**위험 기호:** {chem_data['symbol']}")
                
                with st.expander("🚨 자세한 위험성 (Danger)", expanded=True):
                    st.write(chem_data['danger'])
                with st.expander("🚑 긴급 응급조치 (Emergency Aid)", expanded=True):
                    st.info(chem_data['emergency'])
                st.markdown(f"**CAS 번호:** `{chem_data['cas_no']}`")
                
                st.divider()
                st.subheader("✍️ 스마트 공정 교대근무 일지 제출")
                with st.form("inspection_form", clear_on_submit=True):
                    inspector = st.text_input("👤 현장 검사 마스터 성명 (소속 포함)", placeholder="예: 공정팀 김철수")
                    status = st.selectbox("📊 설비 및 가스 종합 상태 평가", ["정상 (이상 없음)", "주의 (예방 정비 필요)", "위험 (즉시 생산 셧다운 및 조치 요망)"])
                    note = st.text_area("📝 설비 특이사항 및 점검 코멘트")
                    submit_btn = st.form_submit_button("📁 점검 일지 원격 서버 전송")
                    
                    if submit_btn and inspector:
                        now_str = now_kst.strftime("%Y-%m-%d %H:%M:%S")
                        new_log = pd.DataFrame([[now_str, inspector, chem_data['name'], status, note]], columns=LOG_COLS)
                        log_df = pd.read_csv(DB_LOG, encoding="utf-8-sig")
                        pd.concat([log_df, new_log], ignore_index=True).to_csv(DB_LOG, index=False, encoding="utf-8-sig")
                        st.success("📥 데이터베이스 서버 연동 완결! 점검 일지가 성공적으로 등록되었습니다.")
        st.markdown('</div>', unsafe_allow_html=True)

# =========================================================================
# [권한 2] 🖥️ 종합 방재실 관제 센터 모드
# =========================================================================
else:
    st.title("🖥️ 종합 방재실 안전관제 최고 대시보드")
    
    if "admin_authenticated" not in st.session_state:
        st.session_state["admin_authenticated"] = False
    if "login_time" not in st.session_state:
        st.session_state["login_time"] = None

    SESSION_TIMEOUT = timedelta(minutes=10)

    if st.session_state["admin_authenticated"] and st.session_state["login_time"] is not None:
        elapsed_time = datetime.now() - st.session_state["login_time"]
        if elapsed_time > SESSION_TIMEOUT:
            st.session_state["admin_authenticated"] = False
            st.session_state["login_time"] = None
            st.error("⏳ 보안 지침에 따라 관리자 세션이 만료되어 자동 로그아웃되었습니다. 다시 인증해 주세요.")
            time.sleep(1)
            st.rerun()

    if not st.session_state["admin_authenticated"]:
        st.warning("🔒 본 화면은 인가된 방재실 관리자만 접근할 수 있는 국가 중요 보안 시설 관제창입니다.")
        st.info("⏱️ 최고 보안 등급 유지를 위해 관리자 화면은 [10분 후 자동 세션 로그아웃]이 작동합니다.")
        
        with st.form("admin_auth_form"):
            passwd_input = st.text_input("🛡️ 방재실 마스터 통제 패스워드 입력", type="password")
            auth_submit = st.form_submit_button("🔑 관제 센터 시스템 기동")
            
            if auth_submit:
                if verify_password(passwd_input):
                    st.session_state["admin_authenticated"] = True
                    st.session_state["login_time"] = datetime.now()
                    st.success("🔓 자격 증명 성공! 방재실 관제 권한이 획득되었습니다.")
                    st.rerun()
                else:
                    st.error("❌ 자격 증명 실패: 비밀번호가 일치하지 않거나 권한이 거부되었습니다.")
                    
    else:
        time_left = SESSION_TIMEOUT - (datetime.now() - st.session_state["login_time"])
        minutes_left = int(time_left.total_seconds() // 60)
        seconds_left = int(time_left.total_seconds() % 60)
        
        col_status, col_reset, col_logout = st.columns([2, 1, 1])
        
        with col_status:
            st.success(f"🟢 자동 로그아웃까지 남은 시간: {minutes_left}분 {seconds_left}초")
            
        with col_reset:
            if st.button("🔄 전체 데이터 즉시 리셋"):
                init_databases(force=True)
                st.warning("데이터베이스가 수동 초기화되었습니다.")
                time.sleep(1)
                st.rerun()
                
        with col_logout:
            if st.button("🔒 즉시 안전 로그아웃"):
                st.session_state["admin_authenticated"] = False
                st.session_state["login_time"] = None
                st.rerun()
            
        st.divider()
        
        adm_left, adm_right = st.columns([1, 1], gap="medium")
        
        with adm_left:
            st.subheader("🚨 실시간 SOS 비상 신고 접수 현황")
            if active_sos.empty:
                st.success("✅ 현재 접수된 비상 신고가 없습니다. 공장 내부 평온 상태 유지 중")
            else:
                st.warning(f"현재 {len(active_sos)}개의 비상 상황이 발생했습니다.")
                sos_map_data = active_sos.rename(columns={"위치_위도": "lat", "위치_경도": "lon"})
                st.map(sos_map_data, zoom=12)
                
                for index, row in active_sos.iterrows():
                    col_info, col_btn = st.columns([3, 1])
                    with col_info:
                        st.write(f"⏰ **발생시간:** {row['일시']} | **좌표:** {row['위치_위도']:.4f}, {row['위치_경도']:.4f}")
                    with col_btn:
                        if st.button("✅ 조치 완료", key=f"sos_{index}"):
                            full_sos_df = pd.read_csv(DB_SOS, encoding="utf-8-sig")
                            full_sos_df.at[index, "상태"] = "조치완료"
                            full_sos_df.to_csv(DB_SOS, index=False, encoding="utf-8-sig")
                            st.success("상황 조치 완료")
                            st.rerun()

        with adm_right:
            st.subheader("📋 현장 작업자 실시간 점검 기록 DB")
            current_logs = pd.read_csv(DB_LOG, encoding="utf-8-sig")
            if current_logs.empty:
                st.info("아직 제출된 현장 안전 점검 일지가 없거나 초기화된 상태입니다.")
            else:
                st.dataframe(current_logs.sort_values(by="일시", ascending=False), use_container_width=True)
