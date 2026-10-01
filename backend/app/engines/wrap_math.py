import math

EPS = 1e-9
GRAINS = ("length", "width")     # 固定顺序：两向试算与破平（优先长向）依赖此顺序
TIEBREAK_RULE = "length_first"


def paper_area(length: float, width: float, height: float, overlap: float = 1.15) -> dict:
    L, W, H = float(length), float(width), float(height)
    if min(L, W, H) <= 0:
        raise ValueError("box dimensions must be positive")
    base = 2 * (L * W + L * H + W * H)
    need = base * float(overlap)
    return {"box_surface": round(base, 3), "overlap": float(overlap), "paper_m2": round(need, 3)}


def ribbon_estimate(length: float, width: float, height: float, wrap_style: str = "cross") -> dict:
    """Helper: approximate ribbon length in meters (not stored as primary metric)."""
    L, W, H = float(length), float(width), float(height)
    girth = 2 * (W + H)
    if wrap_style == "band":
        meters = girth + 0.3
    else:
        meters = girth * 2 + L + 0.5
    return {"wrap_style": wrap_style, "ribbon_m": round(meters, 2)}


def _is_positive_number(x) -> bool:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return False
    return math.isfinite(v) and v > 0


def eps_ceil(x: float, eps: float = EPS) -> int:
    """向上取整（容浮点）：整数邻域 ±eps 内视为整数。"""
    return int(math.ceil(float(x) - eps))


def unfold_rulers(length: float, width: float, height: float) -> dict:
    """十字展开派生的两把主尺/副尺（米）。

    长向展开（围带顺 L 绕一圈）：主尺 P_len = 2L+2H，副尺 S_len = W+2H
    宽向展开（围带顺 W 绕一圈）：主尺 P_wid = 2W+2H，副尺 S_wid = L+2H
    """
    L, W, H = float(length), float(width), float(height)
    if not all(math.isfinite(v) and v > 0 for v in (L, W, H)):
        raise ValueError("box dimensions must be positive finite numbers")
    return {
        "length": {"primary": round(2 * L + 2 * H, 6), "secondary": round(W + 2 * H, 6)},
        "width": {"primary": round(2 * W + 2 * H, 6), "secondary": round(L + 2 * H, 6)},
    }


def _grain_trial(grain: str, primary: float, secondary: float, roll_width: float) -> dict:
    """卷宽对齐主尺的单卷向试算：sheets=ceil(主尺/卷宽)；副尺只决定每条料长，不增张数。"""
    sheets = eps_ceil(primary / roll_width)
    return {
        "grain": grain,
        "aligned_ruler": round(primary, 6),
        "cross_ruler": round(secondary, 6),
        "roll_width": round(roll_width, 6),
        "sheets": sheets,
        "strip_length": round(secondary, 6),
        "roll_length_used": round(sheets * secondary, 6),
    }


def grain_estimate(length: float, width: float, height: float, roll_width: float, overlap: float = 1.15) -> dict:
    """两种卷向分别试算 sheets 并择优（sheets 小者；相等破平优先长向）。

    paper_m2 沿用面积法（表面积 × overlap），与卷向/卷宽无关。
    """
    L, W, H = float(length), float(width), float(height)
    if not all(math.isfinite(v) and v > 0 for v in (L, W, H)):
        raise ValueError("box dimensions must be positive finite numbers")
    if not _is_positive_number(roll_width):
        raise ValueError("roll_width must be a positive finite number")
    rw = float(roll_width)

    # sheets 用未 round 的原始浮点值配合 eps_ceil，避免展示舍入反噬张数
    raw = {
        "length": (2 * L + 2 * H, W + 2 * H),
        "width": (2 * W + 2 * H, L + 2 * H),
    }
    trials = [_grain_trial(g, raw[g][0], raw[g][1], rw) for g in GRAINS]

    chosen = min(trials, key=lambda t: t["sheets"])  # GRAINS 顺序保证相等时 length 胜出
    tie = trials[0]["sheets"] == trials[1]["sheets"]

    area = paper_area(L, W, H, overlap)
    return {
        "rulers": unfold_rulers(L, W, H),
        "trials": trials,
        "grain": chosen["grain"],
        "sheets": chosen["sheets"],
        "tie": tie,
        "tiebreak": TIEBREAK_RULE if tie else None,
        "box_surface": area["box_surface"],
        "overlap": area["overlap"],
        "paper_m2": area["paper_m2"],
    }
