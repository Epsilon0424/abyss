"""Session-state initialization and widget key helpers.
Streamlit 위젯 key, 기본 세션값, 파티 기본값 주입 로직을 한곳에서 관리합니다.
"""

from __future__ import annotations

import streamlit as st

from ui.app_config import (
    COOKIE_KIND,
    DEFAULT_PARTY_SLOT1_BY_KIND,
    DEFAULT_PARTY_SLOT2_BY_KIND,
)

# =====================================================
# Cookie kind helpers
# =====================================================
def kind_of(cookie_name: str) -> str:
    kind = COOKIE_KIND.get(cookie_name)
    if kind is None:
        raise ValueError(f"지원하지 않는 쿠키: {cookie_name}")
    return kind

# =====================================================
# Widget key helpers
# =====================================================
def mode_key(kind: str) -> str:
    return f"mode_widget__{kind}"

def equip_manual_key(kind: str) -> str:
    return f"equip_manual__{kind}"

def equip_key(kind: str) -> str:
    return f"equip_widget__{kind}"

def seaz_key(kind: str) -> str:
    return f"seaz_widget__{kind}"

def party1_key(kind: str) -> str:
    return f"party_slot1__{kind}"

def party2_key(kind: str) -> str:
    return f"party_slot2__{kind}"

def party_equip1_key(kind: str) -> str:
    return f"party_equip_slot1__{kind}"

def party_equip2_key(kind: str) -> str:
    return f"party_equip_slot2__{kind}"

def party_seaz1_key(kind: str) -> str:
    return f"party_seaz_slot1__{kind}"

def party_seaz2_key(kind: str) -> str:
    return f"party_seaz_slot2__{kind}"

def party_unique1_key(kind: str) -> str:
    return f"party_unique_slot1__{kind}"

def party_unique2_key(kind: str) -> str:
    return f"party_unique_slot2__{kind}"

def main_unique_key(kind: str) -> str:
    return f"main_unique__{kind}"

# =====================================================
# Session-state defaults
# =====================================================
def init_once(key: str, value) -> None:
    """Set a widget value only on the first initialization."""
    flag = f"_init_once__{key}"
    if flag in st.session_state:
        return
    st.session_state[key] = value
    st.session_state[flag] = True

def init_session_state() -> None:
    """Initialize app-level session values without overwriting user selections."""
    defaults = {
        "cookie": "달빛술사 쿠키",
        "seaz": "",
        "party": [],
        "best": None,
        "best_kind": None,
        "last_run": None,
        "mode": "최적(자동)",
        "equip": "",
        "party_seaz": {},
        "party_uniques": {},
        "main_unique": "",
        "party_sets": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value.copy() if isinstance(value, (dict, list)) else value

    if "element" not in st.session_state:
        st.session_state.element = "전체"
    if "_element_prev" not in st.session_state:
        st.session_state._element_prev = st.session_state.element
    if "element_widget" not in st.session_state:
        st.session_state.element_widget = st.session_state.element
    if "_cookie_prev" not in st.session_state:
        st.session_state._cookie_prev = st.session_state.cookie

def reset_party_defaults_for_kind(kind: str) -> None:
    """Reset party-slot widgets to the default pair for the selected main cookie."""
    p1_default = DEFAULT_PARTY_SLOT1_BY_KIND.get(kind)
    p2_default = DEFAULT_PARTY_SLOT2_BY_KIND.get(kind)
    if p1_default is not None:
        st.session_state[party1_key(kind)] = p1_default
    if p2_default is not None:
        st.session_state[party2_key(kind)] = p2_default
