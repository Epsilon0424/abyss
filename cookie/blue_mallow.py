# =====================================================
# Imports
# =====================================================
from .common import *
from .common import _resolve_equip_list_override, _min_crit_slots_needed_for_crit100_generic, _resolve_unique_list_override
from functools import lru_cache

# =====================================================
# 블루멜로우 쿠키
# - 데미지 딜러 / 마법형 / 물속성
# - 승급 효과 공격력 +30%는 흑보리처럼 실제 공격력에서 분리해서
#   base atk를 1.3으로 나누고 atk_pct +30%로 반영한다.
# =====================================================

BLUE_MALLOW_FORCE_CRIT_100 = True
BLUE_MALLOW_WEAPON_ATK_PCT = 0.52
BLUE_MALLOW_WEAPON_FINAL_DMG = 0.30
BLUE_MALLOW_FIXED_ARTIFACT = "오늘도 완벽!"
BLUE_MALLOW_DEFAULT_SEAZ = "바닐라몬드:치열한 선봉자"
BLUE_MALLOW_FIXED_UNIQUE = "로드 나이트메어의 뒤틀린 기억"

# 사용자가 알려준 실제 공격력: 889 + 57 = 946
# 승급 공격력 +30%를 역산해서 기본 공격력으로 분리한다.
BASE_STATS_BLUE_MALLOW = {
    "블루멜로우맛 쿠키": {
        "atk": atk_from_promoted_base_without_friendship(889.0, 0.30),
        "friendship_atk": friendship_atk_for("블루멜로우맛 쿠키"),
        "def": 339.0 + 27.0,
        "hp": 4131.0 + 345.0,
        "elem_atk": 0.0,
        # 승급 공격력 +30% + 전용무기 기본 옵션 공격력 +52%
        "atk_pct": 0.30 + BLUE_MALLOW_WEAPON_ATK_PCT,
        "crit_rate": 0.15,
        "crit_dmg": 1.60,
        "armor_pen": 0.0,
        # 승급 최종 피해 +4% + 전용무기 고유능력 최종 피해 +30%
        "final_dmg": 0.04 + BLUE_MALLOW_WEAPON_FINAL_DMG,
    }
}

# 기본공격 피해 : 85.2%
# 패시브 [노블레스 오블리주] 추가 피해: 426%
# 차지 [퍼펙트 티 파티]는 기본공격과 별도 수치로 계산한다.
BLUE_MALLOW_BASIC_COEFF = 0.852  # 웰컴 드링크 일반 기본 공격 1회 계수
BLUE_MALLOW_NOBLESSE_COEFF = 4.26  # 패시브 [노블레스 오블리주] 추가 피해 계수

# 차지 단계 피해
# 1단계 [얼리 모닝 티]: 160.5% × 3
# 2단계 [일레븐지스]: 213% × 5
# 3단계 [애프터눈 티]: 피해 계산은 319.5% × 8
# 4단계 [애프터 디너 티]: 71% × 15 + 2130%
BLUE_MALLOW_CHARGE1_COEFF = 1.605 * 3.0  # [퍼펙트 티 파티] 1단계 [얼리 모닝 티] 계수
BLUE_MALLOW_CHARGE2_COEFF = 2.13  * 5.0  # [퍼펙트 티 파티] 2단계 [일레븐지스] 계수
BLUE_MALLOW_CHARGE3_HITS = 8  # [애프터눈 티] 적중 수
BLUE_MALLOW_CHARGE4_HITS = 16  # 71% × 15타 + 2130% 마무리 1타
BLUE_MALLOW_CHARGE3_COEFF = 3.195 * BLUE_MALLOW_CHARGE3_HITS
BLUE_MALLOW_CHARGE4_COEFF = (0.710 * 15.0) + 21.30  # [애프터 디너 티] 직접 피해 총계수

