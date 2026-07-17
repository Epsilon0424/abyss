# =====================================================
# Imports
# =====================================================
from .common import *
from .common import _resolve_unique_list_override
from functools import lru_cache

# 네온데니쉬맛 쿠키: 서포터, 보호막 우선 최적화
# =====================================================

# =====================================================
# Constants
# =====================================================
NEON_FIXED_UNIQUE   = "멜랑크림 쿠키의 순수한 기억"
NEON_FIXED_ARTIFACT = "치트키 발견?"
NEON_FIXED_EQUIP    = "영원의 대마술사"
FIXED_SEAZ_NEON     = "허브그린드:작은 성배"
NEON_WEAPON_ATK_PCT = 0.52
NEON_WEAPON_BUFF_AMP = 0.24

BASE_STATS_NEON = {
    "네온데니쉬맛 쿠키": {
        "atk": 558.0,
        "friendship_atk": friendship_atk_for("네온데니쉬맛 쿠키"),
        "elem_atk": 0.0,
        # 전용무기 기본 옵션 공격력 +52%
        "atk_pct": NEON_WEAPON_ATK_PCT,
        "crit_rate": 0.15,
        "crit_dmg": 1.50,
        "armor_pen": 0.0,
        "final_dmg": 0.04,
        # 기본 버프 증폭 15% + 전용무기 버프 증폭 24%
        "buff_amp": 0.15 + NEON_WEAPON_BUFF_AMP,
        "debuff_amp": 0.0,
        "hp": 4848.0,
        "def": 395.0,
    }
}

NEON_POTENTIALS_FIXED = {
    "elem_atk": 2,
    "atk_pct": 2,
    "buff_amp": 4,
    "crit_rate": 0,
    "crit_dmg": 0,
    "armor_pen": 0,
    "debuff_amp": 0,
}

NEON_CYCLE_TOKENS = (
    ["U"] +
    ["S"] + ["B4"] * 5 +
    ["S"] + ["B4"] * 5 +
    ["S"] + ["B4"] * 3 + ["S"]
)

NEON_BASIC_COEFF = 4.97 + 4.97 + 5.396 + 6.106  # 기본공격 4타 합산 계수
NEON_SPECIAL_COEFF = 0.0  # 특수스킬은 회복/보조 스킬이라 피해 계수 0 처리
NEON_ULT_COEFF = 35.50  # 궁극기 피해 계수

NEON_SPECIAL_HEAL_RATIO = 0.504  # 특수스킬 회복 계수
NEON_BARRIER_HP_RATIO = 4.0  # 보호막 HP 계수
NEON_BARRIER_PROMO_MULT = 1.20
NEON_BARRIER_CAP = 12000.0
NEON_PATCH_ATK_BUFF = 0.346
NEON_PATCH_ULT_DMG = 0.15  # 패치/버프 궁극기 피해 증가
NEON_CHEAT_TAKEN_ULT = 0.08
NEON_FATAL_ERROR_ULT = 0.058

# =====================================================
# Helpers - 장비/후보 생성
# =====================================================

def neon_allowed_seaz() -> List[str]:
    return [x for x in SEAZNITES.keys() if str(x).startswith("허브그린드:") or str(x).startswith("민트쿼츠:")]

@lru_cache(maxsize=None)
def neon_generate_shard_candidates(step: int = 1) -> List[Dict[str, int]]:
    steps = list(range(0, NORMAL_SLOTS + 1, max(1, int(step))))
    if steps[-1] != NORMAL_SLOTS:
        steps.append(NORMAL_SLOTS)
    out: List[Dict[str, int]] = []
    seen = set()
    for ea in steps:
        for ap in steps:
            if ea + ap > NORMAL_SLOTS:
                continue
            remain1 = NORMAL_SLOTS - ea - ap
            for hp in steps:
                if hp > remain1:
                    continue
                sp = remain1 - hp
                cur = {
                    "elem_atk": ea,
                    "atk_pct": ap,
                    "heal_pct": hp,
                    "shield_pct": sp,
                    "crit_rate": 0,
                    "crit_dmg": 0,
                    "all_elem_dmg": 0,
                    "basic_dmg": 0,
                    "special_dmg": 0,
                    "ult_dmg": 0,
                    "passive_dmg": 0,
                }
                key = tuple(sorted(cur.items()))
                if key not in seen:
                    seen.add(key)
                    out.append(cur)
    return out

