# =====================================================
# 가져오기
# =====================================================
from .common import *
from .common import _resolve_equip_list_override, _min_crit_slots_needed_for_crit100_generic, _resolve_unique_list_override
from functools import lru_cache
from typing import Sequence

# =====================================================
# 매드시럽 쿠키 (빛 / 레전더리 / 딜러)
# =====================================================

# =====================================================
# 상수
# =====================================================
MAD_SYRUP_PROMO_ENABLED = True
MAD_SYRUP_WEAPON_ATK_PCT = 0.52
MAD_SYRUP_WEAPON_FINAL_DMG = 0.30

# 승급 효과
# - 적 속성 내성 -5% 상시 적용 (고정값, 디버프 증폭 제외 축)
# - 1·2·3특(일반 특수스킬) 피해 ×1.08
# - 강특 사용 1회마다 변신궁 피해 +10.7% (스택끼리 합연산, 최대 9중첩)
MAD_SYRUP_PROMO_ELEM_RES_REDUCTION = 0.05
MAD_SYRUP_PROMO_SPECIAL_NORMAL_MULT = 1.08
MAD_SYRUP_PROMO_SPECIAL_ENHANCED_EXTRA_MULT = 1.365 
MAD_SYRUP_PROMO_ULT_ENH_PER_STACK = 0.107
MAD_SYRUP_PROMO_ULT_ENH_MAX_STACKS = 9

MAD_SYRUP_FIXED_ARTIFACT = "끈질긴 역병의 시선"
# 화면 기본 시즈나이트 (믿음직한 브리더는 윈드파라거스 파티 전용이라 제외 후 최고값)
MAD_SYRUP_DEFAULT_SEAZ = "소다마린:거침없는 습격자"

BASE_STATS_MAD_SYRUP = {
    "매드시럽 쿠키": {
        "atk": 584.0,
        "friendship_atk": friendship_atk_for("매드시럽 쿠키"),
        "def": 566.0,
        "hp": 6392.0,
        "elem_atk": 0.0,
        # 전용무기 기본 옵션 공격력 +52%
        "atk_pct": MAD_SYRUP_WEAPON_ATK_PCT,
        "crit_rate": 0.15,
        "crit_dmg": 1.875,
        "armor_pen": 0.0,
        # 승급/기본 최종 피해 +5% + 전용무기 고유능력 최종 피해 +30%
        "final_dmg": 0.05 + MAD_SYRUP_WEAPON_FINAL_DMG,
    }
}

# -----------------------------------------------------
# 스킬 계수 (각 상수는 해당 스킬 1회 사용 시 합산 계수)
# -----------------------------------------------------
MAD_BASIC_COEFF = 1.022 + 1.221 + 1.562 * 4  # 평 1~3타 합산 계수 102.2% + 122.1% + 156.2%*4
MAD_BASIC_CHARGE_COEFF = 3.124 * 6 + 22.748  # 변신차징 계수 312.4% * 6 + 2274.8%

MAD_SPECIAL1_NORMAL_COEFF = 14.086           # 1특 계수: 1408.6%
MAD_SPECIAL2_NORMAL_COEFF = 5.936 + 15.805   # 2특 계수: 593.6% + 1580.5%
MAD_SPECIAL3_NORMAL_COEFF = 33.796           # 3특 계수: 3379.6%
MAD_SPECIAL_ENHANCED_COEFF = 16.898 * 2      # 강특 계수: 1689.8%×2
MAD_SPECIAL_COEFF_ARTI = 7.0 * 2             # 아티 강특 계수: 700% * 2 (끈질긴 역병의 시선 장착 시)

MAD_PASSIVE_COEFF = 1.42                     # 패시브 1회 피해 계수: 142%
MAD_ULT_NORMAL_COEFF = 27.4344 * 3           # 궁 계수: 2743.44% * 3
MAD_ULT_ENHANCED_COEFF = 10.153 * 8          # 변신궁 계수: 1015.3% * 8

