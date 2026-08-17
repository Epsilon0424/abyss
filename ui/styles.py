"""스트림릿 UI 스타일"""
import streamlit as st

CSS = r"""
<style>
/* ===== 0) 글꼴 및 변수 ===== */
@import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css");

/* 기본 라이트 팔레트 및 테마별 추가 스타일 */
html, body, :root, [data-testid="stApp"], [data-testid="stAppViewContainer"]{
  forced-color-adjust: none !important;
}

:root{
  --FONT_FAMILY: "Pretendard", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic", "Helvetica Neue",
                 Arial, sans-serif;

  --FS_APP: 14px;
  --FS_XS: 11px;
  --FS_SM: 12px;
  --FS_MD: 13px;
  --FS_LG: 16px;
  --FS_XL: 19px;

  --FW_R: 500;
  --FW_M: 600;
  --FW_B: 700;
  --FW_XB: 800;

  --PAGE_BG: #f3f4f6;

  --SHELL_BG: #f9fafb;
  --SHELL_RADIUS: 16px;
  --SHELL_SHADOW: 0 8px 24px rgba(0,0,0,0.06);

  --PANEL_BG: #f3f4f6;
  --PANEL_BG_TRANSPARENT: rgba(243,244,246,0);
  --PANEL_BORDER: #eef2f7;
  --PANEL_RADIUS: 14px;
  --PANEL_PAD: 18px;

  --CARD_BG: #ffffff;
  --CARD_RADIUS: 14px;
  --CARD_SHADOW: 0 8px 24px rgba(0,0,0,0.06);

  --SEL_H: 34px;
  --SEL_FONT: 13px;
  --MENU_FONT: 12px;
  --SELECT_ICON_SIZE: 18px;
  --SELECT_EQUIP_ICON_SIZE: 20px;
  --SELECT_ICON_OFFSET: 22px;

  --COL_GAP: 1.0rem;
  --TAB_GAP: 10px;

  --accent: #ff3434;
  --accent-soft: rgba(255,52,52,0.10);
  --TITLE_INK: #111827;
  --TEXT_MAIN: #111827;
  --TEXT_SUB: #374151;
  --TEXT_MUTED: #6b7280;

  --PROG_H: 16px;
  --PROG_BG: #e5e7eb;
  --PROG_BORDER: #d1d5db;
  --PROG_FG1: #4b5563;
  --PROG_FG2: #111827;

  --EQUIP_ROW_H: 28px;
  --EQUIP_TOGGLE_SHIFT: -2px;
  --ROW_H: 32px;
  --CELL_PX: 12px;
  --TAB_FONT: 13px;
  --TAB_WEIGHT: 750;
}

/* ===== 1) 전역 및 스트림릿 화면 ===== */
html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"]{
  font-family: var(--FONT_FAMILY) !important;
  font-size: var(--FS_APP) !important;
  background: var(--PAGE_BG) !important;
  color: var(--TEXT_MAIN) !important;
}
[data-testid="stAppViewContainer"] *,
[data-testid="stSidebar"] *{
  font-family: var(--FONT_FAMILY) !important;
}

[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] *,
label, p, span,
div[data-testid="stText"],
div[data-testid="stCaptionContainer"]{
  color: var(--TEXT_MAIN);
}

small,
.h-sub,
.h-meta,
.global-note .note-text,
.u-empty{
  color: var(--TEXT_MUTED) !important;
}

section.main > div.block-container,
[data-testid="stMainBlockContainer"],
[data-testid="stAppViewContainer"] .block-container{
  max-width: 1400px !important;
  margin-left: auto !important;
  margin-right: auto !important;
  padding-top: 2.6rem !important;
  padding-bottom: 3.2rem !important;
  padding-left: 2.2rem !important;
  padding-right: 2.2rem !important;
}

header[data-testid="stHeader"]{
  background: transparent !important;
}

/* 상단 스트림릿 메뉴 영향 제외 */
div[data-testid="stToolbar"],
div[data-testid="stToolbar"] *,
div[data-testid="stMainMenu"],
div[data-testid="stMainMenu"] *,
div[data-baseweb="popover"] [data-testid="stMainMenu"],
div[data-baseweb="popover"] [data-testid="stMainMenu"] *{
  text-indent: 0 !important;
  text-transform: none !important;
}

/* 이미지 툴바/확대 버튼 숨김 */
[data-testid="stElementToolbar"],
[data-testid="stElementToolbarButton"],
[data-testid="StyledFullScreenButton"],
button[title*="fullscreen"],
button[title*="Fullscreen"],
button[aria-label*="fullscreen"],
button[aria-label*="Fullscreen"],
button[kind="header"],
[data-testid="stBaseButton-headerNoPadding"]{
  display: none !important;
  visibility: hidden !important;
}

[data-testid="stImage"] [data-testid="stElementToolbar"],
[data-testid="stImageContainer"] [data-testid="stElementToolbar"]{
  display: none !important;
  visibility: hidden !important;
  opacity: 0 !important;
  pointer-events: none !important;
}

[data-testid="stImage"] img,
[data-testid="stImageContainer"] img{
  width: auto !important;
  height: auto !important;
  max-width: 100%;
}

/* 실행 중 흐림 효과 제거 */
[data-stale="true"],
[data-stale="true"] *,
.stale-element,
.stale-element *{
  opacity: 1 !important;
  filter: none !important;
}

/* ===== 2) 레이아웃 및 패널 ===== */
.st-key-outer_shell{
  background: var(--SHELL_BG) !important;
  border: 0 !important;
  border-radius: var(--SHELL_RADIUS) !important;
  box-shadow: var(--SHELL_SHADOW) !important;
  padding: 18px !important;
}
.st-key-outer_shell > div{
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  padding: 0 !important;
}

div[data-testid="stHorizontalBlock"]{
  gap: var(--COL_GAP) !important;
  align-items: flex-start !important;
}

div[data-testid="stVerticalBlockBorderWrapper"]{
  background: var(--CARD_BG) !important;
  border: none !important;
  border-radius: var(--CARD_RADIUS) !important;
  box-shadow: var(--CARD_SHADOW) !important;
  padding: 18px 18px 14px 18px !important;
}

.st-key-panel_select,
.st-key-panel_result{
  background: var(--PANEL_BG) !important;
  border: 1px solid var(--PANEL_BORDER) !important;
  border-radius: var(--PANEL_RADIUS) !important;
  box-shadow: none !important;
  padding: var(--PANEL_PAD) !important;
}

.st-key-panel_select > div,
.st-key-panel_result > div{
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  margin-top: 0 !important;
  padding-top: 0 !important;
}

.st-key-panel_select,
.st-key-panel_select > div,
.st-key-panel_select div[data-testid="stElementContainer"],
.st-key-panel_select div[data-testid="stMarkdownContainer"]{
  overflow: visible !important;
}

@media (max-width: 760px){
  /* 모바일 패널 좌우 여백 축소 */
  section.main > div.block-container,
  [data-testid="stMainBlockContainer"],
  [data-testid="stAppViewContainer"] .block-container{
    padding-left: 1.25rem !important;
    padding-right: 1.25rem !important;
  }

  .title-card,
  .global-note{
    padding-left: 14px !important;
    padding-right: 14px !important;
  }

  .st-key-outer_shell{
    padding: 14px !important;
  }

  .st-key-panel_select,
  .st-key-panel_result{
    padding: 12px !important;
  }

  /* 스트림릿 1.48 열 선택자 호환 */
  .st-key-outer_shell div[data-testid="stColumn"]:has(.st-key-panel_select),
  .st-key-outer_shell div[data-testid="stColumn"]:has(.st-key-panel_result),
  .st-key-outer_shell div[data-testid="column"]:has(.st-key-panel_select),
  .st-key-outer_shell div[data-testid="column"]:has(.st-key-panel_result){
    width: 100% !important;
    min-width: 0 !important;
    max-width: none !important;
    flex: 0 0 100% !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
  }

  .st-key-outer_shell div[data-testid="stHorizontalBlock"]:has(.st-key-panel_select):has(.st-key-panel_result){
    display: flex !important;
    flex-direction: column !important;
    align-items: stretch !important;
    width: 100% !important;
    min-width: 0 !important;
    max-width: none !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    gap: var(--COL_GAP) !important;
  }

  /* 모바일 웹뷰 메인 2열 폭 보정 */
  .st-key-outer_shell div[data-testid="stHorizontalBlock"]:has(.st-key-panel_select):has(.st-key-panel_result)
    > div[data-testid="stColumn"],
  .st-key-outer_shell div[data-testid="stHorizontalBlock"]:has(.st-key-panel_select):has(.st-key-panel_result)
    > div[data-testid="column"]{
    width: 100% !important;
    min-width: 0 !important;
    max-width: none !important;
    flex: 0 0 100% !important;
  }

  .st-key-panel_select,
  .st-key-panel_result{
    width: 100% !important;
    min-width: 0 !important;
    max-width: none !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
    box-sizing: border-box !important;
  }

  .st-key-outer_shell div[data-testid="stHorizontalBlock"]:has(.st-key-panel_select):has(.st-key-panel_result)
    > div[data-testid="column"]{
    width: 100% !important;
    min-width: 100% !important;
    max-width: 100% !important;
    flex: 1 1 100% !important;
  }
}

/* ===== 3) 글꼴 및 제목 ===== */
.h-title,
.select-title-clean,
.result-title-clean,
.info-details .h-title{
  margin: 0 !important;
  padding: 0 !important;
  font-family: var(--FONT_FAMILY) !important;
  font-size: var(--FS_LG) !important;
  font-weight: var(--FW_XB) !important;
  letter-spacing: -0.2px !important;
  line-height: 1.15 !important;
  color: var(--TITLE_INK) !important;
  white-space: nowrap !important;
}

.title-card .h-title{
  font-size: var(--FS_XL) !important;
  letter-spacing: -0.35px !important;
}

.title-card .h-sub,
.title-card .h-meta{
  font-size: var(--FS_SM) !important;
  line-height: 1.55 !important;
  font-weight: 600 !important;
  color: #6b7280 !important;
}

.title-card{
  background: var(--SHELL_BG) !important;
  border-radius: var(--CARD_RADIUS) !important;
  box-shadow: var(--CARD_SHADOW) !important;
  padding: 14px 18px !important;
  margin: 0 0 14px 0 !important;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.title-card .h-title,
.title-card .h-sub,
.title-card .h-meta{
  margin: 0 !important;
}

.ctl-label,
.info-details .ctl-label,
.adjustment-summary-title{
  margin: 10px 0 -10px 0;
  padding: 0 !important;
  font-family: var(--FONT_FAMILY) !important;
  font-size: var(--FS_MD) !important;
  font-weight: var(--FW_XB) !important;
  letter-spacing: 0 !important;
  line-height: 1.15 !important;
  color: #374151 !important;
  white-space: nowrap !important;
}

/* 영어 긴 라벨만 단어 단위로 자동 줄바꿈 */
.label-word-wrap,
.info-details .label-word-wrap,
.adjustment-summary-title{
  white-space: normal !important;
  word-break: normal !important;
  overflow-wrap: normal !important;
  line-height: 1.22 !important;
  max-width: 100% !important;
  min-width: 0 !important;
}

.info-details > summary:has(.label-word-wrap),
.info-details > summary:has(.adjustment-summary-title){
  width: 100% !important;
  max-width: 100% !important;
  min-width: 0 !important;
}

.info-details > summary .label-word-wrap,
.info-details > summary .adjustment-summary-title{
  flex: 1 1 auto !important;
  min-width: 0 !important;
  max-width: calc(100% - 18px) !important;
}

.info-details > summary .ctl-help{
  flex: 0 0 12px !important;
}

/* 지표 카드 */
div[data-testid="stMetricLabel"],
div[data-testid="stMetricLabel"] *{
  font-size: var(--FS_SM) !important;
  font-weight: var(--FW_B) !important;
  color: #374151 !important;
  -webkit-text-fill-color: #374151 !important;
  opacity: 1 !important;
}

div[data-testid="stMetricValue"],
div[data-testid="stMetricValue"] *{
  font-size: 20px !important;
  font-weight: var(--FW_XB) !important;
  letter-spacing: -0.2px !important;
  color: #111827 !important;
  -webkit-text-fill-color: #111827 !important;
  opacity: 1 !important;
}

/* ===== 4) 정보 아이콘 및 클릭 박스 ===== */
.ctl-help-bubble{
  display: none !important;
  visibility: hidden !important;
  opacity: 0 !important;
  pointer-events: none !important;
}

.ctl-label-stack{
  position: relative;
  display: block;
  margin: 10px 0 -10px 0;
  overflow: visible !important;
}

.ctl-label-row{
  display: flex;
  align-items: center;
  gap: 4px;
  overflow: visible !important;
}
.ctl-label-row .ctl-label{
  margin: 0 !important;
}

.ctl-help-wrap{
  position: relative;
  display: inline-flex;
  align-items: center;
  align-self: center;
  line-height: 1;
  transform: translateY(-1px);
  overflow: visible !important;
}

.info-details{
  display: block !important;
  width: 100% !important;
  max-width: 100% !important;
  box-sizing: border-box !important;
  margin: 0 !important;
  padding: 0 !important;
}

.info-details > summary{
  display: inline-flex !important;
  align-items: center !important;
  gap: 5px !important;
  width: fit-content !important;
  max-width: 100% !important;
  list-style: none !important;
  cursor: pointer !important;
  user-select: none !important;
  margin: 0 !important;
  padding: 0 !important;
}
.info-details > summary::-webkit-details-marker{
  display: none !important;
}

.info-details > summary .ctl-label,
.info-details > summary .adjustment-summary-title{
  margin: 0 !important;
}

.ctl-help,
.info-details .ctl-help{
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;

  width: 12px !important;
  height: 12px !important;
  min-width: 12px !important;
  min-height: 12px !important;
  box-sizing: border-box !important;

  border: 0 !important;
  border-radius: 9999px !important;
  background: #9ca3af !important;
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;

  font-size: 8px !important;
  font-weight: 800 !important;
  line-height: 1 !important;
  padding: 0 !important;

  cursor: pointer !important;
  user-select: none !important;
  box-shadow: none !important;
  outline: none !important;
  transform: translateY(0px) !important;
}

.ctl-help *,
.info-details .ctl-help *{
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
  font-size: 8px !important;
  font-weight: 800 !important;
  line-height: 1 !important;
  margin: 0 !important;
  padding: 0 !important;
}

.info-box,
.adjustment-box{
  display: block !important;
  width: 100% !important;
  max-width: 100% !important;
  box-sizing: border-box !important;

  background: #e5e7eb !important;
  border: none !important;
  border-radius: 12px !important;
  padding: 10px 12px !important;
  margin: 0 0 12px 0 !important;

  word-break: keep-all !important;
  overflow-wrap: break-word !important;
  white-space: normal !important;
}

.adjustment-info-details{
  margin: 10px 0 6px 0 !important;
}
.adjustment-info-details .adjustment-box{
  margin: 1px 0 8px 0 !important;
}

.info-box ul,
.adjustment-box ul{
  width: 100% !important;
  max-width: 100% !important;
  box-sizing: border-box !important;
  margin: 0 !important;
  padding-left: 16px !important;
}

.info-box li,
.adjustment-box li{
  font-family: var(--FONT_FAMILY) !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  line-height: 1.45 !important;
  color: #374151 !important;
  margin: 3px 0 !important;

  word-break: keep-all !important;
  overflow-wrap: break-word !important;
  white-space: normal !important;
}

/* 정보 라벨 → 다음 드롭다운 */
.st-key-panel_select .info-details:has(.ctl-label):not(.adjustment-info-details){
  margin: 10px 0 -10px 0 !important;
}
.st-key-panel_select .info-details:has(.ctl-label):not(.adjustment-info-details)[open]{
  margin: 10px 0 -20px 0 !important;
}

/* ===== 5) 선택 상자·메뉴·아이콘 ===== */
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div{
  min-height: var(--SEL_H) !important;
  height: var(--SEL_H) !important;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
  background: #e5e7eb !important;
  border: 0 !important;
  outline: none !important;
  box-shadow: none !important;
  display: flex !important;
  align-items: center !important;
  border-radius: 10px !important;
}

div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus,
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within,
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:hover{
  border: 0 !important;
  outline: none !important;
  box-shadow: none !important;
}

div[data-testid="stSelectbox"] div[role="combobox"]{
  min-height: var(--SEL_H) !important;
  height: var(--SEL_H) !important;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
  display: flex !important;
  align-items: center !important;
  background: transparent !important;
}

div[data-testid="stSelectbox"] div[data-baseweb="select"],
div[data-testid="stSelectbox"] div[data-baseweb="select"] *{
  font-size: var(--SEL_FONT) !important;
  line-height: 1.5 !important;
  font-weight: var(--FW_M) !important;
}

div[data-testid="stSelectbox"] div[data-baseweb="select"],
div[data-testid="stSelectbox"] div[data-baseweb="select"] *,
div[data-testid="stSelectbox"] div[role="combobox"],
div[data-testid="stSelectbox"] div[role="combobox"] *{
  color: var(--TEXT_MAIN) !important;
  -webkit-text-fill-color: var(--TEXT_MAIN) !important;
  opacity: 1 !important;
}

div[data-testid="stSelectbox"] input{
  color: var(--TEXT_MAIN) !important;
  -webkit-text-fill-color: var(--TEXT_MAIN) !important;
  caret-color: var(--TEXT_MAIN) !important;
}
div[data-testid="stSelectbox"] input::placeholder{
  color: var(--TEXT_MUTED) !important;
  -webkit-text-fill-color: var(--TEXT_MUTED) !important;
  opacity: 1 !important;
}
div[data-testid="stSelectbox"] svg{
  fill: var(--TEXT_MUTED) !important;
}

/* 메뉴 */
div[data-baseweb="popover"],
div[data-baseweb="popover"] *{
  font-family: var(--FONT_FAMILY) !important;
}

/* 라이트 모드 드롭다운 메뉴 외곽선/그림자 제거 */
div[data-baseweb="popover"],
div[data-baseweb="popover"] > div,
div[data-baseweb="popover"] [data-baseweb="menu"],
div[data-baseweb="popover"] ul,
div[data-baseweb="menu"],
[role="listbox"]{
  border: 0 !important;
  outline: none !important;
  box-shadow: none !important;
}
div[data-baseweb="popover"] > div,
div[data-baseweb="popover"] [data-baseweb="menu"],
div[data-baseweb="popover"] ul,
div[data-baseweb="popover"] li,
[role="listbox"],
[role="option"]{
  background: #ffffff !important;
  color: var(--TEXT_MAIN) !important;
  -webkit-text-fill-color: var(--TEXT_MAIN) !important;
  opacity: 1 !important;
}
div[data-baseweb="menu"],
[role="listbox"]{
  background: #ffffff !important;
  border: 0 !important;
  outline: none !important;
  border-radius: 10px !important;
  box-shadow: none !important;
  overflow: hidden !important;
}

div[data-baseweb="menu"] *,
[role="listbox"] *,
li[role="option"]{
  font-size: var(--MENU_FONT) !important;
  line-height: 1.35 !important;
  color: var(--TEXT_MAIN) !important;
  -webkit-text-fill-color: var(--TEXT_MAIN) !important;
  opacity: 1 !important;
}

li[role="option"]{
  padding-top: 8px !important;
  padding-bottom: 8px !important;
  background: #ffffff !important;
}
li[role="option"]:hover,
li[role="option"][data-highlighted="true"],
li[role="option"][aria-selected="false"]:hover,
li[role="option"][aria-selected="true"]{
  background: transparent !important;
  background-color: transparent !important;
  color: #ef4444 !important;
}
li[role="option"][aria-selected="true"]{
  font-weight: var(--FW_B) !important;
  color: var(--accent) !important;
  -webkit-text-fill-color: var(--accent) !important;
}

/* 기본·세부사항·설정 아이콘 행 */
.st-key-panel_select [class*="st-key-iconrow_"]{
  position: relative !important;
  width: 100% !important;
  min-width: 0 !important;
  margin-bottom: -6px !important;
  overflow: visible !important;
}

.st-key-panel_select [class*="st-key-iconrow_"] div[data-testid="stElementContainer"]:has(.select-icon-fixed){
  height: 0 !important;
  min-height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  overflow: visible !important;
  position: relative !important;
  z-index: 20 !important;
}

.st-key-panel_select [class*="st-key-iconrow_"] .select-icon-fixed{
  position: absolute !important;
  left: 0 !important;
  top: calc(var(--SEL_H) / 2 + 14px) !important;
  width: var(--SELECT_ICON_SIZE) !important;
  height: var(--SELECT_ICON_SIZE) !important;
  transform: translateY(-50%) !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  margin: 0 !important;
  z-index: 30 !important;
  pointer-events: none !important;
  border-radius: 0 !important;
  overflow: visible !important;
  background: transparent !important;
}

.st-key-panel_select [class*="st-key-iconrow_"] .select-icon-fixed img{
  display: block !important;
  width: 100% !important;
  height: 100% !important;
  object-fit: contain !important;
  border-radius: 0 !important;
  background: transparent !important;
  visibility: visible !important;
  opacity: 1 !important;
}

.st-key-panel_select [class*="st-key-iconrow_"] div[data-testid="stElementContainer"]:has(div[data-testid="stSelectbox"]){
  margin-left: var(--SELECT_ICON_OFFSET) !important;
  width: calc(100% - var(--SELECT_ICON_OFFSET)) !important;
  max-width: calc(100% - var(--SELECT_ICON_OFFSET)) !important;
  min-width: 0 !important;
}

.st-key-panel_select [class*="st-key-iconrow_"] div[data-testid="stSelectbox"],
.st-key-panel_select [class*="st-key-iconrow_"] div[data-baseweb="select"],
.st-key-panel_select [class*="st-key-iconrow_"] div[data-baseweb="select"] > div{
  width: 100% !important;
  max-width: 100% !important;
  min-width: 0 !important;
}

@media (max-width: 760px){
  .st-key-panel_select [class*="st-key-iconrow_"] .select-icon-fixed,
  .st-key-panel_select [class*="st-key-iconrow_"] .select-icon-fixed img{
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
  }
}

/* ===== 6) 선택·결과·탭 간격 ===== */
.st-key-panel_select > div > div[data-testid="stElementContainer"]:has(.select-title-clean){
  margin: 0 0 10px 0 !important;
  padding: 0 !important;
}

.st-key-panel_result > div > div[data-testid="stElementContainer"]:has(.result-title-clean){
  margin: 0 0 14px 0 !important;
  padding: 0 !important;
}

.st-key-panel_result .result-title-clean{
  margin-bottom: 6px !important;
}
.st-key-panel_result div[data-testid="stCaptionContainer"]{
  margin-top: 3px !important;
  padding-top: 0 !important;
}

div[data-testid="stTabs"] div[data-baseweb="tab-panel"] > div{
  margin-top: 0 !important;
  padding-top: 0 !important;
}
.st-key-panel_select div[data-testid="stTabs"]{
  margin-top: 5px !important;
}
.st-key-panel_result div[data-testid="stTabs"]{
  margin-top: -13px !important;
}
.st-key-panel_select div[data-testid="stTabs"] div[data-baseweb="tab-panel"]{
  padding-top: 1px !important;
}
.st-key-panel_result div[data-testid="stTabs"] div[data-baseweb="tab-panel"]{
  padding-top: 15px !important;
}

div[data-testid="stTabs"] button[data-baseweb="tab"],
div[data-testid="stTabs"] button[data-baseweb="tab"] *{
  font-size: var(--TAB_FONT) !important;
  font-weight: var(--TAB_WEIGHT) !important;
}
[data-testid="stCaptionContainer"]{
  font-size: var(--FS_SM) !important;
  line-height: 1.45 !important;
}

.st-key-panel_result div[data-testid="stTabs"] button[data-baseweb="tab"],
.st-key-panel_result div[data-testid="stTabs"] button[data-baseweb="tab"] *{
  padding-bottom: 1px !important;
}

.st-key-panel_select div[data-testid="stTabs"] button[data-baseweb="tab"],
.st-key-panel_select div[data-testid="stTabs"] button[data-baseweb="tab"] *{
  color: var(--TITLE_INK) !important;
  -webkit-text-fill-color: var(--TITLE_INK) !important;
  opacity: 1 !important;
  filter: none !important;
}
.st-key-panel_select div[data-testid="stTabs"] button[data-baseweb="tab"]:hover,
.st-key-panel_select div[data-testid="stTabs"] button[data-baseweb="tab"]:hover *,
.st-key-panel_result div[data-testid="stTabs"] button[data-baseweb="tab"]:hover,
.st-key-panel_result div[data-testid="stTabs"] button[data-baseweb="tab"]:hover *,
.st-key-panel_select div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"],
.st-key-panel_select div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] *,
.st-key-panel_result div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"],
.st-key-panel_result div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] *{
  color: var(--accent) !important;
  -webkit-text-fill-color: var(--accent) !important;
  opacity: 1 !important;
}

div[data-testid="stTabs"] button[data-baseweb="tab"][disabled],
div[data-testid="stTabs"] button[data-baseweb="tab"][aria-disabled="true"],
div[data-testid="stTabs"] button[data-baseweb="tab"][disabled] *,
div[data-testid="stTabs"] button[data-baseweb="tab"][aria-disabled="true"] *,
div[data-testid="stTabs"][aria-busy="true"],
div[data-testid="stTabs"][aria-busy="true"] *,
div[data-baseweb="tab-panel"][aria-busy="true"],
div[data-baseweb="tab-panel"][aria-busy="true"] *{
  opacity: 1 !important;
  filter: none !important;
}

.st-key-panel_select div[data-testid="stMarkdownContainer"] hr.u-divider,
.st-key-panel_result div[data-testid="stMarkdownContainer"] hr.u-divider{
  border: none !important;
  border-top: 1px solid #e5e7eb !important;
  margin-top: 1px !important;
  margin-bottom: 8px !important;
}

/* 선택 패널 하단 5픽셀 간격 */
.st-key-panel_select div[data-testid="stElementContainer"]:has(div[data-testid="stMarkdownContainer"] hr.u-divider){
  margin-top: -5px !important;
}
.st-key-panel_select div[data-testid="stMarkdownContainer"] hr.u-divider{
  margin-top: 10px !important;
}

/* ===== 7) 파티·세부사항 탭 간격 ===== */
/* 기본 탭 파티 드롭다운 4픽셀 간격 */
.st-key-panel_select [class*="st-key-party_group"],
.st-key-panel_select .st-key-party_dealer_group{
  margin: 0 !important;
  padding: 0 !important;
}

.st-key-panel_select [class*="st-key-party_group"] div[data-testid="stVerticalBlock"],
.st-key-panel_select .st-key-party_dealer_group div[data-testid="stVerticalBlock"]{
  gap: 0 !important;
}

/* 파티 선택칸 4픽셀 간격 */
.st-key-panel_select [class*="st-key-iconrow_party_slot"]{
  margin-top: 0 !important;
  margin-bottom: -10px !important;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
}

/* 딜러 메인 파티 행 간격 보정 */
.st-key-panel_select [class*="st-key-iconrow_party_slot2__melan"],
.st-key-panel_select [class*="st-key-iconrow_party_slot2__bb"],
.st-key-panel_select [class*="st-key-iconrow_party_slot2__shining"],
.st-key-panel_select [class*="st-key-iconrow_party_slot2__phoenix"],
.st-key-panel_select [class*="st-key-iconrow_party_slot2__blue"],
.st-key-panel_select [class*="st-key-iconrow_party_slot2__stardust"],
.st-key-panel_select [class*="st-key-iconrow_party_slot2__jackfruit"]{
  margin-top: -14px !important;
}

/* 추가 딜러 아이콘 세로 위치 보정 */
.st-key-panel_select .st-key-party_dealer_group [class*="st-key-iconrow_party_slot3"] .select-icon-fixed,
.st-key-panel_select .st-key-party_dealer_group [class*="st-key-iconrow_party_slot4"] .select-icon-fixed{
  top: calc(var(--SEL_H) / 2) !important;
}

/* 기본 탭 세로 간격 고정 */
.st-key-panel_select div[data-testid="stTabs"] div[data-baseweb="tab-panel"]:first-of-type div[data-testid="stVerticalBlock"]{
  gap: 0 !important;
}
.st-key-panel_select div[data-testid="stTabs"] div[data-baseweb="tab-panel"]:first-of-type div[data-testid="stMarkdownContainer"]:has(.ctl-label){
  margin-bottom: 0 !important;
}

/* 세부사항 탭 */
.st-key-detail_tab_body div[data-testid="stVerticalBlock"]{
  gap: 0 !important;
}

.st-key-detail_tab_body div[data-testid="stMarkdownContainer"]:has(.ctl-label){
  margin-bottom: 0 !important;
}

/* 장비 → 시즈나이트 */
.st-key-detail_tab_body div[data-testid="stElementContainer"]:has([class*="party_equip"]){
  margin-bottom: -5px !important;
  padding-bottom: 0px !important;
}
.st-key-detail_tab_body [class*="party_equip"]{
  margin-bottom: -5px !important;
  padding-bottom: 0px !important;
}

/* 시즈나이트 → 유니크 */
.st-key-detail_tab_body div[data-testid="stElementContainer"]:has([class*="party_seaz"]){
  margin-bottom: -5px !important;
  padding-bottom: 0px !important;
}
.st-key-detail_tab_body [class*="party_seaz"]{
  margin-bottom: -5px !important;
  padding-bottom: 0px !important;
}

/* 유니크 → 다음 쿠키/계산 보정 */
.st-key-detail_tab_body div[data-testid="stElementContainer"]:has([class*="party_unique"]){
  margin-bottom: -5px !important;
  padding-bottom: 0px !important;
}

/* 세부사항 탭 아이콘 위치 */
.st-key-detail_tab_body [class*="st-key-iconrow_party_equip_slot"] .select-icon-fixed,
.st-key-detail_tab_body [class*="st-key-iconrow_party_seaz_slot"] .select-icon-fixed,
.st-key-detail_tab_body [class*="st-key-iconrow_party_unique_slot"] .select-icon-fixed,
.st-key-detail_tab_body [class*="iconrow_party_equip"] .select-icon-fixed,
.st-key-detail_tab_body [class*="iconrow_party_seaz"] .select-icon-fixed,
.st-key-detail_tab_body [class*="iconrow_party_unique"] .select-icon-fixed{
  top: calc(var(--SEL_H) / 2) !important;
  left: 0 !important;
  transform: translateY(-50%) !important;
}

/* 세부사항 탭 장비 아이콘만 살짝 확대 */
.st-key-detail_tab_body [class*="iconrow_party_equip"] .select-icon-fixed{
  width: var(--SELECT_EQUIP_ICON_SIZE) !important;
  height: var(--SELECT_EQUIP_ICON_SIZE) !important;
  left: -1px !important;
  top: calc(var(--SEL_H) / 2) !important;
}
.st-key-detail_tab_body [class*="iconrow_party_equip"] .select-icon-fixed img{
  width: 100% !important;
  height: 100% !important;
  object-fit: contain !important;
  border-radius: 0 !important;
  background: transparent !important;
}

/* 아이콘 원형 크롭 제거: 이미지 원본 비율 그대로 표시 */
.select-icon-fixed,
.select-icon-fixed img,
.st-key-panel_select [class*="st-key-iconrow_"] .select-icon-fixed,
.st-key-panel_select [class*="st-key-iconrow_"] .select-icon-fixed img,
.st-key-detail_tab_body [class*="iconrow_party_equip"] .select-icon-fixed,
.st-key-detail_tab_body [class*="iconrow_party_equip"] .select-icon-fixed img,
.st-key-detail_tab_body [class*="iconrow_party_seaz"] .select-icon-fixed,
.st-key-detail_tab_body [class*="iconrow_party_seaz"] .select-icon-fixed img,
.st-key-detail_tab_body [class*="iconrow_party_unique"] .select-icon-fixed,
.st-key-detail_tab_body [class*="iconrow_party_unique"] .select-icon-fixed img{
  border-radius: 0 !important;
  overflow: visible !important;
  object-fit: contain !important;
  background: transparent !important;
}

/* 잠재력 자동·수동 드롭다운 간격 */
.st-key-detail_tab_body [class*="st-key-iconrow_potential_manual__"] .select-icon-fixed{
  top: calc(var(--SEL_H) / 2) !important;
  left: 0 !important;
  transform: translateY(-50%) !important;
}

/* 잠재력 설정: 세부사항 탭 최상단의 자동/수동 선택 */
[class*="st-key-potential_mode_block_"]{
  padding-top: 10px !important;
  padding-bottom: 0px !important;
}
[class*="st-key-potential_mode_block_"] div[data-testid="stVerticalBlock"]{
  gap: 0 !important;
}
[class*="st-key-potential_mode_block_"] div[data-testid="stMarkdownContainer"]:has(.ctl-label){
  margin: 0 !important;
  padding: 0 !important;
}
[class*="st-key-potential_mode_block_"] .ctl-label{
  margin: 0 0 4px 0 !important;
}
/* 잠재력 제목 공간별 단어 단위 줄바꿈 */
[class*="st-key-potential_mode_block_"] .potential-title{
  display: block !important;
  width: 100% !important;
  min-width: 0 !important;
  max-width: 100% !important;
  white-space: normal !important;
  word-break: keep-all !important;
  overflow-wrap: normal !important;
  overflow: visible !important;
  text-overflow: clip !important;
  line-height: 1.22 !important;
  color: #374151 !important;
  -webkit-text-fill-color: #374151 !important;
}
[class*="st-key-potential_mode_block_"] div[data-testid="stSelectbox"]{
  margin-top: 0 !important;
  margin-bottom: 0 !important;
}

/* 수동 잠재력 요약 상자·드롭다운 묶음 간격 */
[class*="st-key-potential_summary_open_dialog__"]{
  margin-top: 9px !important;
  margin-bottom: 4px !important;
}
[class*="st-key-potential_summary_open_dialog__"] button{
  box-sizing: border-box !important;
  width: 100% !important;
  min-height: 28px !important;
  height: 28px !important;
  padding: 0 10px !important;
  border-radius: 9px !important;
  background: #e5e7eb !important;
  color: var(--TEXT_SUB) !important;
  border: 0 !important;
  box-shadow: none !important;
  justify-content: flex-start !important;
  text-align: left !important;
  font-family: var(--FONT_FAMILY) !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  line-height: 1.45 !important;
}
[class*="st-key-potential_summary_open_dialog__"] button p{
  width: 100% !important;
  margin: 0 !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
  text-align: left !important;
}
[class*="st-key-potential_summary_open_dialog__"] button:hover,
[class*="st-key-potential_summary_open_dialog__"] button:focus,
[class*="st-key-potential_summary_open_dialog__"] button:active{
  background: #dfe2e6 !important;
  color: var(--TEXT_MAIN) !important;
  border: 0 !important;
  box-shadow: none !important;
}

/* 잠재력 수동 설정 모달: 제목 숨김·폭 축소·모바일 2열 */
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]){
  width: 430px !important;
  max-width: calc(100vw - 20px) !important;
  min-width: 0 !important;
  padding: 0 !important;
}

/* 잠재력 다이얼로그 빈 제목 공간 제거 */
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) h2,
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) [data-testid="stDialogHeader"] h2{
  display: none !important;
}
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) [data-testid="stDialogHeader"]{
  position: absolute !important;
  top: 6px !important;
  right: 6px !important;
  z-index: 20 !important;
  width: auto !important;
  min-height: 0 !important;
  height: auto !important;
  padding: 0 !important;
  margin: 0 !important;
  background: transparent !important;
}

/* 다이얼로그 본문 상단 정렬·내부 여백 축소 */
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) [data-testid="stDialogBody"],
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) > div:last-child{
  padding: 10px 12px 10px 12px !important;
  margin: 0 !important;
}

/* 잠재력 수동 설정 모달: 2열 배치 + 작은 스테퍼 */
[class*="st-key-potential_dialog_body_"] div[data-testid="stVerticalBlock"]{
  gap: 5px !important;
}
[class*="st-key-potential_dialog_body_"] div[data-testid="stHorizontalBlock"]{
  display: flex !important;
  flex-direction: row !important;
  flex-wrap: nowrap !important;
  column-gap: 5px !important;
  row-gap: 0 !important;
  width: 100% !important;
}
[class*="st-key-potential_dialog_body_"] div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]{
  flex: 1 1 0 !important;
  width: calc(50% - 4px) !important;
  min-width: 0 !important;
  max-width: calc(50% - 4px) !important;
}
[class*="st-key-potential_dialog_body_"] div[data-testid="stNumberInput"]{
  margin: 0 !important;
}
[class*="st-key-potential_dialog_body_"] div[data-testid="stNumberInput"] label{
  margin-bottom: 2px !important;
}
[class*="st-key-potential_dialog_body_"] div[data-testid="stNumberInput"] label p{
  font-size: var(--FS_SM) !important;
  font-weight: var(--FW_B) !important;
  color: var(--TEXT_SUB) !important;
}
[class*="st-key-potential_dialog_body_"] div[data-testid="stNumberInput"] input{
  min-height: 29px !important;
  height: 29px !important;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
  text-align: center !important;
  font-size: var(--FS_MD) !important;
  font-weight: var(--FW_B) !important;
  background: var(--PANEL_BG) !important;
}
[class*="st-key-potential_dialog_body_"] div[data-testid="stNumberInput"] button{
  min-height: 29px !important;
  height: 29px !important;
  width: 29px !important;
  background: var(--PANEL_BG) !important;
}
/* 숫자 입력칸 호버·포커스 외형 고정 */
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) div[data-testid="stNumberInput"] div[data-baseweb="input"],
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) div[data-testid="stNumberInput"] div[data-baseweb="base-input"],
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) div[data-testid="stNumberInput"] div[data-baseweb="input"]:hover,
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) div[data-testid="stNumberInput"] div[data-baseweb="base-input"]:hover,
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) div[data-testid="stNumberInput"] div[data-baseweb="input"]:focus,
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) div[data-testid="stNumberInput"] div[data-baseweb="base-input"]:focus,
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) div[data-testid="stNumberInput"] div[data-baseweb="input"]:focus-within,
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) div[data-testid="stNumberInput"] div[data-baseweb="base-input"]:focus-within{
  border: 0 !important;
  border-color: transparent !important;
  outline: 0 !important;
  box-shadow: none !important;
  background: var(--PANEL_BG) !important;
}
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) div[data-testid="stNumberInput"] input,
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) div[data-testid="stNumberInput"] input:hover,
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) div[data-testid="stNumberInput"] input:focus,
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) div[data-testid="stNumberInput"] input:focus-visible,
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) div[data-testid="stNumberInput"] button:hover,
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) div[data-testid="stNumberInput"] button:focus,
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) div[data-testid="stNumberInput"] button:active{
  border: 0 !important;
  border-color: transparent !important;
  outline: 0 !important;
  box-shadow: none !important;
}
[class*="st-key-potential_dialog_body_"] .potential-slot-status{
  margin: 3px 0 0 0 !important;
  padding: 4px 8px !important;
  min-height: 25px !important;
  border-radius: 8px !important;
  background: var(--PANEL_BG) !important;
  font-size: var(--FS_SM) !important;
  font-weight: var(--FW_M) !important;
  line-height: 1.2 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  text-align: center !important;
  color: var(--TEXT_SUB) !important;
}
[class*="st-key-potential_dialog_body_"] .potential-slot-ok b{
  color: #16a34a !important;
}
[class*="st-key-potential_dialog_body_"] .potential-slot-bad b{
  color: var(--accent) !important;
}
/* 완료 버튼은 실행 버튼과 동일한 타이포/높이를 쓰되 상태 박스와는 조금 더 띄운다. */
[class*="st-key-potential_dialog_done__"]{
  margin-top: 8px !important;
}
[class*="st-key-potential_dialog_done__"] button,
[class*="st-key-potential_dialog_done__"] button *{
  height: 40px !important;
  font-size: var(--FS_APP) !important;
  font-weight: 700 !important;
}

/* ===== 잠재력 편집창 최종 압축 보정 ===== */
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) {
  padding-top: 0 !important;
  padding-bottom: 0 !important;
  overflow: hidden !important;
}

/* 잠재력 다이얼로그 본문 상단 공간 회수 */
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) [class*="st-key-potential_dialog_body_"] {
  margin-top: -44px !important;
  margin-bottom: 0 !important;
  padding: 8px 12px 10px 12px !important;
}

/* 안내 문구 상단 기본 여백 제거 */
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) [data-testid="stCaptionContainer"] {
  margin: 0 0 4px 0 !important;
  padding: 0 !important;
}
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) [data-testid="stCaptionContainer"] p {
  margin: 0 !important;
  line-height: 1.25 !important;
}

/* 숫자 입력 스테퍼 단일 회색 박스 */
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) div[data-testid="stNumberInput"] div[data-baseweb="input"],
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) div[data-testid="stNumberInput"] div[data-baseweb="base-input"] {
  height: 27px !important;
  min-height: 27px !important;
  background: var(--PANEL_BG) !important;
  border: 0 !important;
  outline: 0 !important;
  box-shadow: none !important;
  border-radius: 7px !important;
  overflow: hidden !important;
}
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) div[data-testid="stNumberInput"] div[data-baseweb="input"] *,
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) div[data-testid="stNumberInput"] div[data-baseweb="base-input"] * {
  border: 0 !important;
  border-color: transparent !important;
  outline: 0 !important;
  box-shadow: none !important;
}
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) div[data-testid="stNumberInput"] input,
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) div[data-testid="stNumberInput"] button,
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) div[data-testid="stNumberInput"] input:hover,
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) div[data-testid="stNumberInput"] input:focus,
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) div[data-testid="stNumberInput"] input:focus-visible,
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) div[data-testid="stNumberInput"] button:hover,
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) div[data-testid="stNumberInput"] button:focus,
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) div[data-testid="stNumberInput"] button:active {
  height: 27px !important;
  min-height: 27px !important;
  background: transparent !important;
  border: 0 !important;
  outline: 0 !important;
  box-shadow: none !important;
}
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) div[data-testid="stNumberInput"] button {
  width: 27px !important;
  min-width: 27px !important;
  padding: 0 !important;
}

/* 사용 칸 상태바는 한 단계 더 낮게 */
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) .potential-slot-status {
  min-height: 22px !important;
  height: 22px !important;
  padding: 1px 6px !important;
  margin-top: 5px !important;
  line-height: 1 !important;
}

/* 완료 버튼: 상태바와 간격을 확보하고 실행 버튼과 동일하게 정확히 중앙 정렬 */
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) [class*="st-key-potential_dialog_done__"] {
  margin-top: 10px !important;
}
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) [class*="st-key-potential_dialog_done__"] button {
  height: 40px !important;
  min-height: 40px !important;
  padding: 0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  text-align: center !important;
  line-height: 1 !important;
  font-size: var(--FS_APP) !important;
  font-weight: 700 !important;
}
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) [class*="st-key-potential_dialog_done__"] button > div,
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) [class*="st-key-potential_dialog_done__"] button p,
div[role="dialog"]:has([class*="st-key-potential_dialog_body_"]) [class*="st-key-potential_dialog_done__"] button span {
  margin: 0 !important;
  padding: 0 !important;
  line-height: 1 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

/* ===== 8) 버튼 및 진행률 ===== */
.stButton > button[kind="primary"]{
  border-radius: 12px;
  height: 40px;
  font-weight: var(--FW_XB);
  background: #ff4b4b !important;
  border: none !important;
  color: #ffffff !important;
  box-shadow: none !important;
}
.stButton > button[kind="primary"] *,
.stButton > button[kind="primary"]:hover *{
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
  opacity: 1 !important;
  background: transparent !important;
  box-shadow: none !important;
}
.stButton > button[kind="primary"]:hover{
  background: #ff3434 !important;
}
.stButton > button:not([kind="primary"]){
  border-radius: 12px;
  height: 40px;
  font-weight: var(--FW_B);
  background: #ffffff !important;
  border: 1px solid #e5e7eb !important;
  color: #111827 !important;
}
.stButton > button:not([kind="primary"]):hover{
  border-color: #d1d5db !important;
  background: #f9fafb !important;
}
.st-key-run_btn button,
.st-key-run_btn button *,
[class*="st-key-potential_dialog_done__"] button,
[class*="st-key-potential_dialog_done__"] button *{
  font-size: var(--FS_APP) !important;
  font-weight: 700 !important;
}

.prog-area{
  padding: 0 !important;
  margin: -5px 0 5px 0 !important;
}
.prog-row{
  display: flex;
  align-items: center;
  width: 100%;
}
.prog-wrap{
  width: 100%;
  height: 18px;
  border-radius: 5px;
  background: #f1f5f9;
  border: 1px solid #e5e7eb;
  overflow: hidden;
  position: relative;
  box-shadow: 0 4px 10px rgba(0,0,0,0.06);
}
.prog-bar{
  height: 100%;
  width: 0%;
  border-radius: 3px;
  background: #46515d;
  transition: width 120ms ease;
  position: relative;
  overflow: hidden;
}
.prog-shimmer{
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: calc(100% * var(--shine-scale, 1));
  overflow: hidden;
  pointer-events: none;
}
.prog-shimmer::after{
  content: "";
  position: absolute;
  top: 0;
  bottom: 0;
  left: -28%;
  width: 28%;
  background: linear-gradient(
    120deg,
    rgba(255,255,255,0) 0%,
    rgba(255,255,255,0.32) 45%,
    rgba(255,255,255,0) 90%
  );
  transform: skewX(-20deg);
  animation: prog_shimmer_full 1.15s linear infinite;
  opacity: 0.9;
}
@keyframes prog_shimmer_full{
  0%   { left: -28%; }
  100% { left: 100%; }
}
.prog-text{
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 800;
  color: #ffffff;
  letter-spacing: 0.2px;
  text-shadow: 0 1px 2px rgba(0,0,0,0.25);
  user-select: none;
}

/* ===== 9) 표·스탯 카드·그리드 ===== */
.stat-wrap{
  margin: 0 0 14px 0;
}
.stat-pill{
  display: block;
  width: 100%;
  box-sizing: border-box;
  background: #fcfcfc;
  border-radius: 12px;
  padding: 10px 12px;
  font-size: var(--FS_SM);
  font-weight: 800 !important;
  line-height: 1.2;
  color: #374151;
  box-shadow: 0 4px 10px rgba(0,0,0,0.03);
  margin: 0 0 8px 0;
}
.u-table{
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  table-layout: fixed;
  background: #fcfcfc;
  border: 0.5px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
}
.u-table thead th,
.u-table tbody td{
  height: var(--ROW_H);
  padding: 0 var(--CELL_PX);
  line-height: var(--ROW_H);
  vertical-align: middle;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: var(--FS_SM);
  color: #374151;
  max-width: 0;
}
.u-table thead th{
  background: #f9fafb;
  color: #374151;
  font-weight: 800 !important;
  border-bottom: 2px solid rgba(255,52,52,0.18) !important;
}
.u-table tbody td{
  font-weight: 400 !important;
  border-bottom: 1px solid #eef2f7;
}
.u-table thead th:not(:last-child),
.u-table tbody td:not(:last-child){
  border-right: 1px solid #eef2f7 !important;
}
.u-table tbody td:first-child{
  font-weight: var(--FW_B) !important;
  color: #374151;
  min-width: 0 !important;
}
.u-table tbody tr:last-child td{
  border-bottom: none;
}
.u-empty{
  font-size: var(--FS_SM);
  color: #6b7280;
  padding: 10px 2px 0 2px;
}

.summary-grid,
.stat-grid{
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.65rem;
  align-items: start;
  margin-top: 0 !important;
}
.stat-grid .stat-wrap{
  margin: 0 !important;
}

@media (max-width: 980px){
  .summary-grid,
  .stat-grid{
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .summary-grid .md-span-2,
  .stat-grid .span-2{
    grid-column: 1 / -1;
  }
}
@media (max-width: 640px){
  .summary-grid,
  .stat-grid{
    grid-template-columns: 1fr;
  }
  .summary-grid .md-span-2,
  .stat-grid .span-2{
    grid-column: auto;
  }
}

/* ===== 10) 하단 안내 ===== */
.global-note{
  background: var(--SHELL_BG) !important;
  border-radius: var(--CARD_RADIUS) !important;
  box-shadow: var(--CARD_SHADOW) !important;
  padding: 14px 18px !important;
  margin: 0 !important;
}
.global-note .note-title{
  font-size: var(--FS_MD);
  font-weight: var(--FW_XB);
  color: #111827;
  margin: 0 0 6px 0;
}
.global-note .note-text{
  font-size: var(--FS_SM);
  font-weight: 400;
  color: #6b7280;
  line-height: 1.55;
  margin: 0;
}
.global-note .note-text b{
  font-weight: var(--FW_B);
  color: #374151;
}
.global-note .note-text code{
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono","Courier New", monospace;
  font-size: calc(var(--FS_SM) - 1px);
  background: #f9fafb;
  border: 1px solid #eef2f7;
  padding: 1px 6px;
  border-radius: 8px;
}

/* ===== 11) 장비 제목 ===== */
.st-key-panel_select [class*="st-key-equip_hdr_"] div[data-testid="stHorizontalBlock"],
.st-key-panel_select [class*="st-key-equip_hdr_"] div[data-testid="column"]{
  align-items: center !important;
}
.equip-label{
  height: var(--EQUIP_ROW_H);
  display: flex;
  align-items: center;
  white-space: nowrap;
  margin: 0;
  padding: 0 !important;
  line-height: 1;
  font-size: var(--FS_MD) !important;
  font-weight: var(--FW_XB) !important;
  color: #374151;
}
.equip-toggle-wrap{
  height: var(--EQUIP_ROW_H);
  display: flex;
  align-items: center;
  justify-content: flex-start;
  margin: 0;
  padding: 0;
}
.equip-toggle-wrap div[data-testid="stToggle"],
.equip-toggle-wrap label{
  margin: 0 !important;
  padding: 0 !important;
}
.equip-toggle-wrap div[data-testid="stToggle"]{
  display: flex;
  align-items: center;
  transform: translateY(var(--EQUIP_TOGGLE_SHIFT));
}
.st-key-panel_select [class*="st-key-equip_hdr_"] div[data-testid="stHorizontalBlock"]{
  gap: 0 !important;
}
.st-key-panel_select [class*="st-key-equip_hdr_"]{
  margin-bottom: 0 !important;
  padding-bottom: 0 !important;
}
.st-key-panel_select [class*="st-key-equip_hdr_"] + div[data-testid="stElementContainer"]{
  margin-top: -4px !important;
}

/* ===== 12) 기본·세부사항·설정 아이콘 크기 ===== */
/* 장비 값이 '자동'이 아닐 때는 기본 탭과 세부사항 탭 모두 같은 크기로 살짝 확대 */
.st-key-panel_select [class*="st-key-iconrow_equip"] .equip-non-auto-icon{
  width: var(--SELECT_EQUIP_ICON_SIZE) !important;
  height: var(--SELECT_EQUIP_ICON_SIZE) !important;
  left: -1px !important;
}

/* 설정 탭 아이콘 중앙 정렬 */
.st-key-panel_select [class*="st-key-iconrow_"] .setting-select-icon{
  top: calc(var(--SEL_H) / 2) !important;
}

/* ===== 13) 설정 탭 간격 ===== */
/* 설정 탭 공통 선택 상자 구조 */
.st-key-setting_tab_body div[data-testid="stVerticalBlock"]{
  gap: 0 !important;
}

.st-key-setting_tab_body div[data-testid="stMarkdownContainer"]:has(.ctl-label){
  margin-bottom: 0 !important;
}

.st-key-setting_tab_body .ctl-label{
  margin: 10px 0 -10px 0 !important;
  padding: 0 !important;
  line-height: 1.15 !important;
}

/* 잠재력 수동 요약 박스 최종 보정 */
.st-key-detail_tab_body [class*="st-key-potential_summary_open_dialog__"] .stButton > button:not([kind="primary"]),
.st-key-detail_tab_body [class*="st-key-potential_summary_open_dialog__"] button:not([kind="primary"]){
  box-sizing: border-box !important;
  width: 100% !important;
  min-height: 28px !important;
  height: 28px !important;
  padding: 0 10px !important;
  border-radius: 10px !important;
  background: #e5e7eb !important;
  border: 0 !important;
  box-shadow: none !important;
  color: #374151 !important;
  justify-content: flex-start !important;
  text-align: left !important;
  font-family: var(--FONT_FAMILY) !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  line-height: 1.45 !important;
}
.st-key-detail_tab_body [class*="st-key-potential_summary_open_dialog__"] .stButton > button:not([kind="primary"]) *,
.st-key-detail_tab_body [class*="st-key-potential_summary_open_dialog__"] button:not([kind="primary"]) *{
  margin: 0 !important;
  background: transparent !important;
  color: #374151 !important;
  -webkit-text-fill-color: #374151 !important;
  box-shadow: none !important;
  font-family: var(--FONT_FAMILY) !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  line-height: 1.45 !important;
}
.st-key-detail_tab_body [class*="st-key-potential_summary_open_dialog__"] .stButton > button:not([kind="primary"]):hover,
.st-key-detail_tab_body [class*="st-key-potential_summary_open_dialog__"] button:not([kind="primary"]):hover{
  background: #dfe2e6 !important;
  border: 0 !important;
  color: #111827 !important;
}

"""

