# =====================================================
# 가져오기
# =====================================================
from .common import *
from .common import _resolve_unique_list_override

# =====================================================
# 산초맛 쿠키
# =====================================================
# 회복 최적화: 이벤트 횟수 기준
# 회복 이벤트: 궁 1회·매듭 10회·영혼꿰기 3회

# =====================================================
# 상수
# =====================================================
SANCHO_FIXED_UNIQUE   = "멜랑크림 쿠키의 순수한 기억"
SANCHO_FIXED_EQUIP    = "영원의 대마술사"
SANCHO_FIXED_ARTIFACT = "진실을 찾아서"
SANCHO_WEAPON_ATK_PCT = 0.52
SANCHO_WEAPON_BUFF_AMP = 0.24

# 잠재 고정
SANCHO_FIXED_POT = {
    "elem_atk": 2,
    "atk_pct": 2,
    "buff_amp": 4,
    "crit_rate": 0,
    "crit_dmg": 0,
    "armor_pen": 0,
    "debuff_amp": 0,
}

BASE_STATS_SANCHO = {
    "산초맛 쿠키": {
        "atk": 556.0,
        "friendship_atk": friendship_atk_for("산초맛 쿠키"),
        "elem_atk": 0.0,
        # 전용무기 기본 옵션 공격력 +52%
        "atk_pct": SANCHO_WEAPON_ATK_PCT,
        "crit_rate": 0.15,
        "crit_dmg": 1.5,
        "armor_pen": 0.0,
        "final_dmg": 0.04,
        # 기본 버프 증폭 15% + 전용무기 버프 증폭 24%
        "buff_amp": 0.15 + SANCHO_WEAPON_BUFF_AMP,
        "debuff_amp": 0.0,
        "healing": 0.2,
    }
}

SANCHO_POTENTIALS_FIXED = {
    "elem_atk": 2,
    "atk_pct": 2,
    "buff_amp": 4,
    "crit_rate": 0,
    "crit_dmg": 0,
    "armor_pen": 0,
    "debuff_amp": 0,
}

# =====================================================
# 로테이션 토큰
# =====================================================

SANCHO_CYCLE_TOKENS = [
    "U", "ES", "S"
    "B1", "B2", "B3",
    "B1", "B2", "B3",
    "H", "H", "H", "H", "H", "H", "H", "H", 
    "S",
    "H", "H", "H", "H", 
    "B1", "B2", "B3",
    "B1", "B2", "B3",
    "B1", "B2",
    "S",
    "H","H","H","H","H","H",
]

# =====================================================
# 스킬 계수
# =====================================================

SANCHO_BASIC_1 = 3.55
SANCHO_BASIC_2 = 3.97
SANCHO_BASIC_3 = 5.112
SANCHO_SPECIAL = (8.52 * 2.0)
SANCHO_ESPECIAL = (21.30 + 25.56)
SANCHO_ULT = (1.42 * 15.0) + 28.4
SANCHO_CHARGE = 0
SANCHO_CHARGE_HEAL_RATIO = 0.081
SANCHO_PASSIVE_TRIGGER_INTERVAL = 4.0



# =====================================================
# 회복 이벤트 및 아티팩트 반영
# =====================================================

# 승급 최소 반영 토글(딜 계산 전용)
# - 회복 횟수 고정
SANCHO_PROMO_ENABLED = True

# =====================================================
# 유틸 함수
# =====================================================
# 시간·회복·피해 계산
# =====================================================
def sancho_cycle_total_time() -> float:
    return 30.0

def sancho_calc_final_atk(stats: Dict[str, float]) -> float:
    return calc_attack_value(stats, floor_result=False)

def sancho_calc_support_metrics(stats: Dict[str, float]) -> Dict[str, float]:
    total_time = sancho_cycle_total_time()
    final_atk = sancho_calc_final_atk(stats)
    heal_mult = 1.0 + float(stats.get("heal_pct", 0.0))

    hold_cnt = sum(1 for t in SANCHO_CYCLE_TOKENS if t == "S")
    heal_hold = final_atk * SANCHO_CHARGE_HEAL_RATIO * hold_cnt * heal_mult
    hps = heal_hold / total_time if total_time > 0 else 0.0
    return {
        "total_time": total_time,
        "final_atk": final_atk,
        "total_heal": heal_hold,
        "hps": hps,
        "main_cnt": hold_cnt,
    }

