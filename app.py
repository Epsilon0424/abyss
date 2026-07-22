# =====================================================
# Imports
# =====================================================
import html as _html
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

import cookie_simulator as sim

from ui.app_config import (
    ALL_COOKIES,
    COOKIE_ELEMENT,
    DEFAULT_PARTY_SLOT1_BY_KIND,
    DEFAULT_PARTY_SLOT2_BY_KIND,
    ELEMENT_OPTIONS,
    STEP_FIXED,
    STRIKE_COOKIE_OPTIONS,
    SUPPORT_COOKIE_OPTIONS,
)

from ui.session_keys import (
    equip_key,
    equip_manual_key,
    init_once,
    init_session_state,
    kind_of,
    main_unique_key,
    mode_key,
    party1_key,
    party2_key,
    party_equip1_key,
    party_equip2_key,
    party_seaz1_key,
    party_seaz2_key,
    party_unique1_key,
    party_unique2_key,
    reset_party_defaults_for_kind,
    seaz_key,
)

from ui.result_helpers import (
    build_stat_tables,
    cycle_breakdown_df,
    hide_breeder_when_not_wind,
    labeled_table_html,
    pretty_potentials,
    pretty_shards,
    render_final_stats_grid,
    render_labeled_table,
    render_main_equip_label_with_adjustment,
    render_party_label_with_adjustment,
    render_seaz_label_with_adjustment,
)

# =====================================================
# UI module imports
# =====================================================
from ui.styles import inject_styles
from ui.translations import (
    _english_on,
    _tr_html,
    _tr_text,
    render_ctl_label,
)
from ui.assets import (
    _icon_for_cookie,
    _icon_for_element,
    _icon_for_equip,
    _icon_for_language,
    _icon_for_role,
    _icon_for_seaz,
    _icon_for_theme,
    selectbox_with_left_icon,
)
from ui.adjustment_notes import (
    _adjustment_note_keys_for_equip,
    _adjustment_note_keys_for_main_cookie,
    _adjustment_note_keys_for_party,
    _adjustment_note_keys_for_seaz,
    _adjustment_note_keys_for_unique,
    _merge_note_keys,
    render_adjustment_summary,
)

from ui.shard_placement import render_shard_placement_tab

# =====================================================
# Page setup and base style
# =====================================================
st.set_page_config(page_title="THE ABYSS RAID COOKIE LAB", layout="wide")

# UI 테마 선택값
# - system: 기기/브라우저 색상 설정을 따름
# - light/dark: 사용자가 앱에서 직접 고정
THEME_OPTIONS = ("system", "light", "dark")
if st.session_state.get("ui_theme") not in THEME_OPTIONS:
    st.session_state.ui_theme = "system"
if st.session_state.get("ui_theme_widget") not in THEME_OPTIONS:
    st.session_state.ui_theme_widget = st.session_state.ui_theme

def _sync_ui_theme_from_widget() -> None:
    picked = st.session_state.get("ui_theme_widget", st.session_state.get("ui_theme", "system"))
    if picked in THEME_OPTIONS:
        st.session_state.ui_theme = picked

def _theme_mode_label(mode: str) -> str:
    labels_ko = {
        "system": "기기 설정",
        "light": "라이트 모드",
        "dark": "다크 모드",
    }
    labels_en = {
        "system": "Device setting",
        "light": "Light Mode",
        "dark": "Dark Mode",
    }
    labels = labels_en if _english_on() else labels_ko
    return labels.get(mode, mode)

inject_styles()
init_session_state()

# =====================================================
# Selection restore and option helpers
# =====================================================
def _restore_selection_widgets_for_language_toggle() -> None:
    """언어 체크박스만 바꿨을 때 기존 선택값이 초기화되지 않도록 위젯 키를 복구한다.
    Streamlit selectbox는 format_func로 표시 문자열이 바뀌면 같은 key라도 내부 위젯 상태가
    기본값으로 돌아가는 경우가 있다. 그래서 언어 변경 직후에는 실제 계산에 쓰는 한국어
    canonical 값들을 다시 각 selectbox key에 넣고 rerun한다.
    """
    try:
        cur_cookie = st.session_state.get("cookie", "")
        cur_element = st.session_state.get("element", "")

        if cur_element:
            st.session_state["element_widget"] = cur_element
            st.session_state["_element_prev"] = cur_element
        if cur_cookie:
            st.session_state["cookie_widget"] = cur_cookie
            st.session_state["_cookie_prev"] = cur_cookie

        if not cur_cookie:
            return

        k = kind_of(cur_cookie)

        if st.session_state.get("mode"):
            st.session_state[mode_key(k)] = st.session_state.get("mode")
        if st.session_state.get("equip"):
            st.session_state[equip_key(k)] = st.session_state.get("equip")
        if st.session_state.get("seaz"):
            st.session_state[seaz_key(k)] = st.session_state.get("seaz")
        if st.session_state.get("main_unique"):
            st.session_state[main_unique_key(k)] = st.session_state.get("main_unique")

        party = list(st.session_state.get("party") or [])
        if len(party) >= 1 and party[0]:
            st.session_state[party1_key(k)] = party[0]
        if len(party) >= 2 and party[1]:
            st.session_state[party2_key(k)] = party[1]

        party_sets = dict(st.session_state.get("party_sets") or {})
        party_seaz = dict(st.session_state.get("party_seaz") or {})
        party_uniques = dict(st.session_state.get("party_uniques") or {})

        if len(party) >= 1 and party[0]:
            p = party[0]
            if p in party_sets:
                st.session_state[party_equip1_key(k)] = party_sets[p]
            if p in party_seaz:
                st.session_state[party_seaz1_key(k)] = party_seaz[p]
            if p in party_uniques:
                st.session_state[party_unique1_key(k)] = party_uniques[p]
        if len(party) >= 2 and party[1]:
            p = party[1]
            if p in party_sets:
                st.session_state[party_equip2_key(k)] = party_sets[p]
            if p in party_seaz:
                st.session_state[party_seaz2_key(k)] = party_seaz[p]
            if p in party_uniques:
                st.session_state[party_unique2_key(k)] = party_uniques[p]
    except Exception:
        # 언어 전환 보정이 실패해도 앱 자체는 계속 실행되도록 한다.
        pass

def _icon_for_party_unique(unique_name: str, party_cookie_name: str) -> str | None:
    """유니크 설탕유리조각 드롭다운 좌측 아이콘.
    - 공용 유니크 : 유형/ALL.png
    - 데미지 딜러 유니크 3종 : 유형/데미지 딜러.png
    - 스트라이커 유니크 2종 : 유형/스트라이커.png
    - 서포터 유니크 3종 : 유형/서포터.png
    """
    unique_name = str(unique_name).strip()

    meta = getattr(sim, "UNIQUE_SHARDS", {}).get(unique_name, {}) or {}
    roles = [str(x).lower() for x in meta.get("allowed_roles", [])]

    # 유니크 자체의 허용 역할 기준으로 우선 결정
    if "dps" in roles:
        return _icon_for_role("데미지 딜러") or _icon_for_role("ALL")
    if "support" in roles:
        return _icon_for_role("서포터") or _icon_for_role("ALL")
    if "strike" in roles:
        return _icon_for_role("스트라이커") or _icon_for_role("ALL")
    if "any" in roles:
        return _icon_for_role("ALL")

    # 메타가 비었을 때는 쿠키 역할 기준으로 보조 판정
    cookie_role = str(getattr(sim, "COOKIE_ROLE", {}).get(party_cookie_name, "")).lower()
    if cookie_role == "dps":
        return _icon_for_role("데미지 딜러") or _icon_for_role("ALL")
    if cookie_role == "support":
        return _icon_for_role("서포터") or _icon_for_role("ALL")
    if cookie_role == "strike":
        return _icon_for_role("스트라이커") or _icon_for_role("ALL")

    return _icon_for_role("ALL")

def _party_unique_options_for_cookie(cookie_name: str) -> tuple[list[str], str]:
    # 메인 딜러 유니크는 쿠키 파일의 allowed_uniques()에서 1개로 고정
    # 파티 쿠키 유니크는 세부 설정에서 직접 선택 가능하게 유지
    support_options = [
        "로드 나이트메어의 기억",
        "멜랑크림 쿠키의 순수한 기억",
        "달빛술사 쿠키의 기억",
    ]
    striker_options = [
        "밀키웨이맛 쿠키의 기억",
        "꿈열차에 실린 기억",
    ]

    if cookie_name == "이슬맛 쿠키":
        return support_options, "멜랑크림 쿠키의 순수한 기억"

    if cookie_name == "달빛술사 쿠키":
        return support_options, "달빛술사 쿠키의 기억"

    if cookie_name in ("샬롯맛 쿠키", "네온데니쉬맛 쿠키"):
        return support_options, "멜랑크림 쿠키의 순수한 기억"

    if cookie_name in ("윈드파라거스 쿠키", "룽샤맛 쿠키", "마블베리맛 쿠키", "밀키웨이맛 쿠키", "체리콜라맛 쿠키"):
        return striker_options, "꿈열차에 실린 기억"

    return [], ""

def _main_unique_options_for_cookie(cookie_name: str) -> tuple[list[str], str]:
    """메인 쿠키 유니크 설탕유리조각 후보 / 기본값."""
    # 메인 쿠키는 역할 기준으로 유니크 후보 표시
    # - 딜러: 딜러 유니크 3종 + 공용 유니크
    # - 스트라이커: 스트라이커 유니크 2종 + 공용 유니크
    # - 서포터: 서포터 유니크 3종 + 공용 유니크
    dps_options = [
        "로드 나이트메어의 뒤틀린 기억",
        "스타더스트 쿠키의 기억",
        "꿈세계의 기억",
        "새벽을 여는 달빛술사 쿠키의 기억",
    ]
    striker_options = [
        "밀키웨이맛 쿠키의 기억",
        "꿈열차에 실린 기억",
        "새벽을 여는 달빛술사 쿠키의 기억",
    ]
    support_options = [
        "로드 나이트메어의 기억",
        "멜랑크림 쿠키의 순수한 기억",
        "달빛술사 쿠키의 기억",
        "새벽을 여는 달빛술사 쿠키의 기억",
    ]

    dps_preferred = {
        "멜랑크림 쿠키": "스타더스트 쿠키의 기억",
        "흑보리맛 쿠키": "로드 나이트메어의 뒤틀린 기억",
        "샤이닝베리맛 쿠키": "스타더스트 쿠키의 기억",
        "피닉스페퍼 쿠키": "로드 나이트메어의 뒤틀린 기억",
        "블루멜로우맛 쿠키": "로드 나이트메어의 뒤틀린 기억",
        "스타더스트 쿠키": "로드 나이트메어의 뒤틀린 기억",
    }
    striker_preferred = {
        "윈드파라거스 쿠키": "꿈열차에 실린 기억",
        "룽샤맛 쿠키": "꿈열차에 실린 기억",
        "마블베리맛 쿠키": "꿈열차에 실린 기억",
        "밀키웨이맛 쿠키": "꿈열차에 실린 기억",
        "체리콜라맛 쿠키": "꿈열차에 실린 기억",
    }
    support_preferred = {
        "이슬맛 쿠키": "멜랑크림 쿠키의 순수한 기억",
        "샬롯맛 쿠키": "멜랑크림 쿠키의 순수한 기억",
        "네온데니쉬맛 쿠키": "멜랑크림 쿠키의 순수한 기억",
        "달빛술사 쿠키": "달빛술사 쿠키의 기억",
    }

    role = getattr(sim, "COOKIE_ROLE", {}).get(cookie_name, "")
    if role == "dps":
        opts = dps_options
        preferred = dps_preferred.get(cookie_name, opts[0])
    elif role == "strike":
        opts = striker_options
        preferred = striker_preferred.get(cookie_name, opts[0])
    elif role == "support":
        opts = support_options
        preferred = support_preferred.get(cookie_name, opts[0])
    else:
        opts = []
        preferred = ""

    # 실제 정의된 유니크만 표시 + 중복 제거
    unique_defs = getattr(sim, "UNIQUE_SHARDS", {})
    seen = set()
    clean: list[str] = []
    for x in opts:
        sx = str(x).strip()
        if sx and sx in unique_defs and sx not in seen:
            clean.append(sx)
            seen.add(sx)

    if preferred not in clean:
        preferred = clean[0] if clean else ""
    return clean, preferred

