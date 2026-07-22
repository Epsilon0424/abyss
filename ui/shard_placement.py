"""Embed the shard placement solver in the cookie-sim tab.

The UI is trimmed for cookie-sim: the 7x7 map editor and manual set-priority panel are
hidden, the board is forced to a fully-open 7x7 grid, and target sets are passed in from
the current cookie-sim result such as "축복 20칸 / 낙인 21칸".
"""

from __future__ import annotations

import base64
import html as html_lib
import json
import mimetypes
import re
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_SHARD_STATIC_DIR = _PROJECT_ROOT / "static"
_SOLVER_HTML_PATH = _SHARD_STATIC_DIR / "shard_placement.html"
_STYLE_PATH = _SHARD_STATIC_DIR / "shard_common.css"
_SOLVER_STYLE_PATH = _SHARD_STATIC_DIR / "shard_placement.css"
_SOLVER_JS_PATH = _SHARD_STATIC_DIR / "shard_placement.js"
_STATIC_IMAGE_PREFIX = "/app/static/"
_USAGE_IMAGE_DIR = _PROJECT_ROOT / "img" / "사용법"

_SET_NAME_TO_KEY = {
    "광휘": "dealer-radiance",
    "관통": "dealer-penetration",
    "원소": "striker-element",
    "파쇄": "striker-fracture",
    "축복": "supporter-blessing",
    "낙인": "supporter-brand",
    "재생": "supporter-regeneration",
    # English labels are accepted too, because the app can run in English mode.
    "Radiance": "dealer-radiance",
    "Penetration": "dealer-penetration",
    "Element": "striker-element",
    "Fracture": "striker-fracture",
    "Blessing": "supporter-blessing",
    "Brand": "supporter-brand",
    "Regeneration": "supporter-regeneration",
    "Brilliant": "dealer-radiance",
    "Piercing": "dealer-penetration",
    "Elemental": "striker-element",
    "Tearing": "striker-fracture",
    "Blessed": "supporter-blessing",
    "Branded": "supporter-brand",
    "Restoring": "supporter-regeneration",
}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _strip_emoji_text(text: str) -> str:
    text = re.sub(r"[0-9]\ufe0f?\u20e3", "", text or "")
    return re.sub(r"[\U0001F300-\U0001FAFF\u2600-\u27BF\ufe0f\u20e3]", "", text)



def _usage_image_to_data_uri(filename: str) -> str:
    """Read guide images from /img/사용법 and return a browser-safe data URI."""
    path = _USAGE_IMAGE_DIR / filename
    if not path.exists():
        return ""
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _inline_usage_modal_images(modal_html: str) -> str:
    """Make the usage modal load images from the project's img/사용법 folder."""
    if not modal_html:
        return modal_html
    files = {
        "1": "1.png",
        "2": "2.png",
        "3": "3.JPG",
        "4": "4.JPG",
        "5": "5.JPG",
        "D5": "D5.JPG",
        "E1": "E1.png",
        "E2": "E2.png",
        "E3": "E3.JPG",
        "E4": "E4.JPG",
        "E5": "E5.JPG",
        "DE5": "DE5.JPG",
    }
    for number, filename in files.items():
        data_uri = _usage_image_to_data_uri(filename)
        if not data_uri:
            continue
        patterns = [
            rf'src="../img/사용법/{re.escape(filename)}"',
            rf'src="../../img/사용법/{re.escape(filename)}"',
            rf'src="/app/img/사용법/{re.escape(filename)}"',
            rf'src="img/사용법/{re.escape(filename)}"',
            rf'src="images/{number}.png"',
            rf'src="images/usage_{number}.png"',
        ]
        for pattern in patterns:
            modal_html = re.sub(pattern, f'src="{data_uri}"', modal_html)
    return modal_html


def _theme_class(theme_mode: str | None = None) -> str:
    mode = str(theme_mode or st.session_state.get("ui_theme", "system") or "system").strip().lower()
    return mode if mode in {"light", "dark", "system"} else "system"


def _english_enabled(value: bool | None = None) -> bool:
    if value is not None:
        return bool(value)
    return bool(st.session_state.get("ui_english", False)) or st.session_state.get("ui_language_widget") == "English"


_SHARD_UI_TEXT = {
    "ko": {
        "section_pill": "조각 배치",
        "auto_title": "조각 자동 배치",
        "auto_desc": "입력한 조각으로 7×7 맵을 자동으로 채웁니다. 다시 시작하려면 '조각 초기화'를 클릭해주세요.",
        "solve": "자동 배치 실행",
        "clear": "조각 초기화",
        "upload_title": "사진에서 자동 인식",
        "upload_help": "조각 이미지를 업로드하면 자동으로 모양을 분석해줍니다. 여러 장 업로드 할 수 있습니다.",
        "upload": "이미지 업로드",
        "usage": "사용법",
        "result_title": "배치 결과",
        "result_empty": "자동 배치를 실행하면 여기에 최적 배치가 표시됩니다.",
        "pieces_title": "보유 조각 입력",
        "target_desc": "설탕유리조각 세트효과: <b>{target}</b>",
        "target_fallback": "설탕유리조각 세트효과를 찾지 못하면 기존 계산 방식으로 배치합니다.",
        "missing_html": "solver.html 파일을 찾을 수 없습니다.",
        "missing_path": "static/shard_placement.html 경로를 확인해주세요.",
    },
    "en": {
        "section_pill": "Shard Placement",
        "auto_title": "Auto Shard Placement",
        "auto_desc": "Automatically fills the 7×7 board with your entered shards. Click 'Reset Shards' to start over.",
        "solve": "Run Auto Placement",
        "clear": "Reset Shards",
        "upload_title": "Auto Recognition from Images",
        "upload_help": "Upload shard images and the app will analyze their shapes automatically. Multiple images are supported.",
        "upload": "Upload Images",
        "usage": "Guide",
        "result_title": "Placement Result",
        "result_empty": "Run auto placement to show the best layout here.",
        "pieces_title": "Owned Shards",
        "target_desc": "Sugar glass shard set effect: <b>{target}</b>",
        "target_fallback": "If the sugar glass shard set effect is not found, the existing placement method will be used.",
        "missing_html": "solver.html was not found.",
        "missing_path": "Please check the static/shard_placement.html path.",
    },
}


def _shard_texts(english: bool) -> dict[str, str]:
    return _SHARD_UI_TEXT["en" if english else "ko"]


_SET_NAME_EN = {
    "광휘": "Radiance",
    "관통": "Penetration",
    "원소": "Element",
    "파쇄": "Fracture",
    "축복": "Blessing",
    "낙인": "Brand",
    "재생": "Regeneration",
}


def _translate_target_label(target_text: str, english: bool) -> str:
    text = str(target_text or "").strip()
    if not english:
        return text or "자동"
    if not text:
        return "Auto"
    for ko, en in _SET_NAME_EN.items():
        text = text.replace(ko, en)
    text = re.sub(r"(\d+)\s*칸", r"\1 cells", text)
    return text


def _usage_image_src(filename: str) -> str:
    return _usage_image_to_data_uri(filename) or f"../img/사용법/{filename}"


def _build_usage_modal(english: bool) -> str:
    def h(text: str) -> str:
        return html_lib.escape(text)

    if english:
        sections = [
            ("1. Capture the game screen", 'Go to the shown path and capture the <strong class="usage-keyword">shard screen</strong>.', [("E1.png", "Shard placement path"), ("E2.png", "Shard inventory filter")], True),
            ("2. Select set effect and capture", "", [("E3.JPG", "Filter screen"), ("E4.JPG", "Filtered result")], False),
            ("3. Upload images", 'Click <strong class="usage-keyword">Upload Images</strong> and select your captured images.<br>You can upload multiple images at once.', [], False),
            ("4. Auto recognition", 'The app automatically recognizes shards from the uploaded images.<br>It analyzes each shard’s <strong class="usage-keyword">shape</strong> and <strong class="usage-keyword">grade</strong>.', [], False),
            ("5. Select set", 'Select the <strong class="usage-keyword">set</strong> for the recognized shards.<br>You can select a different set for each image.', [("E5.JPG", "Set selection", "light"), ("DE5.JPG", "Set selection", "dark")], False),
            ("6. Confirm input", 'The recognized shard counts are entered automatically.<br>You can <strong class="usage-keyword">edit</strong> them manually if needed.', [], False),
            ("7. Run auto placement", 'Click <strong class="usage-keyword">Run Auto Placement</strong> to calculate the best layout.', [], False),
        ]
    else:
        sections = [
            ("1. 게임 화면 캡처", '해당 경로로 이동해서 <strong class="usage-keyword">조각 화면</strong>을 캡처합니다.', [("1.png", "조각 보관함 화면"), ("2.png", "이미지 업로드 버튼")], True),
            ("2. 세트 효과 선택 및 캡처", "", [("3.JPG", "자동 인식 중"), ("4.JPG", "세트 선택 화면")], False),
            ("3. 이미지 업로드", '<strong class="usage-keyword">이미지 업로드</strong> 버튼을 클릭하고 캡처한 이미지를 선택합니다.<br>여러 장의 이미지를 동시에 선택할 수 있습니다.', [], False),
            ("4. 자동 인식", '업로드된 이미지에서 조각들을 자동으로 인식합니다.<br>조각의 <strong class="usage-keyword">모양</strong>과 <strong class="usage-keyword">등급</strong>이 자동으로 분석됩니다.', [], False),
            ("5. 세트 선택", '인식된 조각들의 <strong class="usage-keyword">세트</strong>를 선택합니다.<br><strong class="usage-keyword">사진마다 다른 세트</strong>를 선택할 수 있습니다.', [("5.JPG", "세트 선택 화면", "light"), ("D5.JPG", "세트 선택 화면", "dark")], False),
            ("6. 입력 완료", '인식된 조각들의 개수가 자동으로 입력됩니다.<br>필요하면 수동으로 <strong class="usage-keyword">수정</strong>할 수 있습니다.', [], False),
            ("7. 자동 배치 실행", '<strong class="usage-keyword">자동 배치 실행</strong> 버튼을 클릭하면 최적 배치를 계산합니다.', [], False),
        ]

    section_html = []
    for idx, (title, body, images, grid) in enumerate(sections):
        mb = "0" if idx == len(sections) - 1 else "18px"
        section_html.append(f'<div class="usage-section usage-step-{idx + 1}" style="margin-bottom:{mb};">')
        section_html.append(f'<h3 class="usage-heading">{h(title)}</h3>')
        if body:
            section_html.append(f'<p class="usage-copy">{body}</p>')
        if images:
            if grid:
                section_html.append('<div class="usage-image-pair">')
                for image in images:
                    filename, alt = image[0], image[1]
                    theme = image[2] if len(image) > 2 else ""
                    theme_cls = f" usage-img-theme-{theme}" if theme else ""
                    section_html.append(f'<img src="{_usage_image_src(filename)}" alt="{h(alt)}" class="usage-img{theme_cls}">')
                section_html.append('</div>')
            else:
                for image in images:
                    filename, alt = image[0], image[1]
                    theme = image[2] if len(image) > 2 else ""
                    theme_cls = f" usage-img-theme-{theme}" if theme else ""
                    section_html.append(f'<img src="{_usage_image_src(filename)}" alt="{h(alt)}" class="usage-img usage-img-single{theme_cls}">')
        section_html.append('</div>')

    modal_markup = f'''
<div id="usage-modal" style="display:none;position:fixed;z-index:1000;left:0;top:0;width:100%;height:100%;background-color:rgba(0,0,0,0.7);overflow:auto;">
    <div class="usage-modal-box">
        <span id="close-modal" class="usage-close">&times;</span>
        {''.join(section_html)}
    </div>
</div>
'''

    # Streamlit components.html is rendered inside an iframe. A fixed modal inside that
    # iframe is limited to the shard-placement panel, so clone the guide into the parent
    # document when same-origin access is available. The in-frame modal remains as a
    # fallback for environments that block parent document access.
    parent_modal_script = r'''
<script>
(function () {
    const HOST_ID = 'cs-usage-guide-parent-host';
    let parentHost = null;
    let parentBodyOverflow = '';
    let escapeHandler = null;

    function isDarkTheme() {
        return document.body.classList.contains('cs-theme-dark') || (
            document.body.classList.contains('cs-theme-system') &&
            window.matchMedia &&
            window.matchMedia('(prefers-color-scheme: dark)').matches
        );
    }

    function closeParentUsageModal() {
        if (escapeHandler) {
            try {
                window.parent.document.removeEventListener('keydown', escapeHandler, true);
                document.removeEventListener('keydown', escapeHandler, true);
            } catch (_) {}
            escapeHandler = null;
        }
        if (parentHost && parentHost.isConnected) {
            parentHost.remove();
        }
        parentHost = null;
        try {
            window.parent.document.body.style.overflow = parentBodyOverflow;
        } catch (_) {}
    }

    function openInFrameFallback() {
        const usageModal = document.getElementById('usage-modal');
        if (usageModal) usageModal.style.display = 'block';
    }

    function openParentUsageModal() {
        const sourceBox = document.querySelector('#usage-modal .usage-modal-box');
        if (!sourceBox) {
            openInFrameFallback();
            return;
        }

        try {
            const parentDocument = window.parent.document;
            const parentBody = parentDocument.body;
            if (!parentBody || window.parent === window) {
                openInFrameFallback();
                return;
            }

            const existingHost = parentDocument.getElementById(HOST_ID);
            if (existingHost) {
                parentBody.style.overflow = existingHost.dataset.previousBodyOverflow || '';
                existingHost.remove();
            }

            const host = parentDocument.createElement('div');
            host.id = HOST_ID;
            host.style.position = 'fixed';
            host.style.inset = '0';
            host.style.zIndex = '2147483647';
            host.style.display = 'block';
            host.style.pointerEvents = 'auto';

            const shadow = host.attachShadow({ mode: 'open' });
            const dark = isDarkTheme();
            shadow.innerHTML = `
<style>
:host { all: initial; }
*, *::before, *::after { box-sizing: border-box; }
.overlay {
    position: fixed;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: clamp(16px, 3vw, 32px);
    background: rgba(0, 0, 0, 0.7);
    font-family: Arial, Helvetica, sans-serif;
    color: #111827;
    overflow: hidden;
    overscroll-behavior: contain;
}
.dialog {
    position: relative;
    width: min(550px, calc(100vw - 32px));
    max-width: 550px;
    max-height: min(90vh, calc(100vh - 32px));
    overflow-y: auto;
    overscroll-behavior: contain;
    padding: clamp(12px, 4vw, 24px);
    border-radius: clamp(8px, 2.4vw, 15px);
    background: #ffffff;
    color: #111827;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.25);
    scrollbar-width: thin;
    scrollbar-color: #999ca4 transparent;
}
.dialog::-webkit-scrollbar { width: 4px; }
.dialog::-webkit-scrollbar-track { background: transparent; border-radius: 10px; }
.dialog::-webkit-scrollbar-thumb { background: #999ca4; border-radius: 10px; }
.close {
    position: absolute;
    right: 20px;
    top: 20px;
    z-index: 2;
    border: 0;
    padding: 0;
    background: transparent;
    color: #6b7280;
    font: 800 20px/1 Arial, Helvetica, sans-serif;
    cursor: pointer;
}
.usage-section { margin-bottom: clamp(10px, 3vw, 18px) !important; }
.usage-section:last-child { margin-bottom: 0 !important; }
.usage-heading {
    margin: 0 0 8px;
    color: #ff4048;
    font-size: 13px;
    line-height: 1.35;
    font-weight: 800;
}
.usage-copy {
    margin: 0 0 8px;
    color: #4b5563;
    font-size: 11px;
    line-height: 1.5;
}
.usage-keyword { color: inherit; font-weight: 800; }
.usage-image-pair {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    column-gap: clamp(4px, 2vw, 10px);
    row-gap: 0;
    width: 100%;
    max-width: 500px;
    margin: 0 0 clamp(10px, 3vw, 16px);
    align-items: start;
}
.usage-img {
    display: block;
    width: 100%;
    max-width: 100%;
    height: auto;
    border-radius: clamp(4px, 1.8vw, 10px);
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}
.usage-img-single {
    max-width: 500px;
    margin: 0 0 clamp(10px, 3vw, 16px);
}
.usage-step-2 .usage-img-single:first-of-type {
    margin-bottom: clamp(4px, 2vw, 10px) !important;
}
.usage-img-theme-light { display: block; }
.usage-img-theme-dark { display: none; }
.overlay.dark .dialog {
    background: #303236;
    color: #f3f4f6;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.55);
    scrollbar-color: #6b7280 #303236;
}
.overlay.dark .dialog::-webkit-scrollbar-track { background: #303236; }
.overlay.dark .dialog::-webkit-scrollbar-thumb { background: #6b7280; }
.overlay.dark .usage-copy { color: #cbd5e1; }
.overlay.dark .close { color: #cbd5e1; }
.overlay.dark .usage-img-theme-light { display: none; }
.overlay.dark .usage-img-theme-dark { display: block; }
@media (max-width: 640px) {
    .overlay { align-items: flex-start; padding: 12px; }
    .dialog {
        width: 100%;
        max-height: calc(100vh - 24px);
        padding: 16px;
        border-radius: 12px;
    }
    .close { right: 16px; top: 16px; }
}
</style>
<div class="overlay ${dark ? 'dark' : 'light'}" role="presentation">
    <div class="dialog" role="dialog" aria-modal="true" aria-label="Usage guide">
        <button class="close" type="button" aria-label="Close">&times;</button>
        ${sourceBox.innerHTML.replace(/<span[^>]*id=["']close-modal["'][^>]*>[\s\S]*?<\/span>/i, '')}
    </div>
</div>`;

            parentBodyOverflow = parentBody.style.overflow;
            host.dataset.previousBodyOverflow = parentBodyOverflow;
            parentBody.style.overflow = 'hidden';
            parentBody.appendChild(host);
            parentHost = host;

            const overlay = shadow.querySelector('.overlay');
            const dialog = shadow.querySelector('.dialog');
            const closeButton = shadow.querySelector('.close');
            closeButton?.addEventListener('click', closeParentUsageModal);
            overlay?.addEventListener('click', (event) => {
                if (event.target === overlay) closeParentUsageModal();
            });
            dialog?.addEventListener('click', (event) => event.stopPropagation());

            escapeHandler = (event) => {
                if (event.key === 'Escape') closeParentUsageModal();
            };
            parentDocument.addEventListener('keydown', escapeHandler, true);
            document.addEventListener('keydown', escapeHandler, true);
        } catch (_) {
            closeParentUsageModal();
            openInFrameFallback();
        }
    }

    const usageButton = document.getElementById('usage-btn');
    usageButton?.addEventListener('click', (event) => {
        event.preventDefault();
        event.stopImmediatePropagation();
        openParentUsageModal();
    }, true);

    window.addEventListener('beforeunload', closeParentUsageModal);
    window.csOpenUsageModal = openParentUsageModal;
    window.csCloseUsageModal = closeParentUsageModal;
})();
</script>
'''
    return modal_markup + parent_modal_script



def _parse_sugar_targets(target_text: str) -> tuple[list[str], dict[str, int]]:
    """Parse strings like '축복 20칸 / 낙인 21칸' into solver set keys/counts."""
    priority: list[str] = []
    counts: dict[str, int] = {}
    text = str(target_text or "")
    for name, count in re.findall(r"([A-Za-z가-힣]+)\s*(\d+)\s*(?:칸)?", text):
        key = _SET_NAME_TO_KEY.get(name.strip())
        if not key:
            continue
        if key not in priority:
            priority.append(key)
        try:
            counts[key] = int(count)
        except Exception:
            pass
    return priority, counts


def _extract_modal(html: str, modal_id: str) -> str:
    """Extract one top-level modal block from solver.html by id."""
    marker = f'<div id="{modal_id}"'
    start = html.find(marker)
    if start < 0:
        return ""
    next_script = html.find("<script", start)
    block = html[start: next_script if next_script >= 0 else len(html)]
    # If two modal blocks were included, keep only the first for usage-modal.
    if modal_id == "usage-modal":
        next_modal = block.find('<div id="debug-modal"')
        if next_modal >= 0:
            block = block[:next_modal]
    return block.strip()


