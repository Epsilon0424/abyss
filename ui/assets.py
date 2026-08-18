"""자산 및 아이콘 보조 함수"""
import base64
import html as _html
import io
from pathlib import Path

import streamlit as st
from PIL import ImageChops, ImageDraw

from ui.translations import _tr_text

_ASSET_ROOT = Path(__file__).resolve().parent.parent
_IMG_ROOT = _ASSET_ROOT / "img"

_ELEMENT_ICON = {
    "전체": _IMG_ROOT / "속성" / "ALL.png",
    "어둠": _IMG_ROOT / "속성" / "어둠일러스트.png",
    "빛": _IMG_ROOT / "속성" / "빛일러스트.png",
    "불": _IMG_ROOT / "속성" / "불일러스트.png",
    "물": _IMG_ROOT / "속성" / "물일러스트.png",
    "바람": _IMG_ROOT / "속성" / "바람일러스트.png",
    "대지": _IMG_ROOT / "속성" / "대지일러스트.png",
    "신비": _IMG_ROOT / "속성" / "신비일러스트.png",
}

_THEME_ICON_CANDIDATES = {
    "system": ("기기설정", "자동", "Device setting", "System"),
    "light": ("라이트모드", "라이트 모드", "Light Mode", "Light"),
    "dark": ("다크모드", "다크 모드", "Dark Mode", "Dark"),
}

_LANGUAGE_ICON = {
    "한국어": _IMG_ROOT / "언어" / "한국어.png",
    "English": _IMG_ROOT / "언어" / "English.png",
}

_POTENTIAL_STAT_ICON = {
    "elem_atk": _IMG_ROOT / "스탯" / "공격력.png",
    "atk_pct": _IMG_ROOT / "스탯" / "공격력%.png",
    "crit_rate": _IMG_ROOT / "스탯" / "치명타확률.png",
    "crit_dmg": _IMG_ROOT / "스탯" / "치명타피해.png",
    "armor_pen": _IMG_ROOT / "스탯" / "방어력관통.png",
    "buff_amp": _IMG_ROOT / "스탯" / "버프증폭.png",
    "debuff_amp": _IMG_ROOT / "스탯" / "디버프증폭.png",
}

# =====================================================
# 자산/아이콘 처리
# =====================================================
def _safe_img_path(p: Path | str | None) -> str | None:
    if not p:
        return None
    try:
        pp = Path(p)
        if pp.exists():
            return str(pp)
    except Exception:
        return None
    return None

@st.cache_data(show_spinner=False)
def _asset_index(folder: str) -> dict:
    """PNG 자산 목록 캐시"""
    base = _IMG_ROOT / folder
    if not base.exists():
        return {"base": str(base), "stems": [], "by_stem": {}}
    by_stem = {}
    stems = []
    for f in base.glob("*.png"):
        stem = f.stem
        stems.append(stem)
        by_stem[stem] = str(f)
    return {"base": str(base), "stems": stems, "by_stem": by_stem}

def _norm_key(s: str) -> str:
    return (s or "").strip().replace(":", " ").replace("  ", " ")

def _find_png_by_name(folder: str, name: str) -> str | None:
    """PNG 자산 경로 탐색"""
    if not name:
        return None

    idx = _asset_index(folder)
    by_stem: dict = idx.get("by_stem", {}) or {}
    stems: list[str] = idx.get("stems", []) or []

    n0 = str(name).strip()
    n = _norm_key(n0)

    cands = []
    cands.append(n0)
    cands.append(n)
    cands.append(_norm_key(n0.replace(" 세트", "")))
    cands.append(_norm_key(n0.replace("세트", "")))
    if n0.endswith("복"):
        cands.append(_norm_key(n0[:-1]))
    cands = [c.strip() for c in cands if c and str(c).strip()]

    for cand in cands:
        p = by_stem.get(cand)
        if p:
            return p
        p2 = by_stem.get(cand.replace(":", " "))
        if p2:
            return p2

    best = None
    best_score = -1
    nn = _norm_key(n0)
    for stem in stems:
        s = _norm_key(stem)
        if not s:
            continue
        if (s in nn) or (nn in s):
            score = min(len(s), len(nn))
            if score > best_score:
                best_score = score
                best = stem
    if best and best in by_stem:
        return by_stem[best]
    return None

def _icon_for_element(element: str) -> str | None:
    return _safe_img_path(_ELEMENT_ICON.get(element) or _ELEMENT_ICON.get("전체"))

def _icon_for_cookie(cookie: str, cookie_element_map: dict) -> str | None:
    el = cookie_element_map.get(cookie, "전체")
    return _icon_for_element(el if el else "전체")

def _icon_for_seaz(seaz: str) -> str | None:
    return _find_png_by_name("시즈나이트", seaz)

def _icon_for_equip(equip: str) -> str | None:
    e = str(equip).strip()
    if e == "자동":
        p = _find_png_by_name("장비", "자동")
        return p
    return _find_png_by_name("장비", e)

def _icon_for_role(role_name: str) -> str | None:
    return _find_png_by_name("유형", role_name)

def _icon_for_theme(theme_mode: str) -> str | None:
    """테마 선택 아이콘"""
    mode = theme_mode if theme_mode in _THEME_ICON_CANDIDATES else "system"
    direct_files = {
        "system": ("기기설정.png", "기기 설정.png", "자동.png", "system.png", "System.png", "Device setting.png"),
        "light": ("라이트모드.png", "라이트 모드.png", "light.png", "Light.png"),
        "dark": ("다크모드.png", "다크 모드.png", "dark.png", "Dark.png"),
    }

    for filename in direct_files.get(mode, ()):
        path = _IMG_ROOT / "모드" / filename
        if path.exists():
            # 데이터 주소 직접 사용 시 아이콘 보정
            # 이미지 여백·크기·마스크 보정 유지
            # 기본·세부사항 탭과 동일한 경로 기반 처리
            return str(path)

    for name in _THEME_ICON_CANDIDATES.get(mode, ()):
        found = _find_png_by_name("모드", name)
        if found:
            return found
    return None

