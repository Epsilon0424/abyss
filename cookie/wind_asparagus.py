# =====================================================
# Imports
# =====================================================
from .common import *
from .common import _resolve_equip_list_override, _min_crit_slots_needed_for_crit100_generic, _resolve_unique_list_override
from functools import lru_cache

# =====================================================
# 윈드파라거스: 치확 100% 고정, 설유 치확 자동 배정
# =====================================================

# =====================================================
# Constants
# =====================================================
WIND_PROMO_ENABLED = True

WIND_PROMO_CRIT_RATE_MULT = 1.0
WIND_PROMO_ATK_PCT_MULT   = 1.0
WIND_PROMO_FINAL_DMG_MULT = 1.0
WIND_PROMO_DEF_PCT_MULT   = 1.08
WIND_PROMO_HP_PCT_MULT    = 1.08

WIND_FORCE_CRIT_100 = True
WIND_WEAPON_ATK_PCT = 0.52
WIND_WEAPON_FINAL_DMG = 0.30
# 돌고 도는 바람의 숨결: 치명타 확률 +10%
WIND_PROMO_CRIT_RATE_ADD = 0.10

BASE_STATS_WIND = {
    "윈드파라거스 쿠키": {
        "atk": 686.0,
        "friendship_atk": friendship_atk_for("윈드파라거스 쿠키"),
        "elem_atk": 0.0,
        # 전용무기 기본 옵션 공격력 +52%
        "atk_pct": WIND_WEAPON_ATK_PCT,
        # 기본 치명타 확률 47.5% + 돌고 도는 바람의 숨결 10%
        "crit_rate": 0.475 + WIND_PROMO_CRIT_RATE_ADD,
        "crit_dmg": 1.5,
        "armor_pen": 0.0,
        # 승급/기본 최종 피해 +5% + 전용무기 고유능력 최종 피해 +30%
        "final_dmg": 0.05 + WIND_WEAPON_FINAL_DMG,
    }
}

# -----------------------------
# 사이클과 계수
# -----------------------------

WIND_SPECIAL_COEFF = 21.016  # 특수스킬 [간절한 바람의 기도] 피해 계수
WIND_BASIC_COEFF   = (0.383 * 3) + (0.554 * 7) + 4.544  # 기본공격 [바람의 속삭임] 합산 계수
# 영원한 약속: 스킬 피해 5836.2%
WIND_ULT_COEFF     = 58.362  # 궁극기 [영원한 약속] 피해 계수

# 아르고 - 충성의 기류
# 1타 피해: 506.9% + 506.9% x 2
# 2타 피해: 326.6% x 6
# 3타는 기존 계산 흐름 유지: 510% + 510% x 4
WIND_LOYALTY_1_COEFF = 5.069 + (5.069 * 2)  # 아르고 [충성의 기류] 1타 피해 계수
WIND_LOYALTY_2_COEFF = 3.266 * 6  # 아르고 [충성의 기류] 2타 피해 계수
WIND_LOYALTY_3_COEFF = 5.10 * (1 + 4)  # 아르고 [충성의 기류] 3타 피해 계수

# 아르고 - 자유로운 비상
# 윈드파라거스 쿠키가 간절한 바람의 기도를 사용하면 함께 공격한다.
# 자유로운 비상 피해는 특수스킬 피해로 취급한다.
WIND_FREE_WING_COEFF = 7.242 * 5  # 아르고 [자유로운 비상] 피해 계수

# 이어지는 마음: 아르고가 주위에 있을 때 차지 공격 [맹세의 회오리]가
# [자유의 날개]로 강화된다. 사진 기준 피해는 공격력의 260% × 30.
WIND_CHARGE_COEFF    = 2.60 * 30.0

WIND_ALWAYS_EMPOWERED_CHARGE = True

