# =====================================================
# 가져오기
# =====================================================
from .common import *
from .common import _resolve_equip_list_override, _min_crit_slots_needed_for_crit100_generic, _resolve_unique_list_override
from functools import lru_cache

# =====================================================
# 멜랑크림 쿠키
# =====================================================

# =====================================================
# 상수
# =====================================================
MELAN_PROMO_ENABLED = True

MELAN_PROMO_CRIT_RATE_MULT = 1.0
MELAN_PROMO_ARMOR_PEN_MULT = 1.0
MELAN_PROMO_ATK_PCT_MULT   = 1.0
MELAN_PROMO_FINAL_DMG_MULT = 1.0

MELAN_PROMO_UNDEAD_EXTRA     = 1
MELAN_PROMO_NOVA_EXTRA       = 2
MELAN_PROMO_APOCALYPSE_X2    = True
MELAN_PROMO_PRIMA_DMG_MULT   = 1.25

MELAN_PRELUDE_COEFF = 150.0  # [프렐류드] 500%가 30회 적용되는 궁극기 계수
MELAN_WEAPON_ATK_PCT = 0.52
MELAN_WEAPON_FINAL_DMG = 0.30

BASE_STATS_MELAN = {
    "멜랑크림 쿠키": {
        "atk": 767.0,
        "friendship_atk": friendship_atk_for("멜랑크림 쿠키"),
        "elem_atk": 0.0,
        # 전용무기 기본 옵션 공격력 +52%
        "atk_pct": MELAN_WEAPON_ATK_PCT,
        "crit_rate": 0.25,
        "crit_dmg": 1.875,
        "armor_pen": 0.08,
        # 승급/기본 최종 피해 +5% + 전용무기 고유능력 최종 피해 +30%
        "final_dmg": 0.05 + MELAN_WEAPON_FINAL_DMG,
    }
}

# =====================================================
# 사이클 및 계수
# =====================================================
MELAN_BASIC_NORMAL = [1.704, 1.704, 3.067, 3.408 + 4.544]  # 일반 기본공격 4타 계수
MELAN_BASIC_ENHANCED = [2.726, 2.726, 4.899, 5.433 + 7.270]  # 강화 기본공격 4타 계수: 272.6%, 272.6%, 489.9%, 543.3%+727.0%

MELAN_SPECIAL_NORMAL_COEFF = (4.26 * 5) + 10.65   # 일반 특수스킬 계수 426% × 5 + 마무리 1065%
MELAN_SPECIAL_ENHANCED_COEFF = (7.20 * 8) + 16.00 # 강화 특수스킬 계수 720% × 8 + 1600%
MELAN_ULT_NORMAL_COEFF     = (7.81 * 6) + 35.50  # 일반 궁극기 계수

PASSIVE_TIER_COEFF = {  # 숨결 누적 패시브 티어별 피해 계수
    0.25: 6.816,
    0.50: 7.952,
    0.75: 11.36 * 2,
}

PRIMA_ENTRY_COEFF = 11.36  # 프리마 진입 피해 계수
BREATH_GAIN_PER_BASIC_HIT = 0.05

# 숨결 누적용 히트 수
# - 프리마 진입 전 일반 궁극기·기본공격·특수 타격 숨결 누적
# - 궁극기 781% × 6 + 3550%·7타
# - 강화 기본공격 4타
# - 특수스킬 426% × 5 + 1065%·6타
MELAN_ULT_NORMAL_HITS = 7
MELAN_BASIC_NORMAL_HITS = len(MELAN_BASIC_NORMAL)
MELAN_SPECIAL_NORMAL_HITS = 6

MELAN_CYCLE_TOKENS = [
    "U", "B4", "S", "B4", "U",
    "S_ENH", "B4", "B4", "B4", "B4", "B4",
    "S_ENH", "B4", "B4", "B4", "B4", "B4",
]

MELAN_BASIC_NORMAL_SUM = sum(MELAN_BASIC_NORMAL)
MELAN_BASIC_ENHANCED_SUM = sum(MELAN_BASIC_ENHANCED)