def _render_main_unique_select(cookie_name: str, unique_widget_key: str) -> str:
    """기본 탭에 표시되는 메인 쿠키 유니크 설탕유리조각 드롭다운."""
    unique_options, unique_preferred = _main_unique_options_for_cookie(cookie_name)
    if not unique_options:
        st.session_state.main_unique = ""
        return ""

    prev_key = f"{unique_widget_key}__cookie_prev"
    cookie_changed = st.session_state.get(prev_key, "") != cookie_name
    cur_unique = st.session_state.get(unique_widget_key, "")
    if cookie_changed or (not cur_unique) or (cur_unique not in unique_options):
        st.session_state[unique_widget_key] = unique_preferred if unique_preferred in unique_options else unique_options[0]
    st.session_state[prev_key] = cookie_name

    render_ctl_label("유니크 설탕유리조각")
    picked_unique = selectbox_with_left_icon(
        label="메인 유니크 설탕유리조각",
        options=unique_options,
        key=unique_widget_key,
        icon_path=_icon_for_party_unique(
            st.session_state.get(unique_widget_key, unique_options[0] if unique_options else ""),
            cookie_name,
        ),
    )
    st.session_state.main_unique = picked_unique
    return picked_unique

def _party_equip_options_for_cookie(
    cookie_name: str,
    main_cookie_name: str = "",
    role_label: str = "",
) -> tuple[list[str], str]:
    """파티 쿠키별 장비 후보 / 기본값.

    메인 쿠키와 파티 쿠키의 속성이 다르면 기본 장비만 역할 기준으로 보정
    - 서포터: 전설의 유령해적
    - 스트라이커: 황금 예복
    """
    all_equips = list(getattr(sim, "EQUIP_SETS", {}).keys())

    def keep(names: list[str]) -> list[str]:
        return [x for x in names if x in all_equips]

    def _is_support_cookie(name: str) -> bool:
        return name in ("이슬맛 쿠키", "샬롯맛 쿠키", "네온데니쉬맛 쿠키", "달빛술사 쿠키")

    def _is_striker_cookie(name: str) -> bool:
        return name in ("윈드파라거스 쿠키", "룽샤맛 쿠키", "마블베리맛 쿠키", "밀키웨이맛 쿠키", "체리콜라맛 쿠키")

    if cookie_name == "이슬맛 쿠키":
        opts = keep(["전설의 유령해적", "영원의 대마술사"])
        preferred = "전설의 유령해적"
    elif cookie_name == "샬롯맛 쿠키":
        opts = keep(["전설의 유령해적", "영원의 대마술사"])
        preferred = "전설의 유령해적"
    elif cookie_name == "달빛술사 쿠키":
        opts = keep(["시간관리국의 제복", "유성우의 향연"])
        preferred = "시간관리국의 제복"
    elif cookie_name == "네온데니쉬맛 쿠키":
        # 샤이닝베리 메인 파티 서폿 네온데니쉬는 세부사항 기본 장비를 유령해적으로 표시
        if main_cookie_name == "샤이닝베리맛 쿠키":
            opts = keep(["전설의 유령해적", "영원의 대마술사"])
            preferred = "전설의 유령해적"
        else:
            opts = keep(["영원의 대마술사", "전설의 유령해적"])
            preferred = "영원의 대마술사"
    elif cookie_name == "체리콜라맛 쿠키":
        # 체리콜라는 스트라이커 장비만 사용한다.
        # 단, 최적화의 잠재/일반 설탕유리조각 후보는 딜러형으로 계산한다.
        opts = keep(["황금 예복", "유성우의 향연"])
        preferred = "황금 예복"
    elif cookie_name in ("룽샤맛 쿠키", "마블베리맛 쿠키", "밀키웨이맛 쿠키", "윈드파라거스 쿠키"):
        opts = keep(["황금 예복", "유성우의 향연"])
        preferred = "황금 예복"
    else:
        opts = []
        preferred = ""

    main_elem = COOKIE_ELEMENT.get(main_cookie_name, "")
    party_elem = COOKIE_ELEMENT.get(cookie_name, "")
    elem_diff = bool(main_elem and party_elem and main_elem != party_elem)

    if elem_diff:
        # 메인과 속성이 다르면 화면에 처음 보이는 기본값만 역할 기준으로 보정한다.
        if ("스트" in role_label) or _is_striker_cookie(cookie_name):
            preferred = "황금 예복"
        elif (("서폿" in role_label) or _is_support_cookie(cookie_name)) and cookie_name != "달빛술사 쿠키":
            preferred = "전설의 유령해적"

    if not opts and preferred:
        opts = [preferred]
    if preferred and preferred not in opts:
        opts = [preferred] + opts

    # selectbox 첫 화면이 기본값을 바로 보여주도록 기본값을 맨 앞으로 정렬
    if preferred in opts:
        opts = [preferred] + [x for x in opts if x != preferred]

    return opts, preferred

def _party_seaz_options_for_cookie(cookie_name: str) -> tuple[list[str], str]:
    all_seaz = list(getattr(sim, "SEAZNITES", {}).keys())

    if cookie_name == "윈드파라거스 쿠키":
        opts = (getattr(sim, "wind_allowed_seaz", lambda: [])() or [x for x in all_seaz if str(x).startswith("페퍼루비:")])
        preferred = "리치코랄:믿음직한 브리더"
    elif cookie_name == "룽샤맛 쿠키":
        opts = (getattr(sim, "lungsha_allowed_seaz", lambda: [])() or ["리치코랄:빛나는 은하수"])
        preferred = getattr(sim, "LUNGSHA_FIXED_SEAZ", "리치코랄:빛나는 은하수")
    elif cookie_name == "마블베리맛 쿠키":
        opts = (getattr(sim, "marble_berry_allowed_seaz", lambda: [])() or ["리치코랄:빛나는 은하수"])
        preferred = getattr(sim, "MARBLE_BERRY_FIXED_SEAZ", "리치코랄:빛나는 은하수")
    elif cookie_name == "밀키웨이맛 쿠키":
        opts = (getattr(sim, "milky_way_allowed_seaz", lambda: [])() or ["리치코랄:빛나는 은하수"])
        preferred = getattr(sim, "MILKY_WAY_FIXED_SEAZ", "리치코랄:빛나는 은하수")
    elif cookie_name == "체리콜라맛 쿠키":
        opts = (getattr(sim, "cherry_cola_allowed_seaz", lambda: [])() or ["리치코랄:빛나는 은하수"])
        preferred = getattr(sim, "CHERRY_COLA_FIXED_SEAZ", "리치코랄:빛나는 은하수")
    elif cookie_name == "이슬맛 쿠키":
        opts = [x for x in all_seaz if str(x).startswith("허브그린드:") or str(x).startswith("민트쿼츠:")]
        preferred = getattr(sim, "FIXED_SEAZ_ISLE", "허브그린드:번뜩이는 기지")
    elif cookie_name == "샬롯맛 쿠키":
        opts = [x for x in all_seaz if str(x).startswith("허브그린드:") or str(x).startswith("민트쿼츠:")]
        preferred = "허브그린드:가벼운 손길"
    elif cookie_name == "네온데니쉬맛 쿠키":
        opts = (getattr(sim, "neon_allowed_seaz", lambda: [])() or [x for x in all_seaz if str(x).startswith("허브그린드:") or str(x).startswith("민트쿼츠:")])
        preferred = getattr(sim, "FIXED_SEAZ_NEON", "허브그린드:작은 성배")
    elif cookie_name == "달빛술사 쿠키":
        opts = (getattr(sim, "moonlight_allowed_seaz", lambda: [])() or [x for x in all_seaz if str(x).startswith("플럼나이트:")])
        preferred = getattr(sim, "MOONLIGHT_DEFAULT_SEAZ", "플럼나이트:달빛의 속삭임")
    else:
        opts = []
        preferred = ""

    opts = [str(x) for x in opts if str(x).strip()]
    if not opts and preferred:
        opts = [preferred]
    if preferred and preferred not in opts:
        opts = [preferred] + opts
    return opts, preferred

# =====================================================
# Main UI: title and layout
# =====================================================
st.markdown(f"""
<div class="title-card">
  <div class="h-title">THE ABYSS RAID COOKIE LAB</div>
  <div class="h-sub">{_tr_html("어비스 레이드 기준 쿠키 세팅별 최종 스탯, 사이클 기여도, DPS 분석 시뮬레이터")}</div>
</div>
""", unsafe_allow_html=True)

# 영어/한글 체크박스만 바꿨을 때 선택값이 초기화되는 문제 방지
_lang_now = bool(st.session_state.get("ui_english", False))
if "_ui_english_prev" not in st.session_state:
    st.session_state._ui_english_prev = _lang_now
elif bool(st.session_state.get("_ui_english_prev", False)) != _lang_now:
    _restore_selection_widgets_for_language_toggle()
    st.session_state._ui_english_prev = _lang_now
    st.rerun()

# 언어 선택 드롭다운 초기값 동기화
if "ui_language_widget" not in st.session_state:
    st.session_state.ui_language_widget = "English" if bool(st.session_state.get("ui_english", False)) else "한국어"
else:
    _want_english = (st.session_state.ui_language_widget == "English")
    if bool(st.session_state.get("ui_english", False)) != _want_english:
        st.session_state.ui_english = _want_english
        st.rerun()

