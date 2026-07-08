# =====================================================
# Imports
# =====================================================
from .common import *
from .common import _resolve_unique_list_override

# =====================================================
# 샬롯맛 쿠키: 회복량 최적화, 이벤트 횟수 기반 계산
# 궁 즉시회복 1회 (56%)
# 매듭 7회 (11.2%)
# 승급(영혼꿰기) 1회 (10%)
# 매듭 3회 (11.2%)
# 승급(영혼꿰기) 2회 (10%)
# => 매듭 총 10회, 영혼꿰기 총 3회
# =====================================================

# =====================================================
# Constants
# =====================================================
CHARLOTTE_FIXED_UNIQUE   = "크러쉬드페퍼맛 쿠키의 기억"
CHARLOTTE_FIXED_EQUIP    = "영원의 대마술사"
CHARLOTTE_FIXED_ARTIFACT = "희미한 날갯짓"
CHARLOTTE_WEAPON_ATK_PCT = 0.52
CHARLOTTE_WEAPON_BUFF_AMP = 0.24

# 잠재 고정
CHARLOTTE_FIXED_POT = {
    "elem_atk": 2,
    "atk_pct": 2,
    "buff_amp": 4,
    "crit_rate": 0,
    "crit_dmg": 0,
    "armor_pen": 0,
    "debuff_amp": 0,
}

BASE_STATS_CHARLOTTE = {
    "샬롯맛 쿠키": {
        "atk": 616.0,
        "friendship_atk": friendship_atk_for("샬롯맛 쿠키"),
        "elem_atk": 0.0,
        # 전용무기 기본 옵션 공격력 +52%
        "atk_pct": CHARLOTTE_WEAPON_ATK_PCT,
        "crit_rate": 0.15,
        "crit_dmg": 1.5,
        "armor_pen": 0.0,
        "final_dmg": 0.04,
        # 기본 버프 증폭 15% + 전용무기 버프 증폭 24%
        "buff_amp": 0.15 + CHARLOTTE_WEAPON_BUFF_AMP,
        "debuff_amp": 0.0,
    }
}

# -----------------------------
# 로테이션 토큰
# -----------------------------

CHAR_CYCLE_TOKENS = [
    "U", "S",
    "C", "C", "C", "C",
    "S",
    "C", "C", "C", "C",
    "S",
    "C", "C", "C", "C",
    "S",
    "C", "C",
]

# -----------------------------
# 스킬 계수(딜 계산용)
# -----------------------------
CHAR_BASIC_1 = 2.016  # 기본공격 1타 피해 계수
CHAR_BASIC_2 = 2.215  # 기본공격 2타 피해 계수
CHAR_CHARGE  = (2.13 + 2.556 + 2.84)      # 차지 공격 피해 계수 = 7.526
CHAR_DASH    = 0.25  # 대시 피해 계수
CHAR_SPECIAL = 5.68  # 특수스킬 피해 계수
CHAR_ULT     = (4.26 * 7.0) + 16.33       # 궁극기 피해 계수 = 46.15

# 패시브(딜) 근사(기존 근사 유지)
CHAR_PASSIVE_TRIGGER_INTERVAL = 1.0  # 패시브 발동 간격
CHAR_PASSIVE_PER_TRIGGER      = (2.0 * 3.55) + (9.94 / 3.0)  # 패시브 1회 발동 피해 계수 = 10.413
CHAR_PASSIVE_COEFF_PER_SEC    = CHAR_PASSIVE_PER_TRIGGER / CHAR_PASSIVE_TRIGGER_INTERVAL  # 패시브 초당 피해 계수 = 10.413/s

# -----------------------------
# 아티팩트(희미한 날갯짓) 최소 반영
# -----------------------------
CHAR_ARTI_VOID_PASSIVE_MULT = 1.20   # 공허: 패시브 피해 +20%
CHAR_ARTI_LOSS_PASSIVE_MULT = 1.10   # 유실: 패시브 피해 +10%
CHAR_ARTI_REPOSE_ELEM_ADD   = 0.25   # 진혼: 모든 속성피해 +25% (가산 축)

