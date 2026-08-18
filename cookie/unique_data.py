# =====================================================
# 시즌 4 유니크 설탕유리조각
# =====================================================
SEASON4_UNIQUE_SHARDS = {
    "NONE": {"type": "none", "allowed_roles": ["any"], "allowed_types": ["any"]},

    # 딜러 유니크 설탕유리조각
    "로드 나이트메어의 뒤틀린 기억": {
        "type": "dps_type_damage",
        "allowed_roles": ["dps"],
        "allowed_types": ["shoot", "magic"],
        "final_dmg_add": 0.36,
        "type_damage_add": 0.20,
    },
    "스타더스트 쿠키의 기억": {
        "type": "dps_type_damage",
        "allowed_roles": ["dps"],
        "allowed_types": ["slash", "strike"],
        "final_dmg_add": 0.36,
        "type_damage_add": 0.20,
    },
    "꿈세계의 기억": {
        "type": "dps_ultimate_atk",
        "allowed_roles": ["dps"],
        "allowed_types": ["any"],
        "final_dmg_add": 0.36,
        "atk_pct_buff": 0.30,
    },

    # 스트라이커 유니크 설탕유리조각
    "밀키웨이맛 쿠키의 기억": {
        "type": "striker_all_elem_support",
        "allowed_roles": ["strike"],
        "allowed_types": ["any"],
        "strike_dmg_add": 0.64,
        "all_elem_dmg_buff": 0.15,
    },
    "꿈열차에 실린 기억": {
        "type": "enhanced_mark",
        "allowed_roles": ["strike"],
        "allowed_types": ["any"],
        "strike_dmg_add": 0.64,
        # 강화 속성 표식: 속성 폭발 피해 +30%
        # 일반 속성 강타 피해 축이 아니라 표식 폭발 전용 곱연산 축으로 처리
        "mark_explosion_dmg_add": 0.30,
    },

    # 서포터 유니크 설탕유리조각
    "멜랑크림 쿠키의 순수한 기억": {
        "type": "support_armor_pen",
        "allowed_roles": ["support"],
        "allowed_types": ["any"],
        "buff_amp_add": 0.36,
        "armor_pen_add": 0.12,
        # 세 서포터 모두 특수 스킬로 심연의 별을 갱신해 30초 사이클 내내 유지
        "armor_pen_add_by_cookie": {
            "이슬맛 쿠키": 0.12,
            "샬롯맛 쿠키": 0.12,
            "네온데니쉬맛 쿠키": 0.12,
        },
    },
    "로드 나이트메어의 기억": {
        "type": "support_atk_buff",
        "allowed_roles": ["support"],
        "allowed_types": ["any"],
        "buff_amp_add": 0.36,
        "atk_pct_buff": 0.15,
    },
    "달빛술사 쿠키의 기억": {
        "type": "support_debuff",
        "allowed_roles": ["support"],
        "allowed_types": ["any"],
        "debuff_amp_add": 0.36,
        "dmg_taken_inc": 0.06,
        "atk_reduction": 0.10,
        "dmg_taken_inc_by_cookie": {
            # 네온데니쉬맛 쿠키: 자장가 미발동
            "네온데니쉬맛 쿠키": 0.0,
        },
    },

    # 공용 유니크 설탕유리조각
    "새벽을 여는 달빛술사 쿠키의 기억": {
        "type": "ultimate_self_buff",
        "allowed_roles": ["any"],
        "allowed_types": ["any"],
        "final_dmg_add": 0.36,
        "shield_pct": 0.20,
        "shield_duration": 15.0,
        "atk_pct_buff": 0.08,
        "crit_dmg_buff": 0.12,
        "def_pct_buff": 0.10,
        "duration": 30.0,
    },
}

