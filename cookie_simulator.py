# =====================================================
# 가져오기
# =====================================================
"""쿠키 시뮬레이터 호환 모듈"""

from typing import Callable, Optional

from cookie import *  # noqa: F401,F403

# =====================================================
# 파티 쿠키 딜 기여도
# =====================================================
def calculate_party_damage_contributions(
    best: dict,
    *,
    support_step: int = 2,
    progress_cb: Optional[Callable[[float], None]] = None,
) -> dict:
    """파티 쿠키 딜 기여도 계산"""

    def emit(value: float) -> None:
        if not progress_cb:
            return
        try:
            progress_cb(max(0.0, min(1.0, float(value))))
        except Exception:
            pass

    if not isinstance(best, dict):
        emit(1.0)
        return {"reference_time": 0.0, "members": [], "total_damage": 0.0, "errors": []}

    main_cookie = str(best.get("cookie", "") or "").strip()
    if not main_cookie:
        emit(1.0)
        return {"reference_time": 0.0, "members": [], "total_damage": 0.0, "errors": []}

    party = []
    for name in best.get("party", []) or []:
        cookie_name = str(name or "").strip()
        if cookie_name:
            party.append(cookie_name)

    try:
        reference_time = float(best.get("cycle_total_time", 30.0) or 30.0)
    except Exception:
        reference_time = 30.0
    if reference_time <= 0:
        reference_time = 30.0

    def result_damage_for_reference(result: dict) -> float:
        try:
            dps = float(result.get("dps", 0.0) or 0.0)
        except Exception:
            dps = 0.0
        try:
            cycle_time = float(result.get("cycle_total_time", 0.0) or 0.0)
        except Exception:
            cycle_time = 0.0
        try:
            cycle_damage = float(result.get("cycle_total_damage", 0.0) or 0.0)
        except Exception:
            cycle_damage = 0.0

        if cycle_time > 0 and abs(cycle_time - reference_time) <= 1e-9 and cycle_damage > 0:
            return cycle_damage
        return dps * reference_time

    equip_by_cookie = dict(best.get("party_sets", {}) or {})
    seaz_by_cookie = dict(best.get("party_seaz", {}) or {})
    unique_by_cookie = dict(best.get("party_uniques", {}) or {})

    party_slot_settings = best.get("party_slot_settings") or []
    if not isinstance(party_slot_settings, list):
        party_slot_settings = []

    def _slot_setting(index: int) -> dict:
        if 0 <= index < len(party_slot_settings) and isinstance(party_slot_settings[index], dict):
            return party_slot_settings[index]
        return {}

    def _party_settings_for_remaining_members(remaining_team_indices: list[int]) -> tuple[dict, dict, dict]:
        sets: dict = {}
        seaz: dict = {}
        uniques: dict = {}
        for team_index in remaining_team_indices:
            if team_index == 0:
                continue
            party_index = team_index - 1
            setting = _slot_setting(party_index)
            name = str(setting.get("cookie", "") or "").strip()
            if not name:
                name = str(team[team_index] or "").strip()
            if not name:
                continue
            equip = str(setting.get("equip", "") or "").strip()
            seaz_name = str(setting.get("seaz", "") or "").strip()
            unique = str(setting.get("unique", "") or "").strip()
            if not equip:
                equip = str(equip_by_cookie.get(name, "") or "").strip()
            if not seaz_name:
                seaz_name = str(seaz_by_cookie.get(name, "") or "").strip()
            if not unique:
                unique = str(unique_by_cookie.get(name, "") or "").strip()
            if equip:
                sets[name] = equip
            if seaz_name:
                seaz[name] = seaz_name
            if unique:
                uniques[name] = unique
        return sets, seaz, uniques

    main_equip = best.get("equip") or best.get("equip_fixed") or ""
    main_seaz = best.get("seaz") or best.get("seaz_fixed") or ""
    main_unique = best.get("unique") or best.get("unique_fixed") or ""
    if main_equip:
        equip_by_cookie[main_cookie] = str(main_equip)
    if main_seaz:
        seaz_by_cookie[main_cookie] = str(main_seaz)
    if main_unique:
        unique_by_cookie[main_cookie] = str(main_unique)

    main_damage = result_damage_for_reference(best)
    members = [{
        "cookie": main_cookie,
        "damage": main_damage,
        "dps": float(best.get("dps", 0.0) or 0.0),
        "is_main": True,
    }]
    errors = []

    optimizer_map = {
        "멜랑크림 쿠키": (optimize_melan_cycle, 1),
        "흑보리맛 쿠키": (optimize_black_barley_cycle, 1),
        "샤이닝베리맛 쿠키": (optimize_shining_berry_cycle, 1),
        "피닉스페퍼 쿠키": (optimize_phoenix_pepper_cycle, 1),
        "블루멜로우맛 쿠키": (optimize_blue_mallow_cycle, 1),
        "스타더스트 쿠키": (optimize_stardust_cycle, 1),
        "잭프루트맛 쿠키": (optimize_jackfruit_cycle, 1),
        "스테인드누가맛 쿠키": (optimize_stained_nougat_cycle, 1),
        "매드시럽 쿠키": (optimize_mad_syrup_cycle, 1),
        "윈드파라거스 쿠키": (optimize_wind_cycle, 1),
        "룽샤맛 쿠키": (optimize_lungsha_cycle, 1),
        "마블베리맛 쿠키": (optimize_marble_berry_cycle, 1),
        "밀키웨이맛 쿠키": (optimize_milky_way_cycle, 1),
        "체리콜라맛 쿠키": (optimize_cherry_cola_cycle, 1),
        "이슬맛 쿠키": (optimize_isle_cycle, max(1, int(support_step))),
        "샬롯맛 쿠키": (optimize_char_cycle, max(1, int(support_step))),
        "네온데니쉬맛 쿠키": (optimize_neon_cycle, 1),
        "달빛술사 쿠키": (optimize_moonlight_cycle, 1),
    }

    if not party:
        total_damage = sum(float(row.get("damage", 0.0) or 0.0) for row in members)
        members[0]["ratio"] = 100.0 if total_damage > 0 else 0.0
        emit(1.0)
        return {
            "reference_time": reference_time,
            "members": members,
            "total_damage": total_damage,
            "errors": errors,
        }

    team = [main_cookie] + party
    party_count = len(party)

    for index, cookie_name in enumerate(party):
        # 딜러 슬롯별 세팅을 독립적으로 사용
        current_team_index = index + 1
        current_slot_setting = _slot_setting(index)
        current_equip = str(current_slot_setting.get("equip", "") or "").strip() or equip_by_cookie.get(cookie_name) or ""
        current_seaz = str(current_slot_setting.get("seaz", "") or "").strip() or seaz_by_cookie.get(cookie_name) or ""
        current_unique = str(current_slot_setting.get("unique", "") or "").strip() or unique_by_cookie.get(cookie_name) or ""

        # 메인과 같은 쿠키를 선택한 경우에도 딜러 슬롯 자체의 세팅을 사용
        if cookie_name == main_cookie:
            # 메인과 동일한 쿠키라도 별도 슬롯 세팅으로 다시 계산
            optimizer_info = optimizer_map.get(cookie_name)
            if optimizer_info is None:
                members.append({
                    "cookie": cookie_name,
                    "damage": main_damage,
                    "dps": float(best.get("dps", 0.0) or 0.0),
                    "is_main": False,
                    "same_as_main": True,
                })
                emit((index + 1) / party_count)
                continue

        optimizer_info = optimizer_map.get(cookie_name)
        if optimizer_info is None:
            errors.append(f"{cookie_name}: 지원되는 파티 기여도 계산 함수가 없습니다.")
            emit((index + 1) / party_count)
            continue

        optimizer, step = optimizer_info
        remaining_team_indices = [
            team_index
            for team_index in range(len(team))
            if team_index != current_team_index
        ]
        member_party = [team[team_index] for team_index in remaining_team_indices]
        member_party_sets, member_party_seaz, member_party_uniques = _party_settings_for_remaining_members(
            remaining_team_indices
        )

        def member_progress(value: float, *, _index=index) -> None:
            try:
                local = max(0.0, min(1.0, float(value)))
            except Exception:
                local = 0.0
            emit((_index + local) / party_count)

        try:
            result = optimizer(
                seaz_name=current_seaz or None,
                party=member_party,
                party_sets=member_party_sets,
                party_seaz=member_party_seaz,
                party_uniques=member_party_uniques,
                step=step,
                progress_cb=member_progress,
                equip_override=current_equip or None,
                unique_override=current_unique or None,
                potential_override=None,
            )
        except Exception as exc:
            errors.append(f"{cookie_name}: {exc}")
            emit((index + 1) / party_count)
            continue

        if not isinstance(result, dict):
            errors.append(f"{cookie_name}: 계산 결과가 없습니다.")
            emit((index + 1) / party_count)
            continue

        damage = result_damage_for_reference(result)
        members.append({
            "cookie": cookie_name,
            "damage": damage,
            "dps": float(result.get("dps", 0.0) or 0.0),
            "is_main": False,
        })
        emit((index + 1) / party_count)

    total_damage = sum(float(row.get("damage", 0.0) or 0.0) for row in members)
    for row in members:
        damage = float(row.get("damage", 0.0) or 0.0)
        row["ratio"] = (damage / total_damage * 100.0) if total_damage > 0 else 0.0

    emit(1.0)
    return {
        "reference_time": reference_time,
        "members": members,
        "total_damage": total_damage,
        "errors": errors,
    }
