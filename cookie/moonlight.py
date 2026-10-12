# =====================================================
# 달빛술사 쿠키
# =====================================================
from typing import Callable, Dict, Iterator, List, Optional, Tuple, Union
import math

from .common import *
from .common import _resolve_equip_list_override, _resolve_unique_list_override, _apply_shards_inplace, _clone_stats_for_loop

MOONLIGHT_COOKIE = "달빛술사 쿠키"
MOONLIGHT_FIXED_ARTIFACT = "고요히 흐르는 월광"
MOONLIGHT_FIXED_UNIQUE = "달빛술사 쿠키의 기억"
MOONLIGHT_DEFAULT_EQUIP = "유성우의 향연"
MOONLIGHT_DEFAULT_SEAZ = "플럼나이트:달빛의 속삭임"

MOONLIGHT_WEAPON_ATK_PCT = 0.52
MOONLIGHT_WEAPON_DEBUFF_AMP = 0.24
MOONLIGHT_SELF_MYSTIC_ELEM_ATK_ADD = 650.0
MOONLIGHT_SELF_CRIT_DMG_ADD = 0.80

# =====================================================
# 잠재력 규칙
# =====================================================
# - 장비별 디버프 증폭 고정 없음
# - 전체 8칸을 실제 DPS 기준으로 탐색
# - 디버프 증폭은 본인 패시브 피해 증가에 반영
MOONLIGHT_POTENTIAL_DAMAGE_KEYS = (
    "crit_rate", "atk_pct", "elem_atk", "crit_dmg", "armor_pen", "debuff_amp"
)
MOONLIGHT_POTENTIAL_FINALISTS_PER_COMBO = 3
MOONLIGHT_POTENTIAL_PREFILTER_PER_DEBUFF = 12
MOONLIGHT_POTENTIAL_PREFILTER_OVERALL = 12
MOONLIGHT_FINAL_SHARD_COARSE_STEP = 2

BASE_STATS_MOONLIGHT = {
    MOONLIGHT_COOKIE: {
        "atk": 617.0,
        "friendship_atk": friendship_atk_for(MOONLIGHT_COOKIE),
        "def": 419.0,
        "hp": 5153.0,
        # 환상적인 달의 초대 2성 효과는 파티 역할군에 따라 별도 적용
        "elem_atk": 0.0,
        "atk_pct": MOONLIGHT_WEAPON_ATK_PCT,
        "crit_rate": 0.15,
        "crit_dmg": 1.50,
        "armor_pen": 0.0,
        "final_dmg": 0.05,
        "buff_amp": 0.0,
        # 기본 디버프 증폭 15% + 전용무기 디버프 증폭 24%
        "debuff_amp": 0.15 + MOONLIGHT_WEAPON_DEBUFF_AMP,
    }
}

def _moonlight_base_stats_for_party(party: Optional[List[str]]) -> Dict[str, float]:
    """달빛술사 2성 파티 역할군 효과 적용"""
    base = BASE_STATS_MOONLIGHT[MOONLIGHT_COOKIE].copy()
    roles = {
        str(COOKIE_ROLE.get(name, "") or "").lower()
        for name in (party or [])
        if name and name != "없음"
    }

    # 환상적인 달의 초대: 데미지 딜러 포함 시 신비 속성 공격력 +650
    if "dps" in roles:
        base["elem_atk"] = float(base.get("elem_atk", 0.0)) + MOONLIGHT_SELF_MYSTIC_ELEM_ATK_ADD

    # 환상적인 달의 초대: 스트라이커 포함 시 치명타 피해 +80%
    if "strike" in roles:
        base["crit_dmg"] = float(base.get("crit_dmg", 1.50)) + MOONLIGHT_SELF_CRIT_DMG_ADD

    return base

