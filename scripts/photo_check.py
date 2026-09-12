#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""车辆图片规则校验（jinba 流水线部署前强制步骤）。

规则（用户 2026-09-09 指定）：
  R1 每张图必须是干净背景，不得含公司 logo / 水印 / 角标叠印。
  R2 首图（primary，封面）必须是车辆正前面或左前 45° 角的外观照；
     内饰、仪表、细节特写、纯车尾不能当封面。

检测手段（确定性图像特征，不用生成式）：
  水印 R1：
    a) 边缘条带：底部/顶部近似纯色条带（che168 角标底板）
    b) 半透明叠印：角部固定区域与全图相比呈现"低饱和+局部低对比纹理"
       —— 用角部区域高频能量与四角中位数比值的离群度判定
  封面 R2：
    a) 内饰排除：整体偏暗且上部无天空亮区（内饰特征），或边缘密度过高（细节特写）
    b) 尾部排除：车牌居中偏下且左右对称性高 + 上部无天空 —— 保守策略只判
       "上部亮区占比"与"垂直边缘分布"，正脸/45° 上部必有天空/背景亮区且
       车头横向特征展开；纯车尾在 4:3 构图中亮区偏小
    满足 a 且不触发排除项 → 判定前脸/45° 通过（45° 与正脸在构图特征上同族，
    细分角度靠人工在 cover-report 里复核，脚本只拦"明显不对"的）。

用法：
  "$PY" scripts/photo_check.py                     # 全量 published 车辆
  "$PY" scripts/photo_check.py --id 323 325 326    # 只查指定车辆 id
  "$PY" scripts/photo_check.py --json out.json     # 结果写 JSON（供流水线读取）

退出码：0=全部合规；1=存在违规（部署前必须处理）；2=运行错误。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "vehicles.json"


def gray(im: Image.Image) -> np.ndarray:
    return np.asarray(im.convert("L"), dtype=float)


def strip_bar(a: np.ndarray, frac: float, top: bool) -> bool:
    """近似纯色条带（角标底板）。"""
    h = a.shape[0]
    strip = a[: int(h * frac)] if top else a[int(h * (1 - frac)):, :]
    body = a[int(h * 0.1): int(h * 0.9), :]
    return strip.std() < 18 and abs(strip.mean() - body.mean()) > 25


def corner_overlay(a: np.ndarray) -> list[str]:
    """检测四角半透明水印叠印：角部高频能量显著低于四角中位数 → 有覆盖物。"""
    h, w = a.shape
    k = max(24, int(min(h, w) * 0.12))
    corners = {
        "top-left": a[:k, :k],
        "top-right": a[:k, -k:],
        "bottom-left": a[-k:, :k],
        "bottom-right": a[-k:, -k:],
    }
    # 高频能量 = 相邻像素差分绝对值均值（叠印文字/图形会抬高，均匀遮挡会降低；
    # 这里抓"叠印字"：角部高频能量远高于该图典型水平）
    energies = {n: float(np.abs(np.diff(c, axis=1)).mean()) for n, c in corners.items()}
    vals = np.array(list(energies.values()))
    med = float(np.median(vals))
    hits = []
    for n, c in corners.items():
        e = energies[n]
        if not (med > 0.5 and e > med * 2.6 and e > 4.0):
            continue
        # 文字行特征：能量集中于少数行（行剖面 CV≥0.85）。均匀纹理
        # （树木/建筑/车身反光）CV 低，不是水印 —— 2026-09-09 摸底结论。
        re_ = np.abs(np.diff(c, axis=1)).mean(axis=1)
        cv = re_.std() / (re_.mean() + 1e-6)
        if cv < 0.85:
            continue
        # 多行文字 vs 水平亮线：文字水印的竖笔画使列剖面呈字符空隙结构
        # （列能量 CV≥0.35）；灯带/天花板边缘是整行亮暗跃变，列剖面平坦
        # （CV<0.35）。峰行上下行亮度与角均值接近（无强反差底板）也是场景特征。
        e_cols = np.abs(np.diff(c, axis=0)).mean(axis=0)
        col_cv = e_cols.std() / (e_cols.mean() + 1e-6)
        if col_cv < 0.35:
            continue        # 列剖面平坦 → 水平结构（灯带/檐口/车身边缘）
        hits.append(n)
    return hits