# 진혼 buff_all_elem_dmg_raw(가산)
CHARLOTTE_APPLY_ELEM_MULT_IN_DAMAGE = False

# =====================================================
# Helpers - 회복 이벤트/아티 반영
# =====================================================
def charlotte_heal_event_counts() -> Dict[str, int]:
    knot_cnt = int(CHAR_KNOT_COUNT_1) + int(CHAR_KNOT_COUNT_2)   # 10
    soul_cnt = int(CHAR_SOUL_COUNT_1) + int(CHAR_SOUL_COUNT_2)   # 3
    return {
        "main_cnt": int(CHAR_HEAL_MAIN_COUNT),
        "knot_cnt": knot_cnt,
        "soul_cnt": soul_cnt,
    }

# -----------------------------
# 승급 최소 반영 토글(딜 계산 전용)
# - 힐은 "횟수 고정"이라 promo 레벨/온오프 개념이 필요없음
# -----------------------------
CHARLOTTE_PROMO_ENABLED = True

# 패시브 스킬 피해 +100% => 패시브 항목에 ×2.0
CHAR_PROMO_PASSIVE_DMG_MULT = 2.0

# -----------------------------
# 회복 규칙: 이벤트 횟수 기반
# -----------------------------
CHAR_HEAL_MAIN_RATIO = 0.56     # 궁 즉시 HP 회복
CHAR_HEAL_KNOT_RATIO = 0.112    # 궁 매듭 HP 회복
CHAR_SOUL_HEAL_RATIO = 0.10     # 승급(영혼꿰기) HP 회복

# 성급 효과: 궁극기 회복량 +20%
# - 적용 대상: 궁극기 회복에 포함되는 즉시 HP 회복, 매듭 HP 회복
# - 미적용 대상: 승급(영혼꿰기) 회복
CHAR_ULT_HEAL_PROMO_MULT = 1.20

# 사이클 내 발생 횟수(고정)
CHAR_HEAL_MAIN_COUNT = 1        # 궁 1번
CHAR_KNOT_COUNT_1    = 7        # 매듭 7번
CHAR_SOUL_COUNT_1    = 1        # 승급(영혼꿰기) 1번
CHAR_KNOT_COUNT_2    = 3        # 매듭 3번
CHAR_SOUL_COUNT_2    = 2        # 승급(영혼꿰기) 2번

# -----------------------------
# 유틸 함수
# -----------------------------
# =====================================================
# Calculation - 시간/회복/딜
# =====================================================
def charlotte_cycle_total_time() -> float:
    return 30.0

def charlotte_calc_final_atk(stats: Dict[str, float]) -> float:
    return calc_attack_value(stats, floor_result=False)

def charlotte_calc_heal_per_cycle(stats: Dict[str, float]) -> Dict[str, float]:
    """
    1사이클 총 회복량(이벤트 기반, 횟수 고정)
    - 궁 즉시 HP 회복: 0.56 * 1회 * 1.20
    - 궁 매듭 HP 회복: 0.112 * 10회 * 1.20
    - 승급(영혼꿰기): 0.10 * 3회
    - heal_pct(회복량%) 적용
    """
    total_time = charlotte_cycle_total_time()
    final_atk  = charlotte_calc_final_atk(stats)

    counts = charlotte_heal_event_counts()
    main_cnt = int(counts["main_cnt"])
    knot_cnt = int(counts["knot_cnt"])
    soul_cnt = int(counts["soul_cnt"])

    heal_mult = 1.0 + float(stats.get("heal_pct", 0.0))

    ult_heal_mult = float(CHAR_ULT_HEAL_PROMO_MULT)

    # 성급 효과 "궁극기 회복량 +20%"는 궁극기 회복에 속한
    # 즉시 HP 회복과 매듭 HP 회복에만 적용한다.
    heal_main = final_atk * CHAR_HEAL_MAIN_RATIO * main_cnt * heal_mult * ult_heal_mult
    heal_knot = final_atk * CHAR_HEAL_KNOT_RATIO * knot_cnt * heal_mult * ult_heal_mult
    heal_soul = final_atk * CHAR_SOUL_HEAL_RATIO * soul_cnt * heal_mult

    total_heal = heal_main + heal_knot + heal_soul
    hps        = total_heal / total_time if total_time > 0 else 0.0

    return {
        "total_time": total_time,
        "final_atk": final_atk,
        "heal_main": heal_main,
        "heal_knot": heal_knot,
        "heal_soul": heal_soul,
        "total_heal": total_heal,
        "hps": hps,
        "main_cnt": main_cnt,
        "knot_cnt": knot_cnt,
        "soul_trig_cnt": soul_cnt,
        "ult_heal_mult": ult_heal_mult,
    }

