"""
================================================================================
프로젝트명: 퍼스널 칸반 마스터 보드 (Personal Kanban Master Board)
작성자 / 저작권자: [본인 성함 또는 닉네임 기입]
Copyright (c) 2026 [본인 성함 또는 닉네임]. All rights reserved.

[ 라이선스 고지 (License Notice) ]
1. 본 프로젝트의 소스 코드는 MIT 라이선스에 따라 자유롭게 사용, 수정, 배포할 수 있습니다.
2. 본 소프트웨어는 GUI 구현을 위해 'PyQt6' 라이브러리를 사용하고 있으며, 
   PyQt6는 Riverbank Computing의 저작물로서 GNU General Public License (GPL)를 따릅니다.
================================================================================
"""

import calendar
import json
import math
import os
import re
import sys
import tempfile
from bisect import bisect_left, bisect_right
from datetime import date as PyDate, datetime, timedelta
from html import escape as html_escape

from PyQt6.QtCore import Qt, QDate, QPointF, QRectF, QSettings, QSize, QTimer, QStandardPaths, QEvent
from PyQt6.QtGui import (
    QAbstractTextDocumentLayout,
    QBrush,
    QColor,
    QFont,
    QIcon,
    QKeyEvent,
    QPainter,
    QPainterPath,
    QPalette,
    QPen,
    QPixmap,
    QPolygonF,
    QTextCharFormat,
    QTextDocument,
    QTextOption,
)
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTextEdit,
    QComboBox,
    QDialog,
    QFormLayout,
    QDialogButtonBox,
    QDateEdit,
    QScrollArea,
    QGraphicsDropShadowEffect,
    QCalendarWidget,
    QSizePolicy,
    QToolTip,
    QToolButton,
    QSlider,
    QRadioButton,
    QGroupBox,
    QTextBrowser,
    QMessageBox,
    QCheckBox,
    QMenu,
    QSystemTrayIcon,
)


# 7가지 파스텔 포스트잇 색상
COLOR_PALETTE = {
    "노란색": "#FFF59D",
    "연두색": "#C8E6C9",
    "하늘색": "#B3E5FC",
    "핑크색": "#F8BBD0",
    "주황색": "#FFE0B2",
    "회색": "#CFD8DC",
    "보라색": "#E1BEE7",
}

# 칸(열)의 순서와 키
STATUS_KEYS = ("todo", "today", "inprogress", "waiting", "done")

# 마감일 입력창과 색상 콤보박스의 높이를 같게 맞춤
FIELD_HEIGHT = 28

# 라벨 구성: [글자 칸 3개][콜론 칸]
CHAR_SLOT_WIDTH = 16
NAME_SLOTS = 3
NAME_WIDTH = CHAR_SLOT_WIDTH * NAME_SLOTS
COLON_WIDTH = 8
LABEL_WIDTH = NAME_WIDTH + COLON_WIDTH

# 포스트잇 본문에서 공백 없이 이어진 글자열을 이 글자 수마다 끊어 줄바꿈 가능하게 함
POST_IT_CHUNK_CHARS = 10
ZERO_WIDTH_SPACE = "\u200b"

# 포스트잇 본문 표시 설정
POST_IT_BODY_JUSTIFY = True   # True: 양쪽정렬, False: 왼쪽정렬
POST_IT_BODY_BOLD = False     # True: 굵게, False: 보통 굵기
POST_IT_BODY_FONT_PX = 14     # 본문 글자 크기(px)

# 월간 일정표 레이아웃 설정
MONTH_WEEKDAY_H = 24          # 요일 헤더 높이
MONTH_DAY_NUM_H = 22          # 날짜 숫자 영역 높이
MONTH_LANE_H = 26             # 막대 한 줄의 높이
MONTH_BAR_H = 18              # 막대 자체의 높이
MONTH_BAR_TIP = 8             # 막대 끝 화살촉의 가로 길이
MONTH_HANDLE_W = 10           # 막대 양 끝에서 날짜 조절로 잡는 폭(px)

# 빨간색으로 표시할 연도 범위
HOLIDAY_YEARS = range(2000, 2131)

# 투명도 설정 범위(%)
OPACITY_MIN = 30
OPACITY_MAX = 100


