UNIQUE_SHARDS = {
    "NONE": {"type": "none", "allowed_roles": ["any"], "allowed_types": ["any"]},

    # DPS 유니크 설탕유리조각
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

    # STRIKER 유니크 설탕유리조각
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
        # 일반 속성 강타 피해 축이 아니라 표식 폭발 전용 곱연산 축으로 처리한다.
        "mark_explosion_dmg_add": 0.30,
    },

    # SUPPORT 유니크 설탕유리조각
    "멜랑크림 쿠키의 순수한 기억": {
        "type": "support_armor_pen",
        "allowed_roles": ["support"],
        "allowed_types": ["any"],
        "buff_amp_add": 0.36,
        "armor_pen_add": 0.12,
        # 세 서포터 모두 특수 스킬로 심연의 별을 갱신해 30초 사이클 내내 유지한다.
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
            # 네온데니쉬맛 쿠키는 적에게 디버프를 부여하지 않아 자장가가 발동하지 않는다.
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
