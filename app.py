import streamlit as st
from streamlit_js_eval import get_geolocation
import pandas as pd
from datetime import datetime, timedelta
import os
import time
from io import BytesIO
from PIL import Image

# [1] 🖥️ 웹페이지 기본 설정 (화면을 꽉 채우기 위해 wide 레이아웃으로 설정)
st.set_page_config(page_title="스마트 공장 안전관리 시스템", layout="wide")

# --- [🎨 화면을 빈틈없이 꽉 채우는 프리미엄 CSS 테마 스타일링] ---
st.markdown("""
    <style>
    .stApp { background-color: #f1f5f9; color: #1e293b; font-family: 'Noto Sans KR', sans-serif; }
    .main-title-banner {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 24px; border-radius: 16px; color: white; margin-bottom: 30px;
        box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.3);
    }
    .content-card {
        background-color: #ffffff; border: 1px solid #e2e8f0; padding: 25px; border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); margin-bottom: 20px; height: 100%;
    }
    .sos-container button {
        background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%) !important;
        color: white !important; font-size: 22px !important; font-weight: 800 !important;
        padding: 20px 0px !important; width: 100% !important; border-radius: 14px !important; border: none !important;
        box-shadow: 0px 8px 20px rgba(239, 68, 68, 0.4) !important; transition: all 0.2s ease-in-out;
    }
    .sos-container button:hover { transform: scale(1.02); box-shadow: 0px 10px 25px rgba(239, 68, 68, 0.5) !important; }
    .siren-alert {
        background-color: #fef2f2; border: 2px solid #ef4444; padding: 18px; border-radius: 12px;
        animation: blink 1.5s infinite; color: #b91c1c; font-weight: 800; font-size: 16px; margin-bottom: 25px;
        text-align: center; box-shadow: 0 4px 12px rgba(239, 68, 68, 0.1);
    }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.6; } 100% { opacity: 1; } }
    div[data-testid="stRadio"] p { display: none; }
    div[data-testid="stRadio"] div[role="radiogroup"] {
        display: flex; flex-direction: row; gap: 15px; width: 100%; margin-bottom: 25px;
    }
    div[data-testid="stRadio"] label {
        flex: 1; background-color: #e2e8f0 !important; border: 2px solid #cbd5e1 !important;
        padding: 15px 20px !important; border-radius: 12px !important; font-size: 18px !important; font-weight: 700 !important;
        color: #334155 !important; text-align: center !important; cursor: pointer !important; transition: all 0.2s ease;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);
    }
    div[data-testid="stRadio"] label[data-checked="true"] {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important; color: white !important;
        border-color: #1d4ed8 !important; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- [🔒 암호학 자격 증명 데이터 설정] ---
ADMIN_PASSWORD_PLAIN = "admin1234"

def verify_password(input_password):
    return input_password.strip() == ADMIN_PASSWORD_PLAIN.strip()

# --- [화학물질 데이터베이스] ---
CHEMICALS = {
    "TOLUENE": {
        "name": "톨루엔 (Toluene)","cas_no": "108-88-3",
        "symbol": "🔥 고인화성 / ⚠️ 급성·만성독성 / 🎗️ 생식독성",
        "danger": "• 고인화성 액체 및 증기...\n• 흡입 시 중추신경계 억제...\n• 장기 노출 시 태아 손상...",
        "emergency": "1. [흡입] 즉시 신선한 공기...\n2. [피부] 오염된 의복 제거...\n3. [눈] 15분 이상 세척...\n4. [화재] 포말/CO2/건분말."
    },
    "ACETONE": {
        "name": "아세톤 (Acetone)", "cas_no": "67-64-1",
        "symbol": "🔥 극인화성 / 👁️ 심한 눈 자극 / 💤 마취성",
        "danger": "• 극히 인화성이 높은 휘발성...\n• 증기 흡입 시 졸음, 구토...\n• 눈 접촉 시 통증.",
        "emergency": "1. 신선한 공기 이동...\n2. 눈 15분 세척...\n3. 대형 화재 용기 냉각."
    },
    "SULFURIC_ACID": {
        "name": "황산 (Sulfuric Acid)", "cas_no": "7664-93-9",
        "symbol": "💀 급성독성 / 🧪 부식성 / 👁️ 실명위험",
        "danger": "• 피부 접촉 시 화학 화상...\n• 흡입 시 폐부종...\n• 눈 접촉 시 실명.",
        "emergency": "1. 피부 20분 이상 세척...\n2. 눈 30분 세척 및 진료...\n3. 물과 혼합 시 발열 주의."
    },
    "SODIUM_HYDROXIDE": {"name": "수산화나트륨","cas_no":"1310-73-2","symbol":"🧪 부식성 / 👁️ 실명위험","danger":"• 피부/눈 손상\n• 금속 부식","emergency":"1. 흐르는 물에 세척\n2. 산소 공급"},
    "BENZENE": {"name":"벤젠 (Benzene)","cas_no":"71-43-2","symbol":"🔥 고인화성 / 🎗️ 1급 발암물질 / 💀 독성","danger":"• 백혈병 유발 가능...\n• 조혈 장애...\n• 흡입 위험.","emergency":"1. 안전지역 대피(보호구 필수)\n2. 물/비누 세척 후 병원"},
    "ETHYLENE_OXIDE": {"name":"산화에틸렌 (EO)","cas_no":"75-21-8","symbol":"💥 폭발성 가스 / 🎗️ 발암성","danger":"• 폭발 위험 매우 높음","emergency":"1. 안전지역 대피"},
    "AMMONIA": {"name":"암모니아 (Ammonia)","cas_no":"7664-41-7","symbol":"☣️ 독성 가스 / 🧪 강한 부식성","danger":"• 호흡기 화상","emergency":"1. 신선한 공기 이동"},
    "1_3_BUTADIENE": {"name":"1,3-부타디엔","cas_no":"106-99-0","symbol":"🔥 극인화성 가스 / 🎗️ 발암성","danger":"• 쉽게 점화","emergency":"1. 신선한 공기 이동"},
    "ACRYLONITRILE": {"name":"아크릴로니트릴","cas_no":"107-13-1","symbol":"🔥 고인화성 / 💀 고독성","danger":"• 체내 시안화물로 분해","emergency":"1. 송기마스크 착용 대피"}
}

# --- [데이터 저장 파일/폴더 정의] ---
DB_LOG = "inspection_log.csv"
DB_SOS = "sos_log.csv"
DB_PHOTO = "photo_log.csv"
PHOTO_DIR = "photos"

LOG_COLS = ["일시", "점검자", "점검물질", "상태", "특이사항"]
SOS_COLS = ["일시", "위치_위도", "위치_경도", "상태"]
PHOTO_COLS = ["일시", "위치_위도", "위치_경도", "파일명"]

def init_databases(force=False):
    os.makedirs(PHOTO_DIR, exist_ok=True)
    if force or not os.path.exists(DB_LOG):
        pd.DataFrame(columns=LOG_COLS).to_csv(DB_LOG, index=False, encoding="utf-8-sig")
    if force or not os.path.exists(DB_SOS):
        pd.DataFrame(columns=SOS_COLS).to_csv(DB_SOS, index=False, encoding="utf-8-sig")
    if force or not os.path.exists(DB_PHOTO):
        pd.DataFrame(columns=PHOTO_COLS).to_csv(DB_PHOTO, index=False, encoding="utf-8-sig")

init_databases()

# --- [시간 (KST)] ---
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
photo_df = pd.read_csv(DB_PHOTO, encoding="utf-8-sig")
active_sos = sos_df[sos_df["상태"] == "🚨 미조치 긴급상황"]

if not active_sos.empty:
    st.markdown(f'<div class="siren-alert">⚠️ [종합방재실 비상 경보] 현재 공장 내에 조치되지 않은 SOS 긴급 상황이 발생했습니다! ({len(active_sos)}건 대기 중)</div>', unsafe_allow_html=True)

# --- [상단 빈 영역에 기본 문구 채움] ---
with st.container():
    st.markdown("""
        <div class="content-card">
            <strong>안내</strong> · 상단 공지 및 요약 정보가 이 영역에 표시됩니다. 현재 표시할 공지는 없습니다.
        </div>
    """, unsafe_allow_html=True)
with st.container():
    st.markdown("""
        <div class="content-card">
            <strong>안내</strong> · 시스템 사용 팁과 QR 연동 도움말이 이 영역에 표시됩니다. 필요 시 관리자에 문의하세요.
        </div>
    """, unsafe_allow_html=True)

# --- [사이드바 권한] ---
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
            st.error("🚨 [SOS 신호가 종합방재실 관제 센터로 즉시 송신되었습니다]")
        else:
            st.caption("버튼을 누르면 현재 기기의 GPS 좌표가 함께 전송됩니다.")
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
        st.caption("원하는 기능을 선택하세요.")
        selected_menu = st.radio("메뉴선택", menu_options, index=init_menu_idx, horizontal=True)
        st.markdown("<hr style='margin-top:0; margin-bottom:25px; border:1px solid #cbd5e1;'>", unsafe_allow_html=True)

        if selected_menu == "📍 실시간 내 위치 지침 모듈":
            st.subheader("📍 현재 내 단말기 GPS 정보")
            loc = get_geolocation()
            if loc:
                curr_lat, curr_lon = loc['coords']['latitude'], loc['coords']['longitude']
                st.info(f"정밀 위경도 측정 완료: 위도 {curr_lat:.5f}, 경도 {curr_lon:.5f}")
                st.map(pd.DataFrame({'lat': [curr_lat], 'lon': [curr_lon]}), zoom=15)
            else:
                st.warning("🔄 위치 수집 서버와 통신 중이거나 단말기 GPS가 비활성화되어 가상 고정 좌표 지도를 렌더링합니다.")
                st.map(pd.DataFrame({'lat': [35.5416], 'lon': [129.2555]}), zoom=14)

            st.subheader("📸 현장 이상 부위 사진 촬영 공정 전송")
            cam = st.camera_input("스마트폰 카메라 구동")
            if cam:
                # 사진 저장
                try:
                    img = Image.open(BytesIO(cam.getvalue()))
                    # 파일명: YYYYMMDD_HHMMSS_uuid처럼 유니크하게(여기서는 타임스탬프)
                    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
                    filename = f"{ts}.jpg"
                    save_path = os.path.join(PHOTO_DIR, filename)
                    img.save(save_path, format="JPEG", quality=90)
                    # 위치
                    loc = get_geolocation()
                    plat = loc['coords']['latitude'] if loc else None
                    plon = loc['coords']['longitude'] if loc else None
                    # 로그 저장
                    now_str = now_kst.strftime("%Y-%m-%d %H:%M:%S")
                    photo_df = pd.read_csv(DB_PHOTO, encoding="utf-8-sig")
                    new_photo = pd.DataFrame([[now_str, plat, plon, filename]], columns=PHOTO_COLS)
                    pd.concat([photo_df, new_photo], ignore_index=True).to_csv(DB_PHOTO, index=False, encoding="utf-8-sig")
                    st.success("✨ 사진 저장 및 관제 서버 동기화 완료! 관리자 화면에서 확인할 수 있습니다.")
                except Exception as e:
                    st.error(f"사진 저장 중 오류가 발생했습니다: {e}")
            else:
                st.caption("사진 촬영이 필요 없으면 이 단계를 건너뛸 수 있습니다.")

        elif selected_menu == "📚 화학물질 QR 안전 자료실":
            st.subheader("📋 공장 취급 유해 화학물질 정보 명세")
            chem_options = {info["name"]: key for key, info in CHEMICALS.items()}
            default_index = 0
            if qr_chem and qr_chem in CHEMICALS:
                default_index = chem_list.index(qr_chem)
                st.success(f"🔍 QR 스캔 링크 연동 성공: {CHEMICALS[qr_chem]['name']}")
            else:
                st.caption("QR로 진입하지 않은 경우 목록에서 물질을 직접 선택하세요.")
            selected_name = st.selectbox("🔍 유해화학물질 선택", list(chem_options.keys()), index=default_index, placeholder="물질을 선택하면 상세 정보가 표시됩니다.")
            if selected_name:
                chem_key = chem_options[selected_name]
                chem_data = CHEMICALS[chem_key]
                st.markdown(f"### 🧪 {chem_data['name']}")
                st.error(f"위험 기호: {chem_data['symbol']}")
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
                    note = st.text_area("📝 설비 특이사항 및 점검 코멘트", placeholder="현장 상태, 이상 징후, 즉시 조치 사항 등을 자세히 입력하세요.")
                    submit_btn = st.form_submit_button("📁 점검 일지 원격 서버 전송")
                    if submit_btn and inspector:
                        now_str = now_kst.strftime("%Y-%m-%d %H:%M:%S")
                        new_log = pd.DataFrame([[now_str, inspector, chem_data['name'], status, note]], columns=LOG_COLS)
                        log_df = pd.read_csv(DB_LOG, encoding="utf-8-sig")
                        pd.concat([log_df, new_log], ignore_index=True).to_csv(DB_LOG, index=False, encoding="utf-8-sig")
                        st.success("📥 데이터베이스 서버 연동 완결! 점검 일지가 성공적으로 등록되었습니다.")
                    elif submit_btn and not inspector:
                        st.error("성명을 입력해야 전송됩니다.")
            else:
                st.info("상단의 선택 박스에서 물질을 선택하면 위험성·응급조치 정보가 여기 표시됩니다.")
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
        st.info("⏱️ 최고 보안 등급 유지를 위해 관리자 화면은 10분 후 자동 세션 로그아웃이 작동합니다.")
        
        with st.form("admin_auth_form"):
            passwd_input = st.text_input("🛡️ 방재실 마스터 통제 패스워드 입력", type="password", placeholder="관리자 비밀번호를 입력하세요.")
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
            st.success(f"🟢 자동 로그아웃까지 남은 시간: {minutes_left}분 {seconds_left}초 (보안 이유로 새로고침 시 갱신)")
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
                st.caption("비상 상황이 접수되면 위치 좌표와 발생 시간이 여기에 표시됩니다.")
            else:
                st.warning(f"현재 {len(active_sos)}개의 비상 상황이 발생했습니다.")
                sos_map_data = active_sos.rename(columns={"위치_위도": "lat", "위치_경도": "lon"})
                st.map(sos_map_data, zoom=12)
                for index, row in active_sos.iterrows():
                    col_info, col_btn = st.columns([3, 1])
                    with col_info:
                        st.write(f"⏰ 발생시간: {row['일시']} | 좌표: {row['위치_위도']:.4f}, {row['위치_경도']:.4f}")
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
                st.caption("현장에서 점검이 등록되면 최신 항목이 목록 상단에 표시됩니다.")
            else:
                st.dataframe(current_logs.sort_values(by="일시", ascending=False), use_container_width=True)

        st.divider()
        st.subheader("📸 현장 사진 아카이브")
        st.caption("현장에서 촬영된 사진을 썸네일로 확인하고 개별/일괄 삭제할 수 있습니다. 최신순으로 표시됩니다.")

        # 최신순 데이터프레임
        photo_df = pd.read_csv(DB_PHOTO, encoding="utf-8-sig")
        if photo_df.empty:
            st.info("등록된 현장 사진이 없습니다.")
        else:
            photo_df_sorted = photo_df.sort_values(by="일시", ascending=False).reset_index(drop=True)

            # 일괄 삭제 버튼
            col_bulk_left, col_bulk_right = st.columns([4,1])
            with col_bulk_right:
                if st.button("🗑️ 전체 사진 일괄 삭제"):
                    # 파일 삭제
                    try:
                        for fn in photo_df_sorted["파일명"]:
                            fp = os.path.join(PHOTO_DIR, str(fn))
                            if os.path.exists(fp):
                                os.remove(fp)
                        # 로그 초기화
                        pd.DataFrame(columns=PHOTO_COLS).to_csv(DB_PHOTO, index=False, encoding="utf-8-sig")
                        st.warning("모든 사진과 기록이 삭제되었습니다.")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"일괄 삭제 중 오류: {e}")

            st.markdown("")  # 여백

            # 썸네일 그리드 표시 (한 줄에 3개)
            n_cols = 3
            rows = (len(photo_df_sorted) + n_cols - 1) // n_cols
            for r in range(rows):
                cols = st.columns(n_cols)
                for c in range(n_cols):
                    idx = r * n_cols + c
                    if idx >= len(photo_df_sorted):
                        continue
                    row = photo_df_sorted.iloc[idx]
                    fp = os.path.join(PHOTO_DIR, str(row["파일명"]))
                    with cols[c]:
                        box = st.container(border=True)
                        with box:
                            st.caption(f"🕒 {row['일시']}")
                            if os.path.exists(fp):
                                st.image(fp, use_container_width=True)
                            else:
                                st.error("파일을 찾을 수 없습니다.")
                            st.caption(f"📌 위치: {row['위치_위도'] if pd.notna(row['위치_위도']) else '-'}, {row['위치_경도'] if pd.notna(row['위치_경도']) else '-'}")
                            # 개별 삭제 버튼 (고유 키 필요)
                            if st.button("🗑️ 이 사진 삭제", key=f"del_{idx}"):
                                try:
                                    # 파일 삭제
                                    if os.path.exists(fp):
                                        os.remove(fp)
                                    # 로그에서 해당 행 제거 (파일명 기준)
                                    df_all = pd.read_csv(DB_PHOTO, encoding="utf-8-sig")
                                    df_all = df_all[df_all["파일명"] != row["파일명"]]
                                    df_all.to_csv(DB_PHOTO, index=False, encoding="utf-8-sig")
                                    st.success("사진이 삭제되었습니다.")
                                    time.sleep(0.5)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"삭제 중 오류: {e}")