def _icon_for_language(language_name: str) -> str | None:
    return _safe_img_path(_LANGUAGE_ICON.get(language_name) or _LANGUAGE_ICON.get("한국어"))

def _icon_for_season(season_mode: str) -> str | None:
    season_number = {
        "season1": "1",
        "season2": "2",
        "season3": "3",
        "season4": "4",
    }.get(str(season_mode), "4")
    return _safe_img_path(_IMG_ROOT / "시즌" / f"{season_number}.png")

def _icon_for_potential_stat(stat_key: str) -> str | None:
    return _safe_img_path(_POTENTIAL_STAT_ICON.get(stat_key))

@st.cache_data(show_spinner=False)
def _img_bytes(path: str, size_px: int) -> bytes | None:
    if not path:
        return None
    try:
        pp = Path(path)
        if not pp.exists():
            return None

        data = pp.read_bytes()

        try:
            from PIL import Image, ImageFilter, ImageDraw  # type: ignore

            im = Image.open(io.BytesIO(data)).convert("RGBA")

            # 투명 여백 제거
            alpha = im.getchannel("A")
            bbox = alpha.getbbox()
            if bbox:
                im = im.crop(bbox)

            # 설정 아이콘 공통 여백 보정
            # 언어·테마·시즌 아이콘의 라운드와 표시 비율 통일
            w, h = im.size
            side = max(w, h)
            pad = max(2, int(side * 0.1))
            canvas = Image.new("RGBA", (side + pad * 2, side + pad * 2), (0, 0, 0, 0))
            ox = (canvas.size[0] - w) // 2
            oy = (canvas.size[1] - h) // 2
            canvas.paste(im, (ox, oy), im)
            im = canvas

            # 표시 크기보다 크게 렌더링 후 축소 표시
            render_px = max(int(size_px) * 8, 128)
            im = im.resize((render_px, render_px), Image.LANCZOS)

            # 선명도 보정
            im = im.filter(ImageFilter.UnsharpMask(radius=1.2, percent=210, threshold=1))

            # 언어·테마와 동일한 라운드 마스크 적용
            mask = Image.new("L", (render_px, render_px), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, render_px - 1, render_px - 1), fill=255)

            r, g, b, a = im.split()
            a = ImageChops.multiply(a, mask)
            im = Image.merge("RGBA", (r, g, b, a))

            out = io.BytesIO()
            im.save(out, format="PNG", optimize=True)
            data = out.getvalue()
        except Exception:
            # 이미지 경로/인코딩 오류가 나면 아이콘 없이 계속 표시
            pass

        return data
    except Exception:
        return None

def _icon_data_uri(icon_path: str | None, icon_px: int = 18) -> str | None:
    """아이콘 데이터 주소 변환"""
    if isinstance(icon_path, str) and icon_path.startswith("data:image"):
        return icon_path

    ip = _safe_img_path(icon_path)
    if not ip:
        return None

    data = _img_bytes(ip, int(icon_px))
    if not data:
        return None
    return f"data:image/png;base64,{base64.b64encode(data).decode('ascii')}"

def selectbox_with_left_icon(*, label: str, options: list[str], key: str, icon_path: str | None,
                             disabled: bool=False, help: str|None=None, icon_px: int = 16,
                             format_func=None, on_change=None, args=None, kwargs=None):
    # 열 배치 제거
    # - 좁은 화면 열 배치 깨짐 방지
    # 아이콘 컬럼과 선택 상자 컬럼이 위아래로 갈라지는 문제가 있음
    # - 아이콘 왼쪽 고정·선택 상자 잔여 폭 사용
    icon_src = _icon_data_uri(icon_path, icon_px)

    with st.container(key=f"iconrow_{key}"):
        if icon_src:
            safe_src = _html.escape(icon_src, quote=True)

            # 아이콘 종류별 보정 클래스·크기·위치 통합 관리
            # - 수동 장비 아이콘 확대
            # - 설정 탭 아이콘: 언어·테마 중앙 정렬
            extra_icon_class = ""
            if str(key).startswith("equip_widget__"):
                cur_val = str(st.session_state.get(key, ""))
                if cur_val and cur_val != "자동":
                    extra_icon_class += " equip-non-auto-icon"
            if str(key) in ("ui_language_widget", "ui_theme_widget", "ui_season_widget"):
                extra_icon_class += " setting-select-icon"

            st.markdown(
                f"""
                <div class='icon-slot select-icon-fixed{extra_icon_class}'>
                  <img src='{safe_src}' />
                </div>
                """,
                unsafe_allow_html=True,
            )

        sb_kwargs = dict(
            label=label,
            options=options,
            label_visibility="collapsed",
            key=key,
            disabled=disabled,
            help=help,
        )
        if callable(on_change):
            sb_kwargs["on_change"] = on_change
        if args is not None:
            sb_kwargs["args"] = args
        if kwargs is not None:
            sb_kwargs["kwargs"] = kwargs
        if callable(format_func):
            sb_kwargs["format_func"] = lambda x: _tr_text(format_func(x))
        else:
            sb_kwargs["format_func"] = _tr_text
        return st.selectbox(**sb_kwargs)