# [왕관의 무게]
# [퍼펙트 티 파티] 차지 단계에 따라 각 적중에서 발생하는
# [노블레스 오블리주] 426% 추가 피해가 0/10/20/30% 증가한다.
# 3차징: 8타 각각 426% × 1.20
# 4차징: 16타 각각 426% × 1.30
BLUE_MALLOW_CROWN_NOBLESSE_BONUS = {
    0: 0.00,
    1: 0.00,
    2: 0.10,
    3: 0.20,
    4: 0.30,
}

# 특수스킬은 보호막 스킬이라 피해 계산에서는 제외한다.
# 실제 30초 사이클:
# 특 → 궁(인퓨전 진입) → 4차징 → 2평 → 4차징 → 특 →
# 4평 → 3차징 → 3차징 → 3평 → 3차징
#
# [퍼펙트 티 파티] 3차징은 기본 공격 피해,
# [애프터 디너 티] 4차징은 궁극기 피해로 분류한다.
BLUE_MALLOW_CYCLE_TIME = 30.0
BLUE_MALLOW_ULT_COEFF = BLUE_MALLOW_CHARGE4_COEFF
BLUE_MALLOW_CYCLE_TOKENS = [
    "S",
    "U",
    "C4",
    "B", "B",
    "C4",
    "S",
    "B", "B", "B", "B",
    "C3",
    "C3",
    "B", "B", "B",
    "C3",
]

# =====================================================
# Candidate helpers
# =====================================================
def blue_mallow_allowed_equips() -> List[str]:
    return ["달콤한 설탕 깃털", "미지의 방랑자", "수상한 사냥꾼", "시간관리국의 제복"]

def blue_mallow_allowed_uniques() -> List[str]:
    return [BLUE_MALLOW_FIXED_UNIQUE, "꿈세계의 기억", "새벽을 여는 달빛술사 쿠키의 기억"]

def blue_mallow_allowed_artifacts() -> List[str]:
    return [BLUE_MALLOW_FIXED_ARTIFACT]

def blue_mallow_allowed_seaz() -> List[str]:
    return [x for x in SEAZNITES.keys() if str(x).startswith("바닐라몬드:")]

@lru_cache(maxsize=None)
def blue_mallow_generate_potentials_common() -> List[Dict[str, int]]:
    """속성 공격력 2칸을 고정하고 치확 포함 딜 잠재력을 탐색한다."""
    return generate_damage_potential_candidates(fixed={"elem_atk": 2})