DARK_THEME_CSS = r"""
<style>
:root{
  --PAGE_BG: #0f1012;
  --SHELL_BG: #1a1c20;
  --PANEL_BG: #24262a;
  --PANEL_BG_TRANSPARENT: rgba(36,38,42,0);
  --PANEL_BORDER: transparent;
  --CARD_BG: #1b1d21;
  --SHELL_SHADOW: none;
  --CARD_SHADOW: none;

  --TITLE_INK: #f7f7f8;
  --TEXT_MAIN: #f1f3f5;
  --TEXT_SUB: #c7cbd1;
  --TEXT_MUTED: #9ca3af;

  --PROG_BG: #2c2f35;
  --PROG_BORDER: transparent;
  --PROG_FG1: #525866;
  --PROG_FG2: #d1d5db;
}

html, body, :root, [data-testid="stApp"], [data-testid="stAppViewContainer"]{
  color-scheme: dark !important;
  background: var(--PAGE_BG) !important;
  color: var(--TEXT_MAIN) !important;
}

[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
section.main{
  background: var(--PAGE_BG) !important;
}

.title-card{
  background: #1b1d21 !important;
  border: 0 !important;
  box-shadow: none !important;
}
.title-card .h-title{ color: #f7f7f8 !important; -webkit-text-fill-color: #f7f7f8 !important; }
.title-card .h-sub,
.title-card .h-meta{ color: #b7bcc6 !important; -webkit-text-fill-color: #b7bcc6 !important; }

.st-key-outer_shell{
  background: #1a1c20 !important;
  border: 0 !important;
  box-shadow: none !important;
}
.st-key-panel_select,
.st-key-panel_result{
  background: #24262a !important;
  border: 0 !important;
  box-shadow: none !important;
}

/* 다크모드에서는 큰 사각형 사이 색상 차이만 남기고 테두리는 제거 */
div[data-testid="stVerticalBlockBorderWrapper"]{
  background: #1b1d21 !important;
  border: 0 !important;
  box-shadow: none !important;
}

.h-title,
.select-title-clean,
.result-title-clean,
.info-details .h-title,
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] *,
label, p, span,
div[data-testid="stText"],
div[data-testid="stCaptionContainer"]{
  color: var(--TEXT_MAIN) !important;
  -webkit-text-fill-color: var(--TEXT_MAIN) !important;
}

small,
.h-sub,
.h-meta,
.global-note .note-text,
.u-empty,
.st-key-panel_result div[data-testid="stCaptionContainer"]{
  color: var(--TEXT_MUTED) !important;
  -webkit-text-fill-color: var(--TEXT_MUTED) !important;
}

.ctl-label,
.info-details .ctl-label,
.adjustment-summary-title{
  color: #d6d9df !important;
  -webkit-text-fill-color: #d6d9df !important;
}

/* 탭 */
.st-key-panel_select div[data-testid="stTabs"] button[data-baseweb="tab"],
.st-key-panel_select div[data-testid="stTabs"] button[data-baseweb="tab"] *,
.st-key-panel_result div[data-testid="stTabs"] button[data-baseweb="tab"],
.st-key-panel_result div[data-testid="stTabs"] button[data-baseweb="tab"] *{
  color: #e5e7eb !important;
  -webkit-text-fill-color: #e5e7eb !important;
}
.st-key-panel_select div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"],
.st-key-panel_select div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] *,
.st-key-panel_result div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"],
.st-key-panel_result div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] *{
  color: var(--accent) !important;
  -webkit-text-fill-color: var(--accent) !important;
}

/* 셀렉트 박스 */
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div{
  background: #303236 !important;
  border: 0 !important;
  box-shadow: none !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"],
div[data-testid="stSelectbox"] div[data-baseweb="select"] *,
div[data-testid="stSelectbox"] div[role="combobox"],
div[data-testid="stSelectbox"] div[role="combobox"] *{
  color: #f1f3f5 !important;
  -webkit-text-fill-color: #f1f3f5 !important;
}
/* 드롭다운 메뉴 */
div[data-baseweb="popover"] > div,
div[data-baseweb="popover"] [data-baseweb="menu"],
div[data-baseweb="popover"] ul,
div[data-baseweb="popover"] li,
[role="listbox"],
[role="option"],
div[data-baseweb="menu"]{
  background: #2a2c31 !important;
  color: #f1f3f5 !important;
  -webkit-text-fill-color: #f1f3f5 !important;
  border: 0 !important;
  box-shadow: 0 12px 28px rgba(0,0,0,0.34) !important;
}
li[role="option"]:hover,
li[role="option"][data-highlighted="true"],
li[role="option"][aria-selected="true"]{
  background: #34373d !important;
  color: var(--accent) !important;
  -webkit-text-fill-color: var(--accent) !important;
}

/* 버튼/박스 */
.stButton > button:not([kind="primary"]){
  background: #2a2c31 !important;
  border: 0 !important;
  color: #f1f3f5 !important;
}
.stButton > button:not([kind="primary"]):hover{
  background: #303236 !important;
}
/* 다크모드에서도 잠재력 요약 박스만 밝은 회색으로 남지 않도록 동일한 높은 우선순위로 보정 */
.st-key-detail_tab_body [class*="st-key-potential_summary_open_dialog__"] .stButton > button:not([kind="primary"]),
.st-key-detail_tab_body [class*="st-key-potential_summary_open_dialog__"] button:not([kind="primary"]){
  background: #303236 !important;
  border: 0 !important;
  color: #f1f3f5 !important;
}
.st-key-detail_tab_body [class*="st-key-potential_summary_open_dialog__"] .stButton > button:not([kind="primary"]) *,
.st-key-detail_tab_body [class*="st-key-potential_summary_open_dialog__"] button:not([kind="primary"]) *{
  color: #f1f3f5 !important;
  -webkit-text-fill-color: #f1f3f5 !important;
}
.st-key-detail_tab_body [class*="st-key-potential_summary_open_dialog__"] .stButton > button:not([kind="primary"]):hover,
.st-key-detail_tab_body [class*="st-key-potential_summary_open_dialog__"] button:not([kind="primary"]):hover{
  background: #34373d !important;
}
.adjustment-box,
.info-box,
.prog-wrap,
div[data-testid="stMetricValue"]{
  background: #2a2c31 !important;
  border-color: transparent !important;
  color: #f1f3f5 !important;
}
/* 다크모드 안내 박스 배경 통일 */
.global-note{
  background: var(--SHELL_BG) !important;
  border: 0 !important;
  box-shadow: none !important;
  color: var(--TEXT_MAIN) !important;
}
.global-note .note-title{
  color: var(--TITLE_INK) !important;
}
.global-note .note-text{
  color: var(--TEXT_SUB) !important;
}
.global-note .note-text b{
  color: var(--TEXT_MAIN) !important;
}

/* 다크모드 결과 숫자·탭·표 보정 */
div[data-testid="stMetric"],
div[data-testid="stMetric"] > div,
div[data-testid="stMetricValue"],
div[data-testid="stMetricValue"] > div{
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
}
div[data-testid="stMetricLabel"],
div[data-testid="stMetricLabel"] *,
div[data-testid="stMetricValue"],
div[data-testid="stMetricValue"] *,
div[data-testid="stMetricDelta"],
div[data-testid="stMetricDelta"] *{
  color: #f1f3f5 !important;
  -webkit-text-fill-color: #f1f3f5 !important;
}
div[data-testid="stMetricLabel"],
div[data-testid="stMetricLabel"] *{
  color: #d9dde5 !important;
  -webkit-text-fill-color: #d9dde5 !important;
}
.st-key-panel_result div[data-testid="stTabs"] div[data-baseweb="tab-panel"],
.st-key-panel_result div[data-testid="stTabs"] div[data-baseweb="tab-panel"] > div{
  background: transparent !important;
  color: #f1f3f5 !important;
}
.u-card{
  background: #2a2c31 !important;
  border: 0 !important;
  box-shadow: none !important;
  color: #f1f3f5 !important;
}
.u-card-title{
  background: #303236 !important;
  border: 0 !important;
  color: #f1f3f5 !important;
  -webkit-text-fill-color: #f1f3f5 !important;
}
.stat-pill{
  background: #303236 !important;
  border: 0 !important;
  box-shadow: none !important;
  color: #f1f3f5 !important;
  -webkit-text-fill-color: #f1f3f5 !important;
}
.stat-wrap{
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
}
.summary-grid > div,
.stat-grid > div{
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
}
.u-table{
  background: #2a2c31 !important;
  border: 0 !important;
  box-shadow: none !important;
}
.u-table thead th{
  background: #303236 !important;
  color: #d9dde5 !important;
  -webkit-text-fill-color: #d9dde5 !important;
  border-bottom: 1px solid rgba(255,75,75,0.34) !important;
}
.u-table tbody td{
  background: #2a2c31 !important;
  color: #f1f3f5 !important;
  -webkit-text-fill-color: #f1f3f5 !important;
  border-bottom: 1px solid #34373d !important;
}
.u-table tbody td:first-child{
  color: #d9dde5 !important;
  -webkit-text-fill-color: #d9dde5 !important;
}
.u-table thead th:not(:last-child),
.u-table tbody td:not(:last-child){
  border-right: 1px solid #34373d !important;
}
.u-empty,
.global-note .note-text,
.global-note .note-text b,
.global-note .note-text code{
  color: #b7bcc6 !important;
  -webkit-text-fill-color: #b7bcc6 !important;
}
.global-note .note-text code{
  background: #303236 !important;
  border: 0 !important;
}

hr.u-divider,
.st-key-panel_select div[data-testid="stMarkdownContainer"] hr.u-divider,
.st-key-panel_result div[data-testid="stMarkdownContainer"] hr.u-divider{
  border-color: #373a40 !important;
}
</style>
"""

