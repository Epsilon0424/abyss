"""Central CSS injection for the Streamlit UI."""
import streamlit as st

CSS = r"""
<style>
/* =====================================================
   0) Font / Variables
===================================================== */
@import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css");

/* Theme policy
   - 기본 팔레트는 라이트 모드입니다.
   - 다크 모드와 기기 설정 추적은 inject_styles()에서 별도 CSS로 추가합니다. */
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

/* =====================================================
   1) Global / Streamlit chrome
===================================================== */
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

/* 앱 CSS가 우측 상단 Streamlit 메뉴를 건드리지 않게 최소화 */
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

/* 실행 중 stale/dim 효과 제거 */
[data-stale="true"],
[data-stale="true"] *,
.stale-element,
.stale-element *{
  opacity: 1 !important;
  filter: none !important;
}

/* =====================================================
   2) Layout / Panels
===================================================== */
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
  .st-key-outer_shell div[data-testid="column"]:has(.st-key-panel_select),
  .st-key-outer_shell div[data-testid="column"]:has(.st-key-panel_result){
    width: 100% !important;
    min-width: 100% !important;
    max-width: 100% !important;
    flex: 0 0 100% !important;
  }

  .st-key-outer_shell div[data-testid="stHorizontalBlock"]:has(div[data-testid="column"] .st-key-panel_select),
  .st-key-outer_shell div[data-testid="stHorizontalBlock"]:has(div[data-testid="column"] .st-key-panel_result),
  .st-key-outer_shell div[data-testid="stHorizontalBlock"]:has(.st-key-panel_select):has(.st-key-panel_result){
    flex-direction: column !important;
    align-items: stretch !important;
    width: 100% !important;
    gap: var(--COL_GAP) !important;
  }

  .st-key-panel_select,
  .st-key-panel_result{
    width: 100% !important;
    min-width: min(800px, calc(100vw - 109px)) !important;
    max-width: 100% !important;
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

/* =====================================================
   3) Typography / Titles
===================================================== */
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

/* =====================================================
   4) Info i / Click boxes
===================================================== */
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
  gap: 4px !important;
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

/* i 라벨 → 다음 드롭다운 */
.st-key-panel_select .info-details:has(.ctl-label):not(.adjustment-info-details){
  margin: 10px 0 -10px 0 !important;
}
.st-key-panel_select .info-details:has(.ctl-label):not(.adjustment-info-details)[open]{
  margin: 10px 0 -20px 0 !important;
}

/* =====================================================
   5) Selectbox / Menu / Icons
===================================================== */
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

/* 아이콘 row: 기본 / 세부사항 / Setting 공통 */
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

/* =====================================================
   6) Spacing - SELECT / RESULT / Tabs
===================================================== */
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
  margin-top: 6px !important;
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

/* =====================================================
   7) Spacing - Party / Detail tab
===================================================== */
/* 기본 탭 파티 드롭다운
   파티가 2마리일 때만 slot1 아래 간격을 압축
   파티가 1마리일 때는 실행 버튼/구분선과 겹치지 않게 slot1 아래 여백 확보
*/

/* [A] 파티 2마리: 1번 → 2번 사이만 압축 */
.st-key-party_group:has([class*="party_slot2"])
  div[data-testid="stElementContainer"]:has([class*="party_slot1"]),
.st-key-party_group_shining:has([class*="party_slot2"])
  div[data-testid="stElementContainer"]:has([class*="party_slot1"]),
.st-key-party_group_phoenix:has([class*="party_slot2"])
  div[data-testid="stElementContainer"]:has([class*="party_slot1"]),
.st-key-party_group_blue:has([class*="party_slot2"])
  div[data-testid="stElementContainer"]:has([class*="party_slot1"]){
  margin-bottom: -28px !important;
  padding-bottom: 0 !important;
}

.st-key-party_group:has([class*="party_slot2"]) [class*="party_slot1"],
.st-key-party_group_shining:has([class*="party_slot2"]) [class*="party_slot1"],
.st-key-party_group_phoenix:has([class*="party_slot2"]) [class*="party_slot1"],
.st-key-party_group_blue:has([class*="party_slot2"]) [class*="party_slot1"]{
  margin-bottom: -11px !important;
  padding-bottom: 0 !important;
}

/* [B] 파티 1마리: 1번 아래 여백을 복구해서 실행 버튼/회색선과 겹침 방지 */
.st-key-party_group:not(:has([class*="party_slot2"]))
  div[data-testid="stElementContainer"]:has([class*="party_slot1"]),
.st-key-party_group_shining:not(:has([class*="party_slot2"]))
  div[data-testid="stElementContainer"]:has([class*="party_slot1"]),
.st-key-party_group_phoenix:not(:has([class*="party_slot2"]))
  div[data-testid="stElementContainer"]:has([class*="party_slot1"]),
.st-key-party_group_blue:not(:has([class*="party_slot2"]))
  div[data-testid="stElementContainer"]:has([class*="party_slot1"]){
  margin-bottom: 8px !important;
  padding-bottom: 0 !important;
}

.st-key-party_group:not(:has([class*="party_slot2"])) [class*="party_slot1"],
.st-key-party_group_shining:not(:has([class*="party_slot2"])) [class*="party_slot1"],
.st-key-party_group_phoenix:not(:has([class*="party_slot2"])) [class*="party_slot1"],
.st-key-party_group_blue:not(:has([class*="party_slot2"])) [class*="party_slot1"]{
  margin-bottom: 4px !important;
  padding-bottom: 0 !important;
}

/* [C] 파티 2번 아래쪽은 구분선과 겹치지 않게 기본 여백 유지 */
.st-key-party_group div[data-testid="stElementContainer"]:has([class*="party_slot2"]),
.st-key-party_group_shining div[data-testid="stElementContainer"]:has([class*="party_slot2"]),
.st-key-party_group_phoenix div[data-testid="stElementContainer"]:has([class*="party_slot2"]),
.st-key-party_group_blue div[data-testid="stElementContainer"]:has([class*="party_slot2"]){
  margin-top: 0 !important;
  margin-bottom: 2px !important;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
}

/* 기본 탭: 세부사항/Setting 탭과 동일하게 세로 gap을 0으로 고정.
   기본 탭만 키 컨테이너가 없어 Streamlit 기본 gap을 따라가므로,
   버전(로컬 vs Cloud)에 따라 간격이 벌어지는 문제를 방지한다. */
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

/* =====================================================
   8) Buttons / Progress
===================================================== */
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
.st-key-run_btn button *{
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

/* =====================================================
   9) Tables / Stat cards / Grids
===================================================== */
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

/* =====================================================
   10) Bottom global note
===================================================== */
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

/* =====================================================
   11) Equip header
===================================================== */
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
  gap: 4px !important;
}
.st-key-panel_select [class*="st-key-equip_hdr_"]{
  margin-bottom: 0 !important;
  padding-bottom: 0 !important;
}
.st-key-panel_select [class*="st-key-equip_hdr_"] + div[data-testid="stElementContainer"]{
  margin-top: -4px !important;
}

/* =====================================================
   12) 기본 / 세부사항 / Setting 아이콘 크기 보정
===================================================== */
/* 장비 값이 '자동'이 아닐 때는 기본 탭과 세부사항 탭 모두 같은 크기로 살짝 확대 */
.st-key-panel_select [class*="st-key-iconrow_equip"] .equip-non-auto-icon{
  width: var(--SELECT_EQUIP_ICON_SIZE) !important;
  height: var(--SELECT_EQUIP_ICON_SIZE) !important;
  left: -1px !important;
}

/* Setting 탭 아이콘은 selectbox 중앙에 맞춘다.
   공통 아이콘 위치에는 기본/세부사항 탭용 +14px 보정이 들어가 있으므로,
   Setting 전용 클래스에서는 그 보정을 제거한다. */
.st-key-panel_select [class*="st-key-iconrow_"] .setting-select-icon{
  top: calc(var(--SEL_H) / 2) !important;
}

/* =====================================================
   13) Setting 탭 간격
===================================================== */
/*
   Setting 탭도 기본/세부사항 탭과 같은 selectbox_with_left_icon 구조를 사용한다.
   아이콘 크기, 왼쪽 여백, 드롭다운 폭은 위의 공통 아이콘 row CSS에서 함께 관리한다.
*/
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
.adjustment-box,
.info-box,
.prog-wrap,
div[data-testid="stMetricValue"]{
  background: #2a2c31 !important;
  border-color: transparent !important;
  color: #f1f3f5 !important;
}
/* 다크모드 Notes 박스 배경을 상단 타이틀 박스와 동일하게 맞춤 */
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

/* RESULT 숫자/탭 콘텐츠/HTML 표 다크모드 보정 */
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
    # DARK_THEME_CSS는 아래에서 여러 <style> 블록이 추가될 수 있다.
    # 기기 설정 모드에서도 다크모드와 같은 보정이 적용되도록
    # 모든 다크 CSS를 하나의 prefers-color-scheme: dark 블록으로 다시 감싼다.
    body = css.replace("<style>", "").replace("</style>", "")
    return f"<style>\n@media (prefers-color-scheme: dark){{\n{body}\n}}\n</style>"


SYSTEM_THEME_CSS = _system_theme_css_from_dark(DARK_THEME_CSS)

def inject_styles() -> None:
    st.markdown(CSS, unsafe_allow_html=True)

    # Theme 드롭다운 변경 시 st.tabs가 기본 탭으로 돌아가는 현상 방지
    # - st.selectbox 자체 rerun은 발생하지만, rerun 전후의 Streamlit element 구조를 같게 유지한다.
    # - 라이트/다크/기기 설정 모두 두 번째 style 슬롯을 항상 렌더링한다.
    theme_mode = st.session_state.get("ui_theme", st.session_state.get("ui_theme_widget", "system"))
    if theme_mode == "dark":
        st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)
    elif theme_mode == "light":
        st.markdown(FORCE_LIGHT_CSS, unsafe_allow_html=True)
    else:
        st.markdown(SYSTEM_THEME_CSS, unsafe_allow_html=True)

# =====================================================
# Dropdown hover background / SELECT row alignment
# =====================================================
CSS += r"""
<style>
/* closed selectbox: hover/focus 때 배경색이 바뀌지 않게 고정 */
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:hover,
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus,
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within{
  background: #e5e7eb !important;
  border: 0 !important;
  outline: none !important;
  box-shadow: none !important;
}