# 계수 기준: 업로드 스크린샷
MOONLIGHT_CYCLE_TIME = 30.0
MOONLIGHT_BASIC_COEFF = (1.491 * 2.0) + (1.491 * 2.0)
# [새벽녘] 기본 공격 3평 1묶음
# 1타 170.4%×4 + 2타 170.4%×4 + 3타 369.2% + 532.5%
MOONLIGHT_DAWN_BASIC3_COEFF = (1.704 * 4.0) + (1.704 * 4.0) + 3.692 + 5.325
# 이전 차징 가정값은 남겨두되 현재 사이클에서는 사용하지 않음
MOONLIGHT_DAWN_CHARGE_COEFF = 10.508 * 9.0
MOONLIGHT_SPECIAL_COEFF = 7.952
MOONLIGHT_MOONBALL_COEFF = 1.232
MOONLIGHT_MOONBALL_HITS = 1
MOONLIGHT_ULT_INITIAL_COEFF = 9.088
MOONLIGHT_DREAMLIKE_COEFF = 9.940
MOONLIGHT_ULT_FINISH_COEFF = (4.757 * 4.0) + 30.672
MOONLIGHT_ARTIFACT_DAWN_GUIDE_COEFF = 12.0 * 3.0

MOONLIGHT_PASSIVE_FINAL_PER_DEBUFF_AMP = 0.80
MOONLIGHT_PASSIVE_FINAL_CAP = 1.20
MOONLIGHT_DAWN_CRIT_RATE_ADD = 1.00
MOONLIGHT_DAWN_DAMAGE_INC = 0.25
MOONLIGHT_DAWN_DAMAGE_DURATION = 20.0
MOONLIGHT_DAWN_DAMAGE_AVG = MOONLIGHT_DAWN_DAMAGE_INC * (MOONLIGHT_DAWN_DAMAGE_DURATION / MOONLIGHT_CYCLE_TIME)

# 30초 1사이클
# 궁(달빛 환대) → 특 → 2평 → 2평 → 궁(꿈만 같은 시간) → 궁(새벽녘)
# → 특 → 3평 → 3평 → 3평 → 3평 → 특 → 3평 → 3평 → 특 → 새벽녘 종료 → 2평 → 2평
# - 달무리 실제 타수: 1회
# - 꿈만 같은 시간: 1회
# - 새벽녘 상태 피해 +25%는 20초/30초 평균값으로 본인에게만 적용
MOONLIGHT_CYCLE_TOKENS = [
    "U_RECEPTION", "S", "MOONBALL", "B", "B",
    "U_DREAM", "U_DAWN_START", "S_IN_DAWN",
    "DAWN_BASIC3", "DAWN_BASIC3", "DAWN_BASIC3", "DAWN_BASIC3",
    "S_IN_DAWN", "DAWN_BASIC3", "DAWN_BASIC3", "S_IN_DAWN",
    "DAWN_GUIDE", "U_DAWN_FINISH", "B", "B",
]

def moonlight_allowed_equips() -> List[str]:
    # 달빛술사 장비 후보: 유성우/시간셋을 사용
    # 잠재력은 장비와 관계없이 실제 DPS 기준으로 탐색
    # 기본값은 유성우의 향연
    return [x for x in ["유성우의 향연", "시간관리국의 제복"] if x in EQUIP_SETS]

def moonlight_allowed_seaz() -> List[str]:
    # 달빛술사는 플럼나이트 계열만 표시
    return [x for x in SEAZNITES.keys() if str(x).startswith("플럼나이트:")]

def moonlight_allowed_uniques() -> List[str]:
    # 기본은 달빛술사 쿠키의 기억을 사용
    opts = ["달빛술사 쿠키의 기억", "로드 나이트메어의 기억", "멜랑크림 쿠키의 순수한 기억", "새벽을 여는 달빛술사 쿠키의 기억"]
    return [x for x in opts if x in UNIQUE_SHARDS]

def moonlight_allowed_potentials_for_equip(equip_name: str) -> List[Dict[str, int]]:
    """달빛술사 DPS 기준 잠재력 후보"""
    del equip_name
    return generate_damage_potential_candidates(
        free_keys=MOONLIGHT_POTENTIAL_DAMAGE_KEYS,
    )

MOONLIGHT_DAMAGE_SHARD_KEYS = (
    "atk_pct",
    "elem_atk",
    "crit_rate",
    "crit_dmg",
    "all_elem_dmg",
    "basic_dmg",
    "special_dmg",
    "ult_dmg",
    "passive_dmg",
)
MOONLIGHT_ACTIVE_SHARD_KEY_COUNT = 4

def _moonlight_shard_steps(step: int) -> List[int]:
    step = max(1, int(step or 1))
    steps = list(range(0, NORMAL_SLOTS + 1, step))
    if steps[-1] != NORMAL_SLOTS:
        steps.append(NORMAL_SLOTS)
    return steps

