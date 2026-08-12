# =====================================================
# Imports
# =====================================================
from functools import lru_cache

from .common import *
from .common import (
    _min_crit_slots_needed_for_crit100_generic,
    _resolve_equip_list_override,
    _resolve_unique_list_override,
    should_evaluate_conditional_crit_potential,
)

# =====================================================
# 스타더스트 쿠키
# - 데미지 딜러 / 사격형 / 신비속성
# =====================================================

STARDUST_PROMO_ATK_PCT = 0.30
STARDUST_WEAPON_ATK_PCT = 0.52
STARDUST_WEAPON_FINAL_DMG = 0.30

STARDUST_DEFAULT_SEAZ = "페퍼루비:영예로운 기사도"
STARDUST_FIXED_ARTIFACT = "외딴 별의 여정"
STARDUST_FIXED_UNIQUE = "로드 나이트메어의 뒤틀린 기억"

# 표기 기본공격력 897에는 돌파 공격력 +30%가 포함되어 있다.
# 호감도 공격력 54는 최종 공격력 공식 마지막에 별도로 더한다.
BASE_STATS_STARDUST = {
    "스타더스트 쿠키": {
        "atk": atk_from_promoted_base_without_friendship(897.0, STARDUST_PROMO_ATK_PCT),
        "friendship_atk": friendship_atk_for("스타더스트 쿠키"),
        "elem_atk": 0.0,
        "atk_pct": STARDUST_PROMO_ATK_PCT + STARDUST_WEAPON_ATK_PCT,
        "crit_rate": 0.15,
        "crit_dmg": 1.50,
        "armor_pen": 0.0,
        "final_dmg": 0.04 + STARDUST_WEAPON_FINAL_DMG,
    }
}

# 스킬 계수
STARDUST_BASIC_1_COEFF = 3.181
STARDUST_BASIC_2_COEFF = 3.181
STARDUST_BASIC_3_COEFF = 3.181 * 2.0
STARDUST_SPECIAL_COEFF = 7.810 * 6.0
STARDUST_ULT_COEFF = 8.520 * 5.0
STARDUST_SUPERNOVA_COMBO_COEFF = (1.420 * 3.0) + (1.704 * 3.0) + (1.846 * 3.0)
STARDUST_SHADOW_BASE_COEFF = 2.0
STARDUST_SHADOWS_PER_TRIGGER = 2
STARDUST_SHADOW_TRIGGER_COUNT = 7
STARDUST_SHADOW_TOTAL_COUNT = STARDUST_SHADOWS_PER_TRIGGER * STARDUST_SHADOW_TRIGGER_COUNT

# 밤하늘의 여행자: 별무리 10중첩, 쿠키에게 받는 피해 +10%
STARDUST_STAR_CLUSTER_TAKEN = 0.10
# 외로움 없는 작별: 별무리 대상 공격력 +15%
STARDUST_MARKED_TARGET_ATK_PCT = 0.15

# 파티 스트라이커가 쿠키에게 받는 피해 증가를 부여하면 소우주 기본공격 피해가 전 사이클 유지된다.
STARDUST_COSMOS_FULL_STRIKERS = {
    "룽샤맛 쿠키",
    "마블베리맛 쿠키",
    "밀키웨이맛 쿠키",
    "체리콜라맛 쿠키",
    "스테인드누가맛 쿠키",
}

# 별의 그림자 발동과 관계없이 기본 공격은 1타 → 2타 → 3타 순서가 계속 이어진다.
STARDUST_BASIC_SEQUENCE = ("B1", "B2", "B3")


def _stardust_basic_tokens(start_index: int, count: int) -> Tuple[str, ...]:
    sequence_size = len(STARDUST_BASIC_SEQUENCE)
    return tuple(
        STARDUST_BASIC_SEQUENCE[(start_index + offset) % sequence_size]
        for offset in range(count)
    )


def stardust_allowed_equips() -> List[str]:
    return ["달콤한 설탕 깃털", "미지의 방랑자", "수상한 사냥꾼", "시간관리국의 제복"]


def stardust_allowed_uniques() -> List[str]:
    return [STARDUST_FIXED_UNIQUE, "꿈세계의 기억", "새벽을 여는 달빛술사 쿠키의 기억"]