/* opened dropdown: hover/selected 행 배경 칠해지는 것 제거 */
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
/* dark closed selectbox: hover/focus 때 배경색 고정 */
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:hover,
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus,
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within{
  background: #303236 !important;
  border: 0 !important;
  outline: none !important;
  box-shadow: none !important;
}

/* dark opened dropdown: hover/selected 행 배경 칠해지는 것 제거 */
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
# Dark dropdown opened menu color = closed selectbox
# - 펼친 드롭다운 메뉴 배경을 닫힌 드롭다운(#303236)과 동일하게 맞춤
# - 흰색 테두리/focus ring 제거 유지
# =====================================================
DARK_THEME_CSS += r"""
<style>
/* 다크모드 드롭다운 펼침 메뉴 배경을 닫힌 selectbox와 동일하게 고정 */
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

/* hover/selected 시 배경을 바꾸지 않고 글자색만 강조 */
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

/* focus로 생기는 흰색 링 제거 */
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
# Tabs overflow arrow fade fix
# - st.tabs가 좁아져 스크롤 화살표가 생길 때
#   사각형 배경 대신 투명 → 패널 배경 그라데이션으로 자연스럽게 보정
# =====================================================
_TAB_OVERFLOW_ARROW_FIX_CSS = r"""
<style>
/* 탭 리스트 자체는 투명 유지 */
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