FORCE_LIGHT_CSS = r"""
<style>
html, body, :root, [data-testid="stApp"], [data-testid="stAppViewContainer"]{
  color-scheme: light !important;
  background: #f3f4f6 !important;
  color: #111827 !important;
}
input, textarea, select, button,
div[data-baseweb="select"],
div[data-baseweb="select"] *,
div[data-baseweb="popover"],
div[data-baseweb="popover"] *{
  color-scheme: light !important;
}
</style>
"""

def _system_theme_css_from_dark(css: str) -> str:
    # 기기 설정용 다크 스타일 통합
    body = css.replace("<style>", "").replace("</style>", "")
    return f"<style>\n@media (prefers-color-scheme: dark){{\n{body}\n}}\n</style>"

SYSTEM_THEME_CSS = _system_theme_css_from_dark(DARK_THEME_CSS)

def inject_styles() -> None:
    st.markdown(CSS, unsafe_allow_html=True)

    # 테마 변경 시 탭 상태 유지
    # - 선택 상자 재실행 전후 요소 구조 유지
    # - 모든 테마의 스타일 슬롯 구조 고정
    theme_mode = st.session_state.get("ui_theme", st.session_state.get("ui_theme_widget", "system"))
    if theme_mode == "dark":
        st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)
    elif theme_mode == "light":
        st.markdown(FORCE_LIGHT_CSS, unsafe_allow_html=True)
    else:
        st.markdown(SYSTEM_THEME_CSS, unsafe_allow_html=True)

