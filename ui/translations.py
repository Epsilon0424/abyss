"""Korean/English UI translation and text formatting helpers."""
import html as _html
import re
from pathlib import Path

import pandas as pd
import streamlit as st

_ASSET_ROOT = Path(__file__).resolve().parent.parent

# =====================================================
# English UI translation
# =====================================================
_ENGLISH_TXT_FALLBACK = r"""
전체 : All
어둠 : Dark
빛 : Light
신비 : Mystic
불 : Fire
물 : Water
바람 : Wind
대지 : Earth

윈드파라거스 쿠키: Wind Asparagus
이슬맛 쿠키: Dew
멜랑크림 쿠키: Melanchream
흑보리맛 쿠키: Black Barley
샤이닝베리맛 쿠키: Shiningberry
피닉스페퍼 쿠키: Phoenix Pepper
샬롯맛 쿠키: Shallot
네온데니쉬맛 쿠키: Neon Danish
룽샤맛 쿠키: Mala Longxia
마블베리맛 쿠키: Marbleberry
체리콜라맛 쿠키: Cherry Cola Cookie
블루멜로우맛 쿠키: Blue Mallow Cookie
달빛술사 쿠키: Moonlight Cookie
밀키웨이맛 쿠키: Milky Way Cookie
스타더스트 쿠키: Stardust Cookie

달콤한 설탕 깃털 : Sugar Feather
미지의 방랑자 : Mysterious Wanderer
수상한 사냥꾼 : Suspicious Hunter
시간관리국의 제복 : TBD Uniform
전설의 유령해적 : Ghost Captain
황금 예복 : Golden Finery
유성우의 향연 : Falling Stars
영원의 대마술사 : Eternal Magician

페퍼루비 : Pepper Ruby
리치코랄 : Lychee Coral
바닐라몬드 : Vanilla Almond
레몬그라스톤 : Lemongracite
허브그린드 : Herberyl
민트쿼츠 : Mint Quartz
플럼나이트 : Plumite
믿음직한 브리더 : Trusty Breeder
듬직한 격투가 : Solid Fighter
사냥꾼의 본능 : Hunter's Instinct
위대한 통치자 : Great Ruler
거침없는 습격자 : Unstoppable Raider
영예로운 기사도 : Honorable Chivalry
돌진하는 전차 : Charging Chariot
추격자의 결의 : Pursuer's Resolve
빛나는 은하수 : Shining Galaxy
막힘없는 성장 : Unstoppable Growth
치열한 선봉자 : Fierce Vanguard
백마법사의 의지 : Will of the White Mage
작은 성배 : Small Chalice
가벼운 손길 : Light Touch
번뜩이는 기지 : Coruscating Wit
달빛의 속삭임 : Moonlight Whispers

끝나지 않는 죽음의 밤 : Dawnless Death
이어지는 마음 : Linked Hearts
비에 젖은 과거 : Rain-soaked Past
품 속의 온기 : Warm Embrace
신기록 달성! : New High Score!
타오르는 생의 시작 : Beginning of Blazing Life
축제의 그림자 : Festival Shadows
희미한 날갯짓 : Faint Wingbeats
치트키 발견? : Hidden Cheat Item
충전은 타이밍 : Well-timed Recharge
끈적끈적 후폭풍 : Sticky Situation
오늘도 완벽! : Another Day of Perfection
고요히 흐르는 월광 : Serene Moonlight Flow
꿈의 저편으로 : Toward Dreams' End
외딴 별의 여정 : Journey of a Distant Star

로드 나이트메어의 뒤틀린 기억 : Lord Nightmare's Twisted Memory
스타더스트 쿠키의 기억 : Stardust Cookie's Memory
꿈세계의 기억 : World of Dreams Memory
밀키웨이맛 쿠키의 기억 : Milky Way Cookie's Memory
꿈열차에 실린 기억 : Dream Express Memory
멜랑크림 쿠키의 순수한 기억 : Melanchream Cookie's Pure Memory
로드 나이트메어의 기억 : Lord Nightmare's Memory
달빛술사 쿠키의 기억 : Moonlight Cookie's Memory
새벽을 여는 달빛술사 쿠키의 기억 : Moonlight Cookie's Dawnbreaker Memory

치명타 확률  : CRIT Rate
새벽녘 치명타 확률 : Dawn CRIT Rate
치명타 피해 : CRIT Damage
모든 속성 피해 : All Elemental DMG
기본 공격 피해 : Basic Attack Damage
특수 스킬 피해 : Special Skill Damage
궁극기 피해 : Ultimate Damage
패시브 스킬 피해 : Passive Skill Damage
OA(기본공) : Original ATK
EA(속성공) : Elemental ATK
공격력 % : ATK
공격력 증가% : ATK Increase
속성 공격력 : Elemental ATK
최종 공격력 : Final ATK
방어력 % : DEF
보호막 % : Shield
회복량 % : Healing
방어력 관통 : Def Penetration
버프 증폭 : Buff AMP
디버프 증폭 : Debuff AMP
최종 피해 : Total Damage
강화 속성 표식 : Enhanced Elemental Tag
속성 표식 : Elemental Tag
적이 받는 궁극기 피해 : Ultimate Damage taken
적이 받는 패시브 피해 : Passive Skill Damage taken
방어력 감소 : DEF Reduction
피해량 : Damage
속성 내성 감소 : Elemental RES Reduction
속성 강타 피해 : Elemental Burst Damage
받는 피해 증가 : Damage Taken Increase
적이 받는 피해 증가 : Enemy Damage Taken Increase
궁극기 : Ultimate
속성 강타 : Elemental Burst
기본공격 : Basic Attack
차징 : Charge-Up
특수스킬 : Special Skill
대시 : Dash
패시브 : Passive

설탕유리조각 : Sugarglass Shard
유니크 설탕유리조각 : Unique Sugarglass Shard
속성 : Element
쿠키 : Cookie
시즈나이트 : Seasonite
파티 : Party
자동 : Auto
실행 : Run
계산 보정 안내 : Calculation Adjustment Guide
잠재력 : Hidden Power
아티팩트 : Artifact
1사이클 시간(s) : 1 Cycle Time(s)”
1사이클 총딜 : Total Damage per Cycle
결과 : Result
최종 스탯 : Final Stats
사이클 기여도 : Cycle Contribution
세팅 : Setup
장비 : Equipment
항목 : Item
값 : Value
비율(%) : Ratio(%)
사이클 내 기여도 : Cycle Contribution
세부사항 : Details
공격력 : ATK
치명타 : Critical
피해 보정 : Damage Modifier
스킬 타입 피해 증가 : Skill Type Damage Increase
(파티) 보호막 / 방어 : (Party)Shield / Defense
(파티) 버프 / 디버프 증폭 : (Party)Buff / Debuff Amplification

설정 후 실행하면 결과가 표시됩니다.
Configure the settings and press Run to see the results.

어비스 레이드 기준 쿠키 세팅별 최종 스탯, 사이클 기여도, DPS 분석 시뮬레이터
Abyss Raid simulator for analyzing final stats, cycle contribution, and DPS across different cookie setups.

장비를 자동으로 두고 실행하면 오래 걸릴 수 있습니다. 달콤한 설탕 깃털로 두고 실행하는 것을 권장합니다.
Running with equipment set to Auto may take a long time.
We recommend running it with Sugar Feather selected.

룽샤 : 불가역 20% → 10% 적용
Mala Longxia : Irreversibility 20% → 10% applied

백마법사의 의지 : 공격력 12.5%, 모든 속성 피해 15% 적용
Will of the White Mage : ATK 12.5%, Elemental DMG 15% applied

사냥꾼의 본능 : 보스전 최종피해 0% 적용
Hunter's Instinct : Boss Total DMG 0% applied

영원의 대마술사 : 모든 속성 피해 30% → 15% 적용
Eternal Magician : Elemental DMG 30% → 15% applied

유성우의 향연 : 속성 내성 감소 10% → 5% 적용
Falling Stars : Elemental RES Reduction 10% → 5% applied

유성우의 향연 : 속성 내성 감소 10% 적용
Falling Stars : Elemental RES Reduction 10%


THE ABYSS RAID COOKIE LAB에 사용된 쿠키런:모험의 탑 관련 리소스의 저작권은 데브시스터즈에 있습니다.
Copyright for the CookieRun: Tower of Adventures resources used in THE ABYSS RAID COOKIE LAB belongs to Devsisters.

일부 스탯은 가산/배율 적용이 함께 반영되어, 단순 합산값과 다를 수 있습니다.
Some stats include both additive and multiplicative calculations, so they may differ from simple summed values.

기타 문의 : Epsilon24@gmail.com
For inquiries: Epsilon24@gmail.com
"""