# =====================================================
# Calculation - 시간/스탯/딜
# =====================================================
def neon_cycle_total_time() -> float:
    return 30.0

def neon_calc_final_atk(stats: Dict[str, float]) -> float:
    return calc_attack_value(stats, floor_result=False)

def neon_calc_final_hp(stats: Dict[str, float]) -> float:
    base_hp = float(stats.get("base_hp", 0.0))
    hp_pct = float(stats.get("hp_pct", 0.0))
    promo_hp = float(stats.get("promo_hp_pct_mult", 1.0))
    return base_hp * (1.0 + hp_pct) * promo_hp

def neon_calc_support_metrics(stats: Dict[str, float]) -> Dict[str, float]:
    total_time = neon_cycle_total_time()
    final_atk = neon_calc_final_atk(stats)
    final_hp = neon_calc_final_hp(stats)
    heal_mult = 1.0 + float(stats.get("heal_pct", 0.0))
    shield_mult = 1.0 + float(stats.get("shield_pct", 0.0))

    special_cnt = sum(1 for t in NEON_CYCLE_TOKENS if t == "S")
    raw_shield = final_hp * NEON_BARRIER_HP_RATIO * NEON_BARRIER_PROMO_MULT
    capped_shield = min(raw_shield, NEON_BARRIER_CAP)
    max_shield = capped_shield * shield_mult
    heal_special = final_atk * NEON_SPECIAL_HEAL_RATIO * special_cnt * heal_mult
    hps = heal_special / total_time if total_time > 0 else 0.0
    return {
        "total_time": total_time,
        "final_atk": final_atk,
        "final_hp": final_hp,
        "special_cnt": special_cnt,
        "heal_special": heal_special,
        "total_heal": heal_special,
        "hps": hps,
        "max_shield": max_shield,
        "raw_shield_before_cap": raw_shield,
        "capped_shield_before_bonus": capped_shield,
    }

def neon_cycle_damage(stats: Dict[str, float], party: List[str]) -> Dict[str, float]:
    total_time = neon_cycle_total_time()
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

    for tok in NEON_CYCLE_TOKENS:
        if tok == "B4":
            dmg = skill_damage_from_start(stats, NEON_BASIC_COEFF, "basic")
            direct += dmg
            breakdown["basic"] += dmg
        elif tok == "S":
            dmg = skill_damage_from_start(stats, NEON_SPECIAL_COEFF, "special")
            direct += dmg
            breakdown["special"] += dmg
        elif tok == "U":
            dmg = skill_damage_from_start(stats, NEON_ULT_COEFF, "ult")
            direct += dmg
            breakdown["ult"] += dmg

    strike = strike_total_from_direct(direct, "네온데니쉬맛 쿠키", stats, party)
    unique_extra = skill_damage_from_start(stats, float(stats.get("unique_extra_coeff", 0.0)), "none") * total_time
    breakdown["strike"] = strike
    breakdown["unique"] = unique_extra
    total_damage = math.floor(direct + strike + unique_extra)
    dps = total_damage / 30.0
    return {
        "total_damage": total_damage,
        "total_time": total_time,
        "dps": dps,
        "breakdown_basic": breakdown["basic"],
        "breakdown_special": breakdown["special"],
        "breakdown_ult": breakdown["ult"],
        "breakdown_charge": breakdown["charge"],
        "breakdown_dash": breakdown["dash"],
        "breakdown_passive": breakdown["passive"],
        "breakdown_strike": breakdown["strike"],
        "breakdown_unique": breakdown["unique"],
    }