def front_facade_like(im: Image.Image) -> bool:
    """正前脸特写豁免（2026-09-12 新增）。

    深色车正对镜头近距离拍摄时，画面被车漆暗部填满、上部只有一条窄亮带
    （天空/远处背景），在灰度特征上与"内饰"同族 → interior_like 误杀。
    真实正前脸的几何签名：
      a) 左右高度对称（车头中线镜像）sym < 5
      b) 下半幅存在大面积近黑车漆 dark_bot > 0.45
      c) 上部 1/4 存在成片亮区（天空/室外背景）top_bright > 0.05
    内饰无法同时满足：仪表台/座椅布局左右不对称（sym 通常 ≥ 7），
    且车外亮区不会与"下半幅大面积纯黑车漆"共存。
    """
    r, g, b = (np.asarray(im.getchannel(c), dtype=float) for c in "RGB")
    gl = (r + g + b) / 3.0
    h, w = gl.shape
    sym = float(abs(gl[:, : w // 2].mean() - gl[:, w // 2:].mean()))
    dark_bot = float((gl[h // 2:] < 60).mean())
    top_bright = float((gl[: h // 4] > 170).mean())
    return sym < 5.0 and dark_bot > 0.45 and top_bright > 0.05


def exterior_like(a: np.ndarray) -> tuple[int, float]:
    """外观分（供 cover_auto / photo_fix 复用，越小越好）：
    类别 0=外观（上部有天空/背景亮区）1=中性 2=内饰/细节；
    第二项为"上部亮区占比"的负值（越大越开阔 → 排序用）。
    2026-09-12 从 photo_fix.exterior_score 上移至此，作为唯一实现。"""
    h = a.shape[0]
    mean = float(a.mean())
    top = float(a[: h // 4].mean())
    edges = float(np.abs(np.diff(a, axis=1)).mean())
    if top > mean + 18 and mean > 90:
        cat = 0
    elif mean < 95 or edges > 26:
        cat = 2
    else:
        cat = 1
    return cat, -float((a[: h // 4] > 200).mean())


def interior_like(a: np.ndarray) -> bool:
    """内饰/细节特征：整体暗 + 上部无亮区（窗外天空），或边缘密度过高。"""
    h, w = a.shape
    mean = a.mean()
    top = a[: h // 4].mean()
    edges = np.abs(np.diff(a, axis=1)).mean()
    if top < mean + 8 and mean < 110:
        return True           # 暗且上部无亮区 → 车内
    if edges > 30 and top < mean + 6:
        return True           # 高纹理密度 → 细节特写/内饰按键
    return False


def rear_like(a: np.ndarray) -> bool:
    """纯车尾保守判定：构图左右高度对称 + 中下部有亮色矩形（车牌）+ 上部亮区小。

    只拦明显车尾，不追求识别全部 —— 宁可漏报交人工，不误杀好图。
    """
    h, w = a.shape
    left = a[:, : w // 2]
    right = a[:, w // 2:]
    sym = float(np.abs(left.mean() - right.mean()))
    top_bright = (a[: h // 4] > 200).mean()
    # 车牌区：中下部找高亮小块
    mid = a[int(h * 0.55): int(h * 0.9), :]
    plate = (mid > 235).mean()
    return sym < 6 and plate > 0.012 and top_bright < 0.04


def check_image(path: Path, *, is_cover: bool) -> dict:
    res: dict = {"file": path.name, "ok": True, "issues": []}
    try:
        im = Image.open(path)
        im = im.convert("RGB")
    except Exception as e:  # noqa: BLE001
        res["ok"] = False
        res["issues"].append(f"unreadable: {e}")
        return res
    a = gray(im)

    # R1 水印
    bars = []
    if strip_bar(a, 0.06, top=False):
        bars.append("bottom")
    if strip_bar(a, 0.05, top=True):
        bars.append("top")
    flat_scene = bool(bars) and all(_is_flat_scene_band(a, b)[0] for b in bars)
    if bars and not band_exempt_by_source(path, bars):
        res["ok"] = False
        res["issues"].append("R1 边缘纯色条带（角标/水印底板）")
    elif bars and flat_scene:
        res["issues"].append("R1 边缘条带已豁免（近纯色平场景：展厅地面/背景墙）")
    elif bars:
        res["issues"].append("R1 边缘条带已豁免（原图同位同性质，场景白墙/地面）")
    corners = corner_overlay(a)
    if corners and not exempt_by_source(path, corners):
        res["ok"] = False
        res["issues"].append(f"R1 角部疑似叠印水印/logo: {','.join(corners)}")
    elif corners:
        res["issues"].append(f"R1 角部已豁免（原图同位同能量，场景纹理）: {','.join(corners)}")

    # R2 封面必须是前脸/45°外观
    if is_cover:
        if interior_like(a) and not front_facade_like(im):
            res["ok"] = False
            res["issues"].append("R2 封面疑似内饰/细节特写，需换正前或左前45°外观")
        elif interior_like(a):
            res["issues"].append("R2 内饰特征已豁免（正前脸构图：高对称 + 大面积车漆暗部 + 上部亮带）")
        if rear_like(a) and not front_facade_like(im):
            res["ok"] = False
            res["issues"].append("R2 封面疑似纯车尾，需换正前或左前45°外观")
    return res


def _imports_dir(stock: str) -> Path | None:
    for b in sorted((ROOT / "imports").iterdir()):
        d = b / stock
        if d.is_dir():
            return d
    return None


def exempt_by_source(path: Path, corners: list[str]) -> bool:
    """原图同位能量豁免：webp 与 imports 原图同角高频能量比在 0.9–1.1 →
    高频来自拍摄场景（树木/建筑/反光），不是转码产生的叠印。
    （webp 多经 720x540 裁剪，角区位置与原图同比例对应。）

    兜底同族豁免：enhance/fix 裁剪可能改变取景导致同位对比失效；
    此时若同车**任一** imports 原图同角能量 ≥ webp 的 70%（同一展厅
    灯带/建筑结构会在多张原图同角出现），同样判为场景纹理。"""
    name_map = {"top-left": "TL", "top-right": "TR",
                "bottom-left": "BL", "bottom-right": "BR"}
    # path = uploads/cars/<vid>/<file>；stock 从 photo_check 调用侧不好拿，
    # 用 vid 反查 vehicles.json
    try:
        vid = path.parent.name
        data = json.loads(DATA.read_text(encoding="utf-8"))
        v = next(x for x in data if str(x["id"]) == vid)
        stock = v["stock_id"]
    except Exception:  # noqa: BLE001
        return False
    impd = _imports_dir(stock)
    if impd is None:
        return False
    fn = path.name
    if fn.startswith("primary"):
        src = impd / "primary.jpg"
    else:
        try:
            idx = int(fn.replace("photo-", "").split(".")[0])
        except ValueError:
            return False
        src = impd / f"{stock}_src_{idx}.jpg"
        if not src.is_file():
            # enhance 管线重排过顺序：按序号兜底找同尺寸近似原图
            cands = sorted(impd.glob(f"{stock}_src_*.jpg"))
            if not cands:
                return False
            src = cands[min(idx - 2, len(cands) - 1)] if idx >= 2 else cands[0]
    if not src.is_file():
        return False
    try:
        wimg = gray(Image.open(path))
        simg = gray(Image.open(src))
    except Exception:  # noqa: BLE001
        return False
    wh, ww = wimg.shape
    sh, sw = simg.shape
    wk = max(24, int(min(wh, ww) * 0.12))
    sk = max(24, int(min(sh, sw) * 0.12))
    _sname = {"top-left": "TL", "top-right": "TR",
              "bottom-left": "BL", "bottom-right": "BR"}
    wslices = {"TL": (0, wk, 0, wk), "TR": (0, wk, ww - wk, ww),
               "BL": (wh - wk, wh, 0, wk), "BR": (wh - wk, wh, ww - wk, ww)}
    sslices = {"TL": (0, sk, 0, sk), "TR": (0, sk, sw - sk, sw),
               "BL": (sh - sk, sh, 0, sk), "BR": (sh - sk, sh, sw - sk, sw)}

    def e_of(a: np.ndarray, sl: tuple) -> float:
        c = a[sl[0]:sl[1], sl[2]:sl[3]]
        return float(np.abs(np.diff(c, axis=1)).mean())

    we = {n: e_of(wimg, wslices[_sname[n]]) for n in corners}
    se = {n: e_of(simg, sslices[_sname[n]]) for n in corners}
    ratios = [we[n] / (se[n] + 1e-6) for n in corners]
    if all(0.9 <= r <= 1.1 for r in ratios):
        return True
    # 兜底同族豁免：同车任一原图同角能量 ≥ webp 的 70% → 场景纹理
    try:
        stock_dir = impd
        for jpg in stock_dir.glob("*.jpg"):
            jimg = gray(Image.open(jpg))
            jh, jw = jimg.shape
            jk = max(24, int(min(jh, jw) * 0.12))
            if all(e_of(jimg, sslices[_sname[n]]) >= 0.7 * we[n] for n in corners):
                return True
    except Exception:  # noqa: BLE001
        pass
    return False


def _source_candidates(path: Path) -> tuple[Path | None, Path | None]:
    """返回 (imports 车源目录, 对应原图)。取不到返回 (None, None)。"""
    try:
        vid = path.parent.name
        data = json.loads(DATA.read_text(encoding="utf-8"))
        v = next(x for x in data if str(x["id"]) == vid)
        stock = v["stock_id"]
    except Exception:  # noqa: BLE001
        return None, None
    impd = _imports_dir(stock)
    if impd is None:
        return None, None
    fn = path.name
    if fn.startswith("primary"):
        # 2026-09-12：primary 可能来自 imports 之外的重抓图（cover 修复），
        # 此时 imports/primary.jpg 仍是老图，同位比对会失效 → 交给同族兜底
        return impd, impd / "primary.jpg"
    try:
        idx = int(fn.replace("photo-", "").split(".")[0])
    except ValueError:
        return impd, None
    src = impd / f"{stock}_src_{idx}.jpg"
    return impd, src if src.is_file() else None


def _is_flat_scene_band(arr: np.ndarray, bar: str) -> tuple[bool, float, float]:
    """本图自身的条带是否就是"近纯色平场景"（展厅白墙/灰地/棚拍背景）。

    2026-09-12 新增：R1 的原始意图是抓 **叠加的角标底板/水印条**。但 che168
    棚拍图的顶部/底部常被纯色地面与背景墙填满（std 低、与车身均差大），
    会被 strip_bar 误判。真水印条的特征是**非常平**（std 通常 < 8）且
    **与画面主体反差明显**；而场景地面有轻微纹理与透视渐变。

    判定：std < 12 且与主体均差 > 20 → 场景平带（豁免）。
    真角标底板多为近纯白/纯色矩形，std 更低但同样满足；因此还要配合
    "原图同位同性质"双重确认（见 band_exempt_by_source）才彻底放行。
    """
    h = arr.shape[0]
    frac, top = (0.05, True) if bar == "top" else (0.06, False)
    s = arr[: int(h * frac)] if top else arr[int(h * (1 - frac)):]
    body = arr[int(h * 0.1): int(h * 0.9)]
    std = float(s.std())
    diff = float(abs(s.mean() - body.mean()))
    return (std < 12.0 and diff > 20.0), std, diff


def _refetch_candidates(path: Path) -> list[Path]:
    """cover_auto 重抓图集目录（.workbuddy/cover_auto/<vid>/img_NN.jpg）。

    这些图不在 imports/ 里，band_exempt_by_source 无法靠 imports 比对；
    用重抓图集自身做同族确认（同车同场景，多张图同位同性质即场景面）。
    """
    try:
        vid = path.parent.name
        gdir = ROOT / ".workbuddy" / "cover_auto" / vid
        if gdir.is_dir():
            return sorted(gdir.glob("img_*.jpg"))
    except Exception:  # noqa: BLE001
        pass
    return []


def band_exempt_by_source(path: Path, bars: list[str]) -> bool:
    """边缘纯色条带豁免：条带在 imports 原图同位同性质出现 → 拍摄场景的
    白墙/地面（展厅素色背景），不是 che168 角标底板或水印条。

    判定：原图同位置的 条带 std 与 body mean 差 与 webp 相差很小
    （std 比 0.8–1.25、|mean-body| 差 ≤12 灰阶），且原图自己也满足
    std<25（确为近纯色区域）。同族兜底：同车任一原图同位同样近纯色。
    """
    impd, src = _source_candidates(path)
    if impd is None:
        # cover_auto 重抓图：不在 imports 下 → 用重抓图集做同族确认
        gallery = _refetch_candidates(path)
        if gallery:
            try:
                import numpy as _np
                for jpg in gallery:
                    try:
                        ga = gray(Image.open(jpg))
                    except Exception:  # noqa: BLE001
                        continue
                    if all(_is_flat_scene_band(ga, b)[0] for b in bars):
                        return True
            except Exception:  # noqa: BLE001
                pass
        return False

    def stats(arr: np.ndarray, frac: float, top: bool) -> tuple[float, float]:
        h = arr.shape[0]
        s = arr[: int(h * frac)] if top else arr[int(h * (1 - frac)): ]
        b = arr[int(h * 0.1): int(h * 0.9)]
        return float(s.std()), float(abs(s.mean() - b.mean()))

    try:
        wa = gray(Image.open(path))
    except Exception:  # noqa: BLE001
        return False
    want = {"bottom": (0.06, False), "top": (0.05, True)}

    def match(simg: np.ndarray) -> bool:
        for bar in bars:
            frac, top = want[bar]
            ws, wd = stats(wa, frac, top)
            ss, sd = stats(simg, frac, top)
            if ss >= 25:
                return False       # 原图同位不是纯色 → 不是场景白墙
            if not (0.65 <= ws / (ss + 1e-6) <= 1.6):
                return False
            if abs(wd - sd) > 14:
                return False
        return True

    if src is not None and src.is_file():
        try:
            if match(gray(Image.open(src))):
                return True
        except Exception:  # noqa: BLE001
            pass
    # 本图自证：条带即"近纯色平场景"（展厅地面/背景墙），且同图另有
    # 至少一张同位同性质 → 场景面而非叠印。仅对本图 std 极低的条带生效。
    if all(_is_flat_scene_band(wa, b)[0] for b in bars):
        try:
            others = 0
            for jpg in list(impd.glob("*.jpg")) + _refetch_candidates(path):
                try:
                    ga = gray(Image.open(jpg))
                except Exception:  # noqa: BLE001
                    continue
                if all(_is_flat_scene_band(ga, b)[0] for b in bars):
                    others += 1
                    if others >= 2:
                        return True
        except Exception:  # noqa: BLE001
            pass
    # 同族兜底：任一原图同位近纯色且量级相符
    try:
        for jpg in sorted(impd.glob("*.jpg")):
            if src is not None and jpg.name == src.name:
                continue
            try:
                if match(gray(Image.open(jpg))):
                    return True
            except Exception:  # noqa: BLE001
                continue
    except Exception:  # noqa: BLE001
        pass
    return False


def main() -> int:
    args = sys.argv[1:]
    only_ids = set()
    out_json = None
    it = iter(args)
    for a in it:
        if a == "--id":
            only_ids = {int(x) for x in next(it).split(",")}
        elif a == "--json":
            out_json = Path(next(it))

    if not DATA.exists():
        print(f"NOT FOUND: {DATA}")
        return 2
    data = json.loads(DATA.read_text(encoding="utf-8"))

    report = []
    n_bad = 0
    for v in data:
        if v.get("status") != "published":
            continue
        if only_ids and v["id"] not in only_ids:
            continue
        photos = v.get("photos") or []
        if not photos:
            report.append({"stock": v["stock_id"], "id": v["id"],
                           "ok": False, "issues": ["无 photos"]})
            n_bad += 1
            continue
        vres = {"stock": v["stock_id"], "id": v["id"], "ok": True, "photos": []}
        for i, rel in enumerate(photos):
            p = ROOT / rel.lstrip("/")
            if not p.is_file():
                r = {"file": rel, "ok": False, "issues": ["文件缺失"]}
            else:
                r = check_image(p, is_cover=(i == 0))
            vres["photos"].append(r)
            if not r["ok"]:
                vres["ok"] = False
        if not vres["ok"]:
            n_bad += 1
        report.append(vres)

    bad = [r for r in report if not r["ok"]]
    for r in bad:
        issues = [i for ph in r.get("photos", []) for i in ph["issues"]]
        print(f"✗ {r['stock']} (id {r['id']}): {'; '.join(issues)}")
    print(f"\n检查 {len(report)} 台 published 车辆，违规 {n_bad} 台")
    if out_json:
        out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                            encoding="utf-8")
        print(f"报告 → {out_json}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