def moonlight_generate_shard_candidates(
    step: int = 1,
    shard_keys: Optional[Tuple[str, ...]] = None,
) -> Iterator[Dict[str, int]]:
    """달빛술사 설탕유리조각 후보"""
    keys = tuple(shard_keys or MOONLIGHT_DAMAGE_SHARD_KEYS[:MOONLIGHT_ACTIVE_SHARD_KEY_COUNT])
    if not keys:
        return

    remainder_key = keys[0]
    axes = list(keys[1:])
    steps = _moonlight_shard_steps(step)

    def rec(idx: int, used: int, cur: Dict[str, int]) -> Iterator[Dict[str, int]]:
        if idx >= len(axes):
            out = {key: 0 for key in SHARD_INC.keys()}
            out[remainder_key] = NORMAL_SLOTS - used
            for key, value in cur.items():
                out[key] = int(value)
            yield out
            return

        key = axes[idx]
        for value in steps:
            if used + value > NORMAL_SLOTS:
                continue
            cur[key] = int(value)
            yield from rec(idx + 1, used + value, cur)
        cur.pop(key, None)

    yield from rec(0, 0, {})

def _moonlight_stats_with_shards(
    template: Dict[str, float],
    shards: Dict[str, int],
) -> Dict[str, float]:
    stats = _clone_stats_for_loop(template)
    _apply_shards_inplace(stats, shards)
    stats.pop("_damage_context_cache", None)
    return stats

def _select_moonlight_shard_keys(
    template: Dict[str, float],
    party: List[str],
    artifact_name: str,
    *,
    count: int = MOONLIGHT_ACTIVE_SHARD_KEY_COUNT,
) -> Tuple[str, ...]:
    """달빛술사 설탕유리조각 옵션 선정"""
    base_dps = moonlight_cycle_damage(template, party, artifact_name)["dps"]
    scored = []
    for order, key in enumerate(MOONLIGHT_DAMAGE_SHARD_KEYS):
        one_slot = _moonlight_stats_with_shards(template, {key: 1})
        dps = moonlight_cycle_damage(one_slot, party, artifact_name)["dps"]
        scored.append((float(dps) - float(base_dps), -order, key))
    scored.sort(reverse=True)
    return tuple(item[2] for item in scored[:max(1, int(count))])

def _refine_moonlight_shards(
    template: Dict[str, float],
    initial_shards: Dict[str, int],
    party: List[str],
    artifact_name: str,
) -> Tuple[Dict[str, int], Dict[str, float], Dict[str, float]]:
    """달빛술사 설탕유리조각 보정"""
    current = {key: int(initial_shards.get(key, 0)) for key in SHARD_INC.keys()}
    current_stats = _moonlight_stats_with_shards(template, current)
    current_cycle = moonlight_cycle_damage(current_stats, party, artifact_name)

    iterations = 0
    while iterations < 100:
        iterations += 1
        best_move = None
        best_cycle = current_cycle
        best_stats = current_stats

        for src in MOONLIGHT_DAMAGE_SHARD_KEYS:
            if int(current.get(src, 0)) <= 0:
                continue
            for dst in MOONLIGHT_DAMAGE_SHARD_KEYS:
                if src == dst:
                    continue
                trial = dict(current)
                trial[src] -= 1
                trial[dst] = int(trial.get(dst, 0)) + 1
                trial_stats = _moonlight_stats_with_shards(template, trial)
                trial_cycle = moonlight_cycle_damage(trial_stats, party, artifact_name)
                if float(trial_cycle["dps"]) > float(best_cycle["dps"]) + 1e-9:
                    best_move = trial
                    best_cycle = trial_cycle
                    best_stats = trial_stats

        if best_move is None:
            break
        current = best_move
        current_cycle = best_cycle
        current_stats = best_stats

    return current, current_stats, current_cycle

def moonlight_cycle_total_time() -> float:
    return MOONLIGHT_CYCLE_TIME

def moonlight_calc_support_metrics(stats: Dict[str, float]) -> Dict[str, float]:
    da = float(stats.get("debuff_amp_total", stats.get("debuff_amp", 0.0)))
    ba = float(stats.get("buff_amp_total", stats.get("buff_amp", 0.0)))
    return {
        "total_time": MOONLIGHT_CYCLE_TIME,
        "final_atk": calc_attack_value(stats, floor_result=False),
        "debuff_amp_total": da,
        "buff_amp_total": ba,
        # 선잠 방어력 감소는 달빛술사 본인 디버프증폭을 적용
        # 한밤의 자장가 공격력 +30%: 버프 증폭 제외
        "def_reduction_raw": 0.28 * (1.0 + da),
        "party_final_dmg": 0.25,
        "artifact_all_elem": 0.50,
        "artifact_crit_dmg": 0.50,
        "artifact_atk_buff": 0.30,
    }