WIND_CYCLE_TOKENS = [
    "U", "S", "FW", "C",
    "B",
    "ARGO1",
    "B",
    "ARGO2",
    "B", "B",
    "ARGO3",
    "B",
    "S", "FW", "C",
    "B", "B", "B",
]
# -----------------------------
# 에메랄딘(이어지는 마음) 업타임
# -----------------------------
WIND_EMERALDIN_DEFAULT_DURATION     = 18.0
WIND_EMERALDIN_DEFAULT_CRITDMG_BONUS = 0.40

# =====================================================
# Helpers - 지속시간/후보 생성
# =====================================================
def wind_compute_emeraldin_uptime(
    cycle_tokens: List[str],
    total_time: float,
    empowered_charge_count: int,
    duration: float,
) -> float:
    if empowered_charge_count <= 0 or total_time <= 0:
        return 0.0
    interval = total_time / empowered_charge_count
    if interval <= 0:
        return 1.0
    return clamp(duration / interval, 0.0, 1.0)

# =====================================================
# Helpers - 장비/후보 생성
# =====================================================
def wind_allowed_equips() -> List[str]:
    return ["황금 예복"]

def wind_allowed_uniques() -> List[str]:
    return ["마라맛 쿠키의 기억", "룽샤맛 쿠키의 기억", "칠리맛 쿠키의 기억"]

def wind_allowed_potentials() -> List[Dict[str, int]]:
    return [{
        "debuff_amp": 4,
        "crit_rate": 2,
        "atk_pct": 0,
        "elem_atk": 2,
        "crit_dmg": 0,
        "armor_pen": 0,
        "buff_amp": 0,
    }]

def wind_allowed_artifacts() -> List[str]:
    return ["이어지는 마음"]

def wind_allowed_seaz() -> List[str]:
    return [
        "페퍼루비:믿음직한 브리더",
        "리치코랄:믿음직한 브리더",
        "리치코랄:빛나는 은하수",
    ]

# -----------------------------
# 설유 후보: crit_rate 축 제외
# - 탐색: (crit_dmg / all_elem_dmg / basic_dmg / special_dmg / atk_pct)
# - 자동: crit_rate는 필요한 만큼 배정해서 100% 맞춤
# - 자동: 남는 슬롯은 elem_atk로 채움
# -----------------------------
@lru_cache(maxsize=None)
def wind_generate_shard_candidates_no_cr(step: int = 7) -> List[Dict[str, int]]:
    steps = list(range(0, NORMAL_SLOTS + 1, step))
    if steps[-1] != NORMAL_SLOTS:
        steps.append(NORMAL_SLOTS)

    out: List[Dict[str, int]] = []
    for cd in steps:
        for ae in steps:
            for bd in steps:
                for sd in steps:
                    for ap in steps:
                        used = cd + ae + bd + sd + ap
                        if used > NORMAL_SLOTS:
                            continue
                        out.append({
                            "crit_dmg": cd,
                            "all_elem_dmg": ae,
                            "basic_dmg": bd,
                            "special_dmg": sd,
                            "atk_pct": ap,
                            # 결과 표와 같은 키 구조를 유지하기 위한 고정값
                            "ult_dmg": 0,
                            "passive_dmg": 0,
                        })
    return out