def stardust_allowed_artifacts() -> List[str]:
    return [STARDUST_FIXED_ARTIFACT]


def stardust_allowed_seaz() -> List[str]:
    return [
        name
        for name in SEAZNITES.keys()
        if str(name).startswith("페퍼루비:")
        and "믿음직한 브리더" not in str(name)
    ]


@lru_cache(maxsize=None)
def stardust_generate_potentials_common() -> List[Dict[str, int]]:
    """속성 공격력 2칸을 고정하고 치확 포함 딜 잠재력을 탐색한다."""
    return generate_damage_potential_candidates(fixed={"elem_atk": 2})


STARDUST_SHARD_STEP = 1

# 치명타 확률은 잠재력과 조각을 섞어 100%가 되는 최소 칸을 먼저 배정한다.
# 남은 일반 조각은 장비/유니크/잠재력이 고정된 상태에서 아래 모든 공격 옵션의
# 실제 1칸 DPS를 매번 다시 비교해 배분한다.
STARDUST_DAMAGE_SHARD_KEYS = (
    "atk_pct",
    "elem_atk",
    "crit_dmg",
    "all_elem_dmg",
    "basic_dmg",
    "special_dmg",
    "ult_dmg",
    "passive_dmg",
)

def _apply_stardust_shards_to_template(
    template: Dict[str, float],
    shards: Dict[str, int],
) -> Dict[str, float]:
    candidate = template.copy()
    candidate.pop("_damage_context_cache", None)
    for key, slot_count in shards.items():
        if not slot_count:
            continue
        inc = float(SHARD_INC.get(key, 0.0))
        if inc:
            candidate[key] = float(candidate.get(key, 0.0)) + inc * int(slot_count)
    return candidate


def _greedy_stardust_shards(
    template: Dict[str, float],
    required_crit: int,
    party: List[str],
    artifact_name: str,
    *,
    progress_step_cb: Optional[Callable[[], None]] = None,
) -> Tuple[Dict[str, int], Dict[str, float], Dict[str, float]]:
    """현재 장비 조건에서 남은 조각을 실제 DPS 증가량 기준으로 한 칸씩 배분한다."""
    current = {key: 0 for key in SHARD_INC.keys()}
    current["crit_rate"] = int(required_crit)
    current_stats = _apply_stardust_shards_to_template(template, current)
    current_cycle = stardust_cycle_damage_fast(current_stats, party, artifact_name)

    remain_slots = NORMAL_SLOTS - int(required_crit)
    for _ in range(max(0, remain_slots)):
        best_key = None
        best_stats = current_stats
        best_cycle = current_cycle

        for key in STARDUST_DAMAGE_SHARD_KEYS:
            trial = dict(current)
            trial[key] = int(trial.get(key, 0)) + 1
            trial_stats = _apply_stardust_shards_to_template(template, trial)
            trial_cycle = stardust_cycle_damage_fast(trial_stats, party, artifact_name)
            if best_key is None or float(trial_cycle["dps"]) > float(best_cycle["dps"]) + 1e-9:
                best_key = key
                best_stats = trial_stats
                best_cycle = trial_cycle

        if best_key is None:
            break
        current[best_key] = int(current.get(best_key, 0)) + 1
        current_stats = best_stats
        current_cycle = best_cycle
        if progress_step_cb:
            progress_step_cb()

    return current, current_stats, current_cycle



def _apply_stardust_fixed_effects(stats: Dict[str, float]) -> Dict[str, float]:
    s = dict(stats)
    s.pop("_damage_context_cache", None)
    if s.get("_stardust_fixed_effects_applied"):
        return s
    s["_stardust_fixed_effects_applied"] = 1.0
    # 다른 스타더스트가 이미 파티 공용 [별무리] 10중첩을 묻힌 경우 동일 디버프는 중첩하지 않는다.
    if not bool(s.get("_shared_stardust_star_cluster_applied", False)):
        s["dmg_taken_inc"] = float(s.get("dmg_taken_inc", 0.0)) + STARDUST_STAR_CLUSTER_TAKEN
    s["atk_pct"] = float(s.get("atk_pct", 0.0)) + STARDUST_MARKED_TARGET_ATK_PCT
    return s


