"""Label, table, and result-stat rendering helpers for app.py."""

import html as _html
import math

import pandas as pd
import streamlit as st

import cookie_simulator as sim

from ui.translations import (
    _auto_wrap_label_class,
    _english_on,
    _tr_df,
    _tr_html,
    render_ctl_label,
)

# =====================================================
# Text and table render helpers
# =====================================================
def _kr_or_key(mapping: dict, k: str) -> str:
    return mapping.get(k, k)

def _help_text_to_li_html(help_text: str) -> str:
    lines = [x.strip() for x in str(help_text or "").split("\n") if x.strip()]
    if not lines:
        return ""
    return "\n".join(f"<li>{_tr_html(x)}</li>" for x in lines)

def render_info_details(title: str, help_text: str, *, title_class: str = "ctl-label"):
    rows_html = _help_text_to_li_html(help_text)
    wrap_cls = _auto_wrap_label_class(title)
    final_title_class = f"{title_class}{wrap_cls}"
    if not rows_html:
        st.markdown(f'<div class="{final_title_class}">{_tr_html(title)}</div>', unsafe_allow_html=True)
        return

    st.markdown(
        f"""
        <details class="info-details">
          <summary>
            <span class="{final_title_class}">{_tr_html(title)}</span>
            <span class="ctl-help">i</span>
          </summary>
          <div class="adjustment-box info-box">
            <ul>
              {rows_html}
            </ul>
          </div>
        </details>
        """,
        unsafe_allow_html=True,
    )

def render_ctl_label_with_help(label: str, help_text: str):
    render_info_details(label, help_text, title_class="ctl-label")

# =====================================================
# Label helpers
# =====================================================
# 계산 보정 안내 본문은 ui.adjustment_notes에서 관리
def render_seaz_label_with_adjustment(selected_seaz: str):
    # 계산 보정 문구는 세부사항 탭의 계산 보정 안내에서만 표시
    render_ctl_label("시즈나이트")

def render_party_label_with_adjustment(party_cookies: list[str]):
    # 계산 보정 문구는 세부사항 탭의 계산 보정 안내에서만 표시
    render_ctl_label("파티")

def render_main_equip_label_with_adjustment(kind: str, selected_equip: str, party_cookies: list[str] | None = None):
    # 딜러 자동 장비는 오래 걸릴 수 있어서 장비 라벨에만 안내를 붙인다.
    if kind in ("melan", "bb", "shining", "phoenix", "blue", "stardust"):
        party_cookies = party_cookies or []
        has_moonlight_party = "달빛술사 쿠키" in party_cookies
        if _english_on():
            if has_moonlight_party:
                base_help = (
                    "If you leave the equipment on Auto and run it, it may take a long time.\n"
                    "We recommend running it with TBD Uniform selected."
                )
            else:
                base_help = (
                    "If you leave the equipment on Auto and run it, it may take a long time.\n"
                    "We recommend running it with Sugar Feather selected."
                )
        else:
            if has_moonlight_party:
                base_help = (
                    "장비를 자동으로 두고 실행하면 오래 걸릴 수 있습니다.\n"
                    "시간관리국의 제복으로 두고 실행하는 것을 권장합니다."
                )
            else:
                base_help = (
                    "장비를 자동으로 두고 실행하면 오래 걸릴 수 있습니다.\n"
                    "달콤한 설탕 깃털로 두고 실행하는 것을 권장합니다."
                )
        render_ctl_label_with_help("장비", base_help)
    else:
        render_ctl_label("장비")

# =====================================================
# Table HTML helpers
# =====================================================
def hide_breeder_when_not_wind(cookie_name: str, options: list[str]) -> list[str]:
    # 윈드파라거스일 때만 "믿음직한 브리더" 노출
    if cookie_name == "윈드파라거스 쿠키":
        return options
    return [x for x in options if "믿음직한 브리더" not in str(x)]