def get_program_dir():
    """프로그램 파일이 있는 폴더를 돌려줍니다 (.py 실행과 .exe 실행 모두 지원)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))

    return os.path.dirname(os.path.abspath(__file__))


DATA_DIR = get_program_dir()
DATA_FILE = os.path.join(DATA_DIR, "postits.json")
DATA_VERSION = 1


# ---------------------------------------------------------------
# 테마 (일반 모드 / 다크 모드)
# ---------------------------------------------------------------

THEMES = {
    "light": {
        "window_bg": "#f0f2f5",
        "column_bg": "#f4f5f7",
        "column_border": "#d1d5db",
        "text": "#2d3748",
        "sub_text": "#718096",
        "dialog_bg": "#f7fafc",
        "field_bg": "#ffffff",
        "field_border": "#cbd5e0",
        "field_focus": "#3182ce",
        "drop_bg": "#edf2f7",
        "drop_hover": "#e2e8f0",
        "button_bg": "#edf2f7",
        "button_hover": "#e2e8f0",
        "button_border": "#cbd5e0",
        "accent": "#2b6cb0",
        "icon": "#2d3748",
        "arrow": "#2d3748",
        "holiday": "#e53e3e",
        "cal_bg": "#ffffff",
        "cal_other_bg": "#f7f8fa",
        "cal_header_bg": "#f7fafc",
        "cal_line": "#e2e8f0",
        "cal_day_text": "#2d3748",
        "cal_other_text": "#a0aec0",
        "cal_sat": "#3182ce",
    },
    "dark": {
        "window_bg": "#1a1d24",
        "column_bg": "#252a33",
        "column_border": "#4a5262",
        "text": "#e2e8f0",
        "sub_text": "#a0aec0",
        "dialog_bg": "#20242c",
        "field_bg": "#2d3340",
        "field_border": "#4a5262",
        "field_focus": "#63b3ed",
        "drop_bg": "#363d4b",
        "drop_hover": "#424a5b",
        "button_bg": "#363d4b",
        "button_hover": "#424a5b",
        "button_border": "#4a5262",
        "accent": "#3182ce",
        "icon": "#e2e8f0",
        "arrow": "#e2e8f0",
        "holiday": "#fc8181",
        "cal_bg": "#252a33",
        "cal_other_bg": "#1e222a",
        "cal_header_bg": "#2a303b",
        "cal_line": "#3d4453",
        "cal_day_text": "#e2e8f0",
        "cal_other_text": "#5a6478",
        "cal_sat": "#63b3ed",
    },
}

THEME_LABELS = {"light": "일반 모드", "dark": "다크 모드"}

APP_STATE = {
    "theme": "light",
    "board_opacity": 100,
    "postit_opacity": 100,
    "tray_enabled": False,
}

ICON_FILE_NAMES = ("kanban_icon.ico", "kanban_icon.png")

def find_app_icon():
    folders = [
        get_program_dir(),
        QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DesktopLocation),
    ]

    for folder in folders:
        for name in ICON_FILE_NAMES:
            path = os.path.join(folder, name)

            if os.path.exists(path):
                icon = QIcon(path)

                if not icon.isNull():
                    return icon

    return QIcon()


def theme():
    return THEMES[APP_STATE["theme"]]


def clamp_opacity(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = 100

    return max(OPACITY_MIN, min(OPACITY_MAX, value))


def postit_alpha():
    return round(255 * APP_STATE["postit_opacity"] / 100)


def load_app_settings():
    settings = QSettings("PersonalKanban", "MasterBoard")

    name = settings.value("theme", "light")
    APP_STATE["theme"] = name if name in THEMES else "light"
    APP_STATE["board_opacity"] = clamp_opacity(
        settings.value("board_opacity", 100)
    )
    APP_STATE["postit_opacity"] = clamp_opacity(
        settings.value("postit_opacity", 100)
    )
    APP_STATE["tray_enabled"] = settings.value("tray_enabled", False, type=bool)

def save_app_settings():
    settings = QSettings("PersonalKanban", "MasterBoard")

    settings.setValue("theme", APP_STATE["theme"])
    settings.setValue("board_opacity", APP_STATE["board_opacity"])
    settings.setValue("postit_opacity", APP_STATE["postit_opacity"])
    settings.setValue("tray_enabled", APP_STATE["tray_enabled"])


def valid_date_text(value, fallback):
    try:
        return PyDate.fromisoformat(str(value)).isoformat()
    except (TypeError, ValueError):
        return fallback


def normalize_card(raw):
    today = datetime.now().strftime("%Y-%m-%d")

    status = raw.get("status")
    if status not in STATUS_KEYS:
        status = "todo"

    color = raw.get("color")
    if not isinstance(color, str) or not QColor(color).isValid():
        color = COLOR_PALETTE["노란색"]

    return {
        "id": str(raw.get("id") or datetime.now().timestamp()),
        "content": str(raw.get("content", "")),
        "color": color,
        "status": status,
        "created_date": valid_date_text(raw.get("created_date"), today),
        "due_date": valid_date_text(raw.get("due_date"), today),
        "completed_date": valid_date_text(raw.get("completed_date"), ""),
    }


def load_board_data():
    if not os.path.exists(DATA_FILE):
        return None, None

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            payload = json.load(f)

        raw_cards = payload.get("cards") if isinstance(payload, dict) else None

        if not isinstance(raw_cards, list):
            raise ValueError("cards 목록이 없습니다.")

        cards = [normalize_card(c) for c in raw_cards if isinstance(c, dict)]
        return cards, None

    except (OSError, ValueError) as error:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = f"{DATA_FILE}.broken-{stamp}"

        try:
            os.replace(DATA_FILE, backup)
            where = f"\n\n손상된 파일은 다음 위치에 보관했습니다:\n{backup}"
        except OSError:
            where = ""

        message = (
            "포스트잇 데이터 파일을 읽지 못해 빈 보드로 시작합니다."
            f"{where}\n\n오류: {error}"
        )
        return [], message


def write_board_data(cards):
    payload = {"version": DATA_VERSION, "cards": cards}

    os.makedirs(DATA_DIR, exist_ok=True)

    tmp_path = DATA_FILE + ".tmp"

    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    os.replace(tmp_path, DATA_FILE)


def dialog_qss():
    t = theme()

    return f"""
    QDialog {{
        background-color: {t['dialog_bg']};
    }}

    QLabel {{
        color: {t['text']};
        background: transparent;
    }}

    QGroupBox {{
        color: {t['text']};
        border: 1px solid {t['field_border']};
        border-radius: 6px;
        margin-top: 12px;
        padding: 10px 8px 8px 8px;
        font-weight: bold;
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 4px;
    }}

    QRadioButton {{
        color: {t['text']};
        font-size: 13px;
    }}

    QPushButton {{
        background-color: {t['button_bg']};
        color: {t['text']};
        border: 1px solid {t['button_border']};
        border-radius: 6px;
        padding: 5px 14px;
    }}

    QPushButton:hover {{
        background-color: {t['button_hover']};
    }}
    """


def calendar_qss(t):
    return f"""
    QCalendarWidget {{
        background-color: {t['cal_bg']};
    }}

    QCalendarWidget QWidget#qt_calendar_navigationbar {{
        background-color: {t['cal_header_bg']};
    }}

    QCalendarWidget QToolButton {{
        color: {t['text']};
        background: transparent;
        border: none;
        font-weight: bold;
        padding: 2px 6px;
    }}

    QCalendarWidget QToolButton:hover {{
        background-color: {t['button_hover']};
        border-radius: 4px;
    }}

    QCalendarWidget QMenu {{
        background-color: {t['cal_bg']};
        color: {t['text']};
    }}

    QCalendarWidget QSpinBox {{
        background-color: {t['field_bg']};
        color: {t['text']};
        border: 1px solid {t['field_border']};
    }}

    QCalendarWidget QAbstractItemView {{
        background-color: {t['cal_bg']};
        color: {t['cal_day_text']};
        selection-background-color: {t['accent']};
        selection-color: #ffffff;
        outline: 0;
    }}
    """


def icon_button_qss(t):
    return f"""
    QPushButton {{
        background-color: {t['button_bg']};
        border: 1px solid {t['button_border']};
        border-radius: 6px;
    }}

    QPushButton:hover {{
        background-color: {t['button_hover']};
    }}
    """


# ---------------------------------------------------------------
# 음력 계산
# ---------------------------------------------------------------

_EPOCH = PyDate(1970, 1, 1)
_JD_UNIX_EPOCH = 2440587.5
_KST = 9 / 24


def _jd_of(d):
    return (d - _EPOCH).days + _JD_UNIX_EPOCH


def _jde_to_kst_date(jde):
    dt = datetime(1970, 1, 1) + timedelta(
        days=jde - _JD_UNIX_EPOCH + _KST
    )
    return PyDate(dt.year, dt.month, dt.day)


def _new_moon_jde(k):
    T = k / 1236.85
    jde = (
        2451550.09766
        + 29.530588861 * k
        + 0.00015437 * T * T
        - 0.000000150 * T ** 3
        + 0.00000000073 * T ** 4
    )

    E = 1 - 0.002516 * T - 0.0000074 * T * T
    M = math.radians((2.5534 + 29.10535670 * k - 0.0000014 * T * T) % 360)
    Mp = math.radians(
        (201.5643 + 385.81693528 * k + 0.0107582 * T * T
         + 0.00001238 * T ** 3) % 360
    )
    F = math.radians(
        (160.7108 + 390.67050284 * k - 0.0016118 * T * T
         - 0.00000227 * T ** 3) % 360
    )
    Om = math.radians((124.7746 - 1.56375588 * k + 0.0020672 * T * T) % 360)

    s = math.sin
    corr = (
        -0.40720 * s(Mp)
        + 0.17241 * E * s(M)
        + 0.01608 * s(2 * Mp)
        + 0.01039 * s(2 * F)
        + 0.00739 * E * s(Mp - M)
        - 0.00514 * E * s(Mp + M)
        + 0.00208 * E * E * s(2 * M)
        - 0.00111 * s(Mp - 2 * F)
        - 0.00057 * s(Mp + 2 * F)
        + 0.00056 * E * s(2 * Mp + M)
        - 0.00042 * s(3 * Mp)
        + 0.00042 * E * s(M + 2 * F)
        + 0.00038 * E * s(M - 2 * F)
        - 0.00024 * E * s(2 * Mp - M)
        - 0.00017 * s(Om)
        - 0.00007 * s(Mp + 2 * M)
        + 0.00004 * s(2 * Mp - 2 * F)
        + 0.00004 * s(3 * M)
        + 0.00003 * s(Mp + M - 2 * F)
        + 0.00003 * s(2 * Mp + 2 * F)
        - 0.00003 * s(Mp + M + 2 * F)
        + 0.00003 * s(Mp - M + 2 * F)
        - 0.00002 * s(Mp - M - 2 * F)
        - 0.00002 * s(3 * Mp + M)
        + 0.00002 * s(4 * Mp)
    )
    return jde + corr


def _sun_longitude(jd):
    T = (jd - 2451545.0) / 36525
    L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T
    M = math.radians((357.52911 + 35999.05029 * T - 0.0001537 * T * T) % 360)
    C = (
        (1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(M)
        + (0.019993 - 0.000101 * T) * math.sin(2 * M)
        + 0.000289 * math.sin(3 * M)
    )
    omega = math.radians(125.04 - 1934.136 * T)
    return (L0 + C - 0.00569 - 0.00478 * math.sin(omega)) % 360


_LUNAR_INFO = None


def _build_lunar_info(start_year, end_year):
    k0 = math.floor(
        (_jd_of(PyDate(start_year - 1, 6, 1)) - 2451550.09766)
        / 29.530588861
    )
    k1 = math.ceil(
        (_jd_of(PyDate(end_year + 1, 6, 1)) - 2451550.09766)
        / 29.530588861
    )
    starts = [
        _jde_to_kst_date(_new_moon_jde(k))
        for k in range(k0, k1 + 1)
    ]

    def sector(d):
        jd_midnight_kst = _jd_of(d) - _KST
        return int(_sun_longitude(jd_midnight_kst) // 30) % 12

    t_start = PyDate(start_year - 1, 6, 1)
    t_end = PyDate(end_year + 1, 6, 1)

    zhongqi = []
    prev = sector(t_start)
    d = t_start

    while d < t_end:
        nxt = d + timedelta(days=1)
        cur = sector(nxt)

        if cur != prev:
            zhongqi.append((nxt, cur))

        prev = cur
        d = nxt

    zq_dates = [z[0] for z in zhongqi]

    def has_zhongqi(i):
        j = bisect_left(zq_dates, starts[i])
        return j < len(zq_dates) and zq_dates[j] < starts[i + 1]

    anchors = []

    for d_sol, sec in zhongqi:
        if sec == 9:
            i = bisect_right(starts, d_sol) - 1
            anchors.append((i, d_sol.year))

    info = {}

    for (a, year_a), (b, _) in zip(anchors, anchors[1:]):
        n = b - a
        leap_t = None

        if n == 13:
            for t in range(1, 13):
                if not has_zhongqi(a + t):
                    leap_t = t
                    break
        elif n != 12:
            raise ValueError(f"음력 달 개수 이상: {n}")

        prev_num = None

        for t in range(n):
            i = a + t

            if leap_t is not None and t == leap_t:
                num = prev_num
                leap = True
            else:
                shift = 1 if (leap_t is not None and t > leap_t) else 0
                num = ((10 + t - shift) % 12) + 1
                leap = False

            year = year_a if num in (11, 12) else year_a + 1

            info.setdefault((year, num, leap), starts[i])
            prev_num = num

    return info


def get_lunar_info():
    global _LUNAR_INFO

    if _LUNAR_INFO is None:
        _LUNAR_INFO = _build_lunar_info(1999, 2132)

    return _LUNAR_INFO


def lunar_to_solar(year, month, day, leap=False):
    start = get_lunar_info().get((year, month, leap))

    if start is None:
        return None

    return start + timedelta(days=day - 1)


def to_qdate(pydate):
    return QDate(pydate.year, pydate.month, pydate.day)


def lunar_holiday_entries(year):
    entries = []

    seol = lunar_to_solar(year, 1, 1)

    if seol is not None:
        days = [
            seol - timedelta(days=1),
            seol,
            seol + timedelta(days=1),
        ]
        entries.append(
            ([to_qdate(d) for d in days], "설날 연휴", "sunday")
        )

    buddha = lunar_to_solar(year, 4, 8)

    if buddha is not None:
        entries.append(
            ([to_qdate(buddha)], "부처님오신날", "weekend")
        )

    chuseok = lunar_to_solar(year, 8, 15)

    if chuseok is not None:
        days = [
            chuseok - timedelta(days=1),
            chuseok,
            chuseok + timedelta(days=1),
        ]
        entries.append(
            ([to_qdate(d) for d in days], "추석 연휴", "sunday")
        )

    return entries


# ---------------------------------------------------------------
# 공휴일 계산
# ---------------------------------------------------------------

FIXED_HOLIDAYS = [
    (1, 1, "신정", False),
    (3, 1, "삼일절", True),
    (5, 1, "노동절", True),
    (5, 5, "어린이날", True),
    (6, 6, "현충일", False),
    (7, 17, "제헌절", True),
    (8, 15, "광복절", True),
    (10, 3, "개천절", True),
    (10, 9, "한글날", True),
    (12, 25, "성탄절", True),
]

ONE_OFF_HOLIDAYS = {
    2026: [
        (6, 3, "임시공휴일(지방선거)"),
    ],
}


def make_key(date):
    return (date.year(), date.month(), date.day())


def build_holidays(year):
    holidays = {}
    entries = []

    for month, day, name, substitutable in FIXED_HOLIDAYS:
        rule = "weekend" if substitutable else None
        entries.append(([QDate(year, month, day)], name, rule))

    entries.extend(lunar_holiday_entries(year))

    for month, day, name in ONE_OFF_HOLIDAYS.get(year, []):
        entries.append(([QDate(year, month, day)], name, None))

    for days, name, _ in entries:
        for day in days:
            if day.isValid():
                holidays[make_key(day)] = name

    for days, name, rule in entries:
        if not days or not days[0].isValid():
            continue

        if rule == "weekend":
            condition = days[0].dayOfWeek() >= 6
            anchor = days[0]
        elif rule == "sunday":
            condition = any(day.dayOfWeek() == 7 for day in days)
            anchor = days[-1]
        else:
            continue

        if condition:
            candidate = anchor.addDays(1)

            while (
                candidate.dayOfWeek() >= 6
                or make_key(candidate) in holidays
            ):
                candidate = candidate.addDays(1)

            holidays[make_key(candidate)] = f"대체공휴일({name})"

    return holidays


_HOLIDAY_CACHE = None


def get_all_holidays():
    global _HOLIDAY_CACHE

    if _HOLIDAY_CACHE is None:
        result = {}

        for year in HOLIDAY_YEARS:
            result.update(build_holidays(year))

        _HOLIDAY_CACHE = result

    return _HOLIDAY_CACHE


# ---------------------------------------------------------------
# 아이콘 그리기
# ---------------------------------------------------------------

def make_calendar_icon(color_hex, size=20):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    color = QColor(color_hex)

    painter.setPen(QPen(color, 1.6))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(QRectF(2.5, 4.0, 15.0, 13.5), 2.5, 2.5)
    painter.drawLine(QPointF(2.5, 8.5), QPointF(17.5, 8.5))
    painter.drawLine(QPointF(6.5, 2.0), QPointF(6.5, 5.5))
    painter.drawLine(QPointF(13.5, 2.0), QPointF(13.5, 5.5))

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color)

    for row in range(2):
        for col in range(3):
            painter.drawRect(
                QRectF(5.0 + col * 4.0, 10.5 + row * 3.5, 2.2, 2.2)
            )

    painter.end()
    return QIcon(pixmap)


def make_gear_icon(color_hex, size=20):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.translate(size / 2, size / 2)

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(color_hex))

    painter.drawEllipse(QPointF(0, 0), 6.0, 6.0)

    for i in range(8):
        painter.save()
        painter.rotate(i * 45)
        painter.drawRoundedRect(QRectF(-2.0, -9.0, 4.0, 5.0), 1.0, 1.0)
        painter.restore()

    painter.setCompositionMode(
        QPainter.CompositionMode.CompositionMode_Clear
    )
    painter.drawEllipse(QPointF(0, 0), 2.6, 2.6)

    painter.end()
    return QIcon(pixmap)


def make_chevron_icon(direction, color_hex, size=14):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    pen = QPen(QColor(color_hex))
    pen.setWidthF(1.8)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)

    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    if direction == "left":
        points = [QPointF(9.0, 3.0), QPointF(4.5, 7.0), QPointF(9.0, 11.0)]
    else:
        points = [QPointF(5.0, 3.0), QPointF(9.5, 7.0), QPointF(5.0, 11.0)]

    painter.drawPolyline(QPolygonF(points))
    painter.end()
    return QIcon(pixmap)


_V_ARROW_ICON_PATHS = {}


def get_v_arrow_icon_path():
    color_hex = theme()["arrow"]

    if color_hex not in _V_ARROW_ICON_PATHS:
        size = 12

        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen(QColor(color_hex))
        pen.setWidthF(1.8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)

        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPolyline(
            QPolygonF([
                QPointF(2.5, 4.5),
                QPointF(6.0, 8.0),
                QPointF(9.5, 4.5),
            ])
        )
        painter.end()

        file_name = f"kanban_v_arrow_{color_hex.lstrip('#')}.png"
        path = os.path.join(tempfile.gettempdir(), file_name)
        pixmap.save(path, "PNG")

        _V_ARROW_ICON_PATHS[color_hex] = path.replace("\\", "/")

    return _V_ARROW_ICON_PATHS[color_hex]


# ---------------------------------------------------------------
# 공통 입력 필드 스타일
# ---------------------------------------------------------------

def build_field_style():
    t = theme()
    arrow_path = get_v_arrow_icon_path()

    return f"""
    QTextEdit, QDateEdit, QComboBox {{
        background-color: {t['field_bg']};
        border: 1px solid {t['field_border']};
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 13px;
        color: {t['text']};
    }}

    QTextEdit:focus, QDateEdit:focus, QComboBox:focus {{
        border: 1px solid {t['field_focus']};
    }}

    QDateEdit::drop-down, QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 26px;
        border: none;
        border-left: 1px solid {t['field_border']};
        border-top-right-radius: 4px;
        border-bottom-right-radius: 4px;
        background-color: {t['drop_bg']};
    }}

    QDateEdit::drop-down:hover, QComboBox::drop-down:hover {{
        background-color: {t['drop_hover']};
    }}

    QDateEdit::down-arrow, QComboBox::down-arrow {{
        image: url({arrow_path});
        width: 12px;
        height: 12px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {t['field_bg']};
        color: {t['text']};
        selection-background-color: {t['accent']};
        selection-color: #ffffff;
    }}
    """


def create_form_layout(dialog):
    layout = QFormLayout(dialog)
    layout.setFieldGrowthPolicy(
        QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
    )
    return layout


def make_form_label(name, vertical=Qt.AlignmentFlag.AlignVCenter):
    if len(name) != NAME_SLOTS:
        raise ValueError(
            f"라벨은 {NAME_SLOTS}칸이어야 합니다: {name!r}"
        )

    style = (
        "font-size: 13px;"
        f"color: {theme()['text']};"
        "background: transparent;"
    )

    wrapper = QWidget()
    wrapper.setFixedWidth(LABEL_WIDTH)

    layout = QHBoxLayout(wrapper)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    for ch in name:
        char_label = QLabel(ch)
        char_label.setFixedWidth(CHAR_SLOT_WIDTH)
        char_label.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | vertical
        )
        char_label.setStyleSheet(style)
        layout.addWidget(char_label, 0, vertical)

    colon_label = QLabel(":")
    colon_label.setFixedWidth(COLON_WIDTH)
    colon_label.setAlignment(
        Qt.AlignmentFlag.AlignHCenter | vertical
    )
    colon_label.setStyleSheet(style)
    layout.addWidget(colon_label, 0, vertical)

    return wrapper


def make_text_edit():
    edit = QTextEdit()
    edit.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Expanding,
    )
    edit.setStyleSheet(build_field_style())
    return edit


def make_color_combo():
    combo = QComboBox()
    combo.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Fixed,
    )
    combo.setFixedHeight(FIELD_HEIGHT)
    combo.setStyleSheet(build_field_style())
    return combo


class KoreanCalendarWidget(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        t = theme()
        self.setStyleSheet(calendar_qss(t))

        holiday_format = QTextCharFormat()
        holiday_format.setForeground(QBrush(QColor(t["holiday"])))

        self.setWeekdayTextFormat(
            Qt.DayOfWeek.Sunday,
            holiday_format,
        )

        for year, month, day in get_all_holidays().keys():
            self.setDateTextFormat(
                QDate(year, month, day),
                holiday_format,
            )

        prev_btn = self.findChild(QToolButton, "qt_calendar_prevmonth")
        next_btn = self.findChild(QToolButton, "qt_calendar_nextmonth")

        if prev_btn is not None:
            prev_btn.setIcon(make_chevron_icon("left", t["text"]))

        if next_btn is not None:
            next_btn.setIcon(make_chevron_icon("right", t["text"]))

    def go_to_current_month(self):
        today = QDate.currentDate()
        self.setCurrentPage(today.year(), today.month())

    def showEvent(self, event):
        self.go_to_current_month()
        super().showEvent(event)
        QTimer.singleShot(0, self.go_to_current_month)


class CustomDateEdit(QDateEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setCalendarPopup(True)
        self.setCalendarWidget(KoreanCalendarWidget(self))

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.setFixedHeight(FIELD_HEIGHT)
        self.setStyleSheet(build_field_style())


class PostItEditDialog(QDialog):
    def __init__(
        self,
        current_content,
        current_due,
        current_color,
        parent=None,
    ):
        super().__init__(parent)

        self.setWindowTitle("포스트잇 수정")
        self.resize(320, 240)
        self.setStyleSheet(dialog_qss())

        layout = create_form_layout(self)

        self.content_edit = make_text_edit()
        self.content_edit.setPlainText(current_content)
        layout.addRow(
            make_form_label("내 용", Qt.AlignmentFlag.AlignTop),
            self.content_edit,
        )

        self.due_edit = CustomDateEdit()

        self.due_edit.setDate(
            QDate.fromString(current_due, "yyyy-MM-dd")
        )
        self.due_edit.setDisplayFormat("yyyy-MM-dd")
        layout.addRow(make_form_label("마감일"), self.due_edit)

        self.color_combo = make_color_combo()

        for name in COLOR_PALETTE.keys():
            self.color_combo.addItem(name)

            if COLOR_PALETTE[name] == current_color:
                self.color_combo.setCurrentText(name)

        layout.addRow(make_form_label("색 상"), self.color_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

    def get_data(self):
        color_name = self.color_combo.currentText()

        return {
            "content": self.content_edit.toPlainText(),
            "due_date": self.due_edit.date().toString("yyyy-MM-dd"),
            "color": COLOR_PALETTE[color_name],
        }


def soft_wrap_text(text):
    parts = re.split(r"(\s+)", text)
    result = []

    for part in parts:
        if part and not part.isspace() and len(part) > POST_IT_CHUNK_CHARS:
            chunks = [
                part[i:i + POST_IT_CHUNK_CHARS]
                for i in range(0, len(part), POST_IT_CHUNK_CHARS)
            ]
            part = ZERO_WIDTH_SPACE.join(chunks)

        result.append(part)

    return "".join(result)


class JustifiedTextLabel(QWidget):
    TEXT_COLOR = "#1a202c"

    def __init__(self, parent=None):
        super().__init__(parent)

        self.doc = QTextDocument(self)
        self.doc.setDocumentMargin(0)

        font = QFont()
        font.setPixelSize(POST_IT_BODY_FONT_PX)
        font.setBold(POST_IT_BODY_BOLD)
        self.doc.setDefaultFont(font)

        align = (
            Qt.AlignmentFlag.AlignJustify
            if POST_IT_BODY_JUSTIFY
            else Qt.AlignmentFlag.AlignLeft
        )
        option = QTextOption(align)
        option.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        self.doc.setDefaultTextOption(option)

        self.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Preferred,
        )
        self.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True,
        )
        self.setStyleSheet("background: transparent; border: none;")

    def setText(self, text):
        self.doc.setPlainText(soft_wrap_text(text))
        self.updateGeometry()
        self.update()

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        if width <= 0:
            return 0

        self.doc.setTextWidth(width)
        return math.ceil(self.doc.size().height())

    def sizeHint(self):
        width = self.width() if self.width() > 0 else 200
        return QSize(width, self.heightForWidth(width))

    def paintEvent(self, event):
        self.doc.setTextWidth(self.width())

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        context = QAbstractTextDocumentLayout.PaintContext()
        context.palette.setColor(
            QPalette.ColorRole.Text,
            QColor(self.TEXT_COLOR),
        )

        self.doc.documentLayout().draw(painter, context)
        painter.end()


class PostItWidget(QWidget):
    def __init__(self, data, column_ref):
        super().__init__()

        self.data = data
        self.column_ref = column_ref
        self.main_app = column_ref.main_app
        self.dragging = False
        self.hovered = False

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_created = QLabel()
        self.lbl_created.setStyleSheet(
            "font-size: 11px;"
            "font-weight: bold;"
            "color: #555;"
            "background: transparent;"
        )

        self.lbl_due = QLabel()
        self.lbl_due.setStyleSheet(
            "font-size: 11px;"
            "font-weight: bold;"
            "color: #c53030;"
            "background: transparent;"
        )

        top_layout.addWidget(self.lbl_created)
        top_layout.addStretch()
        top_layout.addWidget(self.lbl_due)

        layout.addLayout(top_layout)

        self.lbl_content = JustifiedTextLabel()
        layout.addWidget(self.lbl_content)

        self.bottom_bar = QWidget()
        self.bottom_bar.setStyleSheet("background: transparent;")

        bottom_layout = QHBoxLayout(self.bottom_bar)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_completed = QLabel()
        self.lbl_completed.setStyleSheet(
            "font-size: 11px;"
            "color: #276749;"
            "font-weight: bold;"
            "background: transparent;"
        )

        self.btn_delete = QPushButton("×")
        self.btn_delete.setFixedSize(18, 18)
        self.btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_delete.setToolTip("삭제")
        self.btn_delete.setStyleSheet(
            """
            QPushButton {
                background: transparent;
                color: #e53e3e;
                border: none;
                font-size: 16px;
                font-weight: bold;
                padding: 0px;
            }

            QPushButton:hover {
                color: #9b2c2c;
            }
            """
        )
        self.btn_delete.clicked.connect(self.request_delete)

        bottom_layout.addWidget(self.lbl_completed)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.btn_delete)

        layout.addWidget(self.bottom_bar)

        self.setLayout(layout)

        self.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Maximum,
        )

        self.update_texts()
        self.setCursor(Qt.CursorShape.OpenHandCursor)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(2, 4)

        self.setGraphicsEffect(shadow)

    def is_in_done_column(self):
        return self.column_ref.status_key == "done"

    def update_texts(self):
        self.lbl_created.setText(self.data["created_date"])
        self.lbl_due.setText(f"마감: {self.data['due_date']}")
        self.lbl_content.setText(self.data["content"])

        completed = self.data["completed_date"]
        self.lbl_completed.setText(f"완료: {completed}" if completed else "")

        in_done = self.is_in_done_column()

        self.btn_delete.setVisible(in_done)
        self.bottom_bar.setVisible(bool(completed) or in_done)

        self.updateGeometry()
        self.update()

    def request_delete(self):
        self.main_app.delete_card(self)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)

        border_color = (
            QColor("#777777") if self.hovered else QColor(0, 0, 0, 31)
        )

        bg_color = QColor(self.data["color"])
        bg_color.setAlpha(postit_alpha())

        painter.setPen(QPen(border_color, 1))
        painter.setBrush(bg_color)
        painter.drawRoundedRect(rect, 6, 6)
        painter.end()

    def enterEvent(self, event):
        self.hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovered = False
        self.update()
        super().leaveEvent(event)

    def refresh_ui(self):
        self.update_texts()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            dialog = PostItEditDialog(
                self.data["content"],
                self.data["due_date"],
                self.data["color"],
                self,
            )

            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_data = dialog.get_data()

                self.data["content"] = new_data["content"]
                self.data["due_date"] = new_data["due_date"]
                self.data["color"] = new_data["color"]

                self.main_app.sync_all_views(
                    self.data["id"]
                )

            event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()

    def mouseMoveEvent(self, event):
        pass

    def mouseReleaseEvent(self, event):
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self.dragging
        ):
            self.dragging = False
            self.setCursor(Qt.CursorShape.OpenHandCursor)

            end_pos = event.globalPosition().toPoint()

            main_pos = self.main_app.mapFromGlobal(end_pos)

            if not self.main_app.rect().contains(main_pos):
                detached_window = DetachedPostItWindow(
                    self.data,
                    self.main_app,
                )

                detached_window.move(
                    end_pos.x() - 100,
                    end_pos.y() - 100,
                )
                detached_window.show()

                self.main_app.detached_windows.append(
                    detached_window
                )

                event.accept()
                return

            target = None

            for _, column in self.main_app.columns.items():
                local_pos = column.mapFromGlobal(end_pos)

                if column.rect().contains(local_pos):
                    target = column
                    break

            if target is None:
                event.accept()
                return

            if target is self.column_ref:
                self.column_ref.reorder_card(self, end_pos)
            else:
                self.column_ref.remove_card(self)
                target.add_card(self.data)

            self.main_app.save_board()

            event.accept()


class DetachedPostItWindow(QWidget):
    WINDOW_WIDTH = 225

    def __init__(self, data, main_app):
        super().__init__()

        self.data = data
        self.main_app = main_app

        self.init_ui()
        self.main_app.registered_detached.append(self)

    def init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground,
            True,
        )

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(4, 4, 11, 11)

        self.container = QWidget(self)

        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(10, 10, 15, 15)
        self.container_layout.setSpacing(6)

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_created = QLabel()
        self.lbl_created.setStyleSheet(
            "font-size: 11px;"
            "font-weight: bold;"
            "color: #555;"
            "background: transparent;"
            "border: none;"
        )

        self.lbl_due = QLabel()
        self.lbl_due.setStyleSheet(
            "font-size: 11px;"
            "font-weight: bold;"
            "color: #c53030;"
            "background: transparent;"
            "border: none;"
        )

        top_layout.addWidget(self.lbl_created)
        top_layout.addStretch()
        top_layout.addWidget(self.lbl_due)

        self.container_layout.addLayout(top_layout)

        self.lbl_content = JustifiedTextLabel()
        self.container_layout.addWidget(self.lbl_content)

        self.bottom_bar = QWidget()
        self.bottom_bar.setStyleSheet(
            "background: transparent; border: none;"
        )

        bottom_layout = QHBoxLayout(self.bottom_bar)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_completed = QLabel()
        self.lbl_completed.setStyleSheet(
            "font-size: 11px;"
            "font-weight: bold;"
            "color: #276749;"
            "background: transparent;"
            "border: none;"
        )

        bottom_layout.addWidget(self.lbl_completed)
        bottom_layout.addStretch()

        self.container_layout.addWidget(self.bottom_bar)
        self.main_layout.addWidget(self.container)

        self.btn_close = QPushButton("×", self)
        self.btn_close.setFixedSize(24, 24)
        self.btn_close.clicked.connect(self.close_window)

        self.btn_close.setStyleSheet(
            """
            QPushButton {
                background: transparent;
                color: #333;
                border: none;
                font-weight: bold;
                font-size: 16px;
                text-align: center;
            }

            QPushButton:hover {
                color: #e53e3e;
            }
            """
        )

        self.update_texts()

    def update_texts(self):
        self.lbl_created.setText(self.data["created_date"])
        self.lbl_due.setText(f"마감: {self.data['due_date']}")
        self.lbl_content.setText(self.data["content"])

        completed = self.data["completed_date"]
        self.lbl_completed.setText(f"완료: {completed}" if completed else "")
        self.bottom_bar.setVisible(bool(completed))

        self.fit_to_content()
        self.update()

    def fit_to_content(self):
        margins = self.main_layout.contentsMargins()
        inner_width = self.WINDOW_WIDTH - margins.left() - margins.right()

        if self.container.hasHeightForWidth():
            content_height = self.container.heightForWidth(inner_width)
        else:
            content_height = self.container.sizeHint().height()

        self.container.setFixedSize(inner_width, content_height)
        self.setFixedSize(
            self.WINDOW_WIDTH,
            content_height + margins.top() + margins.bottom(),
        )

        self.main_layout.activate()
        self.update_close_button_position()

    def update_close_button_position(self):
        fold = 30
        button_size = 24

        margins = self.main_layout.contentsMargins()

        container_width = self.container.width()
        container_height = self.container.height()

        center_x = container_width - (2.0 / 3.0) * fold
        center_y = container_height - (2.0 / 3.0) * fold

        button_x = margins.left() + int(
            center_x - button_size / 2
        )
        button_y = margins.top() + int(
            center_y - button_size / 2
        )

        self.btn_close.move(button_x, button_y)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_close_button_position()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        bg_color = QColor(self.data["color"])
        bg_color.setAlpha(postit_alpha())

        container_rect = self.container.geometry()

        x_offset = container_rect.x()
        y_offset = container_rect.y()
        width = container_rect.width()
        height = container_rect.height()
        fold = 30

        painter.save()
        painter.translate(x_offset, y_offset)

        for i in range(1, 6):
            alpha = max(0, 45 - i * 8)

            painter.setPen(QColor(0, 0, 0, alpha))
            painter.drawLine(
                width + i,
                6,
                width + i,
                height - fold,
            )
            painter.drawLine(
                6,
                height + i,
                width - fold,
                height + i,
            )
            painter.drawLine(
                width + i,
                height - fold + i,
                width - fold + i,
                height + i,
            )

        path = QPainterPath()
        path.moveTo(0, 6)
        path.quadTo(0, 0, 6, 0)
        path.lineTo(width - 6, 0)
        path.lineTo(width, 6)
        path.lineTo(width, height - fold)
        path.lineTo(width - fold, height)
        path.lineTo(6, height)
        path.quadTo(0, height, 0, height - 6)
        path.closeSubpath()

        painter.setPen(QColor(0, 0, 0, 40))
        painter.setBrush(bg_color)
        painter.drawPath(path)

        fold_path = QPainterPath()
        fold_path.moveTo(width, height - fold)
        fold_path.lineTo(width - fold, height)
        fold_path.lineTo(width - fold, height - fold)
        fold_path.closeSubpath()

        darker_color = bg_color.darker(118)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(darker_color)
        painter.drawPath(fold_path)

        painter.setPen(QColor(0, 0, 0, 35))
        painter.drawLine(
            int(width - fold),
            int(height - fold),
            int(width - fold),
            int(height),
        )
        painter.drawLine(
            int(width - fold),
            int(height - fold),
            int(width),
            int(height - fold),
        )

        painter.restore()

    def refresh_ui(self):
        self.update_texts()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            dialog = PostItEditDialog(
                self.data["content"],
                self.data["due_date"],
                self.data["color"],
                self,
            )

            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_data = dialog.get_data()

                self.data["content"] = new_data["content"]
                self.data["due_date"] = new_data["due_date"]
                self.data["color"] = new_data["color"]

                self.main_app.sync_all_views(
                    self.data["id"]
                )

            event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            current_pos = event.globalPosition().toPoint()
            delta = current_pos - self.old_pos

            self.move(
                self.x() + delta.x(),
                self.y() + delta.y(),
            )

            self.old_pos = current_pos

    def close_window(self):
        if self in self.main_app.registered_detached:
            self.main_app.registered_detached.remove(self)

        self.close()


class PostItDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("새 포스트잇 만들기")
        self.resize(320, 240)
        self.setStyleSheet(dialog_qss())

        layout = create_form_layout(self)

        self.content_edit = make_text_edit()
        self.content_edit.setPlaceholderText(
            "할 일을 입력하세요..."
        )
        layout.addRow(
            make_form_label("내 용", Qt.AlignmentFlag.AlignTop),
            self.content_edit,
        )

        self.due_edit = CustomDateEdit()

        self.due_edit.setDate(QDate.currentDate())
        self.due_edit.setDisplayFormat("yyyy-MM-dd")

        layout.addRow(make_form_label("마감일"), self.due_edit)

        self.color_combo = make_color_combo()

        for name in COLOR_PALETTE.keys():
            self.color_combo.addItem(name)

        layout.addRow(make_form_label("색 상"), self.color_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

    def get_data(self):
        color_name = self.color_combo.currentText()

        return {
            "id": str(datetime.now().timestamp()),
            "content": self.content_edit.toPlainText(),
            "color": COLOR_PALETTE[color_name],
            "status": "todo",
            "created_date": datetime.now().strftime(
                "%Y-%m-%d"
            ),
            "due_date": self.due_edit.date().toString(
                "yyyy-MM-dd"
            ),
            "completed_date": "",
        }


class KanbanColumn(QWidget):
    def __init__(self, status_key, title, main_app):
        super().__init__()

        self.status_key = status_key
        self.title = title
        self.main_app = main_app

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.content_widget = QWidget()
        self.content_widget.setStyleSheet(
            "background: transparent;"
        )

        self.cards_layout = QVBoxLayout(
            self.content_widget
        )
        self.cards_layout.setAlignment(
            Qt.AlignmentFlag.AlignTop
        )
        self.cards_layout.setSpacing(10)

        self.scroll.setWidget(self.content_widget)
        layout.addWidget(self.scroll)

    def apply_theme(self):
        t = theme()

        self.scroll.setStyleSheet(
            f"""
            QScrollArea {{
                background-color: {t['column_bg']};
                border: 2px dashed {t['column_border']};
                border-radius: 8px;
            }}

            QWidget#qt_scrollarea_viewport {{
                background-color: {t['column_bg']};
            }}
            """
        )

    def refresh_cards(self):
        for i in range(self.cards_layout.count()):
            item = self.cards_layout.itemAt(i)

            if item and item.widget():
                item.widget().update()

    def add_card(self, data, keep_dates=False):
        data["status"] = self.status_key

        if not keep_dates:
            if self.status_key == "done":
                data["completed_date"] = datetime.now().strftime(
                    "%Y-%m-%d"
                )
            else:
                data["completed_date"] = ""

        card = PostItWidget(data, self)
        self.cards_layout.addWidget(card)

    def remove_card(self, card_widget):
        self.cards_layout.removeWidget(card_widget)
        card_widget.deleteLater()

    def reorder_card(self, card, global_pos):
        drop_y = self.content_widget.mapFromGlobal(global_pos).y()

        new_index = 0

        for i in range(self.cards_layout.count()):
            item = self.cards_layout.itemAt(i)
            widget = item.widget() if item else None

            if widget is None or widget is card:
                continue

            if drop_y > widget.geometry().center().y():
                new_index += 1

        self.cards_layout.removeWidget(card)
        self.cards_layout.insertWidget(new_index, card)


# ---------------------------------------------------------------
# 월간 일정표
# ---------------------------------------------------------------

def is_completed(card):
    return card.get("status") == "done" or bool(card.get("completed_date"))


def collect_cards(main_app):
    cards = {}

    for column in main_app.columns.values():
        layout = column.cards_layout

        for i in range(layout.count()):
            item = layout.itemAt(i)
            widget = item.widget() if item else None

            if isinstance(widget, PostItWidget) and not is_completed(widget.data):
                cards[widget.data["id"]] = widget.data

    return list(cards.values())


class MonthGridWidget(QWidget):
    WEEKDAY_NAMES = ["일", "월", "화", "수", "목", "금", "토"]

    def __init__(self, main_app, parent=None):
        super().__init__(parent)

        self.main_app = main_app
        self.holidays = get_all_holidays()
        self.cards = []
        self.rows = []
        self.bar_hits = []
        self.drag = None
        self.preview = {}

        today = PyDate.today()
        self.year = today.year
        self.month = today.month

        self.setMouseTracking(True)

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self._relayout()

    def set_month(self, year, month):
        self.year = year
        self.month = month
        self._relayout()
        self.update()

    def shift_month(self, delta):
        total = self.year * 12 + (self.month - 1) + delta
        year, month_index = divmod(total, 12)
        self.set_month(year, month_index + 1)

    def set_cards(self, cards):
        self.cards = cards
        self._relayout()
        self.update()

    def _card_raw_range(self, card):
        try:
            created = PyDate.fromisoformat(card["created_date"])
            due = PyDate.fromisoformat(card["due_date"])
        except (KeyError, ValueError, TypeError):
            return None

        return min(created, due), max(created, due)

    def _range_of(self, card):
        if card.get("id") in self.preview:
            return self.preview[card["id"]]

        return self._card_raw_range(card)

    def _month_start(self):
        return PyDate(self.year, self.month, 1)

    def _grid_start(self):
        first = self._month_start()
        offset = (first.weekday() + 1) % 7
        return first - timedelta(days=offset)

    def _row_count(self):
        first = self._month_start()
        offset = (first.weekday() + 1) % 7
        days = calendar.monthrange(self.year, self.month)[1]
        return math.ceil((offset + days) / 7)

    def _relayout(self):
        grid_start = self._grid_start()
        n_rows = self._row_count()
        row_segs = [[] for _ in range(n_rows)]

        for card in self.cards:
            if is_completed(card):
                continue

            rng = self._range_of(card)

            if rng is None:
                continue

            start, end = rng

            for r in range(n_rows):
                row_start = grid_start + timedelta(days=7 * r)
                row_end = row_start + timedelta(days=6)

                if end < row_start or start > row_end:
                    continue

                seg_start = max(start, row_start)
                seg_end = min(end, row_end)

                row_segs[r].append({
                    "card": card,
                    "c0": (seg_start - row_start).days,
                    "c1": (seg_end - row_start).days,
                    "left": seg_start == start,
                    "right": seg_end == end,
                    "lane": 0,
                })

        self.rows = []

        for r, segs in enumerate(row_segs):
            segs.sort(key=lambda g: (g["c0"], -g["c1"]))
            lane_ends = []

            for seg in segs:
                lane = None

                for li, end_col in enumerate(lane_ends):
                    if end_col < seg["c0"]:
                        lane = li
                        break

                if lane is None:
                    lane_ends.append(seg["c1"])
                    lane = len(lane_ends) - 1
                else:
                    lane_ends[lane] = seg["c1"]

                seg["lane"] = lane

            base_h = MONTH_DAY_NUM_H + max(len(lane_ends), 1) * MONTH_LANE_H + 6

            self.rows.append({
                "base_h": base_h,
                "y": 0,
                "h": base_h,
                "row_start": grid_start + timedelta(days=7 * r),
                "segs": segs,
            })

        base_total = MONTH_WEEKDAY_H + sum(r["base_h"] for r in self.rows)
        self.setMinimumHeight(base_total)

        self._apply_stretch()

    def _apply_stretch(self):
        if not self.rows:
            return

        base_total = MONTH_WEEKDAY_H + sum(r["base_h"] for r in self.rows)
        extra = max(0, self.height() - base_total)

        share, remainder = divmod(extra, len(self.rows))
        y = MONTH_WEEKDAY_H

        for i, row in enumerate(self.rows):
            h = row["base_h"] + share + (1 if i < remainder else 0)
            row["y"] = y
            row["h"] = h
            y += h

        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_stretch()

    def paintEvent(self, event):
        t = theme()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        width = self.width()
        cw = width / 7.0
        today = PyDate.today()
        self.bar_hits = []

        painter.fillRect(
            QRectF(0, 0, width, MONTH_WEEKDAY_H),
            QColor(t["cal_header_bg"]),
        )

        font = QFont()
        font.setPixelSize(12)
        font.setBold(True)
        painter.setFont(font)

        for c, name in enumerate(self.WEEKDAY_NAMES):
            if c == 0:
                color = QColor(t["holiday"])
            elif c == 6:
                color = QColor(t["cal_sat"])
            else:
                color = QColor(t["text"])

            painter.setPen(color)
            painter.drawText(
                QRectF(c * cw, 0, cw, MONTH_WEEKDAY_H),
                Qt.AlignmentFlag.AlignCenter,
                name,
            )

        for row in self.rows:
            y = row["y"]
            h = row["h"]

            for c in range(7):
                day = row["row_start"] + timedelta(days=c)
                x = c * cw
                cell = QRectF(x, y, cw, h)
                in_month = day.month == self.month

                painter.fillRect(
                    cell,
                    QColor(t["cal_bg"]) if in_month else QColor(t["cal_other_bg"]),
                )
                painter.setPen(QPen(QColor(t["cal_line"]), 1))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(cell)

                key = (day.year, day.month, day.day)
                holiday_name = self.holidays.get(key) if in_month else None

                if not in_month:
                    num_color = QColor(t["cal_other_text"])
                elif c == 0 or holiday_name:
                    num_color = QColor(t["holiday"])
                elif c == 6:
                    num_color = QColor(t["cal_sat"])
                else:
                    num_color = QColor(t["cal_day_text"])

                num_rect = QRectF(x + 4, y + 3, 20, 16)

                if day == today:
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QColor(t["accent"]))
                    painter.drawRoundedRect(num_rect, 8, 8)
                    num_color = QColor("#ffffff")
                    painter.setBrush(Qt.BrushStyle.NoBrush)

                font.setPixelSize(12)
                font.setBold(True)
                painter.setFont(font)
                painter.setPen(num_color)
                painter.drawText(
                    num_rect,
                    Qt.AlignmentFlag.AlignCenter,
                    str(day.day),
                )

                if holiday_name:
                    small = QFont()
                    small.setPixelSize(10)
                    painter.setFont(small)
                    painter.setPen(QColor(t["holiday"]))

                    name_rect = QRectF(x + 26, y + 3, max(1.0, cw - 30), 16)
                    elided = painter.fontMetrics().elidedText(
                        holiday_name,
                        Qt.TextElideMode.ElideRight,
                        int(name_rect.width()),
                    )
                    painter.drawText(
                        name_rect,
                        Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                        elided,
                    )

        for row in self.rows:
            for seg in row["segs"]:
                self._draw_bar(painter, seg, row, cw)

        painter.end()

    def _draw_bar(self, painter, seg, row, cw):
        card = seg["card"]
        color = QColor(card["color"])

        x0 = seg["c0"] * cw + 3
        x1 = (seg["c1"] + 1) * cw - 3
        width = max(1.0, x1 - x0)

        top = row["y"] + MONTH_DAY_NUM_H + seg["lane"] * MONTH_LANE_H + 4
        bottom = top + MONTH_BAR_H
        mid = top + MONTH_BAR_H / 2

        tip = min(MONTH_BAR_TIP, width / 3)

        points = []

        if seg["left"]:
            points.append(QPointF(x0, mid))
            points.append(QPointF(x0 + tip, top))
        else:
            points.append(QPointF(x0, top))

        if seg["right"]:
            points.append(QPointF(x1 - tip, top))
            points.append(QPointF(x1, mid))
            points.append(QPointF(x1 - tip, bottom))
        else:
            points.append(QPointF(x1, top))
            points.append(QPointF(x1, bottom))

        if seg["left"]:
            points.append(QPointF(x0 + tip, bottom))
        else:
            points.append(QPointF(x0, bottom))

        painter.setPen(QPen(color.darker(160), 1))
        painter.setBrush(color)
        painter.drawPolygon(QPolygonF(points))

        inset_left = tip if seg["left"] else 4
        inset_right = tip if seg["right"] else 4
        text_rect = QRectF(
            x0 + inset_left,
            top,
            max(1.0, x1 - x0 - inset_left - inset_right),
            MONTH_BAR_H,
        )

        font = QFont()
        font.setPixelSize(11)
        font.setBold(True)
        painter.setFont(font)

        text = " ".join(card.get("content", "").split()) or "(내용 없음)"
        elided = painter.fontMetrics().elidedText(
            text,
            Qt.TextElideMode.ElideRight,
            max(1, int(text_rect.width()) - 4),
        )
        painter.setPen(QColor("#1a202c"))
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignCenter,
            elided,
        )

        hit_rect = QRectF(x0, top, width, MONTH_BAR_H)
        self.bar_hits.append((hit_rect, card, seg))

    def _hit_bar(self, pos):
        for rect, card, seg in reversed(self.bar_hits):
            if rect.contains(pos):
                return rect, card, seg

        return None

    def _drag_mode(self, rect, seg, pos):
        if seg["left"] and pos.x() - rect.left() <= MONTH_HANDLE_W:
            return "start"

        if seg["right"] and rect.right() - pos.x() <= MONTH_HANDLE_W:
            return "end"

        return "move"

    def _day_at(self, pos):
        if not self.rows:
            return None

        row = self.rows[-1]

        for r in self.rows:
            if pos.y() < r["y"] + r["h"]:
                row = r
                break

        cw = self.width() / 7.0
        col = max(0, min(6, int(pos.x() // cw)))

        return row["row_start"] + timedelta(days=col)

    def _tooltip_html(self, card, start, end):
        return (
            f"<div>{html_escape(card.get('content', ''))}<br>"
            f"생성 {start.isoformat()} → 마감 {end.isoformat()}</div>"
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            hit = self._hit_bar(pos)

            if hit is not None:
                rect, card, seg = hit
                press_day = self._day_at(pos)
                raw = self._card_raw_range(card)

                if press_day is not None and raw is not None:
                    self.drag = {
                        "card": card,
                        "mode": self._drag_mode(rect, seg, pos),
                        "press_day": press_day,
                        "orig": raw,
                    }

                event.accept()
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        pos = event.position()
        global_pos = event.globalPosition().toPoint()

        if self.drag is not None:
            self._update_drag(pos, global_pos)
            event.accept()
            return

        hit = self._hit_bar(pos)

        if hit is None:
            self.unsetCursor()
            QToolTip.hideText()
            super().mouseMoveEvent(event)
            return

        rect, card, seg = hit
        mode = self._drag_mode(rect, seg, pos)

        self.setCursor(
            Qt.CursorShape.SizeHorCursor
            if mode in ("start", "end")
            else Qt.CursorShape.SizeAllCursor
        )

        rng = self._range_of(card)

        if rng is not None:
            QToolTip.showText(
                global_pos,
                self._tooltip_html(card, rng[0], rng[1]),
                self,
            )

        super().mouseMoveEvent(event)

    def _update_drag(self, pos, global_pos):
        drag = self.drag
        now_day = self._day_at(pos)

        if now_day is None:
            return

        delta = timedelta(days=(now_day - drag["press_day"]).days)
        orig_start, orig_end = drag["orig"]

        if drag["mode"] == "move":
            new_start = orig_start + delta
            new_end = orig_end + delta
        elif drag["mode"] == "start":
            new_start = orig_start + delta
            new_end = orig_end
        else:
            new_start = orig_start
            new_end = orig_end + delta

        if new_start > new_end:
            new_start, new_end = new_end, new_start

        self.preview[drag["card"]["id"]] = (new_start, new_end)

        self._relayout()
        self.update()

        QToolTip.showText(
            global_pos,
            self._tooltip_html(drag["card"], new_start, new_end),
            self,
        )

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.drag is not None:
            drag = self.drag
            self.drag = None

            card = drag["card"]
            new_range = self.preview.pop(card["id"], None)

            QToolTip.hideText()

            if new_range is not None and new_range != drag["orig"]:
                new_start, new_end = new_range
                card["created_date"] = new_start.isoformat()
                card["due_date"] = new_end.isoformat()

                self.main_app.sync_all_views(card["id"])

            self._relayout()
            self.update()

            event.accept()
            return

        super().mouseReleaseEvent(event)

    def leaveEvent(self, event):
        if self.drag is None:
            self.unsetCursor()
            QToolTip.hideText()

        super().leaveEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag = None
            self.preview.clear()

            hit = self._hit_bar(event.position())

            if hit is not None:
                _, card, _ = hit

                dialog = PostItEditDialog(
                    card["content"],
                    card["due_date"],
                    card["color"],
                    self,
                )

                if dialog.exec() == QDialog.DialogCode.Accepted:
                    new_data = dialog.get_data()

                    card["content"] = new_data["content"]
                    card["due_date"] = new_data["due_date"]
                    card["color"] = new_data["color"]

                    self.main_app.sync_all_views(card["id"])

                    self._relayout()
                    self.update()

                event.accept()
                return

        super().mouseDoubleClickEvent(event)


class MonthCalendarDialog(QDialog):
    def __init__(self, main_app, parent=None):
        super().__init__(parent)

        self.main_app = main_app
        t = theme()

        self.setWindowTitle("월간 일정표")
        self.resize(980, 700)
        self.setStyleSheet(dialog_qss())

        layout = QVBoxLayout(self)

        nav = QHBoxLayout()

        btn_prev = QPushButton("◀")
        btn_next = QPushButton("▶")
        btn_today = QPushButton("오늘")

        nav_style = f"""
            QPushButton {{
                background-color: {t['button_bg']};
                color: {t['text']};
                border: 1px solid {t['button_border']};
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {t['button_hover']};
            }}
        """

        for btn in (btn_prev, btn_next, btn_today):
            btn.setStyleSheet(nav_style)
            btn.setFixedHeight(30)

        self.lbl_month = QLabel()
        self.lbl_month.setStyleSheet(
            f"font-size: 18px; font-weight: bold; color: {t['text']};"
            "padding: 0 12px;"
        )

        nav.addWidget(btn_prev)
        nav.addWidget(self.lbl_month)
        nav.addWidget(btn_next)
        nav.addSpacing(12)
        nav.addWidget(btn_today)
        nav.addStretch()

        layout.addLayout(nav)

        self.grid = MonthGridWidget(main_app)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.grid)
        scroll.setStyleSheet(
            f"""
            QScrollArea {{
                background: {t['cal_bg']};
                border: 1px solid {t['field_border']};
                border-radius: 6px;
            }}

            QWidget#qt_scrollarea_viewport {{
                background: {t['cal_bg']};
            }}
            """
        )

        layout.addWidget(scroll, 1)

        hint = QLabel(
            "막대: 생성일 → 마감일  |  "
            "드래그: 양 끝 화살촉은 생성일/마감일 조절, 가운데는 기간 전체 이동  |  "
            "더블클릭: 수정  |  완료된 카드는 표시되지 않습니다."
        )
        hint.setStyleSheet(f"color: {t['sub_text']}; font-size: 12px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        btn_prev.clicked.connect(lambda checked=False: self.move_month(-1))
        btn_next.clicked.connect(lambda checked=False: self.move_month(1))
        btn_today.clicked.connect(lambda checked=False: self.go_today())

        self.reload()

    def reload(self):
        self.grid.set_cards(collect_cards(self.main_app))
        self.lbl_month.setText(f"{self.grid.year}년 {self.grid.month}월")

    def move_month(self, delta):
        self.grid.shift_month(delta)
        self.reload()

    def go_today(self):
        today = PyDate.today()
        self.grid.set_month(today.year, today.month)
        self.reload()


MANUAL_SECTIONS = [
    ("포스트잇 만들기", [
        "상단의 <b>＋ 새 포스트잇 만들기</b> 버튼을 누르거나, 보드의 빈 곳을 더블클릭합니다.",
        "내용, 마감일, 색상을 입력하고 <b>OK</b>를 누르면 <b>할 일(To-Do)</b> 칸에 추가되고 파일에 저장됩니다.",
        "생성일은 오늘 날짜로 자동 저장되고, 마감일의 기본값도 오늘입니다.",
    ]),
    ("포스트잇 수정", [
        "카드를 더블클릭하면 수정 창이 열립니다.",
        "내용, 마감일, 색상을 바꿀 수 있고, 칸반 보드·분리 창·월간 일정표에 함께 반영됩니다.",
        "수정한 내용은 바로 파일에 저장됩니다.",
    ]),
    ("칸 이동과 순서 바꾸기", [
        "카드를 드래그해 다른 칸에 놓으면 그 칸으로 이동합니다.",
        "같은 칸 안에서 놓으면 놓은 위치에 따라 순서가 바뀝니다.",
        "드래그 중에는 카드가 마우스를 따라 움직이지 않고, 놓는 순간 위치가 정해집니다.",
        "칸과 순서는 파일에 저장되므로, 다음 실행 때도 같은 자리에 나타납니다.",
    ]),
    ("완료 처리", [
        "카드를 <b>완료(Done)</b> 칸에 놓으면 완료 날짜가 자동으로 기록되고, 카드 아래에 '완료: 날짜'가 표시됩니다.",
        "다른 칸으로 옮기면 완료 날짜는 지워집니다. 다시 완료 칸에 놓으면 그날 날짜로 새로 기록됩니다.",
        "완료 날짜도 파일에 저장되므로, 프로그램을 다시 켜도 그대로 남아 있습니다.",
    ]),
    ("완료된 포스트잇 삭제", [
        "완료 칸 카드의 오른쪽 아래 <b>빨간 ×</b>를 누르면 바로 삭제됩니다.",
        "확인 창이 없고, 삭제하면 파일에서도 바로 지워져 <b>되돌릴 수 없습니다</b>.",
        "같은 포스트잇의 분리 창이 열려 있으면 함께 닫힙니다.",
    ]),
    ("분리 창", [
        "카드를 보드 밖으로 드래그해 놓으면 독립 창으로 분리됩니다.",
        "보드의 카드는 그대로 남고, 같은 포스트잇의 창이 하나 더 열립니다.",
        "분리 창은 드래그해서 옮기고, 오른쪽 아래 <b>×</b>로 닫습니다. 닫아도 보드의 카드는 지워지지 않습니다.",
        "분리 창을 더블클릭하면 수정할 수 있습니다.",
        "분리 창의 위치와 열림 상태는 저장되지 않습니다. 프로그램을 끄면 분리 창은 함께 닫히고, 다시 켜도 자동으로 열리지 않습니다.",
    ]),
    ("마감일 달력", [
        "마감일 입력칸의 <b>▼</b>를 누르면 달력이 열리며, 항상 오늘이 속한 달부터 보입니다.",
        "빨간 날짜는 일요일, 공휴일(설날·부처님오신날·추석 등 음력 공휴일 포함), 대체공휴일입니다.",
    ]),
    ("월간 일정표", [
        "상단의 <b>달력 아이콘</b>을 누르면 열립니다.",
        "각 포스트잇은 생성일부터 마감일까지 막대로 표시됩니다. 완료된 카드는 표시되지 않습니다.",
        "<b>◀ ▶</b>로 달을 옮기고, <b>오늘</b> 버튼을 누르면 이번 달로 돌아갑니다.",
        "막대의 <b>양 끝</b>을 드래그하면 생성일 또는 마감일을, <b>가운데</b>를 드래그하면 기간 전체를 옮깁니다. 바뀌는 날짜는 툴팁으로 보이며, 놓는 순간 파일에 저장됩니다.",
        "시작일이 마감일보다 뒤로 가면 두 날짜가 자동으로 서로 바뀝니다.",
        "막대를 더블클릭하면 수정 창이 열립니다.",
        "일정표가 열려 있는 동안에는 보드를 조작할 수 없습니다. 닫은 뒤 작업하세요.",
    ]),
    ("설정 (톱니바퀴)", [
        "테마(일반 모드 / 다크 모드), 마스터보드 투명도, 포스트잇 투명도를 바꿀 수 있습니다. 바꾸면 바로 화면에 반영됩니다.",
        "<b>트레이에 넣기</b>를 체크하면 창을 최소화하거나 <b>×</b>로 닫을 때 프로그램이 작업표시줄이 아닌 <b>트레이(시계 옆 아이콘)</b>로 숨습니다.",
        "트레이 아이콘을 클릭하거나 더블클릭하면 창이 다시 나타납니다. 아이콘을 우클릭하면 <b>열기</b>와 <b>종료</b> 메뉴가 나옵니다.",
        "트레이에서 완전히 끄려면 우클릭 후 <b>종료</b>를 선택하세요. 체크를 끄면 트레이 아이콘이 사라집니다.",
        "<b>확인</b>을 누르면 설정이 저장되어 다음 실행 때도 유지되고, <b>취소</b>를 누르면 열기 전 값으로 돌아갑니다.",
    ]),
    ("데이터 저장 (자동 저장)", [
        "포스트잇은 만들기, 수정, 이동, 순서 변경, 삭제를 할 때마다 <b>자동으로 저장</b>됩니다. 저장 버튼은 없습니다.",
        "저장 위치: <b>프로그램이 있는 폴더</b>의 <code>postits.json</code> 파일입니다. 전체 경로는 <code>__DATA_FILE__</code>입니다.",
        "프로그램을 바탕화면이나 문서 폴더처럼 쓰기 권한이 있는 곳에 두세요. 'Program Files'처럼 권한이 제한된 폴더에 두면 저장에 실패합니다.",
        "컴퓨터를 껐다 켜도 포스트잇, 마감일, 완료 날짜, 칸 순서가 그대로 나타납니다.",
        "처음 실행하면 샘플 카드 1장이 들어 있습니다. 저장 파일이 생긴 뒤에는 샘플이 다시 나타나지 않습니다.",
        "<b>백업</b>: 프로그램을 끈 상태에서 위 파일을 다른 곳에 복사해 두면 백업이 됩니다. 복원하려면 프로그램을 끈 뒤 백업 파일을 원래 위치에 덮어씁니다.",
        "파일을 직접 고칠 때는 반드시 프로그램을 끈 상태에서 하세요. 실행 중에는 바꿀 때마다 파일이 새로 쓰여서 편집 내용이 사라질 수 있습니다.",
        "파일을 읽을 수 없으면(내용이 깨진 경우) 손상된 파일을 '.broken-날짜' 이름으로 옆에 보관하고 빈 보드로 시작합니다. 안내 창에 보관 위치가 나옵니다.",
        "저장에 실패하면(예: 폴더 쓰기 권한 문제) 경고 창이 뜹니다. 이때 바뀐 내용은 파일에 반영되지 않았으니, 문제를 해결한 뒤 다시 변경하세요.",
    ]),
    ("단축키", [
        "<b>F5</b>: 화면을 현재 데이터 기준으로 다시 그립니다.",
        "<b>Esc</b>: 대화상자를 취소하고 닫습니다.",
    ]),
    ("주의", [
        "같은 프로그램을 두 개 이상 동시에 실행하면 서로 저장 파일을 덮어쓸 수 있습니다. 한 번에 하나만 실행하세요.",
        "프로그램을 끌 때 분리 창도 함께 닫힙니다.",
        "트레이로 숨겨도 분리 창은 화면에 그대로 남아 있습니다. 트레이에서 <b>종료</b>를 해야 프로그램이 완전히 꺼집니다.",
    ]),
]


def build_manual_html(t):
    accent = t["accent"]
    parts = [
        f'<h2 style="color:{accent};">퍼스널 칸반 마스터 보드 사용 매뉴얼</h2>'
    ]

    for number, (title, items) in enumerate(MANUAL_SECTIONS, 1):
        parts.append(f'<h3 style="color:{accent};">{number}. {title}</h3>')
        parts.append("<ul>")
        parts.extend(f"<li>{item}</li>" for item in items)
        parts.append("</ul>")

    html = "".join(parts)
    return html.replace("__DATA_FILE__", html_escape(DATA_FILE))


class ManualDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        t = theme()

        self.setWindowTitle("사용 매뉴얼")
        self.resize(560, 640)
        self.setStyleSheet(dialog_qss())

        layout = QVBoxLayout(self)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(False)
        browser.setHtml(build_manual_html(t))
        browser.setStyleSheet(
            f"""
            QTextBrowser {{
                background-color: {t['field_bg']};
                color: {t['text']};
                border: 1px solid {t['field_border']};
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }}
            """
        )
        layout.addWidget(browser)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close
        )
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class CopyrightDialog(QDialog):
    """저작권 및 오픈소스 라이선스 정보 안내 창"""

    def __init__(self, parent=None):
        super().__init__(parent)

        t = theme()

        self.setWindowTitle("저작권 및 라이선스 정보")
        self.resize(440, 360)
        self.setStyleSheet(dialog_qss())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        info_text = (
            "<h3>📌 퍼스널 칸반 마스터 보드</h3>"
            "<p><b>Copyright © 2026 aisbm7575. All rights reserved.</b></p>"
            "<p>본 프로그램의 소스 코드는 <b>MIT 라이선스</b>를 따릅니다.<br>"
            "자유롭게 수정 및 배포가 가능합니다.</p>"
            "<hr>"
            "<p><b>⚙️ 외부 라이브러리 고지:</b></p>"
            "<p>이 소프트웨어는 GUI 구현을 위해 Riverbank Computing의 <b>PyQt6</b>를 사용하며, "
            "PyQt6는 <b>GNU General Public License (GPL)</b> 라이선스가 적용됩니다.</p>"
            "<hr>"
            "<p><b>🌐 GitHub 저장소:</b><br>"
            "<a href='https://github.com/aisbm7575/kanban_board'>"
            "https://github.com/aisbm7575/kanban_board</a></p>"
        )

        label = QLabel(info_text)
        label.setOpenExternalLinks(True)
        label.setWordWrap(True)
        label.setStyleSheet(
            f"font-size: 13px; color: {t['text']}; line-height: 140%;"
        )
        layout.addWidget(label)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons, 0, Qt.AlignmentFlag.AlignRight)


class SettingsDialog(QDialog):
    def __init__(self, main_app, parent=None):
        super().__init__(parent)

        self.main_app = main_app
        self.snapshot = dict(APP_STATE)

        self.setWindowTitle("설정")
        self.setFixedWidth(340)
        self.setStyleSheet(dialog_qss())

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # ----- 테마 -----
        theme_box = QGroupBox("테마")
        theme_layout = QHBoxLayout(theme_box)

        self.radio_light = QRadioButton(THEME_LABELS["light"])
        self.radio_dark = QRadioButton(THEME_LABELS["dark"])
        self.radio_light.setChecked(APP_STATE["theme"] == "light")
        self.radio_dark.setChecked(APP_STATE["theme"] == "dark")

        self.radio_light.clicked.connect(
            lambda checked=False: self.set_theme("light")
        )
        self.radio_dark.clicked.connect(
            lambda checked=False: self.set_theme("dark")
        )

        theme_layout.addWidget(self.radio_light)
        theme_layout.addWidget(self.radio_dark)
        layout.addWidget(theme_box)

        # ----- 투명도 -----
        opacity_box = QGroupBox("투명도")
        opacity_layout = QVBoxLayout(opacity_box)
        opacity_layout.setSpacing(10)

        self._make_opacity_row(
            opacity_layout,
            "마스터보드",
            APP_STATE["board_opacity"],
            "board_opacity",
        )
        self._make_opacity_row(
            opacity_layout,
            "포스트잇",
            APP_STATE["postit_opacity"],
            "postit_opacity",
        )

        layout.addWidget(opacity_box)

        # ----- 도움말 -----
        help_box = QGroupBox("도움말")
        help_layout = QVBoxLayout(help_box)
        help_layout.setSpacing(6)

        btn_manual = QPushButton("사용 매뉴얼 보기")
        btn_manual.clicked.connect(self.open_manual)
        help_layout.addWidget(btn_manual)

        btn_copyright = QPushButton("저작권 보기")
        btn_copyright.clicked.connect(self.open_copyright)
        help_layout.addWidget(btn_copyright)

        layout.addWidget(help_box)
        
        # ----- 트레이 -----
        tray_box = QGroupBox("트레이")
        tray_layout = QVBoxLayout(tray_box)

        self.chk_tray = QCheckBox("트레이에 넣기 (최소화·닫기를 누르면 트레이로 숨김)")
        self.chk_tray.setChecked(bool(APP_STATE.get("tray_enabled", False)))
        self.chk_tray.toggled.connect(self.set_tray)
        tray_layout.addWidget(self.chk_tray)

        layout.addWidget(tray_box)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _make_opacity_row(self, parent_layout, title, value, key):
        head = QHBoxLayout()
        head.addWidget(QLabel(title))
        head.addStretch()

        value_label = QLabel(f"{value}%")
        head.addWidget(value_label)
        parent_layout.addLayout(head)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(OPACITY_MIN, OPACITY_MAX)
        slider.setValue(value)

        def on_change(v, key=key, label=value_label):
            APP_STATE[key] = v
            label.setText(f"{v}%")
            self.main_app.apply_all()

        slider.valueChanged.connect(on_change)
        parent_layout.addWidget(slider)

    def set_theme(self, name):
        APP_STATE["theme"] = name
        self.setStyleSheet(dialog_qss())
        self.main_app.apply_all()

    def open_manual(self):
        ManualDialog(self).exec()

    def open_copyright(self):
        CopyrightDialog(self).exec()

    def accept(self):
        save_app_settings()
        super().accept()

    def set_tray(self, checked):
        APP_STATE["tray_enabled"] = checked
        self.main_app.apply_tray_setting()

    def reject(self):
        APP_STATE.update(self.snapshot)
        self.main_app.apply_all()
        self.main_app.apply_tray_setting()
        super().reject()


class PostItDialogPlaceholder:
    pass


class KanbanBoardApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("퍼스널 칸반 마스터 보드")
        self.resize(1300, 750)

        self.detached_windows = []
        self.registered_detached = []

        self.init_ui()

    def init_ui(self):
        self.central_host = QWidget()
        self.central_host.setObjectName("central")
        main_layout = QVBoxLayout(self.central_host)

        control_layout = QHBoxLayout()

        btn_add = QPushButton("＋ 새 포스트잇 만들기")
        btn_add.setStyleSheet(
            """
            QPushButton {
                background-color: #2b6cb0;
                color: white;
                font-weight: bold;
                font-size: 13px;
                padding: 8px 16px;
                border-radius: 6px;
                border: none;
            }

            QPushButton:hover {
                background-color: #2c5282;
            }
            """
        )
        btn_add.setFixedHeight(36)
        btn_add.clicked.connect(self.add_post_it)

        self.btn_calendar = QPushButton()
        self.btn_calendar.setIconSize(QSize(20, 20))
        self.btn_calendar.setFixedSize(40, 36)
        self.btn_calendar.setToolTip("월간 일정표 보기")
        self.btn_calendar.clicked.connect(self.open_month_calendar)

        self.btn_settings = QPushButton()
        self.btn_settings.setIconSize(QSize(20, 20))
        self.btn_settings.setFixedSize(40, 36)
        self.btn_settings.setToolTip("설정")
        self.btn_settings.clicked.connect(self.open_settings)

        control_layout.addWidget(btn_add)
        control_layout.addWidget(self.btn_calendar)
        control_layout.addWidget(self.btn_settings)
        control_layout.addStretch()

        main_layout.addLayout(control_layout)

        columns_layout = QHBoxLayout()

        titles = {
            "todo": "할 일 (To-Do)",
            "today": "오늘 할 일 (Today)",
            "inprogress": "진행 중 (In Progress)",
            "waiting": "대기 (Waiting)",
            "done": "완료 (Done)",
        }

        self.columns = {}
        self.header_labels = []

        for key, title in titles.items():
            self.columns[key] = KanbanColumn(
                key,
                title,
                self,
            )

        for key, column_widget in self.columns.items():
            column_box = QVBoxLayout()

            header_label = QLabel(titles[key])
            self.header_labels.append(header_label)

            column_box.addWidget(header_label)
            column_box.addWidget(column_widget)
            columns_layout.addLayout(column_box)

        main_layout.addLayout(columns_layout)

        self.setCentralWidget(self.central_host)

        self.load_initial_data()
        self.apply_all()

    def load_initial_data(self):
        cards, warning = load_board_data()

        if cards is None:
            self.load_sample_data()
            self.save_board()
        else:
            for data in cards:
                self.columns[data["status"]].add_card(data, keep_dates=True)

        if warning:
            QTimer.singleShot(
                0,
                lambda: QMessageBox.warning(self, "데이터 읽기 오류", warning),
            )

    def save_board(self):
        cards = []

        for column in self.columns.values():
            layout = column.cards_layout

            for i in range(layout.count()):
                item = layout.itemAt(i)
                widget = item.widget() if item else None

                if isinstance(widget, PostItWidget):
                    cards.append(widget.data)

        try:
            write_board_data(cards)
        except OSError as error:
            QMessageBox.warning(
                self,
                "저장 실패",
                "포스트잇 데이터를 파일에 저장하지 못했습니다.\n"
                f"{DATA_FILE}\n\n오류: {error}",
            )

    def apply_all(self):
        t = theme()

        self.central_host.setStyleSheet(
            f"QWidget#central {{ background-color: {t['window_bg']}; }}"
        )

        self.setWindowOpacity(APP_STATE["board_opacity"] / 100)

        for label in self.header_labels:
            label.setStyleSheet(
                "font-weight: bold;"
                "font-size: 14px;"
                "padding: 4px;"
                f"color: {t['text']};"
            )

        self.btn_calendar.setStyleSheet(icon_button_qss(t))
        self.btn_calendar.setIcon(make_calendar_icon(t["icon"]))

        self.btn_settings.setStyleSheet(icon_button_qss(t))
        self.btn_settings.setIcon(make_gear_icon(t["icon"]))

        for column in self.columns.values():
            column.apply_theme()
            column.refresh_cards()

        for window in self.registered_detached:
            window.update()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.add_post_it()
            event.accept()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_F5:
            for column in self.columns.values():
                for i in range(column.cards_layout.count()):
                    item = column.cards_layout.itemAt(i)

                    if item and item.widget():
                        item.widget().refresh_ui()

            for window in self.registered_detached:
                window.refresh_ui()

            event.accept()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        if APP_STATE.get("tray_enabled") and not getattr(self, "_quitting", False):
            event.ignore()
            self.hide()
            return

        for window in list(self.registered_detached):
            window.close()

        self.registered_detached.clear()
        self.save_board()
        super().closeEvent(event)

    def sync_all_views(self, target_id):
        for column in self.columns.values():
            for i in range(column.cards_layout.count()):
                item = column.cards_layout.itemAt(i)

                if item and item.widget():
                    card = item.widget()

                    if card.data["id"] == target_id:
                        card.refresh_ui()

        for window in self.registered_detached:
            if window.data["id"] == target_id:
                window.refresh_ui()

        self.save_board()

    def delete_card(self, card_widget):
        card_id = card_widget.data["id"]

        card_widget.column_ref.remove_card(card_widget)

        for window in list(self.registered_detached):
            if window.data["id"] == card_id:
                self.registered_detached.remove(window)

                if window in self.detached_windows:
                    self.detached_windows.remove(window)

                window.close()

        self.save_board()

    def add_post_it(self):
        dialog = PostItDialog(self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.columns["todo"].add_card(data)
            self.save_board()

    def open_month_calendar(self):
        dialog = MonthCalendarDialog(self, self)
        dialog.exec()

    def open_settings(self):
        dialog = SettingsDialog(self, self)
        dialog.exec()

    def apply_tray_setting(self):
        if APP_STATE.get("tray_enabled"):
            if not hasattr(self, "tray_icon"):
                self.tray_icon = QSystemTrayIcon(self.windowIcon(), self)
                self.tray_icon.setToolTip("퍼스널 칸반 마스터 보드")

                menu = QMenu(self)
                menu.addAction("열기", self.show_from_tray)
                menu.addSeparator()
                menu.addAction("종료", self.quit_from_tray)
                self.tray_icon.setContextMenu(menu)

                self.tray_icon.activated.connect(self.on_tray_activated)
            self.tray_icon.show()
        elif hasattr(self, "tray_icon"):
            self.tray_icon.hide()
            if not self.isVisible():
                self.show_from_tray()

    def show_from_tray(self):
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def on_tray_activated(self, reason):
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.show_from_tray()

    def quit_from_tray(self):
        self._quitting = True
        if hasattr(self, "tray_icon"):
            self.tray_icon.hide()
        self.close()

    def changeEvent(self, event):
        super().changeEvent(event)
        if (
            event.type() == QEvent.Type.WindowStateChange
            and APP_STATE.get("tray_enabled")
            and self.isMinimized()
        ):
            QTimer.singleShot(0, self.hide)

    def load_sample_data(self):
        sample = {
            "id": "1",
            "content": "퍼스널 칸반 마스터 보드 완성하기",
            "color": COLOR_PALETTE["노란색"],
            "status": "today",
            "created_date": "2026-10-07",
            "due_date": "2026-10-30",
            "completed_date": "",
        }

        self.columns["today"].add_card(sample)


if __name__ == "__main__":
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "PersonalKanban.MasterBoard"
        )

    app = QApplication(sys.argv)

    app_icon = find_app_icon()
    app.setWindowIcon(app_icon)

    load_app_settings()

    board = KanbanBoardApp()
    board.setWindowIcon(app_icon)
    board.show()
    board.apply_tray_setting()

    sys.exit(app.exec())