# =====================================================
# 시즌 1 유니크 설탕유리조각
# =====================================================
SEASON1_UNIQUE_SHARDS = {
    "NONE": {"type": "none", "allowed_roles": ["any"], "allowed_types": ["any"]},

    # 딜러 유니크 설탕유리조각
    "로스베이컨맛 쿠키의 기억": {
        "type": "dps_proc",
        "allowed_roles": ["dps"],
        "allowed_types": ["shoot", "magic"],
        "final_dmg_add": 0.36,
        # 모든 공격 사용 시 400% x3 추가 투사체 / 쿨타임 3초
        "proc_coeff_per_sec": 4.0,
    },
    "아르고의 기억": {
        "type": "dps_hit_proc",
        "allowed_roles": ["dps"],
        "allowed_types": ["slash", "strike"],
        "final_dmg_add": 0.36,
        # 오라 보유 중 5회 적중마다 추가 피해 50%
        # 개별 타수 차이는 공통 계산에서 평균 10% 추가 피해로 환산
        "avg_dmg_bonus": 0.10,
        "aura_duration": 15.0,
        "damage_reduction": 0.30,
    },

    # 스트라이커 유니크 설탕유리조각
    "나비스의 기억": {
        "type": "enhanced_mark",
        "allowed_roles": ["strike"],
        "allowed_types": ["any"],
        "strike_dmg_add": 0.64,
        "mark_explosion_dmg_add": 0.30,
    },
    "윈드파라거스 쿠키의 기억": {
        "type": "striker_gauge_support",
        "allowed_roles": ["strike"],
        "allowed_types": ["any"],
        "strike_dmg_add": 0.64,
        # 궁극기 사용 시 아군 강타 게이지 증가 효과 / 15초
        # 증가 수치가 표기되지 않아 추가 수치 계산은 하지 않음
        "gauge_buff_duration": 15.0,
    },

    # 서포터 유니크 설탕유리조각
    "데스파라거스의 기억": {
        "type": "support_amp",
        "allowed_roles": ["support"],
        "allowed_types": ["any"],
        # 기본 디버프 증폭 36% + 특수 스킬 3회마다 어둠 15%(13초)
        # 현재 30초 사이클 특수 사용 횟수 기준 평균 업타임 반영
        "debuff_amp_add": 0.36,
        "debuff_amp_add_by_cookie": {
            "이슬맛 쿠키": 0.36 + (0.15 * 13.0 * 2.0 / 90.0),
            "샬롯맛 쿠키": 0.36 + (0.15 * 13.0 * 4.0 / 90.0),
            "네온데니쉬맛 쿠키": 0.36 + (0.15 * 13.0 * 4.0 / 90.0),
            "달빛술사 쿠키": 0.36 + (0.15 * 13.0 * 4.0 / 90.0),
        },
        "base_debuff_amp_add": 0.36,
        "stack_debuff_amp_add": 0.15,
        "stack_duration": 13.0,
        "shield_atk_ratio": 1.25,
        "shield_duration": 10.0,
    },
    "정화된 에메랄딘의 기억": {
        "type": "support_amp",
        "allowed_roles": ["support"],
        "allowed_types": ["any"],
        # 기본 버프 증폭 36% + 특수 스킬 3회마다 정화 15%(13초)
        # 현재 30초 사이클 특수 사용 횟수 기준 평균 업타임 반영
        "buff_amp_add": 0.36,
        "buff_amp_add_by_cookie": {
            "이슬맛 쿠키": 0.36 + (0.15 * 13.0 * 2.0 / 90.0),
            "샬롯맛 쿠키": 0.36 + (0.15 * 13.0 * 4.0 / 90.0),
            "네온데니쉬맛 쿠키": 0.36 + (0.15 * 13.0 * 4.0 / 90.0),
            "달빛술사 쿠키": 0.36 + (0.15 * 13.0 * 4.0 / 90.0),
        },
        "base_buff_amp_add": 0.36,
        "stack_buff_amp_add": 0.15,
        "stack_duration": 13.0,
        "shield_atk_ratio": 1.25,
        "shield_duration": 10.0,
    },

    # 공용 유니크 설탕유리조각
    "슈가스타의 기억": {
        "type": "ultimate_stack_self_buff",
        "allowed_roles": ["any"],
        "allowed_types": ["any"],
        "final_dmg_add": 0.36,
        "trigger_ultimate_count": 3,
        "atk_pct_buff": 0.30,
        "crit_dmg_buff": 0.40,
        "move_spd_buff": 0.20,
        "duration": 15.0,
    },
    "용감한 쿠키의 기억": {
        "type": "ultimate_stack_proc",
        "allowed_roles": ["any"],
        "allowed_types": ["any"],
        "final_dmg_add": 0.36,
        "trigger_ultimate_count": 3,
        "turret_damage_coeff": 2.25,
        "turret_duration": 8.0,
        "dumbbell_damage_coeff": 12.0,
        "heal_atk_ratio": 0.10,
    },
}