def _stardust_temp_stats(
    stats: Dict[str, float],
    *,
    crit_dmg_add: float = 0.0,
    basic_dmg_add: float = 0.0,
) -> Dict[str, float]:
    out = dict(stats)
    out.pop("_damage_context_cache", None)
    if crit_dmg_add:
        out["buff_crit_dmg_raw"] = float(out.get("buff_crit_dmg_raw", 0.0)) + crit_dmg_add
    if basic_dmg_add:
        out["basic_dmg"] = float(out.get("basic_dmg", 0.0)) + basic_dmg_add
    return out


def _stardust_basic_damage(stats: Dict[str, float], token: str) -> float:
    coeff = {
        "B1": STARDUST_BASIC_1_COEFF,
        "B2": STARDUST_BASIC_2_COEFF,
        "B3": STARDUST_BASIC_3_COEFF,
    }[token]
    return skill_damage_from_start(stats, coeff, "basic")


def stardust_cycle_damage_fast(stats: Dict[str, float], party: List[str], artifact_name: str) -> Dict[str, float]:
    stats = _apply_stardust_fixed_effects(stats)
    total_time = 30.0
    breakdown = {"basic": 0.0, "special": 0.0, "ult": 0.0, "proc": 0.0, "strike": 0.0, "unique": 0.0}
    total_direct = 0.0

    artifact_meta = (ARTIFACTS.get(artifact_name, {}) or {}).get("stardust", {}) or {}
    star_path_crit_dmg = float(artifact_meta.get("star_path_crit_dmg", 0.0))
    cosmos_basic_dmg = float(artifact_meta.get("cosmos_basic_dmg", 0.0))
    shadow_dmg_mult = 1.0 + float(artifact_meta.get("shadow_dmg_increase", 0.0))

    # 궁극기 자체는 사용 후 획득하는 [별의 길] 치명타 피해 증가를 적용하지 않는다.
    ult_damage = skill_damage_from_start(stats, STARDUST_ULT_COEFF, "ult")
    total_direct += ult_damage
    breakdown["ult"] += ult_damage

    post_ult_stats = _stardust_temp_stats(stats, crit_dmg_add=star_path_crit_dmg)
    cosmos_full_cycle = any(name in STARDUST_COSMOS_FULL_STRIKERS for name in (party or []))
    shadow_trigger_index = 0
    basic_attack_index = 0

    def add_special() -> None:
        nonlocal total_direct
        damage = skill_damage_from_start(post_ult_stats, STARDUST_SPECIAL_COEFF, "special")
        total_direct += damage
        breakdown["special"] += damage

    def add_basic_sequence(count: int, cosmos_active: bool) -> None:
        nonlocal total_direct, basic_attack_index
        tokens = _stardust_basic_tokens(basic_attack_index, count)
        basic_attack_index = (basic_attack_index + count) % len(STARDUST_BASIC_SEQUENCE)
        event_stats = _stardust_temp_stats(
            post_ult_stats,
            basic_dmg_add=cosmos_basic_dmg if cosmos_active else 0.0,
        )
        damage = sum(_stardust_basic_damage(event_stats, token) for token in tokens)
        total_direct += damage
        breakdown["basic"] += damage

    def add_enhanced_and_shadows(cosmos_active: bool) -> None:
        nonlocal total_direct, shadow_trigger_index
        event_stats = _stardust_temp_stats(
            post_ult_stats,
            basic_dmg_add=cosmos_basic_dmg if cosmos_active else 0.0,
        )
        enhanced = skill_damage_from_start(event_stats, STARDUST_SUPERNOVA_COMBO_COEFF, "basic")
        shadow_coeff = (
            STARDUST_SHADOW_BASE_COEFF
            * STARDUST_SHADOWS_PER_TRIGGER
            * shadow_dmg_mult
        )
        shadows = skill_damage_from_start(post_ult_stats, shadow_coeff, "passive")
        total_direct += enhanced + shadows
        breakdown["basic"] += enhanced
        breakdown["proc"] += shadows
        shadow_trigger_index += 1

    # 궁 → 특 → (5평 + 별의 그림자 2개) × 6
    add_special()
    for _ in range(6):
        cosmos_active = cosmos_full_cycle or shadow_trigger_index < 4
        add_basic_sequence(5, cosmos_active)
        add_enhanced_and_shadows(cosmos_active)

    # 특 → 5평 + 별의 그림자 2개 → 5평 → 3평 × 4
    add_special()
    cosmos_active = cosmos_full_cycle or shadow_trigger_index < 4
    add_basic_sequence(5, cosmos_active)
    add_enhanced_and_shadows(cosmos_active)

    add_basic_sequence(5, cosmos_full_cycle)
    for _ in range(4):
        add_basic_sequence(3, cosmos_full_cycle)

    if shadow_trigger_index != STARDUST_SHADOW_TRIGGER_COUNT:
        raise RuntimeError(f"스타더스트 별의 그림자 발동 횟수 오류: {shadow_trigger_index}")

    sugar_proc = skill_damage_from_start(post_ult_stats, float(stats.get("sugar_brilliance_coeff", 0.0)), "none")
    if sugar_proc:
        total_direct += sugar_proc
        breakdown["proc"] += sugar_proc

    strike = strike_total_from_direct(total_direct, "스타더스트 쿠키", post_ult_stats, party)
    breakdown["strike"] = strike

    unique_total = skill_damage_from_start(
        post_ult_stats,
        float(stats.get("unique_extra_coeff", 0.0)),
        "none",
    ) * total_time
    breakdown["unique"] = unique_total

    total_damage = math.floor(total_direct + strike + unique_total)
    local_raw = stats.get("_local", None)
    local: Dict[str, Any] = local_raw if isinstance(local_raw, dict) else {}
    elem_dmg_mult = float(local.get("elem_dmg_mult", stats.get("elem_dmg_mult", 1.0)))
    if elem_dmg_mult != 1.0:
        total_damage *= elem_dmg_mult
        for key in breakdown:
            breakdown[key] *= elem_dmg_mult

    return {
        "total_damage": total_damage,
        "total_time": total_time,
        "dps": total_damage / total_time,
        "cosmos_full_cycle": cosmos_full_cycle,
        "shadow_count": STARDUST_SHADOW_TOTAL_COUNT,
        "breakdown_basic": breakdown["basic"],
        "breakdown_special": breakdown["special"],
        "breakdown_ult": breakdown["ult"],
        "breakdown_proc": breakdown["proc"],
        "breakdown_strike": breakdown["strike"],
        "breakdown_unique": breakdown["unique"],
    }