# =====================================================
# 사이클 피해 계산
# =====================================================

def sancho_cycle_damage(stats: Dict[str, float], party: List[str]) -> Dict[str, float]:
    total_time = sancho_cycle_total_time()

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
    for tok in SANCHO_CYCLE_TOKENS:
        if tok == "B1":
            b_toggle ^= 1
            coeff = SANCHO_BASIC_1 if b_toggle == 1 else SANCHO_BASIC_2
            dmg = skill_damage_from_start(stats, coeff, "basic")
            direct += dmg
            breakdown["basic"] += dmg

        if tok == "B2":
            b_toggle ^= 1
            coeff = SANCHO_BASIC_2 if b_toggle == 2 else SANCHO_BASIC_3
            dmg = skill_damage_from_start(stats, coeff, "basic")
            direct += dmg
            breakdown["basic"] += dmg

        if tok == "B3":
            b_toggle ^= 1
            coeff = SANCHO_BASIC_3
            dmg = skill_damage_from_start(stats, coeff, "basic")
            direct += dmg
            breakdown["basic"] += dmg

        elif tok == "S":
            dmg = skill_damage_from_start(stats, SANCHO_SPECIAL, "special")
            direct += dmg
            breakdown["special"] += dmg

        elif tok == "ES":
            dmg = skill_damage_from_start(stats, SANCHO_ESPECIAL, "special")
            direct += dmg
            breakdown["special"] += dmg

        elif tok == "U":
            dmg = skill_damage_from_start(stats, SANCHO_ULT, "ult")
            direct += dmg
            breakdown["ult"] += dmg

        if tok == "H":
            b_toggle ^= 1
            coeff = SANCHO_CHARGE
            dmg = skill_damage_from_start(stats, coeff, "basic")
            direct += dmg
            breakdown["basic"] += dmg

    strike = strike_total_from_direct(direct, "산초맛 쿠키", stats, party)  # <-- 외부 함수
    breakdown["strike"] = strike

    unique_total = skill_damage_from_start(stats, float(stats.get("unique_extra_coeff", 0.0)), "none") * total_time
    breakdown["unique"] = unique_total

    total_damage = math.floor(direct + strike + unique_total)

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
    }

# 최적화 루프
# =====================================================
# 최적화
# =====================================================
def optimize_sancho_cycle(
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
    cookie = "산초맛 쿠키"
    base   = BASE_STATS_SANCHO[cookie].copy()

    equip_name    = SANCHO_FIXED_EQUIP
    artifact_name = SANCHO_FIXED_ARTIFACT
    pot           = dict(potential_override) if potential_override is not None else dict(SANCHO_FIXED_POT)
    uniques = _resolve_unique_list_override(unique_override, [SANCHO_FIXED_UNIQUE])
    unique_name = uniques[0] if uniques else SANCHO_FIXED_UNIQUE

    if isinstance(equip_override, str) and equip_override.strip():
        equip_name = equip_override.strip()

    # 시즈 허용 목록 교정
    fn_seaz = globals().get("sancho_allowed_seaz", None) or globals().get("sancho_allowed_seaz", None)
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
            # 진행률 콜백 오류 무시
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

    def sancho_calc_heal_per_cycle(stats: Dict[str, float]) -> Dict[str, float]:
        """산초맛 쿠키 사이클 회복량"""
        total_time = sancho_cycle_total_time()
        final_atk  = sancho_calc_final_atk(stats)

        heal_mult = 1.0 + float(stats.get("heal_pct", 0.0))

        # 성급 효과 "궁극기 회복량 +20%"는 궁극기 회복에 속한
        # 즉시 회복·매듭 회복 전용
        hold_cnt = sum(1 for t in SANCHO_CYCLE_TOKENS if t == "S")    
        heal_hold = final_atk * SANCHO_CHARGE_HEAL_RATIO * hold_cnt * heal_mult

        total_heal = heal_hold
        hps        = total_heal / total_time if total_time > 0 else 0.0

        return {
            "total_time": total_time,
            "final_atk": final_atk,
            "heal_hold": heal_hold,
            "total_heal": heal_hold,
            "hps": hps,
            "main_cnt": hold_cnt,
    }


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

        # 설탕유리조각 방어 관통 상한 재검사 생략

        heal  = sancho_calc_heal_per_cycle(stats)
        cycle = sancho_cycle_damage(stats, party)
        support = sancho_calc_support_metrics(stats)

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