def _moonlight_apply_passive(stats: Dict[str, float]) -> Dict[str, float]:
    st = dict(stats)
    st.pop("_damage_context_cache", None)
    # [아름다운 밤의 산책]은 달빛술사 본인의 디버프 증폭량만 사용
    da_total = float(st.get("self_debuff_amp_total", st.get("debuff_amp_total", st.get("debuff_amp", 0.0))))
    add_final = min(MOONLIGHT_PASSIVE_FINAL_CAP, MOONLIGHT_PASSIVE_FINAL_PER_DEBUFF_AMP * da_total)
    st["final_dmg"] = float(st.get("final_dmg", 0.0)) + add_final
    return st

def _moonlight_has_res_down_for_dawn(stats: Dict[str, float]) -> bool:
    """달빛술사 새벽 조건 판정"""
    keys = (
        "elem_res_reduction_raw",
        "elem_res_reduction_no_scale_raw",
        "all_elem_res_reduction_raw",
        "all_elem_res_reduction_no_scale_raw",
        "mystic_elem_res_reduction_raw",
        "mystic_elem_res_reduction_no_scale_raw",
        "mystic_res_reduction_raw",
        "mystic_res_reduction_no_scale_raw",
    )
    return any(float(stats.get(k, 0.0) or 0.0) > 0.0 for k in keys)

def _moonlight_apply_dawn_avg_bonus(stats: Dict[str, float]) -> Dict[str, float]:
    st = dict(stats)
    st.pop("_damage_context_cache", None)
    if _moonlight_has_res_down_for_dawn(st):
        # 새벽녘: 신비·모든 속성 내성 감소 대상 피해 25% 증가
        # 새벽녘 평균 유지: 20/30초, 본인 피해 +16.6667%
        st["final_dmg"] = float(st.get("final_dmg", 0.0)) + MOONLIGHT_DAWN_DAMAGE_AVG
        st["moonlight_dawn_avg_final_dmg"] = float(st.get("moonlight_dawn_avg_final_dmg", 0.0)) + MOONLIGHT_DAWN_DAMAGE_AVG
    return st

def _moonlight_dawn_stats(stats: Dict[str, float]) -> Dict[str, float]:
    st = dict(stats)
    st.pop("_damage_context_cache", None)
    st["buff_crit_rate_raw"] = float(st.get("buff_crit_rate_raw", 0.0)) + MOONLIGHT_DAWN_CRIT_RATE_ADD
    return st