_EXTRA_ENGLISH = {
    "기본": "Basic",
    "설정": "Setting",
    "언어": "Language",
    "없음": "None",
    "신비": "Mystic",
    "충전은 타이밍": "Well-timed Recharge",
    "체리콜라맛 쿠키": "Cherry Cola Cookie",
    "블루멜로우맛 쿠키": "Blue Mallow Cookie",
    "달빛술사 쿠키": "Moonlight Cookie",
    "밀키웨이맛 쿠키": "Milky Way Cookie",
    "스타더스트 쿠키": "Stardust Cookie",
    "새벽녘": "Dawn",
    "새벽녘 치명타 확률": "Dawn CRIT Rate",
    "고요히 흐르는 월광": "Serene Moonlight Flow",
    "꿈의 저편으로": "Toward Dreams' End",
    "외딴 별의 여정": "Journey of a Distant Star",
    "플럼나이트": "Plumite",
    "플럼나이트:백마법사의 의지": "Plumite: Will of the White Mage",
    "플럼나이트:작은 성배": "Plumite: Small Chalice",
    "플럼나이트:가벼운 손길": "Plumite: Light Touch",
    "플럼나이트:번뜩이는 기지": "Plumite: Coruscating Wit",
    "플럼나이트:달빛의 속삭임": "Plumite: Moonlight Whispers",
    "끈적끈적 후폭풍": "Sticky Situation",
    "오늘도 완벽!": "Another Day of Perfection",
    "보호막량": "Shield",
    "회복량": "Healing",
    "유니크 조각": "Unique Shard",
    "장비를 자동으로 두고 실행하면 오래 걸릴 수 있습니다.": "If you leave the equipment on Auto and run it, it may take a long time.",
    "달콤한 설탕 깃털로 두고 실행하는 것을 권장합니다.": "We recommend running it with Sugar Feather selected.",
    "룽샤 : 불가역 20% → 10% 적용": "Mala Longxia: Irreversibility 20% → 10% applied",
    "백마법사의 의지 : 공격력 12.5%, 모든 속성 피해 15% 적용": "Will of the White Mage: ATK 12.5%, All Elemental DMG 15% applied",
    "사냥꾼의 본능 : 보스전 최종피해 0% 적용": "Hunter's Instinct: Boss Total DMG 0% applied",
    "영원의 대마술사 : 모든 속성 피해 30% → 15% 적용": "Eternal Magician: All Elemental DMG 30% → 15% applied",
    "유성우의 향연 : 속성 내성 감소 10% → 5% 적용": "Falling Stars: Elemental RES Reduction 10% → 5% applied",
    "유성우의 향연 : 내성 감소 10% 적용": "Falling Stars: Elemental RES Reduction 10%",
    "달빛술사는 속성 내성 감소 10% 적용": "Moonlight applies Elemental RES Reduction 10%",
    "불가역 20% → 10% 적용": "Irreversibility 20% → 10% applied",
    "공격력 12.5%, 모든 속성 피해 15% 적용": "ATK 12.5%, All Elemental DMG 15% applied",
    "보스전 최종피해 0% 적용": "Boss Total DMG 0% applied",
    "모든 속성 피해 30% → 15% 적용": "All Elemental DMG 30% → 15% applied",
    "속성 내성 감소 10% → 5% 적용": "Elemental RES Reduction 10% → 5% applied",
    "THE ABYSS RAID COOKIE LAB에 사용된 쿠키런:모험의 탑 관련 리소스의 저작권은 데브시스터즈에 있습니다.": "Copyright for the CookieRun: Tower of Adventures resources used in THE ABYSS RAID COOKIE LAB belongs to Devsisters.",
    "일부 스탯은 가산/배율 적용이 함께 반영되어, 단순 합산값과 다를 수 있습니다.": "Some stats include both additive and multiplicative calculations, so they may differ from simple summed values.",
    "기타 문의 : Epsilon24@gmail.com": "For inquiries: Epsilon24@gmail.com",
    "광휘": "Brilliant",
    "관통": "Piercing",
    "원소": "Elemental",
    "파쇄": "Tearing",
    "축복": "Blessed",
    "낙인": "Branded",
    # English.txt 안의 "이름 : 보정설명 : 영어설명" 줄이
    # 장비/시즈 이름 번역을 덮어쓰지 않도록 기본 이름을 마지막에 강제 보정한다.
    "영원의 대마술사": "Eternal Magician",
    "전설의 유령해적": "Ghost Captain",
    "달콤한 설탕 깃털": "Sugar Feather",
    "미지의 방랑자": "Mysterious Wanderer",
    "수상한 사냥꾼": "Suspicious Hunter",
    "시간관리국의 제복": "TBD Uniform",
    "플럼나이트": "Plumite",
    "백마법사의 의지": "Will of the White Mage",
    "번뜩이는 기지": "Coruscating Wit",
    "황금 예복": "Golden Finery",
    "유성우의 향연": "Falling Stars",
    "달빛술사 쿠키": "Moonlight Cookie",
    "밀키웨이맛 쿠키": "Milky Way Cookie",
    "스타더스트 쿠키": "Stardust Cookie",
    "고요히 흐르는 월광": "Serene Moonlight Flow",
    "꿈의 저편으로": "Toward Dreams' End",
    "외딴 별의 여정": "Journey of a Distant Star",
    "플럼나이트:백마법사의 의지": "Plumite: Will of the White Mage",
    "플럼나이트:작은 성배": "Plumite: Small Chalice",
    "플럼나이트:가벼운 손길": "Plumite: Light Touch",
    "플럼나이트:번뜩이는 기지": "Plumite: Coruscating Wit",
    "플럼나이트:달빛의 속삭임": "Plumite: Moonlight Whispers",
    "룽샤": "Mala Longxia",
    "백마법사의 의지": "Will of the White Mage",
    "사냥꾼의 본능": "Hunter's Instinct",
    "이슬 + 멜랑크림 순수한 기억": "Dew + Melanchream Pure Memory",
    "선택하신 속성의 쿠키가 없습니다.": "There are no cookies for the selected attribute.",
    "선택 가능한 시즈나이트가 없습니다.": "No available Seasonites.",
    "세부 설정이 없습니다.": "No detail settings.",
    "스탯 정보가 없습니다.": "No stat information.",
    "표시할 항목 없음": "No items to display",
    "사이클 내 딜 기여도": "Damage Contribution in Cycle",
    "딜": "Damage",
    "발동(세트/효과)": "Proc(Set/Effect)",
    "유니크": "Unique",
    "선택(수동)": "Manual",
    "최적(자동)": "Optimal(Auto)",
    "시즈나이트 선택": "Select Seasonite",
    "파티(서폿)": "Party(Support)",
    "파티(스트)": "Party(Striker)",
    "메인 유니크 설탕유리조각": "Main Unique Sugarglass Shard",
    "파티 쿠키의 장비, 시즈나이트, 유니크 설탕유리조각은 세부사항에서 수정할 수 있습니다": "Party cookies' equipment, Seasonite, and unique Sugarglass Shard can be changed in Details.",
    "파티 쿠키의 장비, 시즈나이트,": "Party cookies' equipment and Seasonite,",
    "유니크 설탕유리조각은": "unique Sugarglass Shard",
    "세부사항에서 수정할 수 있습니다": "can be changed in Details.",
    "실행:": "Run:",
    "패시브 피해": "Passive damage",
    "기본공격피해": "Basic Attack Damage",
    "특수스킬피해": "Special Skill Damage",
    "궁극기피해": "Ultimate Damage",
    "패시브스킬피해": "Passive Skill Damage",
    "기본공격 피해": "Basic Attack Damage",
    "특수스킬 피해": "Special Skill Damage",
    "패시브스킬 피해": "Passive Skill Damage",
    "기본 공격피해": "Basic Attack Damage",
    "특수 스킬피해": "Special Skill Damage",
    "패시브 스킬피해": "Passive Skill Damage",
    "기본 공격 피해": "Basic Attack Damage",
    "특수 스킬 피해": "Special Skill Damage",
    "궁극기 피해": "Ultimate Damage",
    "패시브 스킬 피해": "Passive Skill Damage",
    "표식 저항 감소": "Tag RES Reduction",
    "속성공격력": "Elemental ATK",
    "치명타확률": "CRIT Rate",
    "치명타피해": "CRIT Damage",
    "버프증폭": "Buff AMP",
    "디버프증폭": "Debuff AMP",
    "방어력관통": "Def Penetration",
    "공격력%": "ATK",
}