# -----------------------------------------------------
# 타수 (패시브 발동 횟수 계산용)
# - 패시브는 다른 공격 적중 시마다 새로 피해를 주고 지속시간이 초기화되므로
# 사이클 내 패시브 발동 횟수 = 패시브를 제외한 모든 공격의 적중 타수
# -----------------------------------------------------
MAD_HITS = {
    "S1": 1,   # 1특
    "B": 6,    # 평타 (1타 + 2타 + 3타×4)
    "S2": 2,   # 2특
    "S3": 1,   # 3특
    "U": 3,    # 궁
    "BC": 7,   # 변신차징 (6 + 1)
    "SE": 2,   # 강특
    "SA": 2,   # 아티 강특 (강특 발동 시 자동 사용)
    "UE": 8,   # 변신궁
}

MAD_CYCLE_TIME = 30.0

# 사이클
# SPECIAL1, BASIC → SPECIAL2, BASIC → SPECIAL3, ULT_NORMAL → BASIC_CHARGE
# → (SPECIAL_ENHANCED + SPECIAL_ARTI) × 9 → ULT_ENHANCED
# 아티 강특(SA)은 강특(SE) 토큰 처리 시 함께 계산
MAD_ROTATION_TOKENS: Tuple[str, ...] = (
    "S1", "B",
    "S2", "B",
    "S3", "U",
    "BC",
) + ("SE",) * 9 + ("UE",)

# =====================================================
# 상시 효과
# =====================================================
def _apply_mad_syrup_fixed_effects(stats: Dict[str, float]) -> Dict[str, float]:
    """매드시럽 승급 상시 효과 (중복 적용 방지 마커 사용)"""
    if stats.get("_applied_mad_syrup_fixed", False):
        return stats
    s = stats.copy()
    s["_applied_mad_syrup_fixed"] = True

    if MAD_SYRUP_PROMO_ENABLED:
        # 승급: 적 속성 내성 -5% 상시
        # 장비/설탕유리조각 세트처럼 고정값 축(디버프 증폭 제외)으로 반영
        s["elem_res_reduction_no_scale_raw"] = (
            float(s.get("elem_res_reduction_no_scale_raw", 0.0)) + MAD_SYRUP_PROMO_ELEM_RES_REDUCTION
        )

    s.pop("_damage_context_cache", None)
    return s

# =====================================================
# 타수 / 이벤트
# =====================================================
def _mad_rotation_hits(tokens: Sequence[str], artifact_name: str) -> int:
    """사이클 총 적중 타수 = 패시브 발동 횟수"""
    arti_on = artifact_name == MAD_SYRUP_FIXED_ARTIFACT
    total = 0
    for tok in tokens:
        total += MAD_HITS[tok]
        if tok == "SE" and arti_on:
            total += MAD_HITS["SA"]
    return total + 10

