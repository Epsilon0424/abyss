# =====================================================
# Imports
# =====================================================
import html as _html
import streamlit as st

from ui.app_config import COOKIE_ELEMENT
from ui.translations import _english_on, _tr_html

# =====================================================
# Constants
# =====================================================
ADJUSTMENT_NOTES = {
    "party_lungsha": {
        "short": "룽샤 : 불가역 20% → 10% 적용",
        "en_short": "Mala Longxia: Irreversibility 20% → 10% applied",
    },
    "seaz_white_mage": {
        "short": "백마법사의 의지 : 공격력 12.5%, 모든 속성 피해 15% 적용",
        "en_short": "Will of the White Mage: ATK 12.5%, All Elemental DMG 15% applied",
    },
    "seaz_hunter_instinct": {
        "short": "사냥꾼의 본능 : 보스전 최종피해 0% 적용",
        "en_short": "Hunter's Instinct: Boss Total DMG 0% applied",
    },
    "equip_magician": {
        "short": "영원의 대마술사 : 모든 속성 피해 30% → 15% 적용",
        "en_short": "Eternal Magician: All Elemental DMG 30% → 15% applied",
    },
    "equip_meteor": {
        "short": "유성우의 향연 : 속성 내성 감소 10% → 5% 적용",
        "en_short": "Falling Stars: Elemental RES Reduction 10% → 5% applied",
    },
    "equip_meteor_moonlight": {
        "short": "유성우의 향연 : 달빛술사는 속성 내성 감소 10% 적용",
        "en_short": "Falling Stars: Moonlight applies Elemental RES Reduction 10%",
    },
    "equip_meteor_zero": {
        "short": "유성우의 향연 : 속성 내성 감소 10% → 0% 적용",
        "en_short": "Falling Stars: Elemental RES Reduction 10% → 0% applied",
    },
    "unique_crushed_isle": {
        "short": "이슬 + 크러쉬드페퍼 : 방어력 관통 12% → 4% 적용",
        "en_short": "Dew + Crushed Pepper: Def Penetration 12% → 4% applied",
    },
    "striker_sugar_shard": {
        "short": "스트라이커 설탕유리조각 : 쿠키에게 받는 피해, 모든 속성 내성 감소 6% → 3% 적용",
        "en_short": "Striker Sugarglass Shard: Cookie Damage Taken and All Elemental RES Reduction 6% → 3% applied",
    },
    "moonlight_dawn_damage_avg": {
        "short": "달빛술사 결코 잊지 못할 꿈 : 피해 증가 25% → 16.67% 적용",
        "en_short": "Moonlight - Unforgettable Dreams: +25% damage → +16.67%",
    },
}

STRIKER_COOKIES = (
    "윈드파라거스 쿠키",
    "룽샤맛 쿠키",
    "마블베리맛 쿠키",
    "체리콜라맛 쿠키",
)

# =====================================================
# Note-key helpers
# =====================================================
def _note_text(note_key: str, *, full: bool = False) -> str:
    note = ADJUSTMENT_NOTES.get(note_key, {})
    if _english_on():
        en_key = "en_full" if full else "en_short"
        if note.get(en_key):
            return str(note.get(en_key, ""))
    return str(note.get("full" if full else "short", ""))

def _adjustment_note_keys_for_seaz(seaz_name: str, owner_cookie_name: str = "") -> list[str]:
    name = str(seaz_name or "")
    owner = str(owner_cookie_name or "")
    keys = []
    # 달빛술사 쿠키가 플럼나이트:백마법사의 의지를 장착한 경우에는
    # 공격력 25%, 모든 속성 피해 30%를 그대로 적용하므로 12.5%/15% 보정 안내를 표시하지 않는다.
    if "백마법사의 의지" in name and owner != "달빛술사 쿠키":
        keys.append("seaz_white_mage")
    if "사냥꾼의 본능" in name:
        keys.append("seaz_hunter_instinct")
    return keys