def moonlight_cycle_damage(stats: Dict[str, float], party: List[str], artifact_name: str = MOONLIGHT_FIXED_ARTIFACT) -> Dict[str, float]:
    total_time = moonlight_cycle_total_time()
    base_stats = _moonlight_apply_dawn_avg_bonus(_moonlight_apply_passive(stats))
    dawn_stats = _moonlight_dawn_stats(base_stats)

    direct = 0.0
    breakdown = {
        "basic": 0.0,
        "special": 0.0,
        "ult": 0.0,
        "charge": 0.0,
        "dash": 0.0,
        "passive": 0.0,
        "strike": 0.0,
        "unique": 0.0,
        "proc": 0.0,
    }

    for tok in MOONLIGHT_CYCLE_TOKENS:
        if tok == "B":
            # 2평 1묶음: 1타 149.1%×2 + 2타 149.1%×2
            dmg = skill_damage_from_start(base_stats, MOONLIGHT_BASIC_COEFF, "basic")
            direct += dmg
            breakdown["basic"] += dmg
        elif tok == "S":
            dmg = skill_damage_from_start(base_stats, MOONLIGHT_SPECIAL_COEFF, "special")
            direct += dmg
            breakdown["special"] += dmg
        elif tok == "S_IN_DAWN":
            # 새벽녘 중 특수스킬은 새벽녘 상태의 치명타 확률 +100%를 적용
            # 새벽녘 차징 피해와 별개로 일반 특수스킬 1회로 계산
            dmg = skill_damage_from_start(dawn_stats, MOONLIGHT_SPECIAL_COEFF, "special")
            direct += dmg
            breakdown["special"] += dmg
        elif tok == "MOONBALL":
            # 달무리는 실제 적중 1회만 반영
            dmg = skill_damage_from_start(base_stats, MOONLIGHT_MOONBALL_COEFF * MOONLIGHT_MOONBALL_HITS, "special")
            direct += dmg
            breakdown["special"] += dmg
        elif tok == "U_RECEPTION":
            dmg = skill_damage_from_start(base_stats, MOONLIGHT_ULT_INITIAL_COEFF, "ult")
            direct += dmg
            breakdown["ult"] += dmg
        elif tok == "U_DREAM":
            dmg = skill_damage_from_start(base_stats, MOONLIGHT_DREAMLIKE_COEFF, "ult")
            direct += dmg
            breakdown["ult"] += dmg
        elif tok == "U_DAWN_START":
            # 새벽녘 진입 자체는 변신/상태 진입으로 보고 직접 피해 없음
            continue
        elif tok == "DAWN_BASIC3":
            dmg = skill_damage_from_start(dawn_stats, MOONLIGHT_DAWN_BASIC3_COEFF, "basic")
            direct += dmg
            breakdown["basic"] += dmg
        elif tok == "DAWN_CHARGE":
            dmg = skill_damage_from_start(dawn_stats, MOONLIGHT_DAWN_CHARGE_COEFF, "basic")
            direct += dmg
            breakdown["charge"] += dmg
        elif tok == "REST5":
            continue
        elif tok == "U_DAWN_FINISH":
            dmg = skill_damage_from_start(dawn_stats, MOONLIGHT_ULT_FINISH_COEFF, "ult")
            direct += dmg
            breakdown["ult"] += dmg
        elif tok == "DAWN_GUIDE" and artifact_name == MOONLIGHT_FIXED_ARTIFACT:
            # 고요히 흐르는 월광: 공격력 1200% × 3, 수치 그대로 3타
            dmg = skill_damage_from_start(dawn_stats, MOONLIGHT_ARTIFACT_DAWN_GUIDE_COEFF, "special")
            direct += dmg
            breakdown["proc"] += dmg

    strike = strike_total_from_direct(direct, MOONLIGHT_COOKIE, stats, party)
    unique_extra = skill_damage_from_start(base_stats, float(stats.get("unique_extra_coeff", 0.0)), "none") * total_time
    sugar_proc = float(stats.get("sugar_brilliance_coeff", 0.0))
    sugar_damage = skill_damage_from_start(base_stats, sugar_proc, "none") if sugar_proc > 0 else 0.0

    breakdown["strike"] = strike
    breakdown["unique"] = unique_extra + sugar_damage
    total_damage = math.floor(direct + strike + unique_extra + sugar_damage)

    return {
        "total_damage": total_damage,
        "total_time": total_time,
        "dps": total_damage / total_time if total_time > 0 else 0.0,
        "breakdown_basic": breakdown["basic"],
        "breakdown_special": breakdown["special"],
        "breakdown_ult": breakdown["ult"],
        "breakdown_charge": breakdown["charge"],
        "breakdown_dash": breakdown["dash"],
        "breakdown_passive": breakdown["passive"],
        "breakdown_proc": breakdown["proc"],
        "breakdown_strike": breakdown["strike"],
        "breakdown_unique": breakdown["unique"],
    }

def _moonlight_greedy_shards_for_screening(
    template: Dict[str, float],
    party: List[str],
    artifact_name: str,
) -> Tuple[Dict[str, int], Dict[str, float], Dict[str, float]]:
    """달빛술사 잠재력 선별용 조각 최적화"""
    current = {key: 0 for key in SHARD_INC.keys()}
    current_stats = _moonlight_stats_with_shards(template, current)
    current_cycle = moonlight_cycle_damage(current_stats, party, artifact_name)

    for _ in range(NORMAL_SLOTS):
        best_key = None
        best_stats = current_stats
        best_cycle = current_cycle
        for key in MOONLIGHT_DAMAGE_SHARD_KEYS:
            trial = dict(current)
            trial[key] = int(trial.get(key, 0)) + 1
            trial_stats = _moonlight_stats_with_shards(template, trial)
            trial_cycle = moonlight_cycle_damage(trial_stats, party, artifact_name)
            if best_key is None or float(trial_cycle["dps"]) > float(best_cycle["dps"]) + 1e-9:
                best_key = key
                best_stats = trial_stats
                best_cycle = trial_cycle
        if best_key is None:
            break
        current[best_key] = int(current.get(best_key, 0)) + 1
        current_stats = best_stats
        current_cycle = best_cycle

    return current, current_stats, current_cycle

