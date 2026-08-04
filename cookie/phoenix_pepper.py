# =====================================================
# Imports
# =====================================================
from .common import *
from .common import _resolve_equip_list_override, _min_crit_slots_needed_for_crit100_generic, _resolve_unique_list_override
from functools import lru_cache
from typing import Sequence

# =====================================================
# 피닉스페퍼 쿠키
# =====================================================

# =====================================================
# Constants
# =====================================================
PHOENIX_PEPPER_PROMO_ENABLED = True
PHOENIX_PEPPER_FORCE_CRIT_100 = True
PHOENIX_PEPPER_WEAPON_ATK_PCT = 0.52
PHOENIX_PEPPER_WEAPON_FINAL_DMG = 0.30
PHOENIX_PEPPER_PROMO_ULT_DMG_MULT = 1.45
PHOENIX_PEPPER_PROMO_PASSIVE_DMG_MULT = 1.80

BASE_STATS_PHOENIX_PEPPER = {
    "피닉스페퍼 쿠키": {
        "atk": 715.0,
        "friendship_atk": friendship_atk_for("피닉스페퍼 쿠키"),
        "def": 382.0,
        "hp": 4256.0,
        "elem_atk": 0.0,
        # 전용무기 기본 옵션 공격력 +52%
        "atk_pct": PHOENIX_PEPPER_WEAPON_ATK_PCT,
        "crit_rate": 0.15,
        "crit_dmg": 1.875,
        "armor_pen": 0.0,
        # 승급/기본 최종 피해 +5% + 전용무기 고유능력 최종 피해 +30%
        "final_dmg": 0.05 + PHOENIX_PEPPER_WEAPON_FINAL_DMG,
    }
}

PHOENIX_BASIC_COEFF = (1.42 * 3.0) + (1.562 * 3.0) + 9.088 + 9.088  # 기본공격 [불꽃의 춤] 1~4타 합산 피해 계수: 142%×3 + 156.2%×3 + 908.8% + 908.8%
PHOENIX_DASH_COEFF = 1.3064 * 4.0  # 대시 [낙화] 홀드 피해 계수: 130.64%×4, 현재 30초 사이클 계산에는 미사용

PHOENIX_SPECIAL1_COEFF = 5.439 * 2.0  # 특수스킬 [생동] 피해 계수: 543.9%×2
PHOENIX_SPECIAL2_COEFF_BASE = 1.69 * 10.0  # 특수스킬 [충만] 피해 계수: 169%×10
PHOENIX_SPECIAL3_COEFF_BASE = 13.206  # 특수스킬 [회귀] 피해 계수: 1320.6%
PHOENIX_SPECIAL2_COEFF_ARTI = (1.19 * 10.0) + (8.88 * 3.0)  # 아티팩트 [타오르는 생의 시작] 적용 특수스킬 [충만:진] 피해 계수: 119%×10 + 888%×3, 궁극기 피해 취급
PHOENIX_SPECIAL3_COEFF_ARTI = 8.88 * 3.0  # 아티팩트 [타오르는 생의 시작] 적용 특수스킬 [회귀:진] 피해 계수: 888%×3, 궁극기 피해 취급

PHOENIX_PASSIVE_COEFF = 9.869  # 패시브 [타오르는 정열] - [마음의 불티] 피해 계수: 986.9%, 궁극기 피해 취급
PHOENIX_ULT1_COEFF = 5.893 * 7.0  # 궁극기 [우화비천] 피해 계수: 589.3%×7
PHOENIX_ULT2_COEFF = 5.893 * 7.0  # 궁극기 [천략우화] 피해 계수: 589.3%×7
PHOENIX_ULT3_COEFF = 18.2754 * 8.0  # 궁극기 [천지재화] 피해 계수: 1827.54%×8