_SPECIAL_EXACT_ENGLISH = {
    "장비를 자동으로 두고 실행하면 오래 걸릴 수 있습니다.": "If you leave the equipment on Auto and run it, it may take a long time.",
    "달콤한 설탕 깃털로 두고 실행하는 것을 권장합니다.": "We recommend running it with Sugar Feather selected.",
    "기타 문의 : Epsilon24@gmail.com": "For inquiries: Epsilon24@gmail.com",
    "룽샤 : 불가역 20% → 10% 적용": "Mala Longxia: Irreversibility 20% → 10% applied",
    "룽샤 : 불가역 20% -> 10% 적용": "Mala Longxia: Irreversibility 20% → 10% applied",
    "불가역 20% → 10% 적용": "Irreversibility 20% → 10% applied",
    "불가역 20% -> 10% 적용": "Irreversibility 20% → 10% applied",
    "영원의 대마술사 : 모든 속성 피해 30% → 15% 적용": "Eternal Magician: All Elemental DMG 30% → 15% applied",
    "영원의 대마술사 : 모든 속성 피해 30% -> 15% 적용": "Eternal Magician: All Elemental DMG 30% → 15% applied",
    "모든 속성 피해 30% → 15% 적용": "All Elemental DMG 30% → 15% applied",
    "모든 속성 피해 30% -> 15% 적용": "All Elemental DMG 30% → 15% applied",
}