# =====================================================
# 고속 이벤트 전처리
# =====================================================
def _melan_precompute_fast() -> Dict[str, Union[int, float]]:
    ult_count = 0
    is_prima = False
    breath = 0.0
    eps = 1e-12

    c: Dict[str, Union[int, float]] = {
        "b4_norm": 0,
        "s_norm": 0,
        "s_enh": 0,
        "u_norm": 0,
        "prelude": 0,
        "entry": 0,
        "b4_enhanced": 0,
        "hits_pre_prima": 0,
        "tier_0p25": 0,
        "tier_0p50": 0,
        "tier_0p75": 0,
        "total_time": 30.0,
    }

    def normalize_breath(x: float) -> float:
        return 0.0 if x >= 1.0 - eps else x

    def add_breath_hits(hit_count: int) -> None:
        """멜랑크림 프리마 전 숨결 누적"""
        nonlocal breath

        for _ in range(int(hit_count)):
            c["hits_pre_prima"] = int(c["hits_pre_prima"]) + 1
            prev = breath
            new = prev + BREATH_GAIN_PER_BASIC_HIT

            for key, tier in (("tier_0p25", 0.25), ("tier_0p50", 0.50), ("tier_0p75", 0.75)):
                if (prev + eps) < tier <= (new + eps):
                    c[key] = int(c[key]) + 1

            breath = normalize_breath(new)

    for tok in MELAN_CYCLE_TOKENS:
        if tok == "U":
            ult_count += 1
            is_transform = (ult_count == 2)

            if (not is_prima) and (not is_transform):
                # 첫 번째 궁극기: 일반 궁극기 + 최후의 전주곡 피해 계산
                c["u_norm"] = int(c["u_norm"]) + 1
                c["prelude"] = int(c["prelude"]) + 1

                # 첫 번째 궁극기 히트도 숨결 누적에 포함
                add_breath_hits(MELAN_ULT_NORMAL_HITS)

            elif is_transform:
                # 두 번째 궁극기: 프리마 진입
                c["entry"] = int(c["entry"]) + 1
                is_prima = True
                breath = 0.0

        elif tok == "S":
            # 일반 특수스킬 426% × 5 + 마무리 1065%
            # 프리마 상태 무관 일반 특수스킬 토큰
            c["s_norm"] = int(c["s_norm"]) + 1

            if not is_prima:
                # 일반 특수스킬 히트도 숨결 누적에 포함
                add_breath_hits(MELAN_SPECIAL_NORMAL_HITS)

        elif tok == "S_ENH":
            # 강화 특수스킬 지정 2구간
            # 계수 720% × 8 + 1600%
            c["s_enh"] = int(c["s_enh"]) + 1

        elif tok == "B4":
            if is_prima:
                c["b4_enhanced"] = int(c["b4_enhanced"]) + 1
            else:
                c["b4_norm"] = int(c["b4_norm"]) + 1

                # 일반 기본공격 히트 숨결 누적
                add_breath_hits(MELAN_BASIC_NORMAL_HITS)

    return c
_MELAN_FAST = _melan_precompute_fast()

