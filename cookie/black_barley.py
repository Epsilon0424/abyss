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
BLACK_BARLEY_PROMO_SPECIAL_DMG_MULT  = 1.20
BLACK_BARLEY_PROMO_ULT_DMG_MULT      = 1.20
BLACK_BARLEY_PROMO_BASIC_DMG_MULT    = 1.30

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
BB_SPECIAL_COEFF = 2.272 + (4.828 * 2.0)  # 특수스킬 본타 계수
BB_ULT_COEFF     = (10.721 * 2.0) + 11.928  # 궁극기 본타 계수

BB_PASSIVE_ATK_PCT_ADD = 0.30

BB_POISON_TAKEN_INC    = 0.10
BB_POISON_DUR          = 15.0
BB_POISON_EXTRA_COEFF  = 1.90  # 독 부가 피해 1회 계수

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

    for tok in BB_CYCLE_TOKENS:
        # 탄창 규칙: B가 ammo>0이면 E로 치환, E는 ammo 소비
        action = tok
        if tok == "B" and ammo > 0:
            action = "E"
            ammo -= 1
        elif tok == "E" and ammo > 0:
            ammo -= 1

        if tok == "S":
            # 특수기 본타 + 독 부가 2타
            events.append(("special", float(BB_SPECIAL_COEFF), poison_active, False, False))
            poison_active = True

            # 독 부가타: 독 적용된 유닛으로 처리
            events.append(("proc_special", float(BB_POISON_EXTRA_COEFF * 2.0), True, False, False))

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
    base_st["atk_pct"] = float(base_st.get("atk_pct", 0.0)) + BB_PASSIVE_ATK_PCT_ADD

    bb_black_bonus = float(base_st.get("_bb_black_bullet_dmg_bonus_raw", 0.0))
    bb_next8_bonus = float(base_st.get("_bb_next8_shot_dmg_bonus_raw", 0.0))

    poison_st = dict(base_st)
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
            dmg = skill_damage_from_start(st_for_hit, float(coeff), "special")
            total_direct += dmg
            breakdown["special"] += dmg

        elif kind == "ult":
            dmg = skill_damage_from_start(st_for_hit, float(coeff), "ult")
            total_direct += dmg
            breakdown["ult"] += dmg

        else:
            # proc_special / proc_basic
            if kind == "proc_special":
                dmg = skill_damage_from_start(st_for_hit, float(coeff), "special")
            else:
                dmg = skill_damage_from_start(st_for_hit, float(coeff), "basic")

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
    return ["피닉스페퍼 쿠키의 기억"]

def black_barley_allowed_artifacts() -> List[str]:
    return ["품 속의 온기"]

@lru_cache(maxsize=None)
def black_barley_generate_potentials_common() -> List[Dict[str, int]]:
    """
    - 총 8칸, elem_atk 2칸 고정(FREE=6)
    - 치확 100% 고정이면 potentials에서 crit_rate 축 제거
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
                p["crit_rate"] = 0
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

@lru_cache(maxsize=None)
def black_barley_generate_shard_candidates_no_cr(step: int = 7) -> List[Dict[str, int]]:
    """
    crit_rate 축 제거:
      - 탐색: (crit_dmg / all_elem_dmg / atk_pct / basic_dmg / special_dmg / ult_dmg)
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
                    for sd in steps:
                        for ud in steps:
                            used = cd + ae + ap + bd + sd + ud
                            if used > NORMAL_SLOTS:
                                continue
                            out.append({
                                "crit_dmg": cd,
                                "all_elem_dmg": ae,
                                "atk_pct": ap,
                                "basic_dmg": bd,
                                "special_dmg": sd,
                                "ult_dmg": ud,
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
) -> Optional[dict]:
    """
    흑보리 1사이클 DPS 최대화.
    - 외부 의존:
      _resolve_equip_list_override(...)
      build_stats_for_combo(...)
      is_valid_by_caps(stats)
      _min_crit_slots_needed_for_crit100_generic(stats)
      SHARD_INC, NORMAL_SLOTS
    """
    cookie = "흑보리맛 쿠키"
    base = BASE_STATS_BLACK_BARLEY[cookie].copy()

    equips = _resolve_equip_list_override(equip_override, black_barley_allowed_equips())
    uniques = _resolve_unique_list_override(unique_override, black_barley_allowed_uniques())
    potentials = black_barley_generate_potentials_common()
    artifacts = black_barley_allowed_artifacts()

    shard_candidates = black_barley_generate_shard_candidates_no_cr(step=step)

    # shard_candidates -> (adds_list) 미리 계산
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

                    # caps(템플릿) 불통이면 컷
                    if not is_valid_by_caps(template):
                        done += len(shard_candidates)
                        if (done % tick) == 0:
                            emit(done / total)
                        continue

                    # 치확 100% 강제: template 기준 최소 crit 슬롯 계산
                    if BLACK_BARLEY_FORCE_CRIT_100:
                        promo = float(template.get("promo_crit_rate_mult", 1.0))
                        buff_cr = float(template.get("buff_crit_rate_raw", 0.0))
                        base_cr = float(template.get("crit_rate", 0.0))
                        eff_cr = base_cr * promo + buff_cr

                        # 이미 100% 초과면 줄일 방법이 없다고 보고 스킵
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

                    # 로그/표시용 내부키는 최적화 평가에 필요없으면 제거
                    template.pop("_applied_party_buffs", None)
                    template.pop("_applied_enemy_debuffs", None)

                    # armor_pen이 shards로 변동 없음 → 초과면 즉시 컷
                    promo_ap_mult = float(template.get("promo_armor_pen_mult", 1.0))
                    base_ap = float(template.get("armor_pen", 0.0)) * promo_ap_mult
                    if base_ap > 0.80 + 1e-12:
                        done += len(shard_candidates)
                        if (done % tick) == 0:
                            emit(done / total)
                        continue

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

                        if BLACK_BARLEY_FORCE_CRIT_100 and req_cr_slots and cr_inc:
                            stats["crit_rate"] = float(stats.get("crit_rate", 0.0)) + cr_inc * req_cr_slots

                        if ea_slots and ea_inc:
                            stats["elem_atk"] = float(stats.get("elem_atk", 0.0)) + ea_inc * int(ea_slots)

                        # 설탕유리조각은 방어관통을 올리지 않으므로 template 단계의 cap 검사 결과를 그대로 사용한다.
                        # 치확 100% 조건은 req_cr_slots 계산으로 이미 맞춘 상태다.

                        cycle = black_barley_cycle_damage_fast(stats, party, artifact_name)
                        dps = cycle["dps"]

                        if (best is None) or (dps > best["dps"]):
                            shards_out = dict(sh_base)
                            shards_out["crit_rate"] = int(req_cr_slots)
                            shards_out["elem_atk"] = int(ea_slots)

                            # 결과 표와 로그의 키 구조를 맞추기 위한 고정값
                            shards_out["passive_dmg"] = 0
                            shards_out["def_pct"] = 0
                            shards_out["shield_pct"] = 0

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