PHOENIX_CYCLE_TIME = 30.0
PHOENIX_GREAT_RULER_SEAZ = "레몬그라스톤:위대한 통치자"
# 위대한 통치자 메인 효과(궁극기 사용 후 15초)가 끊긴 상태에서 사용하는 궁극기 위치.
# 해당 궁극기는 시즈 보조 옵션은 유지하고, 메인 효과의 궁극기 피해 증가만 제외한다.
PHOENIX_GREAT_RULER_INACTIVE_ULT_POSITIONS = frozenset({
    (0, 10),  # 1사이클 마지막 궁1
    (1, 12),  # 2사이클 마지막 궁2
    (2, 0),   # 3사이클 첫 궁3
})
PHOENIX_ROTATION_CYCLES = (
    # 1사이클: 특특특 궁1 4평 4평 특특특 궁2궁3 4평 4평 특특특 궁1
    ("TRI", "U1", "B4", "B4", "TRI", "U2", "U3", "B4", "B4", "TRI", "U1"),
    # 2사이클: 4평 4평 특특특 궁2궁3 4평 4평 특특특 궁1 4평 4평 특특특 궁2
    ("B4", "B4", "TRI", "U2", "U3", "B4", "B4", "TRI", "U1", "B4", "B4", "TRI", "U2"),
    # 3사이클: 궁3 4평 4평 특특특 궁1 4평 4평 특특특 궁2 궁3 4평 4평
    ("U3", "B4", "B4", "TRI", "U1", "B4", "B4", "TRI", "U2", "U3", "B4", "B4"),
)
PHOENIX_ROTATION_TOKENS = tuple(
    token
    for cycle_tokens in PHOENIX_ROTATION_CYCLES
    for token in cycle_tokens
)

# =====================================================
# Helpers - 히트/이벤트 계산
# =====================================================
def _phoenix_rotation_hits(tokens: Sequence[str], artifact_name: str) -> int:
    """90초 연속 회전에서 마음의 불티 발동 판정에 사용되는 총 타수를 계산한다."""
    arti_on = artifact_name == "타오르는 생의 시작"
    tri_hits = (2 + 13 + 3) if arti_on else (2 + 10 + 1)
    hit_counts = {
        "B4": 3 + 3 + 1 + 1,
        "TRI": tri_hits,
        "U1": 7,
        "U2": 7,
        "U3": 8,
    }
    return sum(hit_counts[token] for token in tokens)