def df_to_html_table(
    df: pd.DataFrame,
    small: bool = False,
    col_ratio=(0.38, 0.62),
    col_widths=None
) -> str:
    if df is None or df.empty:
        return ""

    safe = df.copy().reset_index(drop=True)

    def cell_html(x):
        s = "" if x is None else str(x)
        esc = _html.escape(s).replace("\n", "<br/>")
        tip = _html.escape(s)
        return f'<td title="{tip}">{esc}</td>'

    cls = "u-table small" if small else "u-table"
    ncol = len(safe.columns)

    widths = None
    if col_widths is not None and isinstance(col_widths, (list, tuple)) and len(col_widths) == ncol:
        widths = list(col_widths)
    elif ncol == 2 and col_ratio is not None and len(col_ratio) == 2:
        widths = [float(col_ratio[0]), float(col_ratio[1])]
    else:
        widths = [1.0 / ncol] * ncol

    ssum = sum(widths) if widths else 1.0
    widths = [(w / ssum) for w in widths]

    # 2열 요약표는 항목명 길이에 맞춰 1열 폭을 자동 산정한다.
    if (
        ncol == 2
        and list(safe.columns) == ["항목", "값"]
        and col_widths is None
    ):
        # 영어 모드에서 "Sugarglass Shard" 같은 긴 항목명이 표를 밀어내지 않도록
        # 항목 칸은 고정 폭으로 줄이고, 넘치는 항목명은 CSS ellipsis(...) 처리한다.
        if _english_on():
            first_col_em = 6.1
        else:
            label_values = [str(x) for x in safe["항목"].tolist()] + ["항목"]
            max_label_len = max((len(x) for x in label_values), default=2)
            first_col_em = max(4.8, min(max_label_len * 0.95 + 1.2, 9.0))

        # 들여쓰기 있는 멀티라인 HTML은 Streamlit markdown에서 코드처럼 보일 수 있음
        # - colgroup은 반드시 한 줄 문자열로 생성
        colgroup = (
            f'<colgroup>'
            f'<col style="width:{first_col_em:.2f}em">'
            f'<col>'
            f'</colgroup>'
        )

    elif (
        ncol == 3
        and list(safe.columns) == ["항목", "딜", "비율(%)"]
        and col_widths is None
    ):
        # Cycle Contribution 표는 3개 컬럼을 동일 폭으로 고정한다.
        colgroup = (
            '<colgroup>'
            '<col style="width:33.3333%">'
            '<col style="width:33.3333%">'
            '<col style="width:33.3333%">'
            '</colgroup>'
        )

    else:
        col_tags = "".join([f"<col style='width:{(w*100):.4f}%'>" for w in widths])
        colgroup = f"<colgroup>{col_tags}</colgroup>"

    display_safe = _tr_df(safe)
    ths = "".join([f"<th>{_html.escape(str(c))}</th>" for c in display_safe.columns])

    rows_html = []
    for _, row in display_safe.iterrows():
        tds = "".join([cell_html(row[c]) for c in display_safe.columns])
        rows_html.append(f"<tr>{tds}</tr>")

    body = "".join(rows_html)
    return f"""
    <table class="{cls}">
      {colgroup}
      <thead><tr>{ths}</tr></thead>
      <tbody>{body}</tbody>
    </table>
    """.strip()

def render_labeled_table(
    title: str,
    df: pd.DataFrame,
    small: bool = False,
    col_ratio=(0.38, 0.62),
    col_widths=None
):
    pill = f'<div class="stat-pill">{_tr_html(title)}</div>'

    if df is None or df.empty:
        body = f'<div class="u-empty">{_tr_html("표시할 항목 없음")}</div>'
    else:
        body = df_to_html_table(df, small=small, col_ratio=col_ratio, col_widths=col_widths)

    html = f"""
    <div class="stat-wrap">
      {pill}
      {body}
    </div>
    """.strip()

    st.markdown(html, unsafe_allow_html=True)

