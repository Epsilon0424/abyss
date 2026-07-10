# =====================================================
# Imports
# =====================================================
from .common import *
from .common import _resolve_equip_list_override, _min_crit_slots_needed_for_crit100_generic, _resolve_unique_list_override
from functools import lru_cache

# =====================================================
# 룽샤맛 쿠키
# - 스트라이커 / 타격형 / 불속성
# - 윈드파라거스와 동일하게 스트라이커 전용 구조 사용
# =====================================================

# =====================================================
# Constants
# =====================================================
LUNGSHA_FORCE_CRIT_100 = True
LUNGSHA_WEAPON_ATK_PCT = 0.52
LUNGSHA_WEAPON_FINAL_DMG = 0.30

LUNGSHA_FIXED_SEAZ = "리치코랄:빛나는 은하수"
LUNGSHA_FIXED_ARTIFACT = "축제의 그림자"
LUNGSHA_FIXED_UNIQUE = "룽샤맛 쿠키의 기억"

# 공격력 표기: 861 + 호감도 54
# 승급 공격력 +30%는 호감도 제외 기본공격력(861)에만 역산한다.
BASE_STATS_LUNGSHA = {
    "룽샤맛 쿠키": {
        "atk": atk_from_promoted_base_without_friendship(861.0, 0.30),
        "friendship_atk": friendship_atk_for("룽샤맛 쿠키"),
        "def": 556.0,
        "hp": 5558.0,
        "elem_atk": 0.0,
        # 승급 공격력 +30% + 전용무기 기본 옵션 공격력 +52%
        "atk_pct": 0.30 + LUNGSHA_WEAPON_ATK_PCT,
        "crit_rate": 0.15,
        "crit_dmg": 1.50,
        "armor_pen": 0.0,
        # 승급 최종 피해 +4% + 전용무기 고유능력 최종 피해 +30%
        "final_dmg": 0.04 + LUNGSHA_WEAPON_FINAL_DMG,
    }
}

LUNGSHA_BASIC_COEFF = (0.994 * 2.0) + 1.278 + 1.562  # 기본공격 4타 합산 계수
LUNGSHA_SPECIAL1_COEFF = 2.84  # 특수스킬 1타 피해 계수
LUNGSHA_SPECIAL2_COEFF = 0.71 * 5.0  # 특수스킬 2타 피해 계수
LUNGSHA_SPECIAL3_COEFF = 2.272 * 2.0  # 특수스킬 3타 피해 계수
LUNGSHA_EMPOWERED_SPECIAL_COEFF = 5.112  # 강화 특수스킬 피해 계수
LUNGSHA_ULT_COEFF = 28.40  # 궁극기 피해 계수

# 승급 반영 (스킬 타입 피해 증가 축에 직접 합산)
LUNGSHA_PROMO_SPECIAL_DMG_ADD = 0.10  # 승급 특수스킬 피해 증가
LUNGSHA_PROMO_ULT_DMG_ADD = 0.30  # 승급 궁극기 피해 증가

# 상시 유지로 간주한 디버프/버프
# - 붉은 마음 : 공격력 +16%
# - 불가역 + 주화입마(+불속성 받피증) : 룽샤 기준 총 받피증 +63.6%
# - 삼매각화 : 받는 궁극기 피해 +35%
LUNGSHA_ALWAYS_SELF_ATK_PCT = 0.16
LUNGSHA_ALWAYS_DMG_TAKEN_INC = 0.636
LUNGSHA_ALWAYS_ENEMY_ULT_TAKEN_INC = 0.35

LUNGSHA_CYCLE_TOKENS = [
    "U", "ES", "S1",
    "B4", "B4",
    "S2",
    "B4", "B4",
    "S3",
    "ES",
    "B4", "B4",
    "S1",
    "B4", "B4",
    "S2",
    "B4", "B4",
    "S3",
]

# =====================================================
# Helpers - 장비/후보 생성
# =====================================================
def lungsha_allowed_equips() -> List[str]:
    return ["황금 예복", "유성우의 향연"]

def lungsha_allowed_uniques() -> List[str]:
    return [LUNGSHA_FIXED_UNIQUE, "룽샤맛 쿠키의 기억", "칠리맛 쿠키의 기억"]

def lungsha_allowed_artifacts() -> List[str]:
    return [LUNGSHA_FIXED_ARTIFACT]

def lungsha_allowed_seaz() -> List[str]:
    return [LUNGSHA_FIXED_SEAZ]