# =====================================================
# 드롭다운 호버 배경 및 선택 행 정렬
# =====================================================
CSS += r"""
<style>
/* 닫힌 선택 상자 호버·포커스 배경 고정 */
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:hover,
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus,
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within{
  background: #e5e7eb !important;
  border: 0 !important;
  outline: none !important;
  box-shadow: none !important;
}

/* 펼친 드롭다운 호버·선택 배경 제거 */
div[data-baseweb="popover"] [role="option"],
div[data-baseweb="popover"] [role="option"] *,
div[data-baseweb="popover"] li[role="option"],
div[data-baseweb="popover"] li[role="option"] *{
  background-color: transparent !important;
  box-shadow: none !important;
}
div[data-baseweb="popover"] [role="option"]:hover,
div[data-baseweb="popover"] [role="option"][data-highlighted="true"],
div[data-baseweb="popover"] [role="option"][aria-selected="true"],
div[data-baseweb="popover"] [role="option"]:hover *,
div[data-baseweb="popover"] [role="option"][data-highlighted="true"] *,
div[data-baseweb="popover"] [role="option"][aria-selected="true"] *{
  background-color: transparent !important;
  box-shadow: none !important;
}
div[data-baseweb="popover"] [role="option"][aria-selected="true"],
div[data-baseweb="popover"] [role="option"][aria-selected="true"] *{
  color: var(--accent) !important;
  -webkit-text-fill-color: var(--accent) !important;
  font-weight: var(--FW_B) !important;
}

</style>
"""