@lru_cache(maxsize=None)
def blue_mallow_generate_shard_candidates_no_cr(step: int = 1) -> List[Dict[str, int]]:
    step = max(1, int(step or 1))
    keys = ["crit_dmg", "all_elem_dmg", "atk_pct", "passive_dmg"]
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
# Calculation
# =====================================================
def blue_mallow_cycle_damage_fast(stats: Dict[str, float], party: List[str], artifact_name: str) -> Dict[str, float]:
    breakdown = {
        "basic": 0.0,
        "special": 0.0,
        "ult": 0.0,
        "passive": 0.0,
        "proc": 0.0,
        "strike": 0.0,
        "unique": 0.0,
    }

    total_direct = 0.0

    artifact_meta = ARTIFACTS.get(artifact_name, {}) or {}
    blue_meta = artifact_meta.get("blue_mallow", {}) or {}
    noblesse_extra = 1.0 + float(blue_meta.get("noblesse_extra_dmg", 0.0))
    perfectionist_extra = 1.0 + float(blue_meta.get("perfectionist_passive_dmg", 0.0))

    def charge_passive_damage(charge_stage: int, hit_count: int) -> float:
        """차징 공격의 각 적중마다 노블레스 오블리주 426%를 1회씩 적용한다."""
        crown_bonus = float(BLUE_MALLOW_CROWN_NOBLESSE_BONUS.get(int(charge_stage), 0.0))
        passive_mult = noblesse_extra * (1.0 + crown_bonus) * perfectionist_extra
        return skill_damage_from_start(
            stats,
            BLUE_MALLOW_NOBLESSE_COEFF * max(0, int(hit_count)),
            "passive",
            extra_skill_mult=passive_mult,
        )

    for tok in BLUE_MALLOW_CYCLE_TOKENS:
        dmg = 0.0

        if tok == "B":
            # 웰컴 드링크 일반 기본 공격 1회.
            dmg = skill_damage_from_start(stats, BLUE_MALLOW_BASIC_COEFF, "basic")
            breakdown["basic"] += dmg

        elif tok == "C3":
            # 퍼펙트 티 파티 3차징 [애프터눈 티]는 기본 공격 피해다.
            charge_dmg = skill_damage_from_start(stats, BLUE_MALLOW_CHARGE3_COEFF, "basic")
            passive_dmg = charge_passive_damage(3, BLUE_MALLOW_CHARGE3_HITS)
            breakdown["basic"] += charge_dmg
            breakdown["passive"] += passive_dmg
            dmg = charge_dmg + passive_dmg

        elif tok == "C4":
            # 인퓨전 상태의 4차징 [애프터 디너 티]는 궁극기 피해다.
            charge_dmg = skill_damage_from_start(stats, BLUE_MALLOW_CHARGE4_COEFF, "ult")
            passive_dmg = charge_passive_damage(4, BLUE_MALLOW_CHARGE4_HITS)
            breakdown["ult"] += charge_dmg
            breakdown["passive"] += passive_dmg
            dmg = charge_dmg + passive_dmg

        elif tok == "S":
            # 티 브레이크는 보호막 스킬이라 직접 피해는 없다.
            breakdown["special"] += 0.0

        elif tok == "U":
            # 궁극기 버튼은 인퓨전 상태 진입만 담당하며, 실제 피해는 이어지는 C4에서 발생한다.
            dmg = 0.0

        total_direct += dmg

    sugar_proc = skill_damage_from_start(stats, float(stats.get("sugar_brilliance_coeff", 0.0)), "none")
    if sugar_proc:
        total_direct += sugar_proc
        breakdown["proc"] += sugar_proc

    strike = strike_total_from_direct(total_direct, "블루멜로우맛 쿠키", stats, party)
    breakdown["strike"] = strike

    unique_total = (
        skill_damage_from_start(stats, float(stats.get("unique_extra_coeff", 0.0)), "none")
        * BLUE_MALLOW_CYCLE_TIME
    )
    breakdown["unique"] = unique_total

    total_damage = math.floor(total_direct + strike + unique_total)

    local_raw = stats.get("_local", None)
    local: Dict[str, Any] = local_raw if isinstance(local_raw, dict) else {}
    elem_dmg_mult = float(local.get("elem_dmg_mult", stats.get("elem_dmg_mult", 1.0)))
    if elem_dmg_mult != 1.0:
        total_damage *= elem_dmg_mult
        for key in breakdown:
            breakdown[key] *= elem_dmg_mult

    dps = total_damage / BLUE_MALLOW_CYCLE_TIME
    return {
        "total_damage": total_damage,
        "total_time": BLUE_MALLOW_CYCLE_TIME,
        "dps": dps,
        "breakdown_basic": breakdown["basic"],
        "breakdown_special": breakdown["special"],
        "breakdown_ult": breakdown["ult"],
        "breakdown_passive": breakdown["passive"],
        "breakdown_proc": breakdown["proc"],
        "breakdown_strike": breakdown["strike"],
        "breakdown_unique": breakdown["unique"],
    }

def optimize_blue_mallow_cycle(
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

    cookie = '블루멜로우맛 쿠키'
    base = BASE_STATS_BLUE_MALLOW[cookie].copy()
    equips = _resolve_equip_list_override(equip_override, blue_mallow_allowed_equips())
    uniques = _resolve_unique_list_override(unique_override, blue_mallow_allowed_uniques())
    potentials = blue_mallow_generate_potentials_common()
    artifacts = blue_mallow_allowed_artifacts()
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
                            return blue_mallow_cycle_damage_fast(stats, party, artifact_name)

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