# -----------------------------
# 윈드 사이클 딜 계산
# -----------------------------
# =====================================================
# Calculation - 사이클 딜
# =====================================================
def wind_cycle_damage(stats: Dict[str, float], party: List[str], artifact_name: str) -> Dict[str, float]:
    total_time = 30.0
    empowered_charge_count = sum(1 for tok in WIND_CYCLE_TOKENS if tok == "C" and WIND_ALWAYS_EMPOWERED_CHARGE)

    emeraldin_bonus = 0.0
    if artifact_name == "이어지는 마음":
        em = ARTIFACTS[artifact_name].get("emeraldin", {}) or {}
        dur = float(em.get("duration", WIND_EMERALDIN_DEFAULT_DURATION))
        cd_bonus = float(em.get("crit_dmg_bonus", WIND_EMERALDIN_DEFAULT_CRITDMG_BONUS))

        uptime = wind_compute_emeraldin_uptime(
            cycle_tokens=WIND_CYCLE_TOKENS,
            total_time=total_time,
            empowered_charge_count=empowered_charge_count,
            duration=dur,
        )
        emeraldin_bonus = cd_bonus * uptime

    local = dict(stats)
    local["crit_dmg"] = float(local.get("crit_dmg", 0.0)) + emeraldin_bonus

    # 스킬별 처음부터 계산: skill_damage_from_start 사용

    direct = 0.0
    breakdown = {
        "basic": 0.0,
        "special": 0.0,
        "ult": 0.0,
        "charge": 0.0,
        "argo": 0.0,
        "free_wing": 0.0,
        "strike": 0.0,
        "unique": 0.0,
    }

    def do_basic() -> None:
        nonlocal direct
        dmg = skill_damage_from_start(local, WIND_BASIC_COEFF, "basic")
        direct += dmg
        breakdown["basic"] += dmg

    def do_special() -> None:
        nonlocal direct
        dmg = skill_damage_from_start(local, WIND_SPECIAL_COEFF, "special")
        direct += dmg
        breakdown["special"] += dmg

    def do_ult() -> None:
        nonlocal direct
        dmg = skill_damage_from_start(local, WIND_ULT_COEFF, "ult")
        direct += dmg
        breakdown["ult"] += dmg

    def do_charge() -> None:
        nonlocal direct
        dmg = skill_damage_from_start(local, WIND_CHARGE_COEFF, "basic")
        direct += dmg
        breakdown["charge"] += dmg

    def do_argo(n: int) -> None:
        nonlocal direct
        coeff = WIND_LOYALTY_1_COEFF if n == 1 else (WIND_LOYALTY_2_COEFF if n == 2 else WIND_LOYALTY_3_COEFF)
        dmg = skill_damage_from_start(local, coeff, "basic")
        direct += dmg
        breakdown["argo"] += dmg
        breakdown["basic"] += dmg  # 충성의 기류는 기본공격 피해로 합산

    def do_free_wing() -> None:
        nonlocal direct
        dmg = skill_damage_from_start(local, WIND_FREE_WING_COEFF, "special")
        direct += dmg
        breakdown["free_wing"] += dmg
        breakdown["special"] += dmg  # 특수 피해로 합산

    for tok in WIND_CYCLE_TOKENS:
        if tok == "B":
            do_basic()
        elif tok == "S":
            do_special()
        elif tok == "U":
            do_ult()
        elif tok == "C":
            do_charge()
        elif tok == "FW":
            do_free_wing()
        elif tok == "ARGO1":
            do_argo(1)
        elif tok == "ARGO2":
            do_argo(2)
        elif tok == "ARGO3":
            do_argo(3)

    strike = strike_total_from_direct(direct, "윈드파라거스 쿠키", local, party)
    breakdown["strike"] = strike

    unique_total = skill_damage_from_start(local, float(local.get("unique_extra_coeff", 0.0)), "none") * total_time
    breakdown["unique"] = unique_total

    total_damage = math.floor(direct + strike + unique_total)
    total_damage *= float(local.get("elem_dmg_mult", 1.0))
    dps = total_damage / 30.0

    return {
        "total_damage": total_damage,
        "total_time": total_time,
        "dps": dps,
        "breakdown_basic": breakdown["basic"],
        "breakdown_special": breakdown["special"],
        "breakdown_ult": breakdown["ult"],
        "breakdown_charge": breakdown["charge"],
        "breakdown_strike": breakdown["strike"],
        "breakdown_unique": breakdown["unique"],
        "_emeraldin_avg_critdmg_bonus": emeraldin_bonus,
        "_emeraldin_empowered_charge_count": empowered_charge_count,
    }

