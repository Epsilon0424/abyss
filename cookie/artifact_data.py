"""아티팩트 데이터."""

ARTIFACTS = {
    "NONE": {
        "base_stats": {},
        "unique_stats": {},
        "unique_buffs": {},
    },

    "끝나지 않는 죽음의 밤": {
        "base_stats": {"atk_pct": 0.40},
        "unique_buffs": {"crit_rate": 0.30, "crit_dmg": 0.80},
    },

    "이어지는 마음": {
        "base_stats": {"atk_pct": 0.40},
        "unique_stats": {"debuff_amp": 0.25},
        "unique_buffs": {"crit_dmg": 0.50},
        "emeraldin": {"crit_dmg_bonus": 0.40, "duration": 18.0},
    },

    "비에 젖은 과거": {
        "base_stats": {"buff_amp": 0.16},
        "unique_stats": {},
        "unique_buffs": {"crit_dmg": 0.60},
    },

    "품 속의 온기": {
        "base_stats": {"atk_pct": 0.35},
        "unique_stats": {},
        "unique_buffs": {"all_elem_dmg": 0.30},
        "black_barley": {
            "black_bullet_dmg": 0.40,
            "next8_shot_dmg": 0.60,
        },
    },

    "신기록 달성!": {
        "base_stats": {"crit_dmg": 0.40},
        "unique_stats": {},
        "unique_buffs": {"crit_dmg": 0.80, "all_elem_dmg": 0.60},
    },

    "타오르는 생의 시작": {
        "base_stats": {"atk_pct": 0.40},
        "unique_stats": {},
        "unique_buffs": {"crit_rate": 0.40, "crit_dmg": 0.50},
    },

    "축제의 그림자": {
        "base_stats": {"crit_rate": 0.25},
        "unique_stats": {},
        "unique_buffs": {},
    },

    "희미한 날갯짓": {
        "base_stats": {"buff_amp": 0.16},
        "unique_stats": {},
        "unique_buffs": {},
    },

    "치트키 발견?": {
        "base_stats": {"buff_amp": 0.16},
        "unique_stats": {},
        # 네온 전용 아티
        # - 관리자 권한: 아군 모속피 +30% (벞증 영향 X)
        # - 긴급 패치 +34.6%(공격력 증가), 승급 궁피 +15%는
        # 네온 메인/파티 효과로 별도 적용
        # - 치명적 오류(적 받는 궁 피해 +5.8%)도 별도 적용
        "unique_buffs": {"all_elem_dmg": 0.30},
    },

    "끈적끈적 후폭풍": {
        "base_stats": {"crit_rate": 0.25},
        "unique_stats": {},
        # 체리콜라 전용 아티팩트
        # - 전투 시작 시 공격력 +15%
        # - 강화 기본공격 적중 후 적에게 받는 패시브 스킬 피해 +35%(25초) 부여
        #   적용 타이밍은 cookie/cherrycola.py의 사이클 계산에서 처리한다.
        "unique_buffs": {"atk_pct": 0.15},
        "cherry_cola": {"enemy_passive_taken_inc": 0.35, "duration": 25.0},
    },

    "오늘도 완벽!": {
        "base_stats": {"atk_pct": 0.35},
        "unique_stats": {},
        "unique_buffs": {"crit_rate": 0.40},
        # 블루멜로우 전용 아티팩트
        # - [노블레스 오블리주] 피해 +15%
        # - 차지 공격 사용 시 [완벽주의자]: 패시브 피해 +50% / 5초
        "blue_mallow": {"noblesse_extra_dmg": 0.15, "perfectionist_passive_dmg": 0.50, "duration": 5.0},
    },

    "고요히 흐르는 월광": {
        # Serene Moonlight Flow / 달빛술사 쿠키 전용 아티팩트
        "base_stats": {"debuff_amp": 0.20},
        "unique_stats": {},
        "unique_buffs": {"all_elem_dmg": 0.50, "crit_dmg": 0.50},
        "moonlight": {
            "lullaby_atk_buff": 0.30,
            "dawn_guide_coeff": 12.0 * 3.0,
        },
    },
}