# -----------------------------
# 사이클 딜 계산
# -----------------------------
def charlotte_cycle_damage(stats: Dict[str, float], party: List[str]) -> Dict[str, float]:
    total_time = charlotte_cycle_total_time()
    promo_on = bool(stats.get("_char_promo_on", 0.0)) and bool(CHARLOTTE_PROMO_ENABLED)

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
    }

    b_toggle = 0
    for tok in CHAR_CYCLE_TOKENS:
        if tok == "B":
            b_toggle ^= 1
            coeff = CHAR_BASIC_1 if b_toggle == 1 else CHAR_BASIC_2
            dmg = skill_damage_from_start(stats, coeff, "basic")
            direct += dmg
            breakdown["basic"] += dmg

        elif tok == "C":
            dmg = skill_damage_from_start(stats, CHAR_CHARGE, "basic")
            direct += dmg
            breakdown["charge"] += dmg
            breakdown["basic"] += dmg

        elif tok == "D":
            dmg = skill_damage_from_start(stats, CHAR_DASH, "basic")
            direct += dmg
            breakdown["dash"] += dmg
            breakdown["basic"] += dmg

        elif tok == "S":
            dmg = skill_damage_from_start(stats, CHAR_SPECIAL, "special")
            direct += dmg
            breakdown["special"] += dmg

        elif tok == "U":
            dmg = skill_damage_from_start(stats, CHAR_ULT, "ult")
            direct += dmg
            breakdown["ult"] += dmg

    # 패시브: 아티팩트(공허/유실) 배율 + (승급) 패시브 피해 +100%
    passive_mult = float(stats.get("passive_dmg_mult", 1.0))
    if promo_on:
        passive_mult *= float(CHAR_PROMO_PASSIVE_DMG_MULT)

    passive_total = skill_damage_from_start(stats, (CHAR_PASSIVE_COEFF_PER_SEC * total_time), "passive", extra_skill_mult=passive_mult)
    breakdown["passive"] = passive_total

    strike = strike_total_from_direct(direct, "샬롯맛 쿠키", stats, party)  # <-- 외부 함수
    breakdown["strike"] = strike

    unique_total = skill_damage_from_start(stats, float(stats.get("unique_extra_coeff", 0.0)), "none") * total_time
    breakdown["unique"] = unique_total

    total_damage = math.floor(direct + passive_total + strike + unique_total)

    if CHARLOTTE_APPLY_ELEM_MULT_IN_DAMAGE:
        total_damage *= float(stats.get("elem_dmg_mult", 1.0))

    dps = total_damage / 30.0

    return {
        "total_damage": total_damage,
        "total_time": total_time,
        "dps": dps,
        "breakdown_basic": breakdown["basic"],
        "breakdown_special": breakdown["special"],
        "breakdown_ult": breakdown["ult"],
        "breakdown_charge": breakdown["charge"],
        "breakdown_passive": breakdown["passive"],
        "breakdown_strike": breakdown["strike"],
        "breakdown_unique": breakdown["unique"],
        "promo_on": promo_on,
    }

