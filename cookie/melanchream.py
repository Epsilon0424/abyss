# =====================================================
# Imports
# =====================================================
from .common import *
from .common import _resolve_equip_list_override, _min_crit_slots_needed_for_crit100_generic, _resolve_unique_list_override
from functools import lru_cache

# =====================================================
# 멜랑크림: 치확 100% 고정, 설유 치확 자동 배정, 고속 사이클 계산
# =====================================================

# -----------------------------
# 승급, 플래그, 기본 스탯
# -----------------------------
# =====================================================
# Constants
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
MELAN_FORCE_CRIT_100 = True
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

# -----------------------------
# 사이클과 계수
# -----------------------------
MELAN_BASIC_NORMAL = [1.704, 1.704, 3.067, 3.408 + 4.544]  # 일반 기본공격 4타 계수
MELAN_BASIC_ENHANCED = [2.726, 2.726, 4.899, 5.433 + 7.270]  # 강화 기본공격 4타 계수: 272.6%, 272.6%, 489.9%, 543.3%+727.0%

MELAN_SPECIAL_NORMAL_COEFF = (4.26 * 5) + 10.65   # 일반 특수스킬 계수: 426% x 5 + 피니시 1065%
MELAN_SPECIAL_ENHANCED_COEFF = (7.20 * 8) + 16.00 # 강화 특수스킬 계수: 720% x 8 + 1600%
MELAN_ULT_NORMAL_COEFF     = (7.81 * 6) + 35.50  # 일반 궁극기 계수

PASSIVE_TIER_COEFF = {  # 숨결 누적 패시브 티어별 피해 계수
    0.25: 6.816,
    0.50: 7.952,
    0.75: 11.36 * 2,
}

PRIMA_ENTRY_COEFF = 11.36  # 프리마 진입 피해 계수
BREATH_GAIN_PER_BASIC_HIT = 0.05

# 숨결 누적용 히트 수
# - 두 번째 궁극기(프리마 진입) 전까지의 일반 궁극기 / 일반 기본공격 / 일반 특수 타격으로 숨결 누적
# - U(781% x 6 + 3550%) = 7히트
# - B4(4타 구성) = 4히트
# - S(426% x 5 + 1065%) = 6히트
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

# -----------------------------
# 고속 계산용 사이클 횟수와 총시간을 미리 계산
# -----------------------------
# =====================================================
# Helpers - 고속 이벤트 전처리
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
        """프리마 전 숨결 누적
        - 기존: 일반 B4 히트만 숨결 누적
        - 수정: 첫 번째 궁극기 U, 일반 B4, 일반 특수 S 히트까지 숨결 누적
        - 결과: 두 번째 궁극기 전 25% / 50% / 75% 티어가 모두 1회 발동
        """
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
            # 일반특: 426% x 5 + 피니시 1065%
            # 프리마 상태 여부와 관계없이 S 토큰은 일반특으로 계산
            c["s_norm"] = int(c["s_norm"]) + 1

            if not is_prima:
                # 일반 특수스킬 히트도 숨결 누적에 포함
                add_breath_hits(MELAN_SPECIAL_NORMAL_HITS)

        elif tok == "S_ENH":
            # 강화특: 지정된 두 구간의 S만 강화특으로 계산
            # 계수 = 720% x 8 + 1600%
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
# Calculation - 사이클 딜
# =====================================================
def melan_cycle_damage_fast(stats: Dict[str, float], party: List[str]) -> Dict[str, float]:
    # 스킬별 처음부터 계산: skill_damage_from_start 사용

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
        # 강화특수스킬은 이름은 특수지만 피해 분류는 패시브 피해
        # special_dmg가 아니라 passive_dmg / passive_dmg_mult / enemy_passive_taken_inc 축 적용
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

    # 강화특수스킬 뒤 B4 10회는 전부 강화평(패시브 피해 취급)
    # 강화평 계수 = 272.6%, 272.6%, 489.9%, 543.3%+727.0%
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

    # 설탕 세트 발동 기대값은 비프리마 B4 타격마다 계산
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
        # 강화특수스킬은 패시브 피해이므로 패시브 합계에만 포함
        "breakdown_ult": breakdown["ult"],
        "breakdown_passive": breakdown["passive"],
        "breakdown_proc": breakdown["proc"],
        "breakdown_strike": breakdown["strike"],
        "breakdown_unique": breakdown["unique"],
    }

# -----------------------------
# 허용 목록
# -----------------------------
# =====================================================
# Helpers - 장비/후보 생성
# =====================================================
def melan_allowed_equips() -> List[str]:
    return ["달콤한 설탕 깃털", "미지의 방랑자", "수상한 사냥꾼", "시간관리국의 제복"]