/* hover/focus 때도 흰 사각형이 다시 생기지 않게 같은 그라데이션 유지 */
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

# 다크모드에서 탭 오른쪽/왼쪽 끝에 나타나는 흰색 스크롤 페이드(그라데이션) 제거.
# Streamlit이 스크롤 버튼(aria-label="Scroll tabs left/right")에
# 라이트 테마 배경색(흰색) 기반 background-image를 깔기 때문에,
# 다크모드에서는 요소 형태(button/div, 위치)와 무관하게 배경을 전부 투명 처리한다.
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
/* 탭 리스트 자체/래퍼의 페이드성 pseudo-element도 다크에서는 무색 처리 */
div[data-testid="stTabs"] div[data-baseweb="tab-list"]::before,
div[data-testid="stTabs"] div[role="tablist"]::before{
  background: transparent !important;
  background-image: none !important;
}
</style>
"""


DARK_THEME_CSS += r"""
<style>
/* page scrollbar: remove the white track in dark mode */
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
  width: 8px !important;
  height: 8px !important;
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
  border-radius: 10px !important;
  border: 1px solid #303236 !important;
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

# DARK_THEME_CSS에 드롭다운/focus 보정 CSS를 모두 추가한 뒤,
# 기기 설정 모드용 CSS를 다시 생성한다.
SYSTEM_THEME_CSS = _system_theme_css_from_dark(DARK_THEME_CSS)


# Additional tab overflow cleanup: remove remaining white fade/scroll-button artifacts in all themes.
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


# Final scrollbar colors: light and dark use the exact requested reference colors.
CSS += r"""
<style>
/* cookie-sim: final all-scrollbar thumb color override */
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
/* cookie-sim: final all-scrollbar thumb color override */
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


# Streamlit tabs overflow fade: use the simulator panel color instead of Streamlit theme bgColor.
# Streamlit adds a ::after fade to stTabs when the tab labels overflow. Its default bgColor is
# pure white even inside the custom light/dark panels, which creates a bright vertical strip.
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