DARK_THEME_CSS += r"""
<style>
/* 다크모드 닫힌 선택 상자 배경 고정 */
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:hover,
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus,
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within{
  background: #303236 !important;
  border: 0 !important;
  outline: none !important;
  box-shadow: none !important;
}

/* 다크모드 펼친 드롭다운 배경 제거 */
div[data-baseweb="popover"] [role="option"],
div[data-baseweb="popover"] [role="option"] *,
div[data-baseweb="popover"] li[role="option"],
div[data-baseweb="popover"] li[role="option"] *{
  background-color: transparent !important;
  box-shadow: none !important;
}
div[data-baseweb="popover"] [role="option"]:hover,
div[data-baseweb="popover"] [role="option"][data-highlighted="true"],
div[data-baseweb="popover"] [role="option"][aria-selected="true"],
div[data-baseweb="popover"] [role="option"]:hover *,
div[data-baseweb="popover"] [role="option"][data-highlighted="true"] *,
div[data-baseweb="popover"] [role="option"][aria-selected="true"] *{
  background-color: transparent !important;
  box-shadow: none !important;
}
div[data-baseweb="popover"] [role="option"][aria-selected="true"],
div[data-baseweb="popover"] [role="option"][aria-selected="true"] *{
  color: var(--accent) !important;
  -webkit-text-fill-color: var(--accent) !important;
  font-weight: var(--FW_B) !important;
}
</style>
"""