# =====================================================
# 사이클 피해 계산
# =====================================================
def mad_syrup_cycle_damage_fast(
    stats: Dict[str, float],
    party: List[str],
    artifact_name: str,
    seaz_name: str = "",
) -> Dict[str, float]:
    del seaz_name  # 시즈 효과는 build_stats_for_combo 에서 일괄 반영
    stats = _apply_mad_syrup_fixed_effects(stats)
    total_time = MAD_CYCLE_TIME
    arti_on = artifact_name == MAD_SYRUP_FIXED_ARTIFACT

    promo_special_mult = MAD_SYRUP_PROMO_SPECIAL_NORMAL_MULT if MAD_SYRUP_PROMO_ENABLED else 1.0
    promo_special_enh_mult = MAD_SYRUP_PROMO_SPECIAL_ENHANCED_EXTRA_MULT if MAD_SYRUP_PROMO_ENABLED else 1.0
    per_stack = MAD_SYRUP_PROMO_ULT_ENH_PER_STACK if MAD_SYRUP_PROMO_ENABLED else 0.0

    breakdown = {
        "basic": 0.0,
        "special": 0.0,
        "ult": 0.0,
        "passive": 0.0,
        "proc": 0.0,
        "strike": 0.0,
        "unique": 0.0,
    }

    # 동일 스킬 1회 피해는 한 번만 계산 (최적화 루프 반복 비용 절감)
    basic_unit = skill_damage_from_start(stats, MAD_BASIC_COEFF, "basic")
    basic_charge_unit = skill_damage_from_start(stats, MAD_BASIC_CHARGE_COEFF, "basic")
    s1_unit = skill_damage_from_start(stats, MAD_SPECIAL1_NORMAL_COEFF, "special", extra_skill_mult=promo_special_mult)
    s2_unit = skill_damage_from_start(stats, MAD_SPECIAL2_NORMAL_COEFF, "special", extra_skill_mult=promo_special_mult)
    s3_unit = skill_damage_from_start(stats, MAD_SPECIAL3_NORMAL_COEFF, "special", extra_skill_mult=promo_special_mult)
    se_unit = skill_damage_from_start(stats, MAD_SPECIAL_ENHANCED_COEFF, "special", extra_skill_mult=promo_special_enh_mult)
    sa_unit = skill_damage_from_start(stats, MAD_SPECIAL_COEFF_ARTI, "special") if arti_on else 0.0
    u_unit = skill_damage_from_start(stats, MAD_ULT_NORMAL_COEFF, "ult")

    total_direct = 0.0
    enh_stacks = 0
    for tok in MAD_ROTATION_TOKENS:
        if tok == "B":
            dmg = basic_unit
            breakdown["basic"] += dmg
        elif tok == "BC":
            dmg = basic_charge_unit
            breakdown["basic"] += dmg
        elif tok == "S1":
            dmg = s1_unit
            breakdown["special"] += dmg
        elif tok == "S2":
            dmg = s2_unit
            breakdown["special"] += dmg
        elif tok == "S3":
            dmg = s3_unit
            breakdown["special"] += dmg
        elif tok == "SE":
            dmg = se_unit + sa_unit
            breakdown["special"] += dmg
            enh_stacks = min(enh_stacks + 1, MAD_SYRUP_PROMO_ULT_ENH_MAX_STACKS)
        elif tok == "U":
            dmg = u_unit
            breakdown["ult"] += dmg
        elif tok == "UE":
            # 강특 스택만큼 변신궁 피해 증가 (스택끼리 합연산) 후 스택 소모
            stack_mult = 1.0 + per_stack * enh_stacks
            dmg = skill_damage_from_start(stats, MAD_ULT_ENHANCED_COEFF, "ult", extra_skill_mult=stack_mult)
            breakdown["ult"] += dmg
            enh_stacks = 0
        else:
            raise ValueError(f"알 수 없는 매드시럽 사이클 토큰입니다: {tok}")
        total_direct += dmg

    # 패시브: 적중 타수만큼 발동
    passive_hits = _mad_rotation_hits(MAD_ROTATION_TOKENS, artifact_name)
    passive_total = skill_damage_from_start(stats, MAD_PASSIVE_COEFF, "passive") * passive_hits
    breakdown["passive"] = passive_total
    total_direct += passive_total

    # 광휘 세트: 궁극기 사용 횟수(궁 + 변신궁)만큼 발동
    ult_count = sum(1 for tok in MAD_ROTATION_TOKENS if tok in ("U", "UE"))
    sugar_proc = skill_damage_from_start(stats, float(stats.get("sugar_brilliance_coeff", 0.0)), "none") * ult_count
    if sugar_proc:
        total_direct += sugar_proc
        breakdown["proc"] += sugar_proc

    strike = strike_total_from_direct(total_direct, "매드시럽 쿠키", stats, party)
    breakdown["strike"] = strike

    unique_total = skill_damage_from_start(stats, float(stats.get("unique_extra_coeff", 0.0)), "none") * total_time
    breakdown["unique"] = unique_total

    total_damage = math.floor(total_direct + strike + unique_total)

    local_raw = stats.get("_local", None)
    local: Dict[str, any] = local_raw if isinstance(local_raw, dict) else {}
    elem_dmg_mult = float(local.get("elem_dmg_mult", stats.get("elem_dmg_mult", 1.0)))
    if elem_dmg_mult != 1.0:
        total_damage *= elem_dmg_mult
        for k in breakdown:
            breakdown[k] *= elem_dmg_mult

    dps = total_damage / total_time
    return {
        "total_damage": total_damage,
        "total_time": total_time,
        "dps": dps,
        "rotation_total_hits": passive_hits,
        "breakdown_basic": breakdown["basic"],
        "breakdown_special": breakdown["special"],
        "breakdown_ult": breakdown["ult"],
        "breakdown_passive": breakdown["passive"],
        "breakdown_proc": breakdown["proc"],
        "breakdown_strike": breakdown["strike"],
        "breakdown_unique": breakdown["unique"],
    }