_FORCE_NAME_ENGLISH = {
    "전설의 유령해적": "Ghost Captain",
    "영원의 대마술사": "Eternal Magician",
    "유성우의 향연": "Falling Stars",
    "황금 예복": "Golden Finery",
    "달콤한 설탕 깃털": "Sugar Feather",
    "미지의 방랑자": "Mysterious Wanderer",
    "수상한 사냥꾼": "Suspicious Hunter",
    "시간관리국의 제복": "TBD Uniform",
    "플럼나이트:백마법사의 의지": "Plumite: Will of the White Mage",
    "플럼나이트:작은 성배": "Plumite: Small Chalice",
    "플럼나이트:가벼운 손길": "Plumite: Light Touch",
    "플럼나이트:번뜩이는 기지": "Plumite: Coruscating Wit",
    "플럼나이트:달빛의 속삭임": "Plumite: Moonlight Whispers",
}

def _parse_translation_text(text: str) -> dict[str, str]:
    out: dict[str, str] = {}

    def has_kr(s: str) -> bool:
        return any("가" <= ch <= "힣" for ch in str(s or ""))

    lines = []
    for raw in str(text or "").splitlines():
        line = raw.strip().strip("﻿").strip('”')
        if line and not line.startswith("#"):
            lines.append(line)

    used_as_pair_key: set[int] = set()

    # 1) 긴 안내문 / 보정문처럼 한국어 줄 다음에 영어 줄이 오는 경우를 먼저 저장
    for i in range(len(lines) - 1):
        left = lines[i]
        right = lines[i + 1]
        if has_kr(left) and not has_kr(right):
            # 오른쪽이 실제 영어 문장/문구인 경우만 pair로 사용
            if any(ch.isalpha() for ch in right):
                out[left] = right
                used_as_pair_key.add(i)

    # 2) A : B 형태의 짧은 단어 번역 저장
    for i, line in enumerate(lines):
        if i in used_as_pair_key:
            continue

        if " : " in line:
            left, right = line.split(" : ", 1)
        elif ": " in line:
            left, right = line.split(": ", 1)
        else:
            continue

        left = left.strip().strip("﻿")
        right = right.strip().strip('”')
        if not left or not right:
            continue

        # 왼쪽이 영어인 줄은 번역 키가 아니다.
        # English_fixed2.txt의 두 줄 번역에서
        # 'Mala Longxia : Irreversibility ...' 같은 영어 결과 줄을
        # 다시 번역표에 넣으면 영어 문장이 한 번 더 번역되어 중복된다.
        if not has_kr(left):
            continue

        # 오른쪽에 한글이 있으면 긴 보정문.
        # 예: '영원의 대마술사 : 모든 속성 피해 30% → 15% 적용'
        # 이걸 장비명 번역으로 저장하면 드롭다운이 깨진다.
        if has_kr(right):
            continue

        out[left] = right

    return out

