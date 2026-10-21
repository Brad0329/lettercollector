"""Calligrapher name mapping and aliases between Chinese and Korean."""

# ZDIC specific aliases where pen names or alternate titles appear
ZDIC_ALIASES: dict[str, str] = {
    "赵子昂": "赵孟頫",  # Zhao Mengfu is registered with his courtesy name Zi'ang
}

# Common calligrapher Chinese (Simplified/Traditional) to Korean name mapping
CALLIGRAPHER_KO_MAP: dict[str, str] = {
    "王羲之": "왕희지",
    "王献之": "왕헌지",
    "王獻之": "왕헌지",
    "孙过庭": "손과정",
    "孫過庭": "손과정",
    "怀素": "회소",
    "懷素": "회소",
    "赵孟頫": "조맹부",
    "趙孟頫": "조맹부",
    "黄庭坚": "황정견",
    "黃庭堅": "황정견",
    "米芾": "미불",
    "颜真卿": "안진경",
    "顏真卿": "안진경",
    "董其昌": "동기창",
    "祝允明": "축윤명",
    "张旭": "장욱",
    "張旭": "장욱",
    "智永": "지영",
    "文徵明": "문징명",
    "文征明": "문징명",
    "柳公权": "유공권",
    "柳公權": "유공권",
    "欧阳询": "구양순",
    "歐陽詢": "구양순",
    "苏轼": "소식",
    "蘇軾": "소식",
    "鲜于枢": "선우추",
    "鮮于樞": "선우추",
    "徐渭": "서위",
    "八大山人": "팔대산인",
    "高闲": "고한",
    "高閑": "고한",
    "索靖": "삭정",
    "皇象": "황상",
    "张芝": "장지",
    "張芝": "장지",
    "褚遂良": "저수량",
    "王铎": "왕탁",
    "王鐸": "왕탁",
    "徐伯清": "서백청",
    "潘受": "반수",
    "韩道亨": "한도형",
    "韓道亨": "한도형",
    "邓文原": "등문원",
    "鄧文原": "등문원",
    "赵佶": "조길",
    "趙佶": "조길",
    "草书韵会": "초서운회",
    "草書韻會": "초서운회",
    "空海": "공해",
    "王宠": "왕총",
    "王寵": "왕총",
    "王守仁": "왕수인",
    "沈粲": "심찬",
    "毛泽东": "모택동",
    "毛澤東": "모택동",
    "杨维祯": "양유정",
    "楊維楨": "양유정",
    "敬世江": "경세강",
    "归庄": "귀장",
    "歸莊": "귀장",
    "康里子山": "강리자산",
    "倪元璐": "예원로",
    "俞和": "유화",
}


def normalize_calligrapher_name(zh_name: str) -> str:
    """Normalize alias in Chinese."""
    clean = zh_name.strip()
    return ZDIC_ALIASES.get(clean, clean)


def get_calligrapher_ko(zh_name: str) -> str:
    """Get Korean pronunciation/name for a given calligrapher, falling back to original."""
    norm = normalize_calligrapher_name(zh_name)
    return CALLIGRAPHER_KO_MAP.get(norm, norm)
