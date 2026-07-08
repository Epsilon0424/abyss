UNIQUE_SHARDS = {
    "NONE": {"type": "none", "allowed_roles": ["any"], "allowed_types": ["any"]},

    # DPS 유니크 설탕유리조각
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
        "type": "dps_beacon_atk",
        "allowed_roles": ["dps"],
        "allowed_types": ["any"],
        "final_dmg_add": 0.36,
        "atk_pct_buff": 0.30,
    },

    # STRIKER 유니크 설탕유리조각
    "마라맛 쿠키의 기억": {
        "type": "mala_strike_support",
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
        # 강화속성표식: 속성 폭발 피해 +30%
        # - 일반 속성강타 피해(element_strike_dmg)에 더하지 않고 별도 곱연산 축으로 처리
        "mark_explosion_dmg_add": 0.30,
    },

    # SUPPORT 유니크 설탕유리조각
    "크러쉬드페퍼맛 쿠키의 기억": {
        "type": "crushed_pepper_support",
        "allowed_roles": ["support"],
        "allowed_types": ["any"],
        "final_dmg_add": 0.36,
        # 식지않는 충성: 아군 방어력 관통 +12%
        # 이슬맛 쿠키는 30초 중 10초 유지 → 4% 평균
        # 샬롯/네온데니쉬는 끊기지 않는 것으로 보고 12% 상시
        "armor_pen_add": 0.12,
        "armor_pen_add_by_cookie": {
            "이슬맛 쿠키": 0.04,
            "샬롯맛 쿠키": 0.12,
            "네온데니쉬맛 쿠키": 0.12,
        },
    },
    "체리맛 쿠키의 기억": {
        "type": "cherry_support",
        "allowed_roles": ["support"],
        "allowed_types": ["any"],
        "buff_amp_add": 0.36,
        "atk_pct_buff": 0.15,
    },
    "불야성의 밤의 기억": {
        "type": "sleepless_night_support",
        "allowed_roles": ["support"],
        "allowed_types": ["any"],
        "debuff_amp_add": 0.36,
        # 밤의 열기: 쿠키에게 받는 피해 +8% 상시
        # - 네온데니쉬맛 쿠키는 디버프를 부여하지 않으므로 밤의 열기 0%
        "dmg_taken_inc": 0.08,
        "dmg_taken_inc_by_cookie": {
            "네온데니쉬맛 쿠키": 0.0,
        },
    },

    # ANY 유니크 설탕유리조각
    "칠리맛 쿠키의 기억": {
        "type": "chili_sauce",
        "allowed_roles": ["any"],
        "allowed_types": ["any"],
        "hp_cost_pct": 0.10,
        "shield_pct": 0.20,
        "shield_duration": 15.0,
        "atk_pct_buff": 0.08,
        "crit_dmg_buff": 0.12,
        "move_spd_buff": 0.10,
        "duration": 30.0,
    },
}