# =====================================================
# 펼친 드롭다운 다크모드 색상
# - 펼친 드롭다운 메뉴 배경을 닫힌 드롭다운(#303236)과 동일하게 맞춤
# - 흰색 테두리·포커스 링 제거
# =====================================================
DARK_THEME_CSS += r"""
<style>
/* 다크모드 펼친 드롭다운 배경 통일 */
div[data-baseweb="popover"],
div[data-baseweb="popover"] > div,
div[data-baseweb="popover"] > div > div,
div[data-baseweb="popover"] [data-baseweb="menu"],
div[data-baseweb="popover"] ul,
div[data-baseweb="popover"] ul[role="listbox"],
div[data-baseweb="popover"] [role="listbox"],
div[data-baseweb="popover"] li,
div[data-baseweb="popover"] li[role="option"],
div[data-baseweb="popover"] [role="option"],
div[data-baseweb="menu"]{
  background: #303236 !important;
  background-color: #303236 !important;
  border: 0 !important;
  outline: none !important;
  color: #f1f3f5 !important;
  -webkit-text-fill-color: #f1f3f5 !important;
}

/* 메뉴 바깥은 테두리 없이 그림자만 약하게 */
div[data-baseweb="popover"],
div[data-baseweb="popover"] > div{
  box-shadow: 0 14px 30px rgba(0,0,0,0.42) !important;
}

/* 메뉴 내부는 닫힌 드롭다운과 같은 색상 유지 */
div[data-baseweb="popover"] > div > div,
div[data-baseweb="popover"] [data-baseweb="menu"],
div[data-baseweb="popover"] ul,
div[data-baseweb="popover"] li,
div[data-baseweb="popover"] [role="option"]{
  box-shadow: none !important;
}

/* 호버·선택 글자색만 강조 */
div[data-baseweb="popover"] [role="option"]:hover,
div[data-baseweb="popover"] [role="option"][data-highlighted="true"],
div[data-baseweb="popover"] [role="option"][aria-selected="true"],
div[data-baseweb="popover"] li[role="option"]:hover,
div[data-baseweb="popover"] li[role="option"][data-highlighted="true"],
div[data-baseweb="popover"] li[role="option"][aria-selected="true"]{
  background: #303236 !important;
  background-color: #303236 !important;
  box-shadow: none !important;
}

div[data-baseweb="popover"] [role="option"][aria-selected="true"],
div[data-baseweb="popover"] [role="option"][aria-selected="true"] *,
div[data-baseweb="popover"] li[role="option"][aria-selected="true"],
div[data-baseweb="popover"] li[role="option"][aria-selected="true"] *{
  color: var(--accent) !important;
  -webkit-text-fill-color: var(--accent) !important;
  font-weight: var(--FW_B) !important;
}

/* 포커스 흰색 링 제거 */
div[data-baseweb="popover"] *:focus,
div[data-baseweb="popover"] *:focus-visible,
div[data-baseweb="select"] *:focus,
div[data-baseweb="select"] *:focus-visible{
  border: 0 !important;
  outline: none !important;
  box-shadow: none !important;
}

</style>
"""

# =====================================================
# 탭 넘침 화살표 배경 보정
# - 탭 스크롤 화살표 생성 시
# 사각형 배경 대신 투명 → 패널 배경 그라데이션으로 자연스럽게 보정
# =====================================================
_TAB_OVERFLOW_ARROW_FIX_CSS = r"""
<style>
/* 다크모드 탭 목록 페이드 제거 */
div[data-testid="stTabs"] div[data-baseweb="tab-list"],
div[data-testid="stTabs"] div[role="tablist"]{
  background: transparent !important;
  background-color: transparent !important;
}

/* 오른쪽 화살표 영역: 탭 쪽은 투명, 오른쪽으로 갈수록 패널 배경색 */
div[data-testid="stTabs"] div[data-baseweb="tab-list"] > button:not([data-baseweb="tab"]),
div[data-testid="stTabs"] div[role="tablist"] > button:not([role="tab"]),
div[data-testid="stTabs"] button[aria-label*="Scroll"],
div[data-testid="stTabs"] button[aria-label*="scroll"],
div[data-testid="stTabs"] button[aria-label*="Next"],
div[data-testid="stTabs"] button[aria-label*="next"],
div[data-testid="stTabs"] button[aria-label*="Right"],
div[data-testid="stTabs"] button[aria-label*="right"],
div[data-testid="stTabs"] button[aria-label*="다음"],
div[data-testid="stTabs"] button[aria-label*="오른쪽"]{
  background: linear-gradient(to right, var(--PANEL_BG_TRANSPARENT) 0%, var(--PANEL_BG) 58%, var(--PANEL_BG) 100%) !important;
  background-color: transparent !important;
  border: 0 !important;
  outline: none !important;
  box-shadow: none !important;
  color: var(--TEXT_MAIN) !important;
}

/* 왼쪽 화살표 영역: 반대 방향 그라데이션 */
div[data-testid="stTabs"] button[aria-label*="Previous"],
div[data-testid="stTabs"] button[aria-label*="previous"],
div[data-testid="stTabs"] button[aria-label*="Left"],
div[data-testid="stTabs"] button[aria-label*="left"],
div[data-testid="stTabs"] button[aria-label*="이전"],
div[data-testid="stTabs"] button[aria-label*="왼쪽"]{
  background: linear-gradient(to left, var(--PANEL_BG_TRANSPARENT) 0%, var(--PANEL_BG) 58%, var(--PANEL_BG) 100%) !important;
  background-color: transparent !important;
  border: 0 !important;
  outline: none !important;
  box-shadow: none !important;
  color: var(--TEXT_MAIN) !important;
}

/* 오른쪽 화살표 래퍼도 같은 그라데이션으로 맞춤 */
div[data-testid="stTabs"] div:has(> button[aria-label*="Scroll"]),
div[data-testid="stTabs"] div:has(> button[aria-label*="scroll"]),
div[data-testid="stTabs"] div:has(> button[aria-label*="Next"]),
div[data-testid="stTabs"] div:has(> button[aria-label*="next"]),
div[data-testid="stTabs"] div:has(> button[aria-label*="Right"]),
div[data-testid="stTabs"] div:has(> button[aria-label*="right"]),
div[data-testid="stTabs"] div:has(> button[aria-label*="다음"]),
div[data-testid="stTabs"] div:has(> button[aria-label*="오른쪽"]){
  background: linear-gradient(to right, var(--PANEL_BG_TRANSPARENT) 0%, var(--PANEL_BG) 58%, var(--PANEL_BG) 100%) !important;
  background-color: transparent !important;
  border: 0 !important;
  outline: none !important;
  box-shadow: none !important;
}

/* 왼쪽 화살표 래퍼도 반대 방향으로 맞춤 */
div[data-testid="stTabs"] div:has(> button[aria-label*="Previous"]),
div[data-testid="stTabs"] div:has(> button[aria-label*="previous"]),
div[data-testid="stTabs"] div:has(> button[aria-label*="Left"]),
div[data-testid="stTabs"] div:has(> button[aria-label*="left"]),
div[data-testid="stTabs"] div:has(> button[aria-label*="이전"]),
div[data-testid="stTabs"] div:has(> button[aria-label*="왼쪽"]){
  background: linear-gradient(to left, var(--PANEL_BG_TRANSPARENT) 0%, var(--PANEL_BG) 58%, var(--PANEL_BG) 100%) !important;
  background-color: transparent !important;
  border: 0 !important;
  outline: none !important;
  box-shadow: none !important;
}

/* 호버·포커스 그라데이션 유지 */
div[data-testid="stTabs"] div[data-baseweb="tab-list"] > button:not([data-baseweb="tab"]):hover,
div[data-testid="stTabs"] div[data-baseweb="tab-list"] > button:not([data-baseweb="tab"]):focus,
div[data-testid="stTabs"] div[data-baseweb="tab-list"] > button:not([data-baseweb="tab"]):focus-visible,
div[data-testid="stTabs"] button[aria-label*="Scroll"]:hover,
div[data-testid="stTabs"] button[aria-label*="scroll"]:hover,
div[data-testid="stTabs"] button[aria-label*="Next"]:hover,
div[data-testid="stTabs"] button[aria-label*="next"]:hover,
div[data-testid="stTabs"] button[aria-label*="Right"]:hover,
div[data-testid="stTabs"] button[aria-label*="right"]:hover,
div[data-testid="stTabs"] button[aria-label*="다음"]:hover,
div[data-testid="stTabs"] button[aria-label*="오른쪽"]:hover{
  background: linear-gradient(to right, var(--PANEL_BG_TRANSPARENT) 0%, var(--PANEL_BG) 58%, var(--PANEL_BG) 100%) !important;
  background-color: transparent !important;
  border: 0 !important;
  outline: none !important;
  box-shadow: none !important;
}

div[data-testid="stTabs"] button[aria-label*="Previous"]:hover,
div[data-testid="stTabs"] button[aria-label*="previous"]:hover,
div[data-testid="stTabs"] button[aria-label*="Left"]:hover,
div[data-testid="stTabs"] button[aria-label*="left"]:hover,
div[data-testid="stTabs"] button[aria-label*="이전"]:hover,
div[data-testid="stTabs"] button[aria-label*="왼쪽"]:hover{
  background: linear-gradient(to left, var(--PANEL_BG_TRANSPARENT) 0%, var(--PANEL_BG) 58%, var(--PANEL_BG) 100%) !important;
  background-color: transparent !important;
  border: 0 !important;
  outline: none !important;
  box-shadow: none !important;
}

div[data-testid="stTabs"] button[aria-label*="Scroll"] svg,
div[data-testid="stTabs"] button[aria-label*="scroll"] svg,
div[data-testid="stTabs"] button[aria-label*="Next"] svg,
div[data-testid="stTabs"] button[aria-label*="next"] svg,
div[data-testid="stTabs"] button[aria-label*="Right"] svg,
div[data-testid="stTabs"] button[aria-label*="right"] svg,
div[data-testid="stTabs"] button[aria-label*="Previous"] svg,
div[data-testid="stTabs"] button[aria-label*="previous"] svg,
div[data-testid="stTabs"] button[aria-label*="Left"] svg,
div[data-testid="stTabs"] button[aria-label*="left"] svg,
div[data-testid="stTabs"] button[aria-label*="다음"] svg,
div[data-testid="stTabs"] button[aria-label*="오른쪽"] svg,
div[data-testid="stTabs"] button[aria-label*="이전"] svg,
div[data-testid="stTabs"] button[aria-label*="왼쪽"] svg{
  color: var(--TEXT_MAIN) !important;
  fill: currentColor !important;
}
</style>
"""

