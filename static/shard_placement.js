document.addEventListener('DOMContentLoaded', () => {
    const GRID_SIZE = 7;
    const gridContainer = document.getElementById('grid-container');
    const piecePalette = document.getElementById('piece-palette');
    const solveBtn = document.getElementById('solve-btn');
    const resetGridBtn = document.getElementById('reset-grid-btn');
    const fillAllBtn = document.getElementById('fill-all-btn');
    const clearPiecesBtn = document.getElementById('clear-pieces-btn');
    const solutionSummary = document.getElementById('solution-summary');
    const solutionsContainer = document.getElementById('solutions-container');

    let gridState = Array(GRID_SIZE * GRID_SIZE).fill(false);
    let lockedCells = new Set(); // Cells that cannot be toggled
    let piecesToUse = [];
    let isSolving = false;

    const MAX_SOLUTIONS = 10;
    const MAX_TIME_MS = 30000; // 30 seconds timeout
    const PRIORITIZE_HIGH_SCORE = true; // 높은 점수 조각부터 우선 배치 (false로 설정하면 정렬 없이 탐색)

    let isDragging = false;

    // 모바일에서 드롭다운 항목을 누른 직후 목록이 사라지면서 같은 터치의
    // 합성 click이 뒤쪽 카드로 전달되는 문제를 차단한다.
    const CS_TOUCH_GUARD_ID = 'cs-mobile-touch-guard';
    let csTouchGuardTimer = null;
    window.__csTouchBlockUntil = window.__csTouchBlockUntil || 0;

    function csStopGuardEvent(event) {
        if (!event) return;
        event.preventDefault();
        event.stopPropagation();
        if (event.stopImmediatePropagation) event.stopImmediatePropagation();
    }

    function csBlockTouchThrough(duration = 460) {
        const ms = Math.max(250, Number(duration) || 460);
        window.__csTouchBlockUntil = Math.max(window.__csTouchBlockUntil || 0, Date.now() + ms);

        let guard = document.getElementById(CS_TOUCH_GUARD_ID);
        if (!guard) {
            guard = document.createElement('div');
            guard.id = CS_TOUCH_GUARD_ID;
            guard.setAttribute('aria-hidden', 'true');
            guard.style.position = 'fixed';
            guard.style.inset = '0';
            guard.style.zIndex = '2147483647';
            guard.style.background = 'transparent';
            guard.style.pointerEvents = 'auto';
            guard.style.touchAction = 'none';
            guard.style.userSelect = 'none';
            guard.style.webkitUserSelect = 'none';
            ['pointerdown', 'pointerup', 'pointermove', 'touchstart', 'touchend', 'mousedown', 'mouseup', 'click'].forEach(type => {
                guard.addEventListener(type, csStopGuardEvent, { capture: true, passive: false });
            });
            document.body.appendChild(guard);
        }

        if (csTouchGuardTimer) clearTimeout(csTouchGuardTimer);
        csTouchGuardTimer = setTimeout(() => {
            const current = document.getElementById(CS_TOUCH_GUARD_ID);
            if (current && current.parentNode) current.parentNode.removeChild(current);
            csTouchGuardTimer = null;
        }, ms);
    }
    window.csBlockTouchThrough = csBlockTouchThrough;

    // pointerup 뒤에 브라우저가 만드는 click을 캡처 단계에서 한 번 더 차단한다.
    if (!window.__csTouchClickGuardBound) {
        window.__csTouchClickGuardBound = true;
        document.addEventListener('click', (event) => {
            if (Date.now() < (window.__csTouchBlockUntil || 0)) csStopGuardEvent(event);
        }, true);

        const armForDropdownItem = (event) => {
            const target = event && event.target && event.target.closest
                ? event.target.closest('.cs-modal-select-item, .cs-palette-dropdown-item, .cs-stat-edit-menu button')
                : null;
            if (target) csBlockTouchThrough(460);
        };
        document.addEventListener('pointerup', armForDropdownItem, true);
        document.addEventListener('touchend', armForDropdownItem, { capture: true, passive: true });
    }

    // 동적으로 생성되는 수정창 자체에서 발생한 이벤트가 뒤쪽 화면까지 버블링되지 않게 한다.
    function csIsolateModalTouches(modal) {
        if (!modal || modal.dataset.csTouchIsolated === 'true') return;
        modal.dataset.csTouchIsolated = 'true';
        modal.style.pointerEvents = 'auto';
        ['pointerdown', 'pointerup', 'touchstart', 'touchend', 'click'].forEach(type => {
            modal.addEventListener(type, (event) => event.stopPropagation(), { passive: type.startsWith('touch') });
        });
    }

    const csModalTouchObserver = new MutationObserver((mutations) => {
        mutations.forEach(mutation => {
            mutation.addedNodes.forEach(node => {
                if (!(node instanceof HTMLElement)) return;
                const candidates = [node, ...node.querySelectorAll('div[style*="position: fixed"]')];
                candidates.forEach(candidate => {
                    if (!(candidate instanceof HTMLElement)) return;
                    const z = Number.parseInt(candidate.style.zIndex || '0', 10) || 0;
                    if (candidate.style.position === 'fixed' && z >= 2000) csIsolateModalTouches(candidate);
                });
            });
        });
    });
    csModalTouchObserver.observe(document.body, { childList: true, subtree: true });

    // Streamlit components.html 내부의 모달은 기본적으로 iframe 영역만 기준으로 표시된다.
    // 전체 화면형 오버레이가 열리면 iframe 자체를 브라우저 화면 전체로 확장하고,
    // iframe의 일반 본문은 숨겨 부모 Streamlit 화면 위에 모달만 보이도록 한다.
    const CS_FULLSCREEN_MODAL_ATTR = 'data-cs-fullscreen-modal';
    const CS_FULLSCREEN_MODAL_BODY_CLASS = 'cs-fullscreen-modal-frame';
    const CS_FULLSCREEN_MODAL_STYLE_ID = 'cs-fullscreen-modal-frame-style';
    const CS_FULLSCREEN_MODAL_KNOWN_IDS = new Set(['usage-modal', 'debug-modal']);
    let csFullscreenFrameState = null;
    let csFullscreenSyncQueued = false;

    function csInstallFullscreenModalStyle() {
        if (document.getElementById(CS_FULLSCREEN_MODAL_STYLE_ID)) return;
        const style = document.createElement('style');
        style.id = CS_FULLSCREEN_MODAL_STYLE_ID;
        style.textContent = `
html.${CS_FULLSCREEN_MODAL_BODY_CLASS},
html.${CS_FULLSCREEN_MODAL_BODY_CLASS} body {
    width: 100% !important;
    height: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    background: transparent !important;
}
body.${CS_FULLSCREEN_MODAL_BODY_CLASS} > * {
    visibility: hidden !important;
}
body.${CS_FULLSCREEN_MODAL_BODY_CLASS} > [${CS_FULLSCREEN_MODAL_ATTR}="true"] {
    visibility: visible !important;
}
body.${CS_FULLSCREEN_MODAL_BODY_CLASS} > [${CS_FULLSCREEN_MODAL_ATTR}="true"],
body.${CS_FULLSCREEN_MODAL_BODY_CLASS} > [${CS_FULLSCREEN_MODAL_ATTR}="true"] * {
    pointer-events: auto;
}
`;
        document.head.appendChild(style);
    }

    function csIsFullscreenModalCandidate(element) {
        if (!(element instanceof HTMLElement) || element.id === CS_TOUCH_GUARD_ID) return false;
        if (CS_FULLSCREEN_MODAL_KNOWN_IDS.has(element.id)) return true;
        if (element.parentElement !== document.body) return false;

        const z = Number.parseInt(element.style.zIndex || '0', 10) || 0;
        if (element.style.position !== 'fixed' || z < 2000) return false;

        const insetZero = element.style.inset === '0' || element.style.inset === '0px';
        const fullByEdges = (element.style.left === '0' || element.style.left === '0px') &&
            (element.style.top === '0' || element.style.top === '0px') &&
            (element.style.width === '100%' || element.style.width === '100vw') &&
            (element.style.height === '100%' || element.style.height === '100vh' || element.style.height === '100dvh');
        return insetZero || fullByEdges;
    }

    function csIsVisibleFullscreenModal(element) {
        if (!csIsFullscreenModalCandidate(element) || !element.isConnected) return false;
        const computed = window.getComputedStyle(element);
        return computed.display !== 'none' && computed.visibility !== 'hidden' && computed.opacity !== '0';
    }

    function csCollectFullscreenModals() {
        const candidates = Array.from(document.body.children).filter(csIsFullscreenModalCandidate);
        for (const element of candidates) {
            element.setAttribute(CS_FULLSCREEN_MODAL_ATTR, 'true');
        }
        return candidates.filter(csIsVisibleFullscreenModal);
    }

    function csExpandIframeForModal() {
        if (csFullscreenFrameState) return true;
        try {
            if (window.parent === window || !window.frameElement) return false;
            const parentDocument = window.parent.document;
            const parentWindow = window.parent;
            const frame = window.frameElement;
            if (!parentDocument.body || !parentDocument.documentElement) return false;

            csFullscreenFrameState = {
                frame,
                frameStyle: frame.getAttribute('style'),
                frameWidth: frame.getAttribute('width'),
                frameHeight: frame.getAttribute('height'),
                parentBodyOverflow: parentDocument.body.style.overflow,
                parentHtmlOverflow: parentDocument.documentElement.style.overflow,
                parentScrollX: parentWindow.scrollX,
                parentScrollY: parentWindow.scrollY,
            };

            frame.style.setProperty('position', 'fixed', 'important');
            frame.style.setProperty('inset', '0', 'important');
            frame.style.setProperty('left', '0', 'important');
            frame.style.setProperty('top', '0', 'important');
            frame.style.setProperty('width', '100vw', 'important');
            frame.style.setProperty('height', '100dvh', 'important');
            frame.style.setProperty('max-width', 'none', 'important');
            frame.style.setProperty('max-height', 'none', 'important');
            frame.style.setProperty('margin', '0', 'important');
            frame.style.setProperty('padding', '0', 'important');
            frame.style.setProperty('border', '0', 'important');
            frame.style.setProperty('background', 'transparent', 'important');
            frame.style.setProperty('z-index', '2147483646', 'important');
            frame.style.setProperty('display', 'block', 'important');
            frame.setAttribute('width', '100%');
            frame.setAttribute('height', '100%');
            frame.setAttribute('allowtransparency', 'true');

            parentDocument.documentElement.style.overflow = 'hidden';
            parentDocument.body.style.overflow = 'hidden';
            document.documentElement.classList.add(CS_FULLSCREEN_MODAL_BODY_CLASS);
            document.body.classList.add(CS_FULLSCREEN_MODAL_BODY_CLASS);
            return true;
        } catch (_) {
            csFullscreenFrameState = null;
            return false;
        }
    }

    function csRestoreIframeAfterModal() {
        const state = csFullscreenFrameState;
        document.documentElement.classList.remove(CS_FULLSCREEN_MODAL_BODY_CLASS);
        document.body.classList.remove(CS_FULLSCREEN_MODAL_BODY_CLASS);
        if (!state) return;
        csFullscreenFrameState = null;

        try {
            if (state.frameStyle === null) state.frame.removeAttribute('style');
            else state.frame.setAttribute('style', state.frameStyle);

            if (state.frameWidth === null) state.frame.removeAttribute('width');
            else state.frame.setAttribute('width', state.frameWidth);
            if (state.frameHeight === null) state.frame.removeAttribute('height');
            else state.frame.setAttribute('height', state.frameHeight);

            const parentDocument = window.parent.document;
            parentDocument.body.style.overflow = state.parentBodyOverflow;
            parentDocument.documentElement.style.overflow = state.parentHtmlOverflow;
            window.parent.scrollTo(state.parentScrollX, state.parentScrollY);
        } catch (_) {}
    }

    function csSyncFullscreenModalFrame() {
        csFullscreenSyncQueued = false;
        const visibleModals = csCollectFullscreenModals();
        if (visibleModals.length > 0) {
            csExpandIframeForModal();
        } else {
            csRestoreIframeAfterModal();
        }
    }

    function csQueueFullscreenModalSync() {
        if (csFullscreenSyncQueued) return;
        csFullscreenSyncQueued = true;
        requestAnimationFrame(csSyncFullscreenModalFrame);
    }

    csInstallFullscreenModalStyle();
    const csFullscreenModalObserver = new MutationObserver(csQueueFullscreenModalSync);
    csFullscreenModalObserver.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['style', 'class', 'hidden'],
    });
    window.addEventListener('resize', csQueueFullscreenModalSync);
    window.addEventListener('beforeunload', csRestoreIframeAfterModal);
    window.csSyncFullscreenModalFrame = csSyncFullscreenModalFrame;
    csQueueFullscreenModalSync();

    // Define locked area: center horizontal rectangle, 5 wide x 3 tall
    function initializeLockedArea() {
        const startRow = 2; // Center vertically: (7-3)/2 = 2
        const startCol = 1; // Center horizontally: (7-5)/2 = 1
        const rows = 3; // Height
        const cols = 5; // Width

        for (let r = startRow; r < startRow + rows && r < GRID_SIZE; r++) {
            for (let c = startCol; c < startCol + cols && c < GRID_SIZE; c++) {
                const index = r * GRID_SIZE + c;
                lockedCells.add(index);
                // Set locked cells as fillable by default
                gridState[index] = true;
            }
        }
    }

    initializeLockedArea();

    // --- 1. Grid Logic ---
    function createGrid() {
        gridContainer.innerHTML = '';

        // Add mouseup listener to the whole window to stop dragging
        window.addEventListener('mouseup', () => {
            isDragging = false;
        });

        for (let i = 0; i < GRID_SIZE * GRID_SIZE; i++) {
            const cell = document.createElement('div');
            cell.classList.add('grid-cell');
            cell.dataset.index = i;

            // Check if cell is locked
            if (lockedCells.has(i)) {
                cell.classList.add('locked');
                cell.classList.add('unlocked'); // Locked cells are also fillable
                cell.title = '잠긴 영역 (편집 불가, 조각 배치 가능)';
            } else {
                if (gridState[i]) cell.classList.add('unlocked');

                cell.addEventListener('mousedown', () => {
                    isDragging = true;
                    toggleCell(i);
                });

                cell.addEventListener('mouseover', () => {
                    if (isDragging) {
                        toggleCell(i);
                    }
                });
            }

            gridContainer.appendChild(cell);
        }
    }

    function toggleCell(index) {
        if (isSolving) return;
        if (lockedCells.has(index)) return; // Cannot toggle locked cells

        gridState[index] = !gridState[index];
        gridContainer.querySelector(`[data-index='${index}']`).classList.toggle('unlocked');
    }

    resetGridBtn.addEventListener('click', () => {
        if (isSolving) return;
        gridState.fill(false);
        // Re-initialize locked area as fillable
        lockedCells.forEach(index => {
            gridState[index] = true;
        });
        createGrid();
    });

    fillAllBtn.addEventListener('click', () => {
        if (isSolving) return;
        // Set all cells to unlocked (fillable)
        gridState.fill(true);
        createGrid();
        solutionSummary.textContent = ' 맵 전체가 열렸습니다!';
        solutionsContainer.innerHTML = '';
    });

    // --- 2. Piece Generation Logic ---

    // --- Piece Manipulation Helpers ---
    function normalizeShape(shape) {
        if (shape.length === 0) return [];
        const minR = Math.min(...shape.map(p => p[0]));
        const minC = Math.min(...shape.map(p => p[1]));
        return shape.map(([r, c]) => [r - minR, c - minC]).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    }

    function rotateShape(shape) {
        const rotated = shape.map(([r, c]) => [c, -r]);
        return normalizeShape(rotated);
    }

    function flipShape(shape) {
        const flipped = shape.map(([r, c]) => [r, -c]);
        return normalizeShape(flipped);
    }

    function shapeToString(shape) {
        // 정규화된 shape를 안정적인 문자열로 변환
        const normalized = normalizeShape(shape);
        // 좌표를 정렬한 후 문자열로 변환
        const sorted = [...normalized].sort((a, b) => {
            if (a[0] !== b[0]) return a[0] - b[0];
            return a[1] - b[1];
        });
        return sorted.map(([r, c]) => `${r},${c}`).join('|');
    }

    function stringToShape(str) {
        return str.split('|').map(coord => {
            const [r, c] = coord.split(',').map(Number);
            return [r, c];
        });
    }

    function generateOrientations(baseShape) {
        const orientations = new Set();
        let currentShape = normalizeShape(baseShape);

        for (let i = 0; i < 4; i++) { // 4 rotations
            orientations.add(shapeToString(currentShape));
            orientations.add(shapeToString(flipShape(currentShape)));
            currentShape = rotateShape(currentShape);
        }
        return Array.from(orientations).map(s => stringToShape(s));
    }

    // Score calculation by grade
    // 등급별 점수: 레어=칸당 30점, 에픽=칸당 60점, 슈퍼에픽=칸당 120점
    const GRADE_SCORES = {
        'rare': 30,      // 레어
        'epic': 60,      // 에픽
        'super': 120     // 슈퍼에픽
    };

    function calculateScore(cellCount, grade = 'rare') {
        return cellCount * GRADE_SCORES[grade];
    }

    // --- Set Definitions ---
    // 테마별 세트 색상: 라이트 = 채도 높게(흰 배경에서 또렷), 다크 = 채도 낮게(어두운 배경에서 부드럽게)
    const CS_DARK_UI = (() => {
        try {
            const b = document.body;
            if (b && b.classList.contains('cs-theme-dark')) return true;
            if (b && b.classList.contains('cs-theme-system')) {
                return !!(window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
            }
        } catch (e) {}
        return false;
    })();
    // 역할별 색상 조합: 딜러(광휘=파스텔블루/관통=보라), 스트라이커(파쇄=파스텔마젠타/원소=로즈핑크),
    // 서포터(축복/낙인/재생)=청록→초록→라임, 유니크=골드
    // 라이트: 파스텔톤만 조금 진하게, 진한색은 베이스 유지
    const SET_COLORS_LIGHT = {
        'dealer-radiance': '#9DD9EF',
        'dealer-penetration': '#B7A8F3',
        'striker-element': '#EFB4CA',
        'striker-fracture': '#D3A9F1',
        'supporter-blessing': '#86D8D1',
        'supporter-brand': '#A6DE8F',
        'supporter-regeneration': '#B8C9F3'
    };

    const SET_COLORS_DARK = {
        'dealer-radiance': '#7FC5DF',
        'dealer-penetration': '#AA98E8',
        'striker-element': '#DE9CB8',
        'striker-fracture': '#C398E3',
        'supporter-blessing': '#70C9C1',
        'supporter-brand': '#90CF7A',
        'supporter-regeneration': '#9FB3E2'
    };


    const CS_SET_COLORS = CS_DARK_UI ? SET_COLORS_DARK : SET_COLORS_LIGHT;
    // 유니크(설탕유리조각): 라이트 = 골드 원본, 다크 = 부드러운 골드
    const CS_UNIQUE_COLOR = CS_DARK_UI ? '#E8D06A' : '#F2D65C';
    const SET_INFO = {
        'dealer-radiance': { name: ((typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en') ? 'Brilliant' : '광휘'), color: CS_SET_COLORS['dealer-radiance'], icon: '' },
        'dealer-penetration': { name: ((typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en') ? 'Piercing' : '관통'), color: CS_SET_COLORS['dealer-penetration'], icon: '' },
        'striker-element': { name: ((typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en') ? 'Elemental' : '원소'), color: CS_SET_COLORS['striker-element'], icon: '' },
        'striker-fracture': { name: ((typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en') ? 'Tearing' : '파쇄'), color: CS_SET_COLORS['striker-fracture'], icon: '' },
        'supporter-blessing': { name: ((typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en') ? 'Blessed' : '축복'), color: CS_SET_COLORS['supporter-blessing'], icon: '' },
        'supporter-brand': { name: ((typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en') ? 'Branded' : '낙인'), color: CS_SET_COLORS['supporter-brand'], icon: '' },
        'supporter-regeneration': { name: ((typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en') ? 'Restoring' : '재생'), color: CS_SET_COLORS['supporter-regeneration'], icon: '' }
    };

    // 세트 효과 저항 증가량: 9/12/15/18/21칸 단계마다 265 저항
    const SET_BONUS_RESISTANCE = 265;
    const SET_BONUS_THRESHOLDS = [9, 12, 15, 18, 21];
    // 목표 세트(예: 축복 20칸 / 낙인 21칸) — cookie-sim이 window로 주입, 없으면 빈 객체
    const CS_TARGET_COUNTS = (typeof window !== 'undefined' && window.COOKIE_SIM_SHARD_TARGET_COUNTS) || {};
    const CS_TARGET_KEYS = Object.keys(CS_TARGET_COUNTS).filter(k => Number(CS_TARGET_COUNTS[k]) > 0);
    function csCountTargetsMet(setCellCounts) {
        let met = 0;
        CS_TARGET_KEYS.forEach(k => {
            if ((setCellCounts[k] || 0) >= Number(CS_TARGET_COUNTS[k])) met++;
        });
        return met;
    }

    // Calculate set bonus resistance based on cell counts
    function calculateSetBonus(setCellCounts) {
        let totalBonus = 0;
        const setBonusDetails = {};

        Object.entries(setCellCounts).forEach(([setKey, cellCount]) => {
            let bonus = 0;
            let reachedThresholds = [];

            for (const threshold of SET_BONUS_THRESHOLDS) {
                if (cellCount >= threshold) {
                    bonus += SET_BONUS_RESISTANCE;
                    reachedThresholds.push(threshold);
                }
            }

            if (bonus > 0) {
                setBonusDetails[setKey] = {
                    cellCount: cellCount,
                    bonus: bonus,
                    thresholds: reachedThresholds
                };
                totalBonus += bonus;
            }
        });

        return { totalBonus, setBonusDetails };
    }

    // --- Base Piece Definitions ---
    // 5칸 이하 조각 템플릿
    // 기본 조각 템플릿 (회전/반전 전)
    const BASE_TEMPLATES = {
        '1x1': { shape: [[0,0]] },
        '1x2': { shape: [[0,0], [0,1]] },
        '1x3': { shape: [[0,0], [0,1], [0,2]] },
        '1x4': { shape: [[0,0], [0,1], [0,2], [0,3]] },
        '2x2': { shape: [[0,0], [0,1], [1,0], [1,1]] },
        'L3': { shape: [[0,0], [1,0], [1,1]] },
        'L4': { shape: [[0,0], [1,0], [2,0], [2,1]] },
        'T4': { shape: [[0,1], [1,0], [1,1], [1,2]] },
        'Plus5': { shape: [[0,1], [1,0], [1,1], [1,2], [2,1]] },
        'T5': { shape: [[0,0], [0,1], [0,2], [1,1], [2,1]] },
        'P5_alt': { shape: [[0,1], [0,2], [1,1], [2,0], [2,1]] },
        'L5': { shape: [[0,0], [0,1], [0,2], [1,2], [2,2]] },
        'U5': { shape: [[0,0], [0,2], [1,0], [1,1], [1,2]] }
    };

    // 8칸 유니크 조각 템플릿
    const UNIQUE_BASE_TEMPLATES = {
        '2x4': { shape: [[0,0], [0,1], [0,2], [0,3], [1,0], [1,1], [1,2], [1,3]] },
        'Complex9_1': { shape: [[0,0], [1,0], [1,1], [2,0], [2,1], [3,0], [3,1], [4,1]] },
        'Complex8_1': { shape: [[0,1], [0,2], [1,1], [1,2], [2,0], [2,1], [2,2], [2,3]] },
        'Complex8_2': { shape: [[0,1], [1,0], [1,1], [1,2], [2,0], [2,1], [2,2], [3,1]] }
    };

    // 모든 방향을 별도의 조각으로 확장
    const COMMON_PIECE_TEMPLATES = {};
    Object.entries(BASE_TEMPLATES).forEach(([baseName, baseData]) => {
        const orientations = generateOrientations(baseData.shape);
        orientations.forEach((orientationShape, index) => {
            const fullName = orientations.length > 1 ? `${baseName}-${index}` : baseName;
            COMMON_PIECE_TEMPLATES[fullName] = { shape: orientationShape };
        });
    });

    // 유니크 조각도 동일하게 확장
    const UNIQUE_PIECE_TEMPLATES = {};
    // 사용자가 제거 요청한 일부 방향만 숨김. 템플릿 전체를 삭제하지 않도록 shape signature 기준으로 필터링.
    const COOKIE_SIM_HIDDEN_UNIQUE_SIGNATURES = new Set([
        '0,1;1,0;1,1;2,0;2,1;3,0;3,1;4,0',
        '0,0;0,1;0,2;0,3;1,1;1,2;1,3;1,4',
        '0,0;1,0;1,1;1,2;2,0;2,1;2,2;3,0',
        '0,2;1,0;1,1;1,2;2,0;2,1;2,2;3,2'
    ]);
    function cookieSimShapeSignature(shape) {
        const minR = Math.min(...shape.map(p => p[0]));
        const minC = Math.min(...shape.map(p => p[1]));
        return shape
            .map(p => [p[0] - minR, p[1] - minC])
            .sort((a, b) => (a[0] - b[0]) || (a[1] - b[1]))
            .map(p => `${p[0]},${p[1]}`)
            .join(';');
    }
    Object.entries(UNIQUE_BASE_TEMPLATES).forEach(([baseName, baseData]) => {
        const orientations = generateOrientations(baseData.shape);
        orientations.forEach((orientationShape, index) => {
            if (COOKIE_SIM_HIDDEN_UNIQUE_SIGNATURES.has(cookieSimShapeSignature(orientationShape))) return;
            const fullName = orientations.length > 1 ? `${baseName}-${index}` : baseName;
            UNIQUE_PIECE_TEMPLATES[fullName] = { shape: orientationShape };
        });
    });

    // Build BASE_PIECES
    const BASE_PIECES = {};

    Object.keys(SET_INFO).forEach(setKey => {
        const setColor = SET_INFO[setKey].color;

        // 각 세트에 5칸 이하 조각들 추가
        Object.entries(COMMON_PIECE_TEMPLATES).forEach(([pieceName, pieceData]) => {
            const fullName = `${setKey}-${pieceName}`;
            BASE_PIECES[fullName] = {
                shape: pieceData.shape,
                color: setColor,
                set: setKey
            };
        });

        // 각 세트에 8칸 유니크 조각들 추가
        Object.entries(UNIQUE_PIECE_TEMPLATES).forEach(([pieceName, pieceData]) => {
            const fullName = `${setKey}-${pieceName}`;
            BASE_PIECES[fullName] = {
                shape: pieceData.shape,
                color: setColor,
                set: setKey,
                isUnique: true // 유니크 조각 표시
            };
        });
    });

    // --- Final PIECES object, generated from BASE_PIECES ---
    // 템플릿이 이미 모든 orientation을 포함하므로 그대로 사용
    const PIECES = {};
    let csRecognizedResults = [];
    let csRecognizedFilter = 'all';
    Object.entries(BASE_PIECES).forEach(([pieceName, piece]) => {
        const cellCount = piece.shape.length;

        PIECES[pieceName] = {
            shape: piece.shape,
            color: piece.color,
            cellCount: cellCount,
            set: piece.set || null,
            isUnique: piece.isUnique || false
        };
    });

    // 조각 생성 완료
    console.log(`조각 생성 완료: ${Object.keys(PIECES).length}개`);

    // Helper function to create grade input
    function createGradeInput(pieceName, grade, gradeConfig) {
        const col = document.createElement('div');
        col.style.display = 'flex';
        col.style.flexDirection = 'column';
        col.style.gap = '6px';
        col.style.flex = '1';

        const label = document.createElement('div');
        label.textContent = gradeConfig.label;
        label.style.fontSize = '0.9em';
        label.style.fontWeight = '600';
        label.style.color = gradeConfig.color;
        label.style.backgroundColor = gradeConfig.bgColor;
        label.style.padding = '8px';
        label.style.borderRadius = '6px';
        label.style.textAlign = 'center';
        label.style.border = `2px solid ${gradeConfig.borderColor}`;

        const input = document.createElement('input');
        input.type = 'number';
        input.value = '0';
        input.min = '0';
        input.max = '10';
        input.id = `piece-count-${pieceName}-${grade}`;
        input.classList.add('piece-count-input');
        input.style.width = '100%';
        input.style.padding = '8px';
        input.style.fontSize = '1em';
        input.style.textAlign = 'center';
        input.style.border = `2px solid ${gradeConfig.borderColor}`;
        input.style.borderRadius = '6px';
        input.style.fontWeight = 'bold';

        col.appendChild(label);
        col.appendChild(input);
        return col;
    }

    // Helper function to create piece preview
    function createPiecePreview(piece) {
        const previewContainer = document.createElement('div');
        previewContainer.classList.add('piece-preview');

        const previewGrid = document.createElement('div');
        const shape = piece.shape;
        const maxRows = Math.max(...shape.map(p => p[0])) + 1;
        const maxCols = Math.max(...shape.map(p => p[1])) + 1;

        previewGrid.style.display = 'grid';
        previewGrid.style.gridTemplateColumns = `repeat(${maxCols}, 20px)`;
        previewGrid.style.gridTemplateRows = `repeat(${maxRows}, 20px)`;
        previewGrid.style.gap = '2px';

        for (let r = 0; r < maxRows; r++) {
            for (let c = 0; c < maxCols; c++) {
                const cell = document.createElement('div');
                cell.classList.add('preview-cell');
                cell.style.width = '20px';
                cell.style.height = '20px';
                cell.style.border = '1px solid #ddd';
                cell.style.borderRadius = '3px';
                if (shape.some(p => p[0] === r && p[1] === c)) {
                    cell.style.backgroundColor = piece.color;
                    cell.style.border = '1px solid transparent';
                    cell.classList.add('preview-cell-filled');
                } else {
                    cell.style.backgroundColor = 'transparent';
                }
                previewGrid.appendChild(cell);
            }
        }

        previewContainer.appendChild(previewGrid);
        return previewContainer;
    }


    function csPreviewSurfaceBg() {
        return CS_DARK_UI ? '#303236' : '#fff';
    }

    function csSelectFieldBg() {
        return CS_DARK_UI ? '#303236' : '#dfe3e8';
    }

    function csSelectFieldText() {
        return CS_DARK_UI ? '#f3f4f6' : '#111827';
    }

    function csSelectArrowColor() {
        return CS_DARK_UI ? '#94a3b8' : '#6b7280';
    }

    function openCookieSimPiecePicker(defaultPieceName, onPick, pieceFilter = 'all') {
        const modal = document.createElement('div');
        modal.style.position = 'fixed';
        modal.style.zIndex = '3000';
        modal.style.left = '0';
        modal.style.top = '0';
        modal.style.width = '100%';
        modal.style.height = '100%';
        modal.style.background = 'rgba(0,0,0,0.72)';
        modal.style.display = 'flex';
        modal.style.alignItems = 'center';
        modal.style.justifyContent = 'center';

        const modalContent = document.createElement('div');
        modalContent.style.background = '#fff';
        modalContent.style.borderRadius = '12px';
        modalContent.style.padding = '16px';
        modalContent.style.width = '92%';
        modalContent.style.maxWidth = '920px';
        modalContent.style.maxHeight = '82vh';
        modalContent.style.overflowY = 'auto';
        modalContent.style.boxShadow = '0 12px 32px rgba(0,0,0,0.22)';

        const modalTitle = document.createElement('h3');
        modalTitle.textContent = '조각 선택';
        modalTitle.style.margin = '0 0 10px 0';
        modalTitle.style.color = '#374151';
        modalTitle.style.fontSize = '12px';
        modalTitle.style.fontWeight = '800';
        modalContent.appendChild(modalTitle);

        const piecesGrid = document.createElement('div');
        piecesGrid.style.display = 'grid';
        piecesGrid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(122px, 1fr))';
        piecesGrid.style.gap = '10px';
        piecesGrid.style.maxHeight = '62vh';
        piecesGrid.style.overflowY = 'auto';

        const allPieces = Object.keys({ ...COMMON_PIECE_TEMPLATES, ...UNIQUE_PIECE_TEMPLATES }).filter(pName => {
            const isUniquePiece = !!UNIQUE_PIECE_TEMPLATES[pName];
            if (pieceFilter === 'unique') return isUniquePiece;
            if (pieceFilter === 'regular') return !isUniquePiece;
            return true;
        });
        allPieces.forEach(pName => {
            const templateData = COMMON_PIECE_TEMPLATES[pName] || UNIQUE_PIECE_TEMPLATES[pName];
            if (!templateData) return;
            const pieceCard = document.createElement('div');
            pieceCard.style.padding = '4px';
            pieceCard.style.border = CS_DARK_UI ? '0' : '1px solid #e5e7eb';
            pieceCard.style.borderRadius = '8px';
            pieceCard.style.cursor = 'pointer';
            pieceCard.style.display = 'flex';
            pieceCard.style.alignItems = 'center';
            pieceCard.style.justifyContent = 'center';
            pieceCard.style.background = CS_DARK_UI ? '#303236' : '#fff';
            pieceCard.style.height = '118px';
            pieceCard.style.boxSizing = 'border-box';
            pieceCard.style.transition = 'all 0.15s ease';
            const preview = createPiecePreview({ shape: templateData.shape, color: '#999999' });
            pieceCard.appendChild(preview);
            pieceCard.classList.add('cs-picker-card');
            if (pName === defaultPieceName) pieceCard.dataset.csSelected = 'true';
            pieceCard.addEventListener('click', () => {
                if (typeof onPick === 'function') onPick(pName);
                document.body.removeChild(modal);
            });
            piecesGrid.appendChild(pieceCard);
        });

        modalContent.appendChild(piecesGrid);
        const closeBtn = document.createElement('button');
        closeBtn.textContent = '닫기';
        closeBtn.style.marginTop = '10px';
        closeBtn.style.padding = '8px 14px';
        closeBtn.style.border = '0';
        closeBtn.style.borderRadius = '8px';
        closeBtn.style.background = '#e5e7eb';
        closeBtn.style.cursor = 'pointer';
        closeBtn.style.fontWeight = '800';
        closeBtn.style.fontSize = '12px';
        closeBtn.addEventListener('click', () => document.body.removeChild(modal));
        modalContent.appendChild(closeBtn);
        modal.appendChild(modalContent);
        modal.addEventListener('click', (e) => { if (e.target === modal) document.body.removeChild(modal); });
        document.body.appendChild(modal);
    }

    function createPiecePalette() {
        piecePalette.innerHTML = '';

        const gradeConfigs = {
            rare: { label: ' 레어', color: '#1e7e34', bgColor: '#d4edda', borderColor: '#c3e6cb' },
            epic: { label: ' 에픽', color: '#4527a0', bgColor: '#e1bee7', borderColor: '#ce93d8' },
            super: { label: '⭐ 슈퍼', color: '#e65100', bgColor: '#ffe0b2', borderColor: '#ffcc80' }
        };

        // Get pieces-section parent
        const piecesSection = piecePalette.parentElement;

        // Create tab buttons container
        const tabButtons = document.createElement('div');
        tabButtons.style.display = 'flex';
        tabButtons.style.gap = '5px';
        tabButtons.style.flexWrap = 'wrap';
        tabButtons.style.marginBottom = '15px';
        tabButtons.style.position = 'sticky';
        tabButtons.style.top = '0';
        tabButtons.style.backgroundColor = 'white';
        tabButtons.style.zIndex = '100';
        tabButtons.style.paddingTop = '4px';
        tabButtons.style.paddingBottom = '6px';

        // Create tab content container
        const tabContents = document.createElement('div');

        // Define tabs: 7개 세트 탭 + 1개 유니크 탭
        const tabs = [];

        // 7개 세트 탭 추가 (5칸 이하 조각)
        Object.entries(SET_INFO).forEach(([setKey, setData]) => {
            tabs.push({
                id: setKey,
                name: `${setData.icon} ${setData.name}`,
                description: `${setData.name} 세트 5칸 이하 조각`
            });
        });

        // 유니크 탭 추가 (8칸 조각)
        tabs.push({
            id: 'unique',
            name: ((typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en') ? 'Unique' : '유니크'),
            description: ((typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en') ? '8-cell unique shards from all sets' : '모든 세트의 8칸 유니크 조각')
        });

        let activeTabId = tabs[0].id; // 첫 번째 세트 탭을 기본 활성 탭으로

        // Create tabs
        tabs.forEach((tab, index) => {
            // Tab button
            const tabBtn = document.createElement('button');
            tabBtn.textContent = tab.name;
            tabBtn.className = 'tab-btn';
            tabBtn.dataset.tabId = tab.id;
            tabBtn.style.padding = '12px 20px';
            tabBtn.style.border = 'none';
            tabBtn.style.borderRadius = '8px 8px 0 0';
            tabBtn.style.cursor = 'pointer';
            tabBtn.style.fontWeight = 'bold';
            tabBtn.style.fontSize = '1em';
            tabBtn.style.transition = 'all 0.3s';

            if (index === 0) {
                tabBtn.style.background = 'linear-gradient(135deg, #667eea, #764ba2)';
                tabBtn.style.color = 'white';
            } else {
                tabBtn.style.background = '#e5e7eb';
                tabBtn.style.color = '#666';
            }

            tabBtn.addEventListener('click', () => {
                activeTabId = tab.id;
                // Update button styles
                tabButtons.querySelectorAll('.tab-btn').forEach(btn => {
                    if (btn.dataset.tabId === activeTabId) {
                        btn.style.background = 'linear-gradient(135deg, #667eea, #764ba2)';
                        btn.style.color = 'white';
                    } else {
                        btn.style.background = '#e5e7eb';
                        btn.style.color = '#666';
                    }
                });
                // Update content visibility
                tabContents.querySelectorAll('.tab-content').forEach(content => {
                    content.style.display = content.dataset.tabId === activeTabId ? 'block' : 'none';
                });
            });

            tabButtons.appendChild(tabBtn);

            // Tab content
            const tabContent = document.createElement('div');
            tabContent.className = 'tab-content';
            tabContent.dataset.tabId = tab.id;
            tabContent.style.display = index === 0 ? 'block' : 'none';
            tabContent.style.padding = '20px';
            tabContent.style.background = 'rgba(255, 255, 255, 0.9)';
            tabContent.style.borderRadius = '0 8px 8px 8px';
            tabContent.style.border = '2px solid #667eea';

            // Tab description
            const tabDesc = document.createElement('div');
            tabDesc.textContent = ` ${tab.description}`;
            tabDesc.style.marginBottom = '15px';
            tabDesc.style.padding = '10px';
            tabDesc.style.background = 'rgba(102, 126, 234, 0.1)';
            tabDesc.style.borderRadius = '6px';
            tabDesc.style.fontWeight = '600';
            tabContent.appendChild(tabDesc);

            // Piece grid
            const pieceGrid = document.createElement('div');
            pieceGrid.classList.add('piece-grid');
            pieceGrid.style.display = 'grid';
            pieceGrid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(280px, 1fr))';
            pieceGrid.style.gap = '15px';

            // Get pieces for this tab
            let piecesForTab = [];
            if (tab.id === 'unique') {
                // 유니크 탭: 첫 번째 세트의 8칸 조각들만 표시
                const firstSetKey = Object.keys(SET_INFO)[0]; // 첫 번째 세트
                Object.entries(PIECES).forEach(([name, piece]) => {
                    if (piece.isUnique && piece.set === firstSetKey) {
                        piecesForTab.push([name, piece]);
                    }
                });
            } else {
                // 세트 탭: 해당 세트의 5칸 이하 조각들
                Object.entries(PIECES).forEach(([name, piece]) => {
                    if (piece.set === tab.id && !piece.isUnique) {
                        piecesForTab.push([name, piece]);
                    }
                });
            }

            // Create piece items
            piecesForTab.forEach(([name, piece]) => {
                const pieceEl = document.createElement('div');
                pieceEl.classList.add('piece-item');
                pieceEl.style.padding = '12px';
                pieceEl.style.background = 'white';
                pieceEl.style.borderRadius = '8px';
                pieceEl.style.border = '2px solid #ddd';
                pieceEl.style.transition = 'all 0.3s';
                pieceEl.addEventListener('mouseenter', () => {
                    pieceEl.style.borderColor = '#667eea';
                    pieceEl.style.boxShadow = '0 4px 8px rgba(102, 126, 234, 0.3)';
                });
                pieceEl.addEventListener('mouseleave', () => {
                    pieceEl.style.borderColor = '#ddd';
                    pieceEl.style.boxShadow = 'none';
                });

                // Preview - 유니크 탭일 경우 골드 색상 사용
                const displayPiece = tab.id === 'unique' ? { ...piece, color: CS_UNIQUE_COLOR } : piece;
                const preview = createPiecePreview(displayPiece);
                pieceEl.appendChild(preview);

                // Grades container
                const gradesContainer = document.createElement('div');
                gradesContainer.style.display = 'flex';
                gradesContainer.style.gap = '10px';
                gradesContainer.style.marginTop = '10px';

                if (tab.id === 'unique') {
                    // 유니크 조각: 화면에는 입력 UI를 숨기고, 내부 계산용 입력만 유지
                    const uniqueInput = document.createElement('input');
                    uniqueInput.type = 'number';
                    uniqueInput.value = '0';
                    uniqueInput.min = '0';
                    uniqueInput.max = '10';
                    uniqueInput.id = `piece-count-${name}-unique`;
                    uniqueInput.classList.add('piece-count-input');
                    uniqueInput.style.display = 'none';
                    pieceEl.appendChild(uniqueInput);
                } else {
                    gradesContainer.appendChild(createGradeInput(name, 'rare', gradeConfigs.rare));
                    gradesContainer.appendChild(createGradeInput(name, 'epic', gradeConfigs.epic));
                    gradesContainer.appendChild(createGradeInput(name, 'super', gradeConfigs.super));
                }

                if (tab.id !== 'unique') {
                    pieceEl.appendChild(gradesContainer);
                }
                pieceGrid.appendChild(pieceEl);
            });

            tabContent.appendChild(pieceGrid);
            tabContents.appendChild(tabContent);
        });

        // Insert tab buttons before piece-palette
        piecesSection.insertBefore(tabButtons, piecePalette);

        // Add tab contents to piece-palette
        piecePalette.appendChild(tabContents);
    }


    // --- 3. Clear Pieces ---
    function resetPieceInputsOnly() {
        Object.keys(PIECES).forEach(name => {
            const piece = PIECES[name];
            if (piece.isUnique) {
                const uniqueInput = document.getElementById(`piece-count-${name}-unique`);
                if (uniqueInput) uniqueInput.value = '0';
            } else {
                ['rare', 'epic', 'super'].forEach(grade => {
                    const countInput = document.getElementById(`piece-count-${name}-${grade}`);
                    if (countInput) countInput.value = '0';
                });
            }
        });
    }

    function clearPieces() {
        resetPieceInputsOnly();
        csRecognizedResults = [];
        solutionSummary.textContent = '';
        solutionsContainer.innerHTML = '';
        renderRecognizedPieceCards(csRecognizedResults);
    }

    clearPiecesBtn.addEventListener('click', clearPieces);

    // --- 4. Random Fill Pieces ---
    function randomFillPieces() {
        Object.keys(PIECES).forEach(name => {
            const piece = PIECES[name];
            if (piece.isUnique) {
                // 유니크 조각: 0~1 랜덤
                const uniqueInput = document.getElementById(`piece-count-${name}-unique`);
                if (uniqueInput) {
                    const randomValue = Math.floor(Math.random() * 2); // 0~1
                    uniqueInput.value = randomValue.toString();
                }
            } else {
                // 일반 조각: 등급별 랜덤 범위
                const grades = ['rare', 'epic', 'super'];
                grades.forEach(grade => {
                    const countInput = document.getElementById(`piece-count-${name}-${grade}`);
                    if (countInput) {
                        // 등급별 랜덤 범위: 레어 0~3, 에픽 0~2, 슈퍼에픽 0~1
                        let maxValue;
                        if (grade === 'rare') {
                            maxValue = 4; // 0~3
                        } else if (grade === 'epic') {
                            maxValue = 3; // 0~2
                        } else { // super
                            maxValue = 2; // 0~1
                        }
                        const randomValue = Math.floor(Math.random() * maxValue);
                        countInput.value = randomValue.toString();
                    }
                });
            }
        });
        solutionSummary.textContent = '';
        solutionsContainer.innerHTML = '';
    }

    const randomFillBtn = document.getElementById('random-fill-btn');
    randomFillBtn.addEventListener('click', randomFillPieces);

    // --- Image Upload & OCR ---
    const uploadBtn = document.getElementById('upload-btn');
    const imageUpload = document.getElementById('image-upload');
    const uploadStatus = document.getElementById('upload-status');

    // Disable upload button until OpenCV is ready
    uploadBtn.style.pointerEvents = 'none';
    uploadBtn.style.cursor = 'not-allowed';
    uploadBtn.style.opacity = '0.5';
    uploadStatus.textContent = '이미지 로딩 중...';

    function onCvReady() {
        uploadStatus.textContent = '이미지 분석 준비 완료';
        uploadStatus.style.color = '#10b981';
        uploadBtn.style.pointerEvents = 'auto';
        uploadBtn.style.cursor = 'pointer';
        uploadBtn.style.opacity = '1';
    }

    // Wait for OpenCV to load and initialize
    function checkOpenCV() {
        if (typeof cv !== 'undefined') {
            if (cv.Mat) {
                onCvReady();
            } else {
                cv.onRuntimeInitialized = onCvReady;
            }
        } else {
            setTimeout(checkOpenCV, 100);
        }
    }
    checkOpenCV();

    // 사용법 모달
    const usageModal = document.getElementById('usage-modal');
    const usageBtn = document.getElementById('usage-btn');
    const closeModal = document.getElementById('close-modal');

    usageBtn?.addEventListener('click', () => {
        usageModal.style.display = 'block';
    });

    closeModal?.addEventListener('click', () => {
        usageModal.style.display = 'none';
    });

    window.addEventListener('click', (e) => {
        if (e.target === usageModal) {
            usageModal.style.display = 'none';
        }
    });

    // // 디버그 모달
    const debugModal = document.getElementById('debug-modal');
    const closeDebugModal = document.getElementById('close-debug-modal');
    const debugContent = document.getElementById('debug-content');

    closeDebugModal?.addEventListener('click', () => {
        debugModal.style.display = 'none';
    });

    window.addEventListener('click', (e) => {
        if (e.target === debugModal) {
            debugModal.style.display = 'none';
        }
    });

    function showDebugModal(debugData) {
        debugContent.innerHTML = '';

        debugData.forEach((pieceDebug, index) => {
            const pieceSection = document.createElement('div');
            pieceSection.style.border = '2px solid #667eea';
            pieceSection.style.borderRadius = '10px';
            pieceSection.style.padding = '15px';
            pieceSection.style.background = '#f8f9fa';

            const title = document.createElement('h3');
            title.textContent = `조각 ${index + 1}`;
            title.style.marginTop = '0';
            title.style.color = '#374151';
            title.style.fontSize = '13px';
            title.style.fontWeight = '800';
            title.style.marginBottom = '6px';
    title.style.marginTop = '0';
    title.style.textAlign = 'center';
            pieceSection.appendChild(title);

            const canvasContainer = document.createElement('div');
            canvasContainer.style.display = 'grid';
            canvasContainer.style.gridTemplateColumns = 'repeat(auto-fit, minmax(250px, 1fr))';
            canvasContainer.style.gap = '15px';
            canvasContainer.style.marginBottom = '15px';

            // 원본 이미지
            const originalDiv = document.createElement('div');
            const originalTitle = document.createElement('h4');
            originalTitle.textContent = '1. 원본';
            originalTitle.style.marginTop = '0';
            originalDiv.appendChild(originalTitle);
            // 캔버스 스타일 추가
            pieceDebug.originalCanvas.style.maxWidth = '100%';
            pieceDebug.originalCanvas.style.border = '1px solid #ccc';
            pieceDebug.originalCanvas.style.borderRadius = '5px';
            originalDiv.appendChild(pieceDebug.originalCanvas);
            canvasContainer.appendChild(originalDiv);

            // 처리된 이미지
            const processedDiv = document.createElement('div');
            const processedTitle = document.createElement('h4');
            processedTitle.textContent = '2. 처리 (배경 제거)';
            processedTitle.style.marginTop = '0';
            processedDiv.appendChild(processedTitle);
            // 캔버스 스타일 추가
            pieceDebug.processedCanvas.style.maxWidth = '100%';
            pieceDebug.processedCanvas.style.border = '1px solid #ccc';
            pieceDebug.processedCanvas.style.borderRadius = '5px';
            processedDiv.appendChild(pieceDebug.processedCanvas);
            canvasContainer.appendChild(processedDiv);

            // 그리드 분석
            const gridDiv = document.createElement('div');
            const gridTitle = document.createElement('h4');
            gridTitle.textContent = '3. 그리드 분석';
            gridTitle.style.marginTop = '0';
            gridDiv.appendChild(gridTitle);
            // 캔버스 스타일 추가
            pieceDebug.gridCanvas.style.maxWidth = '100%';
            pieceDebug.gridCanvas.style.border = '1px solid #ccc';
            pieceDebug.gridCanvas.style.borderRadius = '5px';
            gridDiv.appendChild(pieceDebug.gridCanvas);
            canvasContainer.appendChild(gridDiv);

            pieceSection.appendChild(canvasContainer);

            // 분석 정보
            const info = document.createElement('pre');
            info.style.background = 'white';
            info.style.padding = '10px';
            info.style.borderRadius = '5px';
            info.style.fontSize = '0.9em';
            info.style.overflow = 'auto';
            info.textContent = pieceDebug.info;
            pieceSection.appendChild(info);

            debugContent.appendChild(pieceSection);
        });

        debugModal.style.display = 'block';
    }

    // Show set selection modal with tabs for each image
    function showSetSelectionModal(imagesData) {
        return new Promise((resolve) => {
            const modal = document.createElement('div');
            modal.style.position = 'fixed';
            modal.style.zIndex = '2000';
            modal.style.left = '0';
            modal.style.top = '0';
            modal.style.width = '100%';
            modal.style.height = '100%';
            modal.style.background = 'rgba(0,0,0,0.7)';
            modal.style.display = 'flex';
            modal.style.alignItems = 'center';
            modal.style.justifyContent = 'center';

            const modalContent = document.createElement('div');
            modalContent.style.background = 'white';
            modalContent.style.padding = '18px';
            modalContent.style.borderRadius = '15px';
            modalContent.style.maxWidth = '820px';
            modalContent.style.maxHeight = '84vh';
            modalContent.style.overflowY = 'auto';
            modalContent.style.width = '90%';

            const title = document.createElement('h2');
            title.textContent = '사진별 세트 선택';
            title.style.marginTop = '0';
            title.style.color = '#374151';
            title.style.fontSize = '13px';
            title.style.fontWeight = '800';
            title.style.marginBottom = '6px';
            title.style.textAlign = 'center';
            modalContent.appendChild(title);

            const description = document.createElement('p');
            description.innerHTML = `<strong>${imagesData.length}장의 사진</strong>에서 인식된 조각들입니다.<br>각 사진마다 세트를 선택하면 해당 사진의 모든 조각이 선택한 세트로 들어갑니다.`;
            description.style.marginBottom = '12px';
            description.style.fontSize = '12px';
            description.style.color = '#374151';
            description.style.textAlign = 'center';
            description.style.lineHeight = '1.6';
            modalContent.appendChild(description);

            // Create tabs
            const tabButtons = document.createElement('div');
            tabButtons.style.display = 'flex';
            tabButtons.style.gap = '5px';
            tabButtons.style.marginBottom = '10px';
            tabButtons.style.flexWrap = 'nowrap';
            tabButtons.style.overflowX = 'auto';
            tabButtons.style.justifyContent = 'space-evenly';
            tabButtons.style.position = 'sticky';
            tabButtons.style.top = '0';
            tabButtons.style.backgroundColor = 'white';
            tabButtons.style.zIndex = '10';
            tabButtons.style.paddingTop = '4px';
            tabButtons.style.paddingBottom = '6px';

            const tabContents = document.createElement('div');
            tabContents.style.minHeight = '0';

            let activeTabIndex = 0;
            const imageSetSelectors = []; // 각 이미지의 세트 선택기 저장

            // 카드 우상단 × 삭제 버튼 (잘못 인식/중복 인식 제거용)
            const csMakeCardRemoveBtn = (onRemove) => {
                const btn = document.createElement('button');
                btn.type = 'button';
                // 폰트 글리프 '×'는 베이스라인 때문에 원 안에서 살짝 치우쳐 보여서
                // 기하학적으로 정중앙인 SVG 십자로 그린다. currentColor라 hover 색상도 그대로 따라간다.
                btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 14 14" style="display:block" aria-hidden="true"><path d="M4.6 4.6 L9.4 9.4 M9.4 4.6 L4.6 9.4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>';
                btn.title = '이 조각 삭제';
                btn.style.position = 'absolute';
                // 모달 카드 칩은 normalize에서 20px: 중심 = padding 4 + 10 = 14 -> top 7px
                btn.style.top = '7px';
                btn.style.right = '6px';
                btn.style.width = '14px';
                btn.style.height = '14px';
                btn.style.minHeight = '14px';
                btn.style.padding = '0';
                btn.style.margin = '0';
                btn.style.border = 'none';
                btn.style.borderRadius = '50%';
                btn.style.background = '#e5e7eb';
                btn.style.color = '#6b7280';
                btn.style.fontSize = '10px';
                btn.style.fontWeight = '800';
        btn.style.fontFamily = 'Arial, sans-serif';
                btn.style.lineHeight = '14px';
                btn.style.display = 'flex';
                btn.style.alignItems = 'center';
                btn.style.justifyContent = 'center';
                btn.style.cursor = 'pointer';
                btn.style.zIndex = '5';
                btn.addEventListener('mouseenter', () => { btn.style.background = '#ff4048'; btn.style.color = '#fff'; });
                btn.addEventListener('mouseleave', () => { btn.style.background = '#e5e7eb'; btn.style.color = '#6b7280'; });
                btn.addEventListener('click', (ev) => {
                    ev.stopPropagation();
                    if (ev.stopImmediatePropagation) ev.stopImmediatePropagation();
                    if (typeof onRemove === 'function') onRemove();
                });
                return btn;
            };

            // 수동 추가 조각 등급 정의
            const csManualGradeDefs = [{ key: 'rare', label: ((typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en') ? 'Rare' : '레어'), color: '#5d8cff' }, { key: 'epic', label: ((typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en') ? 'Epic' : '에픽'), color: '#b46bff' }, { key: 'super', label: ((typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en') ? 'Super Epic' : '슈퍼에픽'), color: '#ff5b66' }, { key: 'unique', label: ((typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en') ? 'Unique' : '유니크'), color: '#ffcc00' }];
            const csManualGradeBg = { rare: 'rgba(100, 150, 255, 0.2)', epic: 'rgba(200, 100, 255, 0.2)', super: 'rgba(255, 100, 100, 0.2)', unique: 'rgba(255, 204, 0, 0.28)' };
            const csChipInnerBg = () => CS_DARK_UI ? '#303236' : '#fff';
            const csGradeTextColor = (grade) => (csManualGradeDefs.find(d => d.key === grade) || csManualGradeDefs[1]).color;
            const csApplySetChipStyle = (chip) => {
                chip.classList.add('cs-set-chip');
                chip.style.background = csChipInnerBg();
                chip.style.color = '#10b981';
            };
            const csApplyGradeCountStyle = (chip, grade) => {
                chip.classList.add('cs-count-badge', `cs-grade-${grade || 'epic'}`);
                chip.style.background = csChipInnerBg();
                chip.style.color = csGradeTextColor(grade);
            };

            function csOpenGradeSelectModal(onPick) {
                const gModal = document.createElement('div');
                gModal.style.position = 'fixed';
                gModal.style.zIndex = '3000';
                gModal.style.left = '0';
                gModal.style.top = '0';
                gModal.style.width = '100%';
                gModal.style.height = '100%';
                gModal.style.background = 'rgba(0,0,0,0.55)';
                gModal.style.display = 'flex';
                gModal.style.alignItems = 'center';
                gModal.style.justifyContent = 'center';

                const gBox = document.createElement('div');
                gBox.style.width = 'min(300px, 90vw)';
                gBox.style.background = '#fff';
                gBox.style.borderRadius = '12px';
                gBox.style.padding = '16px';
                gBox.style.boxShadow = '0 12px 32px rgba(0,0,0,0.22)';
                gBox.style.boxSizing = 'border-box';

                const gTitle = document.createElement('div');
                gTitle.textContent = '추가할 조각의 등급 선택';
                gTitle.classList.add('cs-grade-title');
                gTitle.style.fontWeight = '800';
                gTitle.style.fontSize = '12px';
                gTitle.style.color = CS_DARK_UI ? '#f3f4f6' : '#374151';
                gTitle.style.marginBottom = '10px';
                gBox.appendChild(gTitle);

                csManualGradeDefs.forEach(def => {
                    const gBtn = document.createElement('button');
                    gBtn.type = 'button';
                    gBtn.textContent = def.label;
                    gBtn.classList.add('cs-grade-pick-btn', `cs-grade-${def.key}`);
                    gBtn.style.display = 'block';
                    gBtn.style.width = '100%';
                    gBtn.style.boxSizing = 'border-box';
                    gBtn.style.padding = '9px 12px';
                    gBtn.style.marginBottom = '6px';
                    gBtn.style.border = 'none';
                    gBtn.style.outline = 'none';
                    gBtn.style.boxShadow = 'none';
                    gBtn.style.borderRadius = '8px';
                    gBtn.style.background = CS_DARK_UI ? '#3a3d42' : '#f3f4f6';
                    gBtn.style.color = '#9ca3af';
                    gBtn.style.fontSize = '12px';
                    gBtn.style.fontWeight = '800';
                    gBtn.style.cursor = 'pointer';
                    gBtn.style.transition = 'background-color .12s ease, color .12s ease';
                    gBtn.addEventListener('mouseenter', () => {
                        gBtn.style.background = csManualGradeBg[def.key] || 'rgba(156,163,175,0.18)';
                        gBtn.style.color = def.color;
                    });
                    gBtn.addEventListener('mouseleave', () => {
                        gBtn.style.background = CS_DARK_UI ? '#3a3d42' : '#f3f4f6';
                        gBtn.style.color = '#9ca3af';
                    });
                    gBtn.addEventListener('focus', () => {
                        gBtn.style.background = csManualGradeBg[def.key] || 'rgba(156,163,175,0.18)';
                        gBtn.style.color = def.color;
                    });
                    gBtn.addEventListener('blur', () => {
                        gBtn.style.background = CS_DARK_UI ? '#3a3d42' : '#f3f4f6';
                        gBtn.style.color = '#9ca3af';
                    });
                    gBtn.addEventListener('click', () => {
                        document.body.removeChild(gModal);
                        if (typeof onPick === 'function') onPick(def.key);
                    });
                    gBox.appendChild(gBtn);
                });

                gModal.appendChild(gBox);
                gModal.addEventListener('click', (ev) => { if (ev.target === gModal) document.body.removeChild(gModal); });
                document.body.appendChild(gModal);
            }

            imagesData.forEach((imageData, imageIndex) => {
                const { fileName, pieces } = imageData;

                // Tab button
                const tabBtn = document.createElement('button');
                tabBtn.textContent = `${fileName || `이미지 ${imageIndex + 1}`}`;
                tabBtn.style.padding = '7px 10px';
                tabBtn.style.border = 'none';
                tabBtn.style.borderRadius = '8px 8px 0 0';
                tabBtn.style.cursor = 'pointer';
                tabBtn.style.fontWeight = 'bold';
                tabBtn.style.fontSize = '11px';
                tabBtn.style.transition = 'all 0.3s';
                tabBtn.style.flex = '1 1 0';
                tabBtn.style.minWidth = '0';
                tabBtn.style.whiteSpace = 'nowrap';
                tabBtn.style.overflow = 'hidden';
                tabBtn.style.textOverflow = 'ellipsis';

                if (imageIndex === 0) {
                    tabBtn.style.background = 'linear-gradient(135deg, #667eea, #764ba2)';
                    tabBtn.style.color = 'white';
                } else {
                    tabBtn.style.background = '#e5e7eb';
                    tabBtn.style.color = '#666';
                }

                tabBtn.addEventListener('click', () => {
                    activeTabIndex = imageIndex;
                    // Update tab styles
                    tabButtons.querySelectorAll('button').forEach((btn, idx) => {
                        if (idx === imageIndex) {
                            btn.style.background = 'linear-gradient(135deg, #667eea, #764ba2)';
                            btn.style.color = 'white';
                        } else {
                            btn.style.background = '#e5e7eb';
                            btn.style.color = '#666';
                        }
                    });
                    // Update content visibility
                    tabContents.querySelectorAll('.image-tab-content').forEach((content, idx) => {
                        content.style.display = idx === imageIndex ? 'block' : 'none';
                    });
                });

                tabButtons.appendChild(tabBtn);

                // Tab content
                const tabContent = document.createElement('div');
                tabContent.className = 'image-tab-content';
                tabContent.style.display = imageIndex === 0 ? 'block' : 'none';

                // image title under the tabs removed for cleaner UI

                // 사진 전체의 세트 선택기
                const setSelectBlock = document.createElement('div');
                setSelectBlock.style.marginBottom = '10px';
                setSelectBlock.style.padding = '0';
                setSelectBlock.style.background = 'transparent';
                setSelectBlock.style.borderRadius = '0';
                setSelectBlock.style.border = '0';

                const setLabel = document.createElement('div');
                setLabel.classList.add('cs-modal-set-label');
                setLabel.textContent = '세트를 선택하세요';
                setLabel.style.fontWeight = '800';
                setLabel.style.marginBottom = '6px';
                setLabel.style.fontSize = '12px';
                setLabel.style.color = CS_DARK_UI ? '#f3f4f6' : '#111827';
                setSelectBlock.appendChild(setLabel);

                const setSelectorWrap = document.createElement('div');
                setSelectorWrap.classList.add('cs-image-set-select-wrap');
                setSelectorWrap.style.position = 'relative';
                setSelectorWrap.style.width = '100%';
                setSelectorWrap.style.overflow = 'visible';

                const setSelector = document.createElement('select');
                setSelector.style.width = '100%';
                setSelector.style.height = '36px';
                setSelector.style.minHeight = '36px';
                setSelector.style.padding = '0 34px 0 12px';
                setSelector.style.fontSize = '12px';
                setSelector.style.borderRadius = '9px';
                setSelector.style.border = '1px solid transparent';
                setSelector.style.background = csSelectFieldBg();
                setSelector.style.color = csSelectFieldText();
                setSelector.style.fontWeight = '700';
                setSelector.style.boxSizing = 'border-box';
                setSelector.style.outline = 'none';
                setSelector.style.appearance = 'none';
                setSelector.style.webkitAppearance = 'none';
                setSelector.style.mozAppearance = 'none';

                const defaultOption = document.createElement('option');
                defaultOption.value = '';
                defaultOption.textContent = '세트를 선택하세요';
                setSelector.appendChild(defaultOption);

                const uniqueOption = document.createElement('option');
                uniqueOption.value = 'unique';
                uniqueOption.textContent = ((typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en') ? 'Unique' : '유니크');
                setSelector.appendChild(uniqueOption);

                Object.entries(SET_INFO).forEach(([setKey, setData]) => {
                    const option = document.createElement('option');
                    option.value = setKey;
                    option.textContent = `${setData.name}`;
                    setSelector.appendChild(option);
                });

                setSelectorWrap.appendChild(setSelector);
                const setSelectorArrow = document.createElement('span');
                setSelectorArrow.textContent = '∨';
                setSelectorArrow.style.position = 'absolute';
                setSelectorArrow.style.right = '12px';
                setSelectorArrow.style.top = '50%';
                setSelectorArrow.style.transform = 'translateY(-50%)';
                setSelectorArrow.style.fontSize = '12px';
                setSelectorArrow.style.fontWeight = '700';
                setSelectorArrow.style.color = csSelectArrowColor();
                setSelectorArrow.style.pointerEvents = 'none';
                setSelectorWrap.appendChild(setSelectorArrow);
                setSelectBlock.appendChild(setSelectorWrap);
                tabContent.appendChild(setSelectBlock);

                // 인식된 조각 목록 표시
                // 장착중 태그가 있는 조각이 있는지 확인
                const hasGreenTagPieces = pieces.some(p => 
                    p.pieceName === null && p.failedPieces && p.failedPieces.some(fp => fp.hasGreenTag)
                );
                
                const piecesTitle = document.createElement('h4');
                piecesTitle.textContent = `인식된 조각 (총 ${pieces.length}종류)`;
                if (hasGreenTagPieces) {
                    piecesTitle.textContent += '';
                }
                piecesTitle.style.color = '#555';
                piecesTitle.style.marginBottom = '10px';
                if (hasGreenTagPieces) {
                    piecesTitle.style.color = '#d97706';
                    piecesTitle.style.fontWeight = 'bold';
                }
                tabContent.appendChild(piecesTitle);

                const statEditHint = document.createElement('div');
                statEditHint.textContent = (typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en') ? 'Click the stat, shard shape, or count box to edit.' : '스탯, 조각 모양, 개수 칸을 클릭하면 각각 수정할 수 있습니다.';
                statEditHint.style.fontSize = '11px';
                statEditHint.style.fontWeight = '800';
                statEditHint.style.color = '#6b7280';
                statEditHint.style.margin = '-4px 0 8px 0';
                tabContent.appendChild(statEditHint);

                const piecesList = document.createElement('div');
                piecesList.style.maxHeight = '286px';
                piecesList.style.overflowY = 'auto';
                piecesList.style.padding = '0';
                piecesList.style.background = 'transparent';
                piecesList.style.borderRadius = '8px';
                piecesList.style.display = 'flex';
                piecesList.style.flexWrap = 'wrap';
                piecesList.style.gap = '8px';

                // 매칭 실패한 조각 또는 장착중 태그가 있는 조각을 맨 앞으로 정렬
                const sortedPieces = [...pieces].sort((a, b) => {
                    // a가 실패하거나 장착중 태그가 있으면 앞으로
                    const aHasIssue = a.pieceName === null || (a.failedPieces && a.failedPieces.some(fp => fp.hasGreenTag));
                    // b가 실패하거나 장착중 태그가 있으면 앞으로
                    const bHasIssue = b.pieceName === null || (b.failedPieces && b.failedPieces.some(fp => fp.hasGreenTag));
                    
                    if (aHasIssue && !bHasIssue) return -1; // a가 문제, b가 정상 -> a가 앞
                    if (!aHasIssue && bHasIssue) return 1;  // a가 정상, b가 문제 -> b가 앞
                    return 0; // 둘 다 같으면 순서 유지
                });

                sortedPieces.forEach((data, sortedIndex) => {
                    const { pieceName, grade, count, failedPieces } = data;
                    
                    // 원본 배열에서의 인덱스 찾기
                    const originalPieceIndex = pieces.findIndex(p => p === data);

                    // 매칭 실패한 조각 또는 장착중 태그가 있는 조각 처리
                    if (pieceName === null && failedPieces) {
                        // 매칭 실패한 조각들을 각각 표시
                        failedPieces.forEach((failedPiece, failedIndex) => {
                            const { grade: failedGrade, debug, hasGreenTag, pieceName: defaultPieceName } = failedPiece;
                            
                            // 등급별 배경색 설정
                            let gradeColor = 'rgba(200, 200, 200, 0.2)'; // 회색 (매칭 실패)
                            let gradeBorderColor = 'rgba(200, 200, 200, 0.5)';
                            if (failedGrade === 'rare') {
                                gradeColor = 'rgba(100, 150, 255, 0.2)';
                                gradeBorderColor = 'rgba(100, 150, 255, 0.5)';
                            } else if (failedGrade === 'epic') {
                                gradeColor = 'rgba(200, 100, 255, 0.2)';
                                gradeBorderColor = 'rgba(200, 100, 255, 0.5)';
                            } else if (failedGrade === 'super') {
                                gradeColor = 'rgba(255, 100, 100, 0.2)';
                                gradeBorderColor = 'rgba(255, 100, 100, 0.5)';
                            } else if (failedGrade === 'unique') {
                                gradeColor = 'rgba(255, 204, 0, 0.18)';
                                gradeBorderColor = 'rgba(255, 204, 0, 0.65)';
                            }

                    const pieceBlock = document.createElement('div');
                            pieceBlock.style.marginBottom = '0';
                            pieceBlock.style.padding = '4px';
                            pieceBlock.style.background = gradeColor;
                    pieceBlock.style.borderRadius = '8px';
                            pieceBlock.style.border = CS_DARK_UI ? '0' : `1px solid ${gradeBorderColor}`;
                    pieceBlock.style.display = 'flex';
                            pieceBlock.style.flexDirection = 'column';
                    pieceBlock.style.alignItems = 'center';
                            pieceBlock.style.gap = '4px';
                            pieceBlock.style.width = '132px';
                            pieceBlock.style.minWidth = '132px';
                            pieceBlock.style.boxSizing = 'border-box';
                            pieceBlock.style.height = '204px';
                            pieceBlock.style.cursor = 'pointer';
                            pieceBlock.style.position = 'relative';
                            // 고유 식별자 추가 (나중에 찾기 위해)
                            pieceBlock.dataset.imageIndex = imageIndex;
                            pieceBlock.dataset.pieceIndex = originalPieceIndex;
                            pieceBlock.dataset.failedIndex = failedIndex;
                            pieceBlock.dataset.isFailed = 'true';
                            pieceBlock.dataset.grade = failedGrade;
                            pieceBlock.dataset.count = '1';

                            const setChip = document.createElement('div');
                            setChip.textContent = '세트 선택';
                            setChip.style.width = '100%';
                            setChip.style.height = '22px';
            setChip.style.flex = '0 0 22px';
                            setChip.style.minHeight = '22px';
                            setChip.style.maxHeight = '22px';
                            setChip.style.display = 'flex';
                            setChip.style.alignItems = 'center';
                            setChip.style.justifyContent = 'center';
                            setChip.style.background = '#fff';
                            setChip.style.borderRadius = '6px';
                            setChip.style.padding = '4px 2px';
                            setChip.style.boxSizing = 'border-box';
                            setChip.style.textAlign = 'center';
                            setChip.style.fontSize = '10px';
                            setChip.style.fontWeight = '800';
                            setChip.style.color = '#10b981';
                            setChip.classList.add('cs-set-chip');
            setChip.style.background = csRecognizedChipBg();
            setChip.style.color = '#10b981';
                            pieceBlock.appendChild(setChip);
                            let failedStatChip = null;
                            if (failedGrade !== 'unique') {
                                failedStatChip = cookieSimMakeEditableStatChip(
                                    failedPiece.stats || null,
                                    () => parseInt(pieceBlock.dataset.count || '1', 10) || 1,
                                    (nextStats) => { failedPiece.stats = nextStats; }
                                );
                            } else {
                                failedPiece.stats = null;
                                failedStatChip = cookieSimMakeStatChip(null);
                                failedStatChip.textContent = (typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en') ? 'None' : '없음';
                                failedStatChip.style.cursor = 'default';
                                failedStatChip.style.pointerEvents = 'none';
                            }
                            pieceBlock.appendChild(failedStatChip);

                            // 원본 이미지 표시
                            if (debug && debug.originalCanvas) {
                                const imgContainer = document.createElement('div');
                                imgContainer.style.width = '100%';
                                imgContainer.style.height = '0';
                                imgContainer.style.display = 'none';
                                imgContainer.style.alignItems = 'center';
                                imgContainer.style.justifyContent = 'center';
                                imgContainer.style.overflow = 'hidden';
                                imgContainer.style.borderRadius = '4px';
                                imgContainer.style.background = '#f0f0f0';
                                
                                const img = document.createElement('img');
                                img.src = debug.originalCanvas.toDataURL();
                                img.style.maxWidth = '100%';
                                img.style.maxHeight = '100%';
                                img.style.objectFit = 'contain';
                                imgContainer.appendChild(img);
                                pieceBlock.appendChild(imgContainer);
                            }

                            // 선택 버튼
                            const selectButton = document.createElement('button');
                            selectButton.textContent = hasGreenTag ? '장착중 조각 선택' : '조각 선택';
                            selectButton.style.width = '100%';
                            selectButton.style.padding = '8px';
                            selectButton.style.fontSize = '0.75em';
                            selectButton.style.borderRadius = '4px';
                            selectButton.style.border = '1px solid #667eea';
                            selectButton.style.background = '#667eea';
                            selectButton.style.color = '#fff';
                            selectButton.style.cursor = 'pointer';
                            selectButton.style.fontWeight = 'bold';
                            
                            
                            // 선택된 조각 표시 영역
                            const selectedDisplay = document.createElement('div');
                            selectedDisplay.style.width = '100%';
                            selectedDisplay.style.minHeight = '74px';
                            selectedDisplay.style.padding = '2px 0';
                            selectedDisplay.style.border = '0';
                            selectedDisplay.style.borderRadius = '4px';
                            selectedDisplay.style.background = csPreviewSurfaceBg();
                            selectedDisplay.style.display = 'none';
                            selectedDisplay.style.flexDirection = 'column';
                            selectedDisplay.style.alignItems = 'center';
                            selectedDisplay.style.gap = '4px';
                            
                            // 기본값으로 선택된 조각이 있으면 표시
                            if (defaultPieceName) {
                                pieceBlock.dataset.selectedPiece = defaultPieceName;
                                pieceBlock.dataset.selectedGrade = failedGrade;
                                
                                // 선택된 조각 표시
                                selectedDisplay.style.display = 'flex';
                                const templateData = COMMON_PIECE_TEMPLATES[defaultPieceName] || UNIQUE_PIECE_TEMPLATES[defaultPieceName];
                                if (templateData) {
                                    const tempPiece = {
                                        shape: templateData.shape,
                                        color: '#999999'
                                    };
                                    const selectedPreview = createPiecePreview(tempPiece);
                                    selectedPreview.style.transform = 'scale(0.6)';
                                    selectedDisplay.appendChild(selectedPreview);
                                    
                                    // 수정 버튼 추가
                                    const editButton = document.createElement('button');
                                    editButton.textContent = '수정';
                                    editButton.style.marginTop = '4px';
                                    editButton.style.padding = '4px 12px';
                                    editButton.style.fontSize = '0.7em';
                                    editButton.style.border = '1px solid #667eea';
                                    editButton.style.borderRadius = '4px';
                                    editButton.style.background = '#667eea';
                                    editButton.style.color = '#fff';
                                    editButton.style.cursor = 'pointer';
                                    editButton.style.fontWeight = 'bold';
                                    editButton.addEventListener('click', () => {
                                        selectButton.click(); // 모달 다시 열기
                                    });
                                    selectedDisplay.appendChild(editButton);
                                    
                                    // 버튼 숨기기
                                    selectButton.style.display = 'none';
                                }
                            }
                            
                            selectedDisplay.style.cursor = 'pointer';
                            selectedDisplay.addEventListener('click', () => selectButton.click());

                            // 버튼 클릭 시 모달 열기
                            selectButton.addEventListener('click', () => {
                                // 모달 생성
                                const modal = document.createElement('div');
                                modal.style.position = 'fixed';
                                modal.style.zIndex = '3000';
                                modal.style.left = '0';
                                modal.style.top = '0';
                                modal.style.width = '100%';
                                modal.style.height = '100%';
                                modal.style.background = 'rgba(0,0,0,0.7)';
                                modal.style.display = 'flex';
                                modal.style.alignItems = 'center';
                                modal.style.justifyContent = 'center';

                                const modalContent = document.createElement('div');
                                modalContent.style.background = '#fff';
                                modalContent.style.borderRadius = '12px';
                                modalContent.style.padding = '18px';
                                modalContent.style.width = '95%';
                                modalContent.style.maxWidth = '1400px';
                                modalContent.style.height = '90vh';
                                modalContent.style.maxHeight = '90vh';
                                modalContent.style.overflowY = 'auto';
                                modalContent.style.boxShadow = '0 10px 40px rgba(0,0,0,0.3)';

                                const modalTitle = document.createElement('h3');
                                modalTitle.textContent = '조각 선택';
                                modalTitle.style.marginBottom = '20px';
                                modalTitle.style.color = '#667eea';
                                modalContent.appendChild(modalTitle);

                                const piecesGrid = document.createElement('div');
                                piecesGrid.style.display = 'grid';
                                piecesGrid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(140px, 1fr))';
                                piecesGrid.style.gap = '16px';
                                piecesGrid.style.maxHeight = 'calc(90vh - 150px)';
                                piecesGrid.style.overflowY = 'auto';

                                // 모든 조각 목록 추가
                                const allPieces = Object.keys({ ...COMMON_PIECE_TEMPLATES, ...UNIQUE_PIECE_TEMPLATES }).filter(pName => failedGrade === 'unique' ? !!UNIQUE_PIECE_TEMPLATES[pName] : !UNIQUE_PIECE_TEMPLATES[pName]);
                                allPieces.forEach(pName => {
                                    const templateData = COMMON_PIECE_TEMPLATES[pName] || UNIQUE_PIECE_TEMPLATES[pName];
                                    if (!templateData) return;

                                    const pieceCard = document.createElement('div');
                                    pieceCard.style.padding = '12px';
                                    pieceCard.style.border = CS_DARK_UI ? '0' : '1px solid #e5e7eb';
                                    pieceCard.style.borderRadius = '8px';
                                    pieceCard.style.cursor = 'pointer';
                                    pieceCard.style.display = 'flex';
                                    pieceCard.style.flexDirection = 'column';
                                    pieceCard.style.alignItems = 'center';
                                    pieceCard.style.gap = '8px';
                                    pieceCard.style.background = CS_DARK_UI ? '#303236' : '#fff';
                                    pieceCard.style.transition = 'background-color 0.15s ease';
                                    pieceCard.dataset.value = pName;

                                    // 조각 미리보기
                                    const tempPiece = {
                                        shape: templateData.shape,
                                        color: '#999999'
                                    };
                                    const preview = createPiecePreview(tempPiece);
                                    preview.style.transform = 'scale(1.0)';
                                    pieceCard.appendChild(preview);

                                    // 호버 효과는 CSS(.cs-picker-card:hover)로 처리
                                    pieceCard.classList.add('cs-picker-card');

                                    // 클릭 시 선택
                                    pieceCard.addEventListener('click', () => {
                                        pieceBlock.dataset.selectedPiece = pName;
                                        pieceBlock.dataset.selectedGrade = failedGrade;
                                        pieceBlock.style.border = CS_DARK_UI ? '0' : `1px solid ${gradeBorderColor}`;
                                        
                                        // 선택된 조각 표시
                                        selectedDisplay.style.display = 'flex';
                                        selectedDisplay.innerHTML = '';
                                        const selectedPreview = createPiecePreview(tempPiece);
                                        selectedPreview.style.transform = 'scale(0.6)';
                                        selectedDisplay.appendChild(selectedPreview);
                                        
                                        // 수정 버튼 추가
                                        const editButton = document.createElement('button');
                                        editButton.textContent = '수정';
                                        editButton.style.marginTop = '4px';
                                        editButton.style.padding = '4px 12px';
                                        editButton.style.fontSize = '0.7em';
                                        editButton.style.border = '1px solid #667eea';
                                        editButton.style.borderRadius = '4px';
                                        editButton.style.background = '#667eea';
                                        editButton.style.color = '#fff';
                                        editButton.style.cursor = 'pointer';
                                        editButton.style.fontWeight = 'bold';
                                        editButton.addEventListener('click', () => {
                                            selectButton.click(); // 모달 다시 열기
                                        });
                                        selectedDisplay.appendChild(editButton);
                                        
                                        // 버튼 숨기기
                                        selectButton.style.display = 'none';
                                        
                                        // 모달 닫기
                                        document.body.removeChild(modal);
                                    });

                                    piecesGrid.appendChild(pieceCard);
                                    
                                    // 기본값으로 선택된 조각이 있으면 하이라이트
                                    if (defaultPieceName && pName === defaultPieceName) {
                                        pieceCard.dataset.csSelected = 'true';
                                    }
                                });

                                modalContent.appendChild(piecesGrid);

                                // 닫기 버튼
                                const closeBtn = document.createElement('button');
                                closeBtn.textContent = '닫기';
                                closeBtn.style.marginTop = '20px';
                                closeBtn.style.padding = '10px 20px';
                                closeBtn.style.border = 'none';
                                closeBtn.style.borderRadius = '6px';
                                closeBtn.style.background = '#ddd';
                                closeBtn.style.cursor = 'pointer';
                                closeBtn.style.fontWeight = 'bold';
                                closeBtn.addEventListener('click', () => {
                                    document.body.removeChild(modal);
                                });
                                modalContent.appendChild(closeBtn);

                                modal.appendChild(modalContent);
                                document.body.appendChild(modal);

                                // 모달 배경 클릭 시 닫기
                                modal.addEventListener('click', (e) => {
                                    if (e.target === modal) {
                                        document.body.removeChild(modal);
                                    }
                                });
                            });

                            pieceBlock.appendChild(selectButton);
                            pieceBlock.appendChild(selectedDisplay);
                            const failCountBadge = document.createElement('div');
                            failCountBadge.textContent = `×${pieceBlock.dataset.count || 1}`;
                            failCountBadge.style.width = '100%';
                            failCountBadge.style.height = '22px';
                            failCountBadge.style.minHeight = '22px';
                            failCountBadge.style.maxHeight = '22px';
                            failCountBadge.style.display = 'flex';
                            failCountBadge.style.alignItems = 'center';
                            failCountBadge.style.justifyContent = 'center';
                            failCountBadge.style.background = '#fff';
                            failCountBadge.style.borderRadius = '6px';
                            failCountBadge.style.padding = '4px 2px';
                            failCountBadge.style.boxSizing = 'border-box';
                            failCountBadge.style.textAlign = 'center';
                            failCountBadge.style.fontSize = '10px';
                            failCountBadge.style.fontWeight = '900';
                            failCountBadge.style.color = csGradeTextColor(failedGrade);
                            csApplyGradeCountStyle(failCountBadge, failedGrade);
                            failCountBadge.style.cursor = 'pointer';
                            failCountBadge.addEventListener('click', (ev) => {
                                ev.stopPropagation();
                                const current = parseInt(pieceBlock.dataset.count || '1', 10) || 1;
                                const next = prompt('개수를 입력하세요.', String(current));
                                if (next === null) return;
                                const n = Math.max(0, Math.min(99, parseInt(next, 10) || 0));
                                pieceBlock.dataset.count = String(n);
                                failedPiece.stats = csResizeStatsForCount(failedPiece.stats, Math.max(1, n));
                                failedStatChip.textContent = cookieSimStatChipText(failedPiece.stats);
                                failCountBadge.textContent = `×${n}`;
                            });
                            pieceBlock.appendChild(failCountBadge);

                            pieceBlock.appendChild(csMakeCardRemoveBtn(() => {
                                failedPiece.deleted = true;
                                pieceBlock.remove();
                            }));

                            piecesList.appendChild(pieceBlock);
                        });
                        return;
                    }

                    // 정상 매칭된 조각 처리
                    // 등급별 배경색 설정
                    let gradeColor = '#ffffff';
                    let gradeBorderColor = '#ddd';
                    if (grade === 'rare') {
                        gradeColor = 'rgba(100, 150, 255, 0.2)'; // 파란색 배경
                        gradeBorderColor = 'rgba(100, 150, 255, 0.5)';
                    } else if (grade === 'epic') {
                        gradeColor = 'rgba(200, 100, 255, 0.2)'; // 보라색 배경
                        gradeBorderColor = 'rgba(200, 100, 255, 0.5)';
                    } else if (grade === 'super') {
                        gradeColor = 'rgba(255, 100, 100, 0.2)'; // 빨간색 배경
                        gradeBorderColor = 'rgba(255, 100, 100, 0.5)';
                    } else if (grade === 'unique') {
                        gradeColor = 'rgba(255, 204, 0, 0.18)';
                        gradeBorderColor = 'rgba(255, 204, 0, 0.65)';
                        data.stats = null;
                    }

                    const pieceBlock = document.createElement('div');
                    pieceBlock.dataset.imageIndex = imageIndex;
                    pieceBlock.dataset.pieceIndex = originalPieceIndex;
                    pieceBlock.dataset.isNormal = 'true';
                    pieceBlock.dataset.grade = grade;
                    pieceBlock.style.marginBottom = '0';
                    pieceBlock.style.padding = '4px';
                    pieceBlock.style.background = gradeColor;
                    pieceBlock.style.borderRadius = '8px';
                    pieceBlock.style.border = CS_DARK_UI ? '0' : `1px solid ${gradeBorderColor}`;
                    pieceBlock.style.display = 'flex';
                    pieceBlock.style.flexDirection = 'column';
                    pieceBlock.style.alignItems = 'center';
                    pieceBlock.style.gap = '4px';
                    pieceBlock.style.width = '132px'; // 한 줄에 5개 (gap 고려)
                    pieceBlock.style.minWidth = '132px';
                    pieceBlock.style.boxSizing = 'border-box';
                    pieceBlock.style.height = '204px';
                    const normalSetChip = document.createElement('div');
                    normalSetChip.textContent = '세트 선택';
                    normalSetChip.style.width = '100%';
                    normalSetChip.style.height = '22px';
                    normalSetChip.style.minHeight = '22px';
                    normalSetChip.style.maxHeight = '22px';
                    normalSetChip.style.display = 'flex';
                    normalSetChip.style.alignItems = 'center';
                    normalSetChip.style.justifyContent = 'center';
                    normalSetChip.style.background = '#fff';
                    normalSetChip.style.borderRadius = '6px';
                    normalSetChip.style.padding = '4px 2px';
                    normalSetChip.style.boxSizing = 'border-box';
                    normalSetChip.style.textAlign = 'center';
                    normalSetChip.style.fontSize = '10px';
                    normalSetChip.style.fontWeight = '800';
                    normalSetChip.style.color = '#10b981';
                    csApplySetChipStyle(normalSetChip);
                    pieceBlock.appendChild(normalSetChip);
                    let normalStatChip = null;
                    if (grade !== 'unique') {
                        normalStatChip = cookieSimMakeEditableStatChip(
                            data.stats || null,
                            () => parseInt(data.count || count || 1, 10) || 1,
                            (nextStats) => { data.stats = nextStats; }
                        );
                    } else {
                        data.stats = null;
                        normalStatChip = cookieSimMakeStatChip(null);
                        normalStatChip.textContent = (typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en') ? 'None' : '없음';
                        normalStatChip.style.cursor = 'default';
                        normalStatChip.style.pointerEvents = 'none';
                    }
                    pieceBlock.appendChild(normalStatChip);

                    // 조각 미리보기 생성 (템플릿 이름으로 조각 찾기)
                    const templateData = COMMON_PIECE_TEMPLATES[pieceName] || UNIQUE_PIECE_TEMPLATES[pieceName];
                    if (templateData) {
                        // 임시 조각 데이터 생성 (회색으로 표시)
                        const tempPiece = {
                            shape: templateData.shape,
                            color: '#999999' // 회색 (세트 선택 전)
                        };
                        const preview = createPiecePreview(tempPiece);
                        preview.style.flex = '0 0 auto';
                        preview.style.transform = 'scale(0.7)'; // 미리보기 크기 축소
                        preview.style.cursor = 'pointer';
                        const bindNormalPreviewEdit = (targetPreview) => {
                            targetPreview.style.cursor = 'pointer';
                            targetPreview.addEventListener('click', () => {
                                openCookieSimPiecePicker(data.pieceName || pieceName, (newPieceName) => {
                                    const newTemplate = COMMON_PIECE_TEMPLATES[newPieceName] || UNIQUE_PIECE_TEMPLATES[newPieceName];
                                    if (!newTemplate) return;
                                    data.pieceName = newPieceName;
                                    const newPreview = createPiecePreview({ shape: newTemplate.shape, color: '#999999' });
                                    newPreview.style.flex = '0 0 auto';
                                    newPreview.style.transform = 'scale(0.7)';
                                    bindNormalPreviewEdit(newPreview);
                                    targetPreview.replaceWith(newPreview);
                                }, grade === 'unique' ? 'unique' : 'regular');
                            });
                        };
                        bindNormalPreviewEdit(preview);
                        pieceBlock.appendChild(preview);
                    }

                    // 개수 표시
                    const countBadge = document.createElement('div');
                    countBadge.textContent = `×${count}`;
                    countBadge.dataset.role = 'count-badge';
                    countBadge.style.fontSize = '10px';
                    countBadge.style.fontWeight = '900';
                    countBadge.style.color = csRecognizedGradeTextColor(grade);
                    countBadge.style.padding = '4px 2px';
                    countBadge.style.height = '22px';
            countBadge.style.flex = '0 0 22px';
                    countBadge.style.minHeight = '22px';
                    countBadge.style.maxHeight = '22px';
                    countBadge.style.display = 'flex';
                    countBadge.style.alignItems = 'center';
                    countBadge.style.justifyContent = 'center';
                    countBadge.style.background = '#fff';
                    countBadge.classList.add('cs-count-badge', `cs-grade-${grade || 'epic'}`);
            countBadge.style.background = csRecognizedChipBg();
            countBadge.style.color = csRecognizedGradeTextColor(grade);
                    countBadge.style.borderRadius = '6px';
                    countBadge.style.width = '100%';
                    countBadge.style.textAlign = 'center';
                    countBadge.style.boxSizing = 'border-box';
                    countBadge.style.cursor = 'pointer';
                    countBadge.addEventListener('click', (ev) => {
                        ev.stopPropagation();
                        const current = parseInt(data.count || count || 1, 10) || 1;
                        const next = prompt('개수를 입력하세요.', String(current));
                        if (next === null) return;
                        const n = Math.max(0, Math.min(99, parseInt(next, 10) || 0));
                        data.count = n;
                        data.stats = csResizeStatsForCount(data.stats, Math.max(1, n));
                        if (normalStatChip) normalStatChip.textContent = cookieSimStatChipText(data.stats);
                        countBadge.textContent = `×${n}`;
                    });
                    pieceBlock.appendChild(countBadge);

                    pieceBlock.style.position = 'relative';
                    pieceBlock.appendChild(csMakeCardRemoveBtn(() => {
                        data.deleted = true;
                        pieceBlock.remove();
                    }));

                    piecesList.appendChild(pieceBlock);
                });

                // 인식되지 않은 조각 수동 추가
                const manualPieces = [];
                let manualSeq = 0;

                const addPieceCard = document.createElement('div');
                addPieceCard.style.width = '100%';
                addPieceCard.style.minWidth = '0';
                addPieceCard.style.height = CS_DARK_UI ? '154px' : '156px';
                addPieceCard.style.boxSizing = 'border-box';
                addPieceCard.style.border = CS_DARK_UI ? '0' : '1px solid #d1d5db';
                addPieceCard.style.borderRadius = '8px';
                const addPieceCardBaseBg = CS_DARK_UI ? '#303236' : '#fff';
                const addPieceCardHoverBg = CS_DARK_UI ? '#34373d' : '#f7f8fa';
                addPieceCard.style.background = addPieceCardBaseBg;
                addPieceCard.style.transition = 'background-color .12s ease';
                addPieceCard.style.display = 'flex';
                addPieceCard.style.flexDirection = 'column';
                addPieceCard.style.alignItems = 'center';
                addPieceCard.style.justifyContent = 'center';
                addPieceCard.style.gap = '2px';
                addPieceCard.style.cursor = 'pointer';
                const addPlus = document.createElement('div');
                addPlus.textContent = '+';
                addPlus.style.fontSize = '26px';
                addPlus.style.fontWeight = '400';
                addPlus.style.lineHeight = '1';
                addPlus.style.color = '#9ca3af';
                const addLabel = document.createElement('div');
                addLabel.textContent = '조각 추가';
                addLabel.style.fontSize = '10px';
                addLabel.style.fontWeight = '800';
                addLabel.style.color = '#9ca3af';
                addPieceCard.appendChild(addPlus);
                addPieceCard.appendChild(addLabel);
                addPieceCard.addEventListener('mouseenter', () => { addPieceCard.style.background = addPieceCardHoverBg; });
                addPieceCard.addEventListener('mouseleave', () => { addPieceCard.style.background = addPieceCardBaseBg; });
                addPieceCard.addEventListener('click', () => {
                    csOpenGradeSelectModal((gradeKey) => {
                        openCookieSimPiecePicker(null, (pName) => {
                            csCreateManualPieceCard(pName, gradeKey);
                        }, gradeKey === 'unique' ? 'unique' : 'regular');
                    });
                });

                const csSyncAddPieceCardHeight = () => {
                    const isUniqueSet = setSelector && setSelector.value === 'unique';
                    addPieceCard.style.height = CS_DARK_UI ? '154px' : '156px';
                    addPieceCard.style.minHeight = addPieceCard.style.height;
                    addPieceCard.style.maxHeight = addPieceCard.style.height;
                };
                setSelector.addEventListener('change', csSyncAddPieceCardHeight);
                setSelector.addEventListener('input', csSyncAddPieceCardHeight);
                csSyncAddPieceCardHeight();

                function csCreateManualPieceCard(pName, gradeKey) {
                    const manualData = { pieceName: pName, grade: gradeKey, count: 1, stats: null, deleted: false };
                    manualPieces.push(manualData);
                    const gradeDef = csManualGradeDefs.find(d => d.key === gradeKey) || csManualGradeDefs[1];

                    const card = document.createElement('div');
                    card.dataset.imageIndex = imageIndex;
                    card.dataset.pieceIndex = `manual-${manualSeq++}`;
                    card.dataset.isManual = 'true';
                    card.dataset.grade = gradeKey;
                    card.style.position = 'relative';
                    card.style.padding = '4px';
                    card.style.background = csManualGradeBg[gradeKey] || csManualGradeBg.epic;
                    card.style.borderRadius = '8px';
                    card.style.border = CS_DARK_UI ? '0' : `1px solid ${gradeDef.color}`;
                    card.style.display = 'flex';
                    card.style.flexDirection = 'column';
                    card.style.alignItems = 'center';
                    card.style.gap = '4px';
                    card.style.width = '132px';
                    card.style.minWidth = '132px';
                    card.style.boxSizing = 'border-box';
                    card.style.height = '156px';

                    const manualSetChip = document.createElement('div');
                    manualSetChip.textContent = '세트 선택';
                    manualSetChip.style.width = '100%';
                    manualSetChip.style.height = '22px';
                    manualSetChip.style.minHeight = '22px';
                    manualSetChip.style.maxHeight = '22px';
                    manualSetChip.style.display = 'flex';
                    manualSetChip.style.alignItems = 'center';
                    manualSetChip.style.justifyContent = 'center';
                    manualSetChip.style.background = '#fff';
                    manualSetChip.style.borderRadius = '6px';
                    manualSetChip.style.padding = '4px 2px';
                    manualSetChip.style.boxSizing = 'border-box';
                    manualSetChip.style.textAlign = 'center';
                    manualSetChip.style.fontSize = '10px';
                    manualSetChip.style.fontWeight = '800';
                    manualSetChip.style.color = '#10b981';
                    csApplySetChipStyle(manualSetChip);
                    card.appendChild(manualSetChip);

                    let manualStatChip = null;
                    if (gradeKey !== 'unique') {
                        manualStatChip = cookieSimMakeEditableStatChip(
                            null,
                            () => parseInt(manualData.count || '1', 10) || 1,
                            (nextStats) => { manualData.stats = nextStats; }
                        );
                    } else {
                        manualData.stats = null;
                        manualStatChip = cookieSimMakeStatChip(null);
                        manualStatChip.textContent = (typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en') ? 'None' : '없음';
                        manualStatChip.style.cursor = 'default';
                        manualStatChip.style.pointerEvents = 'none';
                    }
                    card.appendChild(manualStatChip);

                    const templateData = COMMON_PIECE_TEMPLATES[pName] || UNIQUE_PIECE_TEMPLATES[pName];
                    if (templateData) {
                        const bindManualPreviewEdit = (targetPreview) => {
                            targetPreview.style.cursor = 'pointer';
                            targetPreview.addEventListener('click', () => {
                                openCookieSimPiecePicker(manualData.pieceName, (newPieceName) => {
                                    const newTemplate = COMMON_PIECE_TEMPLATES[newPieceName] || UNIQUE_PIECE_TEMPLATES[newPieceName];
                                    if (!newTemplate) return;
                                    manualData.pieceName = newPieceName;
                                    const newPreview = createPiecePreview({ shape: newTemplate.shape, color: '#999999' });
                                    newPreview.style.flex = '0 0 auto';
                                    newPreview.style.transform = 'scale(0.7)';
                                    bindManualPreviewEdit(newPreview);
                                    targetPreview.replaceWith(newPreview);
                                }, gradeKey === 'unique' ? 'unique' : 'regular');
                            });
                        };
                        const manualPreview = createPiecePreview({ shape: templateData.shape, color: '#999999' });
                        manualPreview.style.flex = '0 0 auto';
                        manualPreview.style.transform = 'scale(0.7)';
                        bindManualPreviewEdit(manualPreview);
                        card.appendChild(manualPreview);
                    }

                    const manualCountBadge = document.createElement('div');
                    manualCountBadge.textContent = '×1';
                    manualCountBadge.dataset.role = 'count-badge';
                    manualCountBadge.style.fontSize = '10px';
                    manualCountBadge.style.fontWeight = '900';
                    manualCountBadge.style.color = gradeDef.color;
                    manualCountBadge.style.padding = '4px 2px';
                    manualCountBadge.style.height = '22px';
                    manualCountBadge.style.minHeight = '22px';
                    manualCountBadge.style.maxHeight = '22px';
                    manualCountBadge.style.display = 'flex';
                    manualCountBadge.style.alignItems = 'center';
                    manualCountBadge.style.justifyContent = 'center';
                    manualCountBadge.style.background = '#fff';
                    csApplyGradeCountStyle(manualCountBadge, gradeKey);
                    manualCountBadge.style.borderRadius = '6px';
                    manualCountBadge.style.width = '100%';
                    manualCountBadge.style.textAlign = 'center';
                    manualCountBadge.style.boxSizing = 'border-box';
                    manualCountBadge.style.cursor = 'pointer';
                    manualCountBadge.addEventListener('click', (ev) => {
                        ev.stopPropagation();
                        const current = parseInt(manualData.count || '1', 10) || 1;
                        const next = prompt('개수를 입력하세요.', String(current));
                        if (next === null) return;
                        const n = Math.max(0, Math.min(99, parseInt(next, 10) || 0));
                        manualData.count = n;
                        manualData.stats = csResizeStatsForCount(manualData.stats, Math.max(1, n));
                        if (manualStatChip) manualStatChip.textContent = cookieSimStatChipText(manualData.stats);
                        manualCountBadge.textContent = `×${n}`;
                    });
                    card.appendChild(manualCountBadge);

                    card.appendChild(csMakeCardRemoveBtn(() => {
                        manualData.deleted = true;
                        card.remove();
                    }));

                    piecesList.insertBefore(card, addPieceCard);
                }

                piecesList.appendChild(addPieceCard);

                tabContent.appendChild(piecesList);

                // 이미지 선택 정보 저장
                imageSetSelectors.push({
                    fileName,
                    pieces,
                    manualPieces,
                    selector: setSelector
                });

                tabContents.appendChild(tabContent);
            });

            modalContent.appendChild(tabButtons);
            modalContent.appendChild(tabContents);

            const buttonContainer = document.createElement('div');
            buttonContainer.style.display = 'flex';
            buttonContainer.style.gap = '10px';
            buttonContainer.style.marginTop = '20px';

            const confirmBtn = document.createElement('button');
            confirmBtn.textContent = '모든 사진 확인';
            confirmBtn.style.flex = '1';
            confirmBtn.style.padding = '12px';
            confirmBtn.style.fontSize = '1em';
            confirmBtn.style.fontWeight = 'bold';
            confirmBtn.style.border = 'none';
            confirmBtn.style.borderRadius = '8px';
            confirmBtn.style.cursor = 'pointer';
            confirmBtn.style.background = 'linear-gradient(135deg, #667eea, #764ba2)';
            confirmBtn.style.color = 'white';

            confirmBtn.addEventListener('click', () => {
                // 장착중 태그가 있는 조각이 있는지 확인
                let hasGreenTagPieces = false;
                imageSetSelectors.forEach((imageData) => {
                    if (imageData.pieces.some(p => 
                        p.pieceName === null && p.failedPieces && p.failedPieces.some(fp => fp.hasGreenTag)
                    )) {
                        hasGreenTagPieces = true;
                    }
                });
                
                // 장착중 태그가 있는 조각이 있으면 confirm으로 확인
                if (hasGreenTagPieces) {
                    const confirmed = confirm('장착 중인 조각은 인식이 어려울 수 있습니다. 모든 조각을 확인해 주세요.');
                    if (!confirmed) {
                        return;
                    }
                }
                
                const results = [];
                let allSelected = true;
                // 사진별 세트 선택이 끝난 뒤, 실제 배치에 쓰일 스탯 풀을 세트 포함 키로 새로 만든다.
                csClearPieceStatCounts();

                // 모든 사진의 세트 선택 검증
                imageSetSelectors.forEach((imageData, imageIndex) => {
                    const selectedSet = imageData.selector.value;
                    const normalizedSet = selectedSet === 'unique' ? (Object.keys(SET_INFO)[0] || 'dealer-radiance') : selectedSet;

                    if (!selectedSet) {
                        allSelected = false;
                        imageData.selector.style.borderColor = '#f5576c';
                        imageData.selector.style.background = '#fff5f5';
                    } else {
                        // 해당 탭의 piecesList 찾기
                        const tabContent = tabContents.children[imageIndex];
                        const piecesList = tabContent.querySelector('div[style*="flex-wrap"]');
                        
                        // 이 사진의 모든 조각에 선택된 세트 적용
                        imageData.pieces.forEach((piece, pieceIndex) => {
                            if (piece.deleted) return; // ×로 삭제한 조각 제외
                            // 매칭 실패한 조각 처리
                            if (piece.pieceName === null && piece.failedPieces) {
                                // 매칭 실패한 조각들 처리
                                piece.failedPieces.forEach((failedPiece, failedIndex) => {
                                    if (failedPiece.deleted) return; // ×로 삭제한 조각 제외
                                    // piecesList에서 해당 조각 블록 찾기 (고유 식별자로)
                                    const pieceBlock = piecesList.querySelector(
                                        `div[data-image-index="${imageIndex}"][data-piece-index="${pieceIndex}"][data-failed-index="${failedIndex}"][data-is-failed="true"]`
                                    );
                                    
                                    if (pieceBlock) {
                                        const selectedPiece = pieceBlock.dataset.selectedPiece;
                                        const selectedGrade = pieceBlock.dataset.selectedGrade || failedPiece.grade;
                                        
                                        if (selectedPiece) {
                                            const selectedCount = parseInt(pieceBlock.dataset.count || '1', 10) || 1;
                                            if (failedPiece.stats) {
                                                const statKey = `${normalizedSet}-${selectedPiece}-${selectedGrade}`;
                                                const expandedStats = {};
                                                Object.entries(failedPiece.stats).forEach(([statName, statCount]) => {
                                                    expandedStats[statName] = (Number(statCount) || 1) * selectedCount;
                                                });
                                                csAddPieceStatCounts(statKey, expandedStats, selectedCount);
                                            }
                                            results.push({
                                                basePieceName: selectedPiece,
                                                selectedSet: normalizedSet,
                                                grade: selectedGrade,
                                                count: selectedCount,
                                                stats: failedPiece.stats || null
                                            });
                                        }
                                    }
                                });
                            } else {
                                // 정상 매칭된 조각
                                const selectedPieceName = piece.pieceName;
                                const selectedGrade = piece.grade;
                                const selectedCount = parseInt(piece.count || '0', 10) || 0;
                                if (piece.stats) {
                                    const statKey = `${normalizedSet}-${selectedPieceName}-${selectedGrade}`;
                                    csAddPieceStatCounts(statKey, piece.stats, selectedCount);
                                }
                                results.push({
                                    basePieceName: selectedPieceName,
                                    selectedSet: normalizedSet,
                                    grade: selectedGrade,
                                    count: selectedCount,
                                    stats: piece.stats || null
                                });
                            }
                        });

                        // 수동으로 추가한 조각 처리
                        (imageData.manualPieces || []).forEach((manualPiece) => {
                            if (manualPiece.deleted) return;
                            const selectedCount = parseInt(manualPiece.count || '0', 10) || 0;
                            if (selectedCount <= 0) return;
                            if (manualPiece.stats) {
                                const statKey = `${normalizedSet}-${manualPiece.pieceName}-${manualPiece.grade}`;
                                csAddPieceStatCounts(statKey, manualPiece.stats, selectedCount);
                            }
                            results.push({
                                basePieceName: manualPiece.pieceName,
                                selectedSet: normalizedSet,
                                grade: manualPiece.grade,
                                count: selectedCount,
                                stats: manualPiece.stats || null
                            });
                        });
                    }
                });

                if (!allSelected) {
                    alert('모든 사진의 세트를 선택해주세요!');
                    return;
                }

                document.body.removeChild(modal);
                resolve(results);
            });

            const cancelBtn = document.createElement('button');
            cancelBtn.textContent = '취소';
            cancelBtn.style.flex = '1';
            cancelBtn.style.padding = '12px';
            cancelBtn.style.fontSize = '1em';
            cancelBtn.style.fontWeight = 'bold';
            cancelBtn.style.border = 'none';
            cancelBtn.style.borderRadius = '8px';
            cancelBtn.style.cursor = 'pointer';
            cancelBtn.style.background = '#e5e7eb';
            cancelBtn.style.color = '#666';

            cancelBtn.addEventListener('click', () => {
                document.body.removeChild(modal);
                resolve(null);
            });

            buttonContainer.appendChild(confirmBtn);
            buttonContainer.appendChild(cancelBtn);
            modalContent.appendChild(buttonContainer);

            modal.appendChild(modalContent);
            document.body.appendChild(modal);
        });
    }

    imageUpload?.addEventListener('change', async (e) => {
        const files = e.target.files;
        if (files.length === 0) return;

        uploadStatus.textContent = `${files.length}장의 이미지 분석 중...`;
        uploadStatus.style.color = '#667eea';

        try {
            // 각 이미지별로 인식된 조각 데이터 저장
            const imagesData = [];
            const finalResults = [];

            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                const pieceData = await recognizePiecesWithCV(file);

                if (pieceData && pieceData.length > 0) {
                    imagesData.push({
                        fileName: file.name,
                        pieces: pieceData
                    });
                }
            }

            if (imagesData.length === 0) {
                uploadStatus.textContent = ' 조각 정보를 찾을 수 없습니다. 이미지가 선명한지 확인해주세요.';
                uploadStatus.style.color = '#f59e0b';
                return;
            }

            // 모든 이미지의 조각에 대해 세트 선택
            uploadStatus.textContent = ` ${imagesData.length}개 이미지의 조각 세트를 선택해주세요...`;

            const selections = await showSetSelectionModal(imagesData);

            if (!selections) {
                uploadStatus.textContent = ' 세트 선택이 취소되었습니다.';
                uploadStatus.style.color = '#f59e0b';
                return;
            }

            // Add selected pieces with set information
            for (const selection of selections) {
                const fullPieceName = `${selection.selectedSet}-${selection.basePieceName}`;
                finalResults.push({
                    pieceName: fullPieceName,
                    selectedSet: selection.selectedSet,
                    basePieceName: selection.basePieceName,
                    grade: selection.grade,
                    count: selection.count,
                    stats: selection.stats || null
                });
            }

            csRecognizedResults = finalResults.map(p => ({ ...p }));
            fillPiecesFromCV(csRecognizedResults);
            renderRecognizedPieceCards(csRecognizedResults);

            const totalPieces = csRecognizedResults.reduce((sum, p) => sum + p.count, 0);
            uploadStatus.textContent = ` ${files.length}장 분석 완료! ${finalResults.length}개 종류, 총 ${totalPieces}개의 조각을 인식했습니다!`;
            uploadStatus.style.color = '#10b981';

        } catch (error) {
            console.error('Image Analysis Error:', error);
            uploadStatus.textContent = ` 이미지 분석 실패: ${error.message || '알 수 없는 오류'}.`;
            uploadStatus.style.color = '#f5576c';
        }

        // 파일 선택 초기화 (같은 파일 다시 선택 가능)
        e.target.value = '';
    });

    
    
    
    
    
    
    
// ===== 설탕유리조각 스탯 색상 분류 (사용자 제공 기준 이미지에서 측정한 HSV 중앙값) =====
const CS_STAT_COLOR_REFS = [
    { name: '치명타 확률',     h: 32,  s: 0.11, v: 1.00 },
    { name: '공격력 %',        h: 56,  s: 0.34, v: 0.98 },
    { name: '속성 공격력',     h: 40,  s: 0.27, v: 0.96 },
    { name: '치명타 피해',     h: 337, s: 0.16, v: 0.97 },
    { name: '궁극기 피해',     h: 320, s: 0.16, v: 0.97 },
    { name: '모든 속성 피해',  h: 204, s: 0.36, v: 1.00 },
    { name: '패시브 스킬 피해', h: 125, s: 0.15, v: 0.99 },
    { name: '기본 공격 피해',  h: 187, s: 0.16, v: 1.00 },
    { name: '방어력 %',        h: 184, s: 0.07, v: 1.00 },
    { name: '보호막 %',        h: 202, s: 0.22, v: 1.00 },
    { name: '회복량 %',        h: 222, s: 0.16, v: 0.98 },
    { name: '특수 스킬 피해',  h: 255, s: 0.26, v: 0.72 }
];


function csStatDistance(h, s, v, ref) {
    let dh = Math.abs(h - ref.h);
    if (dh > 180) dh = 360 - dh;
    return dh + Math.abs(s - ref.s) * 120 + Math.abs(v - ref.v) * 60;
}

function csRgbToHsv(r, g, b) {
    const rn = r / 255, gn = g / 255, bn = b / 255;
    const mx = Math.max(rn, gn, bn);
    const mn = Math.min(rn, gn, bn);
    const delta = mx - mn;
    let h = 0;
    if (delta > 0) {
        if (mx === rn) h = 60 * (((gn - bn) / delta) % 6);
        else if (mx === gn) h = 60 * (((bn - rn) / delta) + 2);
        else h = 60 * (((rn - gn) / delta) + 4);
    }
    if (h < 0) h += 360;
    const s = mx === 0 ? 0 : delta / mx;
    return { h, s, v: mx };
}

function csClassifyStatByColor(h, s, v, maxDist) {
    // 공격력%와 속성 공격력은 둘 다 노란 계열이라 기존 중앙값 방식에서 자주 섞인다.
    // 채도가 충분한 노랑/주황 픽셀은 색상각을 우선해서 둘을 분리한다.
    if (s >= 0.16 && v >= 0.55 && h >= 25 && h <= 70) {
        if (h < 48) return '속성 공격력';
        if (h > 50) return '공격력 %';
        return Math.abs(h - 40) <= Math.abs(h - 56) ? '속성 공격력' : '공격력 %';
    }

    let best = null, bestD = Infinity;
    for (const ref of CS_STAT_COLOR_REFS) {
        const d = csStatDistance(h, s, v, ref);
        if (d < bestD) { bestD = d; best = ref.name; }
    }
    // 기준색과 너무 멀면 미상 처리 (엉뚱한 스탯에 붙는 것 방지)
    return bestD <= (maxDist || 45) ? best : null;
}

function csClassifyStatSamples(samples, maxDist) {
    if (!samples || samples.length < 8) return null;
    const med = arr => {
        const a = arr.slice().sort((x, y) => x - y);
        return a[Math.floor(a.length / 2)];
    };
    const hs = samples.map(p => p.h);
    const ss = samples.map(p => p.s);
    const vs = samples.map(p => p.v);
    return csClassifyStatByColor(med(hs), med(ss), med(vs), maxDist || 45);
}

function csIsGreenTagPixel(r, g, b) {
    const dr = r - 82, dg = g - 206, db = b - 50;
    return Math.sqrt(dr * dr + dg * dg + db * db) <= 35;
}

function csCollectFocusedCellSamples(srcMat, box, bgColor, extractedShape) {
    if (!extractedShape || !extractedShape.length || !bgColor) return [];

    let iconRoi = null;
    let binary = null;
    let bgLower = null;
    let bgUpper = null;
    let bgMask = null;
    let greenLower = null;
    let greenUpper = null;
    let greenMask = null;
    let brightnessMask = null;
    let colorMask = null;
    let smallKernel = null;
    let largeKernel = null;
    let erodeKernel = null;
    let contours = null;
    let hierarchy = null;

    try {
        const marginLeft = 0.08, marginRight = 0.08, marginTop = 0.08, marginBottom = 0.08;
        let iconX = box.x + Math.floor(box.width * marginLeft);
        let iconY = box.y + Math.floor(box.height * marginTop);
        const iconW0 = Math.floor(box.width * (1 - marginLeft - marginRight));
        const iconH0 = Math.floor(box.height * (1 - marginTop - marginBottom));
        if (iconW0 <= 8 || iconH0 <= 8) return [];

        iconRoi = srcMat.roi(new cv.Rect(iconX, iconY, iconW0, iconH0));
        const greenOffset = detectGreenTagOffsetFromMat(iconRoi);
        if (greenOffset > 0 && iconH0 - greenOffset > 10) {
            iconRoi.delete();
            iconY += greenOffset;
            iconRoi = srcMat.roi(new cv.Rect(iconX, iconY, iconW0, iconH0 - greenOffset));
        }

        const iconW = iconRoi.cols;
        const iconH = iconRoi.rows;
        const tolerance = 60;

        bgLower = new cv.Mat(iconH, iconW, iconRoi.type(), [
            Math.max(0, bgColor.r - tolerance),
            Math.max(0, bgColor.g - tolerance),
            Math.max(0, bgColor.b - tolerance),
            0
        ]);
        bgUpper = new cv.Mat(iconH, iconW, iconRoi.type(), [
            Math.min(255, bgColor.r + tolerance),
            Math.min(255, bgColor.g + tolerance),
            Math.min(255, bgColor.b + tolerance),
            255
        ]);
        bgMask = new cv.Mat();
        cv.inRange(iconRoi, bgLower, bgUpper, bgMask);

        greenLower = new cv.Mat(iconH, iconW, iconRoi.type(), [47, 171, 15, 0]);
        greenUpper = new cv.Mat(iconH, iconW, iconRoi.type(), [117, 241, 85, 255]);
        greenMask = new cv.Mat();
        cv.inRange(iconRoi, greenLower, greenUpper, greenMask);

        brightnessMask = cv.Mat.zeros(iconH, iconW, cv.CV_8UC1);
        const topCleanHeight = Math.floor(iconH * 0.25);
        for (let y = 0; y < topCleanHeight; y++) {
            for (let x = 0; x < iconW; x++) {
                const px = iconRoi.ucharPtr(y, x);
                const r = px[0], g = px[1], b = px[2];
                const brightness = (r + g + b) / 3;
                const colorDiff = Math.max(r, g, b) - Math.min(r, g, b);
                const isGray = colorDiff < 30 && brightness > 100;
                const isBright = brightness > 180;
                const isWhite = r > 200 && g > 200 && b > 200;
                if (isBright || isWhite || isGray) brightnessMask.ucharPtr(y, x)[0] = 255;
            }
        }

        colorMask = new cv.Mat();
        cv.bitwise_or(bgMask, greenMask, colorMask);
        cv.bitwise_or(colorMask, brightnessMask, colorMask);
        cv.bitwise_not(colorMask, colorMask); // 전경 후보

        // 너무 어두운 카드 테두리/그림자는 bbox를 망가뜨리므로 제거
        for (let y = 0; y < iconH; y++) {
            for (let x = 0; x < iconW; x++) {
                if (colorMask.ucharPtr(y, x)[0] <= 128) continue;
                const px = iconRoi.ucharPtr(y, x);
                const brightness = (px[0] + px[1] + px[2]) / 3;
                if (brightness <= 35) colorMask.ucharPtr(y, x)[0] = 0;
            }
        }

        smallKernel = cv.getStructuringElement(cv.MORPH_RECT, new cv.Size(3, 3));
        largeKernel = cv.getStructuringElement(cv.MORPH_RECT, new cv.Size(5, 5));
        cv.morphologyEx(colorMask, colorMask, cv.MORPH_OPEN, smallKernel);
        cv.morphologyEx(colorMask, colorMask, cv.MORPH_CLOSE, largeKernel);

        contours = new cv.MatVector();
        hierarchy = new cv.Mat();
        cv.findContours(colorMask, contours, hierarchy, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE);

        binary = cv.Mat.zeros(iconH, iconW, cv.CV_8UC1);
        let largestArea = 0;
        let largestIdx = -1;
        const minArea = iconW * iconH * 0.005;
        for (let i = 0; i < contours.size(); i++) {
            const area = cv.contourArea(contours.get(i));
            if (area > largestArea && area >= minArea) {
                largestArea = area;
                largestIdx = i;
            }
        }
        if (largestIdx < 0) return [];
        cv.drawContours(binary, contours, largestIdx, new cv.Scalar(255), cv.FILLED);

        erodeKernel = cv.getStructuringElement(cv.MORPH_RECT, new cv.Size(3, 3));
        cv.erode(binary, binary, erodeKernel);

        let minX = iconW, maxX = 0, minY = iconH, maxY = 0, filled = 0;
        for (let y = 0; y < iconH; y++) {
            for (let x = 0; x < iconW; x++) {
                if (binary.ucharPtr(y, x)[0] > 128) {
                    filled++;
                    if (x < minX) minX = x;
                    if (x > maxX) maxX = x;
                    if (y < minY) minY = y;
                    if (y > maxY) maxY = y;
                }
            }
        }
        if (filled < 8 || minX >= maxX || minY >= maxY) return [];

        const gridRows = Math.max(...extractedShape.map(p => p[0])) + 1;
        const gridCols = Math.max(...extractedShape.map(p => p[1])) + 1;
        if (gridRows <= 0 || gridCols <= 0) return [];

        const pieceW = maxX - minX + 1;
        const pieceH = maxY - minY + 1;
        const cellW = pieceW / gridCols;
        const cellH = pieceH / gridRows;
        const bg = [bgColor.r, bgColor.g, bgColor.b];
        const samples = [];

        for (const [row, col] of extractedShape) {
            const sx = Math.floor(minX + col * cellW + cellW * 0.25);
            const ex = Math.floor(minX + (col + 1) * cellW - cellW * 0.25);
            const sy = Math.floor(minY + row * cellH + cellH * 0.25);
            const ey = Math.floor(minY + (row + 1) * cellH - cellH * 0.25);
            if (ex <= sx || ey <= sy) continue;
            for (let y = Math.max(0, sy); y < Math.min(iconH, ey); y++) {
                for (let x = Math.max(0, sx); x < Math.min(iconW, ex); x++) {
                    const px = iconRoi.ucharPtr(y, x);
                    const r = px[0], g = px[1], b = px[2];
                    const hsv = csRgbToHsv(r, g, b);
                    if (hsv.v < 0.45) continue;
                    const bgDiff = Math.abs(r - bg[0]) + Math.abs(g - bg[1]) + Math.abs(b - bg[2]);
                    if (bgDiff < 80) continue;
                    if (csIsGreenTagPixel(r, g, b)) continue;
                    samples.push(hsv);
                }
            }
        }
        return samples;
    } catch (e) {
        return [];
    } finally {
        [iconRoi, binary, bgLower, bgUpper, bgMask, greenLower, greenUpper, greenMask,
         brightnessMask, colorMask, smallKernel, largeKernel, erodeKernel, contours, hierarchy]
            .forEach(m => { try { if (m) m.delete(); } catch (_) {} });
    }
}

// 박스 내부(조각 결정 부분)의 대표 색으로 스탯 분류.
// 1차: 조각의 실제 칸 중앙부만 샘플링해서 테두리/모서리 장식 오염을 줄인다.
// 2차: 실패 시 기존 전체 박스 중앙값 방식으로 fallback 한다.
function csSampleStatFromBox(srcMat, box, bgColor, extractedShape) {
    try {
        const focusedSamples = csCollectFocusedCellSamples(srcMat, box, bgColor, extractedShape);
        const focusedName = csClassifyStatSamples(focusedSamples, 55);
        if (focusedName) return focusedName;
    } catch (_) {}

    try {
        const samples = [];
        let scanned = 0;
        const x0 = Math.max(0, box.x);
        // 상단 20%는 '장착중' 태그가 겹치는 영역이라 샘플링에서 제외
        const y0 = Math.max(0, box.y + Math.floor(box.height * 0.20));
        const x1 = Math.min(srcMat.cols, box.x + box.width);
        const y1 = Math.min(srcMat.rows, box.y + box.height);
        const stride = Math.max(1, Math.floor(Math.min(box.width, box.height) / 60));
        const bg = bgColor || null;
        for (let y = y0; y < y1; y += stride) {
            for (let x = x0; x < x1; x += stride) {
                scanned++;
                const px = srcMat.ucharPtr(y, x);
                const r = px[0], g = px[1], b = px[2];
                const hsv = csRgbToHsv(r, g, b);
                if (hsv.v < 0.55) continue;                                   // 어두운 프레임
                if (bg) {                                                     // 등급 배경색 근처 제외
                    const d = Math.abs(r - bg.r) + Math.abs(g - bg.g) + Math.abs(b - bg.b);
                    if (d < 90) continue;
                }
                if (hsv.h >= 195 && hsv.h <= 235 && hsv.s < 0.32 && hsv.v < 0.85) continue; // 슬레이트 회색
                if (hsv.h >= 88 && hsv.h <= 145 && hsv.s >= 0.28 && hsv.v >= 0.5 && hsv.v <= 0.92) continue; // '장착중' 태그·초록 세트 표식
                if (hsv.s < 0.06 && hsv.v < 0.9) continue;                    // 저채도 잡음
                samples.push(hsv);
            }
        }
        if (samples.length < 30) return null;
        // 조각이 작을수록(유효 픽셀 비율이 낮을수록) 표식·배경 오염 위험이 커서 더 엄격한 매칭을 요구
        const keptRatio = samples.length / Math.max(1, scanned);
        const maxDist = keptRatio < 0.045 ? 18 : 45;
        return csClassifyStatSamples(samples, maxDist);
    } catch (e) {
        return null;
    }
}

const CS_STAT_NAME_EN = {
    '치명타 확률': 'CRIT Rate',
    '치명타 피해': 'CRIT Damage',
    '공격력 %': 'ATK%',
    '속성 공격력': 'Elemental ATK',
    '모든 속성 피해': 'Elemental DMG',
    '특수 스킬 피해': 'Special Skill damage',
    '궁극기 피해': 'Ultimate damage',
    '패시브 스킬 피해': 'Passive Ability damage',
    '기본 공격 피해': 'Basic Attack damage',
    '방어력 %': 'DEF',
    '회복량 %': 'Healing',
    '회복량%': 'Healing',
    '보호막': 'Shield',
    '보호막 %': 'Shield',
    '보막': 'Shield',
    '보막 %': 'Shield',
    '스탯 미상': 'Stat: unknown'
};

function csTranslateStatName(name) {
    const en = (typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en');
    if (!en) return name;
    return CS_STAT_NAME_EN[name] || name;
}

function cookieSimStatChipText(stats) {
    const en = (typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en');
    if (!stats) return en ? 'Stat: unknown' : '스탯 미상';
    const names = Object.keys(stats).filter(n => stats[n] > 0).sort((a, b) => stats[b] - stats[a]);
    if (!names.length) return en ? 'Stat: unknown' : '스탯 미상';
    if (names.length === 1) return csTranslateStatName(names[0]);
    return names.map(n => `${csTranslateStatName(n)} ×${stats[n]}`).join(' · ');
}

function cookieSimMakeStatChip(stats) {
    const chip = document.createElement('div');
    const chipBg = CS_DARK_UI ? '#303236' : '#fff';
    const chipText = CS_DARK_UI ? '#f3f4f6' : '#6b7280';
    chip.classList.add('cs-modal-stat-chip');
    chip.textContent = cookieSimStatChipText(stats);
    chip.style.width = '100%';
    chip.style.height = '22px';
    chip.style.minHeight = '22px';
    chip.style.maxHeight = '22px';
    chip.style.background = chipBg;
    chip.style.border = 'none';
    chip.style.borderRadius = '6px';
    chip.style.padding = '4px 2px';
    chip.style.boxSizing = 'border-box';
    chip.style.display = 'flex';
    chip.style.alignItems = 'center';
    chip.style.justifyContent = 'center';
    chip.style.textAlign = 'center';
    chip.style.fontSize = '10px';
    chip.style.fontWeight = '800';
    chip.style.lineHeight = '14px';
    chip.style.color = chipText;
    chip.style.whiteSpace = 'nowrap';
    chip.style.overflow = 'hidden';
    chip.style.textOverflow = 'ellipsis';
    chip.style.boxShadow = 'none';
    chip.style.margin = '0';
    return chip;
}

function csStatNamesForEditor() {
    const names = Array.isArray(CS_STAT_COLOR_REFS) ? CS_STAT_COLOR_REFS.map(ref => ref.name) : [];
    return [...new Set(names.filter(Boolean))];
}

function csExpandStatsForEditor(stats, count) {
    const n = Math.max(1, Math.min(99, parseInt(count || 1, 10) || 1));
    const arr = [];
    if (stats) {
        Object.entries(stats)
            .filter(([, statCount]) => (Number(statCount) || 0) > 0)
            .forEach(([statName, statCount]) => {
                const c = Math.max(0, parseInt(statCount, 10) || 0);
                for (let i = 0; i < c; i++) arr.push(statName);
            });
    }
    const fallback = arr[0] || '';
    while (arr.length < n) arr.push(fallback);
    return arr.slice(0, n);
}

function csStatsFromEditorSelections(values) {
    const stats = {};
    (values || []).forEach(name => {
        if (!name) return;
        stats[name] = (stats[name] || 0) + 1;
    });
    return Object.keys(stats).length ? stats : null;
}

function csResizeStatsForCount(stats, count) {
    return csStatsFromEditorSelections(csExpandStatsForEditor(stats, count));
}

function csOpenStatEditor(currentStats, count, onSave) {
    const en = (typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en');
    const statNames = csStatNamesForEditor();
    const selectedValues = csExpandStatsForEditor(currentStats, count);

    const modal = document.createElement('div');
    modal.className = 'cs-stat-editor-modal';
    modal.style.position = 'fixed';
    modal.style.zIndex = '2000';
    modal.style.left = '0';
    modal.style.top = '0';
    modal.style.width = '100%';
    modal.style.height = '100%';
    modal.style.background = 'rgba(0,0,0,0.55)';
    modal.style.display = 'flex';
    modal.style.alignItems = 'center';
    modal.style.justifyContent = 'center';

    const box = document.createElement('div');
    box.className = 'cs-stat-editor-box';
    box.style.width = 'min(520px, 92vw)';
    box.style.maxHeight = '88dvh';
    box.style.overflowY = 'auto';
    box.style.overflowX = 'visible';
    box.style.background = CS_DARK_UI ? '#303236' : '#fff';
    box.style.borderRadius = '15px';
    box.style.padding = '18px';
    box.style.boxShadow = '0 18px 50px rgba(0,0,0,0.28)';
    box.style.boxSizing = 'border-box';

    const modalTextColor = CS_DARK_UI ? '#f3f4f6' : '#374151';
    const modalSubTextColor = CS_DARK_UI ? '#f3f4f6' : '#374151';

    const title = document.createElement('div');
    title.textContent = en ? 'Edit shard stat' : '조각 스탯 수정';
    title.style.fontWeight = '800';
    title.style.fontSize = '13px';
    title.style.marginBottom = '6px';
    title.style.color = modalTextColor;
    box.appendChild(title);

    const desc = document.createElement('div');
    desc.className = 'cs-stat-editor-desc';
    desc.textContent = en ? 'If there are multiple shards with the same shape, choose stats for each one in order below.' : '같은 모양 조각이 여러 개면 아래에서 순서대로 스탯을 따로 고를 수 있어요.';
    desc.style.fontSize = '12px';
    desc.style.fontWeight = '400';
    desc.style.color = modalSubTextColor;
    desc.style.marginBottom = '4px';
    desc.style.textAlign = 'left';
    desc.style.lineHeight = '1.6';
    box.appendChild(desc);

    const statDropdowns = [];
    const closeStatDropdowns = (except = null) => {
        statDropdowns.forEach(info => {
            if (!info || info === except) return;
            info.close();
        });
    };

    const makeSelect = (value) => {
        const select = document.createElement('select');
        select.dataset.csNativeSelectSkip = 'true';
        select.style.display = 'none';

        const unknown = document.createElement('option');
        unknown.value = '';
        unknown.textContent = en ? 'Stat: unknown' : '스탯 미상';
        select.appendChild(unknown);

        statNames.forEach(name => {
            const option = document.createElement('option');
            option.value = name;
            option.textContent = csTranslateStatName(name);
            select.appendChild(option);
        });
        select.value = value || '';

        const wrap = document.createElement('div');
        wrap.className = 'cs-modal-select-wrap';
        wrap.style.width = '100%';
        wrap.style.position = 'relative';
        wrap.style.boxSizing = 'border-box';

        const btn = document.createElement('button');
        btn.type = 'button';
        btn.textContent = select.options[select.selectedIndex]?.textContent || unknown.textContent;
        btn.style.width = '100%';
        btn.style.height = '38px';
        btn.style.padding = '0 34px 0 12px';
        btn.style.borderRadius = '8px';
        btn.style.border = 'none';
        btn.style.background = CS_DARK_UI ? '#3a3d42' : '#d1d5db';
        btn.style.color = CS_DARK_UI ? '#f3f4f6' : '#111827';
        btn.style.fontSize = '10px';
        btn.style.fontWeight = '800';
        btn.style.fontFamily = 'Arial, sans-serif';
        btn.style.textAlign = 'left';
        btn.style.lineHeight = '38px';
        btn.style.cursor = 'pointer';
        btn.style.boxShadow = 'none';
        btn.style.boxSizing = 'border-box';
        btn.style.position = 'relative';

        const arrow = document.createElement('span');
        arrow.style.position = 'absolute';
        arrow.style.right = '16px';
        arrow.style.top = '50%';
        arrow.style.width = '6px';
        arrow.style.height = '6px';
        arrow.style.borderRight = `2px solid ${CS_DARK_UI ? '#cbd5e1' : '#6b7280'}`;
        arrow.style.borderBottom = `2px solid ${CS_DARK_UI ? '#cbd5e1' : '#6b7280'}`;
        arrow.style.transform = 'translateY(-65%) rotate(45deg)';
        arrow.style.pointerEvents = 'none';
        btn.appendChild(arrow);

        // 스탯 수정 드롭다운은 흰색 수정창 안쪽 흐름에 포함된다.
        // 예전 fixed backdrop은 모바일에서 버튼 터치 직후 click 이벤트를 가로채
        // 드롭다운이 바로 닫히거나 여러 번 눌러야 열리는 문제가 생겨 제거한다.
        const menuBackdrop = null;

        const menu = document.createElement('div');
        menu.className = 'cs-stat-edit-menu';
        menu.style.display = 'none';
        menu.style.position = 'relative';
        menu.style.zIndex = '2147483647';
        menu.style.background = CS_DARK_UI ? '#303236' : '#ffffff';
        menu.style.color = CS_DARK_UI ? '#f3f4f6' : '#374151';
        menu.style.border = '0';
        menu.style.borderRadius = '8px';
        menu.style.marginTop = '4px';
        menu.style.boxShadow = 'none';
        menu.style.overflowY = 'auto';
        menu.style.overflowX = 'hidden';
        menu.style.padding = '6px 0';
        menu.style.boxSizing = 'border-box';
        menu.style.maxHeight = '190px';
        menu.style.touchAction = 'pan-y';
        menu.style.overscrollBehavior = 'contain';
        menu.style.webkitOverflowScrolling = 'touch';

        const items = Array.from(select.options).map(opt => {
            const item = document.createElement('button');
            item.type = 'button';
            item.textContent = opt.textContent;
            item.dataset.value = opt.value;
            item.style.display = 'block';
            item.style.width = '100%';
            item.style.padding = '9px 12px';
            item.style.border = 'none';
            item.style.background = CS_DARK_UI ? '#303236' : '#ffffff';
            item.style.color = CS_DARK_UI ? '#f3f4f6' : '#374151';
            item.style.fontSize = '12px';
            item.style.fontWeight = '700';
            item.style.textAlign = 'left';
            item.style.lineHeight = '1.25';
            item.style.cursor = 'pointer';
            item.style.boxShadow = 'none';
            item.style.boxSizing = 'border-box';
            item.style.touchAction = 'pan-y';
            item.addEventListener('mouseenter', () => {
                item.style.background = CS_DARK_UI ? '#303236' : '#ffffff';
                item.style.color = '#ff4048';
                item.style.fontWeight = '800';
            });
            item.addEventListener('mouseleave', () => {
                item.style.background = CS_DARK_UI ? '#303236' : '#ffffff';
                item.style.color = CS_DARK_UI ? '#f3f4f6' : '#374151';
                item.style.fontWeight = '700';
            });
            let touchStartX = 0;
            let touchStartY = 0;
            let touchMoved = false;
            const chooseItem = (event) => {
                if (event) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                select.value = opt.value;
                btn.childNodes[0].nodeValue = opt.textContent;
                syncActive();
                closeInfo.close();
                // 실제 조각 스탯 반영은 아래 '저장' 버튼을 눌렀을 때만 수행한다.
            };
            item.addEventListener('pointerdown', (event) => {
                event.stopPropagation();
                touchStartX = event.clientX || 0;
                touchStartY = event.clientY || 0;
                touchMoved = false;
            });
            item.addEventListener('pointermove', (event) => {
                const dx = Math.abs((event.clientX || 0) - touchStartX);
                const dy = Math.abs((event.clientY || 0) - touchStartY);
                if (dx > 6 || dy > 6) touchMoved = true;
            });
            item.addEventListener('pointerup', (event) => {
                if (!touchMoved) chooseItem(event);
            });
            item.addEventListener('pointercancel', () => {
                touchMoved = true;
            });
            menu.appendChild(item);
            return item;
        });

        const syncActive = () => {
            items.forEach(item => {
                const active = item.dataset.value === select.value;
                item.style.fontWeight = active ? '800' : '700';
                item.style.color = active ? (CS_DARK_UI ? '#ffffff' : '#111827') : (CS_DARK_UI ? '#f3f4f6' : '#374151');
            });
        };

        const positionMenu = () => {
            // 모바일에서 흰색 수정창 밖으로 나간 드롭다운 항목은 터치가 막힐 수 있어서
            // 스탯 수정 드롭다운은 수정창 안쪽 흐름에 포함시키고, 목록 내부만 스크롤되게 둔다.
            menu.style.left = '0px';
            menu.style.top = 'auto';
            menu.style.bottom = 'auto';
            menu.style.width = '100%';
            menu.style.right = 'auto';
            menu.style.maxHeight = '190px';
            menu.style.marginTop = '0';
            menu.style.borderRadius = '8px';
        menu.style.marginTop = '4px';
        };

        const outsideHandler = (event) => {
            if (menu.contains(event.target) || wrap.contains(event.target)) return;
            closeInfo.close();
        };
        const closeInfo = {
            close: () => {
                menu.style.display = 'none';
                if (menuBackdrop) menuBackdrop.style.display = 'none';
                document.removeEventListener('pointerdown', outsideHandler, true);
            },
            destroy: () => {
                document.removeEventListener('pointerdown', outsideHandler, true);
                if (menu.parentNode) menu.parentNode.removeChild(menu);
                if (menuBackdrop && menuBackdrop.parentNode) menuBackdrop.parentNode.removeChild(menuBackdrop);
            }
        };
        statDropdowns.push(closeInfo);

        // fixed backdrop 없음: 드롭다운/버튼/수정창 내부 터치는 자체 처리하고,
        // 바깥 터치만 outsideHandler에서 닫는다.
        menu.addEventListener('pointerdown', (event) => event.stopPropagation());
        menu.addEventListener('click', (event) => event.stopPropagation());

        const toggleMenu = (event) => {
            if (event) {
                event.preventDefault();
                event.stopPropagation();
                if (event.stopImmediatePropagation) event.stopImmediatePropagation();
            }
            const willOpen = menu.style.display !== 'block';
            closeStatDropdowns(closeInfo);
            if (!willOpen) {
                closeInfo.close();
                return;
            }
            if (menuBackdrop) menuBackdrop.style.display = 'block';
            menu.style.display = 'block';
            syncActive();
            positionMenu();
            document.removeEventListener('pointerdown', outsideHandler, true);
            setTimeout(() => document.addEventListener('pointerdown', outsideHandler, true), 0);
        };
        btn.addEventListener('pointerdown', (event) => {
            // 모바일에서 pointerdown에 바로 열면 이어지는 click/투명막 이벤트로
            // 즉시 닫히는 경우가 있어서 여기서는 전파만 막고 실제 토글은 click에서 처리한다.
            event.stopPropagation();
        });
        btn.addEventListener('click', toggleMenu);
        wrap.appendChild(select);
        wrap.appendChild(btn);
        if (menuBackdrop) wrap.appendChild(menuBackdrop);
        wrap.appendChild(menu);
        select.__csStatDropdownWrap = wrap;
        select.__csStatDropdownDestroy = closeInfo.destroy;
        return select;
    };

    const rows = document.createElement('div');
    rows.className = 'cs-stat-editor-rows';
    rows.style.display = 'flex';
    rows.style.flexDirection = 'column';
    rows.style.gap = '4px';
    rows.style.marginTop = '0px';
    const rowSelects = [];

    selectedValues.forEach((value) => {
        const row = document.createElement('div');
        row.style.display = 'block';

        const select = makeSelect(value);
        rowSelects.push(select);
        row.appendChild(select.__csStatDropdownWrap || select);
        rows.appendChild(row);
    });
    box.appendChild(rows);

    const buttons = document.createElement('div');
    buttons.style.display = 'flex';
    buttons.style.gap = '10px';
    buttons.style.marginTop = '8px';
    buttons.style.position = 'sticky';
    buttons.style.bottom = '0';
    buttons.style.background = CS_DARK_UI ? '#303236' : '#fff';
    buttons.style.paddingTop = '6px';

    const saveBtn = document.createElement('button');
    saveBtn.textContent = en ? 'Save' : '저장';
    saveBtn.style.flex = '1';
    saveBtn.style.padding = '12px';
    saveBtn.style.fontSize = '1em';
    saveBtn.style.fontWeight = 'bold';
    saveBtn.style.border = 'none';
    saveBtn.style.borderRadius = '8px';
    saveBtn.style.cursor = 'pointer';
    saveBtn.style.background = '#ff4048';
    saveBtn.style.color = 'white';
    saveBtn.addEventListener('click', () => {
        const values = rowSelects.map(sel => sel.value || '');
        const nextStats = csStatsFromEditorSelections(values);
        if (typeof onSave === 'function') onSave(nextStats);
        statDropdowns.forEach(info => info && info.destroy && info.destroy());
        document.body.removeChild(modal);
    });

    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = en ? 'Cancel' : '취소';
    cancelBtn.style.flex = '1';
    cancelBtn.style.padding = '12px';
    cancelBtn.style.fontSize = '1em';
    cancelBtn.style.fontWeight = 'bold';
    cancelBtn.style.border = 'none';
    cancelBtn.style.borderRadius = '8px';
    cancelBtn.style.cursor = 'pointer';
    cancelBtn.style.background = '#e5e7eb';
    cancelBtn.style.color = '#666';
    cancelBtn.addEventListener('click', () => {
        statDropdowns.forEach(info => info && info.destroy && info.destroy());
        document.body.removeChild(modal);
    });

    buttons.appendChild(saveBtn);
    buttons.appendChild(cancelBtn);
    box.appendChild(buttons);

    modal.appendChild(box);
    document.body.appendChild(modal);
    modal.addEventListener('click', (ev) => {
        if (ev.target === modal) {
            statDropdowns.forEach(info => info && info.destroy && info.destroy());
            document.body.removeChild(modal);
        }
    });
}

function cookieSimMakeEditableStatChip(stats, getCount, onChange) {
    const chip = cookieSimMakeStatChip(stats);
    const en = (typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en');
    chip.style.cursor = 'pointer';
    chip.style.border = 'none';
    chip.style.background = CS_DARK_UI ? '#303236' : '#fff';
    chip.title = en ? 'Click to edit stat' : '클릭해서 스탯 수정';
    chip.addEventListener('click', (ev) => {
        ev.stopPropagation();
        const count = Math.max(1, Math.min(99, parseInt(typeof getCount === 'function' ? getCount() : 1, 10) || 1));
        csOpenStatEditor(stats, count, (nextStats) => {
            stats = nextStats;
            chip.textContent = cookieSimStatChipText(nextStats);
            if (typeof onChange === 'function') onChange(nextStats);
        });
    });
    return chip;
}

// { `${setKey}-${pieceName}-${grade}`: { statName: count } } — 세트 선택까지 반영한 실제 스탯 분포
const CS_PIECE_STAT_COUNTS = {};
if (typeof window !== 'undefined') window.COOKIE_SIM_PIECE_STAT_COUNTS = CS_PIECE_STAT_COUNTS;

function csClearPieceStatCounts() {
    Object.keys(CS_PIECE_STAT_COUNTS).forEach(k => delete CS_PIECE_STAT_COUNTS[k]);
}

function csAddPieceStatCounts(statKey, stats, countLimit = null) {
    if (!statKey || !stats) return;
    let remain = countLimit === null ? Infinity : Math.max(0, Number(countLimit) || 0);
    if (remain <= 0) return;
    CS_PIECE_STAT_COUNTS[statKey] = CS_PIECE_STAT_COUNTS[statKey] || {};
    Object.entries(stats)
        .filter(([, statCount]) => (Number(statCount) || 0) > 0)
        .sort((a, b) => (Number(b[1]) || 0) - (Number(a[1]) || 0))
        .forEach(([statName, statCount]) => {
            if (remain <= 0) return;
            const n = Math.min(Number(statCount) || 0, remain);
            if (n <= 0) return;
            CS_PIECE_STAT_COUNTS[statKey][statName] = (CS_PIECE_STAT_COUNTS[statKey][statName] || 0) + n;
            remain -= n;
        });
}

// 새로운 이미지 기반 조각 인식 시스템 (OCR 제거)
async function recognizePiecesWithCV(file) {
    // 1. 이미지 로드
    const img = new Image();
    await new Promise(resolve => {
        img.onload = resolve;
        img.src = URL.createObjectURL(file);
    });

    // 2. OpenCV Mat으로 변환
    const src = cv.imread(img);
    const gray = new cv.Mat();
    cv.cvtColor(src, gray, cv.COLOR_RGBA2GRAY);

    // 3. 조각 박스 감지
    const boxes = detectPieceBoxes(src, gray, img);

    if (boxes.length === 0) {
        src.delete();
        gray.delete();
        URL.revokeObjectURL(img.src);
        return [];
    }

    // ===== 디버그 데이터 수집 =====
    // 각 조각의 처리 과정을 시각화하기 위한 데이터 (원본, 처리된 이미지, 그리드 분석)
    // 주의: 데이터는 수집되지만 모달은 표시되지 않음 (GitHub Pages 배포용)
    const debugData = [];

    // 4. 각 박스에서 조각 패턴 추출 및 매칭
    const pieceCounts = {}; // { pieceName-grade: count }
    const pieceStatByKey = {}; // { pieceName-grade: { statName: count } } — 이 파일에서 분류된 스탯
    const failedPieces = []; // 매칭 실패한 조각들

    for (let i = 0; i < boxes.length; i++) {
        const box = boxes[i];

        // 배경색으로 등급 판별 (파란색=rare, 보라색=epic, 빨간색/노란색=super)
        let { grade, bgColor } = detectGradeFromBox(src, box);

        // 그리드 분석으로 조각 모양 추출 + 디버그용 캔버스 생성
        const { shape: extractedShape, hasGreenTag, matchScore, debug } = extractShapeFromImageWithDebug(src, box, bgColor, i, grade);

        // 추출한 모양으로 조각 이름 찾기 (템플릿 매칭)
        const pieceName = findPieceNameByShape(extractedShape);
        if (pieceName && UNIQUE_PIECE_TEMPLATES[pieceName]) {
            grade = 'unique';
        }

        // 디버그 정보에 인식 결과 추가
        debug.info += `\n결과: ${pieceName ? ` ${pieceName} (${grade})` : ' 인식 실패'}`;
        debug.info += `\n추출된 shape: ${JSON.stringify(extractedShape)}`;
        debugData.push(debug);

        // 조각 내부 색상으로 스탯(설탕유리 종류) 분류해 기록
        const statName = csSampleStatFromBox(src, box, bgColor, extractedShape);

        // 장착중 태그는 모양 일부를 가릴 수 있으므로 신뢰도가 충분한 경우에만 자동 확정한다.
        // 신뢰도가 낮거나 모양을 찾지 못한 조각만 기존 확인 목록으로 보낸다.
        const taggedMatchIsReliable = !hasGreenTag ||
            (Number.isFinite(matchScore) && matchScore >= 0.40);
        if (!pieceName || !taggedMatchIsReliable) {
            failedPieces.push({
                grade: grade,
                debug: debug,
                box: box,
                shape: extractedShape,
                hasGreenTag: hasGreenTag || false,
                pieceName: pieceName || null,
                matchScore: Number.isFinite(matchScore) ? matchScore : null,
                stats: statName ? { [statName]: 1 } : null
            });
        } else {
            const key = `${pieceName}-${grade}`;
            pieceCounts[key] = (pieceCounts[key] || 0) + 1;
            if (statName) {
                // 이 단계에서는 아직 사진별 세트를 선택하기 전이라 전역 풀에는 넣지 않는다.
                // 실제 스탯 풀은 '모든 사진 확인' 시 selectedSet까지 포함한 키로 다시 만든다.
                pieceStatByKey[key] = pieceStatByKey[key] || {};
                pieceStatByKey[key][statName] = (pieceStatByKey[key][statName] || 0) + 1;
            }
        }
    }

    // 5. 결과를 배열로 변환
    const result = [];
    for (const [key, count] of Object.entries(pieceCounts)) {
        // 마지막 '-'를 기준으로 조각 이름과 등급 분리
        const lastDashIndex = key.lastIndexOf('-');
        const pieceName = key.substring(0, lastDashIndex);
        const grade = key.substring(lastDashIndex + 1);
        result.push({
            pieceName: pieceName,
            grade: grade,
            count: count,
            stats: pieceStatByKey[key] || null
        });
    }
    
    // 매칭 실패한 조각들도 결과에 포함
    if (failedPieces.length > 0) {
        result.push({
            pieceName: null, // 매칭 실패 표시
            grade: null,
            count: failedPieces.length,
            failedPieces: failedPieces // 원본 이미지 정보 포함
        });
    }

    // ===== 디버그 모달 표시 =====
    // 각 조각의 처리 과정을 시각화한 모달 창 표시
    // (원본 이미지, 배경 제거된 이미지, 그리드 분석 결과)
    // showDebugModal(debugData); // 디버그 모달 비활성화

    // 6. 메모리 정리
    src.delete();
    gray.delete();
    URL.revokeObjectURL(img.src);

    return result;
}

// 조각 박스 감지
function csRectIoU(a, b) {
    const x0 = Math.max(a.x, b.x);
    const y0 = Math.max(a.y, b.y);
    const x1 = Math.min(a.x + a.width, b.x + b.width);
    const y1 = Math.min(a.y + a.height, b.y + b.height);
    const intersection = Math.max(0, x1 - x0) * Math.max(0, y1 - y0);
    if (intersection <= 0) return 0;
    const union = a.width * a.height + b.width * b.height - intersection;
    return union > 0 ? intersection / union : 0;
}

function csChooseRepeatedCardBoxes(candidates) {
    if (!candidates || candidates.length <= 1) return candidates || [];
    let bestGroup = [];
    candidates.forEach((candidate) => {
        const group = candidates.filter((other) => (
            Math.abs(other.width - candidate.width) <= Math.max(8, candidate.width * 0.18) &&
            Math.abs(other.height - candidate.height) <= Math.max(8, candidate.height * 0.18)
        ));
        if (group.length > bestGroup.length) bestGroup = group;
    });
    if (bestGroup.length < 2) return candidates;
    const medianWidth = csMedianNumber(bestGroup.map((item) => item.width));
    const medianHeight = csMedianNumber(bestGroup.map((item) => item.height));
    return candidates.filter((candidate) => (
        Math.abs(candidate.width - medianWidth) <= Math.max(8, medianWidth * 0.16) &&
        Math.abs(candidate.height - medianHeight) <= Math.max(8, medianHeight * 0.16)
    ));
}

function csDetectColoredCardBoxes(src) {
    const rows = src.rows;
    const cols = src.cols;
    const mask = cv.Mat.zeros(rows, cols, cv.CV_8UC1);
    for (let y = 0; y < rows; y++) {
        for (let x = 0; x < cols; x++) {
            const pixel = src.ucharPtr(y, x);
            const r = pixel[0], g = pixel[1], b = pixel[2];
            const maximum = Math.max(r, g, b);
            const minimum = Math.min(r, g, b);
            const brightness = (r + g + b) / 3;
            const chroma = maximum - minimum;
            const greenTag = g > 125 && g > r + 25 && g > b + 25;
            const cardColor = (brightness > 98 && chroma > 18) || brightness > 188;
            if (cardColor && !greenTag) mask.ucharPtr(y, x)[0] = 255;
        }
    }

    const closeSize = csOddKernelSize(Math.min(rows, cols) * 0.0015, 3, 9);
    const closeKernel = cv.getStructuringElement(cv.MORPH_RECT, new cv.Size(closeSize, closeSize));
    const smallKernel = cv.getStructuringElement(cv.MORPH_RECT, new cv.Size(3, 3));
    cv.morphologyEx(mask, mask, cv.MORPH_CLOSE, closeKernel);
    cv.morphologyEx(mask, mask, cv.MORPH_OPEN, smallKernel);
    closeKernel.delete();
    smallKernel.delete();

    const contours = new cv.MatVector();
    const hierarchy = new cv.Mat();
    const contourInput = mask.clone();
    cv.findContours(contourInput, contours, hierarchy, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE);
    contourInput.delete();
    const imageArea = rows * cols;
    const candidates = [];
    for (let i = 0; i < contours.size(); i++) {
        const rect = cv.boundingRect(contours.get(i));
        const rectArea = rect.width * rect.height;
        const ratio = rectArea / Math.max(1, imageArea);
        const aspect = rect.width / Math.max(1, rect.height);
        if (ratio < 0.0025 || ratio > 0.06) continue;
        if (aspect < 0.45 || aspect > 1.8) continue;
        if (rect.width < cols * 0.035 || rect.height < rows * 0.05) continue;
        const roi = mask.roi(new cv.Rect(rect.x, rect.y, rect.width, rect.height));
        const fillRatio = cv.countNonZero(roi) / Math.max(1, rectArea);
        roi.delete();
        if (fillRatio < 0.24) continue;
        candidates.push({ x: rect.x, y: rect.y, width: rect.width, height: rect.height });
    }
    contours.delete();
    hierarchy.delete();
    mask.delete();
    return csChooseRepeatedCardBoxes(candidates);
}

function detectPieceBoxes(src, gray, img) {
    // ===== 1단계: 녹색 "장착중" 태그 영역 마스킹 =====
    const greenLower = new cv.Mat(src.rows, src.cols, src.type(),
        [Math.max(0, 82 - 35), Math.max(0, 206 - 35), Math.max(0, 50 - 35), 0]);
    const greenUpper = new cv.Mat(src.rows, src.cols, src.type(),
        [Math.min(255, 82 + 35), Math.min(255, 206 + 35), Math.min(255, 50 + 35), 255]);

    const greenMask = new cv.Mat();
    cv.inRange(src, greenLower, greenUpper, greenMask);

    greenLower.delete();
    greenUpper.delete();

    // 녹색 마스크 팽창 (외곽선까지 포함하도록)
    const kernel = cv.getStructuringElement(cv.MORPH_RECT, new cv.Size(3, 20)); // 세로로 10픽셀 팽창
    const expandedGreenMask = new cv.Mat();
    cv.dilate(greenMask, expandedGreenMask, kernel);
    kernel.delete();
    greenMask.delete();

    // 팽창된 녹색 영역을 그레이스케일에서 검은색으로 칠하기
    const maskedGray = gray.clone();
    for (let y = 0; y < expandedGreenMask.rows; y++) {
        for (let x = 0; x < expandedGreenMask.cols; x++) {
            if (expandedGreenMask.ucharPtr(y, x)[0] > 128) {
                maskedGray.ucharPtr(y, x)[0] = 0; // 검은색 (녹색 영역 + 외곽선 제거)
            }
        }
    }

    expandedGreenMask.delete();

    console.log('녹색 "장착중" 태그 영역 제거 완료');

    // ===== 2단계: 이진화 (녹색 제거된 이미지로) =====
    const binary = new cv.Mat();
    cv.threshold(maskedGray, binary, 128, 255, cv.THRESH_BINARY);

    maskedGray.delete();

    // ===== 3단계: 윤곽선 검출 =====
    const contours = new cv.MatVector();
    const hierarchy = new cv.Mat();
    cv.findContours(binary, contours, hierarchy, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE);

    // 조각 박스 필터링
    const minArea = (img.width / 20) * (img.height / 20); // 최소 면적
    const maxArea = (img.width / 5) * (img.height / 5);   // 최대 면적

    const boxes = [];
    for (let i = 0; i < contours.size(); i++) {
        const contour = contours.get(i);
        const area = cv.contourArea(contour);

        if (area > minArea && area < maxArea) {
            const rect = cv.boundingRect(contour);

            // 종횡비 확인 (조각 박스는 대략 정사각형)
            const aspectRatio = rect.width / rect.height;
            if (aspectRatio > 0.5 && aspectRatio < 2.0) {
                boxes.push(rect);
            }
        }
    }

    // 고정 명도 이진화가 최신 카드 색상/압축률에서 일부 카드를 놓칠 경우,
    // 반복되는 컬러 카드 사각형을 이용해 누락된 박스를 보완한다.
    const colorBoxes = csDetectColoredCardBoxes(src);
    // 최신 인벤토리 화면은 카드 색상이 반복되는 구조라 컬러 카드 검출이 더 안정적이다.
    // 명도 윤곽선 검출은 카드 내부의 밝은 조각이나 UI를 카드로 오인할 수 있으므로,
    // 반복 카드가 2개 이상 잡히면 컬러 카드 좌표를 우선 사용한다.
    if (colorBoxes.length >= 2) {
        boxes.length = 0;
        colorBoxes.forEach((candidate) => boxes.push(candidate));
    } else {
        colorBoxes.forEach((candidate) => {
            if (!boxes.some((existing) => csRectIoU(existing, candidate) >= 0.55)) {
                boxes.push(candidate);
            }
        });
    }

    // 카드가 한 줄인지 여러 줄인지 이미지 전체 높이로 판단하면,
    // 두 번째 줄과 첫 번째 줄의 간격이 화면 높이에 비해 작을 때 한 줄로 오인한다.
    // 카드 자체 높이를 기준으로 Y 중심을 행 단위로 묶어 위→아래, 왼쪽→오른쪽 순으로 정렬한다.
    if (boxes.length > 0) {
        const medianCardHeight = csMedianNumber(boxes.map((box) => box.height));
        const rowTolerance = Math.max(8, medianCardHeight * 0.42);
        const sortedByCenterY = boxes.slice().sort((a, b) => {
            const centerDiff = (a.y + a.height / 2) - (b.y + b.height / 2);
            if (Math.abs(centerDiff) > 1) return centerDiff;
            return a.x - b.x;
        });
        const cardRows = [];

        sortedByCenterY.forEach((box) => {
            const centerY = box.y + box.height / 2;
            let targetRow = null;
            let closestDistance = Infinity;

            cardRows.forEach((row) => {
                const distance = Math.abs(centerY - row.centerY);
                if (distance <= rowTolerance && distance < closestDistance) {
                    targetRow = row;
                    closestDistance = distance;
                }
            });

            if (!targetRow) {
                targetRow = { boxes: [], centerY };
                cardRows.push(targetRow);
            }

            targetRow.boxes.push(box);
            targetRow.centerY = csMedianNumber(
                targetRow.boxes.map((item) => item.y + item.height / 2)
            );
        });

        cardRows.sort((a, b) => a.centerY - b.centerY);
        boxes.length = 0;
        cardRows.forEach((row) => {
            const rowY = Math.round(csMedianNumber(row.boxes.map((box) => box.y)));
            const rowHeight = Math.round(csMedianNumber(row.boxes.map((box) => box.height)));
            row.boxes.sort((a, b) => a.x - b.x).forEach((box) => {
                // 같은 행 안에서 1~2px 정도 발생하는 검출 오차만 정리하고,
                // 서로 다른 행의 Y 좌표는 절대 첫 행 값으로 덮어쓰지 않는다.
                box.y = rowY;
                box.height = rowHeight;
                boxes.push(box);
            });
        });

        console.log('조각 카드 행 감지:', cardRows.map((row) => row.boxes.length));
    }

    // 메모리 정리
    binary.delete();
    contours.delete();
    hierarchy.delete();

    return boxes;
}

// 배경색으로 등급 판별 (배경색도 반환)
function csMedianNumber(values) {
    if (!values || values.length === 0) return 0;
    const sorted = values.slice().sort((a, b) => a - b);
    const middle = Math.floor(sorted.length / 2);
    return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
}

function csRgbDistance(a, b) {
    if (!a || !b) return Infinity;
    const dr = Number(a.r || 0) - Number(b.r || 0);
    const dg = Number(a.g || 0) - Number(b.g || 0);
    const db = Number(a.b || 0) - Number(b.b || 0);
    return Math.sqrt(dr * dr + dg * dg + db * db);
}

function csSamplePatchMedian(src, centerX, centerY, radius) {
    const xs = [];
    const ys = [];
    const zs = [];
    const x0 = Math.max(0, Math.floor(centerX - radius));
    const x1 = Math.min(src.cols - 1, Math.ceil(centerX + radius));
    const y0 = Math.max(0, Math.floor(centerY - radius));
    const y1 = Math.min(src.rows - 1, Math.ceil(centerY + radius));
    for (let y = y0; y <= y1; y++) {
        for (let x = x0; x <= x1; x++) {
            const pixel = src.ucharPtr(y, x);
            xs.push(pixel[0]);
            ys.push(pixel[1]);
            zs.push(pixel[2]);
        }
    }
    if (!xs.length) return null;
    return { r: csMedianNumber(xs), g: csMedianNumber(ys), b: csMedianNumber(zs) };
}

function csIsGreenTagColor(color) {
    if (!color) return false;
    const r = Number(color.r || 0);
    const g = Number(color.g || 0);
    const b = Number(color.b || 0);
    const targetDistance = csRgbDistance(color, { r: 82, g: 206, b: 50 });
    return targetDistance <= 80 || (g > 120 && g > r + 25 && g > b + 25);
}

function csEstimateCardBackground(src, box) {
    // 카드 테두리 바로 옆은 어두운 외곽선이라 등급색으로 사용할 수 없다.
    // 조각이 거의 닿지 않는 카드 안쪽 양옆/하단을 여러 곳 샘플링한 뒤,
    // 가장 많이 모이는 색상 군집의 중앙값을 카드 배경색으로 사용한다.
    const points = [
        [0.12, 0.28], [0.88, 0.28],
        [0.10, 0.50], [0.90, 0.50],
        [0.12, 0.74], [0.88, 0.74],
        [0.18, 0.88], [0.82, 0.88]
    ];
    const radius = Math.max(2, Math.round(Math.min(box.width, box.height) * 0.025));
    const samples = [];

    points.forEach(([fx, fy]) => {
        const sample = csSamplePatchMedian(
            src,
            box.x + box.width * fx,
            box.y + box.height * fy,
            radius
        );
        if (!sample) return;
        const brightness = (sample.r + sample.g + sample.b) / 3;
        if (brightness < 65 || csIsGreenTagColor(sample)) return;
        samples.push(sample);
    });

    if (!samples.length) {
        const fallback = csSamplePatchMedian(
            src,
            box.x + box.width * 0.12,
            box.y + box.height * 0.62,
            radius
        );
        return fallback || { r: 128, g: 128, b: 128 };
    }

    let bestGroup = [];
    samples.forEach((sample) => {
        const group = samples.filter((candidate) => csRgbDistance(sample, candidate) <= 58);
        if (group.length > bestGroup.length) bestGroup = group;
    });
    const chosen = bestGroup.length ? bestGroup : samples;
    return {
        r: csMedianNumber(chosen.map((item) => item.r)),
        g: csMedianNumber(chosen.map((item) => item.g)),
        b: csMedianNumber(chosen.map((item) => item.b))
    };
}

function csGradeFromCardBackground(bgColor) {
    const references = [
        { grade: 'rare', color: { r: 148, g: 198, b: 249 } },
        { grade: 'epic', color: { r: 216, g: 149, b: 254 } },
        { grade: 'super', color: { r: 254, g: 131, b: 145 } },
        { grade: 'super', color: { r: 248, g: 205, b: 72 } }
    ];
    let best = references[0];
    let bestDistance = Infinity;
    references.forEach((reference) => {
        const distance = csRgbDistance(bgColor, reference.color);
        if (distance < bestDistance) {
            bestDistance = distance;
            best = reference;
        }
    });
    return best.grade;
}

function detectGradeFromBox(src, box) {
    const bgColor = csEstimateCardBackground(src, box);
    return {
        grade: csGradeFromCardBackground(bgColor),
        bgColor
    };
}

// 디버그 버전: 처리 과정 시각화
// OpenCV Mat에서 녹색 태그 offset 감지 (cv.Mat 버전)
function detectGreenTagOffsetFromMat(mat) {
    const maxScanHeight = Math.floor(mat.rows * 0.34);
    let found = false;
    let firstGreenRow = -1;
    let lastGreenRow = -1;
    let blankRows = 0;

    for (let y = 0; y < maxScanHeight; y++) {
        const greenXs = [];
        for (let x = 0; x < mat.cols; x++) {
            const pixel = mat.ucharPtr(y, x);
            const r = pixel[0], g = pixel[1], b = pixel[2];
            const dr = r - 82, dg = g - 206, db = b - 50;
            const nearTagGreen = Math.sqrt(dr * dr + dg * dg + db * db) <= 80;
            const greenDominant = g > 120 && g > r + 25 && g > b + 25;
            if (nearTagGreen || greenDominant) greenXs.push(x);
        }

        let isTagRow = false;
        if (greenXs.length > 0 && mat.cols > 0) {
            const span = greenXs[greenXs.length - 1] - greenXs[0] + 1;
            let longestRun = 1;
            let currentRun = 1;
            for (let i = 1; i < greenXs.length; i++) {
                if (greenXs[i] === greenXs[i - 1] + 1) {
                    currentRun++;
                    if (currentRun > longestRun) longestRun = currentRun;
                } else {
                    currentRun = 1;
                }
            }
            const countRatio = greenXs.length / mat.cols;
            const spanRatio = span / mat.cols;
            const density = greenXs.length / Math.max(1, span);
            const longestRunRatio = longestRun / mat.cols;
            // 장착중 태그는 넓고 연속된 초록 띠다. 조각 모서리의 작은 초록 장식은 제외한다.
            isTagRow = countRatio >= 0.10 && spanRatio >= 0.24 &&
                density >= 0.45 && longestRunRatio >= 0.08;
        }

        if (isTagRow) {
            if (!found) firstGreenRow = y;
            found = true;
            lastGreenRow = y;
            blankRows = 0;
        } else if (found) {
            blankRows++;
            if (blankRows >= 5) break;
        }
    }

    if (!found || firstGreenRow < 0 || lastGreenRow - firstGreenRow < 2) return 0;
    const padding = Math.max(2, Math.floor(mat.rows * 0.015));
    return Math.min(lastGreenRow + padding, Math.floor(mat.rows * 0.42));
}

function isCookieSimUniqueGoldBg(bgColor) {
    if (!bgColor) return false;
    const r = Number(bgColor.r) || 0;
    const g = Number(bgColor.g) || 0;
    const b = Number(bgColor.b) || 0;
    // 유니크 설탕유리조각 카드 배경은 노란/금색 계열이다.
    return r > 145 && g > 105 && b < 130 && (r + g) > 300;
}

function matchUniqueTemplateFromBinary(binary, bbox) {
    if (!binary || !bbox || bbox.width <= 0 || bbox.height <= 0) return null;
    let best = null;
    const templates = UNIQUE_PIECE_TEMPLATES || {};

    Object.entries(templates).forEach(([templateName, templateData]) => {
        const templateShape = normalizeShape(templateData.shape || []);
        if (!templateShape.length) return;
        const rows = Math.max(...templateShape.map(p => p[0])) + 1;
        const cols = Math.max(...templateShape.map(p => p[1])) + 1;
        const filled = new Set(templateShape.map(p => `${p[0]},${p[1]}`));
        const cellW = bbox.width / cols;
        const cellH = bbox.height / rows;
        let filledSum = 0, emptySum = 0, filledN = 0, emptyN = 0;

        for (let row = 0; row < rows; row++) {
            for (let col = 0; col < cols; col++) {
                const x0 = Math.max(0, Math.floor(bbox.x + col * cellW + cellW * 0.12));
                const y0 = Math.max(0, Math.floor(bbox.y + row * cellH + cellH * 0.12));
                const x1 = Math.min(binary.cols, Math.ceil(bbox.x + (col + 1) * cellW - cellW * 0.12));
                const y1 = Math.min(binary.rows, Math.ceil(bbox.y + (row + 1) * cellH - cellH * 0.12));
                let white = 0, total = 0;
                for (let y = y0; y < y1; y++) {
                    for (let x = x0; x < x1; x++) {
                        total++;
                        if (binary.ucharPtr(y, x)[0] > 128) white++;
                    }
                }
                const ratio = total > 0 ? white / total : 0;
                if (filled.has(`${row},${col}`)) {
                    filledSum += ratio;
                    filledN++;
                } else {
                    emptySum += ratio;
                    emptyN++;
                }
            }
        }

        const filledAvg = filledN ? filledSum / filledN : 0;
        const emptyAvg = emptyN ? emptySum / emptyN : 0;
        const aspect = bbox.width / Math.max(1, bbox.height);
        const templateAspect = cols / Math.max(1, rows);
        const aspectPenalty = Math.abs(Math.log(Math.max(0.01, aspect / templateAspect))) * 0.08;
        const score = filledAvg - emptyAvg * 0.65 - aspectPenalty;
        if (!best || score > best.score) {
            best = { templateName, shape: templateShape, rows, cols, score, bbox };
        }
    });
    return best;
}

function extractUniqueShapeFromRoiWithDebug(iconRoi, bgColor, index, hasGreenTag = false) {
    const iconW = iconRoi.cols;
    const iconH = iconRoi.rows;
    const rawMask = cv.Mat.zeros(iconH, iconW, cv.CV_8UC1);

    for (let y = 0; y < iconH; y++) {
        for (let x = 0; x < iconW; x++) {
            const pixel = iconRoi.ucharPtr(y, x);
            const r = pixel[0], g = pixel[1], b = pixel[2];
            const brightness = (r + g + b) / 3;
            const maxCh = Math.max(r, g, b);
            const minCh = Math.min(r, g, b);
            const diff = maxCh - minCh;
            const isYellow = r > 140 && g > 100 && b < 145 && r >= g - 70;
            const isGreen = g > 145 && g > r + 35 && g > b + 35;
            const isDarkOutside = r < 80 && g < 95 && b < 115;
            const isWhiteOrBorder = (r > 205 && g > 190 && b > 145) || (diff < 24 && brightness > 150);
            const nearEdge = x < 3 || y < 3 || x >= iconW - 3 || y >= iconH - 3;
            if (!nearEdge && !isYellow && !isGreen && !isDarkOutside && !isWhiteOrBorder && (diff > 25 || brightness < 170)) {
                rawMask.ucharPtr(y, x)[0] = 255;
            }
        }
    }

    const openKernel = cv.getStructuringElement(cv.MORPH_RECT, new cv.Size(2, 2));
    const closeKernel = cv.getStructuringElement(cv.MORPH_RECT, new cv.Size(4, 4));
    cv.morphologyEx(rawMask, rawMask, cv.MORPH_OPEN, openKernel);
    cv.morphologyEx(rawMask, rawMask, cv.MORPH_CLOSE, closeKernel);
    openKernel.delete();
    closeKernel.delete();

    const contours = new cv.MatVector();
    const hierarchy = new cv.Mat();
    cv.findContours(rawMask, contours, hierarchy, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE);

    let chosenIdx = -1;
    let chosenScore = -Infinity;
    const totalArea = iconW * iconH;
    for (let i = 0; i < contours.size(); i++) {
        const contour = contours.get(i);
        const area = cv.contourArea(contour);
        if (area < totalArea * 0.004) continue;
        const rect = cv.boundingRect(contour);
        const touches = rect.x <= 4 || rect.y <= 4 || rect.x + rect.width >= iconW - 4 || rect.y + rect.height >= iconH - 4;
        const tooLarge = rect.width > iconW * 0.86 || rect.height > iconH * 0.86;
        const cx = rect.x + rect.width / 2;
        const cy = rect.y + rect.height / 2;
        const centerPenalty = Math.hypot(cx - iconW / 2, cy - iconH / 2) / Math.max(iconW, iconH);
        let score = area - centerPenalty * area * 0.5;
        if (touches) score *= 0.25;
        if (tooLarge) score *= 0.45;
        if (score > chosenScore) {
            chosenScore = score;
            chosenIdx = i;
        }
    }

    const binary = cv.Mat.zeros(iconH, iconW, cv.CV_8UC1);
    if (chosenIdx >= 0) {
        cv.drawContours(binary, contours, chosenIdx, new cv.Scalar(255), cv.FILLED);
    } else {
        rawMask.copyTo(binary);
    }
    contours.delete();
    hierarchy.delete();
    rawMask.delete();

    let minX = iconW, maxX = 0, minY = iconH, maxY = 0, totalFilled = 0;
    for (let y = 0; y < iconH; y++) {
        for (let x = 0; x < iconW; x++) {
            if (binary.ucharPtr(y, x)[0] > 128) {
                totalFilled++;
                if (x < minX) minX = x;
                if (x > maxX) maxX = x;
                if (y < minY) minY = y;
                if (y > maxY) maxY = y;
            }
        }
    }

    if (totalFilled === 0) {
        return { shape: [], binary, gridInfo: '유니크 그리드: 0x0\n', dots: [], gridSizeX: 0, gridSizeY: 0, matchScore: null };
    }

    const bbox = { x: minX, y: minY, width: maxX - minX + 1, height: maxY - minY + 1 };
    const match = matchUniqueTemplateFromBinary(binary, bbox);
    if (!match || match.score < 0.01) {
        return { shape: [], binary, gridInfo: `유니크 매칭 실패\n총 픽셀: ${totalFilled}\n`, dots: [], gridSizeX: 0, gridSizeY: 0, matchScore: match ? match.score : null };
    }

    const dots = [];
    const cellW = bbox.width / match.cols;
    const cellH = bbox.height / match.rows;
    match.shape.forEach(([row, col]) => {
        dots.push({
            x: bbox.x + (col + 0.5) * cellW,
            y: bbox.y + (row + 0.5) * cellH,
            area: cellW * cellH
        });
    });

    const gridInfo = `유니크 그리드: ${match.cols}x${match.rows}\n템플릿: ${match.templateName}\n점수: ${match.score.toFixed(3)}\n총 픽셀: ${totalFilled}\n`;
    return { shape: match.shape, binary, gridInfo, dots, gridSizeX: match.cols, gridSizeY: match.rows, matchScore: match.score };
}

// ===== 디버그용 조각 추출 함수 =====
// 조각 모양 추출 + 시각화를 위한 캔버스 3개 생성
function extractShapeFromImageWithDebug(src, box, bgColor, index, grade) {
    // 원본 이미지에서 조각 카드 안쪽만 추출한다.
    const marginLeft = 0.06, marginRight = 0.06, marginTop = 0.06, marginBottom = 0.06;
    const iconX = box.x + Math.floor(box.width * marginLeft);
    const iconY = box.y + Math.floor(box.height * marginTop);
    const iconW = Math.floor(box.width * (1 - marginLeft - marginRight));
    const iconH = Math.floor(box.height * (1 - marginTop - marginBottom));

    const fullIconRoi = src.roi(new cv.Rect(iconX, iconY, iconW, iconH));
    const greenOffset = detectGreenTagOffsetFromMat(fullIconRoi);
    const hasGreenTag = greenOffset > 0;
    const useUniqueExtractor = isCookieSimUniqueGoldBg(bgColor);

    // 일반 조각은 장착중 태그 아래를 통째로 잘라내지 않는다. 태그를 잘라내면
    // 태그 가까이에 있는 세로 막대나 T/L 조각의 윗부분도 함께 사라지기 때문이다.
    // 유니크 조각은 기존 추출기 호환성을 위해 태그 아래 ROI를 사용한다.
    let analysisRoi = fullIconRoi;
    let ownsAnalysisRoi = false;
    if (useUniqueExtractor && hasGreenTag) {
        const adjustedH = iconH - greenOffset;
        if (adjustedH > 10) {
            analysisRoi = src.roi(new cv.Rect(iconX, iconY + greenOffset, iconW, adjustedH));
            ownsAnalysisRoi = true;
        }
    }

    const originalCanvas = document.createElement('canvas');
    cv.imshow(originalCanvas, analysisRoi);

    const extraction = useUniqueExtractor
        ? extractUniqueShapeFromRoiWithDebug(analysisRoi, bgColor, index, hasGreenTag)
        : extractShapeFromRoiWithDebug(analysisRoi, bgColor, index, hasGreenTag, greenOffset);
    const { shape, binary, gridInfo, dots, gridSizeX, gridSizeY, matchScore } = extraction;

    const processedCanvas = document.createElement('canvas');
    cv.imshow(processedCanvas, binary);
    binary.delete();

    const gridCanvas = document.createElement('canvas');
    drawGridAnalysis(gridCanvas, analysisRoi, shape, gridInfo, dots, gridSizeX, gridSizeY);

    if (ownsAnalysisRoi) analysisRoi.delete();
    fullIconRoi.delete();

    let info = `조각 ${index + 1}\n`;
    info += `등급: ${grade}\n`;
    info += `배경색: R=${bgColor.r}, G=${bgColor.g}, B=${bgColor.b}\n`;
    info += `크기: ${iconW}x${iconH}\n`;
    info += gridInfo;

    return {
        shape,
        hasGreenTag,
        matchScore,
        debug: {
            originalCanvas,
            processedCanvas,
            gridCanvas,
            info
        }
    };
}

// ===== 디버그용 그리드 분석 함수 =====
// 배경 제거 + 그리드 분석 + 디버그 정보 반환
function csOddKernelSize(value, minimum = 3, maximum = 9) {
    let size = Math.max(minimum, Math.min(maximum, Math.round(value)));
    if (size % 2 === 0) size += 1;
    if (size > maximum) size = maximum % 2 === 1 ? maximum : maximum - 1;
    return Math.max(3, size);
}

function csBuildCommonDarkOutlineMask(iconRoi, threshold, greenOffset = 0) {
    const gray = new cv.Mat();
    cv.cvtColor(iconRoi, gray, cv.COLOR_RGBA2GRAY);
    const binary = new cv.Mat();
    cv.threshold(gray, binary, threshold, 255, cv.THRESH_BINARY_INV);
    gray.delete();

    const iconW = binary.cols;
    const iconH = binary.rows;
    const sideMargin = Math.max(3, Math.floor(iconW * 0.06));
    const topMargin = Math.max(3, Math.floor(iconH * 0.05));
    const bottomMargin = Math.max(3, Math.floor(iconH * 0.05));
    const tagLimit = greenOffset > 0 ? Math.min(iconH, greenOffset + 2) : topMargin;

    for (let y = 0; y < iconH; y++) {
        for (let x = 0; x < iconW; x++) {
            if (x < sideMargin || x >= iconW - sideMargin ||
                y < topMargin || y >= iconH - bottomMargin ||
                (greenOffset > 0 && y < tagLimit)) {
                binary.ucharPtr(y, x)[0] = 0;
            }
        }
    }

    const closeKernel = cv.getStructuringElement(cv.MORPH_RECT, new cv.Size(3, 3));
    cv.morphologyEx(binary, binary, cv.MORPH_CLOSE, closeKernel);
    closeKernel.delete();
    return binary;
}

function csScoreDarkOutlineTemplate(component, rect, templateShape, iconW, iconH) {
    const shape = normalizeShape(templateShape || []);
    if (!shape.length) return null;
    const rows = Math.max(...shape.map((point) => point[0])) + 1;
    const cols = Math.max(...shape.map((point) => point[1])) + 1;
    const filled = new Set(shape.map((point) => `${point[0]},${point[1]}`));
    const cellW = rect.width / cols;
    const cellH = rect.height / rows;
    let filledSum = 0, emptySum = 0, filledCount = 0, emptyCount = 0;

    for (let row = 0; row < rows; row++) {
        for (let col = 0; col < cols; col++) {
            const x0 = Math.max(0, Math.floor(rect.x + (col + 0.18) * cellW));
            const x1 = Math.min(component.cols, Math.ceil(rect.x + (col + 0.82) * cellW));
            const y0 = Math.max(0, Math.floor(rect.y + (row + 0.18) * cellH));
            const y1 = Math.min(component.rows, Math.ceil(rect.y + (row + 0.82) * cellH));
            let white = 0, total = 0;
            for (let y = y0; y < y1; y++) {
                for (let x = x0; x < x1; x++) {
                    total++;
                    if (component.ucharPtr(y, x)[0] > 128) white++;
                }
            }
            const ratio = total > 0 ? white / total : 0;
            if (filled.has(`${row},${col}`)) {
                filledSum += ratio;
                filledCount++;
            } else {
                emptySum += ratio;
                emptyCount++;
            }
        }
    }

    const filledAverage = filledCount ? filledSum / filledCount : 0;
    const emptyAverage = emptyCount ? emptySum / emptyCount : 0;
    const aspect = rect.width / Math.max(1, rect.height);
    const templateAspect = cols / Math.max(1, rows);
    const aspectPenalty = Math.abs(Math.log(Math.max(0.01, aspect / templateAspect))) * 0.18;
    // 게임 카드의 조각 셀은 카드 크기에 비례해 거의 일정하다. 이 크기 보정을 넣어
    // 실루엣이 같은 1x1/2x2, 1x3/1x4 막대가 서로 바뀌는 문제를 막는다.
    const expectedCell = Math.max(2, Math.min(iconW, iconH) * 0.20);
    const cellPenalty = (
        Math.abs(Math.log(Math.max(0.05, cellW / expectedCell))) +
        Math.abs(Math.log(Math.max(0.05, cellH / expectedCell)))
    ) * 0.12;
    const centerX = rect.x + rect.width / 2;
    const centerY = rect.y + rect.height / 2;
    const centerDistance = Math.sqrt(
        ((centerX - iconW / 2) / Math.max(1, iconW / 2)) ** 2 +
        ((centerY - iconH * 0.53) / Math.max(1, iconH / 2)) ** 2
    );
    const score = filledAverage - emptyAverage * 0.9 - aspectPenalty - cellPenalty - centerDistance * 0.08;
    return { score, shape, rows, cols, filledAverage, emptyAverage, cellW, cellH };
}

function csExtractCommonShapeFromDarkOutline(iconRoi, greenOffset = 0) {
    const iconW = iconRoi.cols;
    const iconH = iconRoi.rows;
    const totalArea = iconW * iconH;
    const thresholds = [105, 115, 125, 135, 145];
    const templateEntries = Object.entries(COMMON_PIECE_TEMPLATES || {});
    let best = null;
    let bestBinary = null;

    thresholds.forEach((threshold) => {
        const binary = csBuildCommonDarkOutlineMask(iconRoi, threshold, greenOffset);
        const contourInput = binary.clone();
        const contours = new cv.MatVector();
        const hierarchy = new cv.Mat();
        cv.findContours(contourInput, contours, hierarchy, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE);
        contourInput.delete();

        for (let contourIndex = 0; contourIndex < contours.size(); contourIndex++) {
            const contour = contours.get(contourIndex);
            const area = cv.contourArea(contour);
            const rect = cv.boundingRect(contour);
            if (area < totalArea * 0.001) continue;
            if (rect.width < iconW * 0.04 || rect.height < iconH * 0.04) continue;
            if (rect.width > iconW * 0.86 || rect.height > iconH * 0.86) continue;

            const component = cv.Mat.zeros(iconH, iconW, cv.CV_8UC1);
            cv.drawContours(component, contours, contourIndex, new cv.Scalar(255), cv.FILLED);
            templateEntries.forEach(([templateName, templateData]) => {
                const scored = csScoreDarkOutlineTemplate(component, rect, templateData.shape, iconW, iconH);
                if (!scored || scored.filledAverage < 0.34) return;
                if (!best || scored.score > best.score) {
                    best = {
                        ...scored,
                        threshold,
                        templateName,
                        rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height }
                    };
                    if (bestBinary) bestBinary.delete();
                    bestBinary = binary.clone();
                }
            });
            component.delete();
        }
        contours.delete();
        hierarchy.delete();
        binary.delete();
    });

    if (!best || best.score < 0.34) {
        if (!bestBinary) bestBinary = cv.Mat.zeros(iconH, iconW, cv.CV_8UC1);
        return {
            shape: [],
            binary: bestBinary,
            gridInfo: `외곽선 템플릿 매칭 실패${best ? ` (점수 ${best.score.toFixed(3)})` : ''}\n`,
            dots: [],
            gridSizeX: 0,
            gridSizeY: 0,
            matchScore: best ? best.score : null
        };
    }

    const dots = best.shape.map(([row, col]) => ({
        x: best.rect.x + (col + 0.5) * best.cellW,
        y: best.rect.y + (row + 0.5) * best.cellH,
        area: best.cellW * best.cellH
    }));
    return {
        shape: best.shape,
        binary: bestBinary,
        gridInfo: `외곽선 그리드: ${best.cols}x${best.rows}\n템플릿: ${best.templateName}\n점수: ${best.score.toFixed(3)}\n명도 기준: ${best.threshold}\n`,
        dots,
        gridSizeX: best.cols,
        gridSizeY: best.rows,
        matchScore: best.score
    };
}

function csBuildCommonPieceMask(iconRoi, bgColor, hasGreenTag = false) {
    const iconW = iconRoi.cols;
    const iconH = iconRoi.rows;
    const binary = cv.Mat.zeros(iconH, iconW, cv.CV_8UC1);

    // 카드의 안쪽 광택 테두리가 조각 윤곽선과 연결되면 세로/가로 막대가
    // 카드 전체 크기의 사각형으로 잡힌다. 테두리 영역을 분석 대상에서 제외한다.
    const sideMargin = Math.max(2, Math.floor(iconW * 0.08));
    const topLimit = Math.max(2, Math.floor(iconH * 0.07));
    // 최신 인벤토리 카드의 하단에는 스탯 아이콘이 있으므로 조각 영역까지만 분석한다.
    const bottomLimit = Math.min(iconH, Math.ceil(iconH * 0.86));
    const threshold = 36;
    const residualTagLimit = Math.max(topLimit + 1, Math.floor(iconH * 0.12));

    for (let y = topLimit; y < bottomLimit; y++) {
        for (let x = sideMargin; x < iconW - sideMargin; x++) {
            const pixel = iconRoi.ucharPtr(y, x);
            const r = pixel[0], g = pixel[1], b = pixel[2];
            const dr = r - bgColor.r;
            const dg = g - bgColor.g;
            const db = b - bgColor.b;
            const distance = Math.sqrt(dr * dr + dg * dg + db * db);
            const brightness = (r + g + b) / 3;

            // 초록/연두색 조각 자체를 장착중 태그로 오인하지 않는다.
            // 태그가 실제로 감지된 카드에서, 잘라낸 뒤 상단에 남은 초록 픽셀만 제외한다.
            const residualGreenTag = hasGreenTag && y < residualTagLimit &&
                g > 135 && g > r + 30 && g > b + 30;

            if (!residualGreenTag && brightness >= 42 && distance >= threshold) {
                binary.ucharPtr(y, x)[0] = 255;
            }
        }
    }

    const smallKernel = cv.getStructuringElement(cv.MORPH_RECT, new cv.Size(3, 3));
    const closeSize = csOddKernelSize(Math.min(iconW, iconH) * 0.04, 5, 9);
    const closeKernel = cv.getStructuringElement(cv.MORPH_RECT, new cv.Size(closeSize, closeSize));
    cv.morphologyEx(binary, binary, cv.MORPH_OPEN, smallKernel);
    cv.morphologyEx(binary, binary, cv.MORPH_CLOSE, closeKernel);
    smallKernel.delete();
    closeKernel.delete();
    return binary;
}

function csScoreCommonTemplate(component, rect, templateShape, iconW, iconH) {
    const shape = normalizeShape(templateShape || []);
    if (!shape.length) return null;
    const rows = Math.max(...shape.map((point) => point[0])) + 1;
    const cols = Math.max(...shape.map((point) => point[1])) + 1;
    const filled = new Set(shape.map((point) => `${point[0]},${point[1]}`));
    const cellW = rect.width / cols;
    const cellH = rect.height / rows;
    let filledSum = 0, emptySum = 0, filledCount = 0, emptyCount = 0;

    for (let row = 0; row < rows; row++) {
        for (let col = 0; col < cols; col++) {
            const x0 = Math.max(0, Math.floor(rect.x + (col + 0.18) * cellW));
            const x1 = Math.min(component.cols, Math.ceil(rect.x + (col + 0.82) * cellW));
            const y0 = Math.max(0, Math.floor(rect.y + (row + 0.18) * cellH));
            const y1 = Math.min(component.rows, Math.ceil(rect.y + (row + 0.82) * cellH));
            let white = 0, total = 0;
            for (let y = y0; y < y1; y++) {
                for (let x = x0; x < x1; x++) {
                    total++;
                    if (component.ucharPtr(y, x)[0] > 128) white++;
                }
            }
            const ratio = total > 0 ? white / total : 0;
            if (filled.has(`${row},${col}`)) {
                filledSum += ratio;
                filledCount++;
            } else {
                emptySum += ratio;
                emptyCount++;
            }
        }
    }

    const filledAverage = filledCount ? filledSum / filledCount : 0;
    const emptyAverage = emptyCount ? emptySum / emptyCount : 0;
    const aspect = rect.width / Math.max(1, rect.height);
    const templateAspect = cols / Math.max(1, rows);
    const aspectPenalty = Math.abs(Math.log(Math.max(0.01, aspect / templateAspect))) * 0.18;
    const expectedCell = Math.max(2, Math.min(iconW, iconH) * 0.22);
    const cellPenalty = (
        Math.abs(Math.log(Math.max(0.05, cellW / expectedCell))) +
        Math.abs(Math.log(Math.max(0.05, cellH / expectedCell)))
    ) * 0.06;
    const centerX = rect.x + rect.width / 2;
    const centerY = rect.y + rect.height / 2;
    const centerDistance = Math.sqrt(
        ((centerX - iconW / 2) / Math.max(1, iconW / 2)) ** 2 +
        ((centerY - iconH * 0.48) / Math.max(1, iconH / 2)) ** 2
    );
    const centerPenalty = Math.min(centerDistance, 2) * 0.06;
    const score = filledAverage - emptyAverage * 0.9 - aspectPenalty - cellPenalty - centerPenalty;
    return { score, shape, rows, cols, filledAverage, emptyAverage, cellW, cellH };
}

function csExtractCommonShapeFromRoiWithDebug(iconRoi, bgColor, hasGreenTag = false) {
    const iconW = iconRoi.cols;
    const iconH = iconRoi.rows;
    const binary = csBuildCommonPieceMask(iconRoi, bgColor, hasGreenTag);
    const contourInput = binary.clone();
    const contours = new cv.MatVector();
    const hierarchy = new cv.Mat();
    cv.findContours(contourInput, contours, hierarchy, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE);
    contourInput.delete();

    let best = null;
    const totalArea = iconW * iconH;
    const templateEntries = Object.entries(COMMON_PIECE_TEMPLATES || {});

    for (let contourIndex = 0; contourIndex < contours.size(); contourIndex++) {
        const contour = contours.get(contourIndex);
        const area = cv.contourArea(contour);
        const rect = cv.boundingRect(contour);
        if (area < totalArea * 0.0015) continue;
        if (rect.width < iconW * 0.04 || rect.height < iconH * 0.04) continue;
        if (rect.width > iconW * 0.90 || rect.height > iconH * 0.90) continue;

        const component = cv.Mat.zeros(iconH, iconW, cv.CV_8UC1);
        cv.drawContours(component, contours, contourIndex, new cv.Scalar(255), cv.FILLED);

        templateEntries.forEach(([templateName, templateData]) => {
            const scored = csScoreCommonTemplate(component, rect, templateData.shape, iconW, iconH);
            if (!scored || scored.filledAverage < 0.36) return;
            if (!best || scored.score > best.score) {
                best = {
                    ...scored,
                    templateName,
                    rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height }
                };
            }
        });
        component.delete();
    }

    contours.delete();
    hierarchy.delete();

    if (!best || best.score < 0.30) {
        return {
            shape: [],
            binary,
            gridInfo: `색상 대비 템플릿 매칭 실패${best ? ` (점수 ${best.score.toFixed(3)})` : ''}\n`,
            dots: [],
            gridSizeX: 0,
            gridSizeY: 0,
            matchScore: best ? best.score : null
        };
    }

    const dots = best.shape.map(([row, col]) => ({
        x: best.rect.x + (col + 0.5) * best.cellW,
        y: best.rect.y + (row + 0.5) * best.cellH,
        area: best.cellW * best.cellH
    }));
    const gridInfo = `색상 대비 그리드: ${best.cols}x${best.rows}\n템플릿: ${best.templateName}\n점수: ${best.score.toFixed(3)}\n`;
    return {
        shape: best.shape,
        binary,
        gridInfo,
        dots,
        gridSizeX: best.cols,
        gridSizeY: best.rows,
        matchScore: best.score
    };
}

function extractShapeFromRoiWithDebug(iconRoi, bgColor, index, hasGreenTag = false, greenOffset = 0) {
    // 카드와 조각의 색 조합에 영향을 덜 받는 짙은 외곽선 판별을 우선한다.
    const outline = csExtractCommonShapeFromDarkOutline(iconRoi, greenOffset);
    if (outline.shape && outline.shape.length) return outline;

    // 외곽선이 지나치게 흐린 구버전 캡처는 카드 배경색 대비 방식으로 다시 확인한다.
    const colorContrast = csExtractCommonShapeFromRoiWithDebug(iconRoi, bgColor, hasGreenTag);
    if (colorContrast.shape && colorContrast.shape.length) {
        try { outline.binary.delete(); } catch (_) {}
        return colorContrast;
    }

    const legacy = extractShapeFromRoiLegacyWithDebug(iconRoi, bgColor, index, hasGreenTag);
    const legacyName = findPieceNameByShape(legacy.shape);
    if (legacyName) {
        try { outline.binary.delete(); } catch (_) {}
        try { colorContrast.binary.delete(); } catch (_) {}
        return legacy;
    }
    try { colorContrast.binary.delete(); } catch (_) {}
    try { legacy.binary.delete(); } catch (_) {}
    return outline;
}

function extractShapeFromRoiLegacyWithDebug(iconRoi, bgColor, index, hasGreenTag = false) {
    const iconW = iconRoi.cols;
    const iconH = iconRoi.rows;

    // ===== 1단계: 엣지 검출로 조각 윤곽선 찾기 =====
    const binary = new cv.Mat();
    const gray = new cv.Mat();

    cv.cvtColor(iconRoi, gray, cv.COLOR_RGBA2GRAY);
    
    // 가우시안 블러로 노이즈 감소 (엣지 검출 전)
    const blurred = new cv.Mat();
    cv.GaussianBlur(gray, blurred, new cv.Size(3, 3), 0);
    
    const edges = new cv.Mat();
    cv.Canny(blurred, edges, 30, 100);
    blurred.delete();

    const kernel = cv.getStructuringElement(cv.MORPH_RECT, new cv.Size(5, 5));
    cv.dilate(edges, edges, kernel);

    const edgeContours = new cv.MatVector();
    const edgeHierarchy = new cv.Mat();
    cv.findContours(edges, edgeContours, edgeHierarchy, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE);

    let maxArea = 0;
    let maxContourIdx = -1;
    for (let i = 0; i < edgeContours.size(); i++) {
        const area = cv.contourArea(edgeContours.get(i));
        if (area > maxArea) {
            maxArea = area;
            maxContourIdx = i;
        }
    }

    const edgeMask = cv.Mat.zeros(iconH, iconW, cv.CV_8UC1);
    if (maxContourIdx >= 0) {
        cv.drawContours(edgeMask, edgeContours, maxContourIdx, new cv.Scalar(255), cv.FILLED);
    }

    edgeContours.delete();
    edgeHierarchy.delete();
    edges.delete();

    // ===== 2단계: 배경색 제거 (색상 범위 기반) =====
    const tolerance = 60;
    const bgLower = new cv.Mat(iconRoi.rows, iconRoi.cols, iconRoi.type(),
        [Math.max(0, bgColor.r - tolerance), Math.max(0, bgColor.g - tolerance),
         Math.max(0, bgColor.b - tolerance), 0]);
    const bgUpper = new cv.Mat(iconRoi.rows, iconRoi.cols, iconRoi.type(),
        [Math.min(255, bgColor.r + tolerance), Math.min(255, bgColor.g + tolerance),
         Math.min(255, bgColor.b + tolerance), 255]);

    const bgMask = new cv.Mat();
    cv.inRange(iconRoi, bgLower, bgUpper, bgMask);  // 배경색 영역 찾기

    bgLower.delete();
    bgUpper.delete();

    // ===== 2-1단계: "장착중" 녹색 태그 제거 (#52CE32) =====
    const greenTolerance = 35;
    const greenLower = new cv.Mat(iconRoi.rows, iconRoi.cols, iconRoi.type(),
        [Math.max(0, 82 - greenTolerance), Math.max(0, 206 - greenTolerance),
         Math.max(0, 50 - greenTolerance), 0]);
    const greenUpper = new cv.Mat(iconRoi.rows, iconRoi.cols, iconRoi.type(),
        [Math.min(255, 82 + greenTolerance), Math.min(255, 206 + greenTolerance),
         Math.min(255, 50 + greenTolerance), 255]);

    const greenMask = new cv.Mat();
    cv.inRange(iconRoi, greenLower, greenUpper, greenMask);  // 녹색 영역 찾기

    greenLower.delete();
    greenUpper.delete();

    // ===== 2-2단계: 상단 영역의 밝은 픽셀 제거 (흰색 텍스트 + 회색 테두리 잔여물) =====
    const topCleanHeight = Math.floor(iconH * 0.25); // 상단 25% 영역
    const brightnessMask = new cv.Mat.zeros(iconH, iconW, cv.CV_8UC1);

    for (let y = 0; y < topCleanHeight; y++) {
        for (let x = 0; x < iconW; x++) {
            const pixel = iconRoi.ucharPtr(y, x);
            const r = pixel[0];
            const g = pixel[1];
            const b = pixel[2];
            const brightness = (r + g + b) / 3;

            // RGB 차이 (회색은 R≈G≈B)
            const maxChannel = Math.max(r, g, b);
            const minChannel = Math.min(r, g, b);
            const colorDiff = maxChannel - minChannel;

            // 제거 조건:
            // 1. 밝은 픽셀 (밝기 > 180)
            // 2. 흰색 (R,G,B > 200)
            // 3. 회색 계열 (색차 < 30 AND 밝기 > 100)
            const isGray = (colorDiff < 30 && brightness > 100);
            const isBright = brightness > 180;
            const isWhite = (r > 200 && g > 200 && b > 200);

            if (isBright || isWhite || isGray) {
                brightnessMask.ucharPtr(y, x)[0] = 255; // 제거 대상
            }
        }
    }

    // 배경색 마스크 + 녹색 마스크 + 밝기 마스크 합치기
    const colorMask = new cv.Mat();
    cv.bitwise_or(bgMask, greenMask, colorMask);  // 배경 + 녹색
    cv.bitwise_or(colorMask, brightnessMask, colorMask);  // + 밝은 픽셀
    cv.bitwise_not(colorMask, colorMask);         // 반전 (조각 영역만 남김)

    bgMask.delete();
    greenMask.delete();
    brightnessMask.delete();

    // ===== 3단계: 엣지 마스크와 색상 마스크 합치기 =====
    cv.bitwise_or(edgeMask, colorMask, binary);
    edgeMask.delete();
    colorMask.delete();
    gray.delete();

    // ===== 4단계: 상단 흰색 라인 제거 =====
    const removeTopLines = 3; // 상단 3픽셀 처리

    if (iconH > 0) {
        const paintEndLine = Math.min(removeTopLines - 1, iconH - 1);
        
        // 상단 3픽셀 처리: 1,2픽셀은 검정, 3픽셀은 회색
        for (let y = 0; y <= paintEndLine; y++) {
        for (let x = 0; x < iconW; x++) {
                if (y === 0 || y === 1) {
                    binary.ucharPtr(y, x)[0] = 0; // 1,2픽셀: 검정
                } else if (y === 2) {
                    binary.ucharPtr(y, x)[0] = 128; // 3픽셀: 회색
                }
            }
        }
    }

    // ===== 4-1단계: 추가 노이즈 제거 (녹색 태그가 있었던 경우) =====
    if (hasGreenTag) {
        // 상단 3px 영역에서 작은 흰색 점들만 제거 (연속된 흰색 영역은 보존)
        const cleanHeight = Math.min(3, iconH);
        for (let y = 0; y < cleanHeight; y++) {
            for (let x = 0; x < iconW; x++) {
                if (binary.ucharPtr(y, x)[0] > 128) {
                    // 주변 8방향 확인
                    let whiteNeighbors = 0;
                    for (let dy = -1; dy <= 1; dy++) {
                        for (let dx = -1; dx <= 1; dx++) {
                            if (dx === 0 && dy === 0) continue;
                            const ny = y + dy;
                            const nx = x + dx;
                            if (ny >= 0 && ny < iconH && nx >= 0 && nx < iconW) {
                                if (binary.ucharPtr(ny, nx)[0] > 128) {
                                    whiteNeighbors++;
                                }
                            }
                        }
                    }
                    // 주변에 흰색이 3개 이하면 노이즈로 간주하고 제거
                    if (whiteNeighbors <= 3) {
                        binary.ucharPtr(y, x)[0] = 0;
                    }
                }
            }
        }
    }

    // ===== 5단계: 노이즈 제거 (모폴로지 연산 강화) =====
    // 작은 커널로 먼저 정리
    const smallKernel = cv.getStructuringElement(cv.MORPH_RECT, new cv.Size(3, 3));
    cv.morphologyEx(binary, binary, cv.MORPH_OPEN, smallKernel);   // 작은 점 제거
    cv.morphologyEx(binary, binary, cv.MORPH_CLOSE, smallKernel);  // 작은 구멍 메우기
    
    // 큰 커널로 추가 정리
    const largeKernel = cv.getStructuringElement(cv.MORPH_RECT, new cv.Size(5, 5));
    cv.morphologyEx(binary, binary, cv.MORPH_CLOSE, largeKernel);  // 더 큰 구멍 메우기
    
    smallKernel.delete();
    largeKernel.delete();

    // ===== 5-1단계: 작은 윤곽선 사전 제거 =====
    const tempContours = new cv.MatVector();
    const tempHierarchy = new cv.Mat();
    cv.findContours(binary, tempContours, tempHierarchy, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE);
    
    // 전체 영역의 1% 미만인 작은 윤곽선 제거
    const totalImageArea = iconW * iconH;
    const minContourArea = totalImageArea * 0.01;
    
    const cleanedBinary = cv.Mat.zeros(iconH, iconW, cv.CV_8UC1);
    for (let i = 0; i < tempContours.size(); i++) {
        const area = cv.contourArea(tempContours.get(i));
        if (area >= minContourArea) {
            cv.drawContours(cleanedBinary, tempContours, i, new cv.Scalar(255), cv.FILLED);
        }
    }
    cleanedBinary.copyTo(binary);
    cleanedBinary.delete();
    tempContours.delete();
    tempHierarchy.delete();

    // ===== 5-2단계: 윤곽선으로 조각 영역 채우기 (가장 큰 윤곽선만) =====
    const contours = new cv.MatVector();
    const hierarchy = new cv.Mat();
    cv.findContours(binary, contours, hierarchy, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE);

    // 가장 큰 윤곽선 찾기 (실제 조각)
    let largestArea = 0;
    let largestIdx = -1;
    for (let i = 0; i < contours.size(); i++) {
        const area = cv.contourArea(contours.get(i));
        if (area > largestArea) {
            largestArea = area;
            largestIdx = i;
        }
    }

    // 새로운 이진 이미지: 가장 큰 윤곽선만 그리기
    binary.setTo(new cv.Scalar(0)); // 초기화 (검정)
    if (largestIdx >= 0) {
        cv.drawContours(binary, contours, largestIdx, new cv.Scalar(255), cv.FILLED);
    }

    contours.delete();
    hierarchy.delete();
    
    // ===== 5-3단계: 최종 정리 (작은 돌기 제거) =====
    const finalKernel = cv.getStructuringElement(cv.MORPH_RECT, new cv.Size(3, 3));
    cv.morphologyEx(binary, binary, cv.MORPH_OPEN, finalKernel);  // 작은 돌기 제거
    finalKernel.delete();
    
    // ===== 5-4단계: 테두리 약간 깎기 (침식 연산) =====
    const erodeKernel = cv.getStructuringElement(cv.MORPH_RECT, new cv.Size(5, 5));
    cv.erode(binary, binary, erodeKernel);  // 테두리를 약간 안쪽으로 축소
    erodeKernel.delete();

    // ===== 6단계: 조각의 bounding box 찾기 =====
    let minX = iconW, maxX = 0, minY = iconH, maxY = 0, totalFilled = 0;
    for (let y = 0; y < iconH; y++) {
        for (let x = 0; x < iconW; x++) {
            if (binary.ucharPtr(y, x)[0] > 128) {
                totalFilled++;
                if (x < minX) minX = x;
                if (x > maxX) maxX = x;
                if (y < minY) minY = y;
                if (y > maxY) maxY = y;
            }
        }
    }

    // 조각이 없으면 빈 shape 반환
    if (totalFilled === 0) {
        const gridInfo = `그리드: 0x0\n총 픽셀: 0\n`;
        return { shape: [], binary, gridInfo, dots: [], gridSizeX: 0, gridSizeY: 0 };
    }

    const pieceW = maxX - minX + 1;
    const pieceH = maxY - minY + 1;

    // 셀 크기 추정 (가장 작은 변을 기준으로)
    const minDim = Math.min(pieceW, pieceH);
    const estimatedCellSize = minDim / Math.max(1, Math.floor(minDim / 20)); // 대략 20px per cell

    // 그리드 크기 계산
    const gridCols = Math.max(1, Math.round(pieceW / estimatedCellSize));
    const gridRows = Math.max(1, Math.round(pieceH / estimatedCellSize));

    // 그리드 크기 제한 (1~5칸)
    const gridSizeX = Math.min(5, Math.max(1, gridCols));
    const gridSizeY = Math.min(5, Math.max(1, gridRows));

    const actualCellW = pieceW / gridSizeX;
    const actualCellH = pieceH / gridSizeY;

    let gridInfo = `그리드: ${gridSizeX}x${gridSizeY}\n`;
    gridInfo += `셀 크기: ${actualCellW.toFixed(1)}x${actualCellH.toFixed(1)}\n`;
    gridInfo += `총 픽셀: ${totalFilled}\n`;

    // 각 그리드 셀 검사
    const shape = [];
    const dots = []; // 디버그용: 각 셀의 중심점

    for (let row = 0; row < gridSizeY; row++) {
        for (let col = 0; col < gridSizeX; col++) {
            const cellX = minX + col * actualCellW;
            const cellY = minY + row * actualCellH;
            const centerX = cellX + actualCellW / 2;
            const centerY = cellY + actualCellH / 2;

            // 셀 영역의 픽셀 샘플링 (70% 영역)
            const sampleMargin = 0.15;
            const sampleX = Math.floor(cellX + actualCellW * sampleMargin);
            const sampleY = Math.floor(cellY + actualCellH * sampleMargin);
            const sampleW = Math.floor(actualCellW * (1 - sampleMargin * 2));
            const sampleH = Math.floor(actualCellH * (1 - sampleMargin * 2));

            if (sampleW > 0 && sampleH > 0 &&
                sampleX >= 0 && sampleY >= 0 &&
                sampleX + sampleW <= iconW &&
                sampleY + sampleH <= iconH) {

                const cellRoi = binary.roi(new cv.Rect(sampleX, sampleY, sampleW, sampleH));
                const mean = cv.mean(cellRoi);
                cellRoi.delete();

                if (mean[0] > 128) {
                    shape.push([row, col]);
                    dots.push({ x: centerX, y: centerY, area: sampleW * sampleH });
                }
            }
        }
    }

    const normalizedShape = normalizeShape(shape);

    return {
        shape: normalizedShape,
        binary: binary.clone(),
        gridInfo,
        dots,
        gridSizeX,
        gridSizeY
    };
}

function drawGridAnalysis(canvas, iconRoi, shape, gridInfo, dots, gridSizeX, gridSizeY) {
    canvas.width = iconRoi.cols;
    canvas.height = iconRoi.rows;
    const ctx = canvas.getContext('2d');

    // 원본 이미지를 canvas에 그리기
    const tempCanvas = document.createElement('canvas');
    cv.imshow(tempCanvas, iconRoi);
    ctx.drawImage(tempCanvas, 0, 0);

    // 도트가 없으면 종료
    if (!dots || dots.length === 0) return;

    // 도트 위치에 파란색 원 그리기 (실제 감지된 도트)
    ctx.fillStyle = 'rgba(0, 0, 255, 0.5)';
    ctx.strokeStyle = 'rgba(0, 0, 255, 0.8)';
    ctx.lineWidth = 2;
    dots.forEach(dot => {
        ctx.beginPath();
        ctx.arc(dot.x, dot.y, 5, 0, 2 * Math.PI);
        ctx.fill();
        ctx.stroke();
    });

    // 그리드가 유효한 경우에만 그리드 라인 그리기
    if (gridSizeX > 0 && gridSizeY > 0 && dots.length > 1) {
        const minDotX = Math.min(...dots.map(d => d.x));
        const minDotY = Math.min(...dots.map(d => d.y));
        const maxDotX = Math.max(...dots.map(d => d.x));
        const maxDotY = Math.max(...dots.map(d => d.y));

        // 실제 셀 크기 계산
        const actualCellW = gridSizeX > 1 ? (maxDotX - minDotX) / (gridSizeX - 1) : 20;
        const actualCellH = gridSizeY > 1 ? (maxDotY - minDotY) / (gridSizeY - 1) : 20;

        // 그리드 라인 그리기 (빨간색)
        ctx.strokeStyle = 'rgba(255, 0, 0, 0.5)';
        ctx.lineWidth = 1;

        for (let i = 0; i <= gridSizeX; i++) {
            const x = minDotX + (i - (gridSizeX > 1 ? 0 : 0.5)) * actualCellW;
            ctx.beginPath();
            ctx.moveTo(x, minDotY - actualCellH * 0.5);
            ctx.lineTo(x, maxDotY + actualCellH * 0.5);
            ctx.stroke();
        }

        for (let i = 0; i <= gridSizeY; i++) {
            const y = minDotY + (i - (gridSizeY > 1 ? 0 : 0.5)) * actualCellH;
            ctx.beginPath();
            ctx.moveTo(minDotX - actualCellW * 0.5, y);
            ctx.lineTo(maxDotX + actualCellW * 0.5, y);
            ctx.stroke();
        }

        // 인식된 셀 표시 (녹색 반투명)
        ctx.fillStyle = 'rgba(0, 255, 0, 0.3)';
        shape.forEach(([row, col]) => {
            const cellX = minDotX + (col - (gridSizeX > 1 ? 0.5 : 0)) * actualCellW;
            const cellY = minDotY + (row - (gridSizeY > 1 ? 0.5 : 0)) * actualCellH;
            ctx.fillRect(cellX, cellY, actualCellW, actualCellH);
        });
    }
}

// 조각 패턴 정규화 (좌상단 정렬)
function normalizeShape(shape) {
    if (shape.length === 0) return [];

    const minRow = Math.min(...shape.map(p => p[0]));
    const minCol = Math.min(...shape.map(p => p[1]));

    return shape.map(p => [p[0] - minRow, p[1] - minCol]);
}

// 두 조각 패턴 비교
function shapesMatch(shape1, shape2) {
    if (shape1.length !== shape2.length) return false;

    // 좌표를 문자열로 변환해서 집합 비교
    const set1 = new Set(shape1.map(p => `${p[0]},${p[1]}`));
    const set2 = new Set(shape2.map(p => `${p[0]},${p[1]}`));

    if (set1.size !== set2.size) return false;

    for (const coord of set1) {
        if (!set2.has(coord)) return false;
    }

    return true;
}

// 추출한 패턴으로 조각 이름 찾기
function findPieceNameByShape(extractedShape) {
    if (!extractedShape || extractedShape.length === 0) {
        return null;
    }

    const normalizedExtracted = normalizeShape(extractedShape);
    const allTemplates = { ...COMMON_PIECE_TEMPLATES, ...UNIQUE_PIECE_TEMPLATES };

    for (const [templateName, templateData] of Object.entries(allTemplates)) {
        const normalizedTemplate = normalizeShape(templateData.shape);
        if (shapesMatch(normalizedExtracted, normalizedTemplate)) {
            return templateName;
        }
    }

    console.warn(` 인식 실패: ${normalizedExtracted.length}칸 조각`);
    return null;
}

    function csRecognizedGradeColor(grade) {
        if (grade === 'unique') return '#ffcc00';
        if (grade === 'super') return '#ff5b66';
        if (grade === 'epic') return '#b46bff';
        if (grade === 'rare') return '#5d8cff';
        return '#d1d5db';
    }



    function csEnsureRecognizedSection() {
        let section = document.getElementById('recognized-pieces-section');
        let filterWrap = document.getElementById('recognized-piece-filter-wrap');
        let palette = document.getElementById('recognized-piece-palette');
        if (section && palette && filterWrap) return { section, palette, filterWrap };
        const baseSection = document.querySelector('.pieces-section');
        if (!baseSection || !baseSection.parentNode) return { section: null, palette: null, filterWrap: null };

        section = document.createElement('section');
        section.id = 'recognized-pieces-section';
        section.className = 'pieces-section cs-card';
        section.style.display = 'none';
        section.style.marginTop = '12px';
        section.style.padding = '14px';
        section.style.border = 'none';
        section.style.overflow = 'visible';
        section.style.position = 'relative';

        const title = document.createElement('h3');
        title.textContent = (typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en') ? 'Recognized Shards' : '인식된 조각';
        title.style.margin = '0';
        title.style.color = '#ff4048';
        title.style.fontSize = '12px';
        title.style.fontWeight = '800';
        title.style.lineHeight = '1.35';
        section.appendChild(title);

        filterWrap = document.createElement('div');
        filterWrap.id = 'recognized-piece-filter-wrap';
        filterWrap.style.marginTop = '6px';
        filterWrap.style.marginBottom = '10px';
        section.appendChild(filterWrap);

        palette = document.createElement('div');
        palette.id = 'recognized-piece-palette';
        palette.className = 'palette';
        section.appendChild(palette);

        baseSection.parentNode.insertBefore(section, baseSection.nextSibling);
        return { section, palette, filterWrap };
    }

    function csRecognizedFilterOptions() {
        const csIsEn = (typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en');
        const opts = [{ value: 'all', label: csIsEn ? 'All' : '전체' }];
        Object.entries(SET_INFO).forEach(([key, info]) => opts.push({ value: key, label: info.name }));
        opts.push({ value: 'unique', label: csIsEn ? 'Unique' : '유니크' });
        return opts;
    }

    function csRenderRecognizedFilter() {
        const refs = csEnsureRecognizedSection();
        const filterWrap = refs.filterWrap;
        if (!filterWrap) return;
        filterWrap.innerHTML = '';
        filterWrap.style.position = 'relative';
        filterWrap.style.zIndex = '20';
        filterWrap.style.overflow = 'visible';

        const options = csRecognizedFilterOptions();
        const current = options.find(opt => opt.value === csRecognizedFilter) || options[0];

        // '사진별 세트 선택' 모달의 세트 드롭다운(cs-modal-select-*)과 완전히 동일한 마크업/클래스를 재사용한다.
        const wrap = document.createElement('div');
        wrap.className = 'cs-modal-select-wrap';
        wrap.style.margin = '0';
        filterWrap.appendChild(wrap);

        const combo = document.createElement('div');
        combo.className = 'cs-modal-select-dropdown';
        wrap.appendChild(combo);

        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'cs-modal-select-button';
        btn.className = 'cs-modal-select-button';
        btn.textContent = current.label;
        combo.appendChild(btn);

        const backdrop = document.createElement('div');
        backdrop.className = 'cs-modal-select-backdrop';
        combo.appendChild(backdrop);

        const menu = document.createElement('div');
        menu.className = 'cs-modal-select-menu';
        menu.className = 'cs-modal-select-menu';
        combo.appendChild(menu);

        const positionMenu = () => {
            const rect = btn.getBoundingClientRect();
            const vh = window.innerHeight || document.documentElement.clientHeight || 0;
            const below = vh - rect.bottom - 10;
            const above = rect.top - 10;
            const desired = Math.min(220, Math.max(menu.scrollHeight || 0, 44));
            let top;
            let maxH;
            if (below >= Math.min(desired, 150) || below >= above) {
                maxH = Math.max(80, Math.min(desired, below));
                top = rect.bottom + 4;
            } else {
                maxH = Math.max(80, Math.min(desired, above));
                top = rect.top - 4 - maxH;
            }
            menu.style.setProperty('--cs-menu-top', top + 'px');
            menu.style.setProperty('--cs-menu-left', rect.left + 'px');
            menu.style.setProperty('--cs-menu-width', rect.width + 'px');
            menu.style.setProperty('--cs-menu-max-h', maxH + 'px');
        };

        options.forEach((opt) => {
            const item = document.createElement('button');
            item.type = 'button';
            item.className = 'cs-modal-select-item';
            item.className = 'cs-modal-select-item';
            item.dataset.value = opt.value;
            item.textContent = opt.label;
            item.tabIndex = -1;
            if (opt.value === csRecognizedFilter) item.classList.add('active');
            let touchStartX = 0;
            let touchStartY = 0;
            let touchMoved = false;
            const chooseRecognizedFilter = (event) => {
                if (event) {
                    event.preventDefault();
                    event.stopPropagation();
                    if (event.stopImmediatePropagation) event.stopImmediatePropagation();
                }
                combo.classList.remove('open');
                csRecognizedFilter = opt.value;
                renderRecognizedPieceCards(csRecognizedResults);
            };
            item.addEventListener('pointerdown', (event) => {
                event.stopPropagation();
                touchStartX = event.clientX || 0;
                touchStartY = event.clientY || 0;
                touchMoved = false;
            });
            item.addEventListener('pointermove', (event) => {
                const dx = Math.abs((event.clientX || 0) - touchStartX);
                const dy = Math.abs((event.clientY || 0) - touchStartY);
                if (dx > 6 || dy > 6) touchMoved = true;
            });
            item.addEventListener('pointerup', (event) => {
                if (!touchMoved) chooseRecognizedFilter(event);
            });
            item.addEventListener('pointercancel', () => {
                touchMoved = true;
            });
            item.addEventListener('click', (event) => {
                event.preventDefault();
                event.stopPropagation();
                if (event.stopImmediatePropagation) event.stopImmediatePropagation();
            });
            menu.appendChild(item);
        });

        const toggleRecognizedMenu = (event) => {
            event.preventDefault();
            event.stopPropagation();
            if (event.stopImmediatePropagation) event.stopImmediatePropagation();
            const willOpen = !combo.classList.contains('open');
            document.querySelectorAll('.cs-palette-dropdown.open, .cs-modal-select-dropdown.open').forEach(el => {
                if (el !== combo) el.classList.remove('open');
            });
            combo.classList.toggle('open', willOpen);
            if (willOpen) positionMenu();
        };
        btn.addEventListener('pointerdown', (event) => {
            event.stopPropagation();
        });
        btn.addEventListener('click', toggleRecognizedMenu);
        backdrop.addEventListener('pointerdown', (event) => {
            event.preventDefault();
            event.stopPropagation();
            if (event.stopImmediatePropagation) event.stopImmediatePropagation();
            combo.classList.remove('open');
        });
        backdrop.addEventListener('click', (event) => {
            event.preventDefault();
            event.stopPropagation();
            if (event.stopImmediatePropagation) event.stopImmediatePropagation();
        });
        combo.addEventListener('pointerdown', (event) => event.stopPropagation());
        combo.addEventListener('click', (event) => event.stopPropagation());

        // 바깥 클릭/스크롤/리사이즈/ESC 시 닫기 (모달 드롭다운과 동일한 동작, 자체 바인딩으로 보장)
        if (!window.__csRecognizedFilterCloseBound) {
            window.__csRecognizedFilterCloseBound = true;
            document.addEventListener('pointerdown', (event) => {
                const path = event.composedPath ? event.composedPath() : [];
                const insideDropdown = path.some(el => el && el.classList && el.classList.contains('cs-modal-select-dropdown'));
                if (!insideDropdown) {
                    document.querySelectorAll('#recognized-piece-filter-wrap .cs-modal-select-dropdown.open').forEach(el => el.classList.remove('open'));
                }
            }, true);
            document.addEventListener('keydown', (event) => {
                if (event.key === 'Escape') {
                    document.querySelectorAll('#recognized-piece-filter-wrap .cs-modal-select-dropdown.open').forEach(el => el.classList.remove('open'));
                }
            });
            document.addEventListener('scroll', (event) => {
                const t = event.target;
                if (t && t.classList && t.classList.contains('cs-modal-select-menu')) return;
                document.querySelectorAll('#recognized-piece-filter-wrap .cs-modal-select-dropdown.open').forEach(el => el.classList.remove('open'));
            }, true);
            window.addEventListener('resize', () => {
                document.querySelectorAll('#recognized-piece-filter-wrap .cs-modal-select-dropdown.open').forEach(el => el.classList.remove('open'));
            });
        }
    }

    function csRecognizedSyncAndRender() {
        fillPiecesFromCV(csRecognizedResults);
        renderRecognizedPieceCards(csRecognizedResults);
    }

    // '조각 추가' 등급 선택 모달: 사진별 세트 선택 모달의 csOpenGradeSelectModal 로직을 복사한 전역 버전
    const csRecognizedGradeDefs = [{ key: 'rare', label: ((typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en') ? 'Rare' : '레어'), color: '#5d8cff' }, { key: 'epic', label: ((typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en') ? 'Epic' : '에픽'), color: '#b46bff' }, { key: 'super', label: ((typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en') ? 'Super Epic' : '슈퍼에픽'), color: '#ff5b66' }, { key: 'unique', label: ((typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en') ? 'Unique' : '유니크'), color: '#ffcc00' }];
    const csRecognizedGradeBg = { rare: 'rgba(100, 150, 255, 0.2)', epic: 'rgba(200, 100, 255, 0.2)', super: 'rgba(255, 100, 100, 0.2)', unique: 'rgba(255, 204, 0, 0.28)' };

    function csOpenRecognizedGradeSelectModal(onPick) {
        const en = (typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en');
        const gradeLabelEn = { rare: 'Rare', epic: 'Epic', super: 'Super Epic', unique: 'Unique' };
        const gModal = document.createElement('div');
        gModal.style.position = 'fixed';
        gModal.style.zIndex = '3000';
        gModal.style.left = '0';
        gModal.style.top = '0';
        gModal.style.width = '100%';
        gModal.style.height = '100%';
        gModal.style.background = 'rgba(0,0,0,0.55)';
        gModal.style.display = 'flex';
        gModal.style.alignItems = 'center';
        gModal.style.justifyContent = 'center';
        gModal.addEventListener('click', (e) => { if (e.target === gModal) document.body.removeChild(gModal); });

        const gBox = document.createElement('div');
        gBox.style.width = 'min(300px, 90vw)';
        gBox.style.background = '#fff';
        gBox.style.borderRadius = '12px';
        gBox.style.padding = '16px';
        gBox.style.boxShadow = '0 12px 32px rgba(0,0,0,0.22)';
        gBox.style.boxSizing = 'border-box';

        const gTitle = document.createElement('div');
        gTitle.textContent = en ? 'Select the grade of the shard to add' : '추가할 조각의 등급 선택';
        gTitle.classList.add('cs-grade-title');
        gTitle.style.fontWeight = '800';
        gTitle.style.fontSize = '12px';
        gTitle.style.color = CS_DARK_UI ? '#f3f4f6' : '#374151';
        gTitle.style.marginBottom = '10px';
        gBox.appendChild(gTitle);

        csRecognizedGradeDefs.forEach(def => {
            const gBtn = document.createElement('button');
            gBtn.type = 'button';
            gBtn.textContent = en ? (gradeLabelEn[def.key] || def.label) : def.label;
            gBtn.classList.add('cs-grade-pick-btn', `cs-grade-${def.key}`);
            gBtn.style.display = 'block';
            gBtn.style.width = '100%';
            gBtn.style.boxSizing = 'border-box';
            gBtn.style.padding = '9px 12px';
            gBtn.style.marginBottom = '6px';
            gBtn.style.border = 'none';
            gBtn.style.outline = 'none';
            gBtn.style.boxShadow = 'none';
            gBtn.style.borderRadius = '8px';
            gBtn.style.background = CS_DARK_UI ? '#3a3d42' : '#f3f4f6';
            gBtn.style.color = '#9ca3af';
            gBtn.style.fontSize = '12px';
            gBtn.style.fontWeight = '800';
            gBtn.style.cursor = 'pointer';
            gBtn.style.transition = 'background-color .12s ease, color .12s ease';
            gBtn.addEventListener('mouseenter', () => {
                gBtn.style.background = csRecognizedGradeBg[def.key] || 'rgba(156,163,175,0.18)';
                gBtn.style.color = def.color;
            });
            gBtn.addEventListener('mouseleave', () => {
                gBtn.style.background = CS_DARK_UI ? '#3a3d42' : '#f3f4f6';
                gBtn.style.color = '#9ca3af';
            });
            gBtn.addEventListener('focus', () => {
                gBtn.style.background = csRecognizedGradeBg[def.key] || 'rgba(156,163,175,0.18)';
                gBtn.style.color = def.color;
            });
            gBtn.addEventListener('blur', () => {
                gBtn.style.background = CS_DARK_UI ? '#3a3d42' : '#f3f4f6';
                gBtn.style.color = '#9ca3af';
            });
            gBtn.addEventListener('click', () => {
                document.body.removeChild(gModal);
                if (typeof onPick === 'function') onPick(def.key);
            });
            gBox.appendChild(gBtn);
        });

        gModal.appendChild(gBox);
        document.body.appendChild(gModal);
    }

    function csOpenRecognizedSetPicker(currentSet, onPick) {
        const en = (typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en');

        const modal = document.createElement('div');
        modal.style.position = 'fixed';
        modal.style.zIndex = '2000';
        modal.style.left = '0';
        modal.style.top = '0';
        modal.style.width = '100%';
        modal.style.height = '100%';
        modal.style.background = 'rgba(0,0,0,0.55)';
        modal.style.display = 'flex';
        modal.style.alignItems = 'center';
        modal.style.justifyContent = 'center';

        const box = document.createElement('div');
        box.style.width = 'min(520px, 92vw)';
        // 조각 스탯 수정 모달과 동일: 수정창 내부만 스크롤되게 하고 드롭다운은 안쪽 흐름에 포함
        box.style.maxHeight = '88dvh';
        box.style.overflowY = 'auto';
        box.style.overflowX = 'visible';
        box.style.background = CS_DARK_UI ? '#303236' : '#fff';
        box.style.borderRadius = '15px';
        box.style.padding = '18px';
        box.style.boxShadow = '0 18px 50px rgba(0,0,0,0.28)';
        box.style.boxSizing = 'border-box';

        const modalTextColor = CS_DARK_UI ? '#f3f4f6' : '#374151';

        const title = document.createElement('div');
        title.textContent = en ? 'Edit shard set' : '조각 세트 수정';
        title.style.fontWeight = '800';
        title.style.fontSize = '13px';
        title.style.marginBottom = '6px';
        title.style.color = modalTextColor;
        box.appendChild(title);

        const desc = document.createElement('div');
        desc.textContent = en ? 'Choose the set this shard belongs to below.' : '아래에서 이 조각이 들어갈 세트를 고를 수 있어요.';
        desc.style.fontSize = '12px';
        desc.style.fontWeight = '400';
        desc.style.color = modalTextColor;
        desc.style.marginBottom = '10px';
        desc.style.textAlign = 'left';
        desc.style.lineHeight = '1.6';
        box.appendChild(desc);

        // 조각 스탯 수정 모달의 드롭다운(makeSelect)과 동일한 디자인
        let selectedSetKey = currentSet && SET_INFO[currentSet] ? currentSet : (Object.keys(SET_INFO)[0] || '');
        const setEntries = Object.entries(SET_INFO);

        const wrap = document.createElement('div');
        wrap.className = 'cs-modal-select-wrap';
        wrap.style.width = '100%';
        wrap.style.position = 'relative';
        wrap.style.boxSizing = 'border-box';
        wrap.style.marginTop = '10px';

        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'cs-modal-select-button';
        btn.textContent = (SET_INFO[selectedSetKey] && SET_INFO[selectedSetKey].name) || '';
        btn.style.width = '100%';
        btn.style.height = '38px';
        btn.style.padding = '0 34px 0 12px';
        btn.style.borderRadius = '8px';
        btn.style.border = 'none';
        btn.style.background = CS_DARK_UI ? '#3a3d42' : '#d1d5db';
        btn.style.color = CS_DARK_UI ? '#f3f4f6' : '#111827';
        btn.style.fontSize = '10px';
        btn.style.fontWeight = '800';
        btn.style.fontFamily = 'Arial, sans-serif';
        btn.style.textAlign = 'left';
        btn.style.lineHeight = '38px';
        btn.style.cursor = 'pointer';
        btn.style.boxShadow = 'none';
        btn.style.boxSizing = 'border-box';
        btn.style.position = 'relative';

        const arrow = document.createElement('span');
        arrow.style.position = 'absolute';
        arrow.style.right = '16px';
        arrow.style.top = '50%';
        arrow.style.width = '6px';
        arrow.style.height = '6px';
        arrow.style.borderRight = `2px solid ${CS_DARK_UI ? '#cbd5e1' : '#6b7280'}`;
        arrow.style.borderBottom = `2px solid ${CS_DARK_UI ? '#cbd5e1' : '#6b7280'}`;
        arrow.style.transform = 'translateY(-65%) rotate(45deg)';
        arrow.style.pointerEvents = 'none';
        btn.appendChild(arrow);

        const menu = document.createElement('div');
        menu.className = 'cs-stat-edit-menu';
        menu.style.display = 'none';
        menu.style.position = 'relative';
        menu.style.zIndex = '2147483647';
        menu.style.background = CS_DARK_UI ? '#303236' : '#ffffff';
        menu.style.color = CS_DARK_UI ? '#f3f4f6' : '#374151';
        menu.style.border = '0';
        menu.style.borderRadius = '8px';
        menu.style.marginTop = '4px';
        menu.style.boxShadow = 'none';
        menu.style.overflowY = 'auto';
        menu.style.overflowX = 'hidden';
        menu.style.padding = '6px 0';
        menu.style.boxSizing = 'border-box';
        menu.style.maxHeight = '190px';
        menu.style.touchAction = 'pan-y';
        menu.style.overscrollBehavior = 'contain';
        menu.style.webkitOverflowScrolling = 'touch';

        const items = setEntries.map(([key, info]) => {
            const item = document.createElement('button');
            item.type = 'button';
            item.className = 'cs-modal-select-item';
            item.textContent = info.name;
            item.dataset.value = key;
            item.style.display = 'block';
            item.style.width = '100%';
            item.style.padding = '9px 12px';
            item.style.border = 'none';
            item.style.background = CS_DARK_UI ? '#303236' : '#ffffff';
            item.style.color = CS_DARK_UI ? '#f3f4f6' : '#374151';
            item.style.fontSize = '12px';
            item.style.fontWeight = '700';
            item.style.textAlign = 'left';
            item.style.lineHeight = '1.25';
            item.style.cursor = 'pointer';
            item.style.boxShadow = 'none';
            item.style.boxSizing = 'border-box';
            item.style.touchAction = 'pan-y';
            item.addEventListener('mouseenter', () => {
                item.style.background = CS_DARK_UI ? '#303236' : '#ffffff';
                item.style.color = '#ff4048';
                item.style.fontWeight = '800';
            });
            item.addEventListener('mouseleave', () => {
                item.style.background = CS_DARK_UI ? '#303236' : '#ffffff';
                item.style.color = CS_DARK_UI ? '#f3f4f6' : '#374151';
                item.style.fontWeight = '700';
            });
            let touchStartX = 0;
            let touchStartY = 0;
            let touchMoved = false;
            const chooseSetItem = (event) => {
                if (event) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                selectedSetKey = key;
                btn.childNodes[0].nodeValue = info.name;
                closeMenu();
                syncActive();
            };
            item.addEventListener('pointerdown', (event) => {
                event.stopPropagation();
                touchStartX = event.clientX || 0;
                touchStartY = event.clientY || 0;
                touchMoved = false;
            });
            item.addEventListener('pointermove', (event) => {
                const dx = Math.abs((event.clientX || 0) - touchStartX);
                const dy = Math.abs((event.clientY || 0) - touchStartY);
                if (dx > 6 || dy > 6) touchMoved = true;
            });
            item.addEventListener('pointerup', (event) => {
                if (!touchMoved) chooseSetItem(event);
            });
            item.addEventListener('pointercancel', () => {
                touchMoved = true;
            });
            menu.appendChild(item);
            return item;
        });

        const syncActive = () => {
            items.forEach(item => {
                const active = item.dataset.value === selectedSetKey;
                item.style.fontWeight = active ? '800' : '700';
                item.style.color = active ? (CS_DARK_UI ? '#ffffff' : '#111827') : (CS_DARK_UI ? '#f3f4f6' : '#374151');
            });
        };

        const positionMenu = () => {
            // 조각 스탯 수정 드롭다운과 동일: 수정창 안쪽 흐름에 포함시키고 목록 내부만 스크롤
            menu.style.left = '0px';
            menu.style.top = 'auto';
            menu.style.bottom = 'auto';
            menu.style.width = '100%';
            menu.style.right = 'auto';
            menu.style.maxHeight = '190px';
            menu.style.marginTop = '4px';
            menu.style.borderRadius = '8px';
        };

        const outsideHandler = (event) => {
            if (menu.contains(event.target) || wrap.contains(event.target)) return;
            closeMenu();
        };
        const closeMenu = () => {
            menu.style.display = 'none';
            document.removeEventListener('pointerdown', outsideHandler, true);
        };
        const destroyMenu = () => {
            document.removeEventListener('pointerdown', outsideHandler, true);
            if (menu.parentNode) menu.parentNode.removeChild(menu);
        };

        // 조각 스탯 수정 드롭다운과 동일한 열기/닫기 처리:
        // 드롭다운/버튼 내부 터치는 자체 처리하고, 바깥 터치만 outsideHandler에서 닫는다.
        menu.addEventListener('pointerdown', (event) => event.stopPropagation());
        menu.addEventListener('click', (event) => event.stopPropagation());

        const toggleMenu = (event) => {
            if (event) {
                event.preventDefault();
                event.stopPropagation();
                if (event.stopImmediatePropagation) event.stopImmediatePropagation();
            }
            const willOpen = menu.style.display !== 'block';
            if (!willOpen) {
                closeMenu();
                return;
            }
            menu.style.display = 'block';
            syncActive();
            positionMenu();
            document.removeEventListener('pointerdown', outsideHandler, true);
            setTimeout(() => document.addEventListener('pointerdown', outsideHandler, true), 0);
        };
        btn.addEventListener('pointerdown', (event) => {
            // 모바일에서 pointerdown에 바로 열면 이어지는 click 이벤트로
            // 즉시 닫히는 경우가 있어서 여기서는 전파만 막고 실제 토글은 click에서 처리한다.
            event.stopPropagation();
        });
        btn.addEventListener('click', toggleMenu);

        wrap.appendChild(btn);
        wrap.appendChild(menu);
        box.appendChild(wrap);

        const buttons = document.createElement('div');
        buttons.style.display = 'flex';
        buttons.style.gap = '10px';
        buttons.style.marginTop = '8px';
        buttons.style.position = 'sticky';
        buttons.style.bottom = '0';
        buttons.style.background = CS_DARK_UI ? '#303236' : '#fff';
        buttons.style.paddingTop = '6px';

        const saveBtn = document.createElement('button');
        saveBtn.textContent = en ? 'Save' : '저장';
        saveBtn.style.flex = '1';
        saveBtn.style.padding = '12px';
        saveBtn.style.fontSize = '1em';
        saveBtn.style.fontWeight = 'bold';
        saveBtn.style.border = 'none';
        saveBtn.style.borderRadius = '8px';
        saveBtn.style.cursor = 'pointer';
        saveBtn.style.background = '#ff4048';
        saveBtn.style.color = 'white';
        saveBtn.addEventListener('click', () => {
            destroyMenu();
            document.body.removeChild(modal);
            if (typeof onPick === 'function') onPick(selectedSetKey);
        });

        const cancelBtn = document.createElement('button');
        cancelBtn.textContent = en ? 'Cancel' : '취소';
        cancelBtn.style.flex = '1';
        cancelBtn.style.padding = '12px';
        cancelBtn.style.fontSize = '1em';
        cancelBtn.style.fontWeight = 'bold';
        cancelBtn.style.border = 'none';
        cancelBtn.style.borderRadius = '8px';
        cancelBtn.style.cursor = 'pointer';
        cancelBtn.style.background = '#e5e7eb';
        cancelBtn.style.color = '#666';
        cancelBtn.addEventListener('click', () => {
            destroyMenu();
            document.body.removeChild(modal);
        });

        buttons.appendChild(saveBtn);
        buttons.appendChild(cancelBtn);
        box.appendChild(buttons);

        modal.appendChild(box);
        document.body.appendChild(modal);
        modal.addEventListener('click', (ev) => {
            if (ev.target === modal) {
                destroyMenu();
                document.body.removeChild(modal);
            }
        });
    }

    function csRecognizedGradeTextColor(grade) {
        if (grade === 'unique') return '#ffcc00';
        if (grade === 'super') return '#ff5b66';
        if (grade === 'epic') return '#b46bff';
        if (grade === 'rare') return '#5d8cff';
        return '#ff4048';
    }

    function csRecognizedChipBg() {
        return CS_DARK_UI ? '#303236' : '#fff';
    }

    function csRecognizedMakeRemoveBtn(onRemove) {
        const btn = document.createElement('button');
        btn.type = 'button';
        // 폰트 글리프 '×'는 베이스라인 때문에 원 안에서 살짝 치우쳐 보여서
        // 기하학적으로 정중앙인 SVG 십자로 그린다. currentColor라 hover 색상도 그대로 따라간다.
        btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 14 14" style="display:block" aria-hidden="true"><path d="M4.6 4.6 L9.4 9.4 M9.4 4.6 L4.6 9.4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>';
        btn.title = '이 조각 삭제';
        btn.style.position = 'absolute';
        // 상단 칩(높이 22px, 카드 padding 4px 아래) 세로 중심에 오도록: 4 + 11 - 7 = 8px
        btn.style.top = '8px';
        btn.style.right = '6px';
        btn.style.width = '14px';
        btn.style.height = '14px';
        btn.style.minHeight = '14px';
        btn.style.padding = '0';
        btn.style.margin = '0';
        btn.style.border = 'none';
        btn.style.borderRadius = '50%';
        btn.style.background = '#e5e7eb';
        btn.style.color = '#6b7280';
        btn.style.fontSize = '10px';
        btn.style.fontWeight = '800';
        btn.style.fontFamily = 'Arial, sans-serif';
        btn.style.lineHeight = '14px';
        btn.style.display = 'flex';
        btn.style.alignItems = 'center';
        btn.style.justifyContent = 'center';
        btn.style.cursor = 'pointer';
        btn.style.zIndex = '5';
        btn.addEventListener('mouseenter', () => { btn.style.background = '#ff4048'; btn.style.color = '#fff'; });
        btn.addEventListener('mouseleave', () => { btn.style.background = '#e5e7eb'; btn.style.color = '#6b7280'; });
        btn.addEventListener('click', (ev) => {
            ev.stopPropagation();
            if (ev.stopImmediatePropagation) ev.stopImmediatePropagation();
            if (typeof onRemove === 'function') onRemove();
        });
        return btn;
    }

    function renderRecognizedPieceCards(pieceData) {
        const { section, palette } = csEnsureRecognizedSection();
        if (!section || !palette) return;
        palette.innerHTML = '';
        const csRecogEn = (typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en');
        section.style.display = 'block';
        const title = section.querySelector(':scope > h3');
        if (title) title.textContent = csRecogEn ? 'Recognized Shards' : '인식된 조각';
        const filterWrapEl = document.getElementById('recognized-piece-filter-wrap');
        if (!Array.isArray(pieceData) || !pieceData.length) {
            // 배치 결과 카드처럼 업로드 전에도 섹션을 보여주고 안내 문구를 표시한다.
            if (filterWrapEl) { filterWrapEl.innerHTML = ''; filterWrapEl.style.display = 'none'; }
            palette.style.display = 'block';
            palette.style.height = 'auto';
            palette.style.maxHeight = 'none';
            palette.style.overflowY = 'visible';
            palette.style.overflowX = 'visible';
            palette.style.padding = '0';
            palette.style.paddingRight = '0';
            palette.style.marginTop = '6px';
            const placeholder = document.createElement('div');
            placeholder.className = 'cs-empty-result';
            placeholder.style.setProperty('min-height', '476px', 'important');
            placeholder.style.setProperty('height', '476px', 'important');
            placeholder.style.setProperty('flex', 'none', 'important');
            placeholder.style.setProperty('display', 'flex', 'important');
            placeholder.style.setProperty('align-items', 'center', 'important');
            placeholder.style.setProperty('justify-content', 'center', 'important');
            placeholder.style.setProperty('box-sizing', 'border-box', 'important');
            placeholder.textContent = csRecogEn ? 'Recognized shards will appear here after you upload images.' : '이미지 업로드를 완료하면 여기에 인식된 조각이 표시됩니다.';
            palette.appendChild(placeholder);
            return;
        }
        if (filterWrapEl) filterWrapEl.style.display = '';
        csRenderRecognizedFilter();
        const visibleData = pieceData.filter((data) => {
            if (csRecognizedFilter === 'all') return true;
            if (csRecognizedFilter === 'unique') return (data.grade || '') === 'unique';
            return (data.grade || '') !== 'unique' && data.selectedSet === csRecognizedFilter;
        });
        palette.style.display = 'grid';
        palette.style.gridTemplateColumns = 'repeat(auto-fill, minmax(118px, 1fr))';
        palette.style.gap = '10px';
        palette.style.padding = '0';
        palette.style.width = '100%';
        palette.style.height = 'auto';
        palette.style.maxHeight = '430px';
        palette.style.overflowY = 'auto';
        palette.style.overflowX = 'hidden';
        palette.style.marginTop = '6px';
        palette.style.paddingRight = '4px';
        palette.style.boxSizing = 'border-box';
        if (!visibleData.length) {
            const empty = document.createElement('div');
            empty.textContent = '선택한 세트의 조각이 없습니다.';
            empty.style.gridColumn = '1 / -1';
            empty.style.padding = '14px 10px';
            empty.style.borderRadius = '10px';
            empty.style.background = CS_DARK_UI ? '#303236' : '#f3f4f6';
            empty.style.color = 'var(--cs-muted, #9ca3af)';
            empty.style.fontWeight = '400';
            empty.style.fontSize = '12px';
            empty.style.lineHeight = '1.4';
            empty.style.textAlign = 'center';
            palette.appendChild(empty);
        }

        visibleData.forEach((data) => {
            const index = csRecognizedResults.indexOf(data);
            const piece = PIECES[data.pieceName];
            if (!piece) return;
            const grade = data.grade || 'rare';
            let gradeColor = 'rgba(200, 100, 255, 0.2)';
            let gradeBorderColor = 'rgba(200, 100, 255, 0.5)';
            if (grade === 'rare') {
                gradeColor = 'rgba(100, 150, 255, 0.2)';
                gradeBorderColor = 'rgba(100, 150, 255, 0.5)';
            } else if (grade === 'epic') {
                gradeColor = 'rgba(200, 100, 255, 0.2)';
                gradeBorderColor = 'rgba(200, 100, 255, 0.5)';
            } else if (grade === 'super') {
                gradeColor = 'rgba(255, 100, 100, 0.2)';
                gradeBorderColor = 'rgba(255, 100, 100, 0.5)';
            } else if (grade === 'unique') {
                gradeColor = 'rgba(255, 204, 0, 0.18)';
                gradeBorderColor = 'rgba(255, 204, 0, 0.65)';
                data.stats = null;
            }

            const pieceBlock = document.createElement('div');
            pieceBlock.dataset.grade = grade;
            pieceBlock.style.marginBottom = '0';
            pieceBlock.style.padding = '4px';
            pieceBlock.style.background = gradeColor;
            pieceBlock.style.borderRadius = '8px';
            pieceBlock.style.border = CS_DARK_UI ? '0' : `1px solid ${gradeBorderColor}`;
            pieceBlock.style.display = 'flex';
            pieceBlock.style.flexDirection = 'column';
            pieceBlock.style.alignItems = 'stretch';
            pieceBlock.style.justifyContent = 'flex-start';
            pieceBlock.style.gap = '4px';
            pieceBlock.style.width = '100%';
            pieceBlock.style.minWidth = '0';
            pieceBlock.style.boxSizing = 'border-box';
            // 내용물 합계(22+22+86+22 + gap 12 + padding 8) = 172. 라이트 모드는 1px 테두리 x2 = +2px.
            // 이렇게 해야 위(세트 칩)와 아래(x1) 여백이 다크/라이트 모두 4px로 동일해진다.
            const csRecogCardH = CS_DARK_UI ? '172px' : '174px';
            pieceBlock.style.height = csRecogCardH;
            pieceBlock.style.minHeight = csRecogCardH;
            pieceBlock.style.maxHeight = csRecogCardH;
            pieceBlock.style.position = 'relative';
            pieceBlock.style.overflow = 'visible';
            pieceBlock.style.boxShadow = 'none';
            pieceBlock.style.transform = 'none';

            const setChip = document.createElement('div');
            setChip.textContent = grade === 'unique' ? ((typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en') ? 'Unique' : '유니크') : ((SET_INFO[data.selectedSet] && SET_INFO[data.selectedSet].name) || ((typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en') ? 'Select Set' : '세트 선택'));
            setChip.style.width = '100%';
            setChip.style.height = '22px';
            setChip.style.minHeight = '22px';
            setChip.style.maxHeight = '22px';
            setChip.style.display = 'flex';
            setChip.style.alignItems = 'center';
            setChip.style.justifyContent = 'center';
            setChip.style.background = '#fff';
            setChip.style.borderRadius = '6px';
            setChip.style.padding = '4px 2px';
            setChip.style.boxSizing = 'border-box';
            setChip.style.textAlign = 'center';
            setChip.style.fontSize = '10px';
            setChip.style.fontWeight = '800';
            setChip.style.color = '#10b981';
            setChip.style.cursor = grade === 'unique' ? 'default' : 'pointer';
            setChip.classList.add('cs-set-chip');
            setChip.style.background = csRecognizedChipBg();
            setChip.style.color = '#10b981';
            if (grade !== 'unique') {
                setChip.title = '클릭해서 세트 수정';
                setChip.addEventListener('click', (ev) => {
                    ev.stopPropagation();
                    csOpenRecognizedSetPicker(data.selectedSet, (nextSet) => {
                        data.selectedSet = nextSet;
                        data.pieceName = `${nextSet}-${data.basePieceName}`;
                        csRecognizedSyncAndRender();
                    });
                });
            }
            pieceBlock.appendChild(setChip);

            let normalStatChip = null;
            if (grade !== 'unique') {
                normalStatChip = cookieSimMakeEditableStatChip(
                    data.stats || null,
                    () => parseInt(data.count || 1, 10) || 1,
                    (nextStats) => {
                        data.stats = nextStats;
                        fillPiecesFromCV(csRecognizedResults);
                    }
                );
            } else {
                normalStatChip = cookieSimMakeStatChip(null);
                normalStatChip.textContent = (typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en') ? 'None' : '없음';
                normalStatChip.style.setProperty('cursor', 'default', 'important');
                normalStatChip.style.setProperty('pointer-events', 'none', 'important');
            }
            normalStatChip.style.setProperty('width', '100%', 'important');
            normalStatChip.style.setProperty('height', '22px', 'important');
            normalStatChip.style.setProperty('min-height', '22px', 'important');
            normalStatChip.style.setProperty('max-height', '22px', 'important');
            normalStatChip.style.setProperty('flex', '0 0 22px', 'important');
            normalStatChip.style.setProperty('border-radius', '6px', 'important');
            normalStatChip.style.setProperty('padding', '4px 2px', 'important');
            normalStatChip.style.setProperty('font-size', '10px', 'important');
            normalStatChip.style.setProperty('font-weight', '800', 'important');
            pieceBlock.appendChild(normalStatChip);

            const preview = createPiecePreview({ shape: piece.shape, color: '#999999' });
            preview.style.setProperty('width', '100%', 'important');
            preview.style.setProperty('height', '86px', 'important');
            preview.style.setProperty('min-height', '86px', 'important');
            preview.style.setProperty('max-height', '86px', 'important');
            preview.style.setProperty('flex', '0 0 86px', 'important');
            preview.style.setProperty('background', csPreviewSurfaceBg(), 'important');
            preview.style.setProperty('border', '0', 'important');
            preview.style.setProperty('border-radius', '6px', 'important');
            preview.style.setProperty('padding', '0', 'important');
            preview.style.setProperty('margin', '0', 'important');
            preview.style.setProperty('box-shadow', 'none', 'important');
            preview.style.setProperty('box-sizing', 'border-box', 'important');
            preview.style.setProperty('overflow', 'hidden', 'important');
            preview.style.setProperty('display', 'flex', 'important');
            preview.style.setProperty('align-items', 'center', 'important');
            preview.style.setProperty('justify-content', 'center', 'important');
            preview.style.transform = 'none';
            const previewGrid = preview.firstElementChild;
            if (previewGrid) {
                previewGrid.style.setProperty('transform', 'scale(0.7)', 'important');
                previewGrid.style.setProperty('transform-origin', 'center center', 'important');
            }
            preview.style.cursor = 'pointer';
            preview.title = '클릭해서 조각 수정';
            preview.addEventListener('click', (ev) => {
                ev.stopPropagation();
                openCookieSimPiecePicker(data.basePieceName, (newPieceName) => {
                    data.basePieceName = newPieceName;
                    data.pieceName = `${data.selectedSet}-${newPieceName}`;
                    csRecognizedSyncAndRender();
                }, grade === 'unique' ? 'unique' : 'regular');
            });
            pieceBlock.appendChild(preview);

            const countBadge = document.createElement('div');
            countBadge.textContent = `×${Math.max(1, parseInt(data.count || 1, 10) || 1)}`;
            countBadge.dataset.role = 'count-badge';
            countBadge.style.fontSize = '10px';
            countBadge.style.fontWeight = '900';
            countBadge.style.color = csRecognizedGradeTextColor(grade);
            countBadge.style.padding = '4px 2px';
            countBadge.style.height = '22px';
            countBadge.style.minHeight = '22px';
            countBadge.style.maxHeight = '22px';
            countBadge.style.display = 'flex';
            countBadge.style.alignItems = 'center';
            countBadge.style.justifyContent = 'center';
            countBadge.style.background = '#fff';
            countBadge.classList.add('cs-count-badge', `cs-grade-${grade || 'epic'}`);
            countBadge.style.background = csRecognizedChipBg();
            countBadge.style.color = csRecognizedGradeTextColor(grade);
            countBadge.style.borderRadius = '6px';
            countBadge.style.width = '100%';
            countBadge.style.textAlign = 'center';
            countBadge.style.boxSizing = 'border-box';
            countBadge.style.cursor = 'pointer';
            countBadge.title = '클릭해서 개수 수정';
            countBadge.addEventListener('click', (ev) => {
                ev.stopPropagation();
                const current = parseInt(data.count || 1, 10) || 1;
                const next = prompt('개수를 입력하세요.', String(current));
                if (next === null) return;
                const n = Math.max(0, Math.min(99, parseInt(next, 10) || 0));
                data.count = n;
                if (grade !== 'unique') data.stats = csResizeStatsForCount(data.stats, Math.max(1, n));
                csRecognizedSyncAndRender();
            });
            pieceBlock.appendChild(countBadge);

            pieceBlock.appendChild(csRecognizedMakeRemoveBtn(() => {
                csRecognizedResults.splice(index, 1);
                csRecognizedSyncAndRender();
            }));
            palette.appendChild(pieceBlock);
        });

        // 맨 아래 '조각 추가' 카드 (사진별 세트 선택 모달의 addPieceCard 로직 복사)
        const addPieceCard = document.createElement('div');
        addPieceCard.style.width = '100%';
        addPieceCard.style.minWidth = '0';
        addPieceCard.style.height = CS_DARK_UI ? '172px' : '174px';
        addPieceCard.style.minHeight = addPieceCard.style.height;
        addPieceCard.style.maxHeight = addPieceCard.style.height;
        addPieceCard.style.boxSizing = 'border-box';
        addPieceCard.style.border = CS_DARK_UI ? '0' : '1px solid #d1d5db';
        addPieceCard.style.borderRadius = '8px';
        const addPieceCardBaseBg = CS_DARK_UI ? '#303236' : '#fff';
        const addPieceCardHoverBg = CS_DARK_UI ? '#34373d' : '#f7f8fa';
        addPieceCard.style.background = addPieceCardBaseBg;
        addPieceCard.style.transition = 'background-color .12s ease';
        addPieceCard.style.display = 'flex';
        addPieceCard.style.flexDirection = 'column';
        addPieceCard.style.alignItems = 'center';
        addPieceCard.style.justifyContent = 'center';
        addPieceCard.style.gap = '2px';
        addPieceCard.style.cursor = 'pointer';
        const addPlus = document.createElement('div');
        addPlus.textContent = '+';
        addPlus.style.fontSize = '26px';
        addPlus.style.fontWeight = '400';
        addPlus.style.lineHeight = '1';
        addPlus.style.color = '#9ca3af';
        const addLabel = document.createElement('div');
        addLabel.textContent = '조각 추가';
        addLabel.style.fontSize = '10px';
        addLabel.style.fontWeight = '800';
        addLabel.style.color = '#9ca3af';
        addPieceCard.appendChild(addPlus);
        addPieceCard.appendChild(addLabel);
        addPieceCard.addEventListener('mouseenter', () => { addPieceCard.style.background = addPieceCardHoverBg; });
        addPieceCard.addEventListener('mouseleave', () => { addPieceCard.style.background = addPieceCardBaseBg; });
        addPieceCard.addEventListener('click', () => {
            csOpenRecognizedGradeSelectModal((gradeKey) => {
                openCookieSimPiecePicker(null, (pName) => {
                    const firstSetKey = Object.keys(SET_INFO)[0] || 'dealer-radiance';
                    const setKey = (gradeKey === 'unique')
                        ? firstSetKey
                        : ((csRecognizedFilter !== 'all' && csRecognizedFilter !== 'unique') ? csRecognizedFilter : firstSetKey);
                    csRecognizedResults.push({
                        pieceName: `${setKey}-${pName}`,
                        selectedSet: setKey,
                        basePieceName: pName,
                        grade: gradeKey,
                        count: 1,
                        stats: null
                    });
                    csRecognizedSyncAndRender();
                }, gradeKey === 'unique' ? 'unique' : 'regular');
            });
        });
        palette.appendChild(addPieceCard);
    }

    function fillPiecesFromCV(pieceData) {
        resetPieceInputsOnly();

        let successCount = 0;

        pieceData.forEach((data) => {
            const { pieceName, grade, count } = data;
            const inputId = `piece-count-${pieceName}-${grade}`;
            const countInput = document.getElementById(inputId);

            if (countInput) {
                const currentValue = parseInt(countInput.value) || 0;
                countInput.value = currentValue + count;
                successCount++;
            } else {
                console.warn(` Input 없음: ${pieceName} (${grade})`);
            }
        });

        console.log(` ${successCount}/${pieceData.length}개 조각 입력 완료`);
    }

    function solve() {
        // Step 1: Check if map is created
        const targetCellCount = gridState.filter(Boolean).length;
        if (targetCellCount === 0) {
            solutionSummary.textContent = ` 맵을 먼저 만들어주세요!`;
            return;
        }

        // Step 2: Collect pieces from inputs
        piecesToUse = [];
        let piecesCellCount = 0;

        Object.entries(PIECES).forEach(([name, piece]) => {
            if (piece.isUnique) {
                // 유니크 조각: 등급 없이 항상 2000점 (칸당 250점)
                const uniqueInput = document.getElementById(`piece-count-${name}-unique`);
                if (uniqueInput) {
                    const count = parseInt(uniqueInput.value, 10);
                    if (count > 0) {
                        const uniqueScore = 2000; // 유니크는 항상 2000점 고정
                        for (let i = 0; i < count; i++) {
                            const uniqueName = `${name}_unique_${i}`;
                            piecesToUse.push({ name: uniqueName, baseName: name, ...piece, score: uniqueScore, grade: 'unique' });
                            piecesCellCount += piece.shape.length;
                        }
                    }
                }
            } else {
                // 일반 조각: 등급별 처리
                const grades = ['rare', 'epic', 'super'];
                grades.forEach(grade => {
                    const countInput = document.getElementById(`piece-count-${name}-${grade}`);
                    if (countInput) {
                        const count = parseInt(countInput.value, 10);
                        if (count > 0) {
                            const pieceScore = calculateScore(piece.cellCount, grade);
                            for (let i = 0; i < count; i++) {
                                const uniqueName = `${name}_${grade}_${i}`;
                                piecesToUse.push({ name: uniqueName, baseName: name, ...piece, score: pieceScore, grade: grade });
                                piecesCellCount += piece.shape.length;
                            }
                        }
                    }
                });
            }
        });

        if (piecesToUse.length === 0) {
            solutionSummary.textContent = ` 조각을 먼저 입력해주세요!`;
            return;
        }

        // 우선순위 세트 읽기 (1, 2, 3순위)
        const prioritySets = [
            document.getElementById('priority-set-1')?.value,
            document.getElementById('priority-set-2')?.value,
            document.getElementById('priority-set-3')?.value
        ].filter(s => s && s !== "");

        // 조각 정렬: 우선순위 → 높은 점수 → 큰 조각 순으로 변경
        if (PRIORITIZE_HIGH_SCORE) {
            piecesToUse.sort((a, b) => {
                const getPriorityLevel = (set) => {
                    const index = prioritySets.indexOf(set);
                    return index === -1 ? 4 : index + 1; // 1, 2, 3순위 또는 4(기타)
                };

                const aPriority = getPriorityLevel(a.set);
                const bPriority = getPriorityLevel(b.set);

                // 1. 우선순위 레벨로 정렬
                if (aPriority !== bPriority) {
                    return aPriority - bPriority;
                }

                // 2. 점수로 정렬 (높은 점수 우선)
                if (b.score !== a.score) {
                    return b.score - a.score;
                }

                // 3. 점수가 같으면 칸 수가 많은 것 우선 (큰 조각부터)
                return b.shape.length - a.shape.length;
            });
        }

        const MAX_UNIQUE_PIECES = 1;
        const MAX_REGULAR_PIECES = 15;

        dlxSolutions = [];
        dlxStartTime = Date.now();
        isSolving = true;
        solveBtn.disabled = true;
        resetGridBtn.disabled = true;
        clearPiecesBtn.disabled = true;

        solutionSummary.textContent = ` 계산 중... (맵 ${targetCellCount}칸, 조각 ${piecesToUse.length}개, 총 ${piecesCellCount}칸, 최대 ${MAX_UNIQUE_PIECES}유니크+${MAX_REGULAR_PIECES}일반 사용)`;
        solutionsContainer.innerHTML = '';

        const board = Array(GRID_SIZE * GRID_SIZE).fill(-1);
        gridState.forEach((unlocked, i) => {
            if (unlocked) {
                board[i] = 0;
            }
        });

        setTimeout(async () => {
            try {
                dlxNodesVisited = 0;
                dlxLastYield = Date.now();
                updateSolveProgress();
                bestScoreFound = -Infinity;
                bestTotalResistance = -Infinity;
                bestSolution = [];
                bestCellsFilled = 0;
                bestTargetsMet = 0;
                allSolutions = [];
                maxUniquePieces = MAX_UNIQUE_PIECES;
                maxRegularPieces = MAX_REGULAR_PIECES;

                // 유니크 조각이 입력되어 있으면 처음부터 같은 탐색 안에서 함께 배치한다.
                // 이전처럼 일반 조각 결과를 먼저 만든 뒤 유니크를 보완 탐색하지 않는다.
                const hasUniqueCandidates = piecesToUse.some(p => p.isUnique);
                requireUnique = hasUniqueCandidates;

                const root = createDlxMatrix(board, piecesToUse);
                // *** 변경점: search 함수에 prioritySets 전달 ***
                await search(root, [], 0, prioritySets);
                requireUnique = false;
                updateSolveProgress(true);
            } catch (e) {
                updateSolveProgress(true);
                console.error("DLX Solver Error:", e);
            }

            isSolving = false;
            solveBtn.disabled = false;
            resetGridBtn.disabled = false;
            clearPiecesBtn.disabled = false;

            // 모든 찾은 해결책에 대해 최종 점수 계산
            allSolutions.forEach(sol => {
                const processed = processDlxSolution(sol.solution, sol.score);
                sol.totalResistance = processed.score; // 세트 보너스 포함 총 저항
                sol.processed = processed; // 나중에 다시 사용하기 위해 저장
            });

            // *** 중요: 최종 해결책 정렬 기준 수정 ***
            // 1. 총 저항(점수)이 높을수록 우선
            // 2. 점수가 같으면 채운 칸 수가 많을수록 우선
            allSolutions.sort((a, b) => {
                if ((b.targetsMet || 0) !== (a.targetsMet || 0)) {
                    return (b.targetsMet || 0) - (a.targetsMet || 0);
                }
                if (b.totalResistance !== a.totalResistance) {
                    return b.totalResistance - a.totalResistance;
                }
                return b.cellsFilled - a.cellsFilled;
            });

            if (allSolutions.length > 0) {
                solutionsContainer.innerHTML = '';
                
                const solutionsToShow = allSolutions.slice(0, MAX_SOLUTIONS);
                solutionsToShow.forEach((sol, index) => {
                    // 이미 처리된 정보 사용
                    const p = sol.processed;
                    renderSolution(p.board, p.score, index + 1, p.usedPieces, p.pieceGrades, p.pieceSets, p.setBonusDetails, p.baseScore, p.setBonus);
                });

                const elapsed = ((Date.now() - dlxStartTime) / 1000).toFixed(1);
                const bestSol = allSolutions[0];
                const maxFilled = bestSol.cellsFilled;
                const totalCells = board.filter(id => id >= 0).length;
                const solutionCount = allSolutions.length;

                let priorityInfo = '';
                if (prioritySets.length > 0) {
                    const priorityLabels = ['', '', ''];
                    const priorityNames = prioritySets.map((set, i) =>
                        `${priorityLabels[i]} ${SET_INFO[set].name}`
                    ).join(', ');
                    priorityInfo = ` [${priorityNames}]`;
                }

                solutionSummary.textContent = ` ${solutionCount}개의 유효한 조합을 찾았습니다!${priorityInfo} (최고 저항: ${bestSol.totalResistance}, ${maxFilled}/${totalCells}칸, ${elapsed}초)`;

            } else {
                const elapsed = ((Date.now() - dlxStartTime) / 1000).toFixed(1);
                solutionSummary.textContent = ` 배치 방법을 찾지 못했습니다. (${elapsed}초)`;
                solutionsContainer.innerHTML = '<p style="text-align: center; color: #e74c3c; padding: 20px;">해결책을 찾지 못했습니다. 다른 조각 조합이나 더 넓은 맵을 시도해보세요.</p>';
            }
        }, 100);
    }

    function processDlxSolution(solution, score) {
        const newBoard = Array(GRID_SIZE * GRID_SIZE).fill(-1);
        let targetCellCount = 0; // Count cells that were initially fillable
        gridState.forEach((unlocked, i) => {
            if (unlocked) {
                newBoard[i] = 0; // Initialize fillable cells as 0
                targetCellCount++;
            }
        });

        let pieceId = 1;
        const usedPiecesDetails = [];
        const pieceGrades = {}; // pieceId -> grade 매핑
        const pieceSets = {}; // pieceId -> set 매핑
        const setCellCounts = {}; // 세트별 칸 수 카운트
        let sumOfPieceCells = 0;

        solution.forEach(node => {
            let pieceNode = node;
            // Find the node in the row that contains the piece info
            while (!pieceNode.pieceInfo && pieceNode.R !== node) {
                pieceNode = pieceNode.R;
            }
            if (pieceNode.pieceInfo) {
                const { piece, pos } = pieceNode.pieceInfo;
                const currentPieceId = pieceId++;
                placePiece(newBoard, piece.shape, pos[0], pos[1], currentPieceId);
                pieceGrades[currentPieceId] = piece.grade || 'rare'; // grade 정보 저장

                // 세트 정보 추출 및 카운트 (유니크 조각은 세트 보너스에 포함하지 않음)
                const pieceSet = piece.set || null;
                pieceSets[currentPieceId] = pieceSet; // 세트 정보 저장
                if (pieceSet && !piece.isUnique) {
                    setCellCounts[pieceSet] = (setCellCounts[pieceSet] || 0) + piece.shape.length;
                }

                usedPiecesDetails.push({
                    name: piece.name,
                    baseName: piece.baseName || piece.name,
                    score: piece.score,
                    shape: piece.shape,
                    grade: piece.grade,
                    set: pieceSet
                });
                sumOfPieceCells += piece.shape.length;
            }
        });

        // 세트 보너스 계산
        const { totalBonus, setBonusDetails } = calculateSetBonus(setCellCounts);
        const finalScore = score + totalBonus;

        const actualFilledCells = newBoard.filter(id => id > 0).length;

        console.log(`--- Solution Details ---`);
        console.log(`Base Score: ${score}`);
        console.log(`Set Bonus: ${totalBonus}`);
        console.log(`Final Score: ${finalScore}`);
        console.log(`Target Fillable Cells: ${targetCellCount}`);
        console.log(`Sum of Cells from Used Pieces: ${sumOfPieceCells}`);
        console.log(`Actual Filled Cells on Board: ${actualFilledCells}`);
        console.log("Used Pieces:");
        usedPiecesDetails.forEach(p => console.log(`  - ${p.name} (Score: ${p.score}, Cells: ${p.shape.length}, Set: ${p.set || 'common'})`));
        console.log("Set Bonuses:");
        Object.entries(setBonusDetails).forEach(([setKey, details]) => {
            console.log(`  - ${SET_INFO[setKey].name}: ${details.cellCount}칸, +${details.bonus} 저항 (${details.thresholds.join(', ')}칸 달성)`);
        });
        console.log("------------------------------------");

        return {
            board: newBoard,
            score: finalScore,
            baseScore: score,
            setBonus: totalBonus,
            setBonusDetails: setBonusDetails,
            usedPieces: usedPiecesDetails,
            pieceGrades: pieceGrades,
            pieceSets: pieceSets,
            setCellCounts: setCellCounts
        };
    }

    function canPlace(board, shape, row, col) {
        for (const [dr, dc] of shape) {
            const r = row + dr;
            const c = col + dc;
            if (r < 0 || r >= GRID_SIZE || c < 0 || c >= GRID_SIZE || board[r * GRID_SIZE + c] !== 0) {
                return false;
            }
        }
        return true;
    }

    function placePiece(board, shape, row, col, id) {
        for (const [dr, dc] of shape) {
            board[(row + dr) * GRID_SIZE + (col + dc)] = id;
        }
    }

    // Generate distinct colors for each piece
    function generateDistinctColors(count) {
        const colors = [];
        const goldenRatio = 0.618033988749895;
        let hue = Math.random();

        for (let i = 0; i < count; i++) {
            hue += goldenRatio;
            hue %= 1;
            const saturation = 0.6 + Math.random() * 0.2;
            const lightness = 0.5 + Math.random() * 0.2;
            colors.push(`hsl(${Math.floor(hue * 360)}, ${Math.floor(saturation * 100)}%, ${Math.floor(lightness * 100)}%)`);
        }
        return colors;
    }

    function renderSolution(board, totalScore = 0, solutionNumber = 1, usedPieces = [], pieceGrades = {}, pieceSets = {}, setBonusDetails = {}, baseScore = 0, setBonus = 0) {
        // Create wrapper for solution
        const solutionWrapper = document.createElement('div');
        solutionWrapper.classList.add('solution-wrapper');

        // Add solution header
        const solutionHeader = document.createElement('div');
        solutionHeader.classList.add('solution-header');

        // Count pieces used and cells filled
        const uniquePieceIds = new Set(board.filter(id => id > 0));
        const filledCells = board.filter(id => id > 0).length;
        const totalCells = board.filter(id => id >= 0).length;

        let headerHTML = `
            <span class="solution-number">해결책 #${solutionNumber}</span>
            <span class="solution-stats">블록 ${uniquePieceIds.size}개 사용 | ${filledCells}/${totalCells} 칸 채움 | 총 저항: ${totalScore}`;

        if (setBonus > 0) {
            headerHTML += ` (기본: ${baseScore} + 세트: ${setBonus})`;
        }
        headerHTML += `</span>`;

        solutionHeader.innerHTML = headerHTML;
        solutionWrapper.appendChild(solutionHeader);

        // Add set bonus details if any
        if (Object.keys(setBonusDetails).length > 0) {
            const setBonusContainer = document.createElement('div');
            setBonusContainer.style.padding = '10px';
            setBonusContainer.style.background = 'rgba(102, 126, 234, 0.1)';
            setBonusContainer.style.borderRadius = '6px';
            setBonusContainer.style.marginBottom = '10px';
            setBonusContainer.style.fontSize = '0.9em';

            const setBonusTitle = document.createElement('div');
            setBonusTitle.textContent = '세트 효과 보너스';
            setBonusTitle.style.fontWeight = 'bold';
            setBonusTitle.style.marginBottom = '2px';
            setBonusTitle.style.color = '#667eea';
            setBonusContainer.appendChild(setBonusTitle);

            Object.entries(setBonusDetails).forEach(([setKey, details]) => {
                const setInfo = document.createElement('div');
                setInfo.style.marginLeft = '10px';
                setInfo.style.marginBottom = '1px';
                setInfo.textContent = `${SET_INFO[setKey].icon} ${SET_INFO[setKey].name}: ${details.cellCount}칸 → +${details.bonus} 저항 (${details.thresholds.join(', ')}칸 단계 달성)`;
                setBonusContainer.appendChild(setInfo);
            });

            solutionWrapper.appendChild(setBonusContainer);
        }

        const solutionGrid = document.createElement('div');
        solutionGrid.classList.add('solution-grid');

        // Generate colors for each piece
        const pieceColors = generateDistinctColors(piecesToUse.length);

        // Create 2D array to detect borders
        const grid2D = [];
        for (let r = 0; r < GRID_SIZE; r++) {
            grid2D[r] = [];
            for (let c = 0; c < GRID_SIZE; c++) {
                grid2D[r][c] = board[r * GRID_SIZE + c];
            }
        }

        for (let i = 0; i < GRID_SIZE * GRID_SIZE; i++) {
            const cell = document.createElement('div');
            cell.classList.add('solution-cell');
            const pieceId = board[i];
            const row = Math.floor(i / GRID_SIZE);
            const col = i % GRID_SIZE;

            if (pieceId > 0) {
                // Apply grade-based color
                const grade = pieceGrades[pieceId] || 'rare';
                let finalColor;

                if (grade === 'rare') {
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

                cell.style.backgroundColor = finalColor;
                cell.style.position = 'relative';

                // Add borders between different pieces
                const borderWidth = '3px';
                const borderColor = 'black';

                // Check top
                if (row === 0 || grid2D[row - 1][col] !== pieceId) {
                    cell.style.borderTop = `${borderWidth} solid ${borderColor}`;
                }
                // Check bottom
                if (row === GRID_SIZE - 1 || grid2D[row + 1][col] !== pieceId) {
                    cell.style.borderBottom = `${borderWidth} solid ${borderColor}`;
                }
                // Check left
                if (col === 0 || grid2D[row][col - 1] !== pieceId) {
                    cell.style.borderLeft = `${borderWidth} solid ${borderColor}`;
                }
                // Check right
                if (col === GRID_SIZE - 1 || grid2D[row][col + 1] !== pieceId) {
                    cell.style.borderRight = `${borderWidth} solid ${borderColor}`;
                }

                // Add overlay pattern for locked cells
                if (lockedCells.has(i)) {
                    const overlay = document.createElement('div');
                    overlay.style.position = 'absolute';
                    overlay.style.top = '0';
                    overlay.style.left = '0';
                    overlay.style.right = '0';
                    overlay.style.bottom = '0';
                    overlay.style.background = 'repeating-linear-gradient(45deg, rgba(255,255,255,0.1), rgba(255,255,255,0.1) 4px, rgba(0,0,0,0.05) 4px, rgba(0,0,0,0.05) 8px)';
                    overlay.style.pointerEvents = 'none';
                    cell.appendChild(overlay);
                }

                // Add piece number and set icon in the center of each piece
                const isCenter = isPieceCenter(grid2D, row, col, pieceId);
                if (isCenter) {
                    const pieceGrade = pieceGrades[pieceId] || 'rare';
                    let setIcon = '';
                    
                    // 유니크 조각은 세트 효과가 없으므로 별표 이모지 사용
                    if (pieceGrade === 'unique') {
                        setIcon = '';
                    } else {
                        const pieceSet = pieceSets[pieceId];
                        setIcon = pieceSet && SET_INFO[pieceSet] ? SET_INFO[pieceSet].icon : '';
                    }
                    
                    cell.textContent = `${setIcon} ${pieceId}`;
                    cell.style.display = 'flex';
                    cell.style.alignItems = 'center';
                    cell.style.justifyContent = 'center';
                    cell.style.fontWeight = 'bold';
                    cell.style.fontSize = '0.75em';
                    cell.style.color = '#fff';
                    cell.style.textShadow = '1px 1px 2px rgba(0,0,0,0.5)';
                    cell.style.zIndex = '1';
                }
            } else if (pieceId === 0) {
                // Empty cell that should have been filled - 회색 + X 표시
                cell.style.position = 'relative';
                cell.style.display = 'flex';
                cell.style.alignItems = 'center';
                cell.style.justifyContent = 'center';
                cell.style.overflow = 'hidden';

                if (lockedCells.has(i)) {
                    cell.style.backgroundColor = '#d1d5db';
                    cell.style.border = '2px solid #9ca3af';
                    cell.style.boxShadow = 'inset 0 0 6px rgba(107, 114, 128, 0.25)';
                } else {
                    cell.style.backgroundColor = '#e5e7eb';
                    cell.style.border = '2px solid #9ca3af';
                    cell.style.boxShadow = 'inset 0 0 6px rgba(107, 114, 128, 0.20)';
                }

                cell.innerHTML = `
                    <span style="
                        display:flex;
                        align-items:center;
                        justify-content:center;
                        width:100%;
                        height:100%;
                        color:#6b7280;
                        font-size:13px;
                        font-weight:900;
                        line-height:1;
                        text-shadow:none;
                        position:relative;
                        z-index:5;
                    ">×</span>
                `;
            }
            solutionGrid.appendChild(cell);
        }
        const csGlassStats = ((typeof window !== 'undefined' && window.COOKIE_SIM_GLASS_STAT_ITEMS) || [])
            .filter(x => x && x.name && Number(x.cells) > 0);
        if (csGlassStats.length > 0) {
            const csIsEn = (typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en');

            // ---- 스탯 배치 계산: 배치된 조각을 스탯별 목표 칸 수에 맞게 분할 ----
            const cellCountByPiece = {};
            for (let i = 0; i < board.length; i++) {
                const id = board[i];
                if (id > 0) cellCountByPiece[id] = (cellCountByPiece[id] || 0) + 1;
            }
            const uniquePieceIdSet = new Set();
            Object.keys(cellCountByPiece).forEach(id => {
                if ((pieceGrades[id] || '') === 'unique') uniquePieceIdSet.add(Number(id));
            });
            const regularPieces = Object.keys(cellCountByPiece).map(Number)
                .filter(id => !uniquePieceIdSet.has(id))
                .map(id => ({ id, size: cellCountByPiece[id] }))
                .sort((a, b) => b.size - a.size);
            const statTargets = csGlassStats.map(s => Number(s.cells));
            const statAssign = {};
            const statActualCells = Array(csGlassStats.length).fill(0);
            let statUnknownCells = 0;
            function csStatPoolKeyFromUsedPiece(det) {
                if (!det) return null;
                // baseName에는 선택된 세트까지 들어간다. 예: supporter-blessing-L5-0
                // confirm 단계에서 만든 스탯 풀도 같은 키 형식이므로 그대로 맞춘다.
                const base = det.baseName || String(det.name || '').replace(new RegExp(`_${det.grade || 'rare'}_\\d+$`), '');
                return `${base}-${det.grade}`;
            }
            (function assignPiecesToStats() {
                const statIdxByName = {};
                csGlassStats.forEach((s, idx) => { statIdxByName[s.name] = idx; });
                const statPools = {};
                const rawPools = (typeof window !== 'undefined' && window.COOKIE_SIM_PIECE_STAT_COUNTS) || {};
                Object.keys(rawPools).forEach(k => { statPools[k] = Object.assign({}, rawPools[k]); });

                regularPieces.forEach(({ id, size }) => {
                    const det = usedPieces[id - 1] || null;
                    const key = csStatPoolKeyFromUsedPiece(det);
                    const pool = key ? statPools[key] : null;
                    let picked = null;

                    if (pool) {
                        // 실제 사진에서 인식된 스탯만 사용한다. 목표 칸 수에 맞추려고 미상 조각을 임의 배정하지 않는다.
                        const cand = Object.keys(pool)
                            .filter(n => pool[n] > 0 && statIdxByName[n] !== undefined)
                            .sort((a, b) => pool[b] - pool[a]);
                        if (cand.length > 0) {
                            const n = cand[0];
                            picked = { n, idx: statIdxByName[n] };
                        }
                    }

                    if (picked) {
                        pool[picked.n] -= 1;
                        statAssign[id] = picked.idx;
                        statActualCells[picked.idx] += size;
                    } else {
                        // 목표 스탯이 아니거나 스탯 인식 실패한 조각은 회색으로 표시한다.
                        statUnknownCells += size;
                    }
                });
            })();

            // ---- 스탯 보드: 세트 보드를 복제해 스탯 색으로 재도색 ----
            const statPalette = [
                '#A9DFF3', // 소프트 스카이
                '#B7D2FF', // 연한 블루
                '#C8BCFF', // 라벤더
                '#AEE8DF', // 쿨 민트
                '#D8C8FF', // 연보라
                '#BFE8FF', // 아이스 블루
                '#B9EAD8', // 민트그린
                '#D7E2FF', // 블루그레이
                '#E0D2FF', // 페일 퍼플
                '#C7EEF2', // 시안 민트
                '#F0C5D6'  // 아주 연한 로즈
            ];

            const statUnknownColor = '#EDF0F4';
            const statGrid = solutionGrid.cloneNode(true);
            // 세트 구분 보드와 스탯 배치 보드의 그림체/크기/선/숫자 스타일을 완전히 동일하게 고정한다.
            statGrid.className = solutionGrid.className;
            statGrid.style.cssText = solutionGrid.style.cssText;
            Array.from(statGrid.children).forEach((cell, idx) => {
                const srcCell = solutionGrid.children[idx];
                if (!srcCell) return;
                cell.className = srcCell.className;
                cell.style.cssText = srcCell.style.cssText;
                cell.style.removeProperty('font-size');
                const span = cell.querySelector('span');
                if (span) span.style.removeProperty('font-size');
            });
            const statCells = statGrid.children;
            for (let i = 0; i < board.length && i < statCells.length; i++) {
                const id = board[i];
                if (id > 0) {
                    if (uniquePieceIdSet.has(id)) {
                        statCells[i].style.backgroundColor = CS_UNIQUE_COLOR;
                    } else if (statAssign[id] !== undefined) {
                        statCells[i].style.backgroundColor = statPalette[statAssign[id] % statPalette.length];
                    } else {
                        statCells[i].style.backgroundColor = statUnknownColor;
                    }
                }
            }

            // ---- 스탯 범례 (세트 효과 보너스 박스와 같은 자리/스타일) ----
            const statLegend = document.createElement('div');
            statLegend.className = 'cs-set-bonus-box cs-stat-legend';
            statLegend.style.background = '#fff7f7';
            statLegend.style.borderRadius = '10px';
            statLegend.style.marginBottom = '0px';
            statLegend.style.border = 'none';
            statLegend.style.width = '100%';
            statLegend.style.boxSizing = 'border-box';
            statLegend.style.textAlign = 'left';
            statLegend.style.padding = '10px 10px';
            statLegend.style.fontSize = '12px';
            statLegend.style.lineHeight = '1.45';
            statLegend.style.color = CS_DARK_UI ? '#f3f4f6' : '#111827';
            if (uniquePieceIdSet.size > 0) {
                const line = document.createElement('div');
                line.className = 'cs-stat-legend-line';
                line.style.fontSize = '12px';
                line.style.lineHeight = '1.45';
                line.style.color = CS_DARK_UI ? '#f3f4f6' : '#111827';
                const chip = document.createElement('span');
                chip.className = 'cs-stat-legend-chip';
                chip.style.background = CS_UNIQUE_COLOR;
                const label = document.createElement('span');
                label.textContent = csIsEn ? 'Unique: 8 cells' : '유니크: 8칸';
                line.appendChild(chip);
                line.appendChild(label);
                statLegend.appendChild(line);
            }
            csGlassStats.forEach((s, idx) => {
                const line = document.createElement('div');
                line.className = 'cs-stat-legend-line';
                line.style.fontSize = '12px';
                line.style.lineHeight = '1.45';
                line.style.color = CS_DARK_UI ? '#f3f4f6' : '#111827';
                const chip = document.createElement('span');
                chip.className = 'cs-stat-legend-chip';
                chip.style.background = statPalette[idx % statPalette.length];
                const label = document.createElement('span');
                const actual = statActualCells[idx] || 0;
                label.textContent = csIsEn ? `${csTranslateStatName(s.name)}: ${actual}/${s.cells} cells` : `${s.name}: ${actual}/${s.cells}칸`;
                line.appendChild(chip);
                line.appendChild(label);
                statLegend.appendChild(line);
            });
            if (statUnknownCells > 0) {
                const line = document.createElement('div');
                line.className = 'cs-stat-legend-line';
                line.style.fontSize = '12px';
                line.style.lineHeight = '1.45';
                line.style.color = CS_DARK_UI ? '#f3f4f6' : '#111827';
                const chip = document.createElement('span');
                chip.className = 'cs-stat-legend-chip';
                chip.style.background = statUnknownColor;
                const label = document.createElement('span');
                label.textContent = csIsEn ? `Other: ${statUnknownCells} cells` : `대상 외: ${statUnknownCells}칸`;
                line.appendChild(chip);
                line.appendChild(label);
                statLegend.appendChild(line);
            }

            // ---- 결과 표시: 기본은 세트 보드 1개만 표시하고, 화살표로 스탯 보드와 전환 ----
            solutionWrapper.classList.add('cs-board-result-wrapper');
            solutionWrapper._csGrid2D = grid2D;

            // 기존 헤더는 제거한다. 결과 상단 제목은 바깥 카드의 '배치 결과'만 사용한다.
            if (solutionHeader && solutionHeader.parentNode) {
                solutionHeader.parentNode.removeChild(solutionHeader);
            }

            // 세트 효과 보너스 박스 준비
            let bonusBox = solutionWrapper.querySelector('.cs-set-bonus-box') || solutionWrapper.querySelector('div[style*="fff7f7"]');
            if (!bonusBox) {
                bonusBox = document.createElement('div');
                bonusBox.className = 'cs-set-bonus-box';
            }
            bonusBox.classList.add('cs-set-bonus-box');
            if (bonusBox.parentNode) {
                bonusBox.parentNode.removeChild(bonusBox);
            }
            bonusBox.innerHTML = '';

            function csAppendCompactLine(parent, color, text) {
                const line = document.createElement('div');
                line.className = 'cs-stat-legend-line';
                line.style.fontSize = '12px';
                line.style.lineHeight = '1.45';
                line.style.color = CS_DARK_UI ? '#f3f4f6' : '#111827';
                line.style.display = 'flex';
                line.style.alignItems = 'center';
                line.style.gap = '6px';
                line.style.margin = '1px 0';
                const chip = document.createElement('span');
                chip.className = 'cs-stat-legend-chip';
                chip.style.background = color;
                const label = document.createElement('span');
                label.textContent = text;
                line.appendChild(chip);
                line.appendChild(label);
                parent.appendChild(line);
            }

            if (uniquePieceIdSet.size > 0) {
                csAppendCompactLine(bonusBox, CS_UNIQUE_COLOR, csIsEn ? 'Unique: 8 cells' : '유니크: 8칸');
            }
            Object.entries(setBonusDetails).forEach(([setKey, details]) => {
                const info = SET_INFO[setKey] || {};
                const name = info.name || setKey;
                const color = info.color || '#d1d5db';
                csAppendCompactLine(bonusBox, color, csIsEn ? `${name}: ${details.cellCount} cells` : `${name}: ${details.cellCount}칸`);
            });

            // 저항 표시는 세트 보너스 상세 안에 한 번만 넣는다.
            if (bonusBox) {
                const bonusDivider = document.createElement('div');
                bonusDivider.dataset.csResistance = '1';
                bonusDivider.style.height = '1px';
                bonusDivider.style.background = CS_DARK_UI
                    ? 'rgba(243, 244, 246, 0.12)'
                    : 'rgba(17, 24, 39, 0.08)';
                bonusDivider.style.margin = '6px 0 4px 0';
                const bonusResistance = document.createElement('div');
                bonusResistance.dataset.csResistance = '1';
                bonusResistance.textContent = csIsEn ? `Resistance : ${totalScore}` : `저항 : ${totalScore}`;
                bonusResistance.style.fontWeight = '400';
                bonusResistance.style.color = CS_DARK_UI ? '#f3f4f6' : '#111827';
                bonusResistance.style.fontSize = '12px';
                bonusResistance.style.lineHeight = '1.45';
                bonusBox.appendChild(bonusDivider);
                bonusBox.appendChild(bonusResistance);
            }

            const resultRoot = document.createElement('div');
            resultRoot.className = 'cs-result-main';

            const boardRow = document.createElement('div');
            boardRow.className = 'cs-result-board-row';

            const prevButton = document.createElement('button');
            prevButton.type = 'button';
            prevButton.className = 'cs-result-arrow cs-result-arrow-prev';
            prevButton.textContent = '‹';
            prevButton.setAttribute('aria-label', csIsEn ? 'Show previous view' : '이전 보기');

            const boardPanel = document.createElement('div');
            boardPanel.className = 'cs-board-panel';

            solutionGrid.classList.add('cs-result-visible-board', 'cs-set-board-view');
            statGrid.classList.add('cs-result-visible-board', 'cs-stat-board-view');
            statGrid.style.display = 'none';

            boardPanel.appendChild(solutionGrid);
            boardPanel.appendChild(statGrid);

            const nextButton = document.createElement('button');
            nextButton.type = 'button';
            nextButton.className = 'cs-result-arrow cs-result-arrow-next';
            nextButton.textContent = '›';
            nextButton.setAttribute('aria-label', csIsEn ? 'Show next view' : '다음 보기');

            boardRow.appendChild(prevButton);
            boardRow.appendChild(boardPanel);
            boardRow.appendChild(nextButton);
            resultRoot.appendChild(boardRow);

            const detailMount = document.createElement('div');
            detailMount.className = 'cs-current-detail-mount';
            resultRoot.appendChild(detailMount);

            function csDrawBoard(grid, gridMap) {
                if (!grid) return;
                if (typeof cookieSimScheduleBoardLines === 'function') {
                    cookieSimScheduleBoardLines(grid, gridMap);
                } else if (typeof cookieSimDrawBoardLines === 'function') {
                    cookieSimDrawBoardLines(grid, gridMap);
                }
            }

            function csMakeToggleButton(titleClosed, titleOpen, content, afterOpen) {
                const wrap = document.createElement('div');
                wrap.className = 'cs-result-detail-area';

                const button = document.createElement('button');
                button.type = 'button';
                button.className = 'cs-result-control-chip cs-result-toggle-wide';
                button.setAttribute('aria-expanded', 'false');

                const label = document.createElement('span');
                label.textContent = titleClosed;
                const arrow = document.createElement('span');
                arrow.className = 'cs-result-control-arrow';
                arrow.textContent = ''; // CSS chevron

                button.appendChild(label);
                button.appendChild(arrow);

                const body = document.createElement('div');
                body.className = 'cs-result-detail-content';
                body.style.display = 'none';
                body.appendChild(content);

                let open = false;
                const sync = () => {
                    body.style.display = open ? '' : 'none';
                    button.setAttribute('aria-expanded', open ? 'true' : 'false');
                    button.classList.toggle('active', open);
                    label.textContent = open ? titleOpen : titleClosed;
                    arrow.textContent = '';
                    arrow.classList.toggle('open', open);
                    if (typeof resultRoot !== 'undefined' && resultRoot) {
                        resultRoot.classList.toggle('cs-detail-open', open);
                    }
                    if (open && typeof afterOpen === 'function') {
                        requestAnimationFrame(() => requestAnimationFrame(afterOpen));
                    }
                };
                button.addEventListener('click', (event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    open = !open;
                    sync();
                });
                wrap._csClose = () => {
                    open = false;
                    sync();
                };
                wrap.appendChild(button);
                wrap.appendChild(body);
                sync();
                return wrap;
            }

            const setDetailToggle = csMakeToggleButton(
                csIsEn ? 'Show set effect bonus' : '세트 효과 보너스 보기',
                csIsEn ? 'Hide set effect bonus' : '세트 효과 보너스 숨기기',
                bonusBox,
                () => csDrawBoard(solutionGrid, grid2D)
            );

            const statDetailToggle = csMakeToggleButton(
                csIsEn ? 'Show recognized stat allocation' : '인식된 스탯 배치 보기',
                csIsEn ? 'Hide recognized stat allocation' : '인식된 스탯 배치 숨기기',
                statLegend,
                () => csDrawBoard(statGrid, grid2D)
            );

            let csCurrentBoardView = 0; // 0: 세트 효과 보드, 1: 인식된 스탯 보드
            function csSyncBoardView() {
                const showingStat = csCurrentBoardView === 1;
                solutionGrid.style.display = showingStat ? 'none' : '';
                statGrid.style.display = showingStat ? '' : 'none';

                setDetailToggle._csClose?.();
                statDetailToggle._csClose?.();
                detailMount.innerHTML = '';
                detailMount.appendChild(showingStat ? statDetailToggle : setDetailToggle);

                requestAnimationFrame(() => requestAnimationFrame(() => {
                    csDrawBoard(showingStat ? statGrid : solutionGrid, grid2D);
                }));
            }

            function csSwitchBoardView(event) {
                if (event) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                csCurrentBoardView = csCurrentBoardView === 0 ? 1 : 0;
                csSyncBoardView();
            }

            prevButton.addEventListener('click', csSwitchBoardView);
            nextButton.addEventListener('click', csSwitchBoardView);

            if (solutionNumber > 1) {
                solutionWrapper.style.display = 'none';
            }

            csSyncBoardView();
            solutionWrapper.appendChild(resultRoot);
        } else {
            solutionWrapper.appendChild(solutionGrid);
        }
        solutionsContainer.appendChild(solutionWrapper);
    }

    // Find approximate center of each piece for labeling
    function isPieceCenter(grid2D, row, col, pieceId) {
        const cells = [];
        for (let r = 0; r < GRID_SIZE; r++) {
            for (let c = 0; c < GRID_SIZE; c++) {
                if (grid2D[r][c] === pieceId) {
                    cells.push([r, c]);
                }
            }
        }

        if (cells.length === 0) return false;

        // Calculate centroid
        const avgRow = cells.reduce((sum, [r]) => sum + r, 0) / cells.length;
        const avgCol = cells.reduce((sum, [, c]) => sum + c, 0) / cells.length;

        // Find closest cell to centroid
        let minDist = Infinity;
        let centerCell = cells[0];
        for (const [r, c] of cells) {
            const dist = Math.sqrt((r - avgRow) ** 2 + (c - avgCol) ** 2);
            if (dist < minDist) {
                minDist = dist;
                centerCell = [r, c];
            }
        }

        return row === centerCell[0] && col === centerCell[1];
    }
    
    // --- 5. Solver Logic (DLX - Dancing Links) ---
    let dlxSolutions = [];
    let dlxStartTime = 0;

    function createDlxMatrix(board, pieces) {
        const fillableCells = [];
        board.forEach((val, i) => {
            if (val === 0) fillableCells.push(i);
        });

        // Primary columns: one for each fillable cell (must be covered)
        const primaryColDefinitions = fillableCells.map(cellIdx => ({ name: `cell_${cellIdx}`, type: 'primary' }));

        // Secondary columns: one for each piece instance (can be covered at most once, optional)
        const secondaryColDefinitions = pieces.map(piece => ({ name: `piece_${piece.name}`, type: 'secondary' }));

        const allColDefinitions = [...primaryColDefinitions, ...secondaryColDefinitions];
        const colMap = new Map(); // To quickly find column objects by name

        const root = { R: null, L: null, name: 'root' };
        root.R = root;
        root.L = root;

        let currentHeader = root;
        allColDefinitions.forEach(h => {
            const newCol = { U: null, D: null, L: currentHeader, R: root, size: 0, name: h.name, type: h.type };
            newCol.U = newCol;
            newCol.D = newCol;
            currentHeader.R = newCol;
            currentHeader = newCol;
            colMap.set(h.name, newCol);
        });
        root.L = currentHeader; // Close the circular list of columns

        // Rows: one for each valid placement of a piece
        for (let i = 0; i < pieces.length; i++) {
            const piece = pieces[i];
            const pieceSecondaryCol = colMap.get(`piece_${piece.name}`); // Get the secondary column for this piece instance

            for (let r = 0; r < GRID_SIZE; r++) {
                for (let c = 0; c < GRID_SIZE; c++) {
                    if (canPlace(board, piece.shape, r, c)) {
                        const coveredCells = piece.shape.map(([dr, dc]) => (r + dr) * GRID_SIZE + (c + dc));
                        const cellColNames = coveredCells.map(cellPos => `cell_${cellPos}`);

                        // Ensure all covered cells are actually fillable (primary columns exist for them)
                        // This check is technically redundant if canPlace is correct, but good for robustness
                        if (cellColNames.some(name => !colMap.has(name) || colMap.get(name).type !== 'primary')) {
                            continue;
                        }

                        // Create a new row
                        const rowNodes = [];
                        // Node for the piece's secondary column
                        rowNodes.push({ col: pieceSecondaryCol, pieceInfo: { piece, pos: [r, c] } });
                        // Nodes for the cell primary columns
                        cellColNames.forEach(colName => {
                            rowNodes.push({ col: colMap.get(colName) });
                        });

                        // Link nodes together
                        if (rowNodes.length > 0) {
                            let firstNode = null, prevNode = null;
                            rowNodes.forEach(nodeData => {
                                const newNode = {
                                    U: nodeData.col.U,
                                    D: nodeData.col,
                                    L: null,
                                    R: null,
                                    C: nodeData.col,
                                    pieceInfo: nodeData.pieceInfo || null
                                };
                                nodeData.col.U.D = newNode;
                                nodeData.col.U = newNode;
                                nodeData.col.size++;

                                if (!firstNode) firstNode = newNode;
                                if (prevNode) {
                                    newNode.L = prevNode;
                                    prevNode.R = newNode;
                                }
                                prevNode = newNode;
                            });
                            firstNode.L = prevNode;
                            prevNode.R = firstNode;
                        }
                    }
                }
            }
        }
        return root;
    }

    function cover(c) {
        c.R.L = c.L;
        c.L.R = c.R;
        for (let i = c.D; i !== c; i = i.D) {
            for (let j = i.R; j !== i; j = j.R) {
                j.D.U = j.U;
                j.U.D = j.D;
                j.C.size--;
            }
        }
    }

    function uncover(c) {
        for (let i = c.U; i !== c; i = i.U) {
            for (let j = i.L; j !== i; j = j.L) {
                j.C.size++;
                j.D.U = j;
                j.U.D = j;
            }
        }
        c.R.L = c;
        c.L.R = c;
    }

    let bestScoreFound = -Infinity;
    let bestTotalResistance = -Infinity; // 세트 보너스 포함 총 저항
    let bestTargetsMet = 0; // 목표 세트 달성 개수 (최우선 순위 키)
    let bestSolution = [];
    let bestCellsFilled = 0;
    let allSolutions = [];
    let maxUniquePieces = 1;
    let maxRegularPieces = 15;
    let requireUnique = false;          // 2차 탐색: 유니크 포함 해만 기록
    let dlxTimeBudget = MAX_TIME_MS;    // 탐색 단계별 시간 예산
    let dlxNodesVisited = 0;            // 탐색한 경로(노드) 수
    let dlxLastYield = 0;               // 마지막으로 이벤트 루프에 양보한 시각

    function ensureSolveProgress() {
        let el = document.getElementById('cs-solve-progress');
        if (!el) {
            el = document.createElement('div');
            el.id = 'cs-solve-progress';
            const btn = document.getElementById('solve-btn');
            const row = btn ? btn.parentElement : null;
            if (row && row.parentElement) {
                row.parentElement.insertBefore(el, row.nextSibling);
            } else if (btn) {
                btn.insertAdjacentElement('afterend', el);
            } else {
                return null;
            }
        }
        return el;
    }

    function updateSolveProgress(done) {
        const el = ensureSolveProgress();
        if (!el) return;
        if (done) { el.textContent = ''; el.style.display = 'none'; return; }
        el.style.display = '';
        const elapsed = ((Date.now() - dlxStartTime) / 1000).toFixed(1);
        const budget = Math.round(dlxTimeBudget / 1000);
        el.textContent = (typeof window !== 'undefined' && window.COOKIE_SIM_LANG === 'en')
            ? `Searching: ${dlxNodesVisited.toLocaleString()} paths · ${elapsed}s / ${budget}s`
            : `탐색 중: ${dlxNodesVisited.toLocaleString()}개 경로 확인 · ${elapsed}초 / ${budget}초`;
    }

    async function search(root, partialSolution = [], currentScore = 0, prioritySets = []) {
        if (Date.now() - dlxStartTime > dlxTimeBudget) {
            return;
        }
        dlxNodesVisited++;
        // 주기적으로 이벤트 루프에 양보해 '응답 없는 페이지' 경고를 방지하고 진행 현황을 갱신
        if (Date.now() - dlxLastYield > 60) {
            dlxLastYield = Date.now();
            updateSolveProgress();
            await new Promise(resolve => setTimeout(resolve, 0));
            if (Date.now() - dlxStartTime > dlxTimeBudget) {
                return;
            }
        }

        let uncoveredPrimaryCount = 0;
        for (let current = root.R; current !== root; current = current.R) {
            if (current.type === 'primary') {
                uncoveredPrimaryCount++;
            }
        }

        const filledCellsSet = new Set();
        const setCellCounts = {}; // 현재 partialSolution의 세트별 칸 수 계산
        let partialHasUnique = false;
        partialSolution.forEach(node => {
            let pieceNode = node;
            while (!pieceNode.pieceInfo && pieceNode.R !== node) pieceNode = pieceNode.R;
            if (pieceNode.pieceInfo) {
                const { piece, pos } = pieceNode.pieceInfo;
                if (piece.isUnique) partialHasUnique = true;
                piece.shape.forEach(([dr, dc]) => filledCellsSet.add((pos[0] + dr) * GRID_SIZE + (pos[1] + dc)));
                // 새로운 로직: setCellCounts 업데이트 (유니크 조각은 세트 보너스에 포함하지 않음)
                if (piece.set && !piece.isUnique) {
                    setCellCounts[piece.set] = (setCellCounts[piece.set] || 0) + piece.shape.length;
                }
            }
        });
        const currentCellsFilled = filledCellsSet.size;
        
        // 현재 상태의 세트 보너스 계산
        const { totalBonus } = calculateSetBonus(setCellCounts);
        const currentTotalResistance = currentScore + totalBonus;

        // 순위: ①목표 세트 달성 개수 → ②총 저항(세트 보너스 포함) → ③채운 칸 수
        const currentTargetsMet = csCountTargetsMet(setCellCounts);
        const recordable = !requireUnique || partialHasUnique;
        if (recordable && (currentTargetsMet > bestTargetsMet ||
            (currentTargetsMet === bestTargetsMet && (currentTotalResistance > bestTotalResistance ||
             (currentTotalResistance === bestTotalResistance && currentCellsFilled > bestCellsFilled))))) {
            bestScoreFound = currentScore;
            bestTotalResistance = currentTotalResistance;
            bestSolution = [...partialSolution];
            bestCellsFilled = currentCellsFilled;
            bestTargetsMet = currentTargetsMet;
        }

        // 해를 찾았을 때 저장 (완전한 해든 부분 해든)
        if (recordable && (uncoveredPrimaryCount === 0 || partialSolution.length > 0)) {
            // 세트 보너스를 포함한 총 저항으로 중복 체크 및 저장
            const isDuplicate = allSolutions.some(sol => 
                sol.cellsFilled === currentCellsFilled && 
                (sol.targetsMet || 0) === currentTargetsMet &&
                Math.abs(sol.totalResistance - currentTotalResistance) < 0.01 // 부동소수점 오차 고려
            );
            if (!isDuplicate) {
                allSolutions.push({ 
                    solution: [...partialSolution], 
                    score: currentScore, 
                    cellsFilled: currentCellsFilled,
                    targetsMet: currentTargetsMet, // 목표 세트 달성 개수
                    totalResistance: currentTotalResistance // 세트 보너스 포함 총 저항 저장
                });
                // 목표 달성 → 총 저항 → 칸 수 순으로 정렬
                allSolutions.sort((a, b) => 
                    (b.targetsMet || 0) - (a.targetsMet || 0) ||
                    b.totalResistance - a.totalResistance || 
                    b.cellsFilled - a.cellsFilled
                );
                // 더 많은 해를 탐색하도록 제한 완화
                if (allSolutions.length > MAX_SOLUTIONS * 3) {
                    allSolutions = allSolutions.slice(0, MAX_SOLUTIONS * 3);
                }
            }
        }
        
        // 완전한 해를 찾았는지 확인 (모든 primary column이 커버됨)
        if (uncoveredPrimaryCount === 0) {
            // 완전한 해를 찾았으므로 더 이상 탐색할 primary column이 없음
            // 하지만 다른 조각 조합으로 더 좋은 점수를 얻을 수 있으므로
            // 이 경로는 종료하되, 다른 경로는 계속 탐색됨
            return;
        }
        
        let c = root.R;
        while (c !== root && c.type === 'secondary') c = c.R;
        if (c === root) return;

        let minSize = Infinity;
        let chosenCol = null;
        for (let j = c; j !== root; j = j.R) {
            if (j.type === 'primary' && j.size > 0 && j.size < minSize) {
                minSize = j.size;
                chosenCol = j;
            }
        }

        if (chosenCol === null) return;
        c = chosenCol;

        const rowsToExplore = [];
        for (let r = c.D; r !== c; r = r.D) {
            let pieceNode = r;
            while (!pieceNode.pieceInfo && pieceNode.R !== r) pieceNode = pieceNode.R;
            if (pieceNode.pieceInfo) {
                rowsToExplore.push({ rowNode: r, piece: pieceNode.pieceInfo.piece });
            }
        }

        if (PRIORITIZE_HIGH_SCORE) {
            const getPriorityLevel = (set) => {
                const index = prioritySets.indexOf(set);
                return index === -1 ? 4 : index + 1;
            };
            rowsToExplore.sort((a, b) => {
                const pieceA = a.piece;
                const pieceB = b.piece;

                // 유니크가 입력된 경우, 아직 유니크를 사용하지 않았다면 같은 탐색 안에서 먼저 배치 후보로 본다.
                if (requireUnique && !partialHasUnique && pieceA.isUnique !== pieceB.isUnique) {
                    return pieceA.isUnique ? -1 : 1;
                }

                // 목표 세트인데 아직 목표 칸 수 미달인 조각을 최우선으로
                const aNeedsTarget = (!pieceA.isUnique && Number(CS_TARGET_COUNTS[pieceA.set]) > 0 && (setCellCounts[pieceA.set] || 0) < Number(CS_TARGET_COUNTS[pieceA.set])) ? 0 : 1;
                const bNeedsTarget = (!pieceB.isUnique && Number(CS_TARGET_COUNTS[pieceB.set]) > 0 && (setCellCounts[pieceB.set] || 0) < Number(CS_TARGET_COUNTS[pieceB.set])) ? 0 : 1;
                if (aNeedsTarget !== bNeedsTarget) return aNeedsTarget - bNeedsTarget;

                // 새로운 로직: 21칸을 넘긴 세트의 조각은 후순위로
                const isSetAMaxed = !pieceA.isUnique && (setCellCounts[pieceA.set] || 0) >= 21;
                const isSetBMaxed = !pieceB.isUnique && (setCellCounts[pieceB.set] || 0) >= 21;

                if (isSetAMaxed && !isSetBMaxed) return 1; // A는 21칸 넘김, B는 안 넘김 -> B 우선
                if (!isSetAMaxed && isSetBMaxed) return -1; // B는 21칸 넘김, A는 안 넘김 -> A 우선

                // 기존 우선순위 로직
                const aPriority = getPriorityLevel(pieceA.set);
                const bPriority = getPriorityLevel(pieceB.set);
                if (aPriority !== bPriority) return aPriority - bPriority;
                if (pieceB.score !== pieceA.score) return pieceB.score - pieceA.score;
                return pieceB.shape.length - pieceA.shape.length;
            });
        }

        cover(c);

        for (const { rowNode: r } of rowsToExplore) {
            let pieceNode = r;
            while (!pieceNode.pieceInfo && pieceNode.R !== r) pieceNode = pieceNode.R;
            if (pieceNode.pieceInfo) {
                const { piece, pos } = pieceNode.pieceInfo;
                let uniqueCount = 0, regularCount = 0;
                partialSolution.forEach(node => {
                    let pNode = node;
                    while (!pNode.pieceInfo && pNode.R !== node) pNode = pNode.R;
                    if (pNode.pieceInfo) {
                        pNode.pieceInfo.piece.isUnique ? uniqueCount++ : regularCount++;
                    }
                });

                if (piece.isUnique && uniqueCount >= maxUniquePieces) continue;
                if (!piece.isUnique && regularCount >= maxRegularPieces) continue;

                const newCells = piece.shape.map(([dr, dc]) => (pos[0] + dr) * GRID_SIZE + (pos[1] + dc));
                const actuallyNewCells = newCells.filter(cell => !filledCellsSet.has(cell));

                if (actuallyNewCells.length > 0) {
                    const potentialCellsFilled = currentCellsFilled + actuallyNewCells.length;
                    const potentialScore = currentScore + piece.score;
                    
                    // 새로운 조각을 추가했을 때의 세트 보너스 계산 (유니크 조각은 세트 보너스에 포함하지 않음)
                    const potentialSetCounts = { ...setCellCounts };
                    if (piece.set && !piece.isUnique) {
                        potentialSetCounts[piece.set] = (potentialSetCounts[piece.set] || 0) + piece.shape.length;
                    }
                    const { totalBonus: potentialBonus } = calculateSetBonus(potentialSetCounts);
                    const potentialTotalResistance = potentialScore + potentialBonus;
                    
                    // 세트 보너스를 포함한 총 저항을 고려한 가지치기 (더 완화)
                    // 완전한 해를 찾았어도 더 좋은 해를 찾기 위해 계속 탐색
                    const targetCellCount = gridState.filter(Boolean).length;
                    const isCompleteSolution = potentialCellsFilled >= targetCellCount;
                    
                    // 낙관적 상한 기반 가지치기:
                    // ①남은 칸으로 아직 달성 가능한 목표 세트 수 → ②저항 상한 순으로,
                    // 현재 최고 기록을 넘어설 여지가 있는 가지만 탐색한다.
                    const remainingFree = targetCellCount - potentialCellsFilled;
                    const optimisticBound = potentialTotalResistance + remainingFree * 250 + 2650;
                    let reachableTargets = 0;
                    CS_TARGET_KEYS.forEach(k => {
                        const need = Number(CS_TARGET_COUNTS[k]) - (potentialSetCounts[k] || 0);
                        if (need <= 0 || need <= remainingFree) reachableTargets++;
                    });
                    const shouldExplore = 
                        (piece.isUnique && uniqueCount === 0) ||
                        reachableTargets > bestTargetsMet ||
                        (reachableTargets === bestTargetsMet &&
                         (optimisticBound > bestTotalResistance ||
                          (optimisticBound === bestTotalResistance && potentialCellsFilled >= bestCellsFilled))) ||
                        isCompleteSolution;

                    if (shouldExplore) {
                        for (let j = r.R; j !== r; j = j.R) cover(j.C);
                        partialSolution.push(r);
                        await search(root, partialSolution, potentialScore, prioritySets);
                        partialSolution.pop();
                        for (let j = r.L; j !== r; j = j.L) uncover(j.C);
                    }
                }
            }
        }
        uncover(c);
    }

    solveBtn.addEventListener('click', solve);

    // --- Initial Calls ---
    createGrid();
    createPiecePalette();
    renderRecognizedPieceCards(csRecognizedResults);
});