# =====================================================
# Calculation - 최적화
# =====================================================
def optimize_neon_cycle(
    seaz_name: Optional[str] = None,
    party: Optional[List[str]] = None,
    party_seaz: Optional[Dict[str, str]] = None,
    party_uniques: Optional[Dict[str, str]] = None,
    party_sets: Optional[Dict[str, str]] = None,
    step: int = 2,
    progress_cb: Optional[Callable[[float], None]] = None,
    equip_override: Optional[str] = None,
    unique_override: Optional[Union[str, List[str], Tuple[str, ...], set]] = None,
) -> Optional[dict]:
    cookie = "네온데니쉬맛 쿠키"
    party = list(party or ["윈드파라거스 쿠키"])
    base = BASE_STATS_NEON[cookie].copy()
    pot = dict(NEON_POTENTIALS_FIXED)
    equip_name = equip_override or NEON_FIXED_EQUIP
    artifact_name = NEON_FIXED_ARTIFACT
    uniques = _resolve_unique_list_override(unique_override, [NEON_FIXED_UNIQUE])
    unique_name = uniques[0] if uniques else NEON_FIXED_UNIQUE
    if not seaz_name:
        opts = neon_allowed_seaz()
        seaz_name = FIXED_SEAZ_NEON if FIXED_SEAZ_NEON in opts else (opts[0] if opts else FIXED_SEAZ_NEON)

    shard_candidates = neon_generate_shard_candidates(step=step)
    total = max(1, len(shard_candidates))
    tick = max(1, total // 150)
    done = 0

    def emit(p: float) -> None:
        if progress_cb:
            try:
                progress_cb(p)
            except Exception:
                # 진행률 콜백 오류는 최적화 계산 결과에 영향이 없으므로 무시한다.
                pass

    emit(0.01)
    best: Optional[dict] = None

    zero_shards = {k: 0 for k in SHARD_INC.keys()}
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

    if not is_valid_by_caps(template):
        emit(1.0)
        return None

    for sh in shard_candidates:
        done += 1
        if (done % tick) == 0:
            emit(done / total)

        stats = dict(template)
        stats["elem_atk"] = float(stats.get("elem_atk", 0.0)) + float(SHARD_INC.get("elem_atk", 0.0)) * int(sh.get("elem_atk", 0))
        stats["atk_pct"] = float(stats.get("atk_pct", 0.0)) + float(SHARD_INC.get("atk_pct", 0.0)) * int(sh.get("atk_pct", 0))
        stats["heal_pct"] = float(stats.get("heal_pct", 0.0)) + float(SHARD_INC.get("heal_pct", 0.0)) * int(sh.get("heal_pct", 0))
        stats["shield_pct"] = float(stats.get("shield_pct", 0.0)) + float(SHARD_INC.get("shield_pct", 0.0)) * int(sh.get("shield_pct", 0))

        # template cap 검사를 이미 통과했고 설탕유리조각은 방어관통을 올리지 않으므로 재검사 생략

        support = neon_calc_support_metrics(stats)
        cycle = neon_cycle_damage(stats, party)
        cur = {
            "cookie": cookie,
            "dps": float(cycle["dps"]),
            "cycle_total_damage": float(cycle["total_damage"]),
            "cycle_total_time": 30.0,
            "cycle_breakdown": cycle,
            "max_shield": float(support["max_shield"]),
            "max_heal": float(support["total_heal"]),
            "hps": float(support["hps"]),
            "support_detail": support,
            "equip": equip_name,
            "seaz": seaz_name,
            "unique": unique_name,
            "artifact": artifact_name,
            "potentials": pot,
            "shards": {
                "elem_atk": int(sh.get("elem_atk", 0)),
                "atk_pct": int(sh.get("atk_pct", 0)),
                "heal_pct": int(sh.get("heal_pct", 0)),
                "shield_pct": int(sh.get("shield_pct", 0)),
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
            if cur["max_shield"] > best["max_shield"] + 1e-9:
                best = cur
            elif abs(cur["max_shield"] - best["max_shield"]) <= 1e-9:
                if cur["max_heal"] > best["max_heal"] + 1e-9:
                    best = cur
                elif abs(cur["max_heal"] - best["max_heal"]) <= 1e-9 and cur["dps"] > best["dps"]:
                    best = cur

    emit(1.0)
    return best