@st.cache_data(show_spinner=False)
def _english_map() -> dict[str, str]:
    m = _parse_translation_text(_ENGLISH_TXT_FALLBACK)
    # repo에 English.txt / English_fixed2.txt를 같이 올린 경우에는 그 파일 번역을 우선 반영한다.
    # English_fixed2.txt가 있으면 마지막에 읽어서 기존 English.txt보다 우선 적용한다.
    for ext_name in ("English.txt", "English_fixed2.txt"):
        ext = _ASSET_ROOT / ext_name
        if ext.exists():
            try:
                m.update(_parse_translation_text(ext.read_text(encoding="utf-8")))
            except Exception:
                # 외부 번역 파일을 읽지 못하면 기본 번역만 사용한다.
                pass
    m.update(_EXTRA_ENGLISH)
    m.update(_SPECIAL_EXACT_ENGLISH)
    m.update(_FORCE_NAME_ENGLISH)
    return m

def _english_on() -> bool:
    return bool(st.session_state.get("ui_english", False))


THEME_MODE_LABELS = {
    "ko": {
        "system": "기기 설정",
        "light": "라이트 모드",
        "dark": "다크 모드",
    },
    "en": {
        "system": "Device setting",
        "light": "Light Mode",
        "dark": "Dark Mode",
    },
}