def _patch_solver_js(js: str, english: bool = False) -> str:
    """Patch only the glue behavior; keep the solver/photo logic intact."""
    if not js:
        return js

    # Show only the single best result in the cookie-sim embed.
    js = js.replace("const MAX_SOLUTIONS = 10;", "const MAX_SOLUTIONS = 1;", 1)

    # cookie-sim: remove all decorative icons/emojis from the embedded solver.
    js = re.sub(r"(name: '[^']+', color: '#[0-9A-Fa-f]+', icon: )'[^']+'", r"\1''", js)
    js = js.replace("rare: { label: '레어'", "rare: { label: '레어'")
    js = js.replace("epic: { label: '에픽'", "epic: { label: '에픽'")
    js = js.replace("super: { label: '슈퍼'", "super: { label: '슈퍼에픽'")
    js = js.replace("name: '유니크'", "name: '유니크'")
    js = js.replace("uniqueLabel.textContent = '유니크';", "uniqueLabel.textContent = '유니크';")
    js = js.replace("uploadStatus.textContent = '이미지 분석 준비 완료';", "uploadStatus.textContent = '이미지 분석 준비 완료';")
    js = js.replace("uploadStatus.textContent = '조각 정보를 찾을 수 없습니다. 이미지가 선명한지 확인해주세요.';", "uploadStatus.textContent = '조각 정보를 찾을 수 없습니다. 이미지가 선명한지 확인해주세요.';")
    js = js.replace('uploadStatus.textContent = `${imagesData.length}개 이미지의 조각 세트를 선택해주세요...`;', 'uploadStatus.textContent = `${imagesData.length}개 이미지의 조각 세트를 선택해주세요...`;')
    js = js.replace("uploadStatus.textContent = '세트 선택이 취소되었습니다.';", "uploadStatus.textContent = '세트 선택이 취소되었습니다.';")
    js = js.replace('uploadStatus.textContent = `${files.length}장 분석 완료! ${finalResults.length}개 종류, 총 ${totalPieces}개의 조각을 인식했습니다!`;', 'uploadStatus.textContent = `${files.length}장 분석 완료! ${finalResults.length}개 종류, 총 ${totalPieces}개의 조각을 인식했습니다!`;')
    js = js.replace("uploadStatus.textContent = `이미지 분석 실패: ${error.message || '알 수 없는 오류'}.`;", "uploadStatus.textContent = `이미지 분석 실패: ${error.message || '알 수 없는 오류'}.`;")
    js = js.replace('solutionSummary.textContent = `맵을 먼저 만들어주세요!`;', 'solutionSummary.textContent = `맵을 먼저 만들어주세요!`;')
    js = js.replace('solutionSummary.textContent = `조각을 먼저 입력해주세요!`;', 'solutionSummary.textContent = ``;')
    js = js.replace('solutionSummary.textContent = `계산 중... (맵 ${targetCellCount}칸, 조각 ${piecesToUse.length}개, 총 ${piecesCellCount}칸, 최대 ${MAX_UNIQUE_PIECES}유니크+${MAX_REGULAR_PIECES}일반 사용)`;', 'solutionSummary.textContent = `계산 중... (맵 ${targetCellCount}칸, 조각 ${piecesToUse.length}개, 총 ${piecesCellCount}칸, 최대 ${MAX_UNIQUE_PIECES}유니크+${MAX_REGULAR_PIECES}일반 사용)`;')
    js = js.replace('solutionSummary.textContent = `${solutionCount}개의 유효한 조합을 찾았습니다!${priorityInfo} (최고 저항: ${bestSol.totalResistance}, ${maxFilled}/${totalCells}칸, ${elapsed}초)`;', 'solutionSummary.textContent = `${solutionCount}개의 유효한 조합을 찾았습니다!${priorityInfo} (최고 저항: ${bestSol.totalResistance}, ${maxFilled}/${totalCells}칸, ${elapsed}초)`;')
    js = js.replace('solutionSummary.textContent = `배치 방법을 찾지 못했습니다. (${elapsed}초)`;', 'solutionSummary.textContent = `배치 방법을 찾지 못했습니다. (${elapsed}초)`;')
    js = js.replace("setIcon = '';", "setIcon = '';")


    if english:
        replacements = {
            "name: '광휘'": "name: 'Brilliant'",
            "name: '관통'": "name: 'Piercing'",
            "name: '원소'": "name: 'Elemental'",
            "name: '파쇄'": "name: 'Tearing'",
            "name: '축복'": "name: 'Blessed'",
            "name: '낙인'": "name: 'Branded'",
            "name: '재생'": "name: 'Restoring'",
            "rare: { label: '레어'": "rare: { label: 'Rare'",
            "epic: { label: '에픽'": "epic: { label: 'Epic'",
            "super: { label: '슈퍼에픽'": "super: { label: 'Super Epic'",
            "name: '유니크'": "name: 'Unique'",
            "uniqueLabel.textContent = '유니크';": "uniqueLabel.textContent = 'Unique';",
            "uploadStatus.textContent = '이미지 로딩 중...';": "uploadStatus.textContent = 'Loading image analyzer...';",
            "uploadStatus.textContent = '이미지 분석 준비 완료';": "uploadStatus.textContent = 'Image analysis ready';",
            "uploadStatus.textContent = '조각 정보를 찾을 수 없습니다. 이미지가 선명한지 확인해주세요.';": "uploadStatus.textContent = 'No shard information was found. Please check that the image is clear.';",
            "uploadStatus.textContent = `${imagesData.length}개 이미지의 조각 세트를 선택해주세요...`;": "uploadStatus.textContent = `Select shard sets for ${imagesData.length} image(s)...`;",
            "uploadStatus.textContent = '세트 선택이 취소되었습니다.';": "uploadStatus.textContent = 'Set selection was canceled.';",
            "uploadStatus.textContent = `${files.length}장의 이미지 분석 중...`;": "uploadStatus.textContent = `Analyzing ${files.length} image(s)...`;",
            "uploadStatus.textContent = ` ${files.length}장 분석 완료! ${finalResults.length}개 종류, 총 ${totalPieces}개의 조각을 인식했습니다!`;": "uploadStatus.textContent = `Analysis complete for ${files.length} image(s). Recognized ${finalResults.length} type(s), ${totalPieces} shard(s) total.`;",
            "uploadStatus.textContent = `${files.length}장 분석 완료! ${finalResults.length}개 종류, 총 ${totalPieces}개의 조각을 인식했습니다!`;": "uploadStatus.textContent = `Analysis complete for ${files.length} image(s). Recognized ${finalResults.length} type(s), ${totalPieces} shard(s) total.`;",
            "modalTitle.textContent = '조각 선택';": "modalTitle.textContent = 'Select Shard';",
            "closeBtn.textContent = '닫기';": "closeBtn.textContent = 'Close';",
            "selectButton.textContent = hasGreenTag ? '장착중 조각 선택' : '조각 선택';": "selectButton.textContent = hasGreenTag ? 'Select Equipped Shard' : 'Select Shard';",
            "prompt('개수를 입력하세요.'": "prompt('Enter a count.'",
            "uploadStatus.textContent = `이미지 분석 실패: ${error.message || '알 수 없는 오류'}.`;": "uploadStatus.textContent = `Image analysis failed: ${error.message || 'Unknown error'}.`;",
            "solutionSummary.textContent = `맵을 먼저 만들어주세요!`;": "solutionSummary.textContent = `Create a board first.`;",
            "solutionSummary.textContent = `계산 중... (맵 ${targetCellCount}칸, 조각 ${piecesToUse.length}개, 총 ${piecesCellCount}칸, 최대 ${MAX_UNIQUE_PIECES}유니크+${MAX_REGULAR_PIECES}일반 사용)`;": "solutionSummary.textContent = `Calculating... (board ${targetCellCount} cells, ${piecesToUse.length} shards, ${piecesCellCount} cells total, max ${MAX_UNIQUE_PIECES} unique + ${MAX_REGULAR_PIECES} regular)`;",
            "solutionSummary.textContent = `${solutionCount}개의 유효한 조합을 찾았습니다!${priorityInfo} (최고 저항: ${bestSol.totalResistance}, ${maxFilled}/${totalCells}칸, ${elapsed}초)`;": "solutionSummary.textContent = `Found ${solutionCount} valid layout(s)!${priorityInfo} (best resistance: ${bestSol.totalResistance}, ${maxFilled}/${totalCells} cells, ${elapsed}s)`;",
            "solutionSummary.textContent = `배치 방법을 찾지 못했습니다. (${elapsed}초)`;": "solutionSummary.textContent = `No placement found. (${elapsed}s)`;",
            "title.textContent = '사진별 세트 선택';": "title.textContent = 'Select Set by Image';",
            "description.innerHTML = `<strong>${imagesData.length}장의 사진</strong>에서 인식된 조각들입니다.<br>각 사진마다 세트를 선택하면 해당 사진의 모든 조각이 선택한 세트로 들어갑니다.`;": "description.innerHTML = `<strong>${imagesData.length} image(s)</strong> recognized.<br>Select a set for each image and all shards in that image will use that set.`;",
            "defaultOption.textContent = '세트를 선택하세요';": "defaultOption.textContent = 'Select a set';",
            "piecesTitle.textContent = `인식된 조각 (총 ${pieces.length}종류)`;": "piecesTitle.textContent = `Recognized Shards (${pieces.length} type(s))`;",
            "confirmBtn.textContent = '모든 사진 확인';": "confirmBtn.textContent = 'Confirm All Images';",
            "const confirmed = confirm('장착 중인 조각은 인식이 어려울 수 있습니다. 모든 조각을 확인해 주세요.');": "const confirmed = confirm('Equipped shards may be difficult to recognize. Please check that no shards are missing.');",
            "alert('모든 사진의 세트를 선택해주세요!');": "alert('Please select a set for every image.');",
            "cancelBtn.textContent = '취소';": "cancelBtn.textContent = 'Cancel';",
            "tabDesc.innerHTML = `이 사진의 모든 조각이 들어갈 세트:`;": "tabDesc.innerHTML = `Set for all shards in this image:`;",
            "setLabel.textContent = '세트를 선택하세요';": "setLabel.textContent = 'Select a set';",
            "setLabel.textContent = '이 사진의 모든 조각이 들어갈 세트:';": "setLabel.textContent = 'Set for all shards in this image:';",
            "setChip.textContent = '세트 선택';": "setChip.textContent = 'Select Set';",
            "normalSetChip.textContent = '세트 선택';": "normalSetChip.textContent = 'Select Set';",
            "manualSetChip.textContent = '세트 선택';": "manualSetChip.textContent = 'Select Set';",
            "btn.title = '이 조각 삭제';": "btn.title = 'Remove this shard';",
            "addLabel.textContent = '조각 추가';": "addLabel.textContent = 'Add Shard';",
            "gTitle.textContent = '추가할 조각의 등급 선택';": "gTitle.textContent = 'Select the grade of the shard to add';",
            "const csManualGradeDefs = [{ key: 'rare', label: '레어', color: '#5d8cff' }, { key: 'epic', label: '에픽', color: '#b46bff' }, { key: 'super', label: '슈퍼에픽', color: '#ff5b66' }];": "const csManualGradeDefs = [{ key: 'rare', label: 'Rare', color: '#5d8cff' }, { key: 'epic', label: 'Epic', color: '#b46bff' }, { key: 'super', label: 'Super Epic', color: '#ff5b66' }];",
            "이미지 ${imageIndex + 1}": "Image ${imageIndex + 1}",
            "해결책을 찾지 못했습니다. 다른 조각 조합이나 더 넓은 맵을 시도해보세요.": "No solution found. Try a different shard combination or a larger board.",
            "세트 효과 보너스": "Set Effect Bonus",
            "칸 달성": "cells reached",
            "칸 단계 달성": "cell threshold reached",
            "저항": "resistance",
        }
        for old, new in replacements.items():
            js = js.replace(old, new)

    # Force all 49 cells to be usable and remove the locked middle editor behavior.
    js = js.replace(
        "initializeLockedArea();",
        """initializeLockedArea();
    if (window.COOKIE_SIM_FORCE_FULL_GRID) {
        lockedCells.clear();
        gridState.fill(true);
    }""",
        1,
    )

    # Hidden map buttons still exist, but reset should also return to full-open mode.
    js = js.replace(
        """        // Re-initialize locked area as fillable
        lockedCells.forEach(index => {
            gridState[index] = true;
        });
        createGrid();""",
        """        // cookie-sim: always use a fully-open 7x7 map
        if (window.COOKIE_SIM_FORCE_FULL_GRID) {
            lockedCells.clear();
            gridState.fill(true);
        } else {
            // Re-initialize locked area as fillable
            lockedCells.forEach(index => {
                gridState[index] = true;
            });
        }
        createGrid();""",
        1,
    )

    # Use target counts from cookie-sim when deciding when a set is already sufficiently filled.
    js = js.replace(
        """    const SET_BONUS_THRESHOLDS = [9, 12, 15, 18, 21];""",
        """    const SET_BONUS_THRESHOLDS = [9, 12, 15, 18, 21];
    const COOKIE_SIM_TARGET_COUNTS = window.COOKIE_SIM_SHARD_TARGET_COUNTS || {};
    function cookieSimTargetLimit(setKey) {
        const n = Number(COOKIE_SIM_TARGET_COUNTS[setKey]);
        return Number.isFinite(n) && n > 0 ? n : 21;
    }""",
        1,
    )

    # Replace the manual select-based priority reading with cookie-sim's automatic targets.
    js = js.replace(
        """        // 우선순위 세트 읽기 (1, 2, 3순위)
        const prioritySets = [
            document.getElementById('priority-set-1')?.value,
            document.getElementById('priority-set-2')?.value,
            document.getElementById('priority-set-3')?.value
        ].filter(s => s && s !== "");""",
        """        // cookie-sim: result tab sugar-glass target is used automatically.
        const autoPrioritySets = Array.isArray(window.COOKIE_SIM_SHARD_PRIORITY_SETS)
            ? window.COOKIE_SIM_SHARD_PRIORITY_SETS.filter(s => s && SET_INFO[s])
            : [];
        const prioritySets = autoPrioritySets.length > 0 ? autoPrioritySets : [
            document.getElementById('priority-set-1')?.value,
            document.getElementById('priority-set-2')?.value,
            document.getElementById('priority-set-3')?.value
        ].filter(s => s && s !== "");""",
        1,
    )

    js = js.replace(
        """                const isSetAMaxed = (setCellCounts[pieceA.set] || 0) >= 21;
                const isSetBMaxed = (setCellCounts[pieceB.set] || 0) >= 21;""",
        """                const isSetAMaxed = (setCellCounts[pieceA.set] || 0) >= cookieSimTargetLimit(pieceA.set);
                const isSetBMaxed = (setCellCounts[pieceB.set] || 0) >= cookieSimTargetLimit(pieceB.set);""",
        1,
    )

    # Show every set used on the board, even when it has fewer than 9 cells and gets no bonus yet.
    js = js.replace(
        """        // 세트 보너스 계산
        const { totalBonus, setBonusDetails } = calculateSetBonus(setCellCounts);
        const finalScore = score + totalBonus;""",
        """        // 세트 보너스 계산
        const { totalBonus, setBonusDetails } = calculateSetBonus(setCellCounts);
        Object.entries(setCellCounts).forEach(([setKey, cellCount]) => {
            if (!setBonusDetails[setKey]) {
                setBonusDetails[setKey] = {
                    cellCount: cellCount,
                    bonus: 0,
                    thresholds: []
                };
            }
        });
        const finalScore = score + totalBonus;""",
        1,
    )

    # Rename the original multi-solution label so the result card reads like one optimal placement.
    js = js.replace(
        """<span class="solution-number">해결책 #${solutionNumber}</span>""",
        """<span class="solution-number">최적 배치</span>""",
        1,
    )

    # Draw connected board borders as overlay lines so inner corners meet cleanly.
    js = js.replace(
        "    function renderSolution(board, totalScore = 0, solutionNumber = 1, usedPieces = [], pieceGrades = {}, pieceSets = {}, setBonusDetails = {}, baseScore = 0, setBonus = 0) {",
        r"""    
    function cookieSimAdjustBoardText(solutionGrid) {
        if (!solutionGrid) return;
        const rect = solutionGrid.getBoundingClientRect();
        if (!rect.width) return;
        const cell = rect.width / GRID_SIZE;
        const size = Math.max(6, Math.min(11, cell * 0.48));
        solutionGrid.querySelectorAll('.solution-cell').forEach(el => {
            el.style.setProperty('font-size', `${size}px`, 'important');
            el.style.setProperty('line-height', '1', 'important');
            el.style.setProperty('overflow', 'hidden', 'important');
            const span = el.querySelector('span');
            if (span) {
                span.style.setProperty('font-size', `${size}px`, 'important');
                span.style.setProperty('line-height', '1', 'important');
            }
        });
    }

    function cookieSimDrawBoardLines(solutionGrid, grid2D) {
        if (!window.COOKIE_SIM_SOLID_BOARD_LINES || !solutionGrid || !grid2D) return;
        const rect = solutionGrid.getBoundingClientRect();
        if (!rect.width || !rect.height) return;
        const cellW = rect.width / GRID_SIZE;
        const cellH = rect.height / GRID_SIZE;
        cookieSimAdjustBoardText(solutionGrid);
        const bw = 2;
        solutionGrid.style.position = 'relative';
        solutionGrid.style.overflow = 'hidden';
        Array.from(solutionGrid.querySelectorAll('.cs-board-line')).forEach(line => line.remove());
        Array.from(solutionGrid.children).forEach(child => {
            if (child.classList && child.classList.contains('solution-cell')) {
                child.style.border = '0';
                child.style.boxSizing = 'border-box';
            }
        });
        const addLine = (left, top, width, height) => {
            const line = document.createElement('div');
            line.className = 'cs-board-line';
            line.style.position = 'absolute';
            line.style.left = `${left}px`;
            line.style.top = `${top}px`;
            line.style.width = `${width}px`;
            line.style.height = `${height}px`;
            line.style.background = '#050505';
            line.style.zIndex = '5';
            line.style.pointerEvents = 'none';
            line.style.borderRadius = '0';
            solutionGrid.appendChild(line);
        };
        for (let r = 0; r <= GRID_SIZE; r++) {
            for (let c = 0; c < GRID_SIZE; c++) {
                const up = r > 0 ? grid2D[r - 1][c] : -1;
                const down = r < GRID_SIZE ? grid2D[r][c] : -1;
                if (up !== down && (up > 0 || down > 0)) {
                    addLine(c * cellW - bw / 2, r * cellH - bw / 2, cellW + bw, bw);
                }
            }
        }
        for (let c = 0; c <= GRID_SIZE; c++) {
            for (let r = 0; r < GRID_SIZE; r++) {
                const left = c > 0 ? grid2D[r][c - 1] : -1;
                const right = c < GRID_SIZE ? grid2D[r][c] : -1;
                if (left !== right && (left > 0 || right > 0)) {
                    addLine(c * cellW - bw / 2, r * cellH - bw / 2, bw, cellH + bw);
                }
            }
        }
    }

    function cookieSimScheduleBoardLines(solutionGrid, grid2D) {
        if (!window.COOKIE_SIM_SOLID_BOARD_LINES || !solutionGrid || !grid2D) return;
        const draw = () => {
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    cookieSimDrawBoardLines(solutionGrid, grid2D);
                });
            });
        };
        draw();

        if (!solutionGrid.dataset.csLineRedrawBound) {
            solutionGrid.dataset.csLineRedrawBound = '1';
            let timer = 0;
            const redraw = () => {
                clearTimeout(timer);
                timer = setTimeout(draw, 40);
            };
            window.addEventListener('resize', redraw, { passive: true });
            if (typeof ResizeObserver !== 'undefined') {
                const ro = new ResizeObserver(redraw);
                ro.observe(solutionGrid);
                solutionGrid._csLineResizeObserver = ro;
            }
        }
    }

    function renderSolution(board, totalScore = 0, solutionNumber = 1, usedPieces = [], pieceGrades = {}, pieceSets = {}, setBonusDetails = {}, baseScore = 0, setBonus = 0) {""",
        1,
    )
    js = js.replace(
        "        solutionsContainer.appendChild(solutionWrapper);",
        "        solutionsContainer.appendChild(solutionWrapper);\n        cookieSimDrawBoardLines(solutionGrid, grid2D);",
        1,
    )

    # cookie-sim: 결과 보드 색상은 등급색이 아니라 실제 세트 색상으로 표시합니다.
    js = js.replace(
        """                if (grade === 'rare') {
                    // 초록색
                    finalColor = 'hsl(120, 60%, 60%)';
                } else if (grade === 'epic') {
                    // 보라색
                    finalColor = 'hsl(280, 60%, 60%)';
                } else if (grade === 'super') {
                    // 연한 빨강
                    finalColor = 'hsl(10, 70%, 65%)';
                } else if (grade === 'unique') {
                    // 골드색 (유니크)
                    finalColor = 'hsl(45, 80%, 60%)';
                }

                cell.style.backgroundColor = finalColor;""",
        """                const pieceSetForColor = pieceSets[pieceId];
                if (grade === 'unique') {
                    finalColor = CS_UNIQUE_COLOR;
                } else if (pieceSetForColor && SET_INFO[pieceSetForColor]) {
                    finalColor = SET_INFO[pieceSetForColor].color;
                } else if (grade === 'rare') {
                    finalColor = '#5d8cff';
                } else if (grade === 'epic') {
                    finalColor = '#b46bff';
                } else if (grade === 'super') {
                    finalColor = '#ff6b6b';
                }

                cell.style.backgroundColor = finalColor;""",
        1,
    )

    # Cookie-sim result card: remove the blue optimal-placement header and move compact stats under set bonuses.
    js = js.replace("setBonusContainer.style.background = 'rgba(102, 126, 234, 0.1)';", "setBonusContainer.style.background = '#fff7f7'; setBonusContainer.classList.add('cs-set-bonus-box');")
    js = js.replace("setBonusContainer.style.borderRadius = '6px';", "setBonusContainer.style.borderRadius = '10px';")
    js = js.replace("setBonusContainer.style.marginBottom = '10px';", "setBonusContainer.style.marginBottom = '0px'; setBonusContainer.style.border = 'none'; setBonusContainer.style.width = '100%'; setBonusContainer.style.boxSizing = 'border-box'; setBonusContainer.style.textAlign = 'left';")
    js = js.replace("setBonusContainer.style.fontSize = '0.9em';", "setBonusContainer.style.fontSize = '12px';")
    js = js.replace("setBonusTitle.textContent = ' 세트 효과 보너스';", "setBonusTitle.textContent = '세트 효과 보너스';")
    js = js.replace("setBonusTitle.textContent = ' Set Effect Bonus';", "setBonusTitle.textContent = 'Set Effect Bonus';")
    js = js.replace("setBonusTitle.style.color = '#667eea';", "setBonusTitle.style.color = '#374151';")
    js = js.replace("setBonusTitle.style.fontWeight = 'bold';", "setBonusTitle.style.fontWeight = '800'; setBonusTitle.style.fontSize = '12px'; setBonusTitle.style.lineHeight = '1.35';")
    _setinfo_old = """                setInfo.style.marginLeft = '10px';
                setInfo.style.marginBottom = '3px';
                setInfo.textContent = `${SET_INFO[setKey].icon} ${SET_INFO[setKey].name}: ${details.cellCount}칸 → +${details.bonus} 저항 (${details.thresholds.join(', ')}칸 단계 달성)`;
                setBonusContainer.appendChild(setInfo);"""
    if english:
        # The translation pass above already rewrote parts of this line, so match the translated form.
        _setinfo_old = _setinfo_old.replace("칸 단계 달성", "cell threshold reached").replace("저항", "resistance")
    _cell_suffix = " cells" if english else "칸"
    js = js.replace(
        _setinfo_old,
        """                setInfo.style.marginLeft = '0';
                setInfo.style.marginBottom = '4px';
                setInfo.style.display = 'flex';
                setInfo.style.alignItems = 'center';
                setInfo.style.gap = '6px';
                setInfo.style.fontSize = '12px';
                setInfo.style.lineHeight = '1.35';
                const setColorChip = document.createElement('span');
                setColorChip.style.width = '12px';
                setColorChip.style.height = '12px';
                setColorChip.style.borderRadius = '3px';
                setColorChip.style.background = SET_INFO[setKey]?.color || '#ff4048';
                setColorChip.style.border = '1px solid rgba(17, 24, 39, 0.08)';
                setColorChip.style.flex = '0 0 12px';
                const setText = document.createElement('span');
                setText.textContent = `${SET_INFO[setKey].name}: ${details.cellCount}""" + _cell_suffix + """`;
                setInfo.appendChild(setColorChip);
                setInfo.appendChild(setText);
                setBonusContainer.appendChild(setInfo);""",
        1,
    )
    _stat_line = (
        "statInfo.textContent = `Resistance : ${totalScore}`;"
        if english else
        "statInfo.textContent = `저항 : ${totalScore}`;"
    )
    js = js.replace(
        """__COOKIE_SIM_NO_DYNAMIC_SET_BONUS_RESISTANCE_INJECTION__""",
        """            const statDivider = document.createElement('div');
            statDivider.style.height = '1px';
            statDivider.style.background = CS_DARK_UI
                ? 'rgba(243, 244, 246, 0.12)'
                : 'rgba(17, 24, 39, 0.08)';
            statDivider.style.margin = '8px 0 7px 0';
            const statInfo = document.createElement('div');
            """ + _stat_line + """
            statInfo.style.fontWeight = '800';
            statInfo.style.color = '#374151';
            statInfo.style.fontSize = '12px';
            statInfo.style.lineHeight = '1.35';
            setBonusContainer.appendChild(statDivider);
            setBonusContainer.appendChild(statInfo);
            solutionWrapper.appendChild(setBonusContainer);""",
        1,
    )

    # After resetting pieces, keep the empty result placeholder visible.
    _empty_msg = "Run auto placement to show the best layout here." if english else "자동 배치를 실행하면 여기에 최적 배치가 표시됩니다."
    js = js.replace(
        """        solutionSummary.textContent = '';
        solutionsContainer.innerHTML = '';""",
        """        solutionSummary.textContent = '';
        solutionsContainer.innerHTML = '<div class=\"cs-empty-result\">""" + _empty_msg + """</div>';""",
        1,
    )

    # Mark only equipped/green-tag pieces so the UI can give them a thin dashed border.
    js = js.replace(
        """                            pieceBlock.dataset.isFailed = 'true';
                            pieceBlock.dataset.count = '1';""",
        """                            pieceBlock.dataset.isFailed = 'true';
                            pieceBlock.dataset.hasGreenTag = hasGreenTag ? 'true' : 'false';
                            pieceBlock.dataset.grade = failedGrade || '';
                            pieceBlock.dataset.count = '1';""",
        1,
    )

    # Guard optional random button in the trimmed UI.
    js = js.replace(
        """    const randomFillBtn = document.getElementById('random-fill-btn');
    randomFillBtn.addEventListener('click', randomFillPieces);""",
        """    const randomFillBtn = document.getElementById('random-fill-btn');
    randomFillBtn?.addEventListener('click', randomFillPieces);""",
        1,
    )

    # Before every solve, make sure the hidden board is still 7x7 fully open.
    js = js.replace(
        """    function solve() {
        // Step 1: Check if map is created""",
        """    function solve() {
        if (window.COOKIE_SIM_FORCE_FULL_GRID) {
            lockedCells.clear();
            gridState.fill(true);
        }
        // Step 1: Check if map is created""",
        1,
    )

    # Piece-picker selected/hover state uses only a border color, not a raised/popup effect.
    js = js.replace("pName === defaultPieceName ? '2px solid #667eea' : '1px solid #e5e7eb'", "pName === defaultPieceName ? '2px solid #ff4048' : '1px solid #e5e7eb'")
    js = js.replace("pieceCard.style.transition = 'all 0.15s ease';", "pieceCard.style.transition = 'border-color 0.15s ease'; pieceCard.style.boxShadow = 'none';")
    js = js.replace("pieceCard.addEventListener('mouseenter', () => { pieceCard.style.borderColor = '#667eea'; });", "pieceCard.addEventListener('mouseenter', () => { pieceCard.style.borderColor = '#ff4048'; pieceCard.style.boxShadow = 'none'; });")
    js = js.replace("pieceCard.addEventListener('mouseleave', () => { pieceCard.style.borderColor = pName === defaultPieceName ? '#667eea' : '#e5e7eb'; });", "pieceCard.addEventListener('mouseleave', () => { pieceCard.style.borderColor = pName === defaultPieceName ? '#ff4048' : '#e5e7eb'; pieceCard.style.boxShadow = 'none'; });")

    # Make generated piece previews clip correctly inside compact cards/modals.
    js = js.replace(
        """        const previewContainer = document.createElement('div');
        previewContainer.classList.add('piece-preview');

        const previewGrid = document.createElement('div');""",
        """        const previewContainer = document.createElement('div');
        previewContainer.classList.add('piece-preview');
        previewContainer.style.overflow = 'hidden';
        previewContainer.style.display = 'flex';
        previewContainer.style.alignItems = 'center';
        previewContainer.style.justifyContent = 'center';

        const previewGrid = document.createElement('div');""",
        1,
    )


    # Modal set selector and confirm button use cookie-sim red instead of the old blue.
    js = js.replace("setSelectBlock.style.background = 'linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1))';", "setSelectBlock.style.background = 'transparent'; setSelectBlock.style.border = 'none'; setSelectBlock.style.boxShadow = 'none'; setSelectBlock.style.padding = '0';")
    js = js.replace("setSelectBlock.style.border = '2px solid #667eea';", "setSelectBlock.style.border = 'none'; setSelectBlock.style.boxShadow = 'none';")
    js = js.replace("setSelector.style.border = '2px solid #667eea';", "setSelector.style.border = 'none'; setSelector.style.background = '#d1d5db'; setSelector.style.boxShadow = 'none';")
    js = js.replace("tabBtn.style.background = 'linear-gradient(135deg, #667eea, #764ba2)';", "tabBtn.style.background = '#ff4048';")
    js = js.replace("btn.style.background = 'linear-gradient(135deg, #667eea, #764ba2)';", "btn.style.background = '#ff4048';")
    js = js.replace("confirmBtn.style.background = 'linear-gradient(135deg, #667eea, #764ba2)';", "confirmBtn.style.background = '#ff4048';")
    js = js.replace("modalTitle.style.color = '#667eea';", "modalTitle.style.color = '#374151';")

    # Failed/equipped piece picker should not pop/scale on hover; only the border color changes.
    js = js.replace("pieceCard.style.transition = 'all 0.2s';", "pieceCard.style.transition = 'border-color 0.15s ease'; pieceCard.style.transform = 'none'; pieceCard.style.boxShadow = 'none';")
    js = js.replace("""                                    pieceCard.addEventListener('mouseenter', () => {
                                        pieceCard.style.borderColor = '#667eea';
                                        pieceCard.style.background = '#f0f4ff';
                                        pieceCard.style.transform = 'scale(1.05)';
                                    });""", """                                    pieceCard.addEventListener('mouseenter', () => {
                                        pieceCard.style.borderColor = '#ff4048';
                                        pieceCard.style.background = '#fff';
                                        pieceCard.style.transform = 'none';
                                        pieceCard.style.boxShadow = 'none';
                                    });""")
    js = js.replace("""                                    pieceCard.addEventListener('mouseleave', () => {
                                        pieceCard.style.borderColor = '#ddd';
                                        pieceCard.style.background = '#fff';
                                        pieceCard.style.transform = 'scale(1)';
                                    });""", """                                    pieceCard.addEventListener('mouseleave', () => {
                                        pieceCard.style.borderColor = pieceCard.dataset.csSelected === 'true' ? '#ff4048' : '#e5e7eb';
                                        pieceCard.style.background = '#fff';
                                        pieceCard.style.transform = 'none';
                                        pieceCard.style.boxShadow = 'none';
                                    });""")
    js = js.replace("""                                        pieceCard.style.borderColor = '#667eea';
                                        pieceCard.style.background = '#f0f4ff';
                                        pieceCard.style.boxShadow = '0 0 10px rgba(102, 126, 234, 0.5)';""", """                                        pieceCard.dataset.csSelected = 'true';
                                        pieceCard.style.borderColor = '#ff4048';
                                        pieceCard.style.background = '#fff';
                                        pieceCard.style.boxShadow = 'none';
                                        pieceCard.style.transform = 'none';""")


    # cookie-sim: 유니크 탭도 3등급 입력 UI를 쓸 수 있게 합산합니다.
    js = js.replace(
        """            if (piece.isUnique) {
                // 유니크 조각: 등급 없이 항상 2000점 (칸당 250점)
                const uniqueInput = document.getElementById(`piece-count-${name}-unique`);
                if (uniqueInput) {
                    const count = parseInt(uniqueInput.value, 10);
                    if (count > 0) {
                        const uniqueScore = 2000; // 유니크는 항상 2000점 고정
                        for (let i = 0; i < count; i++) {
                            const uniqueName = `${name}_unique_${i}`;
                            piecesToUse.push({ name: uniqueName, ...piece, score: uniqueScore, grade: 'unique' });
                            piecesCellCount += piece.shape.length;
                        }
                    }
                }
            } else {""",
        """            if (piece.isUnique) {
                // cookie-sim: 유니크 탭의 3등급 입력값을 합산합니다.
                // 점수는 기존 유니크 조각 규칙인 2000점으로 유지합니다.
                const uniqueScore = 2000;
                const gradeInputs = ['rare', 'epic', 'super']
                    .map(grade => document.getElementById(`piece-count-${name}-${grade}`))
                    .filter(Boolean);
                let count = 0;
                if (gradeInputs.length > 0) {
                    count = gradeInputs.reduce((sum, input) => sum + Math.max(0, parseInt(input.value || '0', 10) || 0), 0);
                }
                if (count <= 0) {
                    const uniqueInput = document.getElementById(`piece-count-${name}-unique`);
                    if (uniqueInput) count = Math.max(0, parseInt(uniqueInput.value || '0', 10) || 0);
                }
                if (count > 0) {
                    for (let i = 0; i < count; i++) {
                        const uniqueName = `${name}_unique_${i}`;
                        piecesToUse.push({ name: uniqueName, ...piece, score: uniqueScore, grade: 'unique' });
                        piecesCellCount += piece.shape.length;
                    }
                }
            } else {""",
        1,
    )

    js = _strip_emoji_text(js)
    return js


def _inline_assets(base_html: str, priority_sets: list[str], target_counts: dict[str, int], target_text: str, english: bool = False, theme_mode: str = 'system', glass_stat_items: list | None = None) -> str:
    style_css = _read_text(_STYLE_PATH)
    solver_style_css = _read_text(_SOLVER_STYLE_PATH)
    solver_js = _patch_solver_js(_read_text(_SOLVER_JS_PATH), english=english)

    texts = _shard_texts(english)
    theme_class = _theme_class(theme_mode)
    lang_attr = "en" if english else "ko"
    target_label = html_lib.escape(_translate_target_label(target_text, english))
    target_desc = (
        texts["target_desc"].format(target=target_label)
        if target_text else
        texts["target_fallback"]
    )

    usage_modal = _build_usage_modal(english)

    config_script = f"""
    <script>
    window.COOKIE_SIM_FORCE_FULL_GRID = true;
    window.COOKIE_SIM_SHARD_TARGET_TEXT = {json.dumps(target_text or '', ensure_ascii=False)};
    window.COOKIE_SIM_SHARD_PRIORITY_SETS = {json.dumps(priority_sets, ensure_ascii=False)};
    window.COOKIE_SIM_SHARD_TARGET_COUNTS = {json.dumps(target_counts, ensure_ascii=False)};
    window.COOKIE_SIM_SOLID_BOARD_LINES = true;
    window.COOKIE_SIM_GLASS_STAT_ITEMS = {json.dumps(glass_stat_items or [], ensure_ascii=False)};
    window.COOKIE_SIM_LANG = {json.dumps('en' if english else 'ko')};
    window.COOKIE_SIM_THEME = {json.dumps(theme_class)};
    </script>
    """

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css">
<script async src="https://docs.opencv.org/4.9.0/opencv.js"></script>
{config_script}
<style>
{style_css}
{solver_style_css}


/* cookie-sim: keep board vertically centered inside the right pink panel */
.cs-result-card .cs-glass-pages > div:not([style*="display: none"]) {{
    align-items: center !important;
}}
.cs-result-card .cs-glass-pages > div > .cs-set-bonus-box,
.cs-result-card .cs-glass-pages > div::before {{
    align-self: stretch !important;
}}
.cs-result-card .cs-glass-pages > div > .solution-grid {{
    align-self: center !important;
    justify-self: center !important;
}}


/* cookie-sim: responsive smaller result board + center in right panel */
.cs-result-card .cs-glass-pages > div:not([style*="display: none"]) {{
    grid-template-rows: minmax(200px, 1fr) !important;
    align-items: center !important;
    align-content: stretch !important;
}}
.cs-result-card .cs-glass-pages > div > .cs-set-bonus-box,
.cs-result-card .cs-glass-pages > div::before {{
    align-self: stretch !important;
}}
.cs-result-card .cs-glass-carousel .solution-grid,
.cs-result-card .cs-glass-pages .solution-grid,
.cs-result-card .cs-glass-pages > div > .solution-grid,
.cs-result-card .solution-grid {{
    grid-template-columns: repeat(7, minmax(0, 1fr)) !important;
    grid-template-rows: repeat(7, minmax(0, 1fr)) !important;
    width: min(168px, calc(100% - 16px)) !important;
    min-width: 0 !important;
    max-width: 168px !important;
    height: auto !important;
    min-height: 0 !important;
    max-height: none !important;
    aspect-ratio: 1 / 1 !important;
    align-self: center !important;
    justify-self: center !important;
    margin: 0 auto !important;
    box-sizing: border-box !important;
    flex: 0 1 auto !important;
}}
.cs-result-card .cs-glass-carousel .solution-cell,
.cs-result-card .cs-glass-pages .solution-cell,
.cs-result-card .cs-glass-pages > div > .solution-grid .solution-cell,
.cs-result-card .solution-cell {{
    width: auto !important;
    min-width: 0 !important;
    max-width: none !important;
    height: auto !important;
    min-height: 0 !important;
    max-height: none !important;
    aspect-ratio: auto !important;
    box-sizing: border-box !important;
}}


/* cookie-sim: when the board shrinks, shrink the numbers inside it too */
.cs-result-card .solution-grid {{
    container-type: inline-size !important;
}}
.cs-result-card .solution-grid .solution-cell,
.cs-result-card .solution-grid .solution-cell > span {{
    font-size: clamp(6px, 6.1cqw, 11px) !important;
    line-height: 1 !important;
    white-space: nowrap !important;
}}
.cs-result-card .solution-grid .solution-cell {{
    min-width: 0 !important;
    min-height: 0 !important;
    overflow: hidden !important;
}}
.cs-result-card .cs-glass-pages > div {{
    min-width: 0 !important;
}}
.cs-result-card .cs-glass-pages > div > .solution-grid {{
    max-width: min(160px, calc(100% - 24px)) !important;
}}

/* cookie-sim: result carousel arrows - transparent circle, keep arrow only */
.cs-result-card .cs-glass-carousel > .cs-glass-arrow,
.cs-result-card .cs-glass-carousel > .cs-glass-arrow:hover,
.cs-result-card .cs-glass-carousel > .cs-glass-arrow:focus,
.cs-result-card .cs-glass-carousel > .cs-glass-arrow:active {{
    background: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
    border: 0 !important;
    outline: 0 !important;
}}
body.cs-theme-dark .cs-result-card .cs-glass-carousel > .cs-glass-arrow,
body.cs-theme-dark .cs-result-card .cs-glass-carousel > .cs-glass-arrow:hover,
body.cs-theme-dark .cs-result-card .cs-glass-carousel > .cs-glass-arrow:focus,
body.cs-theme-dark .cs-result-card .cs-glass-carousel > .cs-glass-arrow:active {{
    background: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
}}
@media (prefers-color-scheme: dark) {{
    body.cs-theme-system .cs-result-card .cs-glass-carousel > .cs-glass-arrow,
    body.cs-theme-system .cs-result-card .cs-glass-carousel > .cs-glass-arrow:hover,
    body.cs-theme-system .cs-result-card .cs-glass-carousel > .cs-glass-arrow:focus,
    body.cs-theme-system .cs-result-card .cs-glass-carousel > .cs-glass-arrow:active {{
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
    }}
}}

/* cookie-sim compact embed */
html, body {{
    margin: 0 !important;
    padding: 0 !important;
    background: transparent !important;
    overflow-x: hidden !important;
    color: #111827;
}}

/* iframe page scrollbar: match the thin dropdown scrollbar */
body.cs-theme-dark,
body.cs-theme-system {{
    scrollbar-width: thin !important;
}}
body.cs-theme-dark {{
    scrollbar-color: #9ca3af #303236 !important;
}}
html:has(body.cs-theme-dark)::-webkit-scrollbar,
body.cs-theme-dark::-webkit-scrollbar {{
    width: 4px !important;
    height: 4px !important;
}}
html:has(body.cs-theme-dark)::-webkit-scrollbar-track,
body.cs-theme-dark::-webkit-scrollbar-track,
html:has(body.cs-theme-dark)::-webkit-scrollbar-corner,
body.cs-theme-dark::-webkit-scrollbar-corner {{
    background: #303236 !important;
}}
html:has(body.cs-theme-dark)::-webkit-scrollbar-thumb,
body.cs-theme-dark::-webkit-scrollbar-thumb {{
    background: #9ca3af !important;
    border-radius: 999px !important;
    border: 1px solid #303236 !important;
}}
html:has(body.cs-theme-dark)::-webkit-scrollbar-thumb:hover,
body.cs-theme-dark::-webkit-scrollbar-thumb:hover {{
    background: #b6bcc6 !important;
}}
@media (prefers-color-scheme: dark) {{
    body.cs-theme-system {{
        scrollbar-color: #9ca3af #303236 !important;
    }}
    html:has(body.cs-theme-system)::-webkit-scrollbar,
    body.cs-theme-system::-webkit-scrollbar {{
        width: 4px !important;
        height: 4px !important;
    }}
    html:has(body.cs-theme-system)::-webkit-scrollbar-track,
    body.cs-theme-system::-webkit-scrollbar-track,
    html:has(body.cs-theme-system)::-webkit-scrollbar-corner,
    body.cs-theme-system::-webkit-scrollbar-corner {{
        background: #303236 !important;
    }}
    html:has(body.cs-theme-system)::-webkit-scrollbar-thumb,
    body.cs-theme-system::-webkit-scrollbar-thumb {{
        background: #9ca3af !important;
        border-radius: 999px !important;
        border: 1px solid #303236 !important;
    }}
    html:has(body.cs-theme-system)::-webkit-scrollbar-thumb:hover,
    body.cs-theme-system::-webkit-scrollbar-thumb:hover {{
        background: #b6bcc6 !important;
    }}
}}
body,
button,
input,
select,
textarea,
.cs-shard-wrap,
.cs-shard-wrap * {{
    font-family: "Pretendard", -apple-system, BlinkMacSystemFont, "Segoe UI",
                 Roboto, "Noto Sans KR", "Apple SD Gothic Neo",
                 "Malgun Gothic", "Helvetica Neue", Arial, sans-serif !important;
}}
.cs-shard-wrap {{
    width: 100%;
    box-sizing: border-box;
    padding-right: 0 !important;
}}
.cs-section-pill {{
    display: block;
    width: 100%;
    box-sizing: border-box;
    background: #fcfcfc !important;
    border-radius: 12px !important;
    padding: 10px 12px !important;
    margin: 0 0 8px 0 !important;
    color: #111827 !important;
    font-size: 12px !important;
    font-weight: 800 !important;
    line-height: 1.2 !important;
    box-shadow: 0 4px 10px rgba(0,0,0,0.03) !important;
}}
.cs-card {{
    background: rgba(255, 255, 255, 0.96);
    border-radius: 10px;
    padding: 10px 10px 10px !important;
    padding-bottom: 0 !important;
    box-sizing: border-box;
    height: 100%;
}}
.cs-top-grid {{
    display: grid;
    grid-template-columns: minmax(0, 6fr) minmax(0, 4fr);
    gap: 10px;
    margin-bottom: 10px;
    align-items: stretch;
}}
.cs-title {{
    margin: 0 0 8px 0 !important;
    color: #ff4048;
    font-size: 12px;
    font-weight: 800;
}}
.cs-desc {{
    margin: 0 0 12px 0;
    color: #111827;
    font-size: 12px;
    font-weight: 400;
    line-height: 1.45;
}}
.cs-target {{
    margin: 8px 0 12px 0;
    padding: 9px 12px;
    border-radius: 12px;
    background: #fff7f7;
    border: none !important;
    color: #374151;
    font-size: 12px;
}}
.cs-action-row, .cs-upload-row {{
    display: grid;
    gap: 6px;
    align-items: stretch;
    width: 100%;
}}
.cs-action-row {{
    margin-top: 12px;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
}}
.cs-upload-block {{
    margin-top: 7px;
    padding-top: 7px;
    border-top: 1px solid rgba(229, 231, 235, 0.95);
}}
.cs-upload-block .cs-title {{
    margin-bottom: 8px;
}}
.cs-upload-row {{
    margin-top: 10px;
    grid-template-columns: minmax(0, 6fr) minmax(0, 4fr);
}}
#solve-btn, #clear-pieces-btn, #upload-btn, #usage-btn {{
    border: 0 !important;
    border-radius: 11px !important;
    min-height: 36px;
    padding: 8px 8px !important;
    font-weight: 900 !important;
    font-size: 12px !important;
    line-height: 1.2 !important;
    cursor: pointer;
    box-sizing: border-box;
    width: 100% !important;
    min-width: 0 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}}
