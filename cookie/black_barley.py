# =====================================================
# Imports
# =====================================================
from .common import *
from .common import _resolve_equip_list_override, _min_crit_slots_needed_for_crit100_generic, _resolve_unique_list_override
from functools import lru_cache

# 흑보리맛: 치확 100% 고정, 설유 치확 자동 배정, 고속 이벤트 계산
# =====================================================

# -----------------------------
# 승급, 플래그, 기본 스탯
# -----------------------------
# =====================================================
# Constants
# =====================================================
BLACK_BARLEY_PROMO_ENABLED = True
BLACK_BARLEY_FORCE_CRIT_100 = True
BLACK_BARLEY_WEAPON_ATK_PCT = 0.52
BLACK_BARLEY_WEAPON_FINAL_DMG = 0.30

BLACK_BARLEY_PROMO_CRIT_RATE_MULT    = 1.0
BLACK_BARLEY_PROMO_BASE_ATK_MULT     = 1.0
BLACK_BARLEY_PROMO_DEF_PCT_MULT      = 1.0
BLACK_BARLEY_PROMO_HP_PCT_MULT       = 1.0

# 공격력 표기: 941 + 호감도 38
# 승급 공격력 +30%는 호감도 제외 기본공격력(941)에만 역산하고, 호감도공은 최종 공격력 계산 마지막에 더한다.
BASE_STATS_BLACK_BARLEY = {
    "흑보리맛 쿠키": {
        "atk": atk_from_promoted_base_without_friendship(941.0, 0.30),
        "friendship_atk": friendship_atk_for("흑보리맛 쿠키"),
        "elem_atk": 0.0,
        # 승급 공격력 +30% + 전용무기 기본 옵션 공격력 +52%
        # 공격력 +8%는 표기 공격력에 이미 포함된 값이라 제외한다.
        "atk_pct": 0.30 + BLACK_BARLEY_WEAPON_ATK_PCT,
        "crit_rate": 0.25,
        "crit_dmg": 1.50,
        "armor_pen": 0.0,
        # 승급 최종 피해 +4% + 전용무기 고유능력 최종 피해 +30%
        "final_dmg": 0.04 + BLACK_BARLEY_WEAPON_FINAL_DMG,
    }
}

# -----------------------------
# 사이클과 계수
# -----------------------------

BB_BASIC_COEFF   = 9.159  # 기본공격 전체 계수
BB_EMPOWER_COEFF = 10.295  # 강화 기본공격 전체 계수
BB_SPECIAL_POTION_COEFF = 2.272       # 사냥전술 1회차: 블랙 스플래시 포션
BB_SPECIAL_GUN_COEFF    = 4.828 * 2.0   # 사냥전술 2회차: 흑보리 단총 2발
BB_ULT_COEFF     = (10.721 * 2.0) + 11.928  # 궁극기 본타 계수

BB_PASSIVE_ATK_PCT_ADD = 0.30

BB_POISON_TAKEN_INC    = 0.10  # 사냥꾼의 독: 쿠키에게 받는 피해 +10%
BB_POISON_DUR          = 15.0
BB_WEAK_AIM_EXTRA_COEFF = 1.90  # 약점 조준: 단총 1발 적중당 추가 피해

BB_PREY_DUR                 = 12.0
BB_PREY_BASIC_EXTRA_COEFF   = 1.55  # 사냥감 표식 대상 기본공격 추가 피해 계수
BB_PREY_EMPOWER_EXTRA_COEFF = 2.30  # 사냥감 표식 대상 강화 기본공격 추가 피해 계수
BB_PREY_EXPLODE_COEFF       = 3.75  # 사냥감 표식 폭발 피해 계수

# 사이클: 특 → 궁 → 4강화평 → (특 → 3평 → 강화평) × 4
BB_CYCLE_TOKENS = ["S", "U"] + (["E"] * 4) + (["S", "B", "B", "B", "E"] * 4)