def theme_mode_label(mode: str) -> str:
    """테마 모드 이름 번역."""
    lang = "en" if _english_on() else "ko"
    return THEME_MODE_LABELS.get(lang, {}).get(mode, mode)

def _tr_sugar_slot_text(s: str) -> str:
    """설탕유리조각 조합 문구 전용 번역.


    값이 이미 일부 변환된 뒤에는 일반 'N칸' 정규식이 다시
    잡히지 않아서 '축복 20'처럼 한글이 남을 수 있다.
    그래서 조각 이름은 하드코딩 매핑으로 한 번 더 치환한다.
    """
    out = str(s or "")
    slot_names = {
        "광휘": "Brilliant",
        "관통": "Piercing",
        "축복": "Blessed",
        "낙인": "Branded",
        "원소": "Elemental",
        "파쇄": "Tearing",
    }
    for kr, en in slot_names.items():
        out = re.sub(rf"(?<![가-힣]){re.escape(kr)}(?![가-힣])", en, out)
    out = re.sub(r"(\d+)\s*칸", r"\1", out)
    return out

def _tr_one(text) -> str:
    s = "" if text is None else str(text)
    if not _english_on():
        return s

    stripped = s.strip()
    normalized_arrow = stripped.replace("->", "→")
    if s in _SPECIAL_EXACT_ENGLISH:
        return _SPECIAL_EXACT_ENGLISH[s]
    if stripped in _SPECIAL_EXACT_ENGLISH:
        left_pad = s[: len(s) - len(s.lstrip())]
        right_pad = s[len(s.rstrip()):]
        return f"{left_pad}{_SPECIAL_EXACT_ENGLISH[stripped]}{right_pad}"
    if normalized_arrow in _SPECIAL_EXACT_ENGLISH:
        left_pad = s[: len(s) - len(s.lstrip())]
        right_pad = s[len(s.rstrip()):]
        return f"{left_pad}{_SPECIAL_EXACT_ENGLISH[normalized_arrow]}{right_pad}"

    m = _english_map()
    if s in m:
        return m[s]

    if stripped in m:
        left_pad = s[: len(s) - len(s.lstrip())]
        right_pad = s[len(s.rstrip()):]
        return f"{left_pad}{m[stripped]}{right_pad}"

    # 설탕유리조각 값 문구는 일부 변환 상태에서도 조각 이름을 영어로 보정한다.
    # 단, "방어력 관통"처럼 일반 스탯 이름 안에 조각명(관통)이 들어가는 경우가 있으므로
    # 전체 번역 딕셔너리 확인이 끝난 뒤에만 부분 치환을 실행한다.
    if any(name in s for name in ("광휘", "관통", "축복", "낙인", "원소", "파쇄")):
        fixed_sugar = _tr_sugar_slot_text(s)
        if fixed_sugar != s:
            return fixed_sugar

    if " / " in s:
        return " / ".join(_tr_one(x) for x in s.split(" / "))

    shard_match = re.fullmatch(r"(.+?)\s*(\d+)칸", stripped)
    if shard_match:
        label = _tr_one(shard_match.group(1).strip())
        return f"{label} {shard_match.group(2)}"

    if ":" in s:
        parts = [x.strip() for x in s.split(":")]
        return ": ".join(_tr_one(x) for x in parts if x != "")

    if ", " in s:
        return ", ".join(_tr_one(x) for x in s.split(", "))

    out = s
    for key in sorted(m.keys(), key=len, reverse=True):
        if not key:
            continue
        if len(key) < 2:
            continue
        if key in out:
            out = out.replace(key, m[key])

    # 부분 번역 뒤에 한국어 "피해"가 남는 경우 보정
    mixed_damage_fixes = {
        "Basic Attack 피해": "Basic Attack Damage",
        "Special Skill 피해": "Special Skill Damage",
        "Ultimate 피해": "Ultimate Damage",
        "Passive Skill 피해": "Passive Skill Damage",
        "Basic AttackDamage": "Basic Attack Damage",
        "Special SkillDamage": "Special Skill Damage",
        "Passive SkillDamage": "Passive Skill Damage",
    }
    for before, after in mixed_damage_fixes.items():
        out = out.replace(before, after)

    out = _tr_sugar_slot_text(out)
    return out