def lungsha_allowed_potentials() -> List[Dict[str, int]]:
    """룽샤 메인 최적화용 잠재 후보.

    - 치명타 확률 2칸 / 속성공격력 2칸은 고정
    - 남은 4칸은 공격력% / 치명타피해 / 방어력관통에 배분
    - 룽샤는 현재 모델에서 방깎/속깎 스킬 디버프를 사용하지 않으므로
      debuff_amp 잠재는 딜세팅 후보에서 제외한다.
    """
    out: List[Dict[str, int]] = []
    remain = 4
    for atk_pct in range(remain + 1):
        for crit_dmg in range(remain - atk_pct + 1):
            armor_pen = remain - atk_pct - crit_dmg
            out.append({
                "debuff_amp": 0,
                "crit_rate": 2,
                "atk_pct": atk_pct,
                "elem_atk": 2,
                "crit_dmg": crit_dmg,
                "armor_pen": armor_pen,
                "buff_amp": 0,
            })
    return out

@lru_cache(maxsize=None)
def lungsha_generate_shard_candidates_no_cr(step: int = 2) -> List[Dict[str, int]]:
    """
    룽샤 FAST 전용 설유 후보.
    - 스트라이커 고정 잠재/장비 구조라 조합 수가 비교적 작다.
    - crit_rate는 자동 배정, 남는 슬롯은 elem_atk로 채운다.
    """
    step = max(1, int(step or 1))
    keys = ["crit_dmg", "all_elem_dmg", "atk_pct"]
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
# Helpers - 고정 효과 반영
# =====================================================
def _apply_lungsha_fixed_effects(stats: Dict[str, float], artifact_name: str) -> Dict[str, float]:
    s = dict(stats)
    s["atk_pct"] = float(s.get("atk_pct", 0.0)) + LUNGSHA_ALWAYS_SELF_ATK_PCT
    s["dmg_taken_inc"] = float(s.get("dmg_taken_inc", 0.0)) + LUNGSHA_ALWAYS_DMG_TAKEN_INC
    s["special_dmg"] = float(s.get("special_dmg", 0.0)) + LUNGSHA_PROMO_SPECIAL_DMG_ADD
    s["ult_dmg"] = float(s.get("ult_dmg", 0.0)) + LUNGSHA_PROMO_ULT_DMG_ADD
    if artifact_name == LUNGSHA_FIXED_ARTIFACT:
        s["enemy_ult_taken_inc"] = float(s.get("enemy_ult_taken_inc", 0.0)) + LUNGSHA_ALWAYS_ENEMY_ULT_TAKEN_INC
    return s

# =====================================================
# Calculation - 사이클 딜
# =====================================================
def lungsha_cycle_damage_fast(stats: Dict[str, float], party: List[str], artifact_name: str) -> Dict[str, float]:
    stats = _apply_lungsha_fixed_effects(stats, artifact_name)

    total_time = 30.0
    # 스킬별 처음부터 계산: skill_damage_from_start 사용

    breakdown = {
        "basic": 0.0,
        "special": 0.0,
        "ult": 0.0,
        "proc": 0.0,
        "strike": 0.0,
        "unique": 0.0,
    }

    total_direct = 0.0
    for tok in LUNGSHA_CYCLE_TOKENS:
        if tok == "B4":
            dmg = skill_damage_from_start(stats, LUNGSHA_BASIC_COEFF, "basic")
            breakdown["basic"] += dmg
        elif tok == "ES":
            dmg = skill_damage_from_start(stats, LUNGSHA_EMPOWERED_SPECIAL_COEFF, "special")
            breakdown["special"] += dmg
        elif tok == "S1":
            dmg = skill_damage_from_start(stats, LUNGSHA_SPECIAL1_COEFF, "special")
            breakdown["special"] += dmg
        elif tok == "S2":
            dmg = skill_damage_from_start(stats, LUNGSHA_SPECIAL2_COEFF, "special")
            breakdown["special"] += dmg
        elif tok == "S3":
            dmg = skill_damage_from_start(stats, LUNGSHA_SPECIAL3_COEFF, "special")
            breakdown["special"] += dmg
        else:
            dmg = skill_damage_from_start(stats, LUNGSHA_ULT_COEFF, "ult")
            breakdown["ult"] += dmg
        total_direct += dmg

    strike = strike_total_from_direct(total_direct, "룽샤맛 쿠키", stats, party)
    breakdown["strike"] = strike

    unique_total = skill_damage_from_start(stats, float(stats.get("unique_extra_coeff", 0.0)), "none") * total_time
    breakdown["unique"] = unique_total

    total_damage = math.floor(total_direct + strike + unique_total)

    local_raw = stats.get("_local", None)
    local: Dict[str, Any] = local_raw if isinstance(local_raw, dict) else {}
    elem_dmg_mult = float(local.get("elem_dmg_mult", stats.get("elem_dmg_mult", 1.0)))
    if elem_dmg_mult != 1.0:
        total_damage *= elem_dmg_mult
        for k in breakdown:
            breakdown[k] *= elem_dmg_mult

    dps = total_damage / 30.0
    return {
        "total_damage": total_damage,
        "total_time": total_time,
        "dps": dps,
        "breakdown_basic": breakdown["basic"],
        "breakdown_special": breakdown["special"],
        "breakdown_ult": breakdown["ult"],
        "breakdown_proc": breakdown["proc"],
        "breakdown_strike": breakdown["strike"],
        "breakdown_unique": breakdown["unique"],
    }

