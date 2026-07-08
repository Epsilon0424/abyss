# =====================================================
# Imports
# =====================================================
from .common import *
from .common import _resolve_unique_list_override
from .common import _clone_stats_for_loop, _apply_shards_inplace
from functools import lru_cache

# =====================================================
# 이슬맛 쿠키: DPS 사이클과 보호막 최적화
# =====================================================

# =====================================================
# Constants
# =====================================================
ISLE_PROMO_ENABLED = True
ISLE_WEAPON_ATK_PCT = 0.52
ISLE_WEAPON_BUFF_AMP = 0.24

# -----------------------------
# 고정 세팅
# -----------------------------
ISLE_FIXED_POT = {
    "elem_atk": 2,
    "buff_amp": 4,
    "atk_pct": 2,
    "crit_rate": 0,
    "crit_dmg": 0,
    "armor_pen": 0,
    "debuff_amp": 0,
}

ISLE_FIXED_UNIQUE   = "체리맛 쿠키의 기억"
ISLE_FIXED_ARTIFACT = "비에 젖은 과거"
ISLE_FIXED_EQUIP    = "전설의 유령해적"
FIXED_SEAZ_ISLE      = "허브그린드:번뜩이는 기지"

BASE_STATS_ISLE = {
    "이슬맛 쿠키": {
        "atk": 625.0,
        "friendship_atk": friendship_atk_for("이슬맛 쿠키"),
        "elem_atk": 0.0,
        # 전용무기 기본 옵션 공격력 +52%
        # 공격력 +8%는 표기 공격력에 이미 포함된 값이라 제외한다.
        "atk_pct": ISLE_WEAPON_ATK_PCT,
        "crit_rate": 0.15,
        "crit_dmg": 1.50,
        "armor_pen": 0.0,
        "final_dmg": 0.04,
        "buff_amp": 0.15 + ISLE_WEAPON_BUFF_AMP,  # 기본 버프 증폭 15% + 전용무기 버프 증폭 24%
    }
}

# -----------------------------
# 로테이션과 계수
# -----------------------------
ISLE_BASIC_COEFF   = 1.42 + 1.42 + 3.834   # 기본공격 3타 합산 계수 = 6.674

def _isle_action_step(tok: str) -> float:
    # 이슬맛 쿠키는 쿨타임/버프 상태를 시간축으로 처리해야 해서 내부 진행용 최소 간격만 둔다.
    if tok == "U":
        return 1.50
    if tok in ("S", "C"):
        return 0.25
    if tok in ("B", "B3"):
        return 2.50
    return 2.50
ISLE_SPECIAL_COEFF = (3.834 * 3) + 5.964   # 특수스킬 피해 계수 = 17.466

ISLE_ULT_HITS_PER_SEC = 1.0
ISLE_ULT_DURATION     = 15.0
ISLE_ULT_HIT_COEFF    = 3.124  # 궁극기 지속타 1회 피해 계수

ISLE_CHARGE_HITS      = 1
ISLE_CHARGE_HIT_COEFF = 1.491  # 차지 공격 1회 피해 계수

ISLE_SHADOW_HITS      = 1
ISLE_SHADOW_HIT_COEFF = 4.26  # 그림자/패시브 추가타 1회 피해 계수

# 사이클: 궁 → 차징 → 특 → 3평 × 3 → 차징 → 특 → 3평 × 3 → 차징 → 3평 × 3 → 차징
# B3는 기본공격 3타 합산(ISLE_BASIC_COEFF), C는 차징 공격을 의미한다.
ISLE_CYCLE_TOKENS = [
    "U", "C", "S",
    "B3", "B3", "B3",
    "C", "S",
    "B3", "B3", "B3",
    "C",
    "B3", "B3", "B3",
    "C",
]

# -----------------------------
# 버프와 패시브 파라미터
# -----------------------------
ISLE_STACK_MAX     = 6
ISLE_STACK_FROM_S  = 1
ISLE_STACK_FROM_U  = 2

ISLE_STRIKE_STACK_CD_BASE         = 8.0
ISLE_STRIKE_STACK_CD_PROMO_REDUCE = 4.0   # => 4초