# -----------------------------
# 고속 계산용 이벤트를 미리 계산
# event: (kind, coeff, use_poison_unit, use_black_bonus, use_next8_bonus)
# kind: "basic" | "special" | "ult" | "proc_special" | "proc_basic"
# -----------------------------
# =====================================================
# Helpers - 고속 이벤트 전처리
# =====================================================
def _bb_precompute_fast_events() -> Tuple[List[Tuple[str, float, bool, bool, bool]], float]:
    events: List[Tuple[str, float, bool, bool, bool]] = []

    poison_active = False
    prey_active = False
    next8_left = 0
    ammo = 0
    prey_triggered = False
    special_use_count = 0

    for tok in BB_CYCLE_TOKENS:
        # 탄창 규칙: B가 ammo>0이면 E로 치환, E는 ammo 소비
        action = tok
        if tok == "B" and ammo > 0:
            action = "E"
            ammo -= 1
        elif tok == "E" and ammo > 0:
            ammo -= 1

        if tok == "S":
            special_use_count += 1

            if special_use_count % 2 == 1:
                # 사냥전술 1회차: 블랙 스플래시 포션만 적중하고 사냥꾼의 독을 부여한다.
                events.append(("special", float(BB_SPECIAL_POTION_COEFF), poison_active, False, False))
                poison_active = True
            else:
                # 사냥전술 2회차: 흑보리 단총 2발.
                events.append(("special", float(BB_SPECIAL_GUN_COEFF), poison_active, False, False))

                # 약점 조준은 단총 1발마다 190% 추가 피해가 발생하므로 2회 적용한다.
                events.append(("proc_special", float(BB_WEAK_AIM_EXTRA_COEFF * 2.0), poison_active, False, False))

            next8_left = 8

        elif tok == "U":
            events.append(("ult", float(BB_ULT_COEFF), poison_active, False, False))
            prey_active = True
            prey_triggered = True
            ammo = 4

        elif action in ("B", "E"):
            coeff = BB_BASIC_COEFF if action == "B" else BB_EMPOWER_COEFF
            use_black_bonus = (action == "E")
            use_next8_bonus = (next8_left > 0)

            events.append(("basic", float(coeff), poison_active, use_black_bonus, use_next8_bonus))

            if next8_left > 0:
                next8_left -= 1

            if prey_active:
                extra = BB_PREY_BASIC_EXTRA_COEFF if action == "B" else BB_PREY_EMPOWER_EXTRA_COEFF
                events.append(("proc_basic", float(extra), poison_active, False, False))

    # 사냥감 폭발은 30초 사이클 끝에 1회 반영
    if prey_triggered:
        events.append(("proc_basic", float(BB_PREY_EXPLODE_COEFF), poison_active, False, False))

    return events, 30.0

_BB_FAST_EVENTS, _BB_FAST_TOTAL_TIME = _bb_precompute_fast_events()

# =====================================================
# Calculation - 사이클 딜
# =====================================================
def black_barley_cycle_damage_fast(stats: Dict[str, float], party: List[str], artifact_name: str) -> Dict[str, float]:
    """
    FAST 이벤트 기반 흑보리 1사이클 딜 계산.
    - 외부 의존:
      skill_damage_from_start(stats, coeff, skill_type) -> float
      strike_total_from_direct(total_direct, cookie_name, stats, party) -> float
    """
    total_time = 30.0

    # 패시브 atk% 추가
    base_st = dict(stats)
    base_st.pop("_damage_context_cache", None)
    base_st["atk_pct"] = float(base_st.get("atk_pct", 0.0)) + BB_PASSIVE_ATK_PCT_ADD

    bb_black_bonus = float(base_st.get("_bb_black_bullet_dmg_bonus_raw", 0.0))
    bb_next8_bonus = float(base_st.get("_bb_next8_shot_dmg_bonus_raw", 0.0))

    poison_st = dict(base_st)
    # 다른 흑보리가 이미 파티 공용 [사냥꾼의 독]을 묻힌 경우 같은 디버프는 중첩하지 않는다.
    # 메인 흑보리 단독일 때만 본인 사이클의 독 적용 타이밍에 +10%를 추가한다.
    if not bool(base_st.get("_shared_black_barley_poison_applied", False)):
        poison_st["dmg_taken_inc"] = float(poison_st.get("dmg_taken_inc", 0.0)) + BB_POISON_TAKEN_INC

    breakdown = {
        "basic": 0.0,
        "special": 0.0,
        "ult": 0.0,
        "proc": 0.0,
        "strike": 0.0,
        "unique": 0.0,
    }

    total_direct = 0.0

    for kind, coeff, use_poison_unit, use_black_bonus, use_next8_bonus in _BB_FAST_EVENTS:
        st_for_hit = poison_st if use_poison_unit else base_st

        if kind == "basic":
            extra_mult = 1.0
            if use_black_bonus:
                extra_mult *= (1.0 + bb_black_bonus)
            if use_next8_bonus:
                extra_mult *= (1.0 + bb_next8_bonus)

            dmg = skill_damage_from_start(
                st_for_hit,
                float(coeff),
                "basic",
                extra_skill_mult=extra_mult,
            )
            total_direct += dmg
            breakdown["basic"] += dmg

        elif kind == "special":
            dmg = skill_damage_from_start(
                st_for_hit,
                float(coeff),
                "special",
            )
            total_direct += dmg
            breakdown["special"] += dmg

        elif kind == "ult":
            dmg = skill_damage_from_start(
                st_for_hit,
                float(coeff),
                "ult",
            )
            total_direct += dmg
            breakdown["ult"] += dmg

        else:
            # proc_special / proc_basic
            if kind == "proc_special":
                dmg = skill_damage_from_start(
                    st_for_hit,
                    float(coeff),
                    "special",
                )
            else:
                dmg = skill_damage_from_start(
                    st_for_hit,
                    float(coeff),
                    "basic",
                )

            total_direct += dmg
            breakdown["proc"] += dmg

    sugar_proc = skill_damage_from_start(base_st, float(stats.get("sugar_brilliance_coeff", 0.0)), "none") * BB_CYCLE_TOKENS.count("U")
    if sugar_proc:
        total_direct += sugar_proc
        breakdown["proc"] += sugar_proc

    strike = strike_total_from_direct(total_direct, "흑보리맛 쿠키", stats, party)
    breakdown["strike"] = strike

    unique_total = skill_damage_from_start(base_st, float(stats.get("unique_extra_coeff", 0.0)), "none") * total_time
    breakdown["unique"] = unique_total

    total_damage = math.floor(total_direct + strike + unique_total)

    # -------------------------------------------------
    # elem_dmg_mult 읽기: local.get 우선 사용
    # - stats["_local"] dict를 우선 사용
    # - 없으면 stats["elem_dmg_mult"]
    # - 없으면 1.0
    # -------------------------------------------------
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
# Helpers - 장비/후보 생성
# =====================================================
def black_barley_allowed_equips() -> List[str]:
    return ["달콤한 설탕 깃털", "미지의 방랑자", "수상한 사냥꾼", "시간관리국의 제복"]