def optimize_stardust_cycle(
    seaz_name: str,
    party: List[str],
    party_seaz: Optional[Dict[str, str]] = None,
    party_uniques: Optional[Dict[str, str]] = None,
    party_sets: Optional[Dict[str, str]] = None,
    step: int = 1,
    progress_cb: Optional[Callable[[float], None]] = None,
    equip_override: Optional[Union[str, List[str], Tuple[str, ...], set]] = None,
    unique_override: Optional[Union[str, List[str], Tuple[str, ...], set]] = None,
    potential_override: Optional[Dict[str, int]] = None,
) -> Optional[dict]:
    del step  # 장비별 실제 DPS를 기준으로 항상 1칸 단위 배분한다.

    cookie = "스타더스트 쿠키"
    base = BASE_STATS_STARDUST[cookie].copy()
    equips = _resolve_equip_list_override(equip_override, stardust_allowed_equips())
    uniques = _resolve_unique_list_override(unique_override, stardust_allowed_uniques())
    potentials = [dict(potential_override)] if potential_override is not None else stardust_generate_potentials_common()
    artifacts = stardust_allowed_artifacts()
    zero_shards = {key: 0 for key in SHARD_INC.keys()}

    def emit(progress: float) -> None:
        if progress_cb:
            try:
                progress_cb(progress)
            except Exception:
                pass

    emit(0.0)

    search_templates = []
    for equip in equips:
        for artifact_name in artifacts:
            for unique_name in uniques:
                for potential in potentials:
                    template = build_stats_for_combo(
                        cookie_name_kr=cookie,
                        base=base,
                        shards=zero_shards,
                        potentials=potential,
                        equip_name=equip,
                        seaz_name=seaz_name,
                        unique_name=unique_name,
                        party=party,
                        artifact_name=artifact_name,
                        party_seaz=party_seaz,
                        party_uniques=party_uniques,
                        party_sets=party_sets,
                    )
                    template = _apply_stardust_fixed_effects(template)
                    if not is_valid_by_caps(template):
                        continue
                    if not should_evaluate_conditional_crit_potential(template, potential):
                        continue

                    required_crit = _min_crit_slots_needed_for_crit100_generic(template)
                    if required_crit is None:
                        continue
                    required_crit = int(required_crit)
                    if required_crit > NORMAL_SLOTS:
                        continue

                    template.pop("_applied_party_buffs", None)
                    template.pop("_applied_enemy_debuffs", None)
                    search_templates.append((
                        equip, artifact_name, unique_name, potential, template, required_crit,
                    ))

    total_steps = sum(max(0, NORMAL_SLOTS - item[5]) for item in search_templates)
    total_steps = max(1, total_steps)
    done_steps = 0
    tick = max(1, total_steps // 150)

    def advance_progress() -> None:
        nonlocal done_steps
        done_steps += 1
        if done_steps % tick == 0:
            emit(0.65 * done_steps / total_steps)

    top_by_equip: Dict[str, List[dict]] = {equip: [] for equip in equips}

    def push_equip_candidate(equip_name: str, result: dict) -> None:
        bucket = top_by_equip.setdefault(equip_name, [])
        bucket.append(result)
        bucket.sort(key=lambda item: float(item.get("dps", 0.0)), reverse=True)
        del bucket[DAMAGE_SHARD_FINALISTS_PER_EQUIP:]

    for equip, artifact_name, unique_name, potential, template, required_crit in search_templates:
        shards_out, candidate, cycle = _greedy_stardust_shards(
            template,
            required_crit,
            party,
            artifact_name,
            progress_step_cb=advance_progress,
        )
        push_equip_candidate(equip, {
            "cookie": cookie,
            "dps": cycle["dps"],
            "cycle_total_damage": cycle["total_damage"],
            "cycle_total_time": 30.0,
            "cycle_breakdown": cycle,
            "equip": equip,
            "seaz": seaz_name,
            "unique": unique_name,
            "artifact": artifact_name,
            "shards": shards_out,
            "potentials": potential,
            "party": party,
            "party_seaz": dict(party_seaz or {}),
            "party_sets": dict(party_sets or {}),
            "party_uniques": dict(party_uniques or {}),
            "stats": candidate,
            "buff_amp_total": candidate.get("buff_amp_total", candidate.get("buff_amp", 0.0)),
            "debuff_amp_total": candidate.get("debuff_amp_total", candidate.get("debuff_amp", 0.0)),
            "_template": template,
            "_required_crit": required_crit,
        })

    finalists = [result for equip in equips for result in top_by_equip.get(equip, [])]
    finalist_total = max(1, len(finalists))
    best: Optional[dict] = None

    for index, result in enumerate(finalists, start=1):
        artifact_name = str(result["artifact"])

        def cycle_for(
            stats: Dict[str, float],
            artifact_name: str = artifact_name,
        ) -> Dict[str, float]:
            return stardust_cycle_damage_fast(stats, party, artifact_name)

        refined_shards, refined_stats, refined_cycle = optimize_damage_shards_top4_for_fixed_combo(
            result["_template"],
            cycle_for,
            required_crit_slots=int(result["_required_crit"]),
            damage_keys=STARDUST_DAMAGE_SHARD_KEYS,
        )
        result["shards"] = refined_shards
        result["stats"] = refined_stats
        result["dps"] = float(refined_cycle["dps"])
        result["cycle_total_damage"] = float(refined_cycle["total_damage"])
        result["cycle_total_time"] = float(refined_cycle.get("total_time", 30.0))
        result["cycle_breakdown"] = refined_cycle
        result["buff_amp_total"] = refined_stats.get(
            "buff_amp_total", refined_stats.get("buff_amp", 0.0)
        )
        result["debuff_amp_total"] = refined_stats.get(
            "debuff_amp_total", refined_stats.get("debuff_amp", 0.0)
        )
        result.pop("_template", None)
        result.pop("_required_crit", None)

        if best is None or float(result["dps"]) > float(best.get("dps", 0.0)):
            best = result
        emit(0.65 + (0.35 * index / finalist_total))

    emit(1.0)
    return best