ISLE_SHADOW_CD_BASE         = 12.0
ISLE_SHADOW_CD_PROMO_REDUCE = 3.0         # => 9초

ISLE_END_BUFF_ATK_PCT             = 0.224
ISLE_END_BUFF_DUR_BASE            = 8.0
ISLE_END_BUFF_DUR_PROMO_ADD       = 2.0

ISLE_CLEAR_DEAL_CRITDMG = 0.56
ISLE_CLEAR_DEAL_DUR     = 30.0

ISLE_PROMO_BASIC_DMG_CLEAR = 0.05
ISLE_PROMO_BASIC_DMG_END   = 0.05

ISLE_PROMO_ATK_MULT       = 1.0
ISLE_PROMO_FINAL_DMG_ADD  = 0.0
ISLE_PROMO_CHARGE_SHADOW_MULT = 1.20

ISLE_SHIELD_BASE_MULT = 1.008  # 보호막 기본 배율(공격력의 100.8%)

# =====================================================
# Helpers - 후보/보조 계산
# =====================================================
@lru_cache(maxsize=None)
def isle_generate_shard_candidates(target: str = "dps", step: int = 7) -> List[Dict[str, int]]:
    """
    - target="dps"   : step 기반 다축 탐색(기존 방식)
    - target="shield": 보호막 최적(정확 전수조사)
                      elem_atk + atk_pct + shield_pct = NORMAL_SLOTS (1칸 단위)
    """
    if target == "shield":
        out: List[Dict[str, int]] = []
        for ea in range(NORMAL_SLOTS + 1):
            for ap in range(NORMAL_SLOTS - ea + 1):
                sp = NORMAL_SLOTS - ea - ap
                out.append({
                    "elem_atk": ea,
                    "atk_pct": ap,
                    "shield_pct": sp,
                    # 스키마 맞추기(고정 0)
                    "crit_rate": 0,
                    "crit_dmg": 0,
                    "all_elem_dmg": 0,
                    "special_dmg": 0,
                    "ult_dmg": 0,
                    "basic_dmg": 0,
                    "passive_dmg": 0,
                })
        return out

    # target이 "dps"인 경우
    steps = list(range(0, NORMAL_SLOTS + 1, step))
    if steps[-1] != NORMAL_SLOTS:
        steps.append(NORMAL_SLOTS)

    out: List[Dict[str, int]] = []
    for cr in steps:
        for cd in steps:
            for ae in steps:
                for ap in steps:
                    for sd in steps:
                        for ud in steps:
                            used = cr + cd + ae + ap + sd + ud
                            if used > NORMAL_SLOTS:
                                continue
                            ea = NORMAL_SLOTS - used
                            out.append({
                                "crit_rate": cr,
                                "crit_dmg": cd,
                                "all_elem_dmg": ae,
                                "atk_pct": ap,
                                "special_dmg": sd,
                                "ult_dmg": ud,
                                "elem_atk": ea,
                                "basic_dmg": 0,
                                "passive_dmg": 0,
                                "shield_pct": 0,  # DPS 탐색에서는 0으로 고정
                            })
    return out

def isle_calc_shield_detail(stats: Dict[str, float]) -> Dict[str, float]:
    """샬롯 회복량 계산처럼 이슬 보호막량을 상세 계산한다.

    보호막 = 최종 공격력 × (1 + 보호막%) × 100.8%
    최적화는 이 값이 가장 큰 설탕유리조각 조합을 우선 선택한다.
    """
    final_atk = calc_attack_value(stats, floor_result=False)
    shield_pct = float(stats.get("shield_pct", 0.0))
    shield = final_atk * (1.0 + shield_pct) * ISLE_SHIELD_BASE_MULT
    return {
        "final_atk": final_atk,
        "shield_pct": shield_pct,
        "shield_base_mult": ISLE_SHIELD_BASE_MULT,
        "max_shield": shield,
    }

def _isle_apply_passive_start_effect(base_stats: Dict[str, float]) -> Dict[str, float]:
    """전투 시작: 버프증폭의 50%만큼 치확 증가(최대 +60%)"""
    st = dict(base_stats)
    BA = float(st.get("buff_amp", 0.0))
    add_cr = min(0.60, 0.50 * BA)
    st["buff_crit_rate_raw"] = float(st.get("buff_crit_rate_raw", 0.0)) + add_cr
    return st