# =====================================================
# Calculation - 최적화
# =====================================================
def optimize_lungsha_cycle(
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
    cookie = "룽샤맛 쿠키"
    base = BASE_STATS_LUNGSHA[cookie].copy()

    equips = _resolve_equip_list_override(equip_override, lungsha_allowed_equips())
    uniques = _resolve_unique_list_override(unique_override, lungsha_allowed_uniques())
    potentials = lungsha_allowed_potentials()
    artifacts = lungsha_allowed_artifacts()
    shard_candidates = lungsha_generate_shard_candidates_no_cr(step=max(1, int(step or 1)))

    shard_adds_list: List[Tuple[Dict[str, int], List[Tuple[str, float]], int]] = []
    for sh in shard_candidates:
        adds: List[Tuple[str, float]] = []
        used = 0
        for k, slots in sh.items():
            slots_i = int(slots)
            used += slots_i
            inc = float(SHARD_INC.get(k, 0.0))
            if inc and slots_i:
                adds.append((k, inc * slots_i))
        shard_adds_list.append((sh, adds, used))

    zero_shards = {k: 0 for k in SHARD_INC.keys()}
    total = max(1, len(equips) * len(artifacts) * len(uniques) * len(potentials) * len(shard_candidates))
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
    cr_inc = float(SHARD_INC.get("crit_rate", 0.0))
    ea_inc = float(SHARD_INC.get("elem_atk", 0.0))

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
                    template = _apply_lungsha_fixed_effects(template, artifact_name)

                    if not is_valid_by_caps(template):
                        done += len(shard_candidates)
                        if (done % tick) == 0:
                            emit(done / total)
                        continue

                    req_cr_slots_opt = _min_crit_slots_needed_for_crit100_generic(template)
                    if req_cr_slots_opt is None:
                        done += len(shard_candidates)
                        if (done % tick) == 0:
                            emit(done / total)
                        continue
                    req_cr_slots = int(req_cr_slots_opt)

                    template.pop("_applied_party_buffs", None)
                    template.pop("_applied_enemy_debuffs", None)

                    remain_slots = NORMAL_SLOTS - req_cr_slots
                    if remain_slots < 0:
                        done += len(shard_candidates)
                        if (done % tick) == 0:
                            emit(done / total)
                        continue

                    for sh_base, adds, used in shard_adds_list:
                        done += 1
                        if (done % tick) == 0:
                            emit(done / total)
                        if used > remain_slots:
                            continue

                        ea_slots = remain_slots - used
                        stats = template.copy()
                        stats.pop("_damage_context_cache", None)
                        for k, dv in adds:
                            stats[k] = float(stats.get(k, 0.0)) + dv
                        if req_cr_slots and cr_inc:
                            stats["crit_rate"] = float(stats.get("crit_rate", 0.0)) + cr_inc * req_cr_slots
                        if ea_slots and ea_inc:
                            stats["elem_atk"] = float(stats.get("elem_atk", 0.0)) + ea_inc * int(ea_slots)

                        # 설탕유리조각은 방어관통을 올리지 않으므로 template 단계의 cap 검사 결과를 그대로 사용한다.
                        # 치확 100% 조건은 req_cr_slots 계산으로 이미 맞춘 상태다.

                        cycle = lungsha_cycle_damage_fast(stats, party, artifact_name)
                        dps = cycle["dps"]
                        if (best is None) or (dps > best["dps"]):
                            shards_out = dict(sh_base)
                            shards_out["crit_rate"] = int(req_cr_slots)
                            shards_out["elem_atk"] = int(ea_slots)
                            shards_out["basic_dmg"] = 0
                            shards_out["special_dmg"] = 0
                            shards_out["ult_dmg"] = 0
                            shards_out["passive_dmg"] = 0
                            shards_out["def_pct"] = 0
                            shards_out["shield_pct"] = 0
                            shards_out["heal_pct"] = 0
                            best = {
                                "cookie": cookie,
                                "dps": dps,
                                "cycle_total_damage": cycle["total_damage"],
                                "cycle_total_time": 30.0,
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
                            }

    emit(1.0)
    return best