# =====================================================
# Calculation - 사이클 딜
# =====================================================
def phoenix_pepper_cycle_damage_fast(
    stats: Dict[str, float],
    party: List[str],
    artifact_name: str,
    seaz_name: str = "",
) -> Dict[str, float]:
    cycle_count = len(PHOENIX_ROTATION_CYCLES)
    total_time = PHOENIX_CYCLE_TIME * cycle_count
    # 세 개의 30초 사이클을 90초 연속 회전으로 계산한 뒤 30초 평균값으로 환산한다.
    # 스킬별 처음부터 계산: skill_damage_from_start 사용

    # 승급 배율
    # - [깨지지 않는 불꽃]은 [우화비천]/[천략우화]/[천지재화] 피해 +45%라서 궁극기 본체 3종에만 별도 적용한다.
    # - [뜨겁게 피어나는 마음]은 [마음의 불티] 피해 +80%라서 마음의 불티에만 별도 적용한다.
    # - [충만:진]/[회귀:진]과 [마음의 불티]는 "궁극기 피해 취급"이므로 ult_dmg/enemy_ult_taken_inc 축은 받지만,
    #   [우화비천]/[천략우화]/[천지재화] 전용 45% 승급 배율은 받지 않는 것으로 계산한다.
    promo_ult_mult = float(
        stats.get(
            "promo_ult_dmg_mult",
            PHOENIX_PEPPER_PROMO_ULT_DMG_MULT if PHOENIX_PEPPER_PROMO_ENABLED else 1.0,
        )
    )
    ember_extra_mult = float(
        stats.get(
            "promo_passive_dmg_mult",
            PHOENIX_PEPPER_PROMO_PASSIVE_DMG_MULT if PHOENIX_PEPPER_PROMO_ENABLED else 1.0,
        )
    )

    arti_on = (artifact_name == "타오르는 생의 시작")
    s2_coeff = PHOENIX_SPECIAL2_COEFF_ARTI if arti_on else PHOENIX_SPECIAL2_COEFF_BASE
    s3_coeff = PHOENIX_SPECIAL3_COEFF_ARTI if arti_on else PHOENIX_SPECIAL3_COEFF_BASE

    breakdown = {
        "basic": 0.0,
        "special": 0.0,
        "ult": 0.0,
        "passive": 0.0,
        "proc": 0.0,
        "strike": 0.0,
        "unique": 0.0,
    }

    # 같은 스탯에서 동일한 스킬 피해는 매번 같으므로 90초 회전마다 한 번만 계산한다.
    # 이후 기존 토큰 순서대로 누적해 계산 결과는 유지하면서 최적화 반복 시간을 줄인다.
    basic_unit = skill_damage_from_start(stats, PHOENIX_BASIC_COEFF, "basic")
    special1_unit = skill_damage_from_start(stats, PHOENIX_SPECIAL1_COEFF, "special")
    # [충만:진]/[회귀:진]은 궁극기 피해 취급이라 skill_type="ult"로 계산하지만,
    # 승급 [깨지지 않는 불꽃]의 45%는 궁극기 본체 3종 전용이라 여기에는 별도로 곱하지 않는다.
    special2_unit = skill_damage_from_start(stats, s2_coeff, "ult")
    special3_unit = skill_damage_from_start(stats, s3_coeff, "ult")
    ult1_unit = skill_damage_from_start(
        stats, PHOENIX_ULT1_COEFF, "ult", extra_skill_mult=promo_ult_mult
    )
    ult2_unit = skill_damage_from_start(
        stats, PHOENIX_ULT2_COEFF, "ult", extra_skill_mult=promo_ult_mult
    )
    ult3_unit = skill_damage_from_start(
        stats, PHOENIX_ULT3_COEFF, "ult", extra_skill_mult=promo_ult_mult
    )
    ult_units = {"U1": ult1_unit, "U2": ult2_unit, "U3": ult3_unit}

    # 위대한 통치자는 보조 옵션 궁극기 피해 +30%와 메인 효과 +30%가 합쳐져
    # 효과 유지 중에는 총 +60%가 적용된다. 사용자가 표시한 세 궁극기에는
    # 15초 메인 효과만 끊긴 것으로 보고, 보조 옵션 +30%는 그대로 유지한다.
    inactive_ult_units: Dict[str, float] = {}
    if seaz_name == PHOENIX_GREAT_RULER_SEAZ:
        seaz_info = SEAZNITES.get(seaz_name, {}) or {}
        great_ruler_main_bonus = float(
            ((seaz_info.get("passive", {}) or {}).get("ult_dmg", 0.0))
        )
        if great_ruler_main_bonus:
            inactive_stats = dict(stats)
            inactive_stats.pop("_damage_context_cache", None)
            inactive_stats["ult_dmg"] = (
                float(inactive_stats.get("ult_dmg", 0.0)) - great_ruler_main_bonus
            )
            inactive_ult_units = {
                "U1": skill_damage_from_start(
                    inactive_stats,
                    PHOENIX_ULT1_COEFF,
                    "ult",
                    extra_skill_mult=promo_ult_mult,
                ),
                "U2": skill_damage_from_start(
                    inactive_stats,
                    PHOENIX_ULT2_COEFF,
                    "ult",
                    extra_skill_mult=promo_ult_mult,
                ),
                "U3": skill_damage_from_start(
                    inactive_stats,
                    PHOENIX_ULT3_COEFF,
                    "ult",
                    extra_skill_mult=promo_ult_mult,
                ),
            }

    total_direct = 0.0
    for cycle_index, cycle_tokens in enumerate(PHOENIX_ROTATION_CYCLES):
        for token_index, tok in enumerate(cycle_tokens):
            if tok == "B4":
                dmg = basic_unit
                breakdown["basic"] += dmg
            elif tok == "TRI":
                dmg = special1_unit + special2_unit + special3_unit
                breakdown["special"] += special1_unit
                breakdown["ult"] += special2_unit + special3_unit
            elif tok in ult_units:
                use_inactive_unit = (
                    bool(inactive_ult_units)
                    and (cycle_index, token_index) in PHOENIX_GREAT_RULER_INACTIVE_ULT_POSITIONS
                )
                dmg = inactive_ult_units[tok] if use_inactive_unit else ult_units[tok]
                breakdown["ult"] += dmg
            else:
                raise ValueError(f"알 수 없는 피닉스페퍼 사이클 토큰입니다: {tok}")
            total_direct += dmg

    # 마음의 불티 카운트는 30초마다 초기화하지 않고 90초 연속 타수에 대해 누적한다.
    ember_hits = _phoenix_rotation_hits(PHOENIX_ROTATION_TOKENS, artifact_name)
    ember_procs = ember_hits // 10
    # [마음의 불티]는 발생 조건은 패시브지만 실제 피해는 궁극기 피해 취급이다.
    # 따라서 skill_type="ult"로 계산하고, 별도로 승급 [뜨겁게 피어나는 마음] +80%만 곱한다.
    ember_total = skill_damage_from_start(stats, PHOENIX_PASSIVE_COEFF, "ult", extra_skill_mult=ember_extra_mult) * ember_procs

    # 마음의 불티 피해는 궁극기 피해에 합산
    breakdown["ult"] += ember_total
    breakdown["passive"] = 0.0

    ult_count = sum(1 for token in PHOENIX_ROTATION_TOKENS if token.startswith("U"))
    sugar_proc = skill_damage_from_start(stats, float(stats.get("sugar_brilliance_coeff", 0.0)), "none") * ult_count
    if sugar_proc:
        total_direct += sugar_proc
        breakdown["proc"] += sugar_proc

    strike = strike_total_from_direct(total_direct + ember_total, "피닉스페퍼 쿠키", stats, party)
    breakdown["strike"] = strike

    unique_total = skill_damage_from_start(stats, float(stats.get("unique_extra_coeff", 0.0)), "none") * total_time
    breakdown["unique"] = unique_total

    rotation_total_damage = math.floor(total_direct + ember_total + strike + unique_total)

    local_raw = stats.get("_local", None)
    local: Dict[str, Any] = local_raw if isinstance(local_raw, dict) else {}
    elem_dmg_mult = float(local.get("elem_dmg_mult", stats.get("elem_dmg_mult", 1.0)))
    if elem_dmg_mult != 1.0:
        rotation_total_damage *= elem_dmg_mult
        for k in breakdown:
            breakdown[k] *= elem_dmg_mult

    # RESULT에는 다른 쿠키와 동일하게 30초 기준 평균 사이클 총딜과 DPS를 표시한다.
    average_cycle_damage = rotation_total_damage / cycle_count
    average_breakdown = {key: value / cycle_count for key, value in breakdown.items()}
    dps = rotation_total_damage / total_time
    return {
        "total_damage": average_cycle_damage,
        "total_time": PHOENIX_CYCLE_TIME,
        "dps": dps,
        "rotation_total_damage": rotation_total_damage,
        "rotation_total_time": total_time,
        "rotation_cycle_count": cycle_count,
        "rotation_total_hits": ember_hits,
        "rotation_ember_procs": ember_procs,
        "breakdown_basic": average_breakdown["basic"],
        "breakdown_special": average_breakdown["special"],
        "breakdown_ult": average_breakdown["ult"],
        "breakdown_passive": average_breakdown["passive"],
        "breakdown_proc": average_breakdown["proc"],
        "breakdown_strike": average_breakdown["strike"],
        "breakdown_unique": average_breakdown["unique"],
    }