# =====================================================
# Calculation - 사이클 딜
# =====================================================
def isle_cycle_damage(stats: Dict[str, float], party: List[str], artifact_name: str) -> Dict[str, float]:
    horizon = 30.0
    promo_on = bool(ISLE_PROMO_ENABLED)

    base_for_sim = dict(stats)
    if promo_on:
        base_for_sim["base_atk"] = float(base_for_sim.get("base_atk", 0.0)) * ISLE_PROMO_ATK_MULT
        base_for_sim["final_dmg"] = float(base_for_sim.get("final_dmg", 0.0)) + ISLE_PROMO_FINAL_DMG_ADD

    base_for_sim = _isle_apply_passive_start_effect(base_for_sim)

    s_cd = 10.0
    u_cd = 30.0

    strike_cd = ISLE_STRIKE_STACK_CD_BASE - (ISLE_STRIKE_STACK_CD_PROMO_REDUCE if promo_on else 0.0)
    strike_cd = max(0.0, strike_cd)

    shadow_cd = ISLE_SHADOW_CD_BASE - (ISLE_SHADOW_CD_PROMO_REDUCE if promo_on else 0.0)
    shadow_cd = max(0.0, shadow_cd)

    end_dur = ISLE_END_BUFF_DUR_BASE + (ISLE_END_BUFF_DUR_PROMO_ADD if promo_on else 0.0)

    t = 0.0
    next_s = 0.0
    next_u = 0.0
    next_strike_stack = 0.0
    next_shadow_ready = 0.0

    stacks = 3 if promo_on else 0

    end_buff_until = -1.0
    clear_deal_until = -1.0
    abyss_until = -1.0

    abyss_amt = 0.0
    abyss_dur = 0.0
    if artifact_name == "비에 젖은 과거":
        meta = ARTIFACTS[artifact_name].get("abyss", {}) or {}
        abyss_amt = float(meta.get("all_elem_dmg", 0.0))
        abyss_dur = float(meta.get("duration", 0.0))

    total_direct = 0.0
    total_time = 0.0

    breakdown = {
        "basic": 0.0,
        "special": 0.0,
        "ult": 0.0,
        "proc": 0.0,
        "strike": 0.0,
        "unique": 0.0,
    }

    def cur_stats_at(time_now: float) -> Dict[str, float]:
        st = dict(base_for_sim)

        if time_now < clear_deal_until:
            BA = float(st.get("buff_amp", 0.0))
            scale = 1.0 + BA
            st["buff_crit_dmg_raw"] = float(st.get("buff_crit_dmg_raw", 0.0)) + ISLE_CLEAR_DEAL_CRITDMG * scale
            if promo_on:
                st["basic_dmg"] = float(st.get("basic_dmg", 0.0)) + ISLE_PROMO_BASIC_DMG_CLEAR

        if time_now < end_buff_until:
            BA = float(st.get("buff_amp", 0.0))
            scale = 1.0 + BA
            st["buff_atk_pct_raw"] = float(st.get("buff_atk_pct_raw", 0.0)) + ISLE_END_BUFF_ATK_PCT * scale
            if promo_on:
                st["basic_dmg"] = float(st.get("basic_dmg", 0.0)) + ISLE_PROMO_BASIC_DMG_END

        if abyss_amt > 0 and time_now < abyss_until:
            BA = float(st.get("buff_amp", 0.0))
            scale = 1.0 + BA
            st["buff_all_elem_dmg_raw"] = float(st.get("buff_all_elem_dmg_raw", 0.0)) + abyss_amt * scale

        return st

    def apply_sonagi_trigger(time_now: float) -> None:
        nonlocal abyss_until
        if abyss_dur > 0:
            abyss_until = max(abyss_until, time_now + abyss_dur)

    def update_strike_stacks(time_now: float) -> None:
        nonlocal stacks, next_strike_stack
        has_marker = ("윈드파라거스 쿠키" in party)
        if not has_marker or strike_cd <= 0:
            return
        while time_now >= next_strike_stack - 1e-9:
            stacks = min(ISLE_STACK_MAX, stacks + 1)
            next_strike_stack += strike_cd

    for tok in ISLE_CYCLE_TOKENS:
        if t >= horizon - 1e-9:
            break

        update_strike_stacks(t)

        if tok == "U":
            st = cur_stats_at(t)

            hits = int(ISLE_ULT_DURATION * ISLE_ULT_HITS_PER_SEC + 1e-9)
            coeff = ISLE_ULT_HIT_COEFF * hits
            dmg = skill_damage_from_start(st, coeff, "ult")

            total_direct += dmg
            breakdown["ult"] += dmg
            apply_sonagi_trigger(t)

            clear_deal_until = max(clear_deal_until, t + ISLE_CLEAR_DEAL_DUR)
            stacks = min(ISLE_STACK_MAX, stacks + ISLE_STACK_FROM_U)

            dt = _isle_action_step("U")
            t += dt
            total_time += dt
            continue

        if tok == "S":
            st = cur_stats_at(t)

            dmg = skill_damage_from_start(st, ISLE_SPECIAL_COEFF, "special")
            total_direct += dmg
            breakdown["special"] += dmg
            apply_sonagi_trigger(t)

            stacks = min(ISLE_STACK_MAX, stacks + ISLE_STACK_FROM_S)

            dt = _isle_action_step("S")
            t += dt
            total_time += dt
            continue

        if tok == "C":
            st = cur_stats_at(t)

            ch_coeff = ISLE_CHARGE_HIT_COEFF * int(ISLE_CHARGE_HITS)
            ch_dmg = skill_damage_from_start(st, ch_coeff, "special")

            if promo_on:
                ch_dmg *= ISLE_PROMO_CHARGE_SHADOW_MULT

            total_direct += ch_dmg
            breakdown["special"] += ch_dmg
            apply_sonagi_trigger(t)

            # 그림자/패시브 추가타는 기존 조건을 유지한다.
            # 스택 3개 이상 + 내부 쿨타임 준비 상태일 때만 발동하고, 발동 시 스택 3개를 소비한다.
            if stacks >= 3 and t >= next_shadow_ready - 1e-9:
                sh_coeff = ISLE_SHADOW_HIT_COEFF * int(ISLE_SHADOW_HITS)
                sh_dmg = skill_damage_from_start(st, sh_coeff, "special")
                if promo_on:
                    sh_dmg *= ISLE_PROMO_CHARGE_SHADOW_MULT

                total_direct += sh_dmg
                breakdown["proc"] += sh_dmg

                stacks -= 3
                end_buff_until = max(end_buff_until, t + end_dur)
                next_shadow_ready = t + shadow_cd

            dt = _isle_action_step("C")
            t += dt
            total_time += dt
            continue

        if tok in ("B", "B3"):
            st = cur_stats_at(t)

            dmg = skill_damage_from_start(st, ISLE_BASIC_COEFF, "basic")
            total_direct += dmg
            breakdown["basic"] += dmg

            dt = _isle_action_step("B3")
            t += dt
            total_time += dt
            continue

    strike = strike_total_from_direct(total_direct, "이슬맛 쿠키", base_for_sim, party)
    breakdown["strike"] = strike

    unique_total = skill_damage_from_start(cur_stats_at(0.0), float(base_for_sim.get("unique_extra_coeff", 0.0)), "none") * 30.0
    breakdown["unique"] = unique_total

    total_damage = math.floor(total_direct + strike + unique_total)
    dps = total_damage / 30.0

    return {
        "total_damage": total_damage,
        "total_time": 30.0,
        "dps": dps,
        "breakdown_basic": breakdown["basic"],
        "breakdown_special": breakdown["special"],
        "breakdown_ult": breakdown["ult"],
        "breakdown_proc": breakdown["proc"],
        "breakdown_strike": breakdown["strike"],
        "breakdown_unique": breakdown["unique"],
    }