# =====================================================
# Main UI: selection and result panels
# =====================================================
with st.container(key="outer_shell", border=False):
    left_col, right_col = st.columns([0.75, 2.45], gap="small")

    # =====================================================
    # 좌측: 선택
    # =====================================================
    with left_col:
        with st.container(key="panel_select", border=True):
            st.markdown('<div class="h-title select-title-clean">SELECT</div>', unsafe_allow_html=True)

            basic_tab, detail_tab, setting_tab = st.tabs([_tr_text("기본"), _tr_text("세부사항"), "Setting"])

            with basic_tab:
                render_ctl_label("속성")

                # 속성 선택(필터)
                # 속성 선택(필터) + 아이콘(좌측)
                _cur_el = st.session_state.get("element_widget", st.session_state.get("element", "전체"))
                element = selectbox_with_left_icon(
                    label="속성",
                    options=ELEMENT_OPTIONS,
                    key="element_widget",
                    icon_path=_icon_for_element(_cur_el),
                )


                # 속성 변경 시: 해당 속성에 쿠키가 있으면 첫 쿠키로 이동 + 상태 초기화
                # : 쿠키가 없으면(예: 빛/불) 현재 쿠키는 유지하고 안내만 표시
                if element != st.session_state._element_prev:
                    st.session_state.element = element
                    st.session_state._element_prev = element

                    all_cookies = ALL_COOKIES
                    if element == "전체":
                        filtered = all_cookies
                    else:
                        filtered = [c for c in all_cookies if COOKIE_ELEMENT.get(c) == element]

                    # 해당 속성에 쿠키가 없으면 현재 세팅을 유지한 채 다시 실행하고 안내문을 표시
                    if (element != "전체") and (not filtered):
                        st.rerun()

                    # 쿠키 위젯을 필터 첫 번째로 맞추고, 기존 쿠키 변경 로직과 동일하게 초기화
                    st.session_state.cookie_widget = filtered[0]
                    st.session_state.cookie = filtered[0]
                    st.session_state._cookie_prev = filtered[0]

                    st.session_state.seaz = ""
                    st.session_state.party = []
                    st.session_state.party_uniques = {}
                    st.session_state.party_sets = {}
                    st.session_state.main_unique = ""
                    st.session_state.best = None
                    st.session_state.best_kind = None
                    st.session_state.last_run = None

                    st.session_state.mode = "최적(자동)"
                    st.session_state.equip = ""

                    k2 = kind_of(st.session_state.cookie)
                    st.session_state[seaz_key(k2)] = ""

                    reset_party_defaults_for_kind(k2)

                    st.session_state[mode_key(k2)] = "최적(자동)"
                    st.session_state[equip_manual_key(k2)] = False
                    st.session_state[equip_key(k2)] = ""
                    st.rerun()

                render_ctl_label("쿠키")

                # 쿠키 옵션(속성 필터 적용)
                all_cookies = ALL_COOKIES

                if st.session_state.element == "전체":
                    cookie_options = all_cookies
                else:
                    cookie_options = [c for c in all_cookies if COOKIE_ELEMENT.get(c) == st.session_state.element]

                # 속성에 쿠키가 없는 경우(예: 빛/불): 안내만 표시 + 쿠키 드롭다운 숨김(현재 쿠키 유지)
                if (st.session_state.element != "전체") and (not cookie_options):
                    st.info(_tr_text("선택하신 속성의 쿠키가 없습니다."))
                    cookie = st.session_state.cookie  # 아래 로직에서 cookie 변수가 필요하니 현재 쿠키로 유지
                else:
                    if "cookie_widget" not in st.session_state:
                        st.session_state.cookie_widget = st.session_state.cookie
                    if st.session_state.cookie_widget not in cookie_options:
                        st.session_state.cookie_widget = cookie_options[0]

                                    # 쿠키 선택 + 아이콘(좌측)
                    _cur_cookie = st.session_state.get("cookie_widget", st.session_state.get("cookie", cookie_options[0]))
                    cookie = selectbox_with_left_icon(
                        label="쿠키",
                        options=cookie_options,
                        key="cookie_widget",
                        icon_path=_icon_for_cookie(_cur_cookie, COOKIE_ELEMENT),
                    )

                if cookie != st.session_state._cookie_prev:
                    st.session_state.cookie = cookie
                    st.session_state._cookie_prev = cookie

                    st.session_state.seaz = ""
                    st.session_state.party = []
                    st.session_state.party_uniques = {}
                    st.session_state.party_sets = {}
                    st.session_state.main_unique = ""
                    st.session_state.best = None
                    st.session_state.best_kind = None
                    st.session_state.last_run = None

                    st.session_state.mode = "최적(자동)"
                    st.session_state.equip = ""

                    k2 = kind_of(cookie)
                    st.session_state[seaz_key(k2)] = ""

                    # 쿠키 종류별 기본 파티 슬롯을 다시 맞춘다.
                    # 딜러는 서포터 1명과 스트라이커 1명, 서포터는 스트라이커 1명을 기본으로 둔다.
                    reset_party_defaults_for_kind(k2)

                    st.session_state[mode_key(k2)] = "최적(자동)"
                    st.session_state[equip_manual_key(k2)] = False
                    st.session_state[equip_key(k2)] = ""
                    st.rerun()

                k = kind_of(cookie)
                sk = seaz_key(k)
                p1k = party1_key(k)
                p2k = party2_key(k)
                mk = mode_key(k)
                ek = equip_key(k)
                muk = main_unique_key(k)
                # =====================================================
                # 장비 선택은 드롭다운에서 '자동'을 고르는 방식으로 처리 (토글 제거)
                # =====================================================

                # 장비 라벨 + 계산 보정 안내
                render_main_equip_label_with_adjustment(k, st.session_state.get(ek, ""), [st.session_state.get(p1k, ""), st.session_state.get(p2k, "")])

                # =====================================================
                # 장비 선택 (드롭다운에 "자동" 포함)
                # - "자동"이면 최적(자동) 모드로 처리하고 장비는 ""로 저장
                # - 장비를 고르면 선택(수동) 모드로 처리
                # =====================================================
                def _equip_select(options: list[str]) -> str:
                    if st.session_state.get(ek) not in options:
                        st.session_state[ek] = options[0]
                    picked_now = st.session_state.get(ek, options[0])

                    picked = selectbox_with_left_icon(
                        label="장비",
                        options=options,
                        key=ek,
                        icon_path=_icon_for_equip(picked_now),
                    )
                    return picked

                if cookie in ("이슬맛 쿠키", "샬롯맛 쿠키"):
                    support_opts = ["전설의 유령해적", "영원의 대마술사"]
                    equip = _equip_select(["자동"] + support_opts)
                    st.session_state.equip = "" if equip == "자동" else equip

                elif cookie == "피닉스페퍼 쿠키":
                    phoenix_opts = (getattr(sim, "phoenix_pepper_allowed_equips", lambda: [""])() or [""])
                    equip = _equip_select(["자동"] + phoenix_opts)
                    st.session_state.equip = "" if equip == "자동" else equip

                elif cookie == "네온데니쉬맛 쿠키":
                    neon_opts = ["전설의 유령해적", "영원의 대마술사"]
                    equip = _equip_select(["자동"] + neon_opts)
                    st.session_state.equip = "" if equip == "자동" else equip

                elif cookie == "달빛술사 쿠키":
                    moon_opts = (getattr(sim, "moonlight_allowed_equips", lambda: ["유성우의 향연"])() or ["유성우의 향연"])
                    equip = _equip_select(["자동"] + moon_opts)
                    st.session_state.equip = "" if equip == "자동" else equip

                else:
                    equip_options = [""]

                    if cookie == "윈드파라거스 쿠키":
                        equip_options = (getattr(sim, "wind_allowed_equips", lambda: [""])() or [""])
                    elif cookie == "멜랑크림 쿠키":
                        equip_options = (getattr(sim, "melan_allowed_equips", lambda: [""])() or [""])
                    elif cookie == "흑보리맛 쿠키":
                        equip_options = (getattr(sim, "black_barley_allowed_equips", lambda: [""])() or [""])
                    elif cookie == "샤이닝베리맛 쿠키":
                        equip_options = (getattr(sim, "shining_berry_allowed_equips", lambda: [""])() or [""])
                    elif cookie == "룽샤맛 쿠키":
                        equip_options = (getattr(sim, "lungsha_allowed_equips", lambda: [""])() or [""])
                    elif cookie == "마블베리맛 쿠키":
                        equip_options = (getattr(sim, "marble_berry_allowed_equips", lambda: [""])() or [""])
                    elif cookie == "밀키웨이맛 쿠키":
                        equip_options = (getattr(sim, "milky_way_allowed_equips", lambda: [""])() or [""])
                    elif cookie == "스타더스트 쿠키":
                        equip_options = (getattr(sim, "stardust_allowed_equips", lambda: [""])() or [""])
                    elif cookie == "체리콜라맛 쿠키":
                        equip_options = (getattr(sim, "cherry_cola_allowed_equips", lambda: [""])() or [""])
                    elif cookie == "블루멜로우맛 쿠키":
                        equip_options = (getattr(sim, "blue_mallow_allowed_equips", lambda: [""])() or [""])
                    elif cookie == "피닉스페퍼 쿠키":
                        equip_options = (getattr(sim, "phoenix_pepper_allowed_equips", lambda: [""])() or [""])

                    equip = _equip_select(["자동"] + equip_options)
                    st.session_state.equip = "" if equip == "자동" else equip

                mode = "최적(자동)" if st.session_state.equip == "" else "선택(수동)"
                st.session_state.mode = mode
                st.session_state[mk] = mode

                # =====================================================
                # 시즈나이트/파티
                # =====================================================
                render_seaz_label_with_adjustment(st.session_state.get(sk, ""))

                # -------------------------
                # 1) 윈드(스트)
                # -------------------------
                if cookie == "윈드파라거스 쿠키":
                    seaz_options = (getattr(sim, "wind_allowed_seaz", lambda: [""])() or [""])
                    seaz_options = hide_breeder_when_not_wind(cookie, seaz_options) or [""]
                    preferred_wind_seaz = "리치코랄:믿음직한 브리더"
                    if preferred_wind_seaz in seaz_options:
                        seaz_options = [preferred_wind_seaz] + [x for x in seaz_options if x != preferred_wind_seaz]

                    if st.session_state.get(sk, "") not in seaz_options:
                        st.session_state[sk] = seaz_options[0]

                    seaz = selectbox_with_left_icon(
                        label="시즈나이트 선택",
                        options=seaz_options,
                        key=sk,
                        icon_path=_icon_for_seaz(st.session_state.get(sk, seaz_options[0] if seaz_options else "")),
                    )
                    st.session_state.seaz = seaz
                    st.session_state.main_unique = _render_main_unique_select(cookie, muk)

                    # 파티: 서폿 1명만 (이슬/샬롯)
                    render_party_label_with_adjustment([st.session_state.get(p1k, ""), st.session_state.get(p2k, "")])
                    support_opts = SUPPORT_COOKIE_OPTIONS
                    init_once(p1k, DEFAULT_PARTY_SLOT1_BY_KIND.get(k, DEFAULT_PARTY_SLOT1_BY_KIND["wind"]))
                    if st.session_state.get(p1k, support_opts[0]) not in support_opts:
                        st.session_state[p1k] = support_opts[0]
                    sup = selectbox_with_left_icon(
                        label="파티(서폿)",
                        options=support_opts,
                        key=p1k,
                        icon_path=_icon_for_cookie(st.session_state.get(p1k, support_opts[0] if support_opts else ""), COOKIE_ELEMENT),
                    )
                    st.session_state.party = [sup]

                elif cookie in ("룽샤맛 쿠키", "마블베리맛 쿠키", "밀키웨이맛 쿠키"):
                    if cookie == "룽샤맛 쿠키":
                        seaz_options = (
                            getattr(sim, "lungsha_allowed_seaz", lambda: [getattr(sim, "LUNGSHA_FIXED_SEAZ", "리치코랄:빛나는 은하수")])()
                            or [getattr(sim, "LUNGSHA_FIXED_SEAZ", "리치코랄:빛나는 은하수")]
                        )
                        fixed_seaz = getattr(sim, "LUNGSHA_FIXED_SEAZ", "리치코랄:빛나는 은하수")
                    elif cookie == "마블베리맛 쿠키":
                        seaz_options = (
                            getattr(sim, "marble_berry_allowed_seaz", lambda: [getattr(sim, "MARBLE_BERRY_FIXED_SEAZ", "리치코랄:빛나는 은하수")])()
                            or [getattr(sim, "MARBLE_BERRY_FIXED_SEAZ", "리치코랄:빛나는 은하수")]
                        )
                        fixed_seaz = getattr(sim, "MARBLE_BERRY_FIXED_SEAZ", "리치코랄:빛나는 은하수")
                    else:
                        seaz_options = (
                            getattr(sim, "milky_way_allowed_seaz", lambda: [getattr(sim, "MILKY_WAY_FIXED_SEAZ", "리치코랄:빛나는 은하수")])()
                            or [getattr(sim, "MILKY_WAY_FIXED_SEAZ", "리치코랄:빛나는 은하수")]
                        )
                        fixed_seaz = getattr(sim, "MILKY_WAY_FIXED_SEAZ", "리치코랄:빛나는 은하수")

                    seaz_options = [str(x) for x in seaz_options if str(x).strip()] or [fixed_seaz]
                    st.session_state[sk] = fixed_seaz if fixed_seaz in seaz_options else seaz_options[0]
                    selectbox_with_left_icon(
                        label="시즈나이트 선택",
                        options=seaz_options,
                        key=sk,
                        icon_path=_icon_for_seaz(st.session_state.get(sk, seaz_options[0] if seaz_options else "")),
                        disabled=True,
                    )
                    st.session_state.seaz = st.session_state[sk]
                    st.session_state.main_unique = _render_main_unique_select(cookie, muk)

                    render_party_label_with_adjustment([st.session_state.get(p1k, ""), st.session_state.get(p2k, "")])
                    support_opts = SUPPORT_COOKIE_OPTIONS
                    init_once(p1k, DEFAULT_PARTY_SLOT1_BY_KIND["wind"])
                    if st.session_state.get(p1k, support_opts[0]) not in support_opts:
                        st.session_state[p1k] = support_opts[0]
                    sup = selectbox_with_left_icon(
                        label="파티(서폿)",
                        options=support_opts,
                        key=p1k,
                        icon_path=_icon_for_cookie(st.session_state.get(p1k, support_opts[0] if support_opts else ""), COOKIE_ELEMENT),
                    )
                    st.session_state.party = [sup]

                # -------------------------
                # 2) 멜랑/흑보리(딜러)
                # -------------------------
                elif cookie == "멜랑크림 쿠키":
                    seaz_options = [x for x in getattr(sim, "SEAZNITES", {}).keys() if str(x).startswith("바닐라몬드:")]
                    seaz_options = hide_breeder_when_not_wind(cookie, seaz_options) or [""]

                    PREFERRED_SEAZ = "바닐라몬드:치열한 선봉자"
                    cur = st.session_state.get(sk, "")
                    if (not cur) or (cur not in seaz_options):
                        st.session_state[sk] = PREFERRED_SEAZ if PREFERRED_SEAZ in seaz_options else seaz_options[0]

                    seaz = selectbox_with_left_icon(
                        label="시즈나이트 선택",
                        options=seaz_options,
                        key=sk,
                        icon_path=_icon_for_seaz(st.session_state.get(sk, seaz_options[0] if seaz_options else "")),
                    )
                    st.session_state.seaz = seaz
                    st.session_state.main_unique = _render_main_unique_select(cookie, muk)

                    with st.container(key="party_group", border=False):
                        render_party_label_with_adjustment([st.session_state.get(p1k, ""), st.session_state.get(p2k, "")])

                        # 역할 고정: 서폿 1(이슬/샬롯 선택) + 스트 1(윈드 고정)
                        support_opts = SUPPORT_COOKIE_OPTIONS
                        init_once(p1k, DEFAULT_PARTY_SLOT1_BY_KIND["melan"])
                        if st.session_state.get(p1k, support_opts[0]) not in support_opts:
                            st.session_state[p1k] = support_opts[0]
                        sup = selectbox_with_left_icon(
                        label="파티(서폿)",
                        options=support_opts,
                        key=p1k,
                        icon_path=_icon_for_cookie(st.session_state.get(p1k, support_opts[0] if support_opts else ""), COOKIE_ELEMENT),
                    )

                        strike_opts = STRIKE_COOKIE_OPTIONS
                        init_once(p2k, DEFAULT_PARTY_SLOT2_BY_KIND.get(k, "윈드파라거스 쿠키"))
                        if st.session_state.get(p2k, strike_opts[0]) not in strike_opts:
                            st.session_state[p2k] = strike_opts[0]
                        strike = selectbox_with_left_icon(
                        label="파티(스트)",
                        options=strike_opts,
                        key=p2k,
                        icon_path=_icon_for_cookie(st.session_state.get(p2k, strike_opts[0] if strike_opts else ""), COOKIE_ELEMENT),
                    )

                        st.session_state.party = [sup, strike]

                elif cookie in ("흑보리맛 쿠키", "스타더스트 쿠키"):
                    if cookie == "스타더스트 쿠키":
                        seaz_options = (
                            getattr(sim, "stardust_allowed_seaz", lambda: None)()
                            or [x for x in getattr(sim, "SEAZNITES", {}).keys() if str(x).startswith("페퍼루비:")]
                        )
                    else:
                        seaz_options = (
                            getattr(sim, "black_barley_allowed_seaz", lambda: None)()
                            or [x for x in getattr(sim, "SEAZNITES", {}).keys() if str(x).startswith("페퍼루비:")]
                        )
                    seaz_options = hide_breeder_when_not_wind(cookie, seaz_options) or [""]

                    PREFERRED_SEAZ = "페퍼루비:영예로운 기사도"
                    cur = st.session_state.get(sk, "")
                    if (not cur) or (cur not in seaz_options):
                        st.session_state[sk] = (PREFERRED_SEAZ if (PREFERRED_SEAZ and PREFERRED_SEAZ in seaz_options) else seaz_options[0])

                    seaz = selectbox_with_left_icon(
                        label="시즈나이트 선택",
                        options=seaz_options,
                        key=sk,
                        icon_path=_icon_for_seaz(st.session_state.get(sk, seaz_options[0] if seaz_options else "")),
                    )
                    st.session_state.seaz = seaz
                    st.session_state.main_unique = _render_main_unique_select(cookie, muk)

                    with st.container(key="party_group", border=False):
                        render_party_label_with_adjustment([st.session_state.get(p1k, ""), st.session_state.get(p2k, "")])

                        support_opts = SUPPORT_COOKIE_OPTIONS
                        init_once(p1k, DEFAULT_PARTY_SLOT1_BY_KIND.get(k, DEFAULT_PARTY_SLOT1_BY_KIND["bb"]))
                        if st.session_state.get(p1k, support_opts[0]) not in support_opts:
                            st.session_state[p1k] = support_opts[0]
                        sup = selectbox_with_left_icon(
                        label="파티(서폿)",
                        options=support_opts,
                        key=p1k,
                        icon_path=_icon_for_cookie(st.session_state.get(p1k, support_opts[0] if support_opts else ""), COOKIE_ELEMENT),
                    )

                        strike_opts = STRIKE_COOKIE_OPTIONS
                        init_once(p2k, DEFAULT_PARTY_SLOT2_BY_KIND.get(k, "윈드파라거스 쿠키"))
                        if st.session_state.get(p2k, strike_opts[0]) not in strike_opts:
                            st.session_state[p2k] = strike_opts[0]
                        strike = selectbox_with_left_icon(
                        label="파티(스트)",
                        options=strike_opts,
                        key=p2k,
                        icon_path=_icon_for_cookie(st.session_state.get(p2k, strike_opts[0] if strike_opts else ""), COOKIE_ELEMENT),
                    )

                        st.session_state.party = [sup, strike]

                elif cookie == "샤이닝베리맛 쿠키":
                    seaz_options = (
                        getattr(sim, "shining_berry_allowed_seaz", lambda: None)()
                        or [x for x in getattr(sim, "SEAZNITES", {}).keys() if str(x).startswith("레몬그라스톤:")]
                    )
                    seaz_options = hide_breeder_when_not_wind(cookie, seaz_options) or [""]

                    PREFERRED_SEAZ = "레몬그라스톤:추격자의 결의"
                    cur = st.session_state.get(sk, "")
                    if (not cur) or (cur not in seaz_options):
                        st.session_state[sk] = (PREFERRED_SEAZ if (PREFERRED_SEAZ and PREFERRED_SEAZ in seaz_options) else seaz_options[0])

                    seaz = selectbox_with_left_icon(
                        label="시즈나이트 선택",
                        options=seaz_options,
                        key=sk,
                        icon_path=_icon_for_seaz(st.session_state.get(sk, seaz_options[0] if seaz_options else "")),
                    )
                    st.session_state.seaz = seaz
                    st.session_state.main_unique = _render_main_unique_select(cookie, muk)

                    with st.container(key="party_group_shining", border=False):
                        render_party_label_with_adjustment([st.session_state.get(p1k, ""), st.session_state.get(p2k, "")])

                        support_opts = SUPPORT_COOKIE_OPTIONS
                        init_once(p1k, DEFAULT_PARTY_SLOT1_BY_KIND["shining"])
                        if st.session_state.get(p1k, support_opts[0]) not in support_opts:
                            st.session_state[p1k] = support_opts[0]
                        sup = selectbox_with_left_icon(
                            label="파티(서폿)",
                            options=support_opts,
                            key=p1k,
                            icon_path=_icon_for_cookie(st.session_state.get(p1k, support_opts[0] if support_opts else ""), COOKIE_ELEMENT),
                        )

                        strike_opts = STRIKE_COOKIE_OPTIONS
                        init_once(p2k, DEFAULT_PARTY_SLOT2_BY_KIND.get(k, "윈드파라거스 쿠키"))
                        if st.session_state.get(p2k, strike_opts[0]) not in strike_opts:
                            st.session_state[p2k] = strike_opts[0]
                        strike = selectbox_with_left_icon(
                            label="파티(스트)",
                            options=strike_opts,
                            key=p2k,
                            icon_path=_icon_for_cookie(st.session_state.get(p2k, strike_opts[0] if strike_opts else ""), COOKIE_ELEMENT),
                        )

                        st.session_state.party = [sup, strike]

                elif cookie == "체리콜라맛 쿠키":
                    seaz_options = (
                        getattr(sim, "cherry_cola_allowed_seaz", lambda: None)()
                        or [getattr(sim, "CHERRY_COLA_FIXED_SEAZ", "리치코랄:빛나는 은하수")]
                    )
                    fixed_seaz = getattr(sim, "CHERRY_COLA_FIXED_SEAZ", "리치코랄:빛나는 은하수")
                    seaz_options = [str(x) for x in seaz_options if str(x).strip()] or [fixed_seaz]
                    st.session_state[sk] = fixed_seaz if fixed_seaz in seaz_options else seaz_options[0]
                    selectbox_with_left_icon(
                        label="시즈나이트 선택",
                        options=seaz_options,
                        key=sk,
                        icon_path=_icon_for_seaz(st.session_state.get(sk, seaz_options[0] if seaz_options else "")),
                        disabled=True,
                    )
                    st.session_state.seaz = st.session_state[sk]
                    st.session_state.main_unique = _render_main_unique_select(cookie, muk)

                    with st.container(key="party_group_cherry", border=False):
                        render_party_label_with_adjustment([st.session_state.get(p1k, ""), st.session_state.get(p2k, "")])

                        support_opts = SUPPORT_COOKIE_OPTIONS
                        init_once(p1k, DEFAULT_PARTY_SLOT1_BY_KIND["cherry"])
                        if st.session_state.get(p1k, support_opts[0]) not in support_opts:
                            st.session_state[p1k] = support_opts[0]
                        sup = selectbox_with_left_icon(
                            label="파티(서폿)",
                            options=support_opts,
                            key=p1k,
                            icon_path=_icon_for_cookie(st.session_state.get(p1k, support_opts[0] if support_opts else ""), COOKIE_ELEMENT),
                        )

                        # 체리콜라는 스트라이커라 메인으로 볼 때는 파티에 스트라이커를 추가로 띄우지 않는다.
                        st.session_state[p2k] = ""
                        st.session_state.party = [sup]

                elif cookie == "피닉스페퍼 쿠키":
                    seaz_options = (
                        getattr(sim, "phoenix_pepper_allowed_seaz", lambda: None)()
                        or [x for x in getattr(sim, "SEAZNITES", {}).keys() if str(x).startswith("레몬그라스톤:")]
                    )
                    seaz_options = [x for x in seaz_options if str(x).startswith("레몬그라스톤:")] or seaz_options
                    seaz_options = hide_breeder_when_not_wind(cookie, seaz_options) or [""]

                    PREFERRED_SEAZ = getattr(sim, "FIXED_SEAZ_PHOENIX", "레몬그라스톤:추격자의 결의")
                    cur = st.session_state.get(sk, "")
                    if (not cur) or (cur not in seaz_options):
                        st.session_state[sk] = PREFERRED_SEAZ if PREFERRED_SEAZ in seaz_options else seaz_options[0]

                    seaz = selectbox_with_left_icon(
                        label="시즈나이트 선택",
                        options=seaz_options,
                        key=sk,
                        icon_path=_icon_for_seaz(st.session_state.get(sk, seaz_options[0] if seaz_options else "")),
                    )
                    st.session_state.seaz = seaz
                    st.session_state.main_unique = _render_main_unique_select(cookie, muk)

                    with st.container(key="party_group_phoenix", border=False):
                        render_party_label_with_adjustment([st.session_state.get(p1k, ""), st.session_state.get(p2k, "")])

                        support_opts = SUPPORT_COOKIE_OPTIONS
                        init_once(p1k, DEFAULT_PARTY_SLOT1_BY_KIND["phoenix"])
                        if st.session_state.get(p1k, support_opts[0]) not in support_opts:
                            st.session_state[p1k] = support_opts[0]
                        sup = selectbox_with_left_icon(
                            label="파티(서폿)",
                            options=support_opts,
                            key=p1k,
                            icon_path=_icon_for_cookie(st.session_state.get(p1k, support_opts[0] if support_opts else ""), COOKIE_ELEMENT),
                        )

                        strike_opts = STRIKE_COOKIE_OPTIONS
                        init_once(p2k, DEFAULT_PARTY_SLOT2_BY_KIND.get("phoenix", "윈드파라거스 쿠키"))
                        if st.session_state.get(p2k, strike_opts[0]) not in strike_opts:
                            st.session_state[p2k] = strike_opts[0]
                        strike = selectbox_with_left_icon(
                            label="파티(스트)",
                            options=strike_opts,
                            key=p2k,
                            icon_path=_icon_for_cookie(st.session_state.get(p2k, strike_opts[0] if strike_opts else ""), COOKIE_ELEMENT),
                        )

                        st.session_state.party = [sup, strike]

                elif cookie == "블루멜로우맛 쿠키":
                    seaz_options = (
                        getattr(sim, "blue_mallow_allowed_seaz", lambda: None)()
                        or [x for x in getattr(sim, "SEAZNITES", {}).keys() if str(x).startswith("바닐라몬드:")]
                    )
                    seaz_options = [x for x in seaz_options if str(x).startswith("바닐라몬드:")] or seaz_options
                    seaz_options = hide_breeder_when_not_wind(cookie, seaz_options) or [""]

                    PREFERRED_SEAZ = getattr(sim, "BLUE_MALLOW_DEFAULT_SEAZ", "바닐라몬드:치열한 선봉자")
                    cur = st.session_state.get(sk, "")
                    if (not cur) or (cur not in seaz_options):
                        st.session_state[sk] = PREFERRED_SEAZ if PREFERRED_SEAZ in seaz_options else seaz_options[0]

                    seaz = selectbox_with_left_icon(
                        label="시즈나이트 선택",
                        options=seaz_options,
                        key=sk,
                        icon_path=_icon_for_seaz(st.session_state.get(sk, seaz_options[0] if seaz_options else "")),
                    )
                    st.session_state.seaz = seaz
                    st.session_state.main_unique = _render_main_unique_select(cookie, muk)

                    with st.container(key="party_group_blue", border=False):
                        render_party_label_with_adjustment([st.session_state.get(p1k, ""), st.session_state.get(p2k, "")])

                        support_opts = SUPPORT_COOKIE_OPTIONS
                        init_once(p1k, DEFAULT_PARTY_SLOT1_BY_KIND["blue"])
                        # 블루멜로우 기본 파티 서포터는 샬롯이지만, 사용자가 직접 고른 서포터는 유지한다.
                        if st.session_state.get(p1k, support_opts[0]) not in support_opts:
                            st.session_state[p1k] = DEFAULT_PARTY_SLOT1_BY_KIND["blue"] if DEFAULT_PARTY_SLOT1_BY_KIND["blue"] in support_opts else support_opts[0]
                        sup = selectbox_with_left_icon(
                            label="파티(서폿)",
                            options=support_opts,
                            key=p1k,
                            icon_path=_icon_for_cookie(st.session_state.get(p1k, support_opts[0] if support_opts else ""), COOKIE_ELEMENT),
                        )

                        strike_opts = STRIKE_COOKIE_OPTIONS
                        init_once(p2k, DEFAULT_PARTY_SLOT2_BY_KIND["blue"])
                        if st.session_state.get(p2k, strike_opts[0]) not in strike_opts:
                            st.session_state[p2k] = strike_opts[0]
                        strike = selectbox_with_left_icon(
                            label="파티(스트)",
                            options=strike_opts,
                            key=p2k,
                            icon_path=_icon_for_cookie(st.session_state.get(p2k, strike_opts[0] if strike_opts else ""), COOKIE_ELEMENT),
                        )

                        st.session_state.party = [sup, strike]

                # -------------------------
                # 3) 이슬(서폿) / 샬롯(서폿)
                # -------------------------
                elif cookie == "이슬맛 쿠키":
                    preferred_seaz = getattr(sim, "FIXED_SEAZ_ISLE", "허브그린드:번뜩이는 기지")
                    all_opts = list(getattr(sim, "SEAZNITES", {}).keys())
                    seaz_options = [
                        x for x in all_opts
                        if str(x).startswith("허브그린드:") or str(x).startswith("민트쿼츠:")
                    ]
                    if not seaz_options:
                        seaz_options = [preferred_seaz]
                    seaz_options = hide_breeder_when_not_wind(cookie, seaz_options) or [seaz_options[0]]
                    if preferred_seaz and preferred_seaz not in seaz_options:
                        seaz_options = [preferred_seaz] + seaz_options
                    cur = st.session_state.get(sk, "")
                    if (not cur) or (cur not in seaz_options):
                        st.session_state[sk] = preferred_seaz if preferred_seaz in seaz_options else seaz_options[0]
                    picked_seaz = selectbox_with_left_icon(
                        label="시즈나이트 선택",
                        options=seaz_options,
                        key=sk,
                        icon_path=_icon_for_seaz(st.session_state.get(sk, seaz_options[0] if seaz_options else "")),
                    )
                    st.session_state.seaz = picked_seaz
                    st.session_state.main_unique = _render_main_unique_select(cookie, muk)

                    render_party_label_with_adjustment([st.session_state.get(p1k, ""), st.session_state.get(p2k, "")])
                    strike_opts = STRIKE_COOKIE_OPTIONS
                    init_once(p1k, "윈드파라거스 쿠키")
                    if st.session_state.get(p1k, strike_opts[0]) not in strike_opts:
                        st.session_state[p1k] = strike_opts[0]
                    strike = selectbox_with_left_icon(
                        label="파티(스트)",
                        options=strike_opts,
                        key=p1k,
                        icon_path=_icon_for_cookie(st.session_state.get(p1k, strike_opts[0] if strike_opts else ""), COOKIE_ELEMENT),
                    )
                    st.session_state.party = [strike]

                elif cookie == "샬롯맛 쿠키":
                    # 샬롯 메인 시뮬 + 역할 고정(서폿) => 파티는 스트(윈드) 고정

                    PREFERRED_SEAZ_CHAR = "허브그린드:가벼운 손길"

                    # 1) 원본 옵션 로드
                    all_opts = (
                        getattr(sim, "char_allowed_seaz", lambda: None)()
                        or list(getattr(sim, "SEAZNITES", {}).keys())
                        or [""]
                    )

                    # 2) 샬롯은 허브그린드, 민트쿼츠만 노출
                    seaz_options = [
                        x for x in all_opts
                        if str(x).startswith("허브그린드:") or str(x).startswith("민트쿼츠:")
                    ]

                    # 3) 혹시 비면(데이터 없을 때) 기본값 후보를 만들어 둠
                    if not seaz_options:
                        # 기존 기본 대체값(FIXED_SEAZ_ISLE) 자동 노출 문제 방지
                        fallback = PREFERRED_SEAZ_CHAR
                        seaz_options = [fallback]

                    # (기존 필터 유지)
                    seaz_options = hide_breeder_when_not_wind(cookie, seaz_options) or [seaz_options[0]]

                    # 기본값 선택 로직: 가벼운 손길이 목록에 있으면 그걸로, 아니면 첫 번째
                    cur = st.session_state.get(sk, "")
                    if (not cur) or (cur not in seaz_options):
                        st.session_state[sk] = PREFERRED_SEAZ_CHAR if PREFERRED_SEAZ_CHAR in seaz_options else seaz_options[0]

                    seaz = selectbox_with_left_icon(
                        label="시즈나이트 선택",
                        options=seaz_options,
                        key=sk,
                        icon_path=_icon_for_seaz(st.session_state.get(sk, seaz_options[0] if seaz_options else "")),
                    )
                    st.session_state.seaz = seaz
                    st.session_state.main_unique = _render_main_unique_select(cookie, muk)

                    render_party_label_with_adjustment([st.session_state.get(p1k, ""), st.session_state.get(p2k, "")])
                    strike_opts = STRIKE_COOKIE_OPTIONS
                    init_once(p1k, "윈드파라거스 쿠키")
                    if st.session_state.get(p1k, strike_opts[0]) not in strike_opts:
                        st.session_state[p1k] = strike_opts[0]
                    strike = selectbox_with_left_icon(
                        label="파티(스트)",
                        options=strike_opts,
                        key=p1k,
                        icon_path=_icon_for_cookie(st.session_state.get(p1k, strike_opts[0] if strike_opts else ""), COOKIE_ELEMENT),
                    )
                    st.session_state.party = [strike]

                elif cookie == "네온데니쉬맛 쿠키":
                    preferred_seaz_support = getattr(sim, "FIXED_SEAZ_NEON", "허브그린드:작은 성배")
                    all_opts = (
                        getattr(sim, "neon_allowed_seaz", lambda: None)()
                        or list(getattr(sim, "SEAZNITES", {}).keys())
                        or [""]
                    )
                    seaz_options = [
                        x for x in all_opts
                        if str(x).startswith("허브그린드:") or str(x).startswith("민트쿼츠:")
                    ]
                    if not seaz_options:
                        seaz_options = [preferred_seaz_support]
                    seaz_options = hide_breeder_when_not_wind(cookie, seaz_options) or [seaz_options[0]]
                    cur = st.session_state.get(sk, "")
                    if (not cur) or (cur not in seaz_options):
                        st.session_state[sk] = preferred_seaz_support if preferred_seaz_support in seaz_options else seaz_options[0]
                    seaz = selectbox_with_left_icon(
                        label="시즈나이트 선택",
                        options=seaz_options,
                        key=sk,
                        icon_path=_icon_for_seaz(st.session_state.get(sk, seaz_options[0] if seaz_options else "")),
                    )
                    st.session_state.seaz = seaz
                    st.session_state.main_unique = _render_main_unique_select(cookie, muk)

                    render_party_label_with_adjustment([st.session_state.get(p1k, ""), st.session_state.get(p2k, "")])
                    strike_opts = STRIKE_COOKIE_OPTIONS
                    init_once(p1k, "윈드파라거스 쿠키")
                    if st.session_state.get(p1k, strike_opts[0]) not in strike_opts:
                        st.session_state[p1k] = strike_opts[0]
                    strike = selectbox_with_left_icon(
                        label="파티(스트)",
                        options=strike_opts,
                        key=p1k,
                        icon_path=_icon_for_cookie(st.session_state.get(p1k, strike_opts[0] if strike_opts else ""), COOKIE_ELEMENT),
                    )
                    st.session_state.party = [strike]

                elif cookie == "달빛술사 쿠키":
                    preferred_seaz_support = getattr(sim, "MOONLIGHT_DEFAULT_SEAZ", "플럼나이트:달빛의 속삭임")
                    all_opts = (
                        getattr(sim, "moonlight_allowed_seaz", lambda: None)()
                        or list(getattr(sim, "SEAZNITES", {}).keys())
                        or [""]
                    )
                    seaz_options = [x for x in all_opts if str(x).startswith("플럼나이트:")]
                    if not seaz_options:
                        seaz_options = [preferred_seaz_support]
                    seaz_options = hide_breeder_when_not_wind(cookie, seaz_options) or [seaz_options[0]]
                    cur = st.session_state.get(sk, "")
                    if (not cur) or (cur not in seaz_options):
                        st.session_state[sk] = preferred_seaz_support if preferred_seaz_support in seaz_options else seaz_options[0]
                    seaz = selectbox_with_left_icon(
                        label="시즈나이트 선택",
                        options=seaz_options,
                        key=sk,
                        icon_path=_icon_for_seaz(st.session_state.get(sk, seaz_options[0] if seaz_options else "")),
                    )
                    st.session_state.seaz = seaz
                    st.session_state.main_unique = _render_main_unique_select(cookie, muk)

                    render_party_label_with_adjustment([st.session_state.get(p1k, ""), st.session_state.get(p2k, "")])
                    strike_opts = STRIKE_COOKIE_OPTIONS
                    init_once(p1k, "윈드파라거스 쿠키")
                    if st.session_state.get(p1k, strike_opts[0]) not in strike_opts:
                        st.session_state[p1k] = strike_opts[0]
                    strike = selectbox_with_left_icon(
                        label="파티(스트)",
                        options=strike_opts,
                        key=p1k,
                        icon_path=_icon_for_cookie(st.session_state.get(p1k, strike_opts[0] if strike_opts else ""), COOKIE_ELEMENT),
                    )
                    st.session_state.party = [strike]

                else:
                    raise ValueError(f"지원하지 않는 쿠키: {cookie}")

            with detail_tab:
                with st.container(key="detail_tab_body"):
                    pe1k = party_equip1_key(k)
                    pe2k = party_equip2_key(k)
                    ps1k = party_seaz1_key(k)
                    ps2k = party_seaz2_key(k)
                    pu1k = party_unique1_key(k)
                    pu2k = party_unique2_key(k)
                    party_sets_map = {}
                    party_seaz_map = {}
                    party_uniques_map = {}

                    detail_note_keys = _merge_note_keys(
                        _adjustment_note_keys_for_main_cookie(cookie),
                        _adjustment_note_keys_for_equip(st.session_state.get(ek, ""), owner_cookie_name=cookie, main_cookie_name=cookie),
                        _adjustment_note_keys_for_seaz(st.session_state.get(sk, ""), owner_cookie_name=cookie),
                        _adjustment_note_keys_for_party([st.session_state.get(p1k, ""), st.session_state.get(p2k, "")]),
                    )

                    def _render_party_detail(
                        role_label: str,
                        party_cookie_name: str,
                        equip_widget_key: str,
                        seaz_widget_key: str,
                        unique_widget_key: str,
                    ):
                        if not party_cookie_name:
                            return "", "", ""

                        safe_cookie = _tr_html(party_cookie_name)
                        st.markdown(f'<div class="ctl-label">{safe_cookie}</div>', unsafe_allow_html=True)

                        # 1) 장비
                        equip_options, equip_preferred = _party_equip_options_for_cookie(
                            party_cookie_name,
                            # 속성 비교에는 내부 kind 값이 아니라 실제 쿠키 이름을 넘긴다.
                            main_cookie_name=cookie,
                            role_label=role_label,
                        )
                        picked_equip = ""
                        if equip_options:
                            equip_prev_key = f"{equip_widget_key}__cookie_prev"
                            equip_main_prev_key = f"{equip_widget_key}__main_prev"
                            equip_cookie_changed = st.session_state.get(equip_prev_key, "") != party_cookie_name
                            equip_main_changed = st.session_state.get(equip_main_prev_key, "") != cookie
                            cur_equip = st.session_state.get(equip_widget_key, "")
                            # 기본 장비는 메인/파티 쿠키가 바뀐 순간에만 자동 보정
                            # 사용자가 세부사항에서 직접 고른 장비는 이후 rerun에서 유지
                            preferred_equip = equip_preferred if equip_preferred in equip_options else equip_options[0]
                            should_reset_equip = (
                                equip_cookie_changed
                                or equip_main_changed
                                or (not cur_equip)
                                or (cur_equip not in equip_options)
                                or (
                                    cookie == "샤이닝베리맛 쿠키"
                                    and party_cookie_name == "네온데니쉬맛 쿠키"
                                    and cur_equip == "영원의 대마술사"
                                )
                            )
                            if should_reset_equip:
                                st.session_state[equip_widget_key] = preferred_equip
                            st.session_state[equip_prev_key] = party_cookie_name
                            st.session_state[equip_main_prev_key] = cookie

                            picked_equip = selectbox_with_left_icon(
                                label=f"{role_label} 장비",
                                options=equip_options,
                                key=equip_widget_key,
                                icon_path=_icon_for_equip(st.session_state.get(equip_widget_key, equip_options[0] if equip_options else "")),
                            )
                            detail_note_keys[:] = _merge_note_keys(detail_note_keys, _adjustment_note_keys_for_equip(picked_equip, owner_cookie_name=party_cookie_name, main_cookie_name=cookie))

                        # 2) 시즈나이트
                        seaz_options, seaz_preferred = _party_seaz_options_for_cookie(party_cookie_name)
                        picked_seaz = ""
                        if seaz_options:
                            seaz_prev_key = f"{seaz_widget_key}__cookie_prev"
                            seaz_cookie_changed = st.session_state.get(seaz_prev_key, "") != party_cookie_name
                            cur_seaz = st.session_state.get(seaz_widget_key, "")
                            # 쿠키가 바뀌었거나 현재 값이 선택지에 없을 때만 기본값으로 보정한다.
                            # 사용자가 세부사항에서 직접 선택한 시즈나이트(예: 백마법사의 의지)는 유지한다.
                            if seaz_cookie_changed or (not cur_seaz) or (cur_seaz not in seaz_options):
                                st.session_state[seaz_widget_key] = seaz_preferred if seaz_preferred in seaz_options else seaz_options[0]
                            st.session_state[seaz_prev_key] = party_cookie_name

                            picked_seaz = selectbox_with_left_icon(
                                label=f"{role_label} 시즈나이트",
                                options=seaz_options,
                                key=seaz_widget_key,
                                icon_path=_icon_for_seaz(st.session_state.get(seaz_widget_key, seaz_options[0] if seaz_options else "")),
                            )
                            detail_note_keys[:] = _merge_note_keys(detail_note_keys, _adjustment_note_keys_for_seaz(picked_seaz, owner_cookie_name=party_cookie_name))
                        else:
                            st.info(_tr_text("선택 가능한 시즈나이트가 없습니다."))

                        # 3) 유니크 설탕유리조각
                        unique_options, unique_preferred = _party_unique_options_for_cookie(party_cookie_name)
                        picked_unique = ""
                        if unique_options:
                            unique_prev_key = f"{unique_widget_key}__cookie_prev"
                            unique_cookie_changed = st.session_state.get(unique_prev_key, "") != party_cookie_name
                            cur_unique = st.session_state.get(unique_widget_key, "")
                            if unique_cookie_changed or (not cur_unique) or (cur_unique not in unique_options):
                                st.session_state[unique_widget_key] = unique_preferred if unique_preferred in unique_options else unique_options[0]
                            st.session_state[unique_prev_key] = party_cookie_name

                            picked_unique = selectbox_with_left_icon(
                                label=f"{role_label} 유니크 설탕유리조각",
                                options=unique_options,
                                key=unique_widget_key,
                                icon_path=_icon_for_party_unique(
                                    st.session_state.get(unique_widget_key, unique_options[0] if unique_options else ""),
                                    party_cookie_name,
                                ),
                            )
                            detail_note_keys[:] = _merge_note_keys(
                                detail_note_keys,
                                _adjustment_note_keys_for_unique(party_cookie_name, picked_unique),
                            )

                        return picked_equip, picked_seaz, picked_unique

                    if cookie in ("윈드파라거스 쿠키", "룽샤맛 쿠키", "마블베리맛 쿠키", "밀키웨이맛 쿠키", "체리콜라맛 쿠키"):
                        support_cookie = st.session_state.get(p1k, "")
                        picked_equip, picked_seaz, picked_unique = _render_party_detail("파티(서폿)", support_cookie, pe1k, ps1k, pu1k)
                        if support_cookie and picked_equip:
                            party_sets_map[support_cookie] = picked_equip
                        if support_cookie and picked_seaz:
                            party_seaz_map[support_cookie] = picked_seaz
                        if support_cookie and picked_unique:
                            party_uniques_map[support_cookie] = picked_unique

                    elif cookie in ("멜랑크림 쿠키", "흑보리맛 쿠키", "샤이닝베리맛 쿠키", "피닉스페퍼 쿠키", "블루멜로우맛 쿠키", "스타더스트 쿠키"):
                        support_cookie = st.session_state.get(p1k, "")
                        strike_cookie = st.session_state.get(p2k, "윈드파라거스 쿠키")
                        picked_support_equip, picked_support_seaz, picked_support_unique = _render_party_detail("파티(서폿)", support_cookie, pe1k, ps1k, pu1k)
                        picked_strike_equip, picked_strike_seaz, picked_strike_unique = _render_party_detail("파티(스트)", strike_cookie, pe2k, ps2k, pu2k)
                        if support_cookie and picked_support_equip:
                            party_sets_map[support_cookie] = picked_support_equip
                        if strike_cookie and picked_strike_equip:
                            party_sets_map[strike_cookie] = picked_strike_equip
                        if support_cookie and picked_support_seaz:
                            party_seaz_map[support_cookie] = picked_support_seaz
                        if support_cookie and picked_support_unique:
                            party_uniques_map[support_cookie] = picked_support_unique
                        if strike_cookie and picked_strike_seaz:
                            party_seaz_map[strike_cookie] = picked_strike_seaz
                        if strike_cookie and picked_strike_unique:
                            party_uniques_map[strike_cookie] = picked_strike_unique

                    elif cookie in ("이슬맛 쿠키", "샬롯맛 쿠키", "네온데니쉬맛 쿠키", "달빛술사 쿠키"):
                        strike_cookie = st.session_state.get(p1k, "윈드파라거스 쿠키")
                        picked_equip, picked_seaz, picked_unique = _render_party_detail("파티(스트)", strike_cookie, pe1k, ps1k, pu1k)
                        if strike_cookie and picked_equip:
                            party_sets_map[strike_cookie] = picked_equip
                        if strike_cookie and picked_seaz:
                            party_seaz_map[strike_cookie] = picked_seaz
                        if strike_cookie and picked_unique:
                            party_uniques_map[strike_cookie] = picked_unique

                    else:
                        st.caption(_tr_text("세부 설정이 없습니다."))

                    render_adjustment_summary(detail_note_keys)

                    st.session_state.party_sets = party_sets_map
                    st.session_state.party_seaz = party_seaz_map
                    st.session_state.party_uniques = party_uniques_map

            with setting_tab:
                with st.container(key="setting_tab_body", border=False):
                    render_ctl_label("Language")
                    _lang_default = "English" if bool(st.session_state.get("ui_english", False)) else "한국어"
                    if st.session_state.get("ui_language_widget") not in ("한국어", "English"):
                        st.session_state.ui_language_widget = _lang_default
                    _current_lang_icon = _icon_for_language(st.session_state.get("ui_language_widget", _lang_default))
                    picked_lang = selectbox_with_left_icon(
                        label="Language",
                        options=["한국어", "English"],
                        key="ui_language_widget",
                        icon_path=_current_lang_icon,
                        format_func=lambda x: x,
                    )
                    _picked_english = (picked_lang == "English")
                    if bool(st.session_state.get("ui_english", False)) != _picked_english:
                        st.session_state.ui_english = _picked_english
                        st.session_state._ui_english_prev = _picked_english
                        _restore_selection_widgets_for_language_toggle()
                        st.rerun()

                    render_ctl_label("Theme")
                    # 테마는 별도 상태(ui_theme)에 저장한다.
                    # system은 브라우저의 prefers-color-scheme 값을 따라가고,
                    # light/dark는 사용자가 앱에서 직접 고정한 값으로 적용한다.
                    if st.session_state.get("ui_theme") not in THEME_OPTIONS:
                        st.session_state.ui_theme = "system"
                    if st.session_state.get("ui_theme_widget") not in THEME_OPTIONS:
                        st.session_state.ui_theme_widget = st.session_state.ui_theme
                    _current_theme_icon = _icon_for_theme(st.session_state.get("ui_theme_widget", st.session_state.get("ui_theme", "system")))
                    selectbox_with_left_icon(
                        label="Theme",
                        options=list(THEME_OPTIONS),
                        key="ui_theme_widget",
                        icon_path=_current_theme_icon,
                        format_func=_theme_mode_label,
                        on_change=_sync_ui_theme_from_widget,
                    )

            st.markdown('<hr class="u-divider">', unsafe_allow_html=True)

            # 선택한 속성에 쿠키가 없으면 실행 버튼 비활성화
            no_cookie_for_element = (st.session_state.element != "전체") and (len(cookie_options) == 0)

            run = st.button(
                _tr_text("실행"),
                type="primary",
                use_container_width=True,
                key="run_btn",
                disabled=no_cookie_for_element,
            )

            progress_slot = st.empty()

            def _progress_html(pct: int) -> str:
                pct = max(0, min(100, int(pct)))
                shine_scale = 100.0 / max(pct, 1)

                return (
            f'<div class="prog-area">'
            f'  <div class="prog-row">'
            f'    <div class="prog-wrap">'
            f'      <div class="prog-bar" style="width:{pct}%; --shine-scale:{shine_scale:.6f};">'
            f'        <div class="prog-shimmer"></div>'
            f'      </div>'
            f'      <div class="prog-text">{pct}%</div>'
            f'    </div>'
            f'  </div>'
            f'</div>'
                )

            def run_with_progress(kind_cookie: str):
                progress_slot.markdown(_progress_html(0), unsafe_allow_html=True)

                def cb(p: float):
                    p = max(0.0, min(1.0, float(p)))
                    progress_slot.markdown(_progress_html(int(p * 100)), unsafe_allow_html=True)

                best = None
                best_kind = None

                equip_override_local = None
                if st.session_state.mode == "선택(수동)":
                    equip_override_local = st.session_state.equip or None
                unique_override_local = st.session_state.get("main_unique") or None

                if kind_cookie == "wind":
                    best = sim.optimize_wind_cycle(
                        seaz_name=st.session_state.seaz,
                        party=st.session_state.party,
                        party_sets=st.session_state.get("party_sets", {}),
                        party_seaz=st.session_state.get("party_seaz", {}),
                        party_uniques=st.session_state.get("party_uniques", {}),
                        step=1,
                        progress_cb=cb,
                        equip_override=equip_override_local,
                        unique_override=unique_override_local,
                    )
                    best_kind = "wind"

                elif kind_cookie == "melan":
                    best = sim.optimize_melan_cycle(
                        seaz_name=st.session_state.seaz,
                        party=st.session_state.party,
                        party_sets=st.session_state.get("party_sets", {}),
                        party_seaz=st.session_state.get("party_seaz", {}),
                        party_uniques=st.session_state.get("party_uniques", {}),
                        step=STEP_FIXED,
                        progress_cb=cb,
                        equip_override=equip_override_local,
                        unique_override=unique_override_local,
                    )
                    best_kind = "melan"

                elif kind_cookie == "bb":
                    fn = getattr(sim, "optimize_black_barley_cycle", None)
                    if fn is None:
                        raise ValueError("sim.optimize_black_barley_cycle 가 없습니다.")
                    best = fn(
                        seaz_name=st.session_state.seaz,
                        party=st.session_state.party,
                        party_sets=st.session_state.get("party_sets", {}),
                        party_seaz=st.session_state.get("party_seaz", {}),
                        party_uniques=st.session_state.get("party_uniques", {}),
                        step=STEP_FIXED,
                        progress_cb=cb,
                        equip_override=equip_override_local,
                        unique_override=unique_override_local,
                    )
                    best_kind = "bb"

                elif kind_cookie == "stardust":
                    fn = getattr(sim, "optimize_stardust_cycle", None)
                    if fn is None:
                        raise ValueError("sim.optimize_stardust_cycle 가 없습니다.")
                    best = fn(
                        seaz_name=st.session_state.seaz,
                        party=st.session_state.party,
                        party_sets=st.session_state.get("party_sets", {}),
                        party_seaz=st.session_state.get("party_seaz", {}),
                        party_uniques=st.session_state.get("party_uniques", {}),
                        step=2,
                        progress_cb=cb,
                        equip_override=equip_override_local,
                        unique_override=unique_override_local,
                    )
                    best_kind = "stardust"

                elif kind_cookie == "shining":
                    fn = getattr(sim, "optimize_shining_berry_cycle", None)
                    if fn is None:
                        raise ValueError("sim.optimize_shining_berry_cycle 가 없습니다.")
                    best = fn(
                        seaz_name=st.session_state.seaz,
                        party=st.session_state.party,
                        party_sets=st.session_state.get("party_sets", {}),
                        party_seaz=st.session_state.get("party_seaz", {}),
                        party_uniques=st.session_state.get("party_uniques", {}),
                        step=STEP_FIXED,
                        progress_cb=cb,
                        equip_override=equip_override_local,
                        unique_override=unique_override_local,
                    )
                    best_kind = "shining"

                elif kind_cookie == "phoenix":
                    fn = getattr(sim, "optimize_phoenix_pepper_cycle", None)
                    if fn is None:
                        raise ValueError("sim.optimize_phoenix_pepper_cycle 가 없습니다.")
                    best = fn(
                        seaz_name=st.session_state.seaz,
                        party=st.session_state.party,
                        party_sets=st.session_state.get("party_sets", {}),
                        party_seaz=st.session_state.get("party_seaz", {}),
                        party_uniques=st.session_state.get("party_uniques", {}),
                        step=STEP_FIXED,
                        progress_cb=cb,
                        equip_override=equip_override_local,
                        unique_override=unique_override_local,
                    )
                    best_kind = "phoenix"

                elif kind_cookie == "lungsha":
                    fn = getattr(sim, "optimize_lungsha_cycle", None)
                    if fn is None:
                        raise ValueError("sim.optimize_lungsha_cycle 가 없습니다.")
                    best = fn(
                        seaz_name=st.session_state.seaz,
                        party=st.session_state.party,
                        party_sets=st.session_state.get("party_sets", {}),
                        party_seaz=st.session_state.get("party_seaz", {}),
                        party_uniques=st.session_state.get("party_uniques", {}),
                        # 룽샤는 후보를 줄였지만 안전하게 step=2 이상 유지
                        step=STEP_FIXED,
                        progress_cb=cb,
                        equip_override=equip_override_local,
                        unique_override=unique_override_local,
                    )
                    best_kind = "lungsha"

                elif kind_cookie == "marble":
                    fn = getattr(sim, "optimize_marble_berry_cycle", None)
                    if fn is None:
                        raise ValueError("sim.optimize_marble_berry_cycle 가 없습니다.")
                    best = fn(
                        seaz_name=st.session_state.seaz,
                        party=st.session_state.party,
                        party_sets=st.session_state.get("party_sets", {}),
                        party_seaz=st.session_state.get("party_seaz", {}),
                        party_uniques=st.session_state.get("party_uniques", {}),
                        step=STEP_FIXED,
                        progress_cb=cb,
                        equip_override=equip_override_local,
                        unique_override=unique_override_local,
                    )
                    best_kind = "marble"

                elif kind_cookie == "milky":
                    fn = getattr(sim, "optimize_milky_way_cycle", None)
                    if fn is None:
                        raise ValueError("sim.optimize_milky_way_cycle 가 없습니다.")
                    best = fn(
                        seaz_name=st.session_state.seaz,
                        party=st.session_state.party,
                        party_sets=st.session_state.get("party_sets", {}),
                        party_seaz=st.session_state.get("party_seaz", {}),
                        party_uniques=st.session_state.get("party_uniques", {}),
                        step=1,
                        progress_cb=cb,
                        equip_override=equip_override_local,
                        unique_override=unique_override_local,
                    )
                    best_kind = "milky"

                elif kind_cookie == "cherry":
                    fn = getattr(sim, "optimize_cherry_cola_cycle", None)
                    if fn is None:
                        raise ValueError("sim.optimize_cherry_cola_cycle 가 없습니다.")
                    best = fn(
                        seaz_name=st.session_state.seaz,
                        party=st.session_state.party,
                        party_sets=st.session_state.get("party_sets", {}),
                        party_seaz=st.session_state.get("party_seaz", {}),
                        party_uniques=st.session_state.get("party_uniques", {}),
                        step=STEP_FIXED,
                        progress_cb=cb,
                        equip_override=equip_override_local,
                        unique_override=unique_override_local,
                    )
                    best_kind = "cherry"

                elif kind_cookie == "blue":
                    fn = getattr(sim, "optimize_blue_mallow_cycle", None)
                    if fn is None:
                        raise ValueError("sim.optimize_blue_mallow_cycle 가 없습니다.")
                    best = fn(
                        seaz_name=st.session_state.seaz,
                        party=st.session_state.party,
                        party_sets=st.session_state.get("party_sets", {}),
                        party_seaz=st.session_state.get("party_seaz", {}),
                        party_uniques=st.session_state.get("party_uniques", {}),
                        step=1,
                        progress_cb=cb,
                        equip_override=equip_override_local,
                        unique_override=unique_override_local,
                    )
                    best_kind = "blue"

                elif kind_cookie == "isle":
                    best = sim.optimize_isle_cycle(
                        seaz_name=st.session_state.seaz,
                        party=st.session_state.party,
                        party_sets=st.session_state.get("party_sets", {}),
                        party_seaz=st.session_state.get("party_seaz", {}),
                        party_uniques=st.session_state.get("party_uniques", {}),
                        step=STEP_FIXED,
                        progress_cb=cb,
                        equip_override=equip_override_local,
                        unique_override=unique_override_local,
                    )
                    best_kind = "isle"

                elif kind_cookie == "char":
                    fn = getattr(sim, "optimize_char_cycle", None)
                    if fn is None:
                        raise ValueError("sim.optimize_char_cycle 가 없습니다. cookie_simulator.py에 추가해 주세요.")
                    best = fn(
                        seaz_name=st.session_state.seaz,
                        party=st.session_state.party,
                        party_sets=st.session_state.get("party_sets", {}),
                        party_seaz=st.session_state.get("party_seaz", {}),
                        party_uniques=st.session_state.get("party_uniques", {}),
                        step=STEP_FIXED,
                        progress_cb=cb,
                        equip_override=equip_override_local,
                        unique_override=unique_override_local,
                    )
                    best_kind = "char"

                elif kind_cookie == "neon":
                    fn = getattr(sim, "optimize_neon_cycle", None)
                    if fn is None:
                        raise ValueError("sim.optimize_neon_cycle 가 없습니다. cookie_simulator.py에 추가해 주세요.")
                    best = fn(
                        seaz_name=st.session_state.seaz,
                        party=st.session_state.party,
                        party_sets=st.session_state.get("party_sets", {}),
                        party_seaz=st.session_state.get("party_seaz", {}),
                        party_uniques=st.session_state.get("party_uniques", {}),
                        step=1,
                        progress_cb=cb,
                        equip_override=equip_override_local,
                        unique_override=unique_override_local,
                    )
                    best_kind = "neon"

                elif kind_cookie == "moonlight":
                    fn = getattr(sim, "optimize_moonlight_cycle", None)
                    if fn is None:
                        raise ValueError("sim.optimize_moonlight_cycle 가 없습니다. cookie_simulator.py에 추가해 주세요.")
                    best = fn(
                        seaz_name=st.session_state.seaz,
                        party=st.session_state.party,
                        party_sets=st.session_state.get("party_sets", {}),
                        party_seaz=st.session_state.get("party_seaz", {}),
                        party_uniques=st.session_state.get("party_uniques", {}),
                        step=1,
                        progress_cb=cb,
                        equip_override=equip_override_local,
                        unique_override=unique_override_local,
                    )
                    best_kind = "moonlight"

                else:
                    raise ValueError(f"지원하지 않는 kind_cookie: {kind_cookie}")

                # -----------------------------------------------------
                # 공통 후처리(필요한 것만)
                # -----------------------------------------------------
                # 서포터류 잠재 고정
                if isinstance(best, dict) and best_kind in ("isle", "char", "neon"):
                    best["potentials"] = {"elem_atk": 2, "atk_pct": 2, "buff_amp": 4}
                elif isinstance(best, dict) and best_kind == "moonlight":
                    # 달술 잠재는 유니크/장비/시즈 선택에 따라 최적화 함수에서 자동 배분한다.
                    best["potentials"] = dict(best.get("potentials") or {})

                progress_slot.markdown(_progress_html(100), unsafe_allow_html=True)
                return best, best_kind

            if run:
                kk = kind_of(st.session_state.cookie)
                best, best_kind = run_with_progress(kk)

                st.session_state.best = best
                st.session_state.best_kind = best_kind
                st.session_state.last_run = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")
                st.rerun()

    # =====================================================
    # 우측: 결과
    # =====================================================
    with right_col:
        with st.container(key="panel_result", border=True):
            st.markdown('<div class="h-title result-title-clean">RESULT</div>', unsafe_allow_html=True)

            best = st.session_state.best
            kind = st.session_state.best_kind

            if not best:
                st.caption(_tr_text("설정 후 실행하면 결과가 표시됩니다."))
            else:
                if kind in ("wind", "melan", "bb", "shining", "phoenix", "lungsha", "marble", "cherry", "blue", "moonlight", "milky", "stardust"):
                    c1, c2, c3 = st.columns(3, gap="small")
                    c1.metric("DPS", f"{best.get('dps', 0):,.4f}")
                    c2.metric(_tr_text("1사이클 시간(s)"), f"{best.get('cycle_total_time', 0):,.4f}")
                    c3.metric(_tr_text("1사이클 총딜"), f"{best.get('cycle_total_damage', 0):,.0f}")

                elif kind == "isle":
                    c1, c2, c3 = st.columns(3, gap="small")
                    c1.metric(_tr_text("보호막량"), f"{best.get('max_shield', 0):,.0f}")
                    c2.metric("DPS", f"{best.get('dps', 0):,.4f}")
                    c3.metric(_tr_text("1사이클 총딜"), f"{best.get('cycle_total_damage', 0):,.0f}")

                elif kind == "char":
                    c1, c2, c3 = st.columns(3, gap="small")
                    c1.metric(_tr_text("회복량"), f"{best.get('max_heal', 0):,.0f}")
                    c2.metric("DPS", f"{best.get('dps', 0):,.4f}")
                    c3.metric(_tr_text("1사이클 총딜"), f"{best.get('cycle_total_damage', 0):,.0f}")

                elif kind == "neon":
                    c1, c2, c3 = st.columns(3, gap="small")
                    c1.metric(_tr_text("보호막량"), f"{best.get('max_shield', 0):,.0f}")
                    c2.metric(_tr_text("회복량"), f"{best.get('max_heal', 0):,.0f}")
                    c3.metric("DPS", f"{best.get('dps', 0):,.4f}")

                def _current_sugar_set_text() -> str:
                    def _only_main_row(lines) -> str:
                        vals = [str(x).strip() for x in (lines or []) if str(x).strip()]
                        if not vals:
                            return ""
                        first = vals[0]
                        if ":" in first:
                            _, rhs = first.split(":", 1)
                            rhs = rhs.strip()
                        else:
                            rhs = first.strip()
                        return rhs

                    stats = best.get("stats", {}) or {}
                    rows0 = stats.get("sugar_glass_rows", [])
                    if rows0:
                        return _only_main_row(rows0)
                    try:
                        txt = sim.sugar_glass_party_text(best.get("cookie", ""), best.get("party", []))
                        return _only_main_row(str(txt).splitlines())
                    except Exception:
                        return ""

                sugar_target_text = _current_sugar_set_text()

                if kind in ("wind", "melan", "bb", "shining", "phoenix", "lungsha", "marble", "cherry", "blue", "isle", "char", "neon", "moonlight", "milky", "stardust"):
                    tab1, tab2, tab3, tab4 = st.tabs([_tr_text("결과"), _tr_text("최종 스탯"), _tr_text("사이클 기여도"), ("Shard Placement" if (_english_on() or st.session_state.get("ui_language_widget") == "English") else "조각 배치")])
                else:
                    tab1, tab2, tab3, tab4 = st.tabs([_tr_text("결과"), _tr_text("최종 스탯"), _tr_text("사이클 기여도"), ("Shard Placement" if (_english_on() or st.session_state.get("ui_language_widget") == "English") else "조각 배치")])

                with tab1:
                    def make_setting_df(best: dict, kind: str) -> pd.DataFrame:
                        party_txt = ", ".join(best.get("party", [])) if best.get("party") else "없음"

                        def _sugar_set_text() -> str:
                            return sugar_target_text

                        def add(rows, k, v):
                            v = "" if v is None else str(v).strip()
                            if v:
                                rows.append({"항목": k, "값": v})

                        rows = []
                        if kind in ("wind", "melan", "bb", "shining", "phoenix", "lungsha", "marble", "cherry", "blue", "char", "neon", "moonlight", "milky", "stardust"):
                            add(rows, "쿠키", best.get("cookie", ""))
                            add(rows, "장비", best.get("equip", ""))
                            add(rows, "시즈나이트", best.get("seaz", ""))
                            add(rows, "유니크 조각", best.get("unique", ""))
                            add(rows, "아티팩트", best.get("artifact", ""))
                            add(rows, "파티", party_txt)
                            add(rows, "설탕유리조각", _sugar_set_text())
                        elif kind in ("isle",):
                            add(rows, "쿠키", "이슬맛 쿠키")
                            add(rows, "장비", best.get("equip_fixed", ""))
                            add(rows, "시즈나이트", best.get("seaz_fixed", getattr(sim, "FIXED_SEAZ_ISLE", "")))
                            u = best.get("unique", "") or best.get("unique_fixed", "")
                            add(rows, "유니크 조각", u)
                            add(rows, "아티팩트", best.get("artifact_fixed", "비에 젖은 과거"))
                            add(rows, "파티", party_txt)
                            add(rows, "설탕유리조각", _sugar_set_text())
                        elif kind in ("neon",):
                            add(rows, "쿠키", best.get("cookie", "네온데니쉬맛 쿠키"))
                            add(rows, "장비", best.get("equip", ""))
                            add(rows, "시즈나이트", best.get("seaz", getattr(sim, "FIXED_SEAZ_NEON", "")))
                            add(rows, "유니크 조각", best.get("unique", ""))
                            add(rows, "아티팩트", best.get("artifact", getattr(sim, "NEON_FIXED_ARTIFACT", "치트키 발견?")))
                            add(rows, "파티", party_txt)
                            add(rows, "설탕유리조각", _sugar_set_text())

                        return pd.DataFrame(rows, columns=["항목", "값"])

                    setting_df = make_setting_df(best, kind)

                    if kind in ("wind", "melan", "bb", "shining", "phoenix", "lungsha", "marble", "cherry", "blue", "char", "moonlight", "milky", "stardust"):
                        p_df = pretty_potentials(best.get("potentials", {}))
                        s_df = pretty_shards(best.get("shards", {}))
                    elif kind in ("isle", "neon"):
                        # 달빛술사는 위 일반 분기에서 자체 고정 잠재(7공퍼/1디벞)를 표시한다.
                        pot = best.get("potentials") or {"elem_atk": 2, "atk_pct": 2, "buff_amp": 4}
                        p_df = pretty_potentials(pot)
                        s_df = pretty_shards(best.get("shards", {}))
                    else:
                        p_df = pd.DataFrame(columns=["항목", "값"])
                        s_df = pd.DataFrame(columns=["항목", "값"])

                    html = f"""
                    <div class="summary-grid">
                    <div>{labeled_table_html("세팅", setting_df, small=False, col_widths=(0.40, 0.60))}</div>
                    <div>{labeled_table_html("잠재력", p_df, small=True,  col_widths=(0.50, 0.50))}</div>
                    <div class="md-span-2">{labeled_table_html("설탕유리조각", s_df, small=True, col_widths=(0.50, 0.50))}</div>
                    </div>
                    """
                    st.markdown(html, unsafe_allow_html=True)

                if kind in ("wind", "melan", "bb", "shining", "phoenix", "lungsha", "marble", "cherry", "blue", "isle", "char", "neon", "moonlight", "milky", "stardust"):
                    with tab2:
                        stats = best.get("stats", {})
                        if not stats:
                            st.caption(_tr_text("스탯 정보가 없습니다."))
                        else:
                            atk_df, crit_df, common_df, skill_df, surv_df, amp_df = build_stat_tables(
                                best["stats"],
                                best.get("cookie", ""),
                                best.get("party", st.session_state.party)
                            )
                            render_final_stats_grid(atk_df, crit_df, common_df, skill_df, surv_df, amp_df)

                if kind in ("wind", "melan", "bb", "shining", "phoenix", "lungsha", "marble", "cherry", "blue", "isle", "char", "neon", "moonlight", "milky", "stardust"):
                    with tab3:
                        cb = best.get("cycle_breakdown", {})
                        df = cycle_breakdown_df(cb)

                        render_labeled_table(
                            "사이클 내 딜 기여도",
                            df,
                            small=False,
                            # Cycle Contribution 표는 Item / Damage / Ratio(%)를 정확히 1:1:1로 표시
                            #       가로 스크롤 없이 현재 RESULT 폭 안에서 고정 비율로 나눈다.
                            col_widths=(1, 1, 1),
                        )

                if kind in ("wind", "melan", "bb", "shining", "phoenix", "lungsha", "marble", "cherry", "blue", "isle", "char", "neon", "moonlight", "milky", "stardust"):
                    with tab4:
                        render_shard_placement_tab(sugar_target_text, english=(_english_on() or st.session_state.get("ui_language_widget") == "English"), theme_mode=st.session_state.get("ui_theme", "system"), glass_shards=best.get("shards", {}))

            if st.session_state.last_run:
                st.caption(f"{_tr_text('실행:')} {st.session_state.last_run}")

# =====================================================
# 전체 안내문 위치: outer_shell 바깥
# =====================================================
_note_copyright = (
    "Copyright for the CookieRun: Tower of Adventures resources used in THE ABYSS RAID COOKIE LAB belongs to Devsisters."
    if _english_on()
    else "THE ABYSS RAID COOKIE LAB에 사용된 쿠키런:모험의 탑 관련 리소스의 저작권은 데브시스터즈에 있습니다."
)
_note_calc = (
    "Some stats include both additive and multiplicative calculations, so they may differ from simple summed values."
    if _english_on()
    else "일부 스탯은 가산/배율 적용이 함께 반영되어, 단순 합산값과 다를 수 있습니다."
)
_note_contact = "For inquiries: Epsilon24@gmail.com" if _english_on() else "기타 문의 : Epsilon24@gmail.com"
st.markdown(
f"""
<div class="global-note">
  <div class="note-title">Notes</div>
  <p class="note-text">
    • {_html.escape(_note_copyright)}<br/>
    • {_html.escape(_note_calc)}<br/>
    • <b>{_html.escape(_note_contact)}</b>
  </p>
</div>
""",
unsafe_allow_html=True,
)