# =====================================================
# Helpers - 장비/후보 생성
# =====================================================
def phoenix_pepper_allowed_equips() -> List[str]:
    return ["달콤한 설탕 깃털", "미지의 방랑자", "수상한 사냥꾼", "시간관리국의 제복"]

def phoenix_pepper_allowed_uniques() -> List[str]:
    return ["로드 나이트메어의 뒤틀린 기억"]

def phoenix_pepper_allowed_artifacts() -> List[str]:
    return ["타오르는 생의 시작"]

def phoenix_pepper_allowed_seaz() -> List[str]:
    return [x for x in SEAZNITES.keys() if str(x).startswith("레몬그라스톤:")]

@lru_cache(maxsize=None)
def phoenix_pepper_generate_potentials_common() -> List[Dict[str, int]]:
    """
    피닉스페퍼 잠재력 후보를 생성한다.

    - 총 8칸 중 속성 공격력 2칸은 기존처럼 고정한다.
    - 남은 6칸에서 치명타 확률도 함께 탐색한다.
    - 각 잠재력 후보마다 치확 100%에 필요한 설탕유리조각 칸을 다시 계산하므로,
      조각으로 치확을 넘겨 맞추는 조합과 잠재력으로 조각 칸을 줄이는 조합을
      실제 DPS로 비교할 수 있다.
    """
    total = 8
    fixed_elem = 2
    free = total - fixed_elem
    keys = ["crit_rate", "atk_pct", "crit_dmg", "armor_pen"]
    cap = {"armor_pen": min(4, free)}
    out: List[Dict[str, int]] = []

    def dfs(i: int, remain: int, cur: Dict[str, int]) -> None:
        if i == len(keys):
            if remain == 0:
                p = dict(cur)
                p["elem_atk"] = fixed_elem
                p["buff_amp"] = 0
                p["debuff_amp"] = 0
                out.append(p)
            return
        k = keys[i]
        lim = min(remain, cap.get(k, remain))
        for x in range(lim + 1):
            cur[k] = x
            dfs(i + 1, remain - x, cur)
        cur.pop(k, None)

    dfs(0, free, {})
    return out