# =====================================================
# 시즌 2 유니크 설탕유리조각
# =====================================================
SEASON2_UNIQUE_SHARDS = {
    "NONE": {"type": "none", "allowed_roles": ["any"], "allowed_types": ["any"]},

    # 딜러 유니크 설탕유리조각
    "다크초코 쿠키의 기억": {
        "type": "dps_proc_type_damage",
        "allowed_roles": ["dps"],
        "allowed_types": ["slash", "strike"],
        "final_dmg_add": 0.36,
        "type_damage_add": 0.20,
        # 스크린샷 하단 수치 누락 추정
        # 샬롯맛 쿠키의 기억과 평균 추가 피해가 같도록 환산
        "proc_coeff_per_sec": 20.0 / 3.0,
        "estimated": True,
    },
    "샬롯맛 쿠키의 기억": {
        "type": "dps_proc_type_damage",
        "allowed_roles": ["dps"],
        "allowed_types": ["shoot", "magic"],
        "final_dmg_add": 0.36,
        "type_damage_add": 0.20,
        # 투사체 피해 1000% x2 / 쿨타임 3초
        "proc_coeff_per_sec": 20.0 / 3.0,
    },

    # 스트라이커 유니크 설탕유리조각
    "연금술사맛 쿠키의 기억": {
        "type": "striker_final_buff",
        "allowed_roles": ["strike"],
        "allowed_types": ["any"],
        "strike_dmg_add": 0.64,
        "final_dmg_buff": 0.25,
        "duration": 10.0,
    },
    "선데맛 쿠키의 기억": {
        "type": "enhanced_mark",
        "allowed_roles": ["strike"],
        "allowed_types": ["any"],
        "strike_dmg_add": 0.64,
        "mark_explosion_dmg_add": 0.30,
    },

    # 서포터 유니크 설탕유리조각
    "블랙베리맛 쿠키의 기억": {
        "type": "support_blackberry",
        "allowed_roles": ["support"],
        "allowed_types": ["any"],
        "buff_amp_add": 0.36,
        # 이동 보호막 +60%(12초)와 유령 낙인 +12%(15초)
        # 30초 기준 이동 보호막 40% 업타임으로 평균화
        "atk_pct_buff": 0.36,
    },
    "버터밀크맛 쿠키의 기억": {
        "type": "support_heal_armor_pen",
        "allowed_roles": ["support"],
        "allowed_types": ["any"],
        "final_dmg_add": 0.36,
        "armor_pen_add": 0.10,
        "armor_pen_add_by_cookie": {
            "이슬맛 쿠키": 0.0,
            "샬롯맛 쿠키": 0.10,
            "네온데니쉬맛 쿠키": 0.10,
            "달빛술사 쿠키": 0.0,
        },
    },
    "콜라비맛 쿠키의 기억": {
        "type": "support_dark_mark",
        "allowed_roles": ["support"],
        "allowed_types": ["any"],
        "debuff_amp_add": 0.36,
        "dmg_taken_inc": 0.08,
        "dmg_taken_inc_by_cookie": {
            "네온데니쉬맛 쿠키": 0.0,
        },
        # 표식 소멸 피해 2000% / 지속 15초
        "proc_coeff_per_sec": 20.0 / 15.0,
        "proc_disabled_cookies": ["네온데니쉬맛 쿠키"],
    },

    # 공용 유니크 설탕유리조각
    "오래된 샬롯맛 쿠키의 기억": {
        "type": "ultimate_self_buff",
        "allowed_roles": ["any"],
        "allowed_types": ["any"],
        "final_dmg_add": 0.36,
        "hp_cost_pct": 0.20,
        "shield_pct": 0.20,
        "shield_duration": 15.0,
        "atk_pct_buff": 0.08,
        "crit_dmg_buff": 0.12,
        "move_spd_buff": 0.10,
        "duration": 30.0,
    },
    "웨어울프맛 쿠키의 기억": {
        "type": "werewolf_mark",
        "allowed_roles": ["any"],
        "allowed_types": ["any"],
        "final_dmg_add": 0.36,
        "dmg_taken_inc": 0.03,
        "atk_pct_buff": 0.08,
        "crit_dmg_buff": 0.12,
        "self_dmg_taken_inc": 0.10,
        "move_spd_buff": 0.10,
        "duration": 30.0,
    },
}