def _tr_text(text) -> str:
    s = "" if text is None else str(text)
    if not _english_on():
        return s
    if "\n" in s:
        return "\n".join(_tr_one(x.strip()) for x in s.splitlines())
    return _tr_one(s)

def _tr_html(text) -> str:
    return _html.escape(_tr_text(text))

def _tr_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty or not _english_on():
        return df
    out = df.copy()
    out.columns = [_tr_one(c) for c in out.columns]
    for c in out.columns:
        out[c] = out[c].map(lambda x: _tr_text(x) if isinstance(x, str) else x)
    return out

def _auto_wrap_label_class(label: str) -> str:
    """영어 모드에서 긴 라벨만 단어 단위 줄바꿈을 허용한다."""
    raw = str(label or "")
    translated = _tr_text(raw)
    targets = {
        "유니크 설탕유리조각",
        "Unique Sugarglass Shard",
        "메인 유니크 설탕유리조각",
        "Main Unique Sugarglass Shard",
        "계산 보정 안내",
        "Calculation Adjustment Guide",
    }
    return " label-word-wrap" if raw in targets or translated in targets else ""

def render_ctl_label(label: str):
    wrap_cls = _auto_wrap_label_class(label)
    st.markdown(f'<div class="ctl-label{wrap_cls}">{_tr_html(label)}</div>', unsafe_allow_html=True)