def _moonlight_exact_shards_for_template(
    template: Dict[str, float],
    party: List[str],
    artifact_name: str,
    step: int = 1,
) -> Tuple[Dict[str, int], Dict[str, float], Dict[str, float]]:
    """달빛술사 고정 조합 조각 정밀 탐색"""
    active_keys = _select_moonlight_shard_keys(template, party, artifact_name)
    best_shards: Optional[Dict[str, int]] = None
    best_stats: Optional[Dict[str, float]] = None
    best_cycle: Optional[Dict[str, float]] = None

    for sh in moonlight_generate_shard_candidates(step=step, shard_keys=active_keys):
        stats = _moonlight_stats_with_shards(template, sh)
        cycle = moonlight_cycle_damage(stats, party, artifact_name)
        if best_cycle is None or float(cycle["dps"]) > float(best_cycle["dps"]) + 1e-9:
            best_shards = dict(sh)
            best_stats = stats
            best_cycle = cycle

    if best_shards is None or best_stats is None or best_cycle is None:
        raise RuntimeError("달빛술사 조각 최적화 결과를 생성하지 못했습니다.")

    return _refine_moonlight_shards(
        template, best_shards, party, artifact_name
    )

def optimize_moonlight_cycle(
    seaz_name: Optional[str] = None,
    party: Optional[List[str]] = None,
    party_seaz: Optional[Dict[str, str]] = None,
    party_uniques: Optional[Dict[str, str]] = None,
    party_sets: Optional[Dict[str, str]] = None,
    step: int = 1,
    progress_cb: Optional[Callable[[float], None]] = None,
    equip_override: Optional[Union[str, List[str], Tuple[str, ...], set]] = None,
    unique_override: Optional[Union[str, List[str], Tuple[str, ...], set]] = None,
    potential_override: Optional[Dict[str, int]] = None,
) -> Optional[dict]:
    """달빛술사 최적화"""
    cookie = MOONLIGHT_COOKIE
    party = list(party or ["윈드파라거스 쿠키"])
    base = _moonlight_base_stats_for_party(party)
    artifact_name = MOONLIGHT_FIXED_ARTIFACT

    equips = _resolve_equip_list_override(equip_override, moonlight_allowed_equips() or [MOONLIGHT_DEFAULT_EQUIP])
    uniques = _resolve_unique_list_override(unique_override, moonlight_allowed_uniques() or [MOONLIGHT_FIXED_UNIQUE])

    if not seaz_name:
        opts = moonlight_allowed_seaz()
        seaz_name = MOONLIGHT_DEFAULT_SEAZ if MOONLIGHT_DEFAULT_SEAZ in opts else (opts[0] if opts else MOONLIGHT_DEFAULT_SEAZ)

    def emit(p: float) -> None:
        if progress_cb:
            try:
                progress_cb(max(0.0, min(1.0, float(p))))
            except Exception:
                pass

    zero_shards = {k: 0 for k in SHARD_INC.keys()}
    potential_lists = {
        equip: ([dict(potential_override)] if potential_override is not None else moonlight_allowed_potentials_for_equip(equip))
        for equip in equips
    }
    prefilter_total = max(1, sum(len(potential_lists[equip]) * len(uniques) for equip in equips))
    prefilter_done = 0
    prefiltered_by_combo: Dict[Tuple[str, str], List[dict]] = {}

    emit(0.01)

    # 1차: 조각 0칸 기준으로 전체 잠재력을 빠르게 선별
    # 디버프 증폭 0~4칸별 상위 후보를 각각 남겨 특정 증폭 구간이 조기에 탈락하지 않도록 함
    for equip_name in equips:
        for unique_name in uniques:
            scored: List[dict] = []
            for pot in potential_lists[equip_name]:
                template = build_stats_for_combo(
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
                template["base_hp"] = float(base.get("hp", 0.0))
                template["base_def"] = float(base.get("def", 0.0))

                prefilter_done += 1
                if not is_valid_by_caps(template):
                    emit(0.25 * prefilter_done / prefilter_total)
                    continue

                cycle_zero = moonlight_cycle_damage(template, party, artifact_name)
                scored.append({
                    "equip": equip_name,
                    "unique": unique_name,
                    "potentials": dict(pot),
                    "_template": template,
                    "_prefilter_dps": float(cycle_zero["dps"]),
                })
                emit(0.25 * prefilter_done / prefilter_total)

            selected: Dict[Tuple[Tuple[str, int], ...], dict] = {}
            scored.sort(key=lambda item: float(item.get("_prefilter_dps", 0.0)), reverse=True)

            for cur in scored[:MOONLIGHT_POTENTIAL_PREFILTER_OVERALL]:
                key = tuple(sorted((str(k), int(v)) for k, v in cur["potentials"].items()))
                selected[key] = cur

            for debuff_slots in range(5):
                group = [
                    cur for cur in scored
                    if int(cur["potentials"].get("debuff_amp", 0)) == debuff_slots
                ]
                for cur in group[:MOONLIGHT_POTENTIAL_PREFILTER_PER_DEBUFF]:
                    key = tuple(sorted((str(k), int(v)) for k, v in cur["potentials"].items()))
                    selected[key] = cur

            prefiltered_by_combo[(equip_name, unique_name)] = list(selected.values())

    # 2차: 선별된 잠재력만 41칸 조각을 빠르게 배분해 실제 DPS 순위를 계산
    greedy_total = max(1, sum(len(bucket) for bucket in prefiltered_by_combo.values()))
    greedy_done = 0
    finalists_by_combo: Dict[Tuple[str, str], List[dict]] = {}

    for combo, candidates in prefiltered_by_combo.items():
        bucket: List[dict] = []
        for cur in candidates:
            shards_quick, stats_quick, cycle_quick = _moonlight_greedy_shards_for_screening(
                cur["_template"], party, artifact_name
            )
            cur["_screen_dps"] = float(cycle_quick["dps"])
            cur["_screen_shards"] = shards_quick
            cur["_screen_stats"] = stats_quick
            bucket.append(cur)
            bucket.sort(key=lambda item: float(item.get("_screen_dps", 0.0)), reverse=True)
            del bucket[MOONLIGHT_POTENTIAL_FINALISTS_PER_COMBO:]

            greedy_done += 1
            emit(0.25 + (0.55 * greedy_done / greedy_total))

        finalists_by_combo[combo] = bucket

    # 3차: 각 장비/유니크 조합의 상위 잠재력만 정밀 조각 탐색으로 확정
    finalists = [item for bucket in finalists_by_combo.values() for item in bucket]
    finalist_total = max(1, len(finalists))
    best: Optional[dict] = None

    for index, cur in enumerate(finalists, start=1):
        template = cur["_template"]
        final_step = max(MOONLIGHT_FINAL_SHARD_COARSE_STEP, int(step or 1))
        shards, stats, cycle = _moonlight_exact_shards_for_template(
            template, party, artifact_name, step=final_step
        )
        support = moonlight_calc_support_metrics(stats)
        result = {
            "cookie": cookie,
            "dps": float(cycle["dps"]),
            "cycle_total_damage": float(cycle["total_damage"]),
            "cycle_total_time": float(cycle.get("total_time", MOONLIGHT_CYCLE_TIME)),
            "cycle_breakdown": cycle,
            "max_shield": 0.0,
            "max_heal": 0.0,
            "hps": 0.0,
            "support_detail": support,
            "equip": cur["equip"],
            "seaz": seaz_name,
            "unique": cur["unique"],
            "artifact": artifact_name,
            "potentials": dict(cur["potentials"]),
            "shards": dict(shards),
            "party": party,
            "party_seaz": dict(party_seaz or {}),
            "party_sets": dict(party_sets or {}),
            "party_uniques": dict(party_uniques or {}),
            "stats": stats,
            "buff_amp_total": stats.get("buff_amp_total", stats.get("buff_amp", 0.0)),
            "debuff_amp_total": stats.get("debuff_amp_total", stats.get("debuff_amp", 0.0)),
        }

        if best is None or float(result["dps"]) > float(best.get("dps", 0.0)):
            best = result
        emit(0.80 + (0.20 * index / finalist_total))

    emit(1.0)
    return best