# =====================================================
# 사이클 피해 계산
# =====================================================
def melan_cycle_damage_fast(stats: Dict[str, float], party: List[str]) -> Dict[str, float]:
    # 스킬별 독립 피해 계산

    promo_on   = (float(stats.get("_melan_promo", 0.0)) > 0.0)
    prima_mult = float(stats.get("promo_prima_dmg_mult", 1.0))

    c = _MELAN_FAST
    total_time = 30.0

    breakdown = {
        "basic": 0.0,
        "special": 0.0,
        "special_normal": 0.0,
        "enhanced_special_passive": 0.0,
        "ult": 0.0,
        "passive": 0.0,
        "proc": 0.0,
        "strike": 0.0,
        "unique": 0.0,
    }

    total_direct = 0.0

    # 비프리마 구간
    if int(c["s_norm"]):
        dmg = skill_damage_from_start(stats, MELAN_SPECIAL_NORMAL_COEFF, "special") * int(c["s_norm"])
        total_direct += dmg
        breakdown["special"] += dmg
        breakdown["special_normal"] += dmg

    if int(c["s_enh"]):
        # 강화 특수스킬 패시브 피해 분류
        # 패시브 피해·배율·받는 패시브 피해 축 적용
        dmg = skill_damage_from_start(stats, MELAN_SPECIAL_ENHANCED_COEFF, "passive", extra_skill_mult=prima_mult) * int(c["s_enh"])
        total_direct += dmg
        breakdown["passive"] += dmg
        breakdown["enhanced_special_passive"] += dmg

    if int(c["b4_norm"]):
        dmg = skill_damage_from_start(stats, MELAN_BASIC_NORMAL_SUM, "basic") * int(c["b4_norm"])
        total_direct += dmg
        breakdown["basic"] += dmg

    if int(c["u_norm"]):
        dmg = skill_damage_from_start(stats, MELAN_ULT_NORMAL_COEFF, "ult") * int(c["u_norm"])
        total_direct += dmg
        breakdown["ult"] += dmg

    if int(c["prelude"]):
        dmg = skill_damage_from_start(stats, MELAN_PRELUDE_COEFF, "ult") * int(c["prelude"])
        total_direct += dmg
        breakdown["ult"] += dmg

    # 프리마 진입
    if int(c["entry"]):
        dmg = skill_damage_from_start(stats, PRIMA_ENTRY_COEFF, "passive", extra_skill_mult=prima_mult) * int(c["entry"])
        total_direct += dmg
        breakdown["passive"] += dmg

    # 강화 특수스킬 이후 강화 기본공격 10회·패시브 피해
    # 강화 기본공격 계수 272.6%·272.6%·489.9%·543.3%+727.0%
    if int(c["b4_enhanced"]):
        dmg = skill_damage_from_start(stats, MELAN_BASIC_ENHANCED_SUM, "passive", extra_skill_mult=prima_mult) * int(c["b4_enhanced"])
        total_direct += dmg
        breakdown["passive"] += dmg

    # 브레스 티어 패시브(비프리마에서만)
    def tier_mult(tier: float) -> float:
        if not promo_on:
            return 1.0
        if tier == 0.25:
            return 1.0 + float(MELAN_PROMO_UNDEAD_EXTRA)
        if tier == 0.50:
            return 1.0 + float(MELAN_PROMO_NOVA_EXTRA)
        if tier == 0.75:
            return 2.0 if bool(MELAN_PROMO_APOCALYPSE_X2) else 1.0
        return 1.0

    # 브레스 티어 패시브(비프리마에서만)
    if int(c["tier_0p25"]):
        dmg = skill_damage_from_start(stats, PASSIVE_TIER_COEFF[0.25], "passive", extra_skill_mult=tier_mult(0.25)) * int(c["tier_0p25"])
        total_direct += dmg
        breakdown["passive"] += dmg

    if int(c["tier_0p50"]):
        dmg = skill_damage_from_start(stats, PASSIVE_TIER_COEFF[0.50], "passive", extra_skill_mult=tier_mult(0.50)) * int(c["tier_0p50"])
        total_direct += dmg
        breakdown["passive"] += dmg

    if int(c["tier_0p75"]):
        dmg = skill_damage_from_start(stats, PASSIVE_TIER_COEFF[0.75], "passive", extra_skill_mult=tier_mult(0.75)) * int(c["tier_0p75"])
        total_direct += dmg
        breakdown["passive"] += dmg

    # 설탕 세트 비프리마 강화 기본공격별 기대값
    if float(stats.get("sugar_set_enabled", 0.0)) > 0.0 and int(c["hits_pre_prima"]) > 0:
        proc = (
            skill_damage_from_start(stats, float(stats.get("sugar_set_proc_coeff", 0.0)), "none")
            * float(stats.get("sugar_set_proc_chance", 0.0))
            * int(c["hits_pre_prima"])
        )
        total_direct += proc
        breakdown["proc"] += proc

    # 광휘 설탕유리조각 추가피해
    sugar_proc = skill_damage_from_start(stats, float(stats.get("sugar_brilliance_coeff", 0.0)), "none") * int(c.get("u_norm", 0))
    if sugar_proc:
        total_direct += sugar_proc
        breakdown["proc"] += sugar_proc

    # 속성강타 + 유니크(초당 추가딜)
    strike = strike_total_from_direct(total_direct, "멜랑크림 쿠키", stats, party)
    breakdown["strike"] = strike

    unique_total = skill_damage_from_start(stats, float(stats.get("unique_extra_coeff", 0.0)), "none") * total_time
    breakdown["unique"] = unique_total

    total_damage = math.floor(total_direct + strike + unique_total)
    total_damage *= float(stats.get("elem_dmg_mult", 1.0))
    dps = total_damage / 30.0

    return {
        "total_damage": total_damage,
        "total_time": total_time,
        "dps": dps,
        "breakdown_basic": breakdown["basic"],
        "breakdown_special": breakdown["special"],
        # 일반특수스킬은 특수스킬 합계에만 포함
        # 강화 특수스킬 패시브 합계 전용
        "breakdown_ult": breakdown["ult"],
        "breakdown_passive": breakdown["passive"],
        "breakdown_proc": breakdown["proc"],
        "breakdown_strike": breakdown["strike"],
        "breakdown_unique": breakdown["unique"],
    }

# 허용 목록
# =====================================================
# 장비 및 후보
# =====================================================
def melan_allowed_equips() -> List[str]:
    return ["달콤한 설탕 깃털", "미지의 방랑자", "수상한 사냥꾼", "시간관리국의 제복"]

def melan_allowed_uniques() -> List[str]:
    return ["스타더스트 쿠키의 기억"]

def melan_allowed_artifacts() -> List[str]:
    return ["끝나지 않는 죽음의 밤"]

# 잠재력 후보: 치명타 확률 제외
@lru_cache(maxsize=None)
def melan_generate_potentials_common() -> List[Dict[str, int]]:
    """멜랑크림 쿠키 잠재력 후보"""
    return generate_damage_potential_candidates(fixed={"elem_atk": 2})

# 설탕유리조각 후보: 치명타 확률 제외
# - 탐색: 치명타 피해·모든 속성 피해·공격력·패시브 피해
# - 자동: 치명타 확률 100% 우선 배정
# - 자동: 잔여 칸 속성 공격력 배정
# - 제외: 기본·특수·궁극기 피해

# 최적화: 치명타 확률 자동 배정
# =====================================================
# 최적화
# =====================================================
def optimize_melan_cycle(
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
    """멜랑크림 쿠키 최적화"""
    del step  # 장비별 조각 최적화는 항상 1칸 단위로 수행

    cookie = '멜랑크림 쿠키'
    base = BASE_STATS_MELAN[cookie].copy()
    equips = _resolve_equip_list_override(equip_override, melan_allowed_equips())
    uniques = _resolve_unique_list_override(unique_override, melan_allowed_uniques())
    potentials = [dict(potential_override)] if potential_override is not None else melan_generate_potentials_common()
    artifacts = melan_allowed_artifacts()
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
                            return melan_cycle_damage_fast(stats, party)

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