#solve-btn, #upload-btn {{
    color: white !important;
    background: linear-gradient(135deg, #ff4048, #ff4d57) !important;
}}
#clear-pieces-btn, #usage-btn {{
    color: #111827 !important;
    background: #e5e7eb !important;
}}
#upload-btn {{
    display: flex !important;
    align-items: center;
    justify-content: center;
    text-align: center;
}}
#upload-status {{
    margin-top: 8px;
    margin-bottom: 8px !important;
    line-height: 1.2 !important;
    min-height: 15px;

    color: #10b981;
    font-size: 11px;
    font-weight: 700 !important;
    text-align: center;
}}
.cs-upload-help {{
    margin: 0;
    color: #111827;
    font-size: 12px;
    line-height: 1.45;
}}
.cs-result-card {{
    min-height: 218px;
}}
#solution-summary {{
    display: none !important;
}}
.piece-item:hover, .reset-btn:hover, .analysis-btn:hover {{
    transform: none !important;
    box-shadow: none !important;
}}
.cs-result-card .solutions-container {{
    margin-top: 0 !important;
    margin-bottom: 0 !important;
    background: transparent !important;
    padding: 0 !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 0 !important;
    justify-content: center !important;
}}
.cs-result-card .solutions-container::before {{
    content: none !important;
    display: none !important;
}}
.cs-result-card .solution-wrapper {{
    margin: 0 !important;
    padding: 0 !important;
    border-radius: 14px !important;
    box-shadow: none !important;
    width: 100% !important;
    align-items: stretch !important;
}}
.cs-result-card .solution-wrapper > div[style*='fff7f7'] {{
    width: 100% !important;
    box-sizing: border-box !important;
    text-align: left !important;
}}
.cs-result-card .cs-board-line {{
    box-shadow: none !important;
}}
.cs-result-card .solution-header {{
    margin-bottom: 8px !important;
    gap: 6px !important;
    flex-wrap: wrap !important;
}}
.cs-result-card .solution-header {{
    display: none !important;
}}
.cs-result-card .solution-wrapper,
.cs-result-card .solution-wrapper:hover {{
    transform: none !important;
    transition: none !important;
    gap: 8px !important;
}}
.cs-result-card .solution-wrapper > div[style*="fff7f7"] {{
    background: #fff7f7 !important;
    color: #374151 !important;
    box-shadow: none !important;
    margin-bottom: 0 !important;
}}
.cs-result-card .solution-grid {{
    margin: 8px auto 0 auto !important;
    transform-origin: top center;
}}
.cs-result-card .solution-grid {{
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    border-radius: 0 !important;
    overflow: hidden !important;
    transform: none !important;
    grid-template-columns: repeat(7, minmax(0, 1fr)) !important;
    grid-template-rows: repeat(7, minmax(0, 1fr)) !important;
    width: min(168px, calc(100% - 16px)) !important;
    min-width: 0 !important;
    max-width: 168px !important;
    height: auto !important;
    min-height: 0 !important;
    max-height: none !important;
    aspect-ratio: 1 / 1 !important;
    box-sizing: border-box !important;
    flex: 0 1 auto !important;
}}
.cs-result-card .solution-cell {{
    margin: 0 !important;
    border-radius: 0 !important;
    overflow: hidden !important;
    width: auto !important;
    min-width: 0 !important;
    max-width: none !important;
    height: auto !important;
    min-height: 0 !important;
    max-height: none !important;
    aspect-ratio: auto !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-set-bonus-box {{
    width: 100% !important;
    max-width: none !important;
    align-self: stretch !important;
    box-sizing: border-box !important;
    text-align: left !important;
}}
.cs-result-card .solution-cell:hover,
.cs-result-card .solution-grid:hover,
.cs-result-card .solution-wrapper:hover {{
    transform: none !important;
}}
.cs-empty-result {{
    width: 100%;
    min-height: 126px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 12px;
    background: #f9fafb;
    color: #9ca3af;
    font-size: 12px;
    text-align: center;
    padding: 0 14px;
    box-sizing: border-box;
}}
.pieces-section {{
    margin-top: 8px !important;
}}
.pieces-section > h3 {{
    display: none !important;
}}
/* 인식된 조각 섹션 제목은 드롭다운 위에 빨간 글씨로 표시 */
#recognized-pieces-section > h3 {{
    display: block !important;
    color: #ff4048 !important;
    font-size: 12px !important;
    font-weight: 800 !important;
    line-height: 1.2 !important;
    margin: 0 0 6px 0 !important;
    text-align: left !important;
}}
.pieces-section.cs-card {{
    box-shadow: none !important;
    padding-bottom: 10px !important;
    margin-bottom: 0 !important;
}}
#piece-palette, .palette {{
    min-height: 0 !important;
    height: auto !important;
    padding: 0 5px 0 0 !important;
    margin: 4px 0 0 0 !important;
    width: 100% !important;
    max-width: none !important;
    box-sizing: border-box !important;
    scrollbar-width: thin !important;
    scrollbar-color: #9ca3af #e5e7eb !important;
}}
#piece-palette::-webkit-scrollbar,
.palette::-webkit-scrollbar {{
    width: 4px !important;
}}
#piece-palette::-webkit-scrollbar-track,
.palette::-webkit-scrollbar-track {{
    background: #e5e7eb !important;
    border-radius: 10px !important;
}}
#piece-palette::-webkit-scrollbar-thumb,
.palette::-webkit-scrollbar-thumb {{
    background: #9ca3af !important;
    border-radius: 10px !important;
}}
#piece-palette::-webkit-scrollbar-thumb:hover,
.palette::-webkit-scrollbar-thumb:hover {{
    background: #6b7280 !important;
}}
#piece-palette .piece-grid {{
    display: grid !important;
    grid-template-columns: repeat(5, minmax(0, 1fr)) !important;
    gap: 8px !important;
    width: 100% !important;
    max-width: none !important;
    margin: 0 !important;
    padding: 0 !important;
    box-sizing: border-box !important;
}}
#piece-palette .piece-item {{
    min-height: 0 !important;
    height: auto !important;
    padding: 6px !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 5px !important;
    border-radius: 10px !important;
    border: none !important;
    background: #e5e7eb !important;
    box-shadow: none !important;
    transition: none !important;
    overflow: hidden !important;
}}
#piece-palette .piece-item:hover {{
    transform: none !important;
    box-shadow: none !important;
    border-color: transparent !important;
}}
#piece-palette .piece-item > .piece-preview {{
    width: 100% !important;
    height: 74px !important;
    min-height: 74px !important;
    flex: 0 0 74px !important;
    background: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0 !important;
    margin: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    overflow: hidden !important;
    box-shadow: none !important;
    box-sizing: border-box !important;
}}
#piece-palette .piece-item > .piece-preview > div {{
    transform: scale(0.58) !important;
    transform-origin: center center !important;
}}
#piece-palette .piece-item > div:has(.piece-count-input) {{
    display: grid !important;
    grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
    gap: 4px !important;
    margin-top: 0 !important;
    width: 100% !important;
}}
#piece-palette .piece-item > div:has(.piece-count-input) > div {{
    min-width: 0 !important;
    gap: 3px !important;
}}
#piece-palette .piece-count-input {{
    height: 23px !important;
    min-height: 23px !important;
    padding: 2px 2px !important;
    font-size: 12px !important;
    line-height: 16px !important;
    border-radius: 6px !important;
    box-sizing: border-box !important;
    background: #fff !important;
}}
#piece-palette .piece-item[data-cs-unique-card="true"] > div:has(.piece-count-input) {{
    display: block !important;
    grid-template-columns: none !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
}}
#piece-palette .piece-item[data-cs-unique-card="true"] .piece-count-input {{
    display: block !important;
    width: 100% !important;
    min-width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
    box-sizing: border-box !important;
}}
@media (max-width: 900px) {{
    #piece-palette .piece-grid, .piece-grid {{
        grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
    }}
}}
@media (max-width: 620px) {{
    #piece-palette .piece-grid, .piece-grid {{
        grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
    }}
}}
@media (max-width: 460px) {{
    #piece-palette .piece-grid, .piece-grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
    }}
}}
@media (max-width: 340px) {{
    #piece-palette .piece-grid, .piece-grid {{
        grid-template-columns: repeat(1, minmax(0, 1fr)) !important;
    }}
}}

.piece-grid {{
    display: grid !important;
    grid-template-columns: repeat(5, minmax(0, 1fr)) !important;
    width: 100% !important;
    max-width: none !important;
    margin: 0 !important;
    padding: 0 !important;
    box-sizing: border-box !important;
}}
.tab-content {{
    padding: 0 !important;
    margin: 0 !important;
    width: 100% !important;
    box-sizing: border-box !important;
}}
.tab-btn {{
    border-radius: 12px !important;
    padding: 10px 14px !important;
}}
.cs-palette-select-wrap {{
    position: relative !important;
    margin: 0 0 8px 0 !important;
    width: 100% !important;
    min-width: 0 !important;
    max-width: none !important;
    z-index: 50 !important;
    box-sizing: border-box !important;
}}
.cs-palette-select {{
    display: none !important;
}}

#cs-palette-set-select-wrap,
#cs-palette-set-combo,
#cs-palette-set-combo-btn,
#cs-palette-set-combo-menu {{
    width: 100% !important;
    min-width: 0 !important;
    max-width: none !important;
    box-sizing: border-box !important;
}}

.cs-palette-dropdown {{
    position: relative !important;
    width: 100% !important;
    font-family: "Pretendard", -apple-system, BlinkMacSystemFont, "Segoe UI",
                 Roboto, "Noto Sans KR", "Apple SD Gothic Neo",
                 "Malgun Gothic", "Helvetica Neue", Arial, sans-serif !important;
}}
.cs-palette-dropdown-button {{
    width: 100% !important;
    height: 36px !important;
    padding: 0 34px 0 12px !important;
    border: none !important;
    border-radius: 9px !important;
    background: #e5e7eb !important;
    color: #111827 !important;
    font-size: 12px !important;
    font-weight: 800 !important;
    line-height: 36px !important;
    text-align: left !important;
    outline: none !important;
    box-shadow: none !important;
    cursor: pointer !important;
    position: relative !important;
    appearance: none !important;
    font-family: "Pretendard", -apple-system, BlinkMacSystemFont, "Segoe UI",
                 Roboto, "Noto Sans KR", "Apple SD Gothic Neo",
                 "Malgun Gothic", "Helvetica Neue", Arial, sans-serif !important;
}}
.cs-palette-dropdown-button::after {{
    content: "";
    position: absolute !important;
    right: 15px !important;
    top: 50% !important;
    width: 5px !important;
    height: 5px !important;
    border-right: 2.5px solid #6b7280 !important;
    border-bottom: 2.5px solid #6b7280 !important;
    transform: translateY(-65%) rotate(45deg) !important;
    pointer-events: none !important;
}}
.cs-palette-dropdown-menu {{
    display: none !important;
    position: absolute !important;
    top: calc(100% + 4px) !important;
    left: -15px !important;
    right: -15px !important;
    width: 100% !important;
    min-width: 100% !important;
    box-sizing: border-box !important;
    background: #ffffff !important;
    border: none !important;
    border-radius: 0 0 8px 8px !important;
    box-shadow: -4px 6px 10px rgba(15, 23, 42, 0.05), 4px 6px 10px rgba(15, 23, 42, 0.05) !important;
    overflow: hidden !important;
    padding: 6px 0 !important;
    z-index: 9999 !important;
    font-family: "Pretendard", -apple-system, BlinkMacSystemFont, "Segoe UI",
                 Roboto, "Noto Sans KR", "Apple SD Gothic Neo",
                 "Malgun Gothic", "Helvetica Neue", Arial, sans-serif !important;
}}
.cs-palette-dropdown.open .cs-palette-dropdown-menu {{
    display: block !important;
}}
.cs-palette-dropdown-item {{
    display: block !important;
    width: 100% !important;
    padding: 9px 12px !important;
    background: #ffffff !important;
    border: none !important;
    color: #374151 !important;
    font-size: 12px !important;
    font-weight: 700 !important;
    text-align: left !important;
    line-height: 1.25 !important;
    cursor: pointer !important;
    box-shadow: none !important;
    transform: none !important;
    transition: color .12s ease !important;
    font-family: "Pretendard", -apple-system, BlinkMacSystemFont, "Segoe UI",
                 Roboto, "Noto Sans KR", "Apple SD Gothic Neo",
                 "Malgun Gothic", "Helvetica Neue", Arial, sans-serif !important;
}}
.cs-palette-dropdown-item:hover,
.cs-palette-dropdown-item:focus {{
    background: #ffffff !important;
    color: #ff4048 !important;
    font-weight: 800 !important;
    transform: none !important;
    box-shadow: none !important;
    outline: none !important;
}}
.cs-palette-dropdown-item:active {{
    background: #ffffff !important;
    color: #ff4048 !important;
    font-weight: 800 !important;
    transform: none !important;
    box-shadow: none !important;
    outline: none !important;
}}
.cs-palette-dropdown-item.active {{
    color: #374151 !important;
    font-weight: 700 !important;
    background: #ffffff !important;
}}
.cs-palette-dropdown-item.active:hover,
.cs-palette-dropdown-item.active:focus {{
    color: #ff4048 !important;
    font-weight: 800 !important;
    background: #ffffff !important;
    outline: none !important;
}}
.cs-palette-dropdown-item.active:active {{
    color: #374151 !important;
    font-weight: 700 !important;
    background: #ffffff !important;
    outline: none !important;
}}

.cs-palette-tab-wrap {{
    display: flex !important;
    flex-wrap: nowrap !important;
    gap: 8px !important;
    width: 100% !important;
    margin: 0 0 10px 0 !important;
    padding: 0 !important;
    overflow-x: auto !important;
    scrollbar-width: none !important;
    box-sizing: border-box !important;
}}
.cs-palette-tab-wrap::-webkit-scrollbar {{
    display: none !important;
}}
.cs-palette-tab-btn {{
    appearance: none !important;
    border: none !important;
    border-radius: 9px !important;
    padding: 9px 16px !important;
    min-width: 58px !important;
    height: 36px !important;
    background: #e5e7eb !important;
    color: #374151 !important;
    font-size: 12px !important;
    font-weight: 800 !important;
    line-height: 18px !important;
    text-align: center !important;
    cursor: pointer !important;
    white-space: nowrap !important;
    box-shadow: none !important;
    transform: none !important;
    transition: none !important;
    font-family: "Pretendard", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic", Arial, sans-serif !important;
}}
.cs-palette-tab-btn.active {{
    background: #ff4048 !important;
    color: #ffffff !important;
    font-weight: 900 !important;
}}
.cs-palette-tab-btn:hover,
.cs-palette-tab-btn:focus,
.cs-palette-tab-btn:active {{
    transform: none !important;
    box-shadow: none !important;
    outline: none !important;
}}


.cs-modal-select-wrap {{
    position: relative !important;
    width: 100% !important;
    min-width: 0 !important;
    max-width: none !important;
    margin: 6px 0 0 0 !important;
    z-index: 10050 !important;
    box-sizing: border-box !important;
}}
.cs-modal-select-native {{
    display: none !important;
}}
.cs-modal-select-dropdown {{
    position: relative !important;
    width: 100% !important;
    font-family: "Pretendard", -apple-system, BlinkMacSystemFont, "Segoe UI",
                 Roboto, "Noto Sans KR", "Apple SD Gothic Neo",
                 "Malgun Gothic", "Helvetica Neue", Arial, sans-serif !important;
}}
.cs-modal-select-button {{
    width: 100% !important;
    height: 38px !important;
    padding: 0 34px 0 12px !important;
    border: none !important;
    border-radius: 8px !important;
    background: #e5e7eb !important;
    color: #111827 !important;
    font-size: 12px !important;
    font-weight: 800 !important;
    line-height: 38px !important;
    text-align: left !important;
    outline: none !important;
    box-shadow: none !important;
    cursor: pointer !important;
    position: relative !important;
    appearance: none !important;
    box-sizing: border-box !important;
    touch-action: pan-y !important;
    font-family: "Pretendard", -apple-system, BlinkMacSystemFont, "Segoe UI",
                 Roboto, "Noto Sans KR", "Apple SD Gothic Neo",
                 "Malgun Gothic", "Helvetica Neue", Arial, sans-serif !important;
}}
.cs-modal-select-button::after {{
    content: "";
    position: absolute !important;
    right: 15px !important;
    top: 50% !important;
    width: 5px !important;
    height: 5px !important;
    border-right: 2.5px solid #6b7280 !important;
    border-bottom: 2.5px solid #6b7280 !important;
    transform: translateY(-65%) rotate(45deg) !important;
    pointer-events: none !important;
}}
.cs-modal-select-menu {{
    display: none !important;
    position: fixed !important;
    top: var(--cs-menu-top, 0px) !important;
    left: var(--cs-menu-left, 0px) !important;
    right: auto !important;
    width: var(--cs-menu-width, 240px) !important;
    min-width: 0 !important;
    max-height: var(--cs-menu-max-h, 280px) !important;
    box-sizing: border-box !important;
    background: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    box-shadow: -4px 6px 10px rgba(15, 23, 42, 0.06), 4px 6px 10px rgba(15, 23, 42, 0.06), 0 2px 8px rgba(15, 23, 42, 0.08) !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
    padding: 6px 0 !important;
    touch-action: pan-y !important;
    overscroll-behavior: contain !important;
    -webkit-overflow-scrolling: touch !important;
    z-index: 10060 !important;
    font-family: "Pretendard", -apple-system, BlinkMacSystemFont, "Segoe UI",
                 Roboto, "Noto Sans KR", "Apple SD Gothic Neo",
                 "Malgun Gothic", "Helvetica Neue", Arial, sans-serif !important;
}}
.cs-modal-select-dropdown.open .cs-modal-select-menu {{
    display: block !important;
}}
.cs-modal-select-item {{
    display: block !important;
    width: 100% !important;
    padding: 9px 12px !important;
    background: #ffffff !important;
    border: none !important;
    color: #374151 !important;
    font-size: 12px !important;
    font-weight: 700 !important;
    text-align: left !important;
    line-height: 1.25 !important;
    cursor: pointer !important;
    box-shadow: none !important;
    transform: none !important;
    transition: none !important;
    box-sizing: border-box !important;
    font-family: "Pretendard", -apple-system, BlinkMacSystemFont, "Segoe UI",
                 Roboto, "Noto Sans KR", "Apple SD Gothic Neo",
                 "Malgun Gothic", "Helvetica Neue", Arial, sans-serif !important;
}}
.cs-modal-select-item:hover {{
    background: #ffffff !important;
    color: #ff4048 !important;
    font-weight: 700 !important;
}}
.cs-modal-select-item.active {{
    background: #ffffff !important;
    color: #374151 !important;
    font-weight: 700 !important;
}}
#recognized-piece-filter-wrap .cs-modal-select-button {{
    height: 34px !important;
    line-height: 34px !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}}
#recognized-piece-filter-wrap .cs-modal-select-menu {{
    max-height: min(var(--cs-menu-max-h, 220px), 220px) !important;
}}

/* cookie-sim: transparent touch shield behind custom dropdown menus.
   It blocks taps from reaching shard cards below while the menu is open. */
.cs-modal-select-backdrop,
.cs-palette-dropdown-backdrop {{
    display: none !important;
    position: fixed !important;
    inset: 0 !important;
    background: transparent !important;
    z-index: 10055 !important;
    pointer-events: auto !important;
    touch-action: none !important;
}}
.cs-modal-select-dropdown.open .cs-modal-select-backdrop,
.cs-palette-dropdown.open .cs-palette-dropdown-backdrop {{
    display: block !important;
}}
.cs-modal-select-menu,
.cs-palette-dropdown-menu {{
    z-index: 10060 !important;
}}


.hidden-solver-elements {{
    position: absolute !important;
    left: -99999px !important;
    width: 1px !important;
    height: 1px !important;
    overflow: hidden !important;
}}
@media (max-width: 780px) {{
    .cs-top-grid {{ grid-template-columns: 1fr; gap: 10px; }}
    .cs-card {{ padding: 10px 10px 10px !important; }}
    .cs-section-pill {{ padding: 10px 12px !important; margin: 0 0 8px 0 !important; }}
    .cs-action-row, .cs-upload-row {{ gap: 6px !important; }}
}}

/* cookie-sim image recognition modal cleanup */
body > div[style*="z-index: 2000"] *,
body > div[style*="z-index: 3000"] * {{
    font-family: "Pretendard", -apple-system, BlinkMacSystemFont, "Segoe UI",
                 Roboto, "Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic", Arial, sans-serif !important;
}}
body > div[style*="z-index: 2000"] h2,
body > div[style*="z-index: 2000"] h3,
body > div[style*="z-index: 2000"] h4,
body > div[style*="z-index: 3000"] h3 {{
    font-size: 13px !important;
    font-weight: 800 !important;
    color: #374151 !important;
    line-height: 1.2 !important;
}}
body > div[style*="z-index: 2000"] button,
body > div[style*="z-index: 2000"] select,
body > div[style*="z-index: 3000"] button {{
    font-size: 12px !important;
}}
body > div[style*="z-index: 2000"] .piece-preview,
body > div[style*="z-index: 3000"] .piece-preview {{
    width: 100% !important;
    height: 76px !important;
    min-height: 76px !important;
    background: #fff !important;
    border: 0 !important;
    border-radius: 6px !important;
    padding: 0 !important;
    margin: 0 !important;
    box-shadow: none !important;
    box-sizing: border-box !important;
    overflow: hidden !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}}
body > div[style*="z-index: 3000"] .piece-preview {{
    height: 96px !important;
    min-height: 96px !important;
}}
body > div[style*="z-index: 2000"] .piece-preview > div,
body > div[style*="z-index: 3000"] .piece-preview > div {{
    transform: scale(0.66) !important;
    transform-origin: center center !important;
}}
body > div[style*="z-index: 2000"] .preview-cell:not(.preview-cell-filled),
body > div[style*="z-index: 3000"] .preview-cell:not(.preview-cell-filled) {{
    border-color: #e5e7eb !important;
}}
body > div[style*="z-index: 2000"] .preview-cell-filled,
body > div[style*="z-index: 3000"] .preview-cell-filled,
#piece-palette .preview-cell-filled,
.preview-cell-filled {{
    border-color: transparent !important;
}}
body > div[style*="z-index: 2000"] button {{
    box-shadow: none !important;
}}
body > div[style*="z-index: 2000"] button:not(:last-child)[style*="수정"],
body > div[style*="z-index: 2000"] button {{
    white-space: nowrap !important;
}}


body > div[style*="z-index: 2000"] select:focus,
body > div[style*="z-index: 3000"] select:focus {{
    outline: none !important;
    border-color: transparent !important;
    box-shadow: 0 0 0 2px rgba(255, 64, 72, 0.12) !important;
}}
body > div[style*="z-index: 2000"] button:hover,
body > div[style*="z-index: 3000"] button:hover {{
    transform: none !important;
    box-shadow: none !important;
}}
body > div[style*="z-index: 3000"] div[style*="cursor: pointer"] {{
    transform: none !important;
    box-shadow: none !important;
}}


body > div[style*="z-index: 2000"] h2 {{
    font-size: 14px !important;
    font-weight: 800 !important;
    color: #374151 !important;
}}


/* Keep upload/action buttons same height even on narrow screens */
.cs-upload-row {{
    display: grid !important;
    grid-template-columns: minmax(0, 6fr) minmax(0, 4fr) !important;
    gap: 6px !important;
    align-items: stretch !important;
}}

#upload-btn,
#usage-btn {{
    height: 36px !important;
    min-height: 36px !important;
    max-height: 36px !important;
    padding: 0 8px !important;
    margin: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    line-height: 1 !important;
    box-sizing: border-box !important;
    white-space: nowrap !important;
    font-size: 12px !important;
    font-weight: 900 !important;
}}

@media (max-width: 780px) {{
    .cs-upload-row {{
        grid-template-columns: minmax(0, 6fr) minmax(0, 4fr) !important;
        gap: 6px !important;
        align-items: stretch !important;
    }}

    #upload-btn,
    #usage-btn {{
        height: 36px !important;
        min-height: 36px !important;
        max-height: 36px !important;
        padding: 0 8px !important;
        line-height: 1 !important;
    }}
}}


/* Keep bottom gap under the result board */
.cs-result-card {{
    padding-bottom: 6px !important;
    overflow: visible !important;
}}

.cs-result-card .solutions-container {{
    padding-bottom: 6px !important;
    margin-bottom: 0 !important;
    overflow: visible !important;
}}

.cs-result-card .solution,
.cs-result-card .solution-card,
.cs-result-card .solution-board-wrap,
.cs-result-card .solution-grid {{
    margin-bottom: 0 !important;
}}

@media (max-width: 780px) {{
    .cs-result-card {{
        padding-bottom: 6px !important;
    }}

    .cs-result-card .solutions-container {{
        padding-bottom: 6px !important;
    }}
}}

/* Empty result box fill */
.cs-result-card {{
    display: flex !important;
    flex-direction: column !important;
}}

.cs-result-card .solutions-container {{
    flex: 1 1 auto !important;
    display: flex !important;
    width: 100% !important;
    padding-bottom: 3px !important;
    margin-bottom: 0 !important;
    overflow: visible !important;
}}

.cs-empty-result {{
    flex: 1 1 auto !important;
    width: 100% !important;
    height: auto !important;
    min-height: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin: 0 !important;
    box-sizing: border-box !important;
}}

.cs-result-card .solution,
.cs-result-card .solution-card,
.cs-result-card .solution-board-wrap,
.cs-result-card .solution-grid {{
    margin-bottom: 0 !important;
}}


/* cookie-sim theme and guide modal */
body.cs-theme-light,
body.cs-theme-system {{
    --cs-accent: #ff4048;
    --cs-accent-2: #ff4d57;
    --cs-text: #111827;
    --cs-muted: #4b5563;
    --cs-card-bg: #fcfcfc;
    --cs-soft-bg: #fff7f7;
    --cs-section-bg: #fcfcfc;
    --cs-modal-bg: #ffffff;
    --cs-button-muted-bg: #e5e7eb;
    --cs-border: rgba(229,231,235,0.95);
    --cs-shadow: 0 4px 20px rgba(0,0,0,0.3);
}}
body.cs-theme-dark {{
    --cs-accent: #ff5b66;
    --cs-accent-2: #ff7680;
    --cs-text: #f3f4f6;
    --cs-muted: #cbd5e1;
    --cs-card-bg: #303236;
    --cs-soft-bg: rgba(255,64,72,0.13);
    --cs-section-bg: #303236;
    --cs-modal-bg: #303236;
    --cs-button-muted-bg: #303236;
    --cs-border: rgba(68, 72, 80, 0.95);
    --cs-shadow: 0 4px 24px rgba(0,0,0,0.55);
}}
@media (prefers-color-scheme: dark) {{
    body.cs-theme-system {{
        --cs-accent: #ff5b66;
        --cs-accent-2: #ff7680;
        --cs-text: #f3f4f6;
        --cs-muted: #cbd5e1;
        --cs-card-bg: #303236;
        --cs-soft-bg: rgba(255,64,72,0.13);
        --cs-section-bg: #303236;
        --cs-modal-bg: #303236;
        --cs-button-muted-bg: #303236;
        --cs-border: rgba(68, 72, 80, 0.95);
        --cs-shadow: 0 4px 24px rgba(0,0,0,0.55);
    }}
}}
body.cs-theme-light,
body.cs-theme-dark,
body.cs-theme-system {{ color: var(--cs-text) !important; }}
.cs-section-pill {{ background: var(--cs-section-bg) !important; color: var(--cs-text) !important; }}
.cs-card, .pieces-section.cs-card, .cs-result-card {{ background: var(--cs-card-bg) !important; color: var(--cs-text) !important; }}
.cs-title, .pieces-section h3, .usage-heading {{ color: var(--cs-accent) !important; }}
#usage-modal .usage-copy .usage-keyword {{ color: inherit !important; }}
.cs-desc, .cs-upload-help, .usage-copy {{ color: var(--cs-muted) !important; }}
.cs-target {{ background: var(--cs-soft-bg) !important; color: var(--cs-text) !important; }}
.cs-upload-block {{ border-top-color: var(--cs-border) !important; }}
#solve-btn, #upload-btn {{ background: linear-gradient(135deg, var(--cs-accent), var(--cs-accent-2)) !important; }}
#clear-pieces-btn, #usage-btn {{ background: var(--cs-button-muted-bg) !important; color: var(--cs-text) !important; }}
.cs-empty-result {{ color: var(--cs-muted) !important; }}
#usage-modal .usage-modal-box {{
    background: var(--cs-modal-bg) !important; color: var(--cs-text) !important;
    margin: 3% auto;
    padding: clamp(12px, 4vw, 24px);
    border-radius: clamp(8px, 2.4vw, 15px);
    width: min(550px, calc(100% - clamp(16px, 7vw, 48px)));
    max-width: 550px; max-height: 90vh; overflow-y: auto; position: relative;
    box-sizing: border-box; font-size: 13px; box-shadow: var(--cs-shadow);
}}
#usage-modal .usage-close {{
    position: absolute; right: 20px; top: 20px; font-size: 20px; font-weight: 800;
    cursor: pointer; color: var(--cs-muted); transition: color 0.2s;
}}
#usage-modal .usage-heading {{ margin: 0 0 8px 0; font-size: 13px; line-height: 1.35; font-weight: 800; }}
#usage-modal .usage-copy {{ line-height: 1.5; margin: 0 0 8px 0; font-size: 11px; }}
#usage-modal .usage-keyword {{ font-weight: 800; }}
#usage-modal .usage-image-pair {{
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    column-gap: clamp(4px, 2vw, 10px);
    row-gap: 0;
    width: 100%; max-width: 500px;
    margin: 0 0 clamp(10px, 3vw, 16px);
    align-items: start;
}}
#usage-modal .usage-img {{
    display: block; width: 100%; max-width: 100%; height: auto;
    border-radius: clamp(4px, 1.8vw, 10px);
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}}
#usage-modal .usage-img-single {{
    max-width: 500px;
    margin: 0 0 clamp(10px, 3vw, 16px);
}}
#usage-modal .usage-step-2 .usage-img-single:first-of-type {{
    margin-bottom: clamp(4px, 2vw, 10px) !important;
}}
#usage-modal .usage-section {{
    margin-bottom: clamp(10px, 3vw, 18px) !important;
}}
#usage-modal .usage-section:last-child {{
    margin-bottom: 0 !important;
}}
/* cookie-sim: theme-specific usage guide images (light/dark variants of step 5) */
#usage-modal .usage-img-theme-light {{ display: block; }}
#usage-modal .usage-img-theme-dark {{ display: none; }}
body.cs-theme-dark #usage-modal .usage-img-theme-light {{ display: none; }}
body.cs-theme-dark #usage-modal .usage-img-theme-dark {{ display: block; }}
@media (prefers-color-scheme: dark) {{
    body.cs-theme-system #usage-modal .usage-img-theme-light {{ display: none; }}
    body.cs-theme-system #usage-modal .usage-img-theme-dark {{ display: block; }}
}}
body.cs-theme-dark > div[style*="z-index: 2000"] > div,
body.cs-theme-dark > div[style*="z-index: 3000"] > div {{
    background: var(--cs-modal-bg) !important; color: var(--cs-text) !important;
}}
body.cs-theme-dark > div[style*="z-index: 2000"] h2,
body.cs-theme-dark > div[style*="z-index: 2000"] h3,
body.cs-theme-dark > div[style*="z-index: 2000"] h4,
body.cs-theme-dark > div[style*="z-index: 2000"] p,
body.cs-theme-dark > div[style*="z-index: 2000"] label,
body.cs-theme-dark > div[style*="z-index: 3000"] h3 {{ color: var(--cs-text) !important; }}
body.cs-theme-dark > div[style*="z-index: 2000"] select,
body.cs-theme-dark > div[style*="z-index: 2000"] input,
body.cs-theme-dark > div[style*="z-index: 3000"] select,
body.cs-theme-dark > div[style*="z-index: 3000"] input {{
    background: #1f2937 !important; color: var(--cs-text) !important; border-color: #4b5563 !important;
}}


