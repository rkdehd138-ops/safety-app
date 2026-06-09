import streamlit as st
from streamlit_js_eval import get_geolocation
import pandas as pd
from datetime import datetime, timedelta
import os
import time
from io import BytesIO
from PIL import Image
import math
import random

# [1] 🖥️ 기본 설정
st.set_page_config(page_title="스마트 공장 안전관리 시스템", layout="wide")

# --- CSS ---
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
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 20px; height: 100%;
}
.sos-container button {
  background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%) !important;
  color: white !important; font-size: 22px !important; font-weight: 800 !important;
  padding: 20px 0 !important; width: 100% !important; border-radius: 14px !important; border: none !important;
  box-shadow: 0 8px 20px rgba(239,68,68,.4) !important; transition: all .2s;
}
.sos-container button:hover { transform: scale(1.02); box-shadow: 0 10px 25px rgba(239,68,68,.5) !important; }
.siren-alert {
  background-color: #fef2f2; border: 2px solid #ef4444; padding: 18px; border-radius: 12px;
  animation: blink 1.5s infinite; color: #b91c1c; font-weight: 800; font-size: 16px; margin-bottom: 25px;
  text-align: center; box-shadow: 0 4px 12px rgba(239,68,68,.1);
}
@keyframes blink { 0% {opacity:1} 50% {opacity:.6} 100% {opacity:1} }
div[data-testid="stRadio"] p { display:none }
div[data-testid="stRadio"] div[role="radiogroup"] { display:flex; gap:15px; width:100%; margin-bottom:25px }
div[data-testid="stRadio"] label {
  flex:1; background:#e2e8f0 !important; border:2px solid #cbd5e1 !important; padding:15px 20px !important;
  border-radius:12px !important; font-size:18px !important; font-weight:700 !important; color:#334155 !important;
  text-align:center !important; cursor:pointer !important; transition:all .2s; box-shadow: inset 0 2px 4px rgba(0,0,0,.02);
}
div[data-testid="stRadio"] label[data-checked="true"] {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important; color:#fff !important; border-color:#1d4ed8 !important;
  box-shadow: 0 4px 12px rgba(37,99,235,.3) !important;
}
.badge {
  display:inline-block; padding:6px 10px; border-radius:999px; font-size:12px; font-weight:700;
  background:#e2e8f0; color:#334155; border:1px solid #cbd5e1; margin-bottom:8px;
}
.badge.primary { background:#dbeafe; color:#1e40af; border-color:#bfdbfe; }
</style>
""", unsafe_allow_html=True)

# --- 보안/상수 ---
ADMIN_PASSWORD_PLAIN = "admin1234"
def verify_password(input_password: str) -> bool:
    return input_password.strip() == ADMIN_PASSWORD_PLAIN.strip()

# --- 기본 공장 좌표(A공장): 스크린샷 근방 값 ---
A_FACTORY_LAT = 35.406982
A_FACTORY_LON = 129.283630

def jitter_around_factory(max_radius_m: float = 1000.0):
    r = random.random() ** 0.5 * max_radius_m
    theta = random.random() * 2 * math.pi
    dlat = r / 111_320.0
    dlon = r / (111_320.0 * math.cos(math.radians(A_FACTORY_LAT)))
    return A_FACTORY_LAT + dlat * math.cos(theta), A_FACTORY_LON + dlon * math.sin(theta)

def get_safe_location():
    lat = None; lon = None
    try:
        loc = get_geolocation()
        if loc and "coords" in loc and isinstance(loc["coords"], dict):
            c = loc["coords"]
            if ("latitude" in c) and ("longitude" in c) and c["latitude"] is not None and c["longitude"] is not None:
                lat = float(c["latitude"]); lon = float(c["longitude"])
    except Exception:
        pass
    if lat is None or lon is None:
        lat, lon = jitter_around_factory(1000.0)
        return lat, lon, True
    return lat, lon, False

# --- 화학물질 DB ---
CHEMICALS = {
    "TOLUENE":{"name":"톨루엔 (Toluene)","cas_no":"108-88-3","symbol":"🔥 고인화성 / ⚠️ 급성·만성독성 / 🎗️ 생식독성",
               "danger":"• 고인화성 액체 및 증기...\n• 흡입 시 중추신경계 억제...\n• 장기 노출 시 태아 손상...",
               "emergency":"1. [흡입] 즉시 신선한 공기...\n2. [피부] 오염된 의복 제거...\n3. [눈] 15분 이상 세척...\n4. [화재] 포말/CO2/건분말."},
    "ACETONE":{"name":"아세톤 (Acetone)","cas_no":"67-64-1","symbol":"🔥 극인화성 / 👁️ 심한 눈 자극 / 💤 마취성",
               "danger":"• 극히 인화성이 높은 휘발성...\n• 증기 흡입 시 졸음, 구토...\n• 눈 접촉 시 통증.",
               "emergency":"1. 신선한 공기 이동...\n2. 눈 15분 세척...\n3. 대형 화재 용기 냉각."},
    "SULFURIC_ACID":{"name":"황산 (Sulfuric Acid)","cas_no":"7664-93-9","symbol":"💀 급성독성 / 🧪 부식성 / 👁️ 실명위험",
                     "danger":"• 피부 접촉 시 화학 화상...\n• 흡입 시 폐부종...\n• 눈 접촉 시 실명.",
                     "emergency":"1. 피부 20분 이상 세척...\n2. 눈 30분 세척 및 진료...\n3. 물과 혼합 시 발열 주의."},
    "SODIUM_HYDROXIDE":{"name":"수산화나트륨","cas_no":"1310-73-2","symbol":"🧪 부식성 / 👁️ 실명위험",
                        "danger":"• 피부/눈 손상\n• 금속 부식","emergency":"1. 흐르는 물에 세척\n2. 산소 공급"},
    "BENZENE":{"name":"벤젠 (Benzene)","cas_no":"71-43-2","symbol":"🔥 고인화성 / 🎗️ 1급 발암물질 / 💀 독성",
               "danger":"• 백혈병 유발 가능...\n• 조혈 장애...\n• 흡입 위험.","emergency":"1. 안전지역 대피(보호구 필수)\n2. 물/비누 세척 후 병원"},
    "ETHYLENE_OXIDE":{"name":"산화에틸렌 (EO)","cas_no":"75-21-8","symbol":"💥 폭발성 가스 / 🎗️ 발암성",
                      "danger":"• 폭발 위험 매우 높음","emergency":"1. 안전지역 대피"},
    "AMMONIA":{"name":"암모니아 (Ammonia)","cas_no":"7664-41-7","symbol":"☣️ 독성 가스 / 🧪 강한 부식성",
               "danger":"• 호흡기 화상","emergency":"1. 신선한 공기 이동"},
    "1_3_BUTADIENE":{"name":"1,3-부타디엔","cas_no":"106-99-0","symbol":"🔥 극인화성 가스 / 🎗️ 발암성",
                     "danger":"• 쉽게 점화","emergency":"1. 신선한 공기 이동"},
    "ACRYLONITRILE":{"name":"아크릴로니트릴","cas_no":"107-13-1","symbol":"🔥 고인화성 / 💀 고독성",
                     "danger":"• 체내 시안화물로 분해","emergency":"1. 송기마스크 착용 대피"}
}

# --- 파일/폴더 ---
DB_LOG = "inspection_log.csv"
DB_SOS = "sos_log.csv"
DB_PHOTO = "photo_log.csv"
PHOTO_DIR = "photos"
LOG_COLS = ["일시","점검자","점검물질","상태","특이사항"]
SOS_COLS = ["일시","위치_위도","위치_경도","상태"]
PHOTO_COLS = ["일시","위치_위도","위치_경도","파일명"]

def init_databases(force=False):
    os.makedirs(PHOTO_DIR, exist_ok=True)
    if force or not os.path.exists(DB_LOG):
        pd.DataFrame(columns=LOG_COLS).to_csv(DB_LOG, index=False, encoding="utf-8-sig")
    if force or not os.path.exists(DB_SOS):
        pd.DataFrame(columns=SOS_COLS).to_csv(DB_SOS, index=False, encoding="utf-8-sig")
    if force or not os.path.exists(DB_PHOTO):
        pd.DataFrame(columns=PHOTO_COLS).to_csv(DB_PHOTO, index=False, encoding="utf-8-sig")

init_databases()

# --- 시간(KST) ---
now_kst = datetime.utcnow() + timedelta(hours=9)

# --- 쿼리 파라미터/메뉴 ---
qr_chem = st.query_params.get("chem", None)
admin_bypass = st.query_params.get("admin", None)
chem_list = list(CHEMICALS.keys())
if isinstance(qr_chem, list) and len(qr_chem) > 0: qr_chem = qr_chem[0]
if qr_chem: qr_chem = str(qr_chem).strip().upper()
init_menu_idx = 1 if (qr_chem and qr_chem in CHEMICALS) else 0

# --- 데이터 적재 ---
log_df = pd.read_csv(DB_LOG, encoding="utf-8-sig")
sos_df = pd.read_csv(DB_SOS, encoding="utf-8-sig")
photo_df = pd.read_csv(DB_PHOTO, encoding="utf-8-sig")
active_sos = sos_df[sos_df["상태"] == "🚨 미조치 긴급상황"]

if not active_sos.empty:
    st.markdown(f'<div class="siren-alert">⚠️ [종합방재실 비상 경보] 미조치 SOS {len(active_sos)}건 대기 중</div>', unsafe_allow_html=True)

# --- 사이드바 ---
st.sidebar.header("⚙️ 시스템 권한 설정")
available_roles = ["👷 현장 작업자 모드"]
if admin_bypass == "true":
    available_roles.append("🖥️ 종합 방재실(관리자) 모드")
else:
    st.sidebar.info("💡 관리자 관제는 인가된 단말기에서만 원격 진입 가능합니다.")
user_role = st.sidebar.selectbox("현재 접속 모드", available_roles)

# ========================== 현장 작업자 모드 ==========================
if user_role == "👷 현장 작업자 모드":
    st.markdown("""
        <div class="main-title-banner">
            <h1 style='margin:0;font-size:32px;'>🏭 스마트 안전관리 모바일 시스템</h1>
            <p style='margin:8px 0 0 0;opacity:0.9;font-size:16px;'>실시간 GPS 관제 · 현장 QR/MSDS · 사진 보고</p>
        </div>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([1,2], gap="large")

    with col_left:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("<h3 style='margin-top:0;color:#1e3a8a;'>🚨 긴급 구조 제어 센터</h3>", unsafe_allow_html=True)
        st.write("중대재해 발생 시 아래 버튼을 누르면 관제에 위치 경보가 전송됩니다.")
        st.markdown('<div class="sos-container">', unsafe_allow_html=True)
        if st.button("🚨 긴급상황 발생 (SOS 신호 즉시 전송)"):
            lat, lon, used_default = get_safe_location()
            now_str = now_kst.strftime("%Y-%m-%d %H:%M:%S")
            new_sos = pd.DataFrame([[now_str, lat, lon, "🚨 미조치 긴급상황"]], columns=SOS_COLS)
            sos_df = pd.read_csv(DB_SOS, encoding="utf-8-sig")
            pd.concat([sos_df, new_sos], ignore_index=True).to_csv(DB_SOS, index=False, encoding="utf-8-sig")
            if used_default:
                st.warning("권한 미동의로 기본 위치(A공장 근방)가 전송되었습니다.")
            st.error("🚨 SOS 신호가 관제 센터로 전송되었습니다.")
        else:
            st.caption("버튼을 누르면 현재 기기의 좌표(또는 A공장 기본 좌표)가 전송됩니다.")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="content-card" style="margin-top:20px;">', unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top:0;color:#475569;'>⚙️ 현장 작업 표준 지침</h4>", unsafe_allow_html=True)
        st.caption("1. 작업 전 보호구(송기마스크, 내화학장갑) 착용.")
        st.caption("2. 가스 검지기 정상 작동 여부 사전 점검.")
        st.caption("3. QR 인식 불가 시 검색창 수동 입력.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("<h3 style='margin-top:0;color:#1e3a8a;'>📱 현장 모바일 관제 시스템</h3>", unsafe_allow_html=True)

        # 라디오 메뉴 라벨을 명확하게: 메인(지도) / 자료실
        menu_options = ["🗺️ 메인 — 실시간 지도/위치", "📚 자료실 — 화학물질 QR/MSDS"]
        st.caption("메뉴 안내: 메인은 현재 단말기 위치 지도를 보여주고, 자료실은 QR·MSDS 정보를 확인합니다.")
        selected_menu = st.radio("기능 선택", menu_options, index=init_menu_idx, horizontal=True)

        # 현재 선택 배지
        if selected_menu.startswith("🗺️"):
            st.markdown('<span class="badge primary">현재 모듈: 메인(지도)</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="badge">현재 모듈: 자료실</span>', unsafe_allow_html=True)

        st.markdown("<hr style='margin-top:8px;margin-bottom:25px;border:1px solid #cbd5e1;'>", unsafe_allow_html=True)

        if selected_menu.startswith("🗺️"):  # 메인 — 지도
            st.subheader("📍 현재 좌표")
            lat, lon, used_default = get_safe_location()
            if used_default:
                st.info(f"A공장 기준 좌표 사용: 위도 {lat:.6f}, 경도 {lon:.6f} (권한 거부 또는 센서 실패)")
            else:
                st.success(f"정밀 위경도 측정 완료: 위도 {lat:.6f}, 경도 {lon:.6f}")
            st.map(pd.DataFrame({'lat':[lat], 'lon':[lon]}), zoom=15)

            st.subheader("📸 현장 이상 부위 사진 촬영 및 전송")
            try:
                cam = st.camera_input("스마트폰 카메라 구동")
            except Exception:
                cam = None
            if cam:
                try:
                    img = Image.open(BytesIO(cam.getvalue()))
                    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
                    filename = f"{ts}.jpg"
                    save_path = os.path.join(PHOTO_DIR, filename)
                    img.save(save_path, format="JPEG", quality=90)
                    plat, plon, _ = get_safe_location()
                    now_str = now_kst.strftime("%Y-%m-%d %H:%M:%S")
                    photo_df = pd.read_csv(DB_PHOTO, encoding="utf-8-sig")
                    new_photo = pd.DataFrame([[now_str, plat, plon, filename]], columns=PHOTO_COLS)
                    pd.concat([photo_df, new_photo], ignore_index=True).to_csv(DB_PHOTO, index=False, encoding="utf-8-sig")
                    st.success("✨ 사진 저장 및 관제 동기화 완료! 관리자 화면에서 확인 가능.")
                except Exception as e:
                    st.error(f"사진 저장 중 오류: {e}")
            else:
                st.caption("카메라 권한이 없거나 촬영을 취소한 경우에도 오류 없이 건너뜁니다.")

        else:  # 자료실 — 화학물질
            st.subheader("📋 공장 취급 유해 화학물질 정보 명세")
            chem_options = {info["name"]: key for key, info in CHEMICALS.items()}
            default_index = chem_list.index(qr_chem) if (qr_chem and qr_chem in CHEMICALS) else 0
            if qr_chem and qr_chem in CHEMICALS:
                st.success(f"🔍 QR 연동 성공: {CHEMICALS[qr_chem]['name']}")
            else:
                st.caption("QR 없이 진입한 경우 목록에서 물질을 선택하세요.")
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
                    status = st.selectbox("📊 설비 및 가스 종합 상태 평가", ["정상 (이상 없음)","주의 (예방 정비 필요)","위험 (즉시 생산 셧다운 및 조치 요망)"])
                    note = st.text_area("📝 설비 특이사항 및 점검 코멘트", placeholder="현장 상태, 이상 징후, 즉시 조치 사항 등을 자세히 입력하세요.")
                    submit_btn = st.form_submit_button("📁 점검 일지 원격 서버 전송")
                    if submit_btn and inspector:
                        now_str = now_kst.strftime("%Y-%m-%d %H:%M:%S")
                        new_log = pd.DataFrame([[now_str, inspector, chem_data['name'], status, note]], columns=LOG_COLS)
                        log_df = pd.read_csv(DB_LOG, encoding="utf-8-sig")
                        pd.concat([log_df, new_log], ignore_index=True).to_csv(DB_LOG, index=False, encoding="utf-8-sig")
                        st.success("📥 점검 일지가 등록되었습니다.")
                    elif submit_btn and not inspector:
                        st.error("성명을 입력해야 전송됩니다.")
        st.markdown('</div>', unsafe_allow_html=True)

# ========================== 관리자 모드 ==========================
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
            st.error("⏳ 보안 지침에 따라 관리자 세션이 만료되어 자동 로그아웃되었습니다.")
            time.sleep(1); st.rerun()

    if not st.session_state["admin_authenticated"]:
        st.warning("🔒 본 화면은 인가된 방재실 관리자만 접근할 수 있습니다.")
        st.info("⏱️ 10분 자동 세션 로그아웃이 작동합니다.")
        with st.form("admin_auth_form"):
            passwd_input = st.text_input("🛡️ 방재실 마스터 통제 패스워드 입력", type="password", placeholder="관리자 비밀번호를 입력하세요.")
            auth_submit = st.form_submit_button("🔑 관제 센터 시스템 기동")
            if auth_submit:
                if verify_password(passwd_input):
                    st.session_state["admin_authenticated"] = True
                    st.session_state["login_time"] = datetime.now()
                    st.success("🔓 자격 증명 성공! 방재실 관제 권한 획득.")
                    st.rerun()
                else:
                    st.error("❌ 자격 증명 실패: 비밀번호가 일치하지 않습니다.")
    else:
        time_left = SESSION_TIMEOUT - (datetime.now() - st.session_state["login_time"])
        minutes_left = int(time_left.total_seconds() // 60)
        seconds_left = int(time_left.total_seconds() % 60)

        col_status, col_reset, col_logout = st.columns([2,1,1])
        with col_status:
            st.success(f"🟢 자동 로그아웃까지 남은 시간: {minutes_left}분 {seconds_left}초")
        with col_reset:
            if st.button("🔄 전체 데이터 즉시 리셋"):
                init_databases(force=True)
                st.warning("데이터베이스 수동 초기화 완료.")
                time.sleep(1); st.rerun()
        with col_logout:
            if st.button("🔒 즉시 안전 로그아웃"):
                st.session_state["admin_authenticated"] = False
                st.session_state["login_time"] = None
                st.rerun()

        st.divider()
        adm_left, adm_right = st.columns([1,1], gap="medium")

        with adm_left:
            st.subheader("🚨 실시간 SOS 비상 신고 접수 현황")
            active_sos = pd.read_csv(DB_SOS, encoding="utf-8-sig")
            active_sos = active_sos[active_sos["상태"] == "🚨 미조치 긴급상황"]
            if active_sos.empty:
                st.success("✅ 현재 접수된 비상 신고가 없습니다.")
                st.caption("신고가 접수되면 위치 좌표와 시간이 표시됩니다.")
            else:
                st.warning(f"현재 {len(active_sos)}건의 비상 상황 발생.")
                sos_map_data = active_sos.rename(columns={"위치_위도":"lat","위치_경도":"lon"})
                st.map(sos_map_data, zoom=12)
                for index, row in active_sos.iterrows():
                    col_info, col_btn = st.columns([3,1])
                    with col_info:
                        st.write(f"⏰ {row['일시']} | 📌 {row['위치_위도']:.5f}, {row['위치_경도']:.5f}")
                    with col_btn:
                        if st.button("✅ 조치 완료", key=f"sos_{index}"):
                            full = pd.read_csv(DB_SOS, encoding="utf-8-sig")
                            full.at[index, "상태"] = "조치완료"
                            full.to_csv(DB_SOS, index=False, encoding="utf-8-sig")
                            st.success("상황 조치 완료")
                            st.rerun()

        with adm_right:
            st.subheader("📋 현장 작업자 실시간 점검 기록 DB")
            current_logs = pd.read_csv(DB_LOG, encoding="utf-8-sig")
            if current_logs.empty:
                st.info("아직 제출된 현장 점검 일지가 없습니다.")
            else:
                st.dataframe(current_logs.sort_values(by="일시", ascending=False), use_container_width=True)

        st.divider()
        st.subheader("📸 현장 사진 아카이브")
        st.caption("썸네일 확인 및 개별/일괄 삭제 지원. 최신순 표시.")

        photo_df = pd.read_csv(DB_PHOTO, encoding="utf-8-sig")
        if photo_df.empty:
            st.info("등록된 현장 사진이 없습니다.")
        else:
            photo_df_sorted = photo_df.sort_values(by="일시", ascending=False).reset_index(drop=True)
            col_bulk_left, col_bulk_right = st.columns([4,1])
            with col_bulk_right:
                if st.button("🗑️ 전체 사진 일괄 삭제"):
                    try:
                        for fn in photo_df_sorted["파일명"]:
                            fp = os.path.join(PHOTO_DIR, str(fn))
                            if os.path.exists(fp):
                                os.remove(fp)
                        pd.DataFrame(columns=PHOTO_COLS).to_csv(DB_PHOTO, index=False, encoding="utf-8-sig")
                        st.warning("모든 사진과 기록이 삭제되었습니다.")
                        time.sleep(1); st.rerun()
                    except Exception as e:
                        st.error(f"일괄 삭제 중 오류: {e}")

            n_cols = 3
            rows = (len(photo_df_sorted) + n_cols - 1) // n_cols
            for r in range(rows):
                cols = st.columns(n_cols)
                for c in range(n_cols):
                    idx = r*n_cols + c
                    if idx >= len(photo_df_sorted): break
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
                            if st.button("🗑️ 이 사진 삭제", key=f"del_{idx}"):
                                try:
                                    if os.path.exists(fp):
                                        os.remove(fp)
                                    df_all = pd.read_csv(DB_PHOTO, encoding="utf-8-sig")
                                    df_all = df_all[df_all["파일명"] != row["파일명"]]
                                    df_all.to_csv(DB_PHOTO, index=False, encoding="utf-8-sig")
                                    st.success("사진이 삭제되었습니다.")
                                    time.sleep(0.5); st.rerun()
                                except Exception as e:
                                    st.error(f"삭제 중 오류: {e}")