# -----------------------------
# 최적화: crit_rate 자동 배정
# -----------------------------
# =====================================================
# Calculation - 최적화
# =====================================================
def optimize_wind_cycle(
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

    cookie = "윈드파라거스 쿠키"
    base = BASE_STATS_WIND[cookie].copy()

    equips = _resolve_equip_list_override(equip_override, wind_allowed_equips())
    uniques = _resolve_unique_list_override(unique_override, wind_allowed_uniques())
    potentials = wind_allowed_potentials()
    artifacts = wind_allowed_artifacts()

    shard_candidates = wind_generate_shard_candidates_no_cr(step=step)

    # 후보에서 "0이 아닌 증가분"만 캐싱 + used(슬롯 사용량)
    shard_adds_list: List[Tuple[Dict[str, int], List[Tuple[str, float]], int]] = []
    for sh in shard_candidates:
        adds: List[Tuple[str, float]] = []
        used = 0
        for k, slots in sh.items():
            if k in ("ult_dmg", "passive_dmg"):
                continue
            used += int(slots)
            inc = float(SHARD_INC.get(k, 0.0))
            if inc and slots:
                adds.append((k, inc * int(slots)))
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

                    # (1) template(설유 0) 생성 → 여기서 "필요 crit_rate 슬롯" 계산
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

                    if WIND_FORCE_CRIT_100:
                        req_cr_slots = _min_crit_slots_needed_for_crit100_generic(template)
                        if req_cr_slots is None:
                            done += len(shard_candidates)
                            if (done % tick) == 0:
                                emit(done / total)
                            continue
                    else:
                        req_cr_slots = 0

                    remain = NORMAL_SLOTS - int(req_cr_slots)
                    if remain < 0:
                        done += len(shard_candidates)
                        if (done % tick) == 0:
                            emit(done / total)
                        continue

                    template.pop("_applied_party_buffs", None)
                    template.pop("_applied_enemy_debuffs", None)

                    for sh_base, adds, used in shard_adds_list:
                        done += 1
                        if (done % tick) == 0:
                            emit(done / total)

                        # 다른 축이 remain을 넘으면 불가
                        if used > remain:
                            continue

                        ea_slots = remain - used  # 남는 슬롯은 elem_atk로

                        stats = template.copy()
                        stats.pop("_damage_context_cache", None)

                        # 후보 축 적용
                        for k, dv in adds:
                            stats[k] = float(stats.get(k, 0.0)) + dv

                        # 치확 설유 자동 배정
                        if WIND_FORCE_CRIT_100 and req_cr_slots and cr_inc:
                            stats["crit_rate"] = float(stats.get("crit_rate", 0.0)) + cr_inc * int(req_cr_slots)

                        # 남는 슬롯 elem_atk
                        if ea_slots and ea_inc:
                            stats["elem_atk"] = float(stats.get("elem_atk", 0.0)) + ea_inc * int(ea_slots)

                        # 최종 검증
                        # 설탕유리조각은 방어관통을 올리지 않으므로 template 단계의 cap 검사 결과를 그대로 사용한다.
                        # 치확 100% 조건은 req_cr_slots 계산으로 이미 맞춘 상태다.

                        cycle = wind_cycle_damage(stats, party, artifact_name)

                        # 기록용 shards(실제 배정 포함)
                        shards_out = dict(sh_base)
                        shards_out["crit_rate"] = int(req_cr_slots)
                        shards_out["elem_atk"] = int(ea_slots)
                        shards_out["ult_dmg"] = 0
                        shards_out["passive_dmg"] = 0

                        cur = {
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
                            "potentials": pot,
                            "party": party,
                                "party_seaz": dict(party_seaz or {}),
                                "party_sets": dict(party_sets or {}),
                                "party_uniques": dict(party_uniques or {}),
                            "stats": stats,
                            "buff_amp_total": stats.get("buff_amp_total", stats.get("buff_amp", 0.0)),
                            "debuff_amp_total": stats.get("debuff_amp_total", stats.get("debuff_amp", 0.0)),
                        }

                        if (best is None) or (cur["dps"] > best["dps"]):
                            best = cur

    emit(1.0)
    return best