# =====================================================
# 장비 및 후보
# =====================================================
def mad_syrup_allowed_equips() -> List[str]:
    return ["달콤한 설탕 깃털", "미지의 방랑자", "수상한 사냥꾼", "시간관리국의 제복"]

# 시즌별 사격형 딜러 유니크 기본 후보
# (화면에서 유니크를 직접 고르면 그 값이 우선 적용되고, 이 목록은 미지정 시 기본값)
MAD_SYRUP_UNIQUE_BY_SEASON = {
    "season1": "로스베이컨맛 쿠키의 기억",
    "season2": "샬롯맛 쿠키의 기억",
    "season3": "피닉스페퍼 쿠키의 기억",
    "season4": "로드 나이트메어의 뒤틀린 기억",
    "season5": "매드시럽 쿠키의 기억",
}

def mad_syrup_allowed_uniques() -> List[str]:
    season = get_active_unique_season()
    name = MAD_SYRUP_UNIQUE_BY_SEASON.get(season, "")
    if name and name in UNIQUE_SHARDS:
        return [name]
    # 알 수 없는 시즌: 현재 시즌에서 장착 가능한 딜러 유니크 중 첫 번째
    for unique_name in UNIQUE_SHARDS:
        if unique_name != "NONE" and is_unique_allowed("매드시럽 쿠키", unique_name):
            return [unique_name]
    return ["NONE"]

def mad_syrup_allowed_artifacts() -> List[str]:
    return [MAD_SYRUP_FIXED_ARTIFACT]

def mad_syrup_allowed_seaz() -> List[str]:
    return [x for x in SEAZNITES.keys() if str(x).startswith("소다마린:")]

@lru_cache(maxsize=None)
def mad_syrup_generate_potentials_common() -> List[Dict[str, int]]:
    """매드시럽 쿠키 잠재력 후보"""
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

# =====================================================
# 최적화
# =====================================================
def optimize_mad_syrup_cycle(
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
    """매드시럽 쿠키 최적화"""
    del step  # 장비별 조각 최적화는 항상 1칸 단위로 수행

    cookie = '매드시럽 쿠키'
    base = BASE_STATS_MAD_SYRUP[cookie].copy()
    equips = _resolve_equip_list_override(equip_override, mad_syrup_allowed_equips())
    uniques = _resolve_unique_list_override(unique_override, mad_syrup_allowed_uniques())
    potentials = [dict(potential_override)] if potential_override is not None else mad_syrup_generate_potentials_common()
    artifacts = mad_syrup_allowed_artifacts()
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
                        # 승급 상시 효과(속성 내성 -5%)를 결과 스탯에도 표시되도록 템플릿에 반영
                        template = _apply_mad_syrup_fixed_effects(template)

                        def cycle_for(
                            stats: Dict[str, float],
                            artifact_name: str = artifact_name,
                        ) -> Dict[str, float]:
                            return mad_syrup_cycle_damage_fast(
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