def optimize_isle_cycle(
    seaz_name: str,
    party: List[str],
    party_seaz: Optional[Dict[str, str]] = None,
    party_uniques: Optional[Dict[str, str]] = None,
    party_sets: Optional[Dict[str, str]] = None,
    step: int = 1,
    progress_cb: Optional[Callable[[float], None]] = None,
    equip_override: Optional[Union[str, List[str], Tuple[str, ...], set]] = None,
    unique_override: Optional[Union[str, List[str], Tuple[str, ...], set]] = None,
) -> Optional[dict]:

    cookie = "이슬맛 쿠키"
    base = BASE_STATS_ISLE[cookie].copy()

    # 기본 장비는 해적셋, 메인 수동 선택 시 대마술사/해적셋 허용
    equip_name    = ISLE_FIXED_EQUIP
    if isinstance(equip_override, str) and equip_override.strip():
        equip_name = equip_override.strip()
    artifact_name = ISLE_FIXED_ARTIFACT
    uniques = _resolve_unique_list_override(unique_override, [ISLE_FIXED_UNIQUE])
    unique_name = uniques[0] if uniques else ISLE_FIXED_UNIQUE
    pot           = ISLE_FIXED_POT

    shard_candidates = isle_generate_shard_candidates(target="shield", step=step)

    total = max(1, len(shard_candidates))
    done = 0
    tick = max(1, total // 150)

    def emit(p: float) -> None:
        if not progress_cb:
            return
        try:
            progress_cb(p)
        except Exception:
            # 진행률 콜백 오류는 최적화 계산 결과에 영향이 없으므로 무시한다.
            pass

    emit(0.0)
    best: Optional[dict] = None

    zero_shards = {k: 0 for k in SHARD_INC.keys()}

    # template(설유 0)
    stats_template = build_stats_for_combo(
        cookie_name_kr=cookie,
        base=base,
        shards=zero_shards,
        potentials=pot,
        equip_name=equip_name,
        seaz_name=seaz_name,
        unique_name=unique_name,
        party=party,
        artifact_name=artifact_name,
        party_seaz=party_seaz,
        party_uniques=party_uniques,
                        party_sets=party_sets,
    )
    if not is_valid_by_caps(stats_template):
        emit(1.0)
        return None

    for shards in shard_candidates:
        done += 1
        if (done % tick) == 0:
            emit(done / total)

        stats = _clone_stats_for_loop(stats_template)
        _apply_shards_inplace(stats, shards)

        # template cap 검사를 이미 통과했고 설탕유리조각은 방어관통을 올리지 않으므로 재검사 생략

        shield_detail = isle_calc_shield_detail(stats)
        shield = float(shield_detail["max_shield"])
        cycle  = isle_cycle_damage(stats, party, artifact_name)

        cur = {
            "cookie": cookie,
            "dps": cycle["dps"],
            "cycle_total_damage": cycle["total_damage"],
            "cycle_total_time": 30.0,
            "cycle_breakdown": cycle,
            "max_shield": shield,
            "shield_detail": shield_detail,

            # 고정키
            "equip_fixed": equip_name,
            "seaz_fixed": seaz_name,
            "unique_fixed": unique_name,
            "artifact_fixed": artifact_name,
            "potentials_fixed": pot,

            # 호환키
            "equip": equip_name,
            "seaz": seaz_name,
            "unique": unique_name,
            "artifact": artifact_name,
            "potentials": pot,

            "shards": {
                "elem_atk": int(shards.get("elem_atk", 0)),
                "atk_pct": int(shards.get("atk_pct", 0)),
                "shield_pct": int(shards.get("shield_pct", 0)),
            },
            "party": party,
            "party_seaz": dict(party_seaz or {}),
            "party_sets": dict(party_sets or {}),
            "party_uniques": dict(party_uniques or {}),
            "stats": stats,
            "buff_amp_total": stats.get("buff_amp_total", stats.get("buff_amp", 0.0)),
            "debuff_amp_total": stats.get("debuff_amp_total", stats.get("debuff_amp", 0.0)),
        }

        if best is None:
            best = cur
        else:
            if cur["max_shield"] > best["max_shield"] + 1e-9:
                best = cur
            elif abs(cur["max_shield"] - best["max_shield"]) <= 1e-9 and cur["dps"] > best["dps"]:
                best = cur

    emit(1.0)
    return best