/* dark-mode cleanup: match the main app gray theme and remove white blocks */
body.cs-theme-dark .cs-shard-wrap,
body.cs-theme-dark .cs-top-grid,
body.cs-theme-dark .pieces-section {{
    background: transparent !important;
}}
body.cs-theme-dark .cs-card,
body.cs-theme-dark .pieces-section.cs-card,
body.cs-theme-dark .cs-result-card {{
    background: #303236 !important;
}}
body.cs-theme-dark .cs-section-pill {{
    background: #303236 !important;
}}
body.cs-theme-dark .cs-empty-result {{
    background: #303236 !important;
    color: #9ca3af !important;
}}
body.cs-theme-dark #piece-palette,
body.cs-theme-dark .palette {{
    scrollbar-width: thin !important;
    scrollbar-color: #6b7280 #202124 !important;
}}
body.cs-theme-dark #piece-palette::-webkit-scrollbar,
body.cs-theme-dark .palette::-webkit-scrollbar {{
    width: 4px !important;
    height: 4px !important;
}}
body.cs-theme-dark #piece-palette::-webkit-scrollbar-track,
body.cs-theme-dark .palette::-webkit-scrollbar-track {{
    background: #303236 !important;
    border-radius: 10px !important;
}}
body.cs-theme-dark #piece-palette::-webkit-scrollbar-thumb,
body.cs-theme-dark .palette::-webkit-scrollbar-thumb {{
    background: #6b7280 !important;
    border-radius: 10px !important;
}}
body.cs-theme-dark #piece-palette::-webkit-scrollbar-thumb:hover,
body.cs-theme-dark .palette::-webkit-scrollbar-thumb:hover {{
    background: #9ca3af !important;
}}
body.cs-theme-dark #piece-palette .piece-item {{
    background: #303236 !important;
}}
body.cs-theme-dark #piece-palette .piece-item > .piece-preview {{
    background: #303236 !important;
}}
body.cs-theme-dark #piece-palette .piece-count-input {{
    background: #303236 !important;
    color: #f3f4f6 !important;
    border-color: #3f444d !important;
}}
body.cs-theme-dark #piece-palette .piece-count-input::placeholder {{
    color: #9ca3af !important;
}}
body.cs-theme-dark #usage-modal .usage-modal-box {{
    scrollbar-width: thin !important;
    scrollbar-color: #6b7280 #202124 !important;
}}
body.cs-theme-dark #usage-modal .usage-modal-box::-webkit-scrollbar {{
    width: 4px !important;
}}
body.cs-theme-dark #usage-modal .usage-modal-box::-webkit-scrollbar-track {{
    background: #303236 !important;
    border-radius: 10px !important;
}}
body.cs-theme-dark #usage-modal .usage-modal-box::-webkit-scrollbar-thumb {{
    background: #6b7280 !important;
    border-radius: 10px !important;
}}
body.cs-theme-dark #usage-modal .usage-modal-box::-webkit-scrollbar-thumb:hover {{
    background: #9ca3af !important;
}}
/* dynamically-created set-selection modal */
body.cs-theme-dark > div[style*="z-index: 2000"] {{
    scrollbar-width: thin !important;
    scrollbar-color: #6b7280 #303236 !important;
}}
body.cs-theme-dark > div[style*="z-index: 2000"] > div {{
    background: #303236 !important;
    color: #f3f4f6 !important;
}}
body.cs-theme-dark > div[style*="z-index: 2000"] > div::-webkit-scrollbar,
body.cs-theme-dark > div[style*="z-index: 2000"] *::-webkit-scrollbar {{
    width: 4px !important;
    height: 4px !important;
}}
body.cs-theme-dark > div[style*="z-index: 2000"] > div::-webkit-scrollbar-track,
body.cs-theme-dark > div[style*="z-index: 2000"] *::-webkit-scrollbar-track {{
    background: #303236 !important;
    border-radius: 10px !important;
}}
body.cs-theme-dark > div[style*="z-index: 2000"] > div::-webkit-scrollbar-thumb,
body.cs-theme-dark > div[style*="z-index: 2000"] *::-webkit-scrollbar-thumb {{
    background: #6b7280 !important;
    border-radius: 10px !important;
}}
body.cs-theme-dark > div[style*="z-index: 2000"] > div::-webkit-scrollbar-thumb:hover,
body.cs-theme-dark > div[style*="z-index: 2000"] *::-webkit-scrollbar-thumb:hover {{
    background: #9ca3af !important;
}}
body.cs-theme-dark > div[style*="z-index: 2000"] [style*="background: white"],
body.cs-theme-dark > div[style*="z-index: 2000"] [style*="background: #fff"],
body.cs-theme-dark > div[style*="z-index: 2000"] [style*="background: #ffffff"],
body.cs-theme-dark > div[style*="z-index: 2000"] [style*="background-color: white"],
body.cs-theme-dark > div[style*="z-index: 2000"] [style*="background-color: #fff"],
body.cs-theme-dark > div[style*="z-index: 2000"] [style*="background-color: #ffffff"],
body.cs-theme-dark > div[style*="z-index: 2000"] [style*="background: rgb(255, 255, 255)"],
body.cs-theme-dark > div[style*="z-index: 2000"] [style*="background-color: rgb(255, 255, 255)"] {{
    background: #303236 !important;
    color: #f3f4f6 !important;
}}
body.cs-theme-dark > div[style*="z-index: 2000"] [style*="background: rgb(248, 249, 250)"],
body.cs-theme-dark > div[style*="z-index: 2000"] [style*="background-color: rgb(248, 249, 250)"],
body.cs-theme-dark > div[style*="z-index: 2000"] [style*="background: #f8f9fa"],
body.cs-theme-dark > div[style*="z-index: 2000"] [style*="background-color: #f8f9fa"] {{
    background: #303236 !important;
    color: #f3f4f6 !important;
}}
body.cs-theme-dark > div[style*="z-index: 2000"] h2,
body.cs-theme-dark > div[style*="z-index: 2000"] h3,
body.cs-theme-dark > div[style*="z-index: 2000"] h4,
body.cs-theme-dark > div[style*="z-index: 2000"] p,
body.cs-theme-dark > div[style*="z-index: 2000"] label,
body.cs-theme-dark > div[style*="z-index: 2000"] div {{
    color: #f3f4f6;
}}
body.cs-theme-dark > div[style*="z-index: 2000"] select,
body.cs-theme-dark > div[style*="z-index: 2000"] input {{
    background: #303236 !important;
    color: #f3f4f6 !important;
    border-color: #3f444d !important;
}}
body.cs-theme-dark > div[style*="z-index: 2000"] option {{
    background: #303236 !important;
    color: #f3f4f6 !important;
}}
body.cs-theme-dark > div[style*="z-index: 2000"] button {{
    color: #f3f4f6;
}}
body.cs-theme-dark > div[style*="z-index: 2000"] button[style*="background: #e5e7eb"],
body.cs-theme-dark > div[style*="z-index: 2000"] button[style*="background-color: #e5e7eb"] {{
    background: #2f333a !important;
    color: #f3f4f6 !important;
}}
body.cs-theme-dark > div[style*="z-index: 2000"] [style*="border: 2px solid #667eea"] {{
    border-color: #3f444d !important;
}}


/* dark-mode dropdown/background final fix */
body.cs-theme-dark .cs-section-pill,
body.cs-theme-dark .cs-card,
body.cs-theme-dark .pieces-section.cs-card,
body.cs-theme-dark .cs-result-card {{
    background: #303236 !important;
}}
body.cs-theme-dark .cs-target,
body.cs-theme-dark .cs-empty-result,
body.cs-theme-dark .cs-upload-block,
body.cs-theme-dark .solutions-container {{
    background-color: #303236 !important;
}}
body.cs-theme-dark #piece-palette,
body.cs-theme-dark .palette {{
    background: #303236 !important;
    scrollbar-color: #6b7280 #303236 !important;
}}
body.cs-theme-dark #piece-palette .piece-item {{
    background: #202124 !important;
}}
body.cs-theme-dark #piece-palette .piece-item > .piece-preview {{
    background: #242528 !important;
}}
body.cs-theme-dark #piece-palette .piece-count-input {{
    background: #202124 !important;
    color: #ffffff !important;
    border-color: #303236 !important;
}}
body.cs-theme-dark .cs-palette-dropdown-button,
body.cs-theme-dark #cs-palette-set-combo-btn {{
    background: #e5e7eb !important;
    color: #111827 !important;
}}
body.cs-theme-dark .cs-palette-dropdown-button::after,
body.cs-theme-dark #cs-palette-set-combo-btn::after {{
    border-right-color: #111827 !important;
    border-bottom-color: #111827 !important;
}}
body.cs-theme-dark .cs-palette-dropdown-menu,
body.cs-theme-dark #cs-palette-set-combo-menu {{
    background: #303236 !important;
    color: #f3f4f6 !important;
    box-shadow: 0 10px 22px rgba(0,0,0,0.28) !important;
}}
body.cs-theme-dark .cs-palette-dropdown-item {{
    background: #303236 !important;
    color: #f3f4f6 !important;
}}
body.cs-theme-dark .cs-palette-dropdown-item:hover,
body.cs-theme-dark .cs-palette-dropdown-item:focus,
body.cs-theme-dark .cs-palette-dropdown-item.active:hover,
body.cs-theme-dark .cs-palette-dropdown-item.active:focus {{
    background: #3a3d42 !important;
    color: #ff5b66 !important;
}}
body.cs-theme-dark .cs-palette-dropdown-item.active,
body.cs-theme-dark .cs-palette-dropdown-item:active,
body.cs-theme-dark .cs-palette-dropdown-item.active:active {{
    background: #303236 !important;
    color: #f3f4f6 !important;
}}
body.cs-theme-dark .cs-palette-select,
body.cs-theme-dark .cs-palette-select option,
body.cs-theme-dark select,
body.cs-theme-dark option {{
    background: #303236 !important;
    color: #f3f4f6 !important;
}}
body.cs-theme-dark #piece-palette::-webkit-scrollbar-track,
body.cs-theme-dark .palette::-webkit-scrollbar-track,
body.cs-theme-dark #usage-modal .usage-modal-box::-webkit-scrollbar-track,
body.cs-theme-dark > div[style*="z-index: 2000"] > div::-webkit-scrollbar-track,
body.cs-theme-dark > div[style*="z-index: 2000"] *::-webkit-scrollbar-track {{
    background: #303236 !important;
}}
body.cs-theme-dark #piece-palette::-webkit-scrollbar-thumb,
body.cs-theme-dark .palette::-webkit-scrollbar-thumb,
body.cs-theme-dark #usage-modal .usage-modal-box::-webkit-scrollbar-thumb,
body.cs-theme-dark > div[style*="z-index: 2000"] > div::-webkit-scrollbar-thumb,
body.cs-theme-dark > div[style*="z-index: 2000"] *::-webkit-scrollbar-thumb {{
    background: #6b7280 !important;
}}
body.cs-theme-dark #usage-modal .usage-modal-box,
body.cs-theme-dark > div[style*="z-index: 2000"] > div {{
    background: #303236 !important;
}}
body.cs-theme-dark > div[style*="z-index: 2000"] [style*="background: white"],
body.cs-theme-dark > div[style*="z-index: 2000"] [style*="background: #fff"],
body.cs-theme-dark > div[style*="z-index: 2000"] [style*="background: #ffffff"],
body.cs-theme-dark > div[style*="z-index: 2000"] [style*="background-color: white"],
body.cs-theme-dark > div[style*="z-index: 2000"] [style*="background-color: #fff"],
body.cs-theme-dark > div[style*="z-index: 2000"] [style*="background-color: #ffffff"],
body.cs-theme-dark > div[style*="z-index: 2000"] [style*="background: rgb(255, 255, 255)"],
body.cs-theme-dark > div[style*="z-index: 2000"] [style*="background-color: rgb(255, 255, 255)"] {{
    background: #303236 !important;
    color: #f3f4f6 !important;
}}
body.cs-theme-dark > div[style*="z-index: 2000"] [style*="background: rgb(248, 249, 250)"],
body.cs-theme-dark > div[style*="z-index: 2000"] [style*="background-color: rgb(248, 249, 250)"],
body.cs-theme-dark > div[style*="z-index: 2000"] [style*="background: #f8f9fa"],
body.cs-theme-dark > div[style*="z-index: 2000"] [style*="background-color: #f8f9fa"],
body.cs-theme-dark > div[style*="z-index: 2000"] .piece-preview {{
    background: #202124 !important;
    color: #f3f4f6 !important;
}}
body.cs-theme-dark > div[style*="z-index: 2000"] h2,
body.cs-theme-dark > div[style*="z-index: 2000"] h3,
body.cs-theme-dark > div[style*="z-index: 2000"] h4,
body.cs-theme-dark > div[style*="z-index: 2000"] p,
body.cs-theme-dark > div[style*="z-index: 2000"] label,
body.cs-theme-dark > div[style*="z-index: 2000"] div {{
    color: #f3f4f6;
}}
body.cs-theme-dark > div[style*="z-index: 2000"] select,
body.cs-theme-dark > div[style*="z-index: 2000"] input {{
    background: #303236 !important;
    color: #f3f4f6 !important;
    border-color: #3f444d !important;
}}
body.cs-theme-dark > div[style*="z-index: 2000"] option {{
    background: #303236 !important;
    color: #f3f4f6 !important;
}}
body.cs-theme-dark > div[style*="z-index: 2000"] button[style*="background: #e5e7eb"],
body.cs-theme-dark > div[style*="z-index: 2000"] button[style*="background-color: #e5e7eb"] {{
    background: #303236 !important;
    color: #f3f4f6 !important;
}}


/* final dropdown color sync */
body.cs-theme-dark .cs-palette-dropdown-button,
body.cs-theme-dark #cs-palette-set-combo-btn,
body.cs-theme-dark .cs-modal-select-button {{
    background: #303236 !important;
    color: #f3f4f6 !important;
}}
body.cs-theme-dark .cs-palette-dropdown-button::after,
body.cs-theme-dark #cs-palette-set-combo-btn::after,
body.cs-theme-dark .cs-modal-select-button::after {{
    border-right-color: #9ca3af !important;
    border-bottom-color: #9ca3af !important;
}}
body.cs-theme-dark .cs-palette-dropdown-menu,
body.cs-theme-dark #cs-palette-set-combo-menu,
body.cs-theme-dark .cs-modal-select-menu {{
    background: #303236 !important;
    color: #f3f4f6 !important;
}}
body.cs-theme-dark .cs-palette-dropdown-item,
body.cs-theme-dark .cs-modal-select-item {{
    background: #303236 !important;
    color: #f3f4f6 !important;
}}
body.cs-theme-dark .cs-palette-dropdown-item:hover,
body.cs-theme-dark .cs-palette-dropdown-item:focus,
body.cs-theme-dark .cs-palette-dropdown-item.active:hover,
body.cs-theme-dark .cs-palette-dropdown-item.active:focus,
body.cs-theme-dark .cs-modal-select-item:hover,
body.cs-theme-dark .cs-modal-select-item:focus,
body.cs-theme-dark .cs-modal-select-item.active:hover,
body.cs-theme-dark .cs-modal-select-item.active:focus {{
    background: #3a3d42 !important;
    color: #ff5b66 !important;
}}
body.cs-theme-dark .cs-palette-dropdown-item.active,
body.cs-theme-dark .cs-palette-dropdown-item:active,
body.cs-theme-dark .cs-palette-dropdown-item.active:active,
body.cs-theme-dark .cs-modal-select-item.active,
body.cs-theme-dark .cs-modal-select-item:active,
body.cs-theme-dark .cs-modal-select-item.active:active {{
    background: #303236 !important;
    color: #f3f4f6 !important;
}}
body.cs-theme-dark select,
body.cs-theme-dark option {{
    background: #303236 !important;
    color: #f3f4f6 !important;
}}


/* dropdown brightness and white empty-area fix */
body.cs-theme-dark .cs-palette-dropdown-button,
body.cs-theme-dark #cs-palette-set-combo-btn,
body.cs-theme-dark .cs-modal-select-button {{
    background: #3a3d42 !important;
    color: #f3f4f6 !important;
}}
body.cs-theme-dark .cs-palette-dropdown-button::after,
body.cs-theme-dark #cs-palette-set-combo-btn::after,
body.cs-theme-dark .cs-modal-select-button::after {{
    border-right-color: #cbd5e1 !important;
    border-bottom-color: #cbd5e1 !important;
}}
body.cs-theme-dark .cs-palette-dropdown-menu,
body.cs-theme-dark #cs-palette-set-combo-menu,
body.cs-theme-dark .cs-modal-select-menu {{
    background: #3a3d42 !important;
    color: #f3f4f6 !important;
}}
body.cs-theme-dark .cs-palette-dropdown-item,
body.cs-theme-dark .cs-modal-select-item {{
    background: #3a3d42 !important;
    color: #f3f4f6 !important;
}}
body.cs-theme-dark .cs-palette-dropdown-item:hover,
body.cs-theme-dark .cs-palette-dropdown-item:focus,
body.cs-theme-dark .cs-palette-dropdown-item.active:hover,
body.cs-theme-dark .cs-palette-dropdown-item.active:focus,
body.cs-theme-dark .cs-modal-select-item:hover,
body.cs-theme-dark .cs-modal-select-item:focus,
body.cs-theme-dark .cs-modal-select-item.active:hover,
body.cs-theme-dark .cs-modal-select-item.active:focus {{
    background: #444850 !important;
    color: #ff5b66 !important;
}}
body.cs-theme-dark .cs-palette-dropdown-item.active,
body.cs-theme-dark .cs-palette-dropdown-item:active,
body.cs-theme-dark .cs-palette-dropdown-item.active:active,
body.cs-theme-dark .cs-modal-select-item.active,
body.cs-theme-dark .cs-modal-select-item:active,
body.cs-theme-dark .cs-modal-select-item.active:active {{
    background: #3a3d42 !important;
    color: #f3f4f6 !important;
}}

/* white area under/around manual shard cards */
body.cs-theme-dark #piece-palette,
body.cs-theme-dark .palette,
body.cs-theme-dark #piece-palette .piece-grid,
body.cs-theme-dark .palette .piece-grid {{
    background: #24262a !important;
    background-color: #24262a !important;
}}
body.cs-theme-dark #piece-palette::before,
body.cs-theme-dark #piece-palette::after,
body.cs-theme-dark .palette::before,
body.cs-theme-dark .palette::after,
body.cs-theme-dark #piece-palette .piece-grid::before,
body.cs-theme-dark #piece-palette .piece-grid::after,
body.cs-theme-dark .palette .piece-grid::before,
body.cs-theme-dark .palette .piece-grid::after {{
    background: #303236 !important;
    background-color: #303236 !important;
}}
body.cs-theme-dark .pieces-section.cs-card {{
    background: #303236 !important;
}}
body.cs-theme-dark #piece-palette .piece-item {{
    background: #202124 !important;
}}
body.cs-theme-dark #piece-palette .piece-item > .piece-preview {{
    background: #242528 !important;
}}
body.cs-theme-dark #piece-palette .piece-count-input {{
    background: #202124 !important;
    color: #ffffff !important;
    border-color: #303236 !important;
}}
body.cs-theme-dark #piece-palette::-webkit-scrollbar-track,
body.cs-theme-dark .palette::-webkit-scrollbar-track {{
    background: #303236 !important;
}}
body.cs-theme-dark #piece-palette::-webkit-scrollbar-corner,
body.cs-theme-dark .palette::-webkit-scrollbar-corner {{
    background: #303236 !important;
}}


/* guide keywords: keep bold weight only, inherit surrounding text color (all languages/themes) */
#usage-modal .usage-keyword {{
    color: inherit !important;
}}
#usage-modal .usage-heading .usage-keyword {{
    color: var(--cs-accent) !important;
}}


/* final button color tuning */
body.cs-theme-dark #solve-btn,
body.cs-theme-dark #upload-btn {{
    background: linear-gradient(135deg, #ff4048, #ff3434) !important;
    color: #ffffff !important;
}}
body.cs-theme-dark #clear-pieces-btn,
body.cs-theme-dark #usage-btn {{
    background: #3a3d42 !important;
    color: #ffffff !important;
}}
body.cs-theme-dark #clear-pieces-btn:hover,
body.cs-theme-dark #usage-btn:hover {{
    background: #444850 !important;
    color: #ffffff !important;
}}


/* exact manual palette color mapping */
body.cs-theme-dark .pieces-section.cs-card,
body.cs-theme-dark #piece-palette,
body.cs-theme-dark .palette,
body.cs-theme-dark #piece-palette .piece-grid,
body.cs-theme-dark .palette .piece-grid,
body.cs-theme-dark #piece-palette::before,
body.cs-theme-dark #piece-palette::after,
body.cs-theme-dark .palette::before,
body.cs-theme-dark .palette::after,
body.cs-theme-dark #piece-palette .piece-grid::before,
body.cs-theme-dark #piece-palette .piece-grid::after,
body.cs-theme-dark .palette .piece-grid::before,
body.cs-theme-dark .palette .piece-grid::after {{
    background: #24262a !important;
    background-color: #24262a !important;
}}
body.cs-theme-dark #piece-palette,
body.cs-theme-dark .palette {{
    scrollbar-color: #9ca3af #24262a !important;
}}
body.cs-theme-dark #piece-palette::-webkit-scrollbar-track,
body.cs-theme-dark .palette::-webkit-scrollbar-track,
body.cs-theme-dark #piece-palette::-webkit-scrollbar-corner,
body.cs-theme-dark .palette::-webkit-scrollbar-corner {{
    background: #24262a !important;
}}
body.cs-theme-dark #piece-palette .piece-item,
body.cs-theme-dark #piece-palette .piece-count-input {{
    background: #303236 !important;
    background-color: #303236 !important;
}}
body.cs-theme-dark #piece-palette .piece-item > .piece-preview {{
    background: #303236 !important;
    background-color: #303236 !important;
}}
body.cs-theme-dark #piece-palette .piece-count-input {{
    color: #ffffff !important;
    border-color: #24262a !important;
}}


/* restore outer palette box color */
body.cs-theme-dark .pieces-section.cs-card {{
    background: #303236 !important;
    background-color: #303236 !important;
}}


/* piece card outer color final */
body.cs-theme-dark #piece-palette .piece-item {{
    background: #24262a !important;
    background-color: #24262a !important;
}}
body.cs-theme-dark #piece-palette .piece-item > .piece-preview {{
    background: #303236 !important;
    background-color: #303236 !important;
}}
body.cs-theme-dark #piece-palette .piece-count-input {{
    background: #303236 !important;
    background-color: #303236 !important;
    color: #ffffff !important;
}}


/* palette empty area color final */
body.cs-theme-dark #piece-palette,
body.cs-theme-dark .palette,
body.cs-theme-dark #piece-palette .piece-grid,
body.cs-theme-dark .palette .piece-grid,
body.cs-theme-dark #piece-palette::before,
body.cs-theme-dark #piece-palette::after,
body.cs-theme-dark .palette::before,
body.cs-theme-dark .palette::after,
body.cs-theme-dark #piece-palette .piece-grid::before,
body.cs-theme-dark #piece-palette .piece-grid::after,
body.cs-theme-dark .palette .piece-grid::before,
body.cs-theme-dark .palette .piece-grid::after {{
    background: #303236 !important;
    background-color: #303236 !important;
}}
body.cs-theme-dark #piece-palette::-webkit-scrollbar-track,
body.cs-theme-dark .palette::-webkit-scrollbar-track,
body.cs-theme-dark #piece-palette::-webkit-scrollbar-corner,
body.cs-theme-dark .palette::-webkit-scrollbar-corner {{
    background: #303236 !important;
}}
body.cs-theme-dark #piece-palette,
body.cs-theme-dark .palette {{
    scrollbar-color: #9ca3af #303236 !important;
}}

/* dark-mode native form controls (number input spinners etc.) */
body.cs-theme-dark input,
body.cs-theme-dark select,
body.cs-theme-dark textarea {{
    color-scheme: dark;
}}

/* result set-bonus box & target box: match dropdown background in dark mode */
body.cs-theme-dark .cs-result-card .cs-set-bonus-box,
body.cs-theme-dark .cs-result-card .solution-wrapper > div[style*="fff7f7"],
body.cs-theme-dark .cs-result-card .solution-wrapper > div[style*="255, 247, 247"] {{
    background: #3a3d42 !important;
    color: #f3f4f6 !important;
}}
body.cs-theme-dark .cs-result-card .cs-set-bonus-box *,
body.cs-theme-dark .cs-result-card .solution-wrapper > div[style*="fff7f7"] *,
body.cs-theme-dark .cs-result-card .solution-wrapper > div[style*="255, 247, 247"] * {{
    color: #f3f4f6 !important;
}}
body.cs-theme-dark .cs-target {{
    background: #3a3d42 !important;
    background-color: #3a3d42 !important;
}}

/* set-selection modal polish */
body.cs-theme-dark > div[style*="z-index: 2000"] .piece-preview {{
    background: #303236 !important;
}}
body.cs-theme-dark > div[style*="z-index: 2000"] .cs-modal-set-label {{
    color: var(--cs-text) !important;
}}
body.cs-theme-dark > div[style*="z-index: 2000"]::-webkit-scrollbar-track,
body.cs-theme-dark > div[style*="z-index: 2000"] > div::-webkit-scrollbar-track,
body.cs-theme-dark > div[style*="z-index: 2000"] *::-webkit-scrollbar-track {{
    background: #303236 !important;
}}
/* page scrollbar styling removed: global html/body scrollbar CSS was leaking into the SELECT/Setting tab.
   Keep scrollbar styling scoped to shard palette/modals only. */
/* prevent raw (pre-tuned) palette flash on load / theme change */
.pieces-section {{
    opacity: 0;
    transition: none;
}}
body.cs-palette-ready .pieces-section {{
    opacity: 1;
}}
.pieces-section div:has(> .tab-btn) {{
    display: none !important;
}}
#piece-palette .tab-content > div:first-child {{
    display: none !important;
}}
/* ===== shard picker (z-index 3000): red hover + selected + proper dark mode ===== */
body > div[style*="z-index: 3000"] .cs-picker-card {{
    transition: background-color 0.15s ease, border-color 0.15s ease !important;
    transform: none !important;
    box-shadow: none !important;
}}
body > div[style*="z-index: 3000"] .cs-picker-card:hover {{
    border-color: rgba(255, 64, 72, 0.6) !important;
}}
body > div[style*="z-index: 3000"] .cs-picker-card[data-cs-selected="true"] {{
    border: 2px solid rgba(255, 64, 72, 0.85) !important;
}}

/* dark mode: make the picker actually dark */
body.cs-theme-dark > div[style*="z-index: 3000"] > div {{
    background: #303236 !important;
    scrollbar-color: #6b7280 #303236;
}}
body.cs-theme-dark > div[style*="z-index: 3000"] h3 {{
    color: #f3f4f6 !important;
}}
body.cs-theme-dark > div[style*="z-index: 3000"] .cs-picker-card {{
    background: #303236 !important;
    border: 1px solid #4a4d54 !important;
}}
body.cs-theme-dark > div[style*="z-index: 3000"] .piece-preview {{
    background: #303236 !important;
}}
body.cs-theme-dark > div[style*="z-index: 3000"] .preview-cell:not(.preview-cell-filled) {{
    border-color: #43464c !important;
}}
body.cs-theme-dark > div[style*="z-index: 3000"] button {{
    background: #3a3d42 !important;
    color: #f3f4f6 !important;
}}
body.cs-theme-dark > div[style*="z-index: 3000"] *::-webkit-scrollbar-track {{
    background: #303236 !important;
}}
body.cs-theme-dark > div[style*="z-index: 3000"] *::-webkit-scrollbar-thumb {{
    background: #6b7280 !important;
    border-radius: 8px;
}}
body.cs-theme-dark > div[style*="z-index: 3000"] .cs-picker-card:hover {{
    border-color: rgba(255, 91, 102, 0.65) !important;
}}
body.cs-theme-dark > div[style*="z-index: 3000"] .cs-picker-card[data-cs-selected="true"] {{
    border-color: rgba(255, 91, 102, 0.9) !important;
}}
@media (prefers-color-scheme: dark) {{
    body.cs-theme-system > div[style*="z-index: 3000"] > div {{
        background: #303236 !important;
        scrollbar-color: #6b7280 #303236;
    }}
    body.cs-theme-system > div[style*="z-index: 3000"] h3 {{
        color: #f3f4f6 !important;
    }}
    body.cs-theme-system > div[style*="z-index: 3000"] .cs-picker-card {{
        background: #303236 !important;
        border: 1px solid #4a4d54 !important;
    }}
    body.cs-theme-system > div[style*="z-index: 3000"] .piece-preview {{
        background: #303236 !important;
    }}
    body.cs-theme-system > div[style*="z-index: 3000"] .preview-cell:not(.preview-cell-filled) {{
        border-color: #43464c !important;
    }}
    body.cs-theme-system > div[style*="z-index: 3000"] button {{
        background: #3a3d42 !important;
        color: #f3f4f6 !important;
    }}
    body.cs-theme-system > div[style*="z-index: 3000"] *::-webkit-scrollbar-track {{
        background: #303236 !important;
    }}
    body.cs-theme-system > div[style*="z-index: 3000"] *::-webkit-scrollbar-thumb {{
        background: #6b7280 !important;
        border-radius: 8px;
    }}
    body.cs-theme-system > div[style*="z-index: 3000"] .cs-picker-card:hover {{
        border-color: rgba(255, 91, 102, 0.65) !important;
    }}
    body.cs-theme-system > div[style*="z-index: 3000"] .cs-picker-card[data-cs-selected="true"] {{
        border-color: rgba(255, 91, 102, 0.9) !important;
    }}
}}