# =====================================================
# 시즌 3 유니크 설탕유리조각
# =====================================================
SEASON3_UNIQUE_SHARDS = {
    "NONE": {"type": "none", "allowed_roles": ["any"], "allowed_types": ["any"]},

    # 딜러 유니크 설탕유리조각
    "피닉스페퍼 쿠키의 기억": {
        "type": "dps_type_damage",
        "allowed_roles": ["dps"],
        "allowed_types": ["shoot", "magic"],
        "final_dmg_add": 0.36,
        "type_damage_add": 0.20,
    },
    "폭주한 룽샤맛 쿠키의 기억": {
        "type": "dps_type_damage",
        "allowed_roles": ["dps"],
        "allowed_types": ["slash", "strike"],
        "final_dmg_add": 0.36,
        "type_damage_add": 0.20,
    },
    "꺼지지 않는 봉화의 기억": {
        "type": "dps_ultimate_atk",
        "allowed_roles": ["dps"],
        "allowed_types": ["any"],
        "final_dmg_add": 0.36,
        "atk_pct_buff": 0.30,
    },

    # 스트라이커 유니크 설탕유리조각
    "마라맛 쿠키의 기억": {
        "type": "striker_all_elem_support",
        "allowed_roles": ["strike"],
        "allowed_types": ["any"],
        "strike_dmg_add": 0.64,
        "all_elem_dmg_buff": 0.15,
    },
    "룽샤맛 쿠키의 기억": {
        "type": "enhanced_mark",
        "allowed_roles": ["strike"],
        "allowed_types": ["any"],
        "strike_dmg_add": 0.64,
        "mark_explosion_dmg_add": 0.30,
    },

    # 서포터 유니크 설탕유리조각
    "크러쉬드페퍼맛 쿠키의 기억": {
        "type": "support_armor_pen",
        "allowed_roles": ["support"],
        "allowed_types": ["any"],
        "final_dmg_add": 0.36,
        "armor_pen_add": 0.12,
        "armor_pen_add_by_cookie": {
            "이슬맛 쿠키": 0.08,
            "샬롯맛 쿠키": 0.12,
            "네온데니쉬맛 쿠키": 0.12,
            "달빛술사 쿠키": 0.12,
        },
    },
    "체리맛 쿠키의 기억": {
        "type": "support_atk_buff",
        "allowed_roles": ["support"],
        "allowed_types": ["any"],
        "buff_amp_add": 0.36,
        "atk_pct_buff": 0.15,
    },
    "불야성의 밤의 기억": {
        "type": "support_debuff",
        "allowed_roles": ["support"],
        "allowed_types": ["any"],
        "debuff_amp_add": 0.36,
        "dmg_taken_inc": 0.08,
        "dmg_taken_inc_by_cookie": {
            "네온데니쉬맛 쿠키": 0.0,
        },
    },

    # 공용 유니크 설탕유리조각
    "칠리맛 쿠키의 기억": {
        "type": "ultimate_self_buff",
        "allowed_roles": ["any"],
        "allowed_types": ["any"],
        "final_dmg_add": 0.36,
        "shield_pct": 0.20,
        "shield_duration": 15.0,
        "hp_cost_pct": 0.10,
        "atk_pct_buff": 0.08,
        "crit_dmg_buff": 0.12,
        "move_spd_buff": 0.10,
        "duration": 30.0,
    },
}

# =====================================================
# 시즌별 활성 유니크 설탕유리조각
# =====================================================
SEASON_UNIQUE_SHARDS = {
    "season1": SEASON1_UNIQUE_SHARDS,
    "season2": SEASON2_UNIQUE_SHARDS,
    "season3": SEASON3_UNIQUE_SHARDS,
    "season4": SEASON4_UNIQUE_SHARDS,
}

_ACTIVE_UNIQUE_SEASON = "season4"
UNIQUE_SHARDS = dict(SEASON4_UNIQUE_SHARDS)


def set_active_unique_season(season: str) -> str:
    """활성 시즌 유니크 데이터 전환"""
    global _ACTIVE_UNIQUE_SEASON
    normalized = str(season or "season4").strip().lower()
    if normalized not in SEASON_UNIQUE_SHARDS:
        normalized = "season4"
    UNIQUE_SHARDS.clear()
    UNIQUE_SHARDS.update(SEASON_UNIQUE_SHARDS[normalized])
    _ACTIVE_UNIQUE_SEASON = normalized
    return normalized


def get_active_unique_season() -> str:
    """활성 유니크 시즌"""
    return _ACTIVE_UNIQUE_SEASON


def get_unique_shards_for_season(season: str) -> dict:
    """시즌별 유니크 데이터"""
    normalized = str(season or "season4").strip().lower()
    return SEASON_UNIQUE_SHARDS.get(normalized, SEASON4_UNIQUE_SHARDS)