def melan_allowed_uniques() -> List[str]:
    return ["스타더스트 쿠키의 기억"]

def melan_allowed_artifacts() -> List[str]:
    return ["끝나지 않는 죽음의 밤"]

# -----------------------------
# 잠재 후보: crit_rate 축 제외
# -----------------------------
@lru_cache(maxsize=None)
def melan_generate_potentials_common() -> List[Dict[str, int]]:
    """
    - 총 8칸, elem_atk 2칸 고정(FREE=6)
    - 치확 100% 강제 → crit_rate 축 제거
    """
    total = 8
    fixed_elem = 2
    free = total - fixed_elem

    keys = ["atk_pct", "crit_dmg", "armor_pen"]
    cap = {"armor_pen": min(4, free)}

    out: List[Dict[str, int]] = []

    def dfs(i: int, remain: int, cur: Dict[str, int]) -> None:
        if i == len(keys):
            if remain == 0:
                p = dict(cur)
                p["elem_atk"] = fixed_elem
                p["buff_amp"] = 0
                p["debuff_amp"] = 0
                p["crit_rate"] = 0  # 안전한 스키마 유지
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

# -----------------------------
# 설유 후보: crit_rate 축 제외
# - 탐색: (crit_dmg / all_elem_dmg / atk_pct / passive_dmg)
# - 자동: crit_rate는 필요한 만큼 배정해서 100% 맞춤
# - 자동: 남는 슬롯은 elem_atk로 채움
# - 제외: basic_dmg / special_dmg / ult_dmg
# -----------------------------
@lru_cache(maxsize=None)
def melan_generate_shard_candidates_no_cr(step: int = 7) -> List[Dict[str, int]]:
    steps = list(range(0, NORMAL_SLOTS + 1, step))
    if steps[-1] != NORMAL_SLOTS:
        steps.append(NORMAL_SLOTS)

    out: List[Dict[str, int]] = []
    for cd in steps:
        for ae in steps:
            for ap in steps:
                for pd in steps:
                    used = cd + ae + ap + pd
                    if used > NORMAL_SLOTS:
                        continue
                    out.append({
                        "crit_dmg": cd,
                        "all_elem_dmg": ae,
                        "atk_pct": ap,
                        "passive_dmg": pd,
                        # 탐색에서 제외된 피해 종류는 결과 표 구조를 위해 0으로 유지
                        "basic_dmg": 0,
                        "special_dmg": 0,
                        "ult_dmg": 0,
                    })
    return out

# -----------------------------
# 최적화: crit_rate 자동 배정
# -----------------------------
# =====================================================
# Calculation - 최적화
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
) -> Optional[dict]:

    cookie = "멜랑크림 쿠키"
    base = BASE_STATS_MELAN[cookie].copy()

    equips = _resolve_equip_list_override(equip_override, melan_allowed_equips())
    uniques = _resolve_unique_list_override(unique_override, melan_allowed_uniques())
    potentials = melan_generate_potentials_common()
    artifacts = melan_allowed_artifacts()

    shard_candidates = melan_generate_shard_candidates_no_cr(step=step)

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
    eps = 1e-12

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

                    if not is_valid_by_caps(template):
                        done += len(shard_candidates)
                        if (done % tick) == 0:
                            emit(done / total)
                        continue

                    # 치확 100% 강제면, "이미 100% 초과"는 줄일 방법이 없다고 보고 스킵(기존 의도 유지)
                    if MELAN_FORCE_CRIT_100:
                        promo = float(template.get("promo_crit_rate_mult", 1.0))
                        buff_cr = float(template.get("buff_crit_rate_raw", 0.0))
                        base_cr = float(template.get("crit_rate", 0.0))
                        eff_cr = base_cr * promo + buff_cr
                        if eff_cr > 1.0 + eps:
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
                    else:
                        req_cr_slots = 0

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

                        if MELAN_FORCE_CRIT_100 and req_cr_slots and cr_inc:
                            stats["crit_rate"] = float(stats.get("crit_rate", 0.0)) + cr_inc * req_cr_slots

                        if ea_slots and ea_inc:
                            stats["elem_atk"] = float(stats.get("elem_atk", 0.0)) + ea_inc * int(ea_slots)

                        # 설탕유리조각은 방어관통을 올리지 않으므로 template 단계의 cap 검사 결과를 그대로 사용한다.
                        # 치확 100% 조건은 req_cr_slots 계산으로 이미 맞춘 상태다.

                        cycle = melan_cycle_damage_fast(stats, party)
                        dps = cycle["dps"]

                        if (best is None) or (dps > best["dps"]):
                            shards_out = dict(sh_base)
                            shards_out["crit_rate"] = int(req_cr_slots)
                            shards_out["elem_atk"] = int(ea_slots)

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