/* final modal color fixes: keep picker border gray, make only background turn red */
body > div[style*="z-index: 3000"] .cs-picker-card {{
    border: 1px solid #e5e7eb !important;
    background: #fff !important;
    transition: background-color 0.15s ease !important;
    box-shadow: none !important;
}}
body > div[style*="z-index: 3000"] .cs-picker-card:hover,
body > div[style*="z-index: 3000"] .cs-picker-card[data-cs-selected="true"] {{
    border: 1px solid #d1d5db !important;
    background: rgba(107, 114, 128, 0.14) !important;
    box-shadow: none !important;
}}
body > div[style*="z-index: 3000"] .cs-picker-card .piece-preview {{
    background: transparent !important;
}}
body > div[style*="z-index: 3000"] .cs-picker-card:hover .piece-preview,
body > div[style*="z-index: 3000"] .cs-picker-card[data-cs-selected="true"] .piece-preview {{
    background: transparent !important;
}}
body > div[style*="z-index: 3000"] .cs-grade-title {{
    color: #374151 !important;
}}
body > div[style*="z-index: 3000"] .cs-grade-pick-btn {{
    border: 0 !important;
    background: #f3f4f6 !important;
    color: #9ca3af !important;
    box-shadow: none !important;
}}
body > div[style*="z-index: 3000"] .cs-grade-pick-btn.cs-grade-rare:hover,
body > div[style*="z-index: 3000"] .cs-grade-pick-btn.cs-grade-rare:focus {{
    background: rgba(100, 150, 255, 0.2) !important;
    color: #5d8cff !important;
}}
body > div[style*="z-index: 3000"] .cs-grade-pick-btn.cs-grade-epic:hover,
body > div[style*="z-index: 3000"] .cs-grade-pick-btn.cs-grade-epic:focus {{
    background: rgba(200, 100, 255, 0.2) !important;
    color: #b46bff !important;
}}
body > div[style*="z-index: 3000"] .cs-grade-pick-btn.cs-grade-super:hover,
body > div[style*="z-index: 3000"] .cs-grade-pick-btn.cs-grade-super:focus {{
    background: rgba(255, 100, 100, 0.2) !important;
    color: #ff5b66 !important;
}}
body > div[style*="z-index: 3000"] .cs-grade-pick-btn.cs-grade-unique:hover,
body > div[style*="z-index: 3000"] .cs-grade-pick-btn.cs-grade-unique:focus {{
    background: rgba(255, 204, 0, 0.28) !important;
    color: #ffcc00 !important;
}}
body > div[style*="z-index: 2000"] .cs-set-chip {{
    background: #fff !important;
    color: #10b981 !important;
}}
body > div[style*="z-index: 2000"] .cs-modal-stat-chip {{
    background: #fff !important;
    color: #111827 !important;
}}
body > div[style*="z-index: 2000"] .cs-count-badge {{
    background: #fff !important;
}}
body > div[style*="z-index: 2000"] .cs-count-badge.cs-grade-rare {{ color: #5d8cff !important; }}
body > div[style*="z-index: 2000"] .cs-count-badge.cs-grade-epic {{ color: #b46bff !important; }}
body > div[style*="z-index: 2000"] .cs-count-badge.cs-grade-super {{ color: #ff5b66 !important; }}
body > div[style*="z-index: 2000"] .cs-count-badge.cs-grade-unique {{ color: #ffcc00 !important; }}

body.cs-theme-dark > div[style*="z-index: 3000"] .cs-picker-card {{
    border: 1px solid #4a4d54 !important;
    background: #303236 !important;
}}
body.cs-theme-dark > div[style*="z-index: 3000"] .cs-picker-card:hover,
body.cs-theme-dark > div[style*="z-index: 3000"] .cs-picker-card[data-cs-selected="true"] {{
    border: 1px solid #5a5f68 !important;
    background: rgba(255, 255, 255, 0.10) !important;
}}
body.cs-theme-dark > div[style*="z-index: 3000"] .cs-picker-card .piece-preview {{
    background: transparent !important;
}}
body.cs-theme-dark > div[style*="z-index: 3000"] .cs-grade-title {{ color: #f3f4f6 !important; }}
body.cs-theme-dark > div[style*="z-index: 3000"] .cs-grade-pick-btn {{
    border: 0 !important;
    background: #3a3d42 !important;
    color: #9ca3af !important;
}}
body.cs-theme-dark > div[style*="z-index: 3000"] .cs-grade-pick-btn.cs-grade-rare:hover,
body.cs-theme-dark > div[style*="z-index: 3000"] .cs-grade-pick-btn.cs-grade-rare:focus {{
    background: rgba(100, 150, 255, 0.2) !important;
    color: #5d8cff !important;
}}
body.cs-theme-dark > div[style*="z-index: 3000"] .cs-grade-pick-btn.cs-grade-epic:hover,
body.cs-theme-dark > div[style*="z-index: 3000"] .cs-grade-pick-btn.cs-grade-epic:focus {{
    background: rgba(200, 100, 255, 0.2) !important;
    color: #b46bff !important;
}}
body.cs-theme-dark > div[style*="z-index: 3000"] .cs-grade-pick-btn.cs-grade-super:hover,
body.cs-theme-dark > div[style*="z-index: 3000"] .cs-grade-pick-btn.cs-grade-super:focus {{
    background: rgba(255, 100, 100, 0.2) !important;
    color: #ff5b66 !important;
}}
body.cs-theme-dark > div[style*="z-index: 3000"] .cs-grade-pick-btn.cs-grade-unique:hover,
body.cs-theme-dark > div[style*="z-index: 3000"] .cs-grade-pick-btn.cs-grade-unique:focus {{
    background: rgba(255, 204, 0, 0.28) !important;
    color: #ffcc00 !important;
}}
body.cs-theme-dark > div[style*="z-index: 2000"] .cs-set-chip {{
    background: #303236 !important;
    color: #10b981 !important;
}}
body.cs-theme-dark > div[style*="z-index: 2000"] .cs-modal-stat-chip {{
    background: #303236 !important;
    color: #f3f4f6 !important;
}}
body.cs-theme-dark > div[style*="z-index: 2000"] .cs-count-badge {{
    background: #303236 !important;
}}
body.cs-theme-dark > div[style*="z-index: 2000"] .cs-count-badge.cs-grade-rare {{ color: #5d8cff !important; }}
body.cs-theme-dark > div[style*="z-index: 2000"] .cs-count-badge.cs-grade-epic {{ color: #b46bff !important; }}
body.cs-theme-dark > div[style*="z-index: 2000"] .cs-count-badge.cs-grade-super {{ color: #ff5b66 !important; }}
body.cs-theme-dark > div[style*="z-index: 2000"] .cs-count-badge.cs-grade-unique {{ color: #ffcc00 !important; }}
@media (prefers-color-scheme: dark) {{
    body.cs-theme-system > div[style*="z-index: 3000"] .cs-picker-card {{
        border: 1px solid #4a4d54 !important;
        background: #303236 !important;
    }}
    body.cs-theme-system > div[style*="z-index: 3000"] .cs-picker-card:hover,
    body.cs-theme-system > div[style*="z-index: 3000"] .cs-picker-card[data-cs-selected="true"] {{
        border: 1px solid #5a5f68 !important;
        background: rgba(255, 255, 255, 0.10) !important;
    }}
    body.cs-theme-system > div[style*="z-index: 3000"] .cs-picker-card .piece-preview {{
        background: transparent !important;
    }}
    body.cs-theme-system > div[style*="z-index: 3000"] .cs-grade-title {{ color: #f3f4f6 !important; }}
    body.cs-theme-system > div[style*="z-index: 3000"] .cs-grade-pick-btn {{
        border: 0 !important;
        background: #3a3d42 !important;
        color: #9ca3af !important;
    }}
    body.cs-theme-system > div[style*="z-index: 3000"] .cs-grade-pick-btn.cs-grade-rare:hover,
    body.cs-theme-system > div[style*="z-index: 3000"] .cs-grade-pick-btn.cs-grade-rare:focus {{
        background: rgba(100, 150, 255, 0.2) !important;
        color: #5d8cff !important;
    }}
    body.cs-theme-system > div[style*="z-index: 3000"] .cs-grade-pick-btn.cs-grade-epic:hover,
    body.cs-theme-system > div[style*="z-index: 3000"] .cs-grade-pick-btn.cs-grade-epic:focus {{
        background: rgba(200, 100, 255, 0.2) !important;
        color: #b46bff !important;
    }}
    body.cs-theme-system > div[style*="z-index: 3000"] .cs-grade-pick-btn.cs-grade-super:hover,
    body.cs-theme-system > div[style*="z-index: 3000"] .cs-grade-pick-btn.cs-grade-super:focus {{
        background: rgba(255, 100, 100, 0.2) !important;
        color: #ff5b66 !important;
    }}
    body.cs-theme-system > div[style*="z-index: 3000"] .cs-grade-pick-btn.cs-grade-unique:hover,
    body.cs-theme-system > div[style*="z-index: 3000"] .cs-grade-pick-btn.cs-grade-unique:focus {{
        background: rgba(255, 204, 0, 0.28) !important;
        color: #ffcc00 !important;
    }}
    body.cs-theme-system > div[style*="z-index: 2000"] .cs-set-chip {{
        background: #303236 !important;
        color: #10b981 !important;
    }}
    body.cs-theme-system > div[style*="z-index: 2000"] .cs-modal-stat-chip {{
        background: #303236 !important;
        color: #f3f4f6 !important;
    }}
    body.cs-theme-system > div[style*="z-index: 2000"] .cs-count-badge {{
        background: #303236 !important;
    }}
    body.cs-theme-system > div[style*="z-index: 2000"] .cs-count-badge.cs-grade-rare {{ color: #5d8cff !important; }}
    body.cs-theme-system > div[style*="z-index: 2000"] .cs-count-badge.cs-grade-epic {{ color: #b46bff !important; }}
    body.cs-theme-system > div[style*="z-index: 2000"] .cs-count-badge.cs-grade-super {{ color: #ff5b66 !important; }}
    body.cs-theme-system > div[style*="z-index: 2000"] .cs-count-badge.cs-grade-unique {{ color: #ffcc00 !important; }}
}}

/* dark mode: dim empty preview-cell borders everywhere (palette etc.) */
body.cs-theme-dark .preview-cell:not(.preview-cell-filled) {{
    border-color: #43464c !important;
}}
@media (prefers-color-scheme: dark) {{
    body.cs-theme-system .preview-cell:not(.preview-cell-filled) {{
        border-color: #43464c !important;
    }}
}}

/* glass stat carousel: title bar + side arrows around the result board */
.cs-glass-stat-bar {{
    background: #f3f4f6;
    border-radius: 10px;
    padding: 9px 14px;
    font-weight: 800;
    font-size: 13px;
    color: #374151;
    margin: 6px 0 10px;
    text-align: center;
}}
body.cs-theme-dark .cs-glass-stat-bar {{
    background: #3a3d42;
    color: #f3f4f6;
}}
.cs-glass-carousel {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
}}
.cs-glass-arrow {{
    width: 30px;
    height: 30px;
    border-radius: 50%;
    border: none;
    background: #f3f4f6;
    color: #374151;
    font-size: 18px;
    font-weight: 800;
    cursor: pointer;
    flex: 0 0 30px;
    line-height: 1;
    padding: 0;
}}
.cs-glass-arrow:hover {{
    color: #ff4048;
}}
body.cs-theme-dark .cs-glass-arrow {{
    background: #3a3d42;
    color: #f3f4f6;
}}
body.cs-theme-dark .cs-glass-arrow:hover {{
    color: #ff5b66;
}}



/* stat legend lines inside the stat-view page */
.cs-glass-pages {{
    flex: 1 1 auto;
    min-width: 0;
}}
.cs-stat-legend-line {{
    display: flex;
    align-items: center;
    gap: 6px;
    margin: 3px 0 3px 0px;
    font-size: 12px !important;
    line-height: 1.2 !important;
}}


/* result board top breathing room: match bottom space */
.cs-result-card .cs-glass-pages .solution-grid,
.cs-result-card .cs-glass-carousel .solution-grid {{
    margin-top: 8px !important;
    margin-left: auto !important;
    margin-right: auto !important;
    margin-bottom: 0 !important;
}}

/* stat/set result boards must have the exact same drawing style */
.cs-result-card .cs-glass-carousel .solution-grid,
.cs-result-card .cs-glass-pages .solution-grid {{
    transform: none !important;
    grid-template-columns: repeat(7, 24px) !important;
    grid-template-rows: repeat(7, 24px) !important;
    width: 168px !important;
    min-width: 168px !important;
    max-width: 168px !important;
    height: 168px !important;
    min-height: 168px !important;
    max-height: 168px !important;
    box-sizing: content-box !important;
}}
.cs-result-card .cs-glass-carousel .solution-cell,
.cs-result-card .cs-glass-pages .solution-cell {{
    width: 24px !important;
    min-width: 24px !important;
    max-width: 24px !important;
    height: 24px !important;
    min-height: 24px !important;
    max-height: 24px !important;
    border-radius: 0 !important;
    margin: 0 !important;
    box-sizing: border-box !important;
    font-size: 0.75em !important;
    font-weight: 800 !important;
    line-height: 1 !important;
}}

.cs-stat-legend-chip {{
    width: 12px;
    height: 12px;
    border-radius: 3px;
    border: 1px solid rgba(17, 24, 39, 0.08);
    flex: 0 0 12px;
    display: inline-block;
}}


/* cookie-sim: result split layout fix
   Split the result area exactly into left/right halves.
   Left half = bonus/stat box fills the side. Right half = board centered. */
.cs-result-card .solutions-container {{
    align-items: stretch !important;
}}
.cs-result-card .solution-wrapper {{
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 auto !important;
    align-self: stretch !important;
    min-height: 0 !important;
}}
.cs-result-card .cs-glass-carousel {{
    position: relative !important;
    display: flex !important;
    flex: 1 1 auto !important;
    width: 100% !important;
    min-height: 200px !important;
    align-items: stretch !important;
    justify-content: stretch !important;
    gap: 0 !important;
    padding: 0 !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-glass-carousel .cs-glass-pages {{
    flex: 1 1 auto !important;
    width: 100% !important;
    height: 100% !important;
    min-height: 200px !important;
    max-width: none !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-glass-pages > div {{
    width: 100% !important;
    height: 100% !important;
    min-height: 200px !important;
    box-sizing: border-box !important;
    gap: 8px !important;
    align-items: stretch !important;
    justify-content: stretch !important;
}}
.cs-result-card .cs-glass-pages > div:not([style*="display: none"]) {{
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) !important;
    grid-template-rows: minmax(200px, 1fr) !important;
    column-gap: 8px !important;
    align-content: stretch !important;
}}
.cs-result-card .cs-glass-pages > div > .cs-set-bonus-box {{
    grid-column: 1 !important;
    width: 100% !important;
    min-width: 0 !important;
    max-width: none !important;
    height: 100% !important;
    min-height: 200px !important;
    align-self: stretch !important;
    justify-self: stretch !important;
    margin: 0 !important;
    box-sizing: border-box !important;
    flex: none !important;
}}
.cs-result-card .cs-glass-pages > div > .solution-grid {{
    grid-column: 2 !important;
    justify-self: center !important;
    align-self: center !important;
    flex: none !important;
    margin: 0 !important;
}}

/* cookie-sim: add the same soft panel behind the placement board */
.cs-result-card .cs-glass-pages > div::before {{
    content: "" !important;
    grid-column: 2 !important;
    grid-row: 1 !important;
    width: 100% !important;
    height: 100% !important;
    min-height: 200px !important;
    align-self: stretch !important;
    justify-self: stretch !important;
    background: #fff7f7 !important;
    border-radius: 10px !important;
    box-sizing: border-box !important;
    z-index: 0 !important;
}}
.cs-result-card .cs-glass-pages > div > .cs-set-bonus-box {{
    grid-row: 1 !important;
    position: relative !important;
    z-index: 1 !important;
}}
.cs-result-card .cs-glass-pages > div > .solution-grid {{
    grid-row: 1 !important;
    position: relative !important;
    z-index: 1 !important;
}}
body.cs-theme-dark .cs-result-card .cs-glass-pages > div::before {{
    background: #3a3d42 !important;
}}
@media (prefers-color-scheme: dark) {{
    body.cs-theme-system .cs-result-card .cs-glass-pages > div::before {{
        background: #3a3d42 !important;
    }}
}}
.cs-result-card .cs-glass-carousel > .cs-glass-arrow {{
    position: absolute !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    z-index: 80 !important;
    box-shadow: none !important;
}}
.cs-result-card .cs-glass-carousel > .cs-glass-arrow-left,
.cs-result-card .cs-glass-carousel > .cs-glass-arrow:first-child {{
    left: -15px !important;
    right: auto !important;
}}
.cs-result-card .cs-glass-carousel > .cs-glass-arrow-right,
.cs-result-card .cs-glass-carousel > .cs-glass-arrow:last-child {{
    left: auto !important;
    right: -15px !important;
}}
@media (max-width: 430px) {{
    .cs-result-card .cs-glass-pages > div:not([style*="display: none"]) {{
        grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) !important;
    }}
    .cs-result-card .cs-glass-pages > div > .cs-set-bonus-box {{
        min-width: 0 !important;
        max-width: none !important;
    }}
}}

/* solve progress line (below run/reset buttons, centered) */
#cs-solve-progress {{
    text-align: center;
    font-size: 11px;
    font-weight: 700;
    line-height: 1.35;
    min-height: 15px;
    color: #6b7280;
    margin: 8px auto 0px;
}}
#cs-solve-progress:empty {{
    display: none;
    margin: 0;
    min-height: 0;
}}
body.cs-theme-dark #cs-solve-progress {{
    color: #9ca3af;
}}

/* recognized-shards modal: same faint empty-cell design as the picker */
body.cs-theme-dark > div[style*="z-index: 2000"] .preview-cell:not(.preview-cell-filled) {{
    border-color: #43464c !important;
}}
@media (prefers-color-scheme: dark) {{
    body.cs-theme-system > div[style*="z-index: 2000"] .preview-cell:not(.preview-cell-filled) {{
        border-color: #43464c !important;
    }}
}}




/* cookie-sim: final responsive board shrink + right-panel title */
.cs-result-card .cs-glass-pages > div:not([style*="display: none"]) {{
    grid-template-rows: minmax(200px, 1fr) !important;
    align-items: center !important;
    align-content: stretch !important;
}}
.cs-result-card .cs-glass-pages > div::after {{
    content: "{texts['result_title']}" !important;
    grid-column: 2 !important;
    grid-row: 1 !important;
    align-self: start !important;
    justify-self: start !important;
    margin: 13px 0 0 16px !important;
    color: #374151 !important;
    font-size: 12px !important;
    font-weight: 800 !important;
    line-height: 1 !important;
    position: relative !important;
    z-index: 3 !important;
    pointer-events: none !important;
}}
body.cs-theme-dark .cs-result-card .cs-glass-pages > div::after {{
    color: #f3f4f6 !important;
}}
@media (prefers-color-scheme: dark) {{
    body.cs-theme-system .cs-result-card .cs-glass-pages > div::after {{
        color: #f3f4f6 !important;
    }}
}}
.cs-result-card .cs-glass-pages > div > .cs-set-bonus-box,
.cs-result-card .cs-glass-pages > div::before {{
    align-self: stretch !important;
}}
.cs-result-card .cs-glass-carousel .solution-grid,
.cs-result-card .cs-glass-pages .solution-grid,
.cs-result-card .cs-glass-pages > div > .solution-grid,
.cs-result-card .solution-grid {{
    grid-template-columns: repeat(7, minmax(0, 1fr)) !important;
    grid-template-rows: repeat(7, minmax(0, 1fr)) !important;
    width: min(160px, 74%) !important;
    min-width: 0 !important;
    max-width: 160px !important;
    height: auto !important;
    min-height: 0 !important;
    max-height: none !important;
    aspect-ratio: 1 / 1 !important;
    align-self: center !important;
    justify-self: center !important;
    margin: 0 auto !important;
    box-sizing: border-box !important;
    flex: 0 1 auto !important;
    transform: translateY(10px) !important;
}}
.cs-result-card .cs-glass-carousel .solution-cell,
.cs-result-card .cs-glass-pages .solution-cell,
.cs-result-card .cs-glass-pages > div > .solution-grid .solution-cell,
.cs-result-card .solution-cell {{
    width: auto !important;
    min-width: 0 !important;
    max-width: none !important;
    height: auto !important;
    min-height: 0 !important;
    max-height: none !important;
    aspect-ratio: auto !important;
    box-sizing: border-box !important;
}}


/* cookie-sim: single result layout + collapsible stat detail */
.cs-result-card .cs-glass-carousel.cs-glass-single {{
    position: relative !important;
    display: flex !important;
    width: 100% !important;
    min-height: 0 !important;
    height: auto !important;
    align-items: stretch !important;
    justify-content: center !important;
    padding: 0 !important;
    gap: 0 !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-glass-carousel.cs-glass-single .cs-glass-pages {{
    width: 100% !important;
    height: auto !important;
    min-height: 0 !important;
    max-width: none !important;
    flex: 1 1 auto !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-glass-carousel.cs-glass-single .cs-glass-pages > .cs-glass-single-page,
.cs-result-card .cs-glass-carousel.cs-glass-single .cs-glass-pages > div:not([style*="display: none"]).cs-glass-single-page {{
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: flex-start !important;
    gap: 8px !important;
    grid-template-columns: none !important;
    grid-template-rows: none !important;
    width: 100% !important;
    height: auto !important;
    min-height: 0 !important;
    padding: 10px 10px 12px !important;
    background: #fff7f7 !important;
    border-radius: 10px !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-glass-carousel.cs-glass-single .cs-glass-pages > .cs-glass-single-page::before,
.cs-result-card .cs-glass-carousel.cs-glass-single .cs-glass-pages > .cs-glass-single-page::after {{
    content: none !important;
    display: none !important;
}}
.cs-result-card .cs-glass-carousel.cs-glass-single .cs-set-bonus-box:not(.cs-stat-legend) {{
    display: flex !important;
    flex-wrap: wrap !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 5px !important;
    width: 100% !important;
    height: auto !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    background: transparent !important;
    border: 0 !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-glass-carousel.cs-glass-single .cs-set-bonus-box:not(.cs-stat-legend) > div:first-child,
.cs-result-card .cs-glass-carousel.cs-glass-single .cs-set-bonus-box:not(.cs-stat-legend) > div[style*="height: 1px"] {{
    display: none !important;
}}
.cs-result-card .cs-glass-carousel.cs-glass-single .cs-set-bonus-box:not(.cs-stat-legend) > div:not(:first-child):not([style*="height: 1px"]) {{
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 5px !important;
    flex: 0 0 auto !important;
    width: auto !important;
    min-width: 0 !important;
    height: auto !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 4px 8px !important;
    border-radius: 999px !important;
    background: rgba(255, 255, 255, 0.72) !important;
    color: #374151 !important;
    font-size: 11px !important;
    font-weight: 800 !important;
    line-height: 1.15 !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-board-panel {{
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 7px !important;
    width: 100% !important;
    min-height: 182px !important;
    margin: 0 !important;
    padding: 0 !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-board-title {{
    align-self: flex-start !important;
    margin: 0 0 0 4px !important;
    color: #374151 !important;
    font-size: 12px !important;
    font-weight: 800 !important;
    line-height: 1.2 !important;
}}
.cs-result-card .cs-glass-carousel.cs-glass-single .solution-grid,
.cs-result-card .cs-glass-carousel.cs-glass-single .cs-glass-pages .solution-grid,
.cs-result-card .cs-glass-carousel.cs-glass-single .cs-glass-pages > div > .solution-grid {{
    grid-template-columns: repeat(7, minmax(0, 1fr)) !important;
    grid-template-rows: repeat(7, minmax(0, 1fr)) !important;
    width: 168px !important;
    min-width: 168px !important;
    max-width: 168px !important;
    height: 168px !important;
    min-height: 168px !important;
    max-height: 168px !important;
    aspect-ratio: 1 / 1 !important;
    align-self: center !important;
    justify-self: center !important;
    margin: 0 auto !important;
    transform: none !important;
    box-sizing: content-box !important;
    flex: 0 0 auto !important;
}}
.cs-result-card .cs-glass-carousel.cs-glass-single .solution-cell,
.cs-result-card .cs-glass-carousel.cs-glass-single .cs-glass-pages .solution-cell,
.cs-result-card .cs-glass-carousel.cs-glass-single .cs-glass-pages > div > .solution-grid .solution-cell {{
    width: 24px !important;
    min-width: 24px !important;
    max-width: 24px !important;
    height: 24px !important;
    min-height: 24px !important;
    max-height: 24px !important;
    border-radius: 0 !important;
    margin: 0 !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-stat-details {{
    width: 100% !important;
    max-width: 320px !important;
    margin: 0 auto !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-stat-toggle {{
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    gap: 8px !important;
    border: 0 !important;
    border-radius: 9px !important;
    background: rgba(255, 255, 255, 0.72) !important;
    color: #374151 !important;
    padding: 7px 10px !important;
    font-size: 12px !important;
    font-weight: 800 !important;
    line-height: 1.2 !important;
    cursor: pointer !important;
    box-shadow: none !important;
    outline: 0 !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-stat-toggle:hover {{
    color: #ff4048 !important;
}}
.cs-result-card .cs-stat-toggle-arrow {{
    font-size: 10px !important;
    line-height: 1 !important;
    flex: 0 0 auto !important;
}}
.cs-result-card .cs-stat-detail-content {{
    margin-top: 7px !important;
    padding: 8px !important;
    border-radius: 9px !important;
    background: rgba(255, 255, 255, 0.62) !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-stat-detail-content .cs-stat-legend {{
    width: 100% !important;
    margin: 0 0 8px 0 !important;
    padding: 0 !important;
    background: transparent !important;
    border: 0 !important;
}}
.cs-result-card .cs-stat-detail-content .cs-stat-legend > div:first-child {{
    margin-bottom: 6px !important;
}}
.cs-result-card .cs-stat-detail-content .cs-stat-legend-line {{
    margin: 1px 0 !important;
}}
.cs-result-card .cs-stat-detail-content .solution-grid {{
    margin-top: 8px !important;
}}
body.cs-theme-dark .cs-result-card .cs-glass-carousel.cs-glass-single .cs-glass-pages > .cs-glass-single-page {{
    background: #3a3d42 !important;
}}
body.cs-theme-dark .cs-result-card .cs-board-title,
body.cs-theme-dark .cs-result-card .cs-stat-toggle,
body.cs-theme-dark .cs-result-card .cs-glass-carousel.cs-glass-single .cs-set-bonus-box:not(.cs-stat-legend) > div:not(:first-child):not([style*="height: 1px"]) {{
    color: #f3f4f6 !important;
}}
body.cs-theme-dark .cs-result-card .cs-stat-toggle,
body.cs-theme-dark .cs-result-card .cs-stat-detail-content,
body.cs-theme-dark .cs-result-card .cs-glass-carousel.cs-glass-single .cs-set-bonus-box:not(.cs-stat-legend) > div:not(:first-child):not([style*="height: 1px"]) {{
    background: rgba(48, 50, 54, 0.88) !important;
}}
@media (prefers-color-scheme: dark) {{
    body.cs-theme-system .cs-result-card .cs-glass-carousel.cs-glass-single .cs-glass-pages > .cs-glass-single-page {{
        background: #3a3d42 !important;
    }}
    body.cs-theme-system .cs-result-card .cs-board-title,
    body.cs-theme-system .cs-result-card .cs-stat-toggle,
    body.cs-theme-system .cs-result-card .cs-glass-carousel.cs-glass-single .cs-set-bonus-box:not(.cs-stat-legend) > div:not(:first-child):not([style*="height: 1px"]) {{
        color: #f3f4f6 !important;
    }}
    body.cs-theme-system .cs-result-card .cs-stat-toggle,
    body.cs-theme-system .cs-result-card .cs-stat-detail-content,
    body.cs-theme-system .cs-result-card .cs-glass-carousel.cs-glass-single .cs-set-bonus-box:not(.cs-stat-legend) > div:not(:first-child):not([style*="height: 1px"]) {{
        background: rgba(48, 50, 54, 0.88) !important;
    }}
}}


/* cookie-sim: collapsed result summary + original two-column details */
.cs-result-card .cs-result-collapsible {{
    width: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 8px !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-result-summary-chips {{
    width: 100% !important;
    display: flex !important;
    flex-wrap: wrap !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 6px !important;
    margin: 0 !important;
    padding: 2px 2px 0 !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-result-summary-chip {{
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 5px !important;
    min-width: 0 !important;
    padding: 5px 9px !important;
    border-radius: 999px !important;
    background: #fff7f7 !important;
    color: #374151 !important;
    font-size: 11px !important;
    font-weight: 800 !important;
    line-height: 1.15 !important;
    box-sizing: border-box !important;
    white-space: nowrap !important;
}}
.cs-result-card .cs-result-summary-chip-color {{
    width: 12px !important;
    height: 12px !important;
    border-radius: 4px !important;
    border: 1px solid rgba(17, 24, 39, 0.08) !important;
    flex: 0 0 12px !important;
    display: inline-block !important;
}}
.cs-result-card .cs-result-toggle-wrap {{
    width: 100% !important;
    margin: 0 !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-result-toggle-button {{
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    gap: 8px !important;
    border: 0 !important;
    border-radius: 10px !important;
    background: #fff7f7 !important;
    color: #374151 !important;
    padding: 8px 11px !important;
    font-size: 12px !important;
    font-weight: 800 !important;
    line-height: 1.2 !important;
    cursor: pointer !important;
    box-shadow: none !important;
    outline: 0 !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-result-toggle-button:hover {{
    color: #ff4048 !important;
}}
.cs-result-card .cs-result-toggle-arrow {{
    font-size: 10px !important;
    line-height: 1 !important;
    flex: 0 0 auto !important;
}}
.cs-result-card .cs-result-toggle-content {{
    width: 100% !important;
    margin-top: 7px !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-result-detail-grid {{
    width: 100% !important;
    min-height: 200px !important;
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) !important;
    gap: 8px !important;
    align-items: stretch !important;
    justify-content: stretch !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-result-detail-info,
.cs-result-card .cs-result-detail-board {{
    min-width: 0 !important;
    min-height: 200px !important;
    background: #fff7f7 !important;
    border-radius: 10px !important;
    border: 0 !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-result-detail-info {{
    padding: 10px !important;
    display: block !important;
    text-align: left !important;
}}
.cs-result-card .cs-result-detail-board {{
    padding: 12px 10px 10px !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 6px !important;
}}
.cs-result-card .cs-result-detail-board-title {{
    width: 100% !important;
    align-self: stretch !important;
    color: #374151 !important;
    font-size: 12px !important;
    font-weight: 800 !important;
    line-height: 1.2 !important;
    text-align: left !important;
    margin: 0 !important;
    padding: 0 0 2px 0 !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-result-detail-info > .cs-set-bonus-box,
.cs-result-card .cs-result-detail-info > .cs-stat-legend {{
    width: 100% !important;
    height: auto !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    background: transparent !important;
    border: 0 !important;
    box-sizing: border-box !important;
    text-align: left !important;
}}
.cs-result-card .cs-result-detail-info .cs-set-bonus-box > div:first-child,
.cs-result-card .cs-result-detail-info .cs-stat-legend > div:first-child {{
    display: block !important;
    color: #374151 !important;
    font-size: 12px !important;
    font-weight: 800 !important;
    line-height: 1.2 !important;
    margin: 0 0 7px 0 !important;
}}
.cs-result-card .cs-result-detail-info .cs-stat-legend-line {{
    display: flex !important;
    align-items: center !important;
    gap: 6px !important;
    margin: 1px 0 !important;
    font-size: 12px !important;
    line-height: 1.2 !important;
}}
.cs-result-card .cs-result-detail-grid .solution-grid {{
    grid-template-columns: repeat(7, minmax(0, 1fr)) !important;
    grid-template-rows: repeat(7, minmax(0, 1fr)) !important;
    width: 160px !important;
    min-width: 160px !important;
    max-width: 160px !important;
    height: 160px !important;
    min-height: 160px !important;
    max-height: 160px !important;
    aspect-ratio: 1 / 1 !important;
    align-self: center !important;
    justify-self: center !important;
    margin: auto !important;
    transform: none !important;
    box-sizing: content-box !important;
    flex: 0 0 auto !important;
}}
.cs-result-card .cs-result-detail-grid .solution-cell {{
    width: auto !important;
    min-width: 0 !important;
    max-width: none !important;
    height: auto !important;
    min-height: 0 !important;
    max-height: none !important;
    border-radius: 0 !important;
    margin: 0 !important;
    box-sizing: border-box !important;
}}
body.cs-theme-dark .cs-result-card .cs-result-summary-chip,
body.cs-theme-dark .cs-result-card .cs-result-toggle-button,
body.cs-theme-dark .cs-result-card .cs-result-detail-info,
body.cs-theme-dark .cs-result-card .cs-result-detail-board {{
    background: #3a3d42 !important;
    color: #f3f4f6 !important;
}}
body.cs-theme-dark .cs-result-card .cs-result-detail-board-title,
body.cs-theme-dark .cs-result-card .cs-result-detail-info .cs-set-bonus-box > div:first-child,
body.cs-theme-dark .cs-result-card .cs-result-detail-info .cs-stat-legend > div:first-child {{
    color: #f3f4f6 !important;
}}
@media (prefers-color-scheme: dark) {{
    body.cs-theme-system .cs-result-card .cs-result-summary-chip,
    body.cs-theme-system .cs-result-card .cs-result-toggle-button,
    body.cs-theme-system .cs-result-card .cs-result-detail-info,
    body.cs-theme-system .cs-result-card .cs-result-detail-board {{
        background: #3a3d42 !important;
        color: #f3f4f6 !important;
    }}
    body.cs-theme-system .cs-result-card .cs-result-detail-board-title,
    body.cs-theme-system .cs-result-card .cs-result-detail-info .cs-set-bonus-box > div:first-child,
    body.cs-theme-system .cs-result-card .cs-result-detail-info .cs-stat-legend > div:first-child {{
        color: #f3f4f6 !important;
    }}
}}

/* cookie-sim: keep expanded detail text readable in dark mode */
body.cs-theme-dark .cs-result-card .cs-result-detail-info .cs-set-bonus-box,
body.cs-theme-dark .cs-result-card .cs-result-detail-info .cs-set-bonus-box div,
body.cs-theme-dark .cs-result-card .cs-result-detail-info .cs-set-bonus-box span,
body.cs-theme-dark .cs-result-card .cs-result-detail-info .cs-stat-legend,
body.cs-theme-dark .cs-result-card .cs-result-detail-info .cs-stat-legend div,
body.cs-theme-dark .cs-result-card .cs-result-detail-info .cs-stat-legend span {{
    color: #f3f4f6 !important;
}}
@media (prefers-color-scheme: dark) {{
    body.cs-theme-system .cs-result-card .cs-result-detail-info .cs-set-bonus-box,
    body.cs-theme-system .cs-result-card .cs-result-detail-info .cs-set-bonus-box div,
    body.cs-theme-system .cs-result-card .cs-result-detail-info .cs-set-bonus-box span,
    body.cs-theme-system .cs-result-card .cs-result-detail-info .cs-stat-legend,
    body.cs-theme-system .cs-result-card .cs-result-detail-info .cs-stat-legend div,
    body.cs-theme-system .cs-result-card .cs-result-detail-info .cs-stat-legend span {{
        color: #f3f4f6 !important;
    }}
}}



/* cookie-sim: final result layout — board first, details only when chips are clicked */
.cs-result-card .cs-board-result-wrapper,
.cs-result-card .cs-board-result-wrapper:hover {{
    transform: none !important;
    transition: none !important;
    gap: 8px !important;
    width: 100% !important;
    margin: 0 !important;
}}
.cs-result-card .cs-board-result-wrapper .solution-header {{
    display: none !important;
}}
.cs-result-card .cs-result-main {{
    width: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 8px !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-result-chip-row {{
    width: 100% !important;
    display: flex !important;
    flex-wrap: wrap !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 6px !important;
    margin: 0 !important;
    padding: 0 !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-result-control-chip,
.cs-result-card .cs-result-static-chip {{
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 5px !important;
    min-width: 0 !important;
    padding: 5px 9px !important;
    border: 0 !important;
    border-radius: 999px !important;
    background: #fff7f7 !important;
    color: #374151 !important;
    font-size: 11px !important;
    font-weight: 800 !important;
    line-height: 1.15 !important;
    white-space: nowrap !important;
    box-shadow: none !important;
    outline: 0 !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-result-control-chip {{
    cursor: pointer !important;
}}
.cs-result-card .cs-result-control-chip:hover,
.cs-result-card .cs-result-control-chip.active {{
    color: #ff4048 !important;
}}
.cs-result-card .cs-result-control-arrow {{
    font-size: 10px !important;
    line-height: 1 !important;
}}
.cs-result-card .cs-result-board-row {{
    position: relative !important;
    width: 100% !important;
    min-height: 190px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-result-board-row .cs-board-panel {{
    width: 100% !important;
    min-height: 190px !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 7px !important;
    padding: 10px !important;
    border-radius: 10px !important;
    background: #fff7f7 !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-board-title {{
    align-self: flex-start !important;
    margin: 0 0 0 4px !important;
    color: #374151 !important;
    font-size: 12px !important;
    font-weight: 800 !important;
    line-height: 1.2 !important;
}}
.cs-result-card .cs-result-board-row .solution-grid,
.cs-result-card .cs-result-detail-board .solution-grid {{
    grid-template-columns: repeat(7, minmax(0, 1fr)) !important;
    grid-template-rows: repeat(7, minmax(0, 1fr)) !important;
    width: 168px !important;
    min-width: 168px !important;
    max-width: 168px !important;
    height: 168px !important;
    min-height: 168px !important;
    max-height: 168px !important;
    aspect-ratio: 1 / 1 !important;
    align-self: center !important;
    justify-self: center !important;
    margin: 0 auto !important;
    transform: none !important;
    box-sizing: content-box !important;
    flex: 0 0 auto !important;
    border: 0 !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    outline: none !important;
}}
.cs-result-card .cs-result-board-row .solution-cell,
.cs-result-card .cs-result-detail-board .solution-cell {{
    width: 24px !important;
    min-width: 24px !important;
    max-width: 24px !important;
    height: 24px !important;
    min-height: 24px !important;
    max-height: 24px !important;
    border-radius: 0 !important;
    margin: 0 !important;
    box-sizing: border-box !important;
    font-size: 0.75em !important;
    font-weight: 800 !important;
    line-height: 1 !important;
}}
.cs-result-card .cs-result-arrow,
.cs-result-card .cs-result-arrow:hover,
.cs-result-card .cs-result-arrow:focus,
.cs-result-card .cs-result-arrow:active {{
    position: absolute !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    width: 24px !important;
    height: 36px !important;
    border: 0 !important;
    background: transparent !important;
    color: #111827 !important;
    font-size: 22px !important;
    font-weight: 900 !important;
    line-height: 1 !important;
    padding: 0 !important;
    cursor: pointer !important;
    z-index: 10 !important;
    box-shadow: none !important;
    outline: 0 !important;
}}
.cs-result-card .cs-result-arrow-prev {{ left: -10px !important; }}
.cs-result-card .cs-result-arrow-next {{ right: -10px !important; }}
.cs-result-card .cs-result-detail-area {{
    width: 100% !important;
    margin: 0 !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-result-detail-grid {{
    width: 100% !important;
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) !important;
    gap: 8px !important;
    align-items: stretch !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-result-detail-grid:not(:has(.cs-result-detail-board)) {{
    grid-template-columns: minmax(0, 1fr) !important;
}}
.cs-result-card .cs-result-detail-info,
.cs-result-card .cs-result-detail-board {{
    min-width: 0 !important;
    background: #fff7f7 !important;
    border-radius: 10px !important;
    border: 0 !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-result-detail-info {{
    padding: 10px !important;
    text-align: left !important;
}}
.cs-result-card .cs-result-detail-board {{
    padding: 12px 10px 10px !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 6px !important;
}}
.cs-result-card .cs-result-detail-board-title {{
    width: 100% !important;
    color: #374151 !important;
    font-size: 12px !important;
    font-weight: 800 !important;
    line-height: 1.2 !important;
    text-align: left !important;
    margin: 0 !important;
    padding: 0 0 2px 0 !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-result-detail-info > .cs-set-bonus-box,
.cs-result-card .cs-result-detail-info > .cs-stat-legend {{
    width: 100% !important;
    height: auto !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    background: transparent !important;
    border: 0 !important;
    box-sizing: border-box !important;
    text-align: left !important;
}}
.cs-result-card .cs-stat-legend-line {{
    display: flex !important;
    align-items: center !important;
    gap: 6px !important;
    margin: 1px 0 !important;
    font-size: 12px !important;
    font-weight: 400 !important;
    line-height: 1.45 !important;
    color: #111827 !important;
}}
.cs-result-card .cs-stat-legend-chip {{
    width: 12px !important;
    height: 12px !important;
    border-radius: 3px !important;
    flex: 0 0 12px !important;
}}
body.cs-theme-dark .cs-result-card .cs-result-control-chip,
body.cs-theme-dark .cs-result-card .cs-result-static-chip,
body.cs-theme-dark .cs-result-card .cs-result-board-row .cs-board-panel,
body.cs-theme-dark .cs-result-card .cs-result-detail-info,
body.cs-theme-dark .cs-result-card .cs-result-detail-board {{
    background: #3a3d42 !important;
    color: #f3f4f6 !important;
}}
body.cs-theme-dark .cs-result-card .cs-board-title,
body.cs-theme-dark .cs-result-card .cs-result-detail-board-title,
body.cs-theme-dark .cs-result-card .cs-result-arrow {{
    color: #f3f4f6 !important;
}}
@media (prefers-color-scheme: dark) {{
    body.cs-theme-system .cs-result-card .cs-result-control-chip,
    body.cs-theme-system .cs-result-card .cs-result-static-chip,
    body.cs-theme-system .cs-result-card .cs-result-board-row .cs-board-panel,
    body.cs-theme-system .cs-result-card .cs-result-detail-info,
    body.cs-theme-system .cs-result-card .cs-result-detail-board {{
        background: #3a3d42 !important;
        color: #f3f4f6 !important;
    }}
    body.cs-theme-system .cs-result-card .cs-board-title,
    body.cs-theme-system .cs-result-card .cs-result-detail-board-title,
    body.cs-theme-system .cs-result-card .cs-result-arrow {{
        color: #f3f4f6 !important;
    }}
}}
@media (max-width: 430px) {{
    .cs-result-card .cs-result-detail-grid {{
        grid-template-columns: minmax(0, 1fr) !important;
    }}
    .cs-result-card .cs-result-arrow-prev {{ left: -8px !important; }}
    .cs-result-card .cs-result-arrow-next {{ right: -8px !important; }}
}}

/* cookie-sim: final compact result layout - one visible board, details in toggles */
.cs-result-card .cs-result-main {{
    width: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    /* 배치 표 <-> 토글 간격. 토글 <-> 상세 박스 간격(.cs-result-detail-content margin-top: 6px)과 동일하게 6px. */
    gap: 6px !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-result-board-row {{
    position: relative !important;
    width: 100% !important;
    min-height: 206px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-result-board-row .cs-board-panel {{
    width: 100% !important;
    min-height: 206px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 10px !important;
    border-radius: 10px !important;
    background: #fff7f7 !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-result-board-row .solution-grid {{
    width: 168px !important;
    min-width: 168px !important;
    max-width: 168px !important;
    height: 168px !important;
    min-height: 168px !important;
    max-height: 168px !important;
    margin: 0 auto !important;
    border: 0 !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    outline: none !important;
    overflow: hidden !important;
    transform: none !important;
    box-sizing: content-box !important;
    flex: 0 0 auto !important;
}}
.cs-result-card .cs-result-board-row .solution-cell {{
    width: 24px !important;
    min-width: 24px !important;
    max-width: 24px !important;
    height: 24px !important;
    min-height: 24px !important;
    max-height: 24px !important;
    border-radius: 0 !important;
    margin: 0 !important;
    box-sizing: border-box !important;
    font-size: 0.75em !important;
    font-weight: 800 !important;
    line-height: 1 !important;
}}
.cs-result-card .cs-result-arrow,
.cs-result-card .cs-result-arrow:hover,
.cs-result-card .cs-result-arrow:focus,
.cs-result-card .cs-result-arrow:active {{
    position: absolute !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    width: 24px !important;
    height: 40px !important;
    border: 0 !important;
    background: transparent !important;
    color: #111827 !important;
    font-size: 24px !important;
    font-weight: 900 !important;
    line-height: 1 !important;
    padding: 0 !important;
    cursor: pointer !important;
    z-index: 10 !important;
    box-shadow: none !important;
    outline: 0 !important;
}}
.cs-result-card .cs-result-arrow-prev {{ left: -10px !important; }}
.cs-result-card .cs-result-arrow-next {{ right: -10px !important; }}
.cs-result-card .cs-result-detail-area {{
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-result-toggle-wide {{
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    gap: 8px !important;
    padding: 8px 10px !important;
    border-radius: 10px !important;
    background: #fff7f7 !important;
    color: #374151 !important;
    font-size: 12px !important;
    font-weight: 800 !important;
    line-height: 1.2 !important;
    text-align: left !important;
    white-space: normal !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-result-toggle-wide:hover,
.cs-result-card .cs-result-toggle-wide.active {{
    color: #ff4048 !important;
}}
.cs-result-card .cs-result-detail-content {{
    width: 100% !important;
    margin-top: 6px !important;
    padding: 10px !important;
    border-radius: 10px !important;
    background: #fff7f7 !important;
    color: #374151 !important;
    box-sizing: border-box !important;
    text-align: left !important;
}}
.cs-result-card .cs-result-detail-content > .cs-set-bonus-box,
.cs-result-card .cs-result-detail-content > .cs-stat-legend {{
    width: 100% !important;
    height: auto !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    background: transparent !important;
    border: 0 !important;
    box-sizing: border-box !important;
    text-align: left !important;
}}
.cs-result-card .cs-result-detail-content .cs-stat-legend-line {{
    display: flex !important;
    align-items: center !important;
    gap: 6px !important;
    margin: 1px 0 !important;
    font-size: 12px !important;
    font-weight: 400 !important;
    line-height: 1.45 !important;
    color: #111827 !important;
}}
.cs-result-card .cs-result-detail-content .cs-stat-legend-chip {{
    width: 12px !important;
    height: 12px !important;
    border-radius: 3px !important;
    flex: 0 0 12px !important;
}}
body.cs-theme-dark .cs-result-card .cs-result-board-row .cs-board-panel,
body.cs-theme-dark .cs-result-card .cs-result-toggle-wide,
body.cs-theme-dark .cs-result-card .cs-result-detail-content {{
    background: #3a3d42 !important;
    color: #f3f4f6 !important;
}}
body.cs-theme-dark .cs-result-card .cs-result-arrow,
body.cs-theme-dark .cs-result-card .cs-result-detail-content,
body.cs-theme-dark .cs-result-card .cs-result-detail-content * {{
    color: #f3f4f6 !important;
}}
@media (prefers-color-scheme: dark) {{
    body.cs-theme-system .cs-result-card .cs-result-board-row .cs-board-panel,
    body.cs-theme-system .cs-result-card .cs-result-toggle-wide,
    body.cs-theme-system .cs-result-card .cs-result-detail-content {{
        background: #3a3d42 !important;
        color: #f3f4f6 !important;
    }}
    body.cs-theme-system .cs-result-card .cs-result-arrow,
    body.cs-theme-system .cs-result-card .cs-result-detail-content,
    body.cs-theme-system .cs-result-card .cs-result-detail-content * {{
        color: #f3f4f6 !important;
    }}
}}



/* cookie-sim: result board view switcher fix */
.cs-result-card .cs-result-board-row .cs-board-panel {{
    position: relative !important;
    overflow: visible !important;
}}
.cs-result-card .cs-result-visible-board {{
    display: grid !important;
}}
.cs-result-card .cs-result-visible-board[style*="display: none"] {{
    display: none !important;
}}
.cs-result-card .cs-result-arrow,
.cs-result-card .cs-result-arrow:hover,
.cs-result-card .cs-result-arrow:focus,
.cs-result-card .cs-result-arrow:active {{
    pointer-events: auto !important;
    user-select: none !important;
    -webkit-user-select: none !important;
    touch-action: manipulation !important;
}}
.cs-result-card .cs-current-detail-mount {{
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    box-sizing: border-box !important;
}}


/* cookie-sim: requested final result layout refinements */
.cs-top-grid {{
    grid-template-columns: minmax(0, 6fr) minmax(0, 4fr) !important;
}}

.cs-result-card .cs-result-detail-content,
.cs-result-card .cs-result-detail-content > .cs-set-bonus-box,
.cs-result-card .cs-result-detail-content > .cs-stat-legend,
.cs-result-card .cs-result-detail-content > .cs-set-bonus-box > div,
.cs-result-card .cs-result-detail-content > .cs-stat-legend > div,
.cs-result-card .cs-result-detail-content [data-cs-resistance="1"] {{
    text-align: left !important;
}}
.cs-result-card .cs-result-detail-content > .cs-set-bonus-box,
.cs-result-card .cs-result-detail-content > .cs-stat-legend {{
    align-items: stretch !important;
    justify-content: flex-start !important;
}}
.cs-result-card .cs-result-detail-content .cs-stat-legend-line {{
    justify-content: flex-start !important;
    width: 100% !important;
}}

.cs-result-card .cs-result-arrow,
.cs-result-card .cs-result-arrow:hover,
.cs-result-card .cs-result-arrow:focus,
.cs-result-card .cs-result-arrow:active {{
    color: transparent !important;
    font-size: 0 !important;
    line-height: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}}
.cs-result-card .cs-result-arrow::before {{
    content: '' !important;
    display: block !important;
    width: 8px !important;
    height: 8px !important;
    border-right: 2.5px solid #6b7280 !important;
    border-bottom: 2.5px solid #6b7280 !important;
    box-sizing: border-box !important;
}}
.cs-result-card .cs-result-arrow-prev::before {{
    transform: rotate(135deg) !important;
}}
.cs-result-card .cs-result-arrow-next::before {{
    transform: rotate(-45deg) !important;
}}
.cs-result-card .cs-result-arrow-prev {{ left: 14px !important; }}
.cs-result-card .cs-result-arrow-next {{ right: 14px !important; }}

body.cs-theme-dark .cs-result-card .cs-result-arrow::before {{
    border-color: #aeb4bd !important;
}}
@media (prefers-color-scheme: dark) {{
    body.cs-theme-system .cs-result-card .cs-result-arrow::before {{
        border-color: #aeb4bd !important;
    }}
}}

/* When the top layout collapses but there is still width, put detail left and board right. */
@media (max-width: 780px) and (min-width: 521px) {{
    .cs-top-grid {{
        grid-template-columns: 1fr !important;
    }}
    .cs-result-card .cs-result-main.cs-detail-open {{
        display: grid !important;
        grid-template-columns: minmax(0, 0.82fr) minmax(0, 1fr) !important;
        grid-template-areas: 'detail board' !important;
        column-gap: 8px !important;
        row-gap: 0 !important;
        align-items: stretch !important;
    }}
    .cs-result-card .cs-result-main.cs-detail-open .cs-result-board-row {{
        grid-area: board !important;
        min-height: 206px !important;
        height: 100% !important;
    }}
    .cs-result-card .cs-result-main.cs-detail-open .cs-current-detail-mount {{
        grid-area: detail !important;
        height: 100% !important;
        display: flex !important;
        flex-direction: column !important;
    }}
    .cs-result-card .cs-result-main.cs-detail-open .cs-result-detail-area {{
        height: 100% !important;
        display: flex !important;
        flex-direction: column !important;
    }}
    .cs-result-card .cs-result-main.cs-detail-open .cs-result-toggle-wide {{
        flex: 0 0 auto !important;
    }}
    .cs-result-card .cs-result-main.cs-detail-open .cs-result-detail-content {{
        flex: 1 1 auto !important;
        margin-top: 6px !important;
        display: flex !important;
        align-items: flex-start !important;
        justify-content: flex-start !important;
    }}
    .cs-result-card .cs-result-main.cs-detail-open .cs-result-detail-content > .cs-set-bonus-box,
    .cs-result-card .cs-result-main.cs-detail-open .cs-result-detail-content > .cs-stat-legend {{
        width: 100% !important;
    }}
}}

@media (max-width: 520px) {{
    .cs-top-grid {{
        grid-template-columns: 1fr !important;
    }}
    .cs-result-card .cs-result-main.cs-detail-open {{
        display: flex !important;
        flex-direction: column !important;
    }}
    .cs-result-card .cs-result-arrow-prev {{ left: 10px !important; }}
    .cs-result-card .cs-result-arrow-next {{ right: 10px !important; }}
}}


/* cookie-sim: layout balance fix - keep top cards visually aligned */
.cs-top-grid {{
    grid-template-columns: minmax(0, 6fr) minmax(0, 4fr) !important;
    align-items: stretch !important;
}}
.cs-top-grid > .cs-card,
.cs-top-grid > .cs-result-card {{
    min-width: 0 !important;
    height: 100% !important;
}}
.cs-result-card {{
    display: flex !important;
    flex-direction: column !important;
}}
.cs-result-card .solutions-container {{
    flex: 1 1 auto !important;
    width: 100% !important;
    min-height: 0 !important;
    display: flex !important;
}}
.cs-result-card .cs-empty-result {{
    flex: 1 1 auto !important;
    width: 100% !important;
    min-height: 232px !important;
    height: 100% !important;
}}
@media (max-width: 780px) {{
    .cs-top-grid {{
        grid-template-columns: 1fr !important;
    }}
    .cs-result-card .cs-empty-result {{
        min-height: 210px !important;
    }}
}}


/* cookie-sim: gray width alignment fix */
.cs-top-grid {{
    grid-template-columns: minmax(0, 6fr) minmax(0, 4fr) !important;
}}
.cs-action-row {{
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
}}
.cs-upload-row {{
    grid-template-columns: minmax(0, 6fr) minmax(0, 4fr) !important;
}}
.cs-result-card .solutions-container {{
    padding: 0 !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
}}
.cs-result-card .cs-empty-result {{
    width: 100% !important;
    max-width: none !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
    box-sizing: border-box !important;
}}
@media (max-width: 780px) {{
    .cs-top-grid {{
        grid-template-columns: 1fr !important;
    }}
}}


/* cookie-sim: right edge alignment + scrollbar gap fix */
.cs-shard-wrap {{
    width: 100% !important;
    max-width: none !important;
    padding-right: 0 !important;
    margin-right: 0 !important;
    box-sizing: border-box !important;
}}
.cs-section-pill,
.cs-top-grid,
.pieces-section.cs-card {{
    width: 100% !important;
    max-width: none !important;
    margin-right: 0 !important;
    box-sizing: border-box !important;
}}
.cs-top-grid > .cs-card,
.cs-top-grid > .cs-result-card {{
    max-width: none !important;
    margin-right: 0 !important;
    box-sizing: border-box !important;
}}


.cs-result-card .cs-result-detail-content > .cs-set-bonus-box > div:not(:first-child):not([style*="height: 1px"]),
.cs-result-card .cs-result-detail-content > .cs-stat-legend > div:not(:first-child),
.cs-result-card .cs-result-detail-content > .cs-set-bonus-box span,
.cs-result-card .cs-result-detail-content > .cs-stat-legend span {{
    font-size: 12px !important;
    font-weight: 400 !important;
    line-height: 1.45 !important;
    color: #111827 !important;
}}

.cs-result-card .cs-result-detail-content > .cs-set-bonus-box > div,
.cs-result-card .cs-result-detail-content > .cs-stat-legend > div {{
    margin-top: 1px !important;
    margin-bottom: 1px !important;
}}
.cs-result-card .cs-result-detail-content > .cs-set-bonus-box > div[style*="height: 1px"] {{
    margin-top: 6px !important;
    margin-bottom: 4px !important;
}}

body.cs-theme-dark .cs-desc,
body.cs-theme-dark .cs-upload-help,
body.cs-theme-dark .cs-result-card .cs-stat-legend-line,
body.cs-theme-dark .cs-result-card .cs-result-detail-content .cs-stat-legend-line,
body.cs-theme-dark .cs-result-card .cs-result-detail-content > .cs-set-bonus-box > div:not(:first-child):not([style*="height: 1px"]),
body.cs-theme-dark .cs-result-card .cs-result-detail-content > .cs-stat-legend > div:not(:first-child),
body.cs-theme-dark .cs-result-card .cs-result-detail-content > .cs-set-bonus-box span,
body.cs-theme-dark .cs-result-card .cs-result-detail-content > .cs-stat-legend span {{
    color: #f3f4f6 !important;
}}
body.cs-theme-dark .cs-result-card .cs-result-detail-content > .cs-set-bonus-box > div[style*="height: 1px"] {{
    background: rgba(243, 244, 246, 0.12) !important;
}}

body.cs-theme-dark .pieces-section .piece-item,
body.cs-theme-dark .pieces-section [data-cs-unique-card="true"],
body.cs-theme-dark .pieces-section .cs-picker-card {{
    border-color: transparent !important;
    box-shadow: none !important;
}}
body.cs-theme-dark .pieces-section .piece-item *,
body.cs-theme-dark .pieces-section .cs-modal-stat-chip {{
    color: #f3f4f6;
}}

/* cookie-sim: dark mode modal/stat editor and recognized cards border cleanup */
body.cs-theme-dark .pieces-section .piece-item,
body.cs-theme-dark #piece-palette .piece-item,
body.cs-theme-dark #recognized-pieces-section .piece-item,
body.cs-theme-dark .cs-picker-card {{
    border: 0 !important;
    border-color: transparent !important;
    outline: 0 !important;
    box-shadow: none !important;
}}
body.cs-theme-dark .cs-modal-select-menu,
body.cs-theme-dark .cs-modal-select-dropdown,
body.cs-theme-dark .cs-modal-select-button {{
    border: 0 !important;
    outline: 0 !important;
    box-shadow: none !important;
}}
body.cs-theme-dark .cs-modal-select-menu *,
body.cs-theme-dark .cs-modal-select-button {{
    color: #f3f4f6 !important;
}}

/* cookie-sim: dark mode recognized card border + stat editor dropdown box cleanup */
body.cs-theme-dark #recognized-pieces-section div[style*="132px"][style*="border"],
body.cs-theme-dark #piece-palette div[style*="132px"][style*="border"],
body.cs-theme-dark #recognized-pieces-section div[style*="204px"][style*="border"],
body.cs-theme-dark #piece-palette div[style*="204px"][style*="border"],
body.cs-theme-dark #recognized-pieces-section div[style*="156px"][style*="border"],
body.cs-theme-dark #piece-palette div[style*="156px"][style*="border"],
body.cs-theme-dark .cs-picker-card {{
    border: 0 !important;
    border-color: transparent !important;
    outline: 0 !important;
    box-shadow: none !important;
}}
body.cs-theme-dark div[style*="max-height: 190px"][style*="overflow-y: auto"] {{
    background: transparent !important;
    border: 0 !important;
    border-color: transparent !important;
    outline: 0 !important;
    box-shadow: none !important;
}}
body.cs-theme-dark div[style*="max-height: 190px"][style*="overflow-y: auto"] button {{
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
}}
body.cs-theme-dark div[style*="max-height: 190px"][style*="overflow-y: auto"] button:hover {{
    background: #303236 !important;
}}

/* cookie-sim: dark mode stat editor dropdown blend + brighter recognized card tones */
body.cs-theme-dark .cs-modal-select-button {{
    background: #303236 !important;
    color: #f3f4f6 !important;
}}
body.cs-theme-dark .cs-modal-select-menu,
body.cs-theme-dark .cs-modal-select-dropdown {{
    background: #303236 !important;
    border: 0 !important;
    box-shadow: none !important;
}}
body.cs-theme-dark .cs-modal-select-menu button {{
    background: #303236 !important;
    color: #f3f4f6 !important;
}}
/* 호버 시 배경은 그대로, 글씨만 빨간색 */
body.cs-theme-dark .cs-modal-select-menu button:hover {{
    background: #303236 !important;
    color: #ff4048 !important;
}}

.cs-stat-edit-menu {{
    scrollbar-width: thin;
    scrollbar-color: #8f96a3 transparent;
}}
.cs-stat-edit-menu::-webkit-scrollbar {{
    width: 4px;
}}
.cs-stat-edit-menu::-webkit-scrollbar-track {{
    background: transparent;
}}
.cs-stat-edit-menu::-webkit-scrollbar-thumb {{
    background: #8f96a3;
    border-radius: 999px;
    border: 1px solid transparent;
}}
body.cs-theme-dark .cs-stat-edit-menu::-webkit-scrollbar-thumb {{
    background: #8f96a3;
}}
body.cs-theme-dark .cs-stat-edit-menu::-webkit-scrollbar-track {{
    background: transparent;
}}

/* cookie-sim: result toggle spacing
   배치 표(핑크 패널)와 '인식된 스탯 배치 보기' 토글 사이 간격은
   .cs-result-main의 flex gap(8px)과 이 margin-top의 합이다.
   16px이 너무 넓어 margin-top을 0으로 -> 총 8px. */
.cs-result-card .cs-result-toggle-wide {{
    margin-top: 0 !important;
}}
.cs-result-card .cs-result-board-row {{
    margin-bottom: 0 !important;
}}

/* cookie-sim: 인식된 조각 빈 상태 박스의 좌우 여백 통일.
   공통 .palette 규칙의 padding-right: 5px 때문에 오른쪽만 더 넓어지던 문제를 제거한다. */
#recognized-piece-palette {{
    width: 100% !important;
    max-width: none !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
    box-sizing: border-box !important;
}}
#recognized-piece-palette > .cs-empty-result {{
    width: 100% !important;
    max-width: none !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
    box-sizing: border-box !important;
}}

/* cookie-sim: 배치 결과 빈 상태 회색 박스의 아래 여백을 좌우(10px)와 동일하게.
   .cs-empty-result는 height:100%로 컨테이너에 고정돼 있어 margin으로는 못 당기므로,
   빈 상태일 때만 카드 자체의 padding-bottom을 6px -> 10px로 올린다.
   실제 배치 결과가 표시되면 :has()가 매칭되지 않아 기존 6px이 유지된다. */
.cs-result-card:has(.cs-empty-result) {{
    padding-bottom: 10px !important;
}}

/* cookie-sim: '조각 자동 배치' 설명 문구와 세트효과 박스 사이 간격 축소 (12px -> 6px).
   제목과 설명 사이 간격(8px)은 유지. */
.cs-card > .cs-desc {{
    margin-bottom: 6px !important;
}}
.cs-card > .cs-target {{
    margin-top: 0 !important;
}}

/* cookie-sim: dark-mode dropdowns use the same two-tone design as the stat editor.
   Closed field = #3a3d42, opened list/items = modal background #303236. */
body.cs-theme-dark .cs-modal-select-dropdown {{
    background: transparent !important;
}}
body.cs-theme-dark .cs-modal-select-button {{
    background: #3a3d42 !important;
    color: #f3f4f6 !important;
    border: 0 !important;
    outline: 0 !important;
    box-shadow: none !important;
}}
body.cs-theme-dark .cs-modal-select-button::after {{
    border-right-color: #cbd5e1 !important;
    border-bottom-color: #cbd5e1 !important;
}}
body.cs-theme-dark .cs-modal-select-menu,
body.cs-theme-dark .cs-stat-edit-menu {{
    background: #303236 !important;
    color: #f3f4f6 !important;
    border: 0 !important;
    outline: 0 !important;
    box-shadow: none !important;
}}
body.cs-theme-dark .cs-modal-select-menu .cs-modal-select-item,
body.cs-theme-dark .cs-stat-edit-menu .cs-modal-select-item,
body.cs-theme-dark .cs-stat-edit-menu > button {{
    background: #303236 !important;
    color: #f3f4f6 !important;
    border: 0 !important;
    box-shadow: none !important;
}}
body.cs-theme-dark .cs-modal-select-menu .cs-modal-select-item.active,
body.cs-theme-dark .cs-stat-edit-menu .cs-modal-select-item.active {{
    background: #303236 !important;
    color: #ffffff !important;
}}
body.cs-theme-dark .cs-modal-select-menu .cs-modal-select-item:hover,
body.cs-theme-dark .cs-modal-select-menu .cs-modal-select-item:focus,
body.cs-theme-dark .cs-stat-edit-menu .cs-modal-select-item:hover,
body.cs-theme-dark .cs-stat-edit-menu .cs-modal-select-item:focus,
body.cs-theme-dark .cs-stat-edit-menu > button:hover,
body.cs-theme-dark .cs-stat-edit-menu > button:focus {{
    background: #303236 !important;
    color: #ff4048 !important;
}}

/* Final scrollbar override: apply to light, dark and system themes.
   This is intentionally last so older 8px/17px rules cannot override it. */
html,
body,
body * {{
    scrollbar-width: thin !important;
    scrollbar-color: #9ca3af transparent !important;
}}
html::-webkit-scrollbar,
body::-webkit-scrollbar,
body *::-webkit-scrollbar {{
    width: 4px !important;
    height: 4px !important;
}}
html::-webkit-scrollbar-track,
body::-webkit-scrollbar-track,
body *::-webkit-scrollbar-track,
html::-webkit-scrollbar-corner,
body::-webkit-scrollbar-corner,
body *::-webkit-scrollbar-corner {{
    background: transparent !important;
}}
html::-webkit-scrollbar-thumb,
body::-webkit-scrollbar-thumb,
body *::-webkit-scrollbar-thumb {{
    background: #9ca3af !important;
    border: 0 !important;
    border-radius: 999px !important;
}}
html::-webkit-scrollbar-thumb:hover,
body::-webkit-scrollbar-thumb:hover,
body *::-webkit-scrollbar-thumb:hover {{
    background: #b6bcc6 !important;
}}


/* cookie-sim: final embedded theme-specific scrollbar thumb colors */
/* Light: sampled from the requested reference image (#999ca4). */
html:not(#cs-scroll-color-a):not(#cs-scroll-color-b),
body:not(#cs-scroll-color-a):not(#cs-scroll-color-b),
body *:not(#cs-scroll-color-a):not(#cs-scroll-color-b) {{
    scrollbar-color: #999ca4 transparent !important;
}}
html:not(#cs-scroll-color-a):not(#cs-scroll-color-b)::-webkit-scrollbar-thumb,
body:not(#cs-scroll-color-a):not(#cs-scroll-color-b)::-webkit-scrollbar-thumb,
body *:not(#cs-scroll-color-a):not(#cs-scroll-color-b)::-webkit-scrollbar-thumb,
html:not(#cs-scroll-color-a):not(#cs-scroll-color-b)::-webkit-scrollbar-thumb:hover,
body:not(#cs-scroll-color-a):not(#cs-scroll-color-b)::-webkit-scrollbar-thumb:hover,
body *:not(#cs-scroll-color-a):not(#cs-scroll-color-b)::-webkit-scrollbar-thumb:hover {{
    background: #999ca4 !important;
}}

/* Explicit dark theme: sampled from the requested dark reference image (#9ca3af). */
body.cs-theme-dark:not(#cs-scroll-color-a):not(#cs-scroll-color-b),
body.cs-theme-dark:not(#cs-scroll-color-a):not(#cs-scroll-color-b) *:not(#cs-scroll-color-c):not(#cs-scroll-color-d) {{
    scrollbar-color: #9ca3af transparent !important;
}}
body.cs-theme-dark:not(#cs-scroll-color-a):not(#cs-scroll-color-b)::-webkit-scrollbar-thumb,
body.cs-theme-dark:not(#cs-scroll-color-a):not(#cs-scroll-color-b) *:not(#cs-scroll-color-c):not(#cs-scroll-color-d)::-webkit-scrollbar-thumb,
body.cs-theme-dark:not(#cs-scroll-color-a):not(#cs-scroll-color-b)::-webkit-scrollbar-thumb:hover,
body.cs-theme-dark:not(#cs-scroll-color-a):not(#cs-scroll-color-b) *:not(#cs-scroll-color-c):not(#cs-scroll-color-d)::-webkit-scrollbar-thumb:hover {{
    background: #9ca3af !important;
}}

/* System theme while the device is dark. */
@media (prefers-color-scheme: dark) {{
    body.cs-theme-system:not(#cs-scroll-color-a):not(#cs-scroll-color-b),
    body.cs-theme-system:not(#cs-scroll-color-a):not(#cs-scroll-color-b) *:not(#cs-scroll-color-c):not(#cs-scroll-color-d) {{
        scrollbar-color: #9ca3af transparent !important;
    }}
    body.cs-theme-system:not(#cs-scroll-color-a):not(#cs-scroll-color-b)::-webkit-scrollbar-thumb,
    body.cs-theme-system:not(#cs-scroll-color-a):not(#cs-scroll-color-b) *:not(#cs-scroll-color-c):not(#cs-scroll-color-d)::-webkit-scrollbar-thumb,
    body.cs-theme-system:not(#cs-scroll-color-a):not(#cs-scroll-color-b)::-webkit-scrollbar-thumb:hover,
    body.cs-theme-system:not(#cs-scroll-color-a):not(#cs-scroll-color-b) *:not(#cs-scroll-color-c):not(#cs-scroll-color-d)::-webkit-scrollbar-thumb:hover {{
        background: #9ca3af !important;
    }}
}}

</style>
</head>
<body class="cs-theme-{theme_class}" lang="{lang_attr}">
<div class="cs-shard-wrap">
    <div class="cs-section-pill">{texts["section_pill"]}</div>

    <div class="hidden-solver-elements" aria-hidden="true">
        <div id="grid-container" class="grid"></div>
        <button id="fill-all-btn" type="button">{texts["solve"]}</button>
        <button id="reset-grid-btn" type="button">{texts["clear"]}</button>
        <button id="random-fill-btn" type="button">{texts["clear"]}</button>
    </div>

    <div class="cs-top-grid">
        <section class="cs-card">
            <h3 class="cs-title">{texts["auto_title"]}</h3>
            <p class="cs-desc">{texts["auto_desc"]}</p>
            <div class="cs-target">{target_desc}</div>
            <div class="cs-action-row">
                <button id="solve-btn" type="button">{texts["solve"]}</button>
                <button id="clear-pieces-btn" type="button">{texts["clear"]}</button>
            </div>

            <div class="cs-upload-block">
                <h3 class="cs-title">{texts["upload_title"]}</h3>
                <p class="cs-upload-help">{texts["upload_help"]}</p>
                <input type="file" id="image-upload" accept="image/*" multiple style="position:absolute;width:1px;height:1px;opacity:0;overflow:hidden;">
                <div class="cs-upload-row">
                    <label for="image-upload" id="upload-btn">{texts["upload"]}</label>
                    <button id="usage-btn" type="button">{texts["usage"]}</button>
                </div>
                <div id="upload-status"></div>
            </div>
        </section>

        <section class="cs-card cs-result-card">
            <h3 class="cs-title">{texts["result_title"]}</h3>
            <div id="solution-summary" class="solution-summary"></div>
            <div id="solutions-container" class="solutions-container"><div class="cs-empty-result">{texts["result_empty"]}</div></div>
        </section>
    </div>

    <section class="pieces-section cs-card">
        <h3>{texts["pieces_title"]}</h3>
        <div id="piece-palette" class="palette"></div>
    </section>

    <div id="preview-container" style="display:none;"><img id="preview-image" alt=""></div>
</div>

{usage_modal}

<script>
(function() {{
    function cleanEmojiText(root) {{
        if (!root) return;
        const emojiPattern = /[\\u2600-\\u27BF\\u20E3]|\\uD83C[\\uDF00-\\uDFFF]|\\uD83D[\\uDC00-\\uDEFF]|\\uD83E[\\uDD00-\\uDDFF]/g;
        const keycapPattern = /[0-9]\\uFE0F?\\u20E3/g;
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
        const nodes = [];
        while (walker.nextNode()) nodes.push(walker.currentNode);
        nodes.forEach(n => {{
            const orig = n.nodeValue;
            let cleaned = orig.replace(keycapPattern, '').replace(emojiPattern, '');
            if (cleaned !== orig) {{
                cleaned = cleaned.replace(/\\s{{2,}}/g, ' ').trimStart();
                n.nodeValue = cleaned;
            }}
        }});
        root.querySelectorAll('button').forEach(btn => {{
            if (btn.textContent.trim() === '수정') btn.style.display = 'none';
        }});
        root.querySelectorAll('h4').forEach(h => {{
            if ((h.textContent || '').includes('인식된 조각')) h.style.display = 'none';
        }});
    }}
    function cookieSimGradeColor(card) {{
        const raw = `${{card.dataset.selectedGrade || ''}} ${{card.dataset.grade || ''}} ${{card.style.background || ''}} ${{card.style.backgroundColor || ''}} ${{card.style.borderColor || ''}}`.toLowerCase();
        if (raw.includes('unique') || raw.includes('255, 204, 0') || raw.includes('255,204,0')) return '#ffcc00';
        if (raw.includes('super') || raw.includes('255, 100, 100') || raw.includes('255,100,100')) return '#ff5b66';
        if (raw.includes('epic') || raw.includes('200, 100, 255') || raw.includes('200,100,255')) return '#b46bff';
        if (raw.includes('rare') || raw.includes('100, 150, 255') || raw.includes('100,150,255')) return '#5d8cff';
        return '#ff4048';
    }}
    function cookieSimNormalizePieceCard(card) {{
        const gradeColor = cookieSimGradeColor(card);
        const needsCheck = card.dataset.hasGreenTag === 'true';
        let statChip = card.querySelector('.cs-modal-stat-chip');
        const isUniqueCard = gradeColor === '#ffcc00' || ((card.dataset.grade || '').toLowerCase() === 'unique') || ((card.dataset.selectedGrade || '').toLowerCase() === 'unique');
        if (isUniqueCard && statChip) {{
            // 유니크 조각도 일반 조각과 동일하게 스탯 박스를 보여주되, '없음' 고정 표기 + 수정 불가 처리한다.
            statChip.textContent = (typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en') ? 'None' : '없음';
            statChip.style.cursor = 'default';
            statChip.style.pointerEvents = 'none';
        }}
        const isDarkUi = (document.body.classList.contains('cs-theme-dark') || (document.body.classList.contains('cs-theme-system') && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches));
        // 카드 높이를 내용물(칩 20 + 스탯 18 + 미리보기 76 + 개수 20 + gap 4x3 + padding 4x2)에 딱 맞춰
        // 위(세트 칩~배경)와 아래(x1~배경) 여백이 4px로 동일해지도록 한다. 라이트 모드는 테두리 1px x2 만큼 추가.
        const cardH = statChip ? (isDarkUi ? '154px' : '156px') : (isDarkUi ? '132px' : '134px');
        const chipBg = isDarkUi ? '#303236' : '#fff';
        const statText = isDarkUi ? '#f3f4f6' : '#111827';
        card.style.width = '100%';
        card.style.minWidth = '0';
        card.style.height = cardH;
        card.style.minHeight = cardH;
        card.style.maxHeight = cardH;
        card.style.padding = '4px';
        card.style.gap = '4px';
        card.style.justifyContent = 'flex-start';
        card.style.alignItems = 'stretch';
        card.style.boxSizing = 'border-box';
        card.style.border = isDarkUi ? '0' : `1px solid ${{gradeColor}}`;
        card.style.borderRadius = '8px';
        card.style.overflow = 'hidden';
        card.style.boxShadow = 'none';
        card.style.transform = 'none';
        card.style.transition = 'none';
        const chip = card.firstElementChild;
        if (chip) {{
            chip.style.width = '100%';
            chip.style.background = chipBg;
            chip.style.borderRadius = '6px';
            chip.style.padding = '3px 2px';
            chip.style.height = '20px';
            chip.style.minHeight = '20px';
            chip.style.maxHeight = '20px';
            chip.style.boxSizing = 'border-box';
            chip.style.textAlign = 'center';
            chip.style.fontSize = '11px';
            chip.style.lineHeight = '14px';
            chip.style.fontWeight = '800';
            chip.style.color = '#10b981';
            chip.style.flex = '0 0 20px';
            chip.style.margin = '0';
        }}
        if (statChip) {{
            statChip.style.width = '100%';
            statChip.style.background = chipBg;
            statChip.style.borderRadius = '6px';
            statChip.style.padding = '3px 2px';
            statChip.style.height = '18px';
            statChip.style.minHeight = '18px';
            statChip.style.maxHeight = '18px';
            statChip.style.flex = '0 0 18px';
            statChip.style.boxSizing = 'border-box';
            statChip.style.textAlign = 'center';
            statChip.style.fontSize = '9.5px';
            statChip.style.lineHeight = '12px';
            statChip.style.fontWeight = '800';
            statChip.style.color = statText;
            statChip.style.whiteSpace = 'nowrap';
            statChip.style.overflow = 'hidden';
            statChip.style.textOverflow = 'ellipsis';
            statChip.style.margin = '0';
        }}

        card.querySelectorAll('button').forEach(btn => {{
            if ((btn.textContent || '').trim().includes('수정') || (btn.textContent || '').trim().includes('조각 선택')) {{
                btn.style.display = 'none';
                btn.style.margin = '0';
                btn.style.padding = '0';
                btn.style.height = '0';
                btn.style.minHeight = '0';
            }}
        }});

        const preview = card.querySelector('.piece-preview');
        if (preview) {{
            const previewBox = preview.parentElement && preview.parentElement !== card ? preview.parentElement : preview;
            previewBox.style.width = '100%';
            previewBox.style.height = '76px';
            previewBox.style.minHeight = '76px';
            previewBox.style.maxHeight = '76px';
            previewBox.style.flex = '0 0 76px';
            previewBox.style.background = '#fff';
            previewBox.style.border = '0';
            previewBox.style.borderRadius = '6px';
            previewBox.style.padding = '0';
            previewBox.style.margin = '0';
            previewBox.style.boxSizing = 'border-box';
            previewBox.style.overflow = 'hidden';
            previewBox.style.display = 'flex';
            previewBox.style.alignItems = 'center';
            previewBox.style.justifyContent = 'center';
            previewBox.style.cursor = 'pointer';
            previewBox.style.gap = '0';
            preview.style.width = '100%';
            preview.style.height = '100%';
            preview.style.minHeight = '76px';
            preview.style.maxHeight = '76px';
            preview.style.flex = '0 0 76px';
            preview.style.background = '#fff';
            preview.style.border = '0';
            preview.style.borderRadius = '6px';
            preview.style.padding = '0';
            preview.style.margin = '0';
            preview.style.transform = 'none';
            preview.style.overflow = 'hidden';
            preview.style.display = 'flex';
            preview.style.alignItems = 'center';
            preview.style.justifyContent = 'center';
            const grid = preview.firstElementChild;
            if (grid) {{
                grid.style.transform = 'scale(0.58)';
                grid.style.transformOrigin = 'center center';
            }}
        }}
        const count = card.querySelector('[data-role="count-badge"]') || Array.from(card.children).find(el => (el.textContent || '').trim().startsWith('×'));
        if (count) {{
            count.style.width = '100%';
            count.style.background = chipBg;
            count.style.borderRadius = '6px';
            count.style.padding = '3px 2px';
            count.style.height = '20px';
            count.style.minHeight = '20px';
            count.style.maxHeight = '20px';
            count.style.flex = '0 0 20px';
            count.style.boxSizing = 'border-box';
            count.style.textAlign = 'center';
            count.style.fontSize = '11px';
            count.style.lineHeight = '14px';
            count.style.fontWeight = '900';
            count.style.color = gradeColor;
            count.style.margin = '0';
            count.style.cursor = 'pointer';
        }}
        if (!card.dataset.csHoverTuned) {{
            card.dataset.csHoverTuned = 'true';
            card.addEventListener('mouseenter', () => {{
                card.style.transform = 'none';
                card.style.boxShadow = 'none';
            }});
            card.addEventListener('mouseleave', () => {{
                card.style.transform = 'none';
                card.style.boxShadow = 'none';
                card.style.border = isDarkUi ? '0' : `1px solid ${{gradeColor}}`;
            }});
        }}
    }}
    function setupPaletteDropdown(palette) {{
        if (!palette) return;
        const oldTabs = document.getElementById('cs-palette-set-tabs');
        if (oldTabs) oldTabs.remove();
        const tabButtons = Array.from(document.querySelectorAll('.tab-btn'));
        if (!tabButtons.length) return;
        const btnWrap = tabButtons[0].parentElement;
        if (!btnWrap) return;
        btnWrap.style.display = 'none';

        let wrap = document.getElementById('cs-palette-set-select-wrap');
        let select = document.getElementById('cs-palette-set-select');
        let combo = document.getElementById('cs-palette-set-combo');
        let comboBtn = document.getElementById('cs-palette-set-combo-btn');
        let menu = document.getElementById('cs-palette-set-combo-menu');

        function showTab(tabId) {{
            const target = tabButtons.find(src => src.dataset.tabId === tabId);
            if (target) target.click();
            document.querySelectorAll('.tab-content').forEach(content => {{
                content.style.display = content.dataset.tabId === tabId ? 'block' : 'none';
            }});
            if (select) select.value = tabId;
            const label = tabButtons.find(src => src.dataset.tabId === tabId)?.textContent?.trim() || '';
            if (comboBtn) comboBtn.textContent = label;
            if (menu) {{
                menu.querySelectorAll('.cs-palette-dropdown-item').forEach(item => {{
                    item.classList.toggle('active', item.dataset.value === tabId);
                }});
            }}
        }}

        function bindComboEvents() {{
            if (!comboBtn.dataset.csDropdownToggleBound) {{
                comboBtn.dataset.csDropdownToggleBound = 'true';
                comboBtn.addEventListener('pointerdown', (event) => {{
                    event.preventDefault();
                    event.stopPropagation();
                    if (event.stopImmediatePropagation) event.stopImmediatePropagation();
                    const willOpen = !combo.classList.contains('open');
                    document.querySelectorAll('.cs-palette-dropdown.open').forEach(el => {{
                        if (el !== combo) el.classList.remove('open');
                    }});
                    combo.classList.toggle('open', willOpen);
                }});
                comboBtn.addEventListener('click', (event) => {{
                    event.preventDefault();
                    event.stopPropagation();
                    if (event.stopImmediatePropagation) event.stopImmediatePropagation();
                }});
            }}
            if (!combo.dataset.csDropdownInsideBound) {{
                combo.dataset.csDropdownInsideBound = 'true';
                combo.addEventListener('pointerdown', (event) => event.stopPropagation());
                combo.addEventListener('click', (event) => event.stopPropagation());
            }}
        }}

        function rebuildOptionsIfNeeded() {{
            const signature = tabButtons.map(btn => `${{btn.dataset.tabId || ''}}:${{(btn.textContent || '').trim()}}`).join('|');
            if (menu.dataset.csSignature === signature && select.dataset.csSignature === signature) return;
            menu.dataset.csSignature = signature;
            select.dataset.csSignature = signature;
            menu.textContent = '';
            select.textContent = '';
            tabButtons.forEach(btn => {{
                const value = btn.dataset.tabId || '';
                const label = (btn.textContent || '').trim();
                if (value === 'unique') return;

                const opt = document.createElement('option');
                opt.value = value;
                opt.textContent = label;
                select.appendChild(opt);

                const item = document.createElement('button');
                item.type = 'button';
                item.className = 'cs-palette-dropdown-item';
                item.dataset.value = value;
                item.textContent = label;
                item.tabIndex = -1;
                item.addEventListener('pointerdown', (event) => {{
                    event.preventDefault();
                    event.stopPropagation();
                    if (event.stopImmediatePropagation) event.stopImmediatePropagation();
                    showTab(value);
                    combo.classList.remove('open');
                }});
                item.addEventListener('click', (event) => {{
                    event.preventDefault();
                    event.stopPropagation();
                    if (event.stopImmediatePropagation) event.stopImmediatePropagation();
                }});
                menu.appendChild(item);
            }});
        }}

        if (!wrap || !select || !combo || !comboBtn || !menu) {{
            wrap = document.createElement('div');
            wrap.id = 'cs-palette-set-select-wrap';
            wrap.className = 'cs-palette-select-wrap';

            select = document.createElement('select');
            select.id = 'cs-palette-set-select';
            select.className = 'cs-palette-select';

            combo = document.createElement('div');
            combo.id = 'cs-palette-set-combo';
            combo.className = 'cs-palette-dropdown';

            comboBtn = document.createElement('button');
            comboBtn.id = 'cs-palette-set-combo-btn';
            comboBtn.type = 'button';
            comboBtn.className = 'cs-palette-dropdown-button';

            const comboBackdrop = document.createElement('div');
            comboBackdrop.className = 'cs-palette-dropdown-backdrop';

            menu = document.createElement('div');
            menu.id = 'cs-palette-set-combo-menu';
            menu.className = 'cs-palette-dropdown-menu';

            select.addEventListener('change', () => showTab(select.value));
            combo.appendChild(comboBtn);
            combo.appendChild(comboBackdrop);
            combo.appendChild(menu);
            wrap.appendChild(select);
            wrap.appendChild(combo);
            btnWrap.parentElement.insertBefore(wrap, btnWrap);
        }}

        let comboBackdrop = combo ? combo.querySelector('.cs-palette-dropdown-backdrop') : null;
        if (combo && !comboBackdrop) {{
            comboBackdrop = document.createElement('div');
            comboBackdrop.className = 'cs-palette-dropdown-backdrop';
            combo.insertBefore(comboBackdrop, menu);
        }}
        if (comboBackdrop && !comboBackdrop.dataset.csPaletteBackdropBound) {{
            comboBackdrop.dataset.csPaletteBackdropBound = 'true';
            comboBackdrop.addEventListener('pointerdown', (event) => {{
                event.preventDefault();
                event.stopPropagation();
                if (event.stopImmediatePropagation) event.stopImmediatePropagation();
                combo.classList.remove('open');
            }});
            comboBackdrop.addEventListener('click', (event) => {{
                event.preventDefault();
                event.stopPropagation();
                if (event.stopImmediatePropagation) event.stopImmediatePropagation();
            }});
        }}

        bindComboEvents();
        rebuildOptionsIfNeeded();

        if (!window.__csPaletteDropdownOutsideCloseBound) {{
            window.__csPaletteDropdownOutsideCloseBound = true;
            document.addEventListener('pointerdown', (event) => {{
                const path = event.composedPath ? event.composedPath() : [];
                const insideDropdown = path.some(el => el && el.classList && (el.classList.contains('cs-palette-dropdown') || el.classList.contains('cs-modal-select-dropdown')));
                if (!insideDropdown) {{
                    document.querySelectorAll('.cs-palette-dropdown.open, .cs-modal-select-dropdown.open').forEach(el => el.classList.remove('open'));
                }}
            }}, true);
            document.addEventListener('keydown', (event) => {{
                if (event.key === 'Escape') {{
                    document.querySelectorAll('.cs-palette-dropdown.open, .cs-modal-select-dropdown.open').forEach(el => el.classList.remove('open'));
                }}
            }});
        }}

        const activeBtn = tabButtons.find(btn => btn.style.color === 'white' || btn.classList.contains('active')) || tabButtons[0];
        const activeId = activeBtn?.dataset?.tabId || select.options[0]?.value || '';
        showTab(activeId);

        tabButtons.forEach(btn => {{
            if (!btn.dataset.csSelectSync) {{
                btn.dataset.csSelectSync = 'true';
                btn.addEventListener('click', () => {{
                    if (btn.dataset.tabId) showTab(btn.dataset.tabId);
                }});
            }}
        }});
    }}


    function csPositionModalSelectMenu(btn, menu) {{
        const rect = btn.getBoundingClientRect();
        const vh = window.innerHeight || document.documentElement.clientHeight || 0;
        const below = vh - rect.bottom - 10;
        const above = rect.top - 10;
        const desired = Math.min(280, Math.max(menu.scrollHeight || 0, 44));
        let top;
        let maxH;
        if (below >= Math.min(desired, 150) || below >= above) {{
            maxH = Math.max(80, Math.min(desired, below));
            top = rect.bottom + 4;
        }} else {{
            maxH = Math.max(80, Math.min(desired, above));
            top = rect.top - 4 - maxH;
        }}
        menu.style.setProperty('--cs-menu-top', top + 'px');
        menu.style.setProperty('--cs-menu-left', rect.left + 'px');
        menu.style.setProperty('--cs-menu-width', rect.width + 'px');
        menu.style.setProperty('--cs-menu-max-h', maxH + 'px');
    }}

    function setupModalSelectDropdown(sel) {{
        if (!sel || sel.dataset.csNativeSelectSkip === 'true') return;
        const options = Array.from(sel.options || []);
        if (!options.length) return;
        sel.classList.add('cs-modal-select-native');
        sel.style.display = 'none';

        let wrap = sel.nextElementSibling;
        if (!wrap || !wrap.classList || !wrap.classList.contains('cs-modal-select-wrap')) {{
            wrap = document.createElement('div');
            wrap.className = 'cs-modal-select-wrap';
            const combo = document.createElement('div');
            combo.className = 'cs-modal-select-dropdown';
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'cs-modal-select-button';
            const backdrop = document.createElement('div');
            backdrop.className = 'cs-modal-select-backdrop';
            const menu = document.createElement('div');
        menu.className = 'cs-modal-select-menu';
            menu.className = 'cs-modal-select-menu';
            combo.appendChild(btn);
            combo.appendChild(backdrop);
            combo.appendChild(menu);
            wrap.appendChild(combo);
            sel.parentNode.insertBefore(wrap, sel.nextSibling);
        }}
        const combo = wrap.querySelector('.cs-modal-select-dropdown');
        const btn = wrap.querySelector('.cs-modal-select-button');
        const menu = wrap.querySelector('.cs-modal-select-menu');
        if (!combo || !btn || !menu) return;
        let backdrop = wrap.querySelector('.cs-modal-select-backdrop');
        if (!backdrop) {{
            backdrop = document.createElement('div');
            backdrop.className = 'cs-modal-select-backdrop';
            combo.insertBefore(backdrop, menu);
        }}

        const signature = options.map(opt => `${{opt.value}}:${{opt.textContent}}`).join('|');
        if (menu.dataset.csSignature !== signature) {{
            menu.dataset.csSignature = signature;
            menu.textContent = '';
            options.forEach(opt => {{
                const item = document.createElement('button');
                item.type = 'button';
                item.className = 'cs-modal-select-item';
                item.dataset.value = opt.value;
                item.textContent = opt.textContent;
                item.tabIndex = -1;
                let touchStartX = 0;
                let touchStartY = 0;
                let touchMoved = false;
                const chooseModalSelectItem = (event) => {{
                    if (event) {{
                        event.preventDefault();
                        event.stopPropagation();
                        if (event.stopImmediatePropagation) event.stopImmediatePropagation();
                    }}
                    sel.value = opt.value;
                    sel.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    sel.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    btn.textContent = opt.textContent;
                    menu.querySelectorAll('.cs-modal-select-item').forEach(node => {{
                        node.classList.toggle('active', node.dataset.value === sel.value);
                    }});
                    combo.classList.remove('open');
                }};
                item.addEventListener('pointerdown', (event) => {{
                    event.stopPropagation();
                    if (event.stopImmediatePropagation) event.stopImmediatePropagation();
                    touchStartX = event.clientX || 0;
                    touchStartY = event.clientY || 0;
                    touchMoved = false;
                }});
                item.addEventListener('pointermove', (event) => {{
                    const dx = Math.abs((event.clientX || 0) - touchStartX);
                    const dy = Math.abs((event.clientY || 0) - touchStartY);
                    if (dx > 6 || dy > 6) touchMoved = true;
                }});
                item.addEventListener('pointerup', (event) => {{
                    if (!touchMoved) chooseModalSelectItem(event);
                }});
                item.addEventListener('pointercancel', () => {{
                    touchMoved = true;
                }});
                item.addEventListener('click', (event) => {{
                    event.preventDefault();
                    event.stopPropagation();
                    if (event.stopImmediatePropagation) event.stopImmediatePropagation();
                }});
                menu.appendChild(item);
            }});
        }}

        const currentOpt = options.find(opt => opt.value === sel.value) || options[sel.selectedIndex] || options[0];
        btn.textContent = currentOpt ? currentOpt.textContent : '';
        menu.querySelectorAll('.cs-modal-select-item').forEach(node => {{
            node.classList.toggle('active', node.dataset.value === sel.value);
        }});

        if (!btn.dataset.csModalDropdownBound) {{
            btn.dataset.csModalDropdownBound = 'true';
            btn.addEventListener('pointerdown', (event) => {{
                event.preventDefault();
                event.stopPropagation();
                if (event.stopImmediatePropagation) event.stopImmediatePropagation();
                const willOpen = !combo.classList.contains('open');
                document.querySelectorAll('.cs-palette-dropdown.open, .cs-modal-select-dropdown.open').forEach(el => {{
                    if (el !== combo) el.classList.remove('open');
                }});
                combo.classList.toggle('open', willOpen);
                if (willOpen) csPositionModalSelectMenu(btn, menu);
            }});
            if (!window.__csModalMenuViewportBound) {{
                window.__csModalMenuViewportBound = true;
                document.addEventListener('scroll', (event) => {{
                    const t = event.target;
                    if (t && t.classList && t.classList.contains('cs-modal-select-menu')) return;
                    document.querySelectorAll('.cs-modal-select-dropdown.open').forEach(el => el.classList.remove('open'));
                }}, true);
                window.addEventListener('resize', () => {{
                    document.querySelectorAll('.cs-modal-select-dropdown.open').forEach(el => el.classList.remove('open'));
                }});
            }}
            btn.addEventListener('click', (event) => {{
                event.preventDefault();
                event.stopPropagation();
                if (event.stopImmediatePropagation) event.stopImmediatePropagation();
            }});
        }}
        if (!backdrop.dataset.csDropdownBackdropBound) {{
            backdrop.dataset.csDropdownBackdropBound = 'true';
            backdrop.addEventListener('pointerdown', (event) => {{
                event.preventDefault();
                event.stopPropagation();
                if (event.stopImmediatePropagation) event.stopImmediatePropagation();
                combo.classList.remove('open');
            }});
            backdrop.addEventListener('click', (event) => {{
                event.preventDefault();
                event.stopPropagation();
                if (event.stopImmediatePropagation) event.stopImmediatePropagation();
            }});
        }}
        if (!combo.dataset.csDropdownInsideBound) {{
            combo.dataset.csDropdownInsideBound = 'true';
            combo.addEventListener('pointerdown', (event) => event.stopPropagation());
            combo.addEventListener('click', (event) => event.stopPropagation());
        }}
        if (!sel.dataset.csModalSelectSyncBound) {{
            sel.dataset.csModalSelectSyncBound = 'true';
            sel.addEventListener('change', () => {{
                const now = Array.from(sel.options || []).find(opt => opt.value === sel.value) || sel.options[sel.selectedIndex];
                if (now) btn.textContent = now.textContent;
                menu.querySelectorAll('.cs-modal-select-item').forEach(node => {{
                    node.classList.toggle('active', node.dataset.value === sel.value);
                }});
            }});
        }}
    }}

    function tunePiecePalette() {{

        const matchGapContainer = document.getElementById('solutions-container');
        if (matchGapContainer) {{
            matchGapContainer.style.paddingBottom = '6px';
            matchGapContainer.style.marginBottom = '0';
        }}
        document.querySelectorAll('.cs-result-card .solution, .cs-result-card .solution-card, .cs-result-card .solution-board-wrap, .cs-result-card .solution-grid').forEach(el => {{
            el.style.marginBottom = '0';
        }});


        const resultCard = document.querySelector('.cs-result-card');
        if (resultCard) {{
            resultCard.style.paddingBottom = '6px';
            resultCard.style.overflow = 'visible';
        }}
        const resultContainer = document.getElementById('solutions-container');
        if (resultContainer) {{
            resultContainer.style.paddingBottom = '6px';
            resultContainer.style.marginBottom = '0';
            resultContainer.style.overflow = 'visible';
        }}
        document.querySelectorAll('.cs-result-card .solution, .cs-result-card .solution-card, .cs-result-card .solution-board-wrap, .cs-result-card .solution-grid').forEach(el => {{
            el.style.marginBottom = '0';
        }});


        const uploadBtn = document.getElementById('upload-btn');
        const usageBtn = document.getElementById('usage-btn');
        [uploadBtn, usageBtn].forEach(btn => {{
            if (!btn) return;
            btn.style.height = '36px';
            btn.style.minHeight = '36px';
            btn.style.maxHeight = '36px';
            btn.style.padding = '0 8px';
            btn.style.display = 'flex';
            btn.style.alignItems = 'center';
            btn.style.justifyContent = 'center';
            btn.style.lineHeight = '14px';
            btn.style.boxSizing = 'border-box';
            btn.style.whiteSpace = 'nowrap';
        }});

        const palette = document.getElementById('piece-palette');
        if (!palette) return;
        const recognizedPiecesSection = palette.closest('.pieces-section');
        if (recognizedPiecesSection && recognizedPiecesSection.dataset.csRecognizedCardsVisible === 'true') {{
            recognizedPiecesSection.style.display = 'block';
            recognizedPiecesSection.style.height = 'auto';
            recognizedPiecesSection.style.minHeight = '0';
            recognizedPiecesSection.style.maxHeight = 'none';
            recognizedPiecesSection.style.margin = '12px 0 0 0';
            recognizedPiecesSection.style.padding = '12px';
            recognizedPiecesSection.style.border = 'none';
            recognizedPiecesSection.style.overflow = 'visible';
            palette.style.display = 'grid';
            palette.style.gridTemplateColumns = 'repeat(auto-fill, minmax(132px, 1fr))';
            palette.style.gap = '10px';
            palette.style.padding = '0';
            palette.style.width = '100%';
            palette.style.maxWidth = 'none';
            palette.style.height = 'auto';
            palette.style.maxHeight = 'none';
            palette.style.overflow = 'visible';
            palette.style.marginTop = '6px';
            const title = recognizedPiecesSection.querySelector(':scope > h3');
            if (title) {{
                title.style.display = 'block';
                title.textContent = (typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en') ? 'Recognized Shards' : '인식된 조각';
            }}
            return;
        }}
        setupPaletteDropdown(palette);
        const paletteSelect = document.getElementById('cs-palette-set-select');
        const paletteWrap = document.getElementById('cs-palette-set-select-wrap');
        const firstRegularContent = Array.from(palette.querySelectorAll('.tab-content')).find(content => content.dataset.tabId !== 'unique');
        const firstRegularId = firstRegularContent ? firstRegularContent.dataset.tabId : '';
        if (paletteSelect && firstRegularId) {{
            paletteSelect.value = firstRegularId;
            paletteSelect.dispatchEvent(new Event('change', {{ bubbles: true }}));
        }}
        palette.querySelectorAll('.tab-content').forEach(content => {{
            content.style.display = firstRegularId ? (content.dataset.tabId === firstRegularId) : (content.dataset.tabId !== 'unique');
        }});
        const uniqueContent = palette.querySelector('.tab-content[data-tab-id="unique"]');
        if (uniqueContent) uniqueContent.style.display = 'none';
        if (paletteWrap) paletteWrap.style.display = '';
        palette.style.padding = '0 16px 0 0';
        palette.style.minHeight = '0';
        palette.style.height = 'auto';
        palette.style.marginBottom = '0';
        palette.style.marginTop = '4px';
        palette.style.scrollbarWidth = 'thin';
        palette.style.scrollbarColor = '#9ca3af #e5e7eb';
        palette.style.width = '100%';
        palette.style.maxWidth = 'none';
        palette.style.boxSizing = 'border-box';
        const piecesSection = palette.closest('.pieces-section');
        if (piecesSection) {{
            piecesSection.style.display = 'none';
            piecesSection.style.height = '0';
            piecesSection.style.minHeight = '0';
            piecesSection.style.maxHeight = '0';
            piecesSection.style.margin = '0';
            piecesSection.style.padding = '0';
            piecesSection.style.border = '0';
            piecesSection.style.overflow = 'hidden';

            const title = piecesSection.querySelector(':scope > h3');
            if (title) title.style.display = 'none';
        }}
        palette.style.display = 'none';
        palette.querySelectorAll('.piece-grid').forEach(grid => {{
            grid.style.display = 'grid';
            grid.style.gridTemplateColumns = 'repeat(5, minmax(0, 1fr))';
            grid.style.gap = '8px';
            grid.style.alignItems = 'stretch';
            grid.style.width = '100%';
            grid.style.maxWidth = 'none';
            grid.style.margin = '0';
            grid.style.padding = '0';
            grid.style.boxSizing = 'border-box';
        }});
        palette.querySelectorAll('.tab-content').forEach(content => {{
            content.style.padding = '0';
            content.style.margin = '0';
            content.style.border = '0';
            content.style.background = '#fff';
            content.style.borderRadius = '10px';
            content.style.width = '100%';
            content.style.boxSizing = 'border-box';
        }});
        palette.querySelectorAll('.tab-content > div:first-child').forEach(desc => {{
            if ((desc.textContent || '').includes('조각')) desc.style.display = 'none';
        }});
        const gradeMeta = {{
            rare: {{ label: '{"Rare" if english else "레어"}', color: '#5d8cff', bg: '#eef4ff', border: '#9bb8ff' }},
            epic: {{ label: '{"Epic" if english else "에픽"}', color: '#aa96da', bg: '#f3efff', border: '#c7b8ef' }},
            super: {{ label: '{"Super" if english else "슈에"}', color: '#ff6b6b', bg: '#ffecec', border: '#ffb5b5' }}
        }};
        function makeGradeCol(pieceName, grade) {{
            const meta = gradeMeta[grade];
            const col = document.createElement('div');
            col.style.display = 'flex';
            col.style.flexDirection = 'column';
            col.style.gap = '3px';
            col.style.minWidth = '0';
            const label = document.createElement('div');
            label.textContent = meta.label;
            label.style.height = '18px';
            label.style.minHeight = '18px';
            label.style.padding = '0 0px';
            label.style.borderRadius = '6px';
            label.style.display = 'flex';
            label.style.alignItems = 'center';
            label.style.justifyContent = 'center';
            label.style.border = 'none';
            label.style.background = meta.bg;
            label.style.color = meta.color;
            label.style.fontSize = '5px';
            label.style.fontWeight = '800';
            label.style.textAlign = 'center';
            label.style.lineHeight = '18px';
            label.style.boxSizing = 'border-box';
            const input = document.createElement('input');
            input.type = 'number';
            input.value = '0';
            input.min = '0';
            input.max = '10';
            input.id = `piece-count-${{pieceName}}-${{grade}}`;
            input.classList.add('piece-count-input');
            input.style.width = '100%';
            input.style.height = '23px';
            input.style.padding = '2px 2px';
            input.style.fontSize = '5px';
            input.style.background = '#fff';
            input.style.textAlign = 'center';
            input.style.border = 'none';
            input.style.borderRadius = '6px';
            input.style.fontWeight = '800';
            input.style.boxSizing = 'border-box';
            input.style.color = '#111827';
            col.appendChild(label);
            col.appendChild(input);
            return col;
        }}
        function styleGradeColumn(col, grade) {{
            const meta = gradeMeta[grade];
            if (!meta || !col) return;
            col.style.display = 'flex';
            col.style.flexDirection = 'column';
            col.style.gap = '3px';
            col.style.minWidth = '0';
            const label = Array.from(col.children).find(el => !el.matches || !el.matches('input'));
            if (label) {{
                label.textContent = meta.label;
                label.style.height = '20px';
                label.style.minHeight = '20px';
                label.style.padding = '0 1px';
                label.style.borderRadius = '6px';
                label.style.display = 'flex';
                label.style.alignItems = 'center';
                label.style.justifyContent = 'center';
                label.style.border = 'none';
                label.style.background = meta.bg;
                label.style.color = meta.color;
                label.style.fontSize = '11px';
                label.style.fontWeight = '800';
                label.style.textAlign = 'center';
                label.style.lineHeight = '20px';
                label.style.boxSizing = 'border-box';
            }}
            const input = col.querySelector('input');
            if (input) {{
                input.style.width = '100%';
                input.style.height = '23px';
                input.style.minHeight = '23px';
                input.style.padding = '2px 2px';
                input.style.fontSize = '12px';
                input.style.textAlign = 'center';
                input.style.background = '#fff';
                input.style.border = 'none';
                input.style.borderRadius = '6px';
                input.style.fontWeight = '800';
                input.style.boxSizing = 'border-box';
                input.style.color = '#111827';
            }}
        }}
        palette.querySelectorAll('.piece-item').forEach(card => {{
            card.style.minHeight = '0';
            card.style.height = 'auto';
            card.style.padding = '6px';
            card.style.display = 'flex';
            card.style.flexDirection = 'column';
            card.style.gap = '5px';
            card.style.borderRadius = '10px';
            card.style.border = 'none';
            card.style.background = '#f3f4f6';
            card.style.boxShadow = 'none';
            card.style.transform = 'none';
            card.style.transition = 'none';
            const preview = card.querySelector(':scope > .piece-preview');
            if (preview) {{
                preview.style.width = '100%';
                preview.style.setProperty('width', '100%', 'important');
                preview.style.alignSelf = 'stretch';
                preview.style.height = '74px';
                preview.style.minHeight = '74px';
                preview.style.flex = '0 0 74px';
                preview.style.background = '#fff';
                preview.style.border = 'none';
                preview.style.borderRadius = '8px';
                preview.style.padding = '0';
                preview.style.margin = '0';
                preview.style.display = 'flex';
                preview.style.alignItems = 'center';
                preview.style.justifyContent = 'center';
                preview.style.overflow = 'hidden';
                preview.style.boxShadow = 'none';
                const grid = preview.firstElementChild;
                if (grid) {{
                    grid.style.transform = 'scale(0.58)';
                    grid.style.transformOrigin = 'center center';
                }}
            }}
            let grades = Array.from(card.querySelectorAll('input.piece-count-input'));
            const uniqueInput = grades.find(input => /-unique$/.test(input.id || ''));
            const gradeRow = Array.from(card.children).find(el => el.querySelector && el.querySelector('input.piece-count-input') && el.style.display !== 'none');
            if (uniqueInput) {{
                card.dataset.csUniqueCard = 'true';
                const uniqueCol = uniqueInput.closest('div');
                if (gradeRow && gradeRow !== card && gradeRow !== uniqueInput) {{
                    gradeRow.style.display = 'none';
                }}
                if (uniqueCol && uniqueCol !== card) {{
                    uniqueCol.style.display = 'none';
                }}
                uniqueInput.style.display = 'none';
                uniqueInput.style.setProperty('display', 'none', 'important');
                uniqueInput.style.width = '0';
                uniqueInput.style.height = '0';
                uniqueInput.style.minWidth = '0';
                uniqueInput.style.minHeight = '0';
                uniqueInput.style.margin = '0';
                uniqueInput.style.padding = '0';
                uniqueInput.style.border = '0';
            }} else {{
                if (gradeRow) {{
                    gradeRow.style.display = 'grid';
                    gradeRow.style.gridTemplateColumns = 'repeat(3, minmax(0, 1fr))';
                    gradeRow.style.gap = '4px';
                    gradeRow.style.marginTop = '0';
                    gradeRow.style.width = '100%';
                }}
                ['rare','epic','super'].forEach(grade => {{
                    const input = card.querySelector(`input[id$="-${{grade}}"]`);
                    if (input) styleGradeColumn(input.closest('div'), grade);
                }});
            }}
            if (!card.dataset.csPaletteHoverTuned) {{
                card.dataset.csPaletteHoverTuned = 'true';
                card.addEventListener('mouseenter', () => {{
                    card.style.transform = 'none';
                    card.style.boxShadow = 'none';
                    card.style.borderColor = 'transparent';
                }});
                card.addEventListener('mouseleave', () => {{
                    card.style.transform = 'none';
                    card.style.boxShadow = 'none';
                    card.style.borderColor = 'transparent';
                }});
            }}
        }});
        const clearBtn = document.getElementById('clear-pieces-btn');
        if (clearBtn && !clearBtn.dataset.csClearAllInputs) {{
            clearBtn.dataset.csClearAllInputs = 'true';
            clearBtn.addEventListener('click', () => {{
                setTimeout(() => {{
                    palette.querySelectorAll('input.piece-count-input').forEach(input => {{ input.value = '0'; }});
                }}, 0);
            }});
        }}
        if (document.getElementById('cs-palette-set-combo-btn')) {{
            document.body.classList.add('cs-palette-ready');
        }}
    }}
    function tuneModal(root) {{
        tunePiecePalette();
        document.querySelectorAll('body > div[style*="z-index: 2000"]').forEach(modal => {{
            cleanEmojiText(modal);
            const content = modal.firstElementChild;
            if (content) {{
                content.style.padding = '14px';
                content.style.maxWidth = '820px';
                content.style.maxHeight = '84vh';
                content.style.boxSizing = 'border-box';
            }}
            modal.querySelectorAll('select').forEach(sel => {{
                setupModalSelectDropdown(sel);
            }});
            modal.querySelectorAll('.image-tab-content').forEach(tab => {{
                tab.style.background = '#fff';
                tab.style.border = '0';
                tab.style.borderRadius = '0';
                tab.style.padding = '0';
                tab.style.boxShadow = 'none';
            }});
            Array.from(modal.querySelectorAll('div')).forEach(el => {{
                const txt = (el.textContent || '').trim();
                if (txt.startsWith('이 사진의 모든 조각이 들어갈 세트') || txt.startsWith('Set for all shards in this image')) {{
                    let box = el.querySelector && el.querySelector('select') ? el : el.parentElement;
                    if (box && box.classList && box.classList.contains('image-tab-content')) return;
                    if (box) {{
                        box.style.background = 'transparent';
                        box.style.border = 'none';
                        box.style.borderRadius = '0';
                        box.style.padding = '0';
                        box.style.boxShadow = 'none';
                    }}
                }}
            }});
            modal.querySelectorAll('button').forEach(btn => {{
                const t = (btn.textContent || '').trim();
                btn.style.transform = 'none';
                btn.style.boxShadow = 'none';
                const bg = String(btn.style.background || btn.style.backgroundImage || '');
                const isImageTabBtn = /\\.(jpg|jpeg|png|webp)$/i.test(t) || /^KakaoTalk_/i.test(t);
                const isActiveImageTab = isImageTabBtn && (btn.style.color === 'white' || bg.includes('667eea') || bg.includes('764ba2') || bg.includes('linear-gradient'));
                if (isActiveImageTab) {{
                    btn.style.background = '#ff4048';
                    btn.style.backgroundImage = 'none';
                    btn.style.color = '#fff';
                }}
                if (isImageTabBtn) {{
                    btn.style.minWidth = '0';
                    btn.style.overflow = 'hidden';
                    btn.style.textOverflow = 'ellipsis';
                    btn.style.whiteSpace = 'nowrap';
                }}
                if (isImageTabBtn && !btn.dataset.csImageTabClickFixed) {{
                    btn.dataset.csImageTabClickFixed = 'true';
                    btn.addEventListener('click', () => setTimeout(() => {{
                        document.querySelectorAll('body > div[style*="z-index: 2000"] button').forEach(b => {{
                            const tt = (b.textContent || '').trim();
                            const bbg = String(b.style.background || b.style.backgroundImage || '');
                            const imageTab = /\\.(jpg|jpeg|png|webp)$/i.test(tt) || /^KakaoTalk_/i.test(tt);
                            if (imageTab && (b.style.color === 'white' || bbg.includes('667eea') || bbg.includes('764ba2') || bbg.includes('linear-gradient'))) {{
                                b.style.background = '#ff4048';
                                b.style.backgroundImage = 'none';
                                b.style.color = '#fff';
                            }}
                        }});
                    }}, 0));
                }}
                if (t === '모든 사진 확인' || t === 'Confirm All Images') {{
                    btn.style.background = '#ff4048';
                    btn.style.color = '#fff';
                    btn.style.borderRadius = '8px';
                }}
            }});
            modal.querySelectorAll('div[style*="flex-wrap"]').forEach(list => {{
                list.style.display = 'grid';
                list.style.gridTemplateColumns = 'repeat(auto-fill, minmax(132px, 1fr))';
                list.style.gap = '8px';
                list.style.background = 'transparent';
                list.style.padding = '0';
                list.style.alignItems = 'stretch';
                list.style.width = '100%';
            }});
            modal.querySelectorAll('div[data-image-index][data-piece-index], div[data-is-normal="true"]').forEach(card => {{
                const rawImg = card.querySelector('img');
                if (rawImg && rawImg.parentElement && !rawImg.closest('.piece-preview')) rawImg.parentElement.style.display = 'none';
                cookieSimNormalizePieceCard(card);
                card.querySelectorAll('button').forEach(btn => {{
                    if (btn.textContent.trim() === '수정') btn.style.display = 'none';
                }});
            }});
            modal.querySelectorAll('.image-tab-content').forEach(tab => {{
                const sel = tab.querySelector('select');
                if (!sel) return;
                const csSetChipDefault = '{"Select Set" if english else "세트 선택"}';
                const syncSetLabel = () => {{
                    const label = sel.value ? (sel.options[sel.selectedIndex]?.textContent || csSetChipDefault).trim() : csSetChipDefault;
                    tab.querySelectorAll('div[data-image-index][data-piece-index], div[data-is-normal="true"]').forEach(card => {{
                        const chip = card.firstElementChild;
                        if (chip) chip.textContent = label;
                    }});
                }};
                if (!sel.dataset.csSetChipSync) {{
                    sel.dataset.csSetChipSync = 'true';
                    sel.addEventListener('change', syncSetLabel);
                    sel.addEventListener('input', syncSetLabel);
                }}
                syncSetLabel();
            }});
        }});
        document.querySelectorAll('body > div[style*="z-index: 3000"]').forEach(modal => {{
            cleanEmojiText(modal);
            const content = modal.firstElementChild;
            if (content) {{
                content.style.height = 'auto';
                content.style.maxWidth = '920px';
                content.style.maxHeight = '82vh';
                content.style.padding = '16px';
                content.style.boxSizing = 'border-box';
            }}
            const grids = Array.from(modal.querySelectorAll('div')).filter(el =>
                el.style && el.style.gridTemplateColumns && !el.closest('.piece-preview') && el.children.length >= 8
            );
            grids.forEach(grid => {{
                grid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(122px, 1fr))';
                grid.style.gap = '10px';
                grid.style.maxHeight = '62vh';
                grid.style.overflowY = 'auto';
            }});
            modal.querySelectorAll('.piece-preview').forEach(preview => {{
                preview.style.transform = 'none';
                preview.style.width = '100%';
                preview.style.height = '96px';
                preview.style.minHeight = '96px';
                preview.style.background = '#fff';
                preview.style.border = '0';
                preview.style.borderRadius = '8px';
                preview.style.padding = '0';
                preview.style.margin = '0';
                preview.style.overflow = 'hidden';
                preview.style.display = 'flex';
                preview.style.alignItems = 'center';
                preview.style.justifyContent = 'center';
                const inner = preview.firstElementChild;
                if (inner) {{
                    inner.style.transform = 'scale(0.68)';
                    inner.style.transformOrigin = 'center center';
                }}
            }});
            modal.querySelectorAll('.piece-preview').forEach(preview => {{
                const card = preview.parentElement;
                if (card && card.style) {{
                    card.style.padding = '4px';
                    card.style.borderRadius = '8px';
                    card.style.background = '#fff';
                    card.style.boxSizing = 'border-box';
                    card.style.overflow = 'hidden';
                    card.style.boxShadow = 'none';
                    if (card.style.borderColor === 'rgb(102, 126, 234)' || card.style.borderColor === '#667eea') card.style.borderColor = 'transparent';
                }}
            }});
            Array.from(modal.querySelectorAll('div')).forEach(card => {{
                if (!card.querySelector || !card.querySelector('.piece-preview')) return;
                if (card.closest('.piece-preview')) return;
                const hasPreview = card.children && card.children.length <= 3;
                if (!hasPreview) return;
                const wasBlue = String(card.style.borderColor || '').includes('102') || String(card.style.boxShadow || '').includes('102') || String(card.style.background || '').includes('f0f4ff');
                if (wasBlue || card.dataset.csSelected === 'true') {{
                    card.dataset.csSelected = 'true';
                    card.style.borderColor = 'transparent';
                }}
                card.style.background = '#fff';
                card.style.boxShadow = 'none';
                card.style.transform = 'none';
                card.style.transition = 'none';
                if (!card.dataset.csPickerHoverTuned) {{
                    card.dataset.csPickerHoverTuned = 'true';
                    if (card.querySelector(':scope > .piece-preview')) {{
                        card.classList.add('cs-picker-card');
                    }}
                }}
            }});
        }});
    }}
    // 분석 중 조각 카드가 많이 생성될 때마다 전체 DOM을 계속 훑으면 느려져서,
    // 변경 감지는 짧게 모았다가 한 번만 정리합니다.
    let cookieSimTuneTimer = null;
    function scheduleCookieSimTune() {{
        if (cookieSimTuneTimer) return;
        cookieSimTuneTimer = window.setTimeout(() => {{
            cookieSimTuneTimer = null;
            tuneModal();
        }}, 120);
    }}
    const observer = new MutationObserver(scheduleCookieSimTune);
    document.addEventListener('DOMContentLoaded', () => {{
        observer.observe(document.body, {{ childList: true, subtree: true }});
        tuneModal();
        // Safety: never leave the palette hidden if tuning could not run.
        window.setTimeout(() => {{
            try {{ tuneModal(); }} catch (e) {{}}
            document.body.classList.add('cs-palette-ready');
        }}, 3000);
    
    function fixDarkPaletteBackground() {{
        if (!document.body.classList.contains('cs-theme-dark')) return;
        const palette = document.getElementById('piece-palette');
        if (!palette) return;
        palette.style.background = '#303236';
        palette.style.backgroundColor = '#303236';

        palette.querySelectorAll('.piece-grid').forEach((grid) => {{
            grid.style.background = '#303236';
            grid.style.backgroundColor = '#303236';
        }});
    }}

    const darkPaletteObserverTarget = document.getElementById('piece-palette');
    if (darkPaletteObserverTarget) {{

        let darkPaletteObserverPending = false;
        const darkPaletteObserverCallback = () => {{
            if (darkPaletteObserverPending) return;
            darkPaletteObserverPending = true;
            requestAnimationFrame(() => {{
                darkPaletteObserverPending = false;
                fixDarkPaletteBackground();
            }});
        }};
        const darkPaletteObserver = new MutationObserver(darkPaletteObserverCallback);
        darkPaletteObserver.observe(darkPaletteObserverTarget, {{ childList: true, subtree: true }});
        fixDarkPaletteBackground();
        window.addEventListener('load', fixDarkPaletteBackground);
        setTimeout(fixDarkPaletteBackground, 100);
        setTimeout(fixDarkPaletteBackground, 500);
    }}


    function fixExactManualPaletteColors() {{
        if (!document.body.classList.contains('cs-theme-dark')) return;
        const palette = document.getElementById('piece-palette');
        if (!palette) return;

        palette.style.background = '#24262a';
        palette.style.backgroundColor = '#24262a';

        palette.querySelectorAll('.piece-grid').forEach((grid) => {{
            grid.style.background = '#24262a';
            grid.style.backgroundColor = '#24262a';
        }});

        palette.querySelectorAll('.piece-item').forEach((item) => {{
            item.style.background = '#303236';
            item.style.backgroundColor = '#303236';
        }});

        palette.querySelectorAll('.piece-preview').forEach((preview) => {{
            preview.style.background = '#303236';
            preview.style.backgroundColor = '#303236';
        }});

        palette.querySelectorAll('.piece-count-input').forEach((input) => {{
            input.style.background = '#303236';
            input.style.backgroundColor = '#303236';
            input.style.color = '#ffffff';
            input.style.borderColor = '#24262a';
        }});
    }}

    const exactManualPaletteColorTarget = document.getElementById('piece-palette');
    if (exactManualPaletteColorTarget) {{

        let exactManualPaletteColorObserverPending = false;
        const exactManualPaletteColorObserverCallback = () => {{
            if (exactManualPaletteColorObserverPending) return;
            exactManualPaletteColorObserverPending = true;
            requestAnimationFrame(() => {{
                exactManualPaletteColorObserverPending = false;
                fixExactManualPaletteColors();
            }});
        }};
        const exactManualPaletteColorObserver = new MutationObserver(exactManualPaletteColorObserverCallback);
        exactManualPaletteColorObserver.observe(exactManualPaletteColorTarget, {{ childList: true, subtree: true }});
        fixExactManualPaletteColors();
        window.addEventListener('load', fixExactManualPaletteColors);
        setTimeout(fixExactManualPaletteColors, 100);
        setTimeout(fixExactManualPaletteColors, 500);
    }}


    function fixPieceOuterColorFinal() {{
        if (!document.body.classList.contains('cs-theme-dark')) return;
        const palette = document.getElementById('piece-palette');
        if (!palette) return;

        palette.querySelectorAll('.piece-item').forEach((item) => {{
            item.style.background = '#303236';
            item.style.backgroundColor = '#303236';
        }});

        palette.querySelectorAll('.piece-preview').forEach((preview) => {{
            preview.style.background = '#303236';
            preview.style.backgroundColor = '#303236';
        }});

        palette.querySelectorAll('.piece-count-input').forEach((input) => {{
            input.style.background = '#303236';
            input.style.backgroundColor = '#303236';
            input.style.color = '#ffffff';
        }});
    }}

    const pieceOuterColorTarget = document.getElementById('piece-palette');
    if (pieceOuterColorTarget) {{

        let pieceOuterColorObserverPending = false;
        const pieceOuterColorObserverCallback = () => {{
            if (pieceOuterColorObserverPending) return;
            pieceOuterColorObserverPending = true;
            requestAnimationFrame(() => {{
                pieceOuterColorObserverPending = false;
                fixPieceOuterColorFinal();
            }});
        }};
        const pieceOuterColorObserver = new MutationObserver(pieceOuterColorObserverCallback);
        pieceOuterColorObserver.observe(pieceOuterColorTarget, {{ childList: true, subtree: true }});
        fixPieceOuterColorFinal();
        window.addEventListener('load', fixPieceOuterColorFinal);
        setTimeout(fixPieceOuterColorFinal, 100);
        setTimeout(fixPieceOuterColorFinal, 500);
    }}


    function fixPaletteEmptyAreaColorFinal() {{
        if (!document.body.classList.contains('cs-theme-dark')) return;
        const palette = document.getElementById('piece-palette');
        if (!palette) return;

        palette.style.background = '#303236';
        palette.style.backgroundColor = '#303236';

        palette.querySelectorAll('.piece-grid').forEach((grid) => {{
            grid.style.background = '#303236';
            grid.style.backgroundColor = '#303236';
        }});
    }}

    const paletteEmptyAreaTarget = document.getElementById('piece-palette');
    if (paletteEmptyAreaTarget) {{

        let paletteEmptyAreaObserverPending = false;
        const paletteEmptyAreaObserverCallback = () => {{
            if (paletteEmptyAreaObserverPending) return;
            paletteEmptyAreaObserverPending = true;
            requestAnimationFrame(() => {{
                paletteEmptyAreaObserverPending = false;
                fixPaletteEmptyAreaColorFinal();
            }});
        }};
        const paletteEmptyAreaObserver = new MutationObserver(paletteEmptyAreaObserverCallback);
        paletteEmptyAreaObserver.observe(paletteEmptyAreaTarget, {{ childList: true, subtree: true }});
        fixPaletteEmptyAreaColorFinal();
        window.addEventListener('load', fixPaletteEmptyAreaColorFinal);
        setTimeout(fixPaletteEmptyAreaColorFinal, 100);
        setTimeout(fixPaletteEmptyAreaColorFinal, 500);
        setTimeout(fixPaletteEmptyAreaColorFinal, 1000);
    }}

    cleanEmojiText(document.body);
    }});
}})();
</script>

<script>
{solver_js}
</script>
</body>
</html>"""


def _load_solver_html(target_text: str = "", english: bool | None = None, theme_mode: str | None = None, glass_stat_items: list | None = None) -> str:
    english = _english_enabled(english)
    theme_mode = _theme_class(theme_mode)
    texts = _shard_texts(english)
    if not _SOLVER_HTML_PATH.exists():
        return f"""
        <div style="padding:24px;border-radius:16px;background:#fff3f3;color:#b91c1c;font-family:sans-serif;">
          <b>{texts["missing_html"]}</b><br>
          {texts["missing_path"]}
        </div>
        """

    base_html = _read_text(_SOLVER_HTML_PATH)
    priority_sets, target_counts = _parse_sugar_targets(target_text)
    return _inline_assets(base_html, priority_sets, target_counts, target_text, english=english, theme_mode=theme_mode, glass_stat_items=glass_stat_items)


def render_shard_placement_tab(target_text: str = "", english: bool | None = None, theme_mode: str | None = None, glass_shards: dict | None = None) -> None:
    """Render the trimmed shard placement page."""
    glass_stat_items: list[dict] = []
    if glass_shards:
        try:
            from cookie.stat_data import SHARD_KR
            for key, cells in glass_shards.items():
                if int(cells or 0) > 0:
                    glass_stat_items.append({"name": SHARD_KR.get(key, str(key)), "cells": int(cells)})
        except Exception:
            glass_stat_items = []
    components.html(
        _load_solver_html(target_text, english=english, theme_mode=theme_mode, glass_stat_items=glass_stat_items),
        height=865,
        scrolling=True,
    )