# =====================================================
# Final-stat table helpers
# =====================================================
def labeled_table_html(title: str, df: pd.DataFrame, small: bool = False, col_ratio=(0.38, 0.62), col_widths=None) -> str:
    pill = f'<div class="stat-pill">{_tr_html(title)}</div>'
    if df is None or df.empty:
        body = f'<div class="u-empty">{_tr_html("표시할 항목 없음")}</div>'
    else:
        body = df_to_html_table(df, small=small, col_ratio=col_ratio, col_widths=col_widths)
    return f'<div class="stat-wrap">{pill}{body}</div>'

def labeled_table_html_optional(
    title: str,
    df: pd.DataFrame,
    small: bool = False,
    col_ratio=(0.38, 0.62),
    col_widths=None
) -> str:
    if df is None or df.empty:
        return ""

    pill = f'<div class="stat-pill">{_tr_html(title)}</div>'
    body = df_to_html_table(df, small=small, col_ratio=col_ratio, col_widths=col_widths)
    return f'<div class="stat-wrap">{pill}{body}</div>'

def render_final_stats_grid(atk_df, crit_df, common_df, skill_df, surv_df, amp_df):
    items = []

    def add(title, df):
        # Final Stats 탭의 Item / Value 표 비중을 50:50으로 고정
        block = labeled_table_html_optional(title, df, small=False, col_widths=(0.5, 0.5))
        if block:
            items.append(f"<div>{block}</div>")

    add("공격력", atk_df)
    add("치명타", crit_df)
    add("피해 보정", common_df)
    add("스킬 타입 피해 증가", skill_df)
    add("(파티) 보호막 / 방어", surv_df)
    add("(파티) 버프 / 디버프 증폭", amp_df)

    html = "<div class='stat-grid'>" + "".join(items) + "</div>"
    st.markdown(html, unsafe_allow_html=True)

# =====================================================
# Potential and shard summary helpers
# =====================================================
def _normalize_item_label(label: str) -> str:
    s = str(label or "")
    return s.replace(" ", "").replace("%", "").replace("(", "").replace(")", "")

def _priority_named_value_rows(rows: list[dict]) -> pd.DataFrame:
    priority = [
        "속성공격력",
        "공격력",
        "치명타확률",
        "치명타피해",
        "버프증폭",
        "디버프증폭",
        "방어력관통",
    ]
    priority_map = {name: idx for idx, name in enumerate(priority)}

    def sort_key(row: dict):
        label = _normalize_item_label(row.get("항목", ""))
        for key, idx in priority_map.items():
            if key in label:
                return (idx, str(row.get("항목", "")))
        return (len(priority_map), str(row.get("항목", "")))

    ordered = sorted(rows, key=sort_key)
    return pd.DataFrame(ordered, columns=["항목", "값"])

# =====================================================
# Result table builders
# =====================================================
def pretty_potentials(pot: dict) -> pd.DataFrame:
    rows = []
    for k, v in (pot or {}).items():
        try:
            iv = int(v)
        except Exception:
            continue
        if iv >= 1:
            rows.append({"항목": _kr_or_key(getattr(sim, "POTENTIAL_KR", {}), k), "값": iv})
    return _priority_named_value_rows(rows)

def pretty_shards(shards: dict) -> pd.DataFrame:
    rows = []
    for k, v in (shards or {}).items():
        try:
            iv = int(v)
        except Exception:
            continue
        if iv >= 1:
            rows.append({"항목": _kr_or_key(getattr(sim, "SHARD_KR", {}), k), "값": iv})
    return _priority_named_value_rows(rows)

