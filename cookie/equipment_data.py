"""장비 세트 데이터"""

# 유성우/대마술사 세트효과는 30초 중 15초 평균 반영값으로 관리
# 장비 속성 내성 감소 디버프 증폭 제외
# 달빛술사 유성우 속성 내성 감소 10% 원값
EQUIP_EFFECT_UPTIME_WEIGHT = 0.5

# 기존 코드 호환용 내부 변수
weight = EQUIP_EFFECT_UPTIME_WEIGHT

EQUIP_SETS = {
    "달콤한 설탕 깃털": {
        "head": {"base": {"all_elem_dmg": 0.312}, "unique": {"atk_pct": 0.30}},
        "top":  {"base": {"def_pct": 0.52},       "unique": {"armor_pen": 0.15}},
        "bottom":{"base": {"hp_pct": 0.52},       "unique": {"elem_atk": 96}},
        "set_effect": {"base": {"all_elem_dmg": 0.20}}
    },
    "미지의 방랑자": {
        "head": {"base": {"all_elem_dmg": 0.312}, "unique": {"crit_dmg": 0.375}},
        "top":  {"base": {"def_pct": 0.52},       "unique": {"all_elem_dmg": 0.225}},
        "bottom":{"base": {"hp_pct": 0.52},       "unique": {"elem_atk": 120}},
        "set_effect": {"base": {"crit_rate": 0.15}}
    },
    "수상한 사냥꾼": {
        "head": {"base": {"all_elem_dmg": 0.312}, "unique": {"basic_dmg": 0.225}},
        "top":  {"base": {"def_pct": 0.52},       "unique": {"crit_rate": 0.225}},
        "bottom":{"base": {"hp_pct": 0.52},       "unique": {"crit_dmg": 0.375}},
        # 세트 공격력 20% 일반 공격력 합산
        "set_effect": {"base": {"atk_pct": 0.20}}
    },
    "시간관리국의 제복": {
        "head": {"base": {"all_elem_dmg": 0.312}, "unique": {"atk_pct": 0.30}},
        "top":  {"base": {"def_pct": 0.52},       "unique": {"elem_atk": 120}},
        "bottom":{"base": {"hp_pct": 0.52},       "unique": {"all_elem_dmg": 0.225}},
        # 세트효과 공격력 15% + 15%
        # - 일반 공격력 15%
        # - 버프 공격력 15%
        "set_effect": {"base": {"atk_pct": 0.15, "final_atk_mult": 0.15}}
    },
    "전설의 유령해적": {
        "head": {"base": {"all_elem_dmg": 0.312}, "unique": {"atk_pct": 0.30}},
        "top":  {"base": {"def_pct": 0.52},       "unique": {"hp_pct": 0.30}},
        "bottom":{"base": {"hp_pct": 0.52},       "unique": {"def_pct": 0.30}},
        "set_effect": {"base": {"all_elem_dmg": 0.30, "def_reduction_raw": 0.10}}
    },
    "황금 예복": {
        "head": {"base": {"all_elem_dmg": 0.312}, "unique": {"crit_rate": 0.225}},
        "top":  {"base": {"def_pct": 0.52},       "unique": {"special_dmg": 0.225}},
        "bottom":{"base": {"hp_pct": 0.52},       "unique": {"ult_dmg": 0.225}},
        "set_effect": {"base": {"element_strike_dmg": 0.25, "debuff_amp": 0.15}}
    },
    "유성우의 향연": {
        "head": {"base": {"all_elem_dmg": 0.312}, "unique": {"debuff_amp": 0.15}},
        "top":  {"base": {"def_pct": 0.52},       "unique": {"hp_pct": 0.30}},
        "bottom":{"base": {"hp_pct": 0.52},       "unique": {"def_pct": 0.30}},
        "set_effect": {"base": {"elem_res_reduction_raw": 0.10 * weight, "debuff_amp": 0.15}}
    },
    "영원의 대마술사": {
        "head": {"base": {"all_elem_dmg": 0.312}, "unique": {"buff_amp": 0.15}},
        "top":  {"base": {"def_pct": 0.52},       "unique": {"hp_pct": 0.30}},
        "bottom":{"base": {"hp_pct": 0.52},       "unique": {"def_pct": 0.30}},
        "set_effect": { "base": {"buff_amp": 0.15, "all_elem_dmg": 0.30 * weight}
        }
    },
}