CSS += _TAB_OVERFLOW_ARROW_FIX_CSS
DARK_THEME_CSS += _TAB_OVERFLOW_ARROW_FIX_CSS

# 다크모드 탭 스크롤 페이드 제거
DARK_THEME_CSS += r"""
<style>
div[data-testid="stTabs"] [aria-label="Scroll tabs left"],
div[data-testid="stTabs"] [aria-label="Scroll tabs right"],
div[data-testid="stTabs"] [aria-label*="Scroll tabs"],
[data-testid="stApp"] [aria-label*="Scroll tabs"],
div[data-testid="stTabs"] div[data-baseweb="tab-list"] > button:not([data-baseweb="tab"]):not([role="tab"]),
div[data-testid="stTabs"] div[data-baseweb="tab-list"] ~ button:not([data-baseweb="tab"]):not([role="tab"]){
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  border: 0 !important;
  outline: none !important;
  box-shadow: none !important;
  color: var(--TEXT_MAIN) !important;
}
div[data-testid="stTabs"] [aria-label*="Scroll tabs"] svg,
div[data-testid="stTabs"] [aria-label*="Scroll tabs"] svg *{
  fill: var(--TEXT_MAIN) !important;
  color: var(--TEXT_MAIN) !important;
}
/* 다크모드 탭 목록 페이드 제거 */
div[data-testid="stTabs"] div[data-baseweb="tab-list"]::before,
div[data-testid="stTabs"] div[role="tablist"]::before{
  background: transparent !important;
  background-image: none !important;
}
</style>
"""

DARK_THEME_CSS += r"""
<style>
/* 다크모드 페이지 스크롤 흰색 트랙 제거 */
html,
body,
[data-testid="stApp"],
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
section.main{
  scrollbar-color: #9ca3af #303236 !important;
}
html::-webkit-scrollbar,
body::-webkit-scrollbar,
[data-testid="stApp"]::-webkit-scrollbar,
[data-testid="stAppViewContainer"]::-webkit-scrollbar,
[data-testid="stMain"]::-webkit-scrollbar,
[data-testid="stMainBlockContainer"]::-webkit-scrollbar,
section.main::-webkit-scrollbar{
  width: 4px !important;
  height: 4px !important;
}
html::-webkit-scrollbar-track,
body::-webkit-scrollbar-track,
[data-testid="stApp"]::-webkit-scrollbar-track,
[data-testid="stAppViewContainer"]::-webkit-scrollbar-track,
[data-testid="stMain"]::-webkit-scrollbar-track,
[data-testid="stMainBlockContainer"]::-webkit-scrollbar-track,
section.main::-webkit-scrollbar-track,
html::-webkit-scrollbar-corner,
body::-webkit-scrollbar-corner,
[data-testid="stApp"]::-webkit-scrollbar-corner,
[data-testid="stAppViewContainer"]::-webkit-scrollbar-corner,
[data-testid="stMain"]::-webkit-scrollbar-corner,
[data-testid="stMainBlockContainer"]::-webkit-scrollbar-corner,
section.main::-webkit-scrollbar-corner{
  background: #303236 !important;
}
html::-webkit-scrollbar-thumb,
body::-webkit-scrollbar-thumb,
[data-testid="stApp"]::-webkit-scrollbar-thumb,
[data-testid="stAppViewContainer"]::-webkit-scrollbar-thumb,
[data-testid="stMain"]::-webkit-scrollbar-thumb,
[data-testid="stMainBlockContainer"]::-webkit-scrollbar-thumb,
section.main::-webkit-scrollbar-thumb{
  background: #9ca3af !important;
  border-radius: 999px !important;
  border: 0 !important;
}
html::-webkit-scrollbar-thumb:hover,
body::-webkit-scrollbar-thumb:hover,
[data-testid="stApp"]::-webkit-scrollbar-thumb:hover,
[data-testid="stAppViewContainer"]::-webkit-scrollbar-thumb:hover,
[data-testid="stMain"]::-webkit-scrollbar-thumb:hover,
[data-testid="stMainBlockContainer"]::-webkit-scrollbar-thumb:hover,
section.main::-webkit-scrollbar-thumb:hover{
  background: #b6bcc6 !important;
}
</style>
"""

# 다크 테마 드롭다운·포커스 보정 통합
# 기기 설정 모드 스타일 재생성
SYSTEM_THEME_CSS = _system_theme_css_from_dark(DARK_THEME_CSS)

# 전체 테마 탭 넘침 흰색 잔상 제거
_TAB_OVERFLOW_ARROW_CLEANUP_CSS = r"""
<style>
div[data-testid="stTabs"] [aria-label="Scroll tabs left"],
div[data-testid="stTabs"] [aria-label="Scroll tabs right"],
div[data-testid="stTabs"] [aria-label*="Scroll tabs"],
[data-testid="stApp"] [aria-label*="Scroll tabs"],
div[data-testid="stTabs"] div[data-baseweb="tab-list"] > button:not([data-baseweb="tab"]):not([role="tab"]),
div[data-testid="stTabs"] div[data-baseweb="tab-list"] ~ button:not([data-baseweb="tab"]):not([role="tab"]),
div[data-testid="stTabs"] div:has(> button[aria-label*="Scroll"]),
div[data-testid="stTabs"] div:has(> button[aria-label*="scroll"]),
div[data-testid="stTabs"] div:has(> button[aria-label*="Next"]),
div[data-testid="stTabs"] div:has(> button[aria-label*="next"]),
div[data-testid="stTabs"] div:has(> button[aria-label*="Right"]),
div[data-testid="stTabs"] div:has(> button[aria-label*="right"]),
div[data-testid="stTabs"] div:has(> button[aria-label*="다음"]),
div[data-testid="stTabs"] div:has(> button[aria-label*="오른쪽"]),
div[data-testid="stTabs"] div:has(> button[aria-label*="Previous"]),
div[data-testid="stTabs"] div:has(> button[aria-label*="previous"]),
div[data-testid="stTabs"] div:has(> button[aria-label*="Left"]),
div[data-testid="stTabs"] div:has(> button[aria-label*="left"]),
div[data-testid="stTabs"] div:has(> button[aria-label*="이전"]),
div[data-testid="stTabs"] div:has(> button[aria-label*="왼쪽"]),
div[data-testid="stTabs"] div[data-baseweb="tab-list"]::before,
div[data-testid="stTabs"] div[role="tablist"]::before,
div[data-testid="stTabs"] div[data-baseweb="tab-list"]::after,
div[data-testid="stTabs"] div[role="tablist"]::after{
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  border: 0 !important;
  outline: none !important;
  box-shadow: none !important;
}
</style>
"""

CSS += _TAB_OVERFLOW_ARROW_CLEANUP_CSS
DARK_THEME_CSS += _TAB_OVERFLOW_ARROW_CLEANUP_CSS

# 라이트·다크 스크롤바 최종 색상
CSS += r"""
<style>
/* 전체 스크롤 막대 손잡이 색상 최종 보정 */
html:not(#cs-main-scroll-a):not(#cs-main-scroll-b),
body:not(#cs-main-scroll-a):not(#cs-main-scroll-b),
body *:not(#cs-main-scroll-a):not(#cs-main-scroll-b){
  scrollbar-color: #999ca4 transparent !important;
}
html:not(#cs-main-scroll-a):not(#cs-main-scroll-b)::-webkit-scrollbar-thumb,
body:not(#cs-main-scroll-a):not(#cs-main-scroll-b)::-webkit-scrollbar-thumb,
body *:not(#cs-main-scroll-a):not(#cs-main-scroll-b)::-webkit-scrollbar-thumb,
html:not(#cs-main-scroll-a):not(#cs-main-scroll-b)::-webkit-scrollbar-thumb:hover,
body:not(#cs-main-scroll-a):not(#cs-main-scroll-b)::-webkit-scrollbar-thumb:hover,
body *:not(#cs-main-scroll-a):not(#cs-main-scroll-b)::-webkit-scrollbar-thumb:hover{
  background: #999ca4 !important;
}
</style>
"""
DARK_THEME_CSS += r"""
<style>
/* 전체 스크롤 막대 손잡이 색상 최종 보정 */
html:not(#cs-main-scroll-a):not(#cs-main-scroll-b),
body:not(#cs-main-scroll-a):not(#cs-main-scroll-b),
body *:not(#cs-main-scroll-a):not(#cs-main-scroll-b){
  scrollbar-color: #9ca3af transparent !important;
}
html:not(#cs-main-scroll-a):not(#cs-main-scroll-b)::-webkit-scrollbar-thumb,
body:not(#cs-main-scroll-a):not(#cs-main-scroll-b)::-webkit-scrollbar-thumb,
body *:not(#cs-main-scroll-a):not(#cs-main-scroll-b)::-webkit-scrollbar-thumb,
html:not(#cs-main-scroll-a):not(#cs-main-scroll-b)::-webkit-scrollbar-thumb:hover,
body:not(#cs-main-scroll-a):not(#cs-main-scroll-b)::-webkit-scrollbar-thumb:hover,
body *:not(#cs-main-scroll-a):not(#cs-main-scroll-b)::-webkit-scrollbar-thumb:hover{
  background: #9ca3af !important;
}
</style>
"""
SYSTEM_THEME_CSS = _system_theme_css_from_dark(DARK_THEME_CSS)

# 탭 넘침 그라데이션 패널 색상
_TAB_CONTAINER_THEME_FADE_CSS = r"""
<style>
div[data-testid="stTabs"]::after{
  background-image: linear-gradient(
    to right,
    var(--PANEL_BG_TRANSPARENT) 0%,
    var(--PANEL_BG) 100%
  ) !important;
  background-color: transparent !important;
  border: 0 !important;
  outline: none !important;
  box-shadow: none !important;
}
</style>
"""

CSS += _TAB_CONTAINER_THEME_FADE_CSS
DARK_THEME_CSS += _TAB_CONTAINER_THEME_FADE_CSS
SYSTEM_THEME_CSS = _system_theme_css_from_dark(DARK_THEME_CSS)

# 모바일 스크롤바 너비 통일
# 중첩 스크롤 영역 4픽셀 통일
_MOBILE_SCROLLBAR_GEOMETRY_CSS = r"""
<style>
/* 드롭다운 포털 세로 스크롤 4픽셀 */
html,
body,
[data-testid="stApp"],
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
section.main,
div[data-baseweb="popover"],
div[data-baseweb="popover"] *,
div[data-baseweb="menu"],
div[data-baseweb="menu"] *,
[role="listbox"],
[role="listbox"] *{
  scrollbar-width: thin !important;
  scrollbar-color: #999ca4 transparent !important;
}

html::-webkit-scrollbar,
body::-webkit-scrollbar,
[data-testid="stApp"]::-webkit-scrollbar,
[data-testid="stAppViewContainer"]::-webkit-scrollbar,
[data-testid="stMain"]::-webkit-scrollbar,
[data-testid="stMainBlockContainer"]::-webkit-scrollbar,
section.main::-webkit-scrollbar,
div[data-baseweb="popover"]::-webkit-scrollbar,
div[data-baseweb="popover"] *::-webkit-scrollbar,
div[data-baseweb="menu"]::-webkit-scrollbar,
div[data-baseweb="menu"] *::-webkit-scrollbar,
[role="listbox"]::-webkit-scrollbar,
[role="listbox"] *::-webkit-scrollbar{
  width: 4px !important;
  height: 0 !important;
}

html::-webkit-scrollbar-track,
body::-webkit-scrollbar-track,
[data-testid="stApp"]::-webkit-scrollbar-track,
[data-testid="stAppViewContainer"]::-webkit-scrollbar-track,
[data-testid="stMain"]::-webkit-scrollbar-track,
[data-testid="stMainBlockContainer"]::-webkit-scrollbar-track,
section.main::-webkit-scrollbar-track,
div[data-baseweb="popover"]::-webkit-scrollbar-track,
div[data-baseweb="popover"] *::-webkit-scrollbar-track,
div[data-baseweb="menu"]::-webkit-scrollbar-track,
div[data-baseweb="menu"] *::-webkit-scrollbar-track,
[role="listbox"]::-webkit-scrollbar-track,
[role="listbox"] *::-webkit-scrollbar-track,
html::-webkit-scrollbar-corner,
body::-webkit-scrollbar-corner,
div[data-baseweb="popover"]::-webkit-scrollbar-corner,
div[data-baseweb="popover"] *::-webkit-scrollbar-corner,
div[data-baseweb="menu"]::-webkit-scrollbar-corner,
div[data-baseweb="menu"] *::-webkit-scrollbar-corner,
[role="listbox"]::-webkit-scrollbar-corner,
[role="listbox"] *::-webkit-scrollbar-corner{
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
}

html::-webkit-scrollbar-thumb,
body::-webkit-scrollbar-thumb,
[data-testid="stApp"]::-webkit-scrollbar-thumb,
[data-testid="stAppViewContainer"]::-webkit-scrollbar-thumb,
[data-testid="stMain"]::-webkit-scrollbar-thumb,
[data-testid="stMainBlockContainer"]::-webkit-scrollbar-thumb,
section.main::-webkit-scrollbar-thumb,
div[data-baseweb="popover"]::-webkit-scrollbar-thumb,
div[data-baseweb="popover"] *::-webkit-scrollbar-thumb,
div[data-baseweb="menu"]::-webkit-scrollbar-thumb,
div[data-baseweb="menu"] *::-webkit-scrollbar-thumb,
[role="listbox"]::-webkit-scrollbar-thumb,
[role="listbox"] *::-webkit-scrollbar-thumb{
  background: #999ca4 !important;
  border: 0 !important;
  border-radius: 999px !important;
  box-shadow: none !important;
  background-clip: padding-box !important;
}

/* 베이스웹 드롭다운 가로 스크롤 제거 */
div[data-baseweb="popover"] [role="listbox"],
div[data-baseweb="menu"] [role="listbox"],
body > div [role="listbox"]{
  overflow-x: hidden !important;
  scrollbar-gutter: auto !important;
  overscroll-behavior: contain !important;
}
</style>
"""