# =====================================================
# Cycle-breakdown table builder
# =====================================================
def cycle_breakdown_df(cb: dict) -> pd.DataFrame:
    name_map = {
        "breakdown_basic": "기본공격",
        "breakdown_special": "특수스킬",
        "breakdown_ult": "궁극기",
        "breakdown_charge": "차징",
        "breakdown_passive": "패시브",
        "breakdown_proc": "발동(세트/효과)",
        "breakdown_strike": "속성 강타",
        "breakdown_unique": "유니크",
    }

    rows = []
    total = 0.0
    for k, v in (cb or {}).items():
        if not str(k).startswith("breakdown_"):
            continue
        # 내부 검산용 세부 항목은 표에서 따로 표시하지 않음
        # - 특수스킬(일반) → 특수스킬 합계에 포함
        # - 강화특수스킬(패시브 피해) → 패시브 합계에 포함
        if k in {"breakdown_special_normal", "breakdown_enhanced_special_passive"}:
            continue
        try:
            fv = float(v)
        except Exception:
            continue
        if abs(fv) < 1e-12:
            continue
        total += fv
        rows.append((name_map.get(k, k.replace("breakdown_", "")), fv))

    if not rows or total == 0:
        return pd.DataFrame(columns=["항목", "딜", "비율(%)"])

    out = []
    for label, fv in sorted(rows, key=lambda x: x[1], reverse=True):
        pct = fv / total * 100.0
        out.append({
            "항목": label,
            "딜": f"{math.ceil(fv):,}",
            "비율(%)": f"{pct:.2f}",
        })
    return pd.DataFrame(out, columns=["항목", "딜", "비율(%)"])