# -----------------------------
# 최적화 루프
# -----------------------------
# =====================================================
# Calculation - 최적화
# =====================================================
def optimize_char_cycle(
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
    cookie = "샬롯맛 쿠키"
    base   = BASE_STATS_CHARLOTTE[cookie].copy()

    equip_name    = CHARLOTTE_FIXED_EQUIP
    artifact_name = CHARLOTTE_FIXED_ARTIFACT
    pot           = CHARLOTTE_FIXED_POT
    uniques = _resolve_unique_list_override(unique_override, [CHARLOTTE_FIXED_UNIQUE])
    unique_name = uniques[0] if uniques else CHARLOTTE_FIXED_UNIQUE

    if isinstance(equip_override, str) and equip_override.strip():
        equip_name = equip_override.strip()

    # seaz 허용 교정(있으면)
    fn_seaz = globals().get("char_allowed_seaz", None) or globals().get("charlotte_allowed_seaz", None)
    if callable(fn_seaz):
        allowed = fn_seaz() or []
        if allowed and (seaz_name not in allowed):
            seaz_name = allowed[0]

    NS = int(globals().get("NORMAL_SLOTS", 0) or 0)
    shard_inc = globals().get("SHARD_INC", None)
    if not isinstance(shard_inc, dict):
        raise RuntimeError("SHARD_INC 가 dict로 정의되어 있어야 합니다.")
    if NS <= 0:
        raise RuntimeError("NORMAL_SLOTS 가 1 이상으로 정의되어 있어야 합니다.")

    shard_candidates: List[Dict[str, int]] = []
    for ea in range(NS + 1):
        for ap in range(NS - ea + 1):
            hp = NS - ea - ap
            shard_candidates.append({"elem_atk": ea, "atk_pct": ap, "heal_pct": hp})

    total = max(1, len(shard_candidates))
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

    zero_shards = {k: 0 for k in shard_inc.keys()}

    template = build_stats_for_combo(  # <-- 외부 함수
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

    # 딜쪽 승급 토글(패시브 +100% 같은 최소 반영이 필요하면 사용)
    template["_char_promo_on"] = 1.0 if CHARLOTTE_PROMO_ENABLED else 0.0

    if not is_valid_by_caps(template):  # <-- 외부 함수
        emit(1.0)
        return None

    ea_inc = float(shard_inc.get("elem_atk", 0.0))
    ap_inc = float(shard_inc.get("atk_pct", 0.0))
    hp_inc = float(shard_inc.get("heal_pct", 0.0))

    done = 0
    for sh in shard_candidates:
        done += 1
        if (done % tick) == 0:
            emit(done / total)

        stats = dict(template)

        stats["elem_atk"] = float(stats.get("elem_atk", 0.0)) + ea_inc * int(sh.get("elem_atk", 0))
        stats["atk_pct"]  = float(stats.get("atk_pct", 0.0))  + ap_inc * int(sh.get("atk_pct", 0))
        stats["heal_pct"] = float(stats.get("heal_pct", 0.0)) + hp_inc * int(sh.get("heal_pct", 0))

        # template cap 검사를 이미 통과했고 설탕유리조각은 방어관통을 올리지 않으므로 재검사 생략

        heal  = charlotte_calc_heal_per_cycle(stats)
        cycle = charlotte_cycle_damage(stats, party)

        cur = {
            "cookie": cookie,
            "dps": float(cycle["dps"]),
            "cycle_total_damage": float(cycle["total_damage"]),
            "cycle_total_time": 30.0,
            "cycle_breakdown": cycle,

            "max_heal": float(heal["total_heal"]),
            "hps": float(heal["hps"]),
            "heal_detail": heal,

            "equip": equip_name,
            "seaz": seaz_name,
            "unique": unique_name,
            "artifact": artifact_name,
            "potentials": pot,

            "shards": {
                "elem_atk": int(sh.get("elem_atk", 0)),
                "atk_pct": int(sh.get("atk_pct", 0)),
                "heal_pct": int(sh.get("heal_pct", 0)),
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
            if cur["max_heal"] > best["max_heal"] + 1e-9:
                best = cur
            elif abs(cur["max_heal"] - best["max_heal"]) <= 1e-9 and cur["dps"] > best["dps"]:
                best = cur

    emit(1.0)
    return best