# 잠재력 수동 설정은 팝업이 아니라 세부사항 탭 안에서 바로 편집
# 좁은 패널에서도 잠재력 항목은 항상 한 줄에 2개씩 유지
_POTENTIAL_CUSTOM_STEPPER_CSS = r"""
<style>
/* ===== 세부사항 탭: 수동 잠재력 인라인 편집 ===== */
.st-key-detail_tab_body [class*="st-key-potential_inline_body_"]{
  width: 100% !important;
  margin: 10px 0 2px 0 !important;
  padding: 0 !important;
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
}
.st-key-detail_tab_body [class*="st-key-potential_inline_body_"] > div,
.st-key-detail_tab_body [class*="st-key-potential_inline_body_"] > div > div[data-testid="stVerticalBlock"]{
  width: 100% !important;
  min-width: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  gap: 0 !important;
}

/* 잠재력 행별 컨테이너 간격 */
.st-key-detail_tab_body [class*="st-key-potential_row_first__"],
.st-key-detail_tab_body [class*="st-key-potential_row__"]{
  width: 100% !important;
  min-width: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
}
.st-key-detail_tab_body [class*="st-key-potential_row__"]{
  margin-top: 0 !important;
}

/* 잠재력 행 간격 고정 스페이서 */
.st-key-detail_tab_body .potential-row-spacer{
  display: block !important;
  width: 100% !important;
  height: 5px !important;
  min-height: 5px !important;
  margin: 0 !important;
  padding: 0 !important;
  line-height: 0 !important;
}
.st-key-detail_tab_body div[data-testid="stMarkdownContainer"]:has(.potential-row-spacer){
  height: 5px !important;
  min-height: 5px !important;
  margin: 0 !important;
  padding: 0 !important;
}
.st-key-detail_tab_body [class*="st-key-potential_row_first__"] > div,
.st-key-detail_tab_body [class*="st-key-potential_row__"] > div,
.st-key-detail_tab_body [class*="st-key-potential_row_first__"] div[data-testid="stVerticalBlock"],
.st-key-detail_tab_body [class*="st-key-potential_row__"] div[data-testid="stVerticalBlock"]{
  width: 100% !important;
  min-width: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  gap: 0 !important;
}
/* 잠재력 항상 2열·좌우 5픽셀 간격 */
.st-key-detail_tab_body [class*="st-key-potential_row_first__"] div[data-testid="stHorizontalBlock"],
.st-key-detail_tab_body [class*="st-key-potential_row__"] div[data-testid="stHorizontalBlock"]{
  display: grid !important;
  grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  gap: 5px !important;
  width: 100% !important;
  min-width: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  align-items: start !important;
}
.st-key-detail_tab_body [class*="st-key-potential_row_first__"] div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"],
.st-key-detail_tab_body [class*="st-key-potential_row__"] div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]{
  width: 100% !important;
  min-width: 0 !important;
  max-width: none !important;
  margin: 0 !important;
  padding: 0 !important;
}

/* 각 스탯 항목 */
.st-key-detail_tab_body [class*="st-key-potential_statitem__"]{
  width: 100% !important;
  min-width: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  border: 0 !important;
  outline: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
}
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] > div,
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] div[data-testid="stVerticalBlock"]{
  width: 100% !important;
  min-width: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  gap: 2px !important;
  background: transparent !important;
}
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] .potential-stepper-label{
  display: block !important;
  width: 100% !important;
  max-width: 100% !important;
  min-width: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  font-size: 11px !important;
  font-weight: 700 !important;
  line-height: 1.05 !important;
  color: var(--TEXT_SUB) !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] div[data-testid="stMarkdownContainer"]:has(.potential-stepper-label){
  margin: 0 !important;
  padding: 0 !important;
}

/* 잠재력 스탯 아이콘 입력칸 왼쪽 고정 */
.st-key-detail_tab_body [class*="st-key-potential_statitem__"]{
  position: relative !important;
}
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] div[data-testid="stElementContainer"]:has(.potential-stat-icon){
  height: 0 !important;
  min-height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  overflow: visible !important;
  position: relative !important;
  z-index: 20 !important;
}
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] .potential-stat-icon{
  position: absolute !important;
  left: 0 !important;
  top: 14px !important;
  width: var(--SELECT_ICON_SIZE) !important;
  height: var(--SELECT_ICON_SIZE) !important;
  transform: translateY(-50%) !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  margin: 0 !important;
  padding: 0 !important;
  z-index: 30 !important;
  pointer-events: none !important;
  overflow: visible !important;
  background: transparent !important;
}
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] .potential-stat-icon img{
  display: block !important;
  width: 100% !important;
  height: 100% !important;
  object-fit: contain !important;
  border-radius: 0 !important;
  background: transparent !important;
}
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] div[data-testid="stElementContainer"]:has(div[data-testid="stTextInput"]){
  margin-left: var(--SELECT_ICON_OFFSET) !important;
  width: calc(100% - var(--SELECT_ICON_OFFSET)) !important;
  max-width: calc(100% - var(--SELECT_ICON_OFFSET)) !important;
  min-width: 0 !important;
}

/* 숫자 입력 박스 하나만 사용 */
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] div[data-testid="stTextInput"]{
  width: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
}
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] div[data-testid="stTextInput"] > div{
  margin: 0 !important;
  padding: 0 !important;
}
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] div[data-testid="stTextInput"] label{
  display: none !important;
}
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] div[data-testid="stTextInput"] [data-baseweb="base-input"],
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] div[data-testid="stTextInput"] [data-baseweb="input"],
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] div[data-testid="stTextInput"] [data-baseweb="base-input"]:hover,
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] div[data-testid="stTextInput"] [data-baseweb="input"]:hover,
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] div[data-testid="stTextInput"] [data-baseweb="base-input"]:focus-within,
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] div[data-testid="stTextInput"] [data-baseweb="input"]:focus-within{
  width: 100% !important;
  height: 28px !important;
  min-height: 28px !important;
  margin: 0 !important;
  padding: 0 !important;
  background: #E5E7EB !important;
  border: 0 !important;
  outline: 0 !important;
  box-shadow: none !important;
  border-radius: 8px !important;
}
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] div[data-testid="stTextInput"] input,
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] div[data-testid="stTextInput"] input:hover,
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] div[data-testid="stTextInput"] input:focus,
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] div[data-testid="stTextInput"] input:focus-visible,
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] div[data-testid="stTextInput"] input[aria-invalid="true"]{
  width: 100% !important;
  height: 28px !important;
  min-height: 28px !important;
  margin: 0 !important;
  padding: 0 8px !important;
  background: transparent !important;
  border: 0 !important;
  outline: 0 !important;
  box-shadow: none !important;
  color: var(--TEXT_MAIN) !important;
  text-align: center !important;
  font-size: 12px !important;
  font-weight: 700 !important;
  line-height: 28px !important;
  caret-color: var(--TEXT_MAIN) !important;
}
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] div[data-testid="stTextInput"] input::placeholder{
  color: #6b7280 !important;
  opacity: 1 !important;
}

/* 8칸 상태 표시. */
.st-key-detail_tab_body [class*="st-key-potential_status_cell__"]{
  width: 100% !important;
  min-width: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
}
.st-key-detail_tab_body [class*="st-key-potential_status_cell__"] > div,
.st-key-detail_tab_body [class*="st-key-potential_status_cell__"] div[data-testid="stVerticalBlock"]{
  width: 100% !important;
  min-width: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  gap: 0 !important;
}
.st-key-detail_tab_body [class*="st-key-potential_status_cell__"]{
  width: 100% !important;
  min-width: 0 !important;
  overflow: visible !important;
}
/* 잠재력 상태 영역 폭 고정 및 말줄임 */
.st-key-detail_tab_body [class*="st-key-potential_inline_body_"] .potential-slot-status{
  width: 100% !important;
  max-width: 100% !important;
  min-width: 0 !important;
  height: 28px !important;
  min-height: 28px !important;
  margin: 13px 0 0 0 !important;
  padding: 0 2px !important;
  border: 0 !important;
  background: transparent !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 4px !important;
  font-size: 10px !important;
  font-weight: 600 !important;
  line-height: 1 !important;
  overflow: hidden !important;
  box-sizing: border-box !important;
}
.st-key-detail_tab_body [class*="st-key-potential_inline_body_"] .potential-slot-status > span{
  display: block !important;
  flex: 0 1 auto !important;
  min-width: 0 !important;
  max-width: none !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
}
.st-key-detail_tab_body [class*="st-key-potential_inline_body_"] .potential-slot-status > b{
  display: block !important;
  flex: 0 0 auto !important;
  width: auto !important;
  min-width: 0 !important;
  text-align: left !important;
  white-space: nowrap !important;
  overflow: visible !important;
}
.st-key-detail_tab_body [class*="st-key-potential_inline_body_"] .potential-slot-ok b{ color: #059669 !important; }
.st-key-detail_tab_body [class*="st-key-potential_inline_body_"] .potential-slot-bad b{ color: #ef4444 !important; }
</style>
"""
CSS += _POTENTIAL_CUSTOM_STEPPER_CSS
DARK_THEME_CSS += _POTENTIAL_CUSTOM_STEPPER_CSS

# 수동 잠재력 숫자 입력칸: 다크모드 전용 색상
# 라이트 테마 테두리 색상 다크 테마 혼입 보정
# 다크 테마에서만 선택자를 뒤에서 다시 덮어 사용
_POTENTIAL_DARK_MODE_CSS = r"""
<style>
[class*="st-key-potential_mode_block_"] .potential-title{
  color: #d6d9df !important;
  -webkit-text-fill-color: #d6d9df !important;
}
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] .potential-stepper-label{
  color: #F1F3F5 !important;
}

.st-key-detail_tab_body [class*="st-key-potential_statitem__"] div[data-testid="stTextInput"] [data-baseweb="base-input"],
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] div[data-testid="stTextInput"] [data-baseweb="input"],
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] div[data-testid="stTextInput"] [data-baseweb="base-input"]:hover,
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] div[data-testid="stTextInput"] [data-baseweb="input"]:hover,
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] div[data-testid="stTextInput"] [data-baseweb="base-input"]:focus-within,
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] div[data-testid="stTextInput"] [data-baseweb="input"]:focus-within{
  background: #303236 !important;
  border: 0 !important;
  outline: 0 !important;
  box-shadow: none !important;
}

.st-key-detail_tab_body [class*="st-key-potential_statitem__"] div[data-testid="stTextInput"] input,
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] div[data-testid="stTextInput"] input:hover,
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] div[data-testid="stTextInput"] input:focus,
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] div[data-testid="stTextInput"] input:focus-visible,
.st-key-detail_tab_body [class*="st-key-potential_statitem__"] div[data-testid="stTextInput"] input[aria-invalid="true"]{
  background: transparent !important;
  color: #F1F3F5 !important;
  caret-color: #F1F3F5 !important;
  border: 0 !important;
  outline: 0 !important;
  box-shadow: none !important;
}
</style>
"""
DARK_THEME_CSS += _POTENTIAL_DARK_MODE_CSS

CSS += _MOBILE_SCROLLBAR_GEOMETRY_CSS
DARK_THEME_CSS += _MOBILE_SCROLLBAR_GEOMETRY_CSS.replace(
    "scrollbar-color: #999ca4 transparent !important;",
    "scrollbar-color: #9ca3af transparent !important;",
).replace(
    "background: #999ca4 !important;",
    "background: #9ca3af !important;",
)
SYSTEM_THEME_CSS = _system_theme_css_from_dark(DARK_THEME_CSS)