# =====================================================
# Final-stat group builder
# - 값이 0인 항목은 숨긴다.
# - 치피는 총 치명타 피해(%) 기준으로 표시한다.
# - 패시브 피해는 최종 배율을 표시용 증가율로 변환한다.
# =====================================================
def build_stat_tables(stats: dict, cookie_name: str = "", party=None):
    stats = stats or {}
    party = party or []

    # summarize_effective_stats는 현재 sim 버전 기준 사용
    eff = sim.summarize_effective_stats(stats).get("numeric", {})

    def _f(d: dict, k: str, default=0.0) -> float:
        try:
            return float(d.get(k, default))
        except Exception:
            return float(default)

    def _fmt_num(x: float) -> str:
        if abs(x) >= 1000:
            s = f"{x:,.2f}"
            return s.rstrip("0").rstrip(".")
        s = f"{x:.4f}"
        return s.rstrip("0").rstrip(".")

    def _fmt_pct(x: float) -> str:
        return f"{x*100:.1f}%"

    def add_if_nonzero(rows, label, value_str, numeric_check, eps=1e-12):
        try:
            if abs(float(numeric_check)) < eps:
                return
        except Exception:
            return
        rows.append([label, value_str])

    # =========================
    # 공격력 (표시=합, 최종공격력 계산=곱환산)
    # =========================
    OA = _f(stats, "base_atk", 0.0) + _f(stats, "equip_atk_flat", 0.0)
    EA = _f(stats, "base_elem_atk", 0.0) + _f(stats, "elem_atk", 0.0)

    atk_pct_sum   = float(eff.get("atk_pct_sum", 0.0))         # 공퍼합
    atk_pct_equiv = float(eff.get("atk_pct_equiv", 0.0))
    final_atk_add = float(eff.get("final_atk_mult_add", 0.0))  # 버프공퍼합

    final_atk_input = float(eff.get("final_attack", 0.0))

    atk_rows = []
    add_if_nonzero(atk_rows, "OA(기본공)", _fmt_num(OA), OA)
    add_if_nonzero(atk_rows, "EA(속성공)", _fmt_num(EA), EA)
    add_if_nonzero(atk_rows, "공격력%", _fmt_pct(atk_pct_sum), atk_pct_sum)
    add_if_nonzero(atk_rows, "공격력 증가%", _fmt_pct(final_atk_add), final_atk_add)
    add_if_nonzero(atk_rows, "최종 공격력", _fmt_num(final_atk_input), final_atk_input)
    atk_df = pd.DataFrame(atk_rows, columns=["항목", "값"])

    # =========================
    # 치명 (치피는 "총 치피(%)"로 표시)
    # - eff_crit_dmg_total_pct: 예시 190.0
    # - eff_crit_dmg_mult: 예시 1.90
    # =========================
    crit_rows = []
    eff_cr = float(eff.get("eff_crit_rate", 0.0))
    add_if_nonzero(crit_rows, "치명타 확률", _fmt_pct(eff_cr), eff_cr)

    if cookie_name == "달빛술사 쿠키":
        dawn_cr_add = float(getattr(sim, "MOONLIGHT_DAWN_CRIT_RATE_ADD", 1.0))
        dawn_cr = min(1.0, max(0.0, eff_cr + dawn_cr_add))
        dawn_label = "Dawn CRIT Rate" if _english_on() else "새벽녘 치명타 확률"
        add_if_nonzero(crit_rows, dawn_label, _fmt_pct(dawn_cr), dawn_cr)

    cd_total_pct = float(eff.get("eff_crit_dmg_total_pct", 0.0))  # 190.0 같은 값
    cd_mult      = float(eff.get("eff_crit_dmg_mult", 1.0))        # 1.90

    # 총 치피가 0으로 들어오는 경우를 방어한다. 키 누락이나 구버전 eff를 대비
    if cd_total_pct <= 0.0:
        # 보정: 기존 eff_crit_dmg가 배율로 들어온 경우를 대비
        cd_mult_fallback = float(eff.get("eff_crit_dmg", cd_mult))
        cd_mult = cd_mult_fallback if cd_mult_fallback > 0 else cd_mult
        cd_total_pct = cd_mult * 100.0

    # 표시는 "190.0%"처럼 총치피로
    add_if_nonzero(crit_rows, "치명타 피해", f"{cd_total_pct:.1f}%", cd_mult - 1.0)
    crit_df = pd.DataFrame(crit_rows, columns=["항목", "값"])

    # =========================
    # 피해 보정
    # =========================
    common_rows = []
    add_if_nonzero(common_rows, "모든 속성 피해", _fmt_pct(float(eff.get("eff_all_elem_dmg", 0.0))), float(eff.get("eff_all_elem_dmg", 0.0)))
    add_if_nonzero(common_rows, "방어력 관통", _fmt_pct(float(eff.get("eff_armor_pen", 0.0))), float(eff.get("eff_armor_pen", 0.0)))

    add_if_nonzero(common_rows, "방어력 감소", _fmt_pct(float(eff.get("eff_def_reduction", 0.0))), float(eff.get("eff_def_reduction", 0.0)))
    add_if_nonzero(common_rows, "속성 내성 감소", _fmt_pct(float(eff.get("eff_elem_res_reduction", 0.0))), float(eff.get("eff_elem_res_reduction", 0.0)))

    add_if_nonzero(common_rows, "피해량", _fmt_pct(float(eff.get("dmg_bonus", 0.0))), float(eff.get("dmg_bonus", 0.0)))
    add_if_nonzero(common_rows, "속성 강타 피해", _fmt_pct(float(eff.get("element_strike_dmg", 0.0))), float(eff.get("element_strike_dmg", 0.0)))
    add_if_nonzero(common_rows, "강화 속성 표식", _fmt_pct(float(eff.get("element_mark_explosion_dmg", 0.0))), float(eff.get("element_mark_explosion_dmg", 0.0)))

    # 최종 피해는 summarize_effective_stats에만 의존하지 않고 stats에서 등가값으로 직접 계산
    final_dmg_add = float(stats.get("final_dmg", 0.0)) + float(stats.get("buff_final_dmg_raw", 0.0))
    promo_final_mult = float(stats.get("promo_final_dmg_mult", 1.0))
    final_dmg_equiv = (1.0 + final_dmg_add) * promo_final_mult - 1.0
    add_if_nonzero(common_rows, "최종 피해", _fmt_pct(final_dmg_equiv), final_dmg_equiv)

    common_df = pd.DataFrame(common_rows, columns=["항목", "값"])

    # =========================
    # 스킬 타입 피해 증가
    # =========================
    skill_rows = []
    add_if_nonzero(skill_rows, "기본공격 피해", _fmt_pct(_f(stats, "basic_dmg", 0.0)), _f(stats, "basic_dmg", 0.0))
    add_if_nonzero(skill_rows, "특수스킬 피해", _fmt_pct(_f(stats, "special_dmg", 0.0)), _f(stats, "special_dmg", 0.0))
    add_if_nonzero(skill_rows, "궁극기 피해", _fmt_pct(_f(stats, "ult_dmg", 0.0)), _f(stats, "ult_dmg", 0.0))
    add_if_nonzero(skill_rows, "받는 피해 증가", _fmt_pct(_f(stats, "dmg_taken_inc", 0.0)), _f(stats, "dmg_taken_inc", 0.0))
    add_if_nonzero(skill_rows, "적이 받는 피해 증가", _fmt_pct(_f(stats, "enemy_dmg_taken_inc", 0.0)), _f(stats, "enemy_dmg_taken_inc", 0.0))
    add_if_nonzero(skill_rows, "적이 받는 궁극기 피해", _fmt_pct(_f(stats, "enemy_ult_taken_inc", 0.0)), _f(stats, "enemy_ult_taken_inc", 0.0))

    # =========================
    # 패시브 스킬 피해
    # =========================
    p_add = float(stats.get("passive_dmg", 0.0))                 # add
    t_add = float(stats.get("enemy_passive_taken_inc", 0.0))     # add
    m     = float(stats.get("passive_dmg_mult", 1.0))            # mult (x1.20 등)

    total_no_promo = (1.0 + p_add) * (1.0 + t_add) * m

    add_if_nonzero(skill_rows, "패시브 피해", _fmt_pct(total_no_promo - 1.0), total_no_promo - 1.0)
    add_if_nonzero(skill_rows, "적이 받는 패시브 피해", _fmt_pct(t_add), t_add)

    skill_df = pd.DataFrame(skill_rows, columns=["항목", "값"])

    # =========================
    # 보호막/방어
    # =========================
    surv_rows = []
    add_if_nonzero(surv_rows, "보호막 %", _fmt_pct(_f(stats, "shield_pct", 0.0)), _f(stats, "shield_pct", 0.0))
    add_if_nonzero(surv_rows, "방어력 %", _fmt_pct(_f(stats, "def_pct", 0.0)), _f(stats, "def_pct", 0.0))
    surv_df = pd.DataFrame(surv_rows, columns=["항목", "값"])

    # =========================
    # 버프/디버프 증폭
    # =========================
    def pick_num(*keys, default=0.0):
        for k in keys:
            if k in eff and eff.get(k) is not None:
                try:
                    return float(eff.get(k))
                except Exception:
                    # 선택값 보정 실패는 앱 실행을 막지 않도록 무시한다.
                    pass
        for k in keys:
            if k in stats and stats.get(k) is not None:
                try:
                    return float(stats.get(k))
                except Exception:
                    # 선택값 보정 실패는 앱 실행을 막지 않도록 무시한다.
                    pass
        return float(default)

    buff_amp   = pick_num("party_buff_amp_total", "buff_amp_total")
    debuff_amp = pick_num("party_debuff_amp_total", "debuff_amp_total")

    amp_rows = []
    add_if_nonzero(amp_rows, "버프 증폭", _fmt_pct(buff_amp), buff_amp)
    add_if_nonzero(amp_rows, "디버프 증폭", _fmt_pct(debuff_amp), debuff_amp)
    amp_df = pd.DataFrame(amp_rows, columns=["항목", "값"])

    return atk_df, crit_df, common_df, skill_df, surv_df, amp_df