def black_barley_allowed_uniques() -> List[str]:
    return ["로드 나이트메어의 뒤틀린 기억"]

def black_barley_allowed_artifacts() -> List[str]:
    return ["품 속의 온기"]

@lru_cache(maxsize=None)
def black_barley_generate_potentials_common() -> List[Dict[str, int]]:
    """속성 공격력 2칸을 고정하고 치확 포함 딜 잠재력을 탐색한다."""
    return generate_damage_potential_candidates(fixed={"elem_atk": 2})

@lru_cache(maxsize=None)
def black_barley_generate_shard_candidates_no_cr(step: int = 7) -> List[Dict[str, int]]:
    """
    crit_rate 축 제거:
      - 탐색: (crit_dmg / all_elem_dmg / atk_pct / basic_dmg)
      - 자동: crit_rate는 필요한 만큼 배정해서 100% 맞춤
      - 자동: 남는 슬롯은 elem_atk로 채움
    """
    steps = list(range(0, NORMAL_SLOTS + 1, step))
    if steps[-1] != NORMAL_SLOTS:
        steps.append(NORMAL_SLOTS)

    out: List[Dict[str, int]] = []
    for cd in steps:
        for ae in steps:
            for ap in steps:
                for bd in steps:
                    used = cd + ae + ap + bd
                    if used > NORMAL_SLOTS:
                        continue
                    out.append({
                        "crit_dmg": cd,
                        "all_elem_dmg": ae,
                        "atk_pct": ap,
                        "basic_dmg": bd,
                    })
    return out

# =====================================================
# Calculation - 최적화
# =====================================================
def optimize_black_barley_cycle(
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
    """장비별 상위 후보를 선별한 뒤 상위 4스탯을 step=1로 전수조사한다."""
    del step  # 장비별 조각 최적화는 항상 1칸 단위로 수행한다.

    cookie = '흑보리맛 쿠키'
    base = BASE_STATS_BLACK_BARLEY[cookie].copy()
    equips = _resolve_equip_list_override(equip_override, black_barley_allowed_equips())
    uniques = _resolve_unique_list_override(unique_override, black_barley_allowed_uniques())
    potentials = [dict(potential_override)] if potential_override is not None else black_barley_generate_potentials_common()
    artifacts = black_barley_allowed_artifacts()
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
                            return black_barley_cycle_damage_fast(stats, party, artifact_name)

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