def _adjustment_note_keys_for_equip(
    equip_name: str,
    owner_cookie_name: str = "",
    main_cookie_name: str = "",
) -> list[str]:
    name = str(equip_name or "")
    owner = str(owner_cookie_name or "")
    main = str(main_cookie_name or "")
    keys = []
    if name == "영원의 대마술사":
        keys.append("equip_magician")
    if name == "유성우의 향연":
        owner_elem = COOKIE_ELEMENT.get(owner, "")
        main_elem = COOKIE_ELEMENT.get(main, "")
        # 달빛술사 파티 장비 유성우는 신비 속성 딜러가 아니면 속성 내성 감소가 적용되지 않는다.
        if owner == "달빛술사 쿠키" and main and main != "달빛술사 쿠키" and owner_elem and main_elem and owner_elem != main_elem:
            keys.append("equip_meteor_zero")
        # 달빛술사가 메인일 때는 본인 유성우 10% 원값 적용 안내를 표시하지 않는다.
        elif owner == "달빛술사 쿠키" and main == "달빛술사 쿠키":
            pass
        # 파티 달빛술사가 유성우를 착용해 신비 딜러에게 적용되는 경우에만 안내를 표시한다.
        elif owner == "달빛술사 쿠키":
            keys.append("equip_meteor_moonlight")
        # 그 외에는 실제로 속성이 맞아 적용되는 유성우만 10% → 5% 보정 안내를 표시한다.
        elif (not owner_elem) or (not main_elem) or (owner_elem == main_elem):
            keys.append("equip_meteor")
    return keys

def _adjustment_note_keys_for_party(party_cookies: list[str]) -> list[str]:
    return ["party_lungsha"] if "룽샤맛 쿠키" in [str(x) for x in party_cookies] else []

def _adjustment_note_keys_for_main_cookie(main_cookie_name: str) -> list[str]:
    # [결코 잊지 못할 꿈]의 새벽녘 조건 피해 증가는
    # 달빛술사 쿠키가 메인일 때 본인 딜에만 평균 보정하므로,
    # 계산 보정 안내도 달빛술사 메인일 때만 표시한다.
    return ["moonlight_dawn_damage_avg"] if str(main_cookie_name or "") == "달빛술사 쿠키" else []

def _adjustment_note_keys_for_unique(cookie_name: str, unique_name: str) -> list[str]:
    cookie_name = str(cookie_name or "")
    unique_name = str(unique_name or "")
    if cookie_name == "이슬맛 쿠키" and unique_name == "크러쉬드페퍼맛 쿠키의 기억":
        return ["unique_crushed_isle"]
    return []

def _adjustment_note_keys_for_striker_sugar_shard(main_cookie: str, party_cookies: list[str]) -> list[str]:
    cookies = [main_cookie] + [str(x) for x in (party_cookies or []) if str(x or "").strip()]
    return ["striker_sugar_shard"] if any(str(x) in STRIKER_COOKIES for x in cookies) else []

def _merge_note_keys(*groups) -> list[str]:
    merged = []
    for group in groups:
        for key in (group or []):
            if key and key not in merged:
                merged.append(key)
    return merged

# =====================================================
# Render helpers
# =====================================================
def render_adjustment_summary(note_keys: list[str]):
    note_keys = _merge_note_keys(note_keys)
    if not note_keys:
        return

    rows = []
    for key in note_keys:
        text = _note_text(key, full=False)
        if text:
            safe_text = _html.escape(text) if _english_on() else _tr_html(text)
            rows.append(f"<li>{safe_text}</li>")
    if not rows:
        return

    rows_html = "\n".join(rows)
    st.markdown(
        f"""
        <details class="info-details adjustment-info-details">
          <summary>
            <span class="adjustment-summary-title label-word-wrap">{_tr_html("계산 보정 안내")}</span>
            <span class="ctl-help">i</span>
          </summary>
          <div class="adjustment-box">
            <ul>
              {rows_html}
            </ul>
          </div>
        </details>
        """,
        unsafe_allow_html=True,
    )