@lru_cache(maxsize=None)
def phoenix_pepper_generate_shard_candidates_no_cr(step: int = 2) -> List[Dict[str, int]]:
    """
    피닉스 FAST 전용 설유 후보 생성.
    - step 값은 그대로 사용하되, 6축 완전탐색 대신
      "합계가 NORMAL_SLOTS 이하인 stepped composition"만 생성해서
      step=2여도 멜랑처럼 빠르게 돌도록 한다.
    - 남는 슬롯은 이후 crit_rate / elem_atk 자동 배정으로 처리된다.
    """
    step = max(1, int(step or 1))
    # 피페 설유 탐색 축: 기본 공격/특수 스킬/패시브 피해 증가 제외
    keys = ["crit_dmg", "all_elem_dmg", "atk_pct", "ult_dmg"]

    out: List[Dict[str, int]] = []

    def dfs(idx: int, remain: int, cur: Dict[str, int]) -> None:
        if idx == len(keys):
            out.append({k: int(cur.get(k, 0)) for k in keys})
            return

        k = keys[idx]
        for x in range(0, remain + 1, step):
            cur[k] = x
            dfs(idx + 1, remain - x, cur)
        cur.pop(k, None)

    dfs(0, NORMAL_SLOTS, {})
    return out

# =====================================================
# Calculation - 최적화
# =====================================================
def optimize_phoenix_pepper_cycle(
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
    """장비별 상위 후보를 선별한 뒤 상위 4스탯을 step=1로 전수조사한다."""
    del step  # 장비별 조각 최적화는 항상 1칸 단위로 수행한다.

    cookie = '피닉스페퍼 쿠키'
    base = BASE_STATS_PHOENIX_PEPPER[cookie].copy()
    equips = _resolve_equip_list_override(equip_override, phoenix_pepper_allowed_equips())
    uniques = _resolve_unique_list_override(unique_override, phoenix_pepper_allowed_uniques())
    potentials = phoenix_pepper_generate_potentials_common()
    artifacts = phoenix_pepper_allowed_artifacts()
    zero_shards = {key: 0 for key in SHARD_INC.keys()}

    total = max(1, len(equips) * len(artifacts) * len(uniques) * len(potentials))
    done = 0

    def emit(progress: float) -> None:
        if not progress_cb:
            return
        try:
            progress_cb(progress)
        except Exception:
            pass

    emit(0.0)
    screened_by_equip: Dict[str, List[dict]] = {equip: [] for equip in equips}

    for equip in equips:
        for artifact_name in artifacts:
            for unique_name in uniques:
                for pot in potentials:
                    template = build_stats_for_combo(
                        cookie_name_kr=cookie,
                        base=base,
                        shards=zero_shards,
                        potentials=pot,
                        equip_name=equip,
                        seaz_name=seaz_name,
                        unique_name=unique_name,
                        party=party,
                        artifact_name=artifact_name,
                        party_seaz=party_seaz,
                        party_uniques=party_uniques,
                        party_sets=party_sets,
                    )

                    try:
                        if not is_valid_by_caps(template):
                            continue
                        if not should_evaluate_conditional_crit_potential(template, pot):
                            continue

                        required_crit = _min_crit_slots_needed_for_crit100_generic(template)
                        if required_crit is None:
                            continue
                        required_crit = int(required_crit)
                        if required_crit > NORMAL_SLOTS:
                            continue

                        template.pop("_applied_party_buffs", None)
                        template.pop("_applied_enemy_debuffs", None)

                        def cycle_for(
                            stats: Dict[str, float],
                            artifact_name: str = artifact_name,
                        ) -> Dict[str, float]:
                            return phoenix_pepper_cycle_damage_fast(
                                stats,
                                party,
                                artifact_name,
                                seaz_name=seaz_name,
                            )

                        shards_out, stats, cycle = optimize_damage_shards_for_fixed_combo(
                            template,
                            cycle_for,
                            required_crit_slots=required_crit,
                        )

                        cur = {
                            "cookie": cookie,
                            "dps": cycle["dps"],
                            "cycle_total_damage": cycle["total_damage"],
                            "cycle_total_time": float(cycle.get("total_time", 30.0)),
                            "cycle_breakdown": cycle,
                            "equip": equip,
                            "seaz": seaz_name,
                            "unique": unique_name,
                            "artifact": artifact_name,
                            "shards": shards_out,
                            "potentials": pot,
                            "party": party,
                            "party_seaz": dict(party_seaz or {}),
                            "party_sets": dict(party_sets or {}),
                            "party_uniques": dict(party_uniques or {}),
                            "stats": stats,
                            "buff_amp_total": stats.get("buff_amp_total", stats.get("buff_amp", 0.0)),
                            "debuff_amp_total": stats.get("debuff_amp_total", stats.get("debuff_amp", 0.0)),
                            "_template": template,
                            "_cycle_fn": cycle_for,
                            "_required_crit": required_crit,
                        }
                        bucket = screened_by_equip.setdefault(equip, [])
                        bucket.append(cur)
                        bucket.sort(key=lambda item: float(item.get("dps", 0.0)), reverse=True)
                        del bucket[DAMAGE_SHARD_FINALISTS_PER_EQUIP:]
                    finally:
                        done += 1
                        emit(0.65 * done / total)

    finalists = [candidate for bucket in screened_by_equip.values() for candidate in bucket]
    finalist_total = max(1, len(finalists))
    best: Optional[dict] = None

    for index, cur in enumerate(finalists, start=1):
        shards_out, stats, cycle = optimize_damage_shards_top4_for_fixed_combo(
            cur["_template"],
            cur["_cycle_fn"],
            required_crit_slots=int(cur["_required_crit"]),
        )
        cur["shards"] = shards_out
        cur["stats"] = stats
        cur["dps"] = float(cycle["dps"])
        cur["cycle_total_damage"] = float(cycle["total_damage"])
        cur["cycle_total_time"] = float(cycle.get("total_time", 30.0))
        cur["cycle_breakdown"] = cycle
        cur["buff_amp_total"] = stats.get("buff_amp_total", stats.get("buff_amp", 0.0))
        cur["debuff_amp_total"] = stats.get("debuff_amp_total", stats.get("debuff_amp", 0.0))
        cur.pop("_template", None)
        cur.pop("_cycle_fn", None)
        cur.pop("_required_crit", None)

        if best is None or float(cur["dps"]) > float(best["dps"]):
            best = cur
        emit(0.65 + (0.35 * index / finalist_total))

    emit(1.0)
    return best