def get_default_party_unique(cookie_name: str, season: str | None = None) -> str:
    """시즌별 파티 유니크 기본값"""
    active_season = str(season or _ACTIVE_UNIQUE_SEASON or "season4").strip().lower()
    if active_season == "season1":
        defaults = {
            "멜랑크림 쿠키": "아르고의 기억",
            "흑보리맛 쿠키": "로스베이컨맛 쿠키의 기억",
            "샤이닝베리맛 쿠키": "아르고의 기억",
            "피닉스페퍼 쿠키": "로스베이컨맛 쿠키의 기억",
            "블루멜로우맛 쿠키": "로스베이컨맛 쿠키의 기억",
            "스타더스트 쿠키": "로스베이컨맛 쿠키의 기억",
            "잭프루트맛 쿠키": "아르고의 기억",
            "윈드파라거스 쿠키": "나비스의 기억",
            "룽샤맛 쿠키": "나비스의 기억",
            "마블베리맛 쿠키": "나비스의 기억",
            "밀키웨이맛 쿠키": "나비스의 기억",
            "체리콜라맛 쿠키": "나비스의 기억",
            "스테인드누가맛 쿠키": "나비스의 기억",
            "이슬맛 쿠키": "정화된 에메랄딘의 기억",
            "샬롯맛 쿠키": "정화된 에메랄딘의 기억",
            "네온데니쉬맛 쿠키": "정화된 에메랄딘의 기억",
            "달빛술사 쿠키": "데스파라거스의 기억",
        }
    elif active_season == "season2":
        defaults = {
            "멜랑크림 쿠키": "다크초코 쿠키의 기억",
            "흑보리맛 쿠키": "샬롯맛 쿠키의 기억",
            "샤이닝베리맛 쿠키": "다크초코 쿠키의 기억",
            "피닉스페퍼 쿠키": "샬롯맛 쿠키의 기억",
            "블루멜로우맛 쿠키": "샬롯맛 쿠키의 기억",
            "스타더스트 쿠키": "샬롯맛 쿠키의 기억",
            "잭프루트맛 쿠키": "다크초코 쿠키의 기억",
            "윈드파라거스 쿠키": "선데맛 쿠키의 기억",
            "룽샤맛 쿠키": "선데맛 쿠키의 기억",
            "마블베리맛 쿠키": "선데맛 쿠키의 기억",
            "밀키웨이맛 쿠키": "선데맛 쿠키의 기억",
            "체리콜라맛 쿠키": "선데맛 쿠키의 기억",
            "스테인드누가맛 쿠키": "선데맛 쿠키의 기억",
            "이슬맛 쿠키": "블랙베리맛 쿠키의 기억",
            "샬롯맛 쿠키": "버터밀크맛 쿠키의 기억",
            "네온데니쉬맛 쿠키": "블랙베리맛 쿠키의 기억",
            "달빛술사 쿠키": "콜라비맛 쿠키의 기억",
        }
    elif active_season == "season3":
        defaults = {
            "이슬맛 쿠키": "크러쉬드페퍼맛 쿠키의 기억",
            "샬롯맛 쿠키": "크러쉬드페퍼맛 쿠키의 기억",
            "네온데니쉬맛 쿠키": "크러쉬드페퍼맛 쿠키의 기억",
            "달빛술사 쿠키": "불야성의 밤의 기억",
            "윈드파라거스 쿠키": "룽샤맛 쿠키의 기억",
            "룽샤맛 쿠키": "룽샤맛 쿠키의 기억",
            "마블베리맛 쿠키": "룽샤맛 쿠키의 기억",
            "밀키웨이맛 쿠키": "룽샤맛 쿠키의 기억",
            "체리콜라맛 쿠키": "룽샤맛 쿠키의 기억",
            "스테인드누가맛 쿠키": "룽샤맛 쿠키의 기억",
        }
    else:
        defaults = {
            "이슬맛 쿠키": "멜랑크림 쿠키의 순수한 기억",
            "샬롯맛 쿠키": "멜랑크림 쿠키의 순수한 기억",
            "네온데니쉬맛 쿠키": "멜랑크림 쿠키의 순수한 기억",
            "달빛술사 쿠키": "달빛술사 쿠키의 기억",
            "윈드파라거스 쿠키": "꿈열차에 실린 기억",
            "룽샤맛 쿠키": "꿈열차에 실린 기억",
            "마블베리맛 쿠키": "꿈열차에 실린 기억",
            "밀키웨이맛 쿠키": "꿈열차에 실린 기억",
            "체리콜라맛 쿠키": "꿈열차에 실린 기억",
            "스테인드누가맛 쿠키": "꿈열차에 실린 기억",
        }
    return defaults.get(str(cookie_name or "").strip(), "")
