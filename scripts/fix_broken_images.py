"""修复 uploads 中损坏(截断)的车辆图片。

数据源：imports/2026-08-che168/JB-XXXX/  目录（每车最多 10 张源图，完整未裁剪）
映射：imports/vehicles.csv 的 stock_id(JB-XXXX) -> data/vehicles.json 的 id
匹配键：优先 (brand, model, year)，退化为 title

用法：
  python scripts/fix_broken_images.py map      # 建立并打印映射
  python scripts/fix_broken_images.py scan     # 列出损坏文件及可修复情况
  python scripts/fix_broken_images.py fix      # 执行修复（从 imports 源图重建）
"""
import csv
import io
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
IMPORTS = ROOT / 'imports' / '2026-08-che168'
UPLOADS = ROOT / 'uploads' / 'cars'
VEHICLES = ROOT / 'data' / 'vehicles.json'
BACKUP = ROOT / '.workbuddy' / 'broken_backup'


def norm(s):
    return ''.join(c for c in str(s or '') if c.isalnum()).lower()


def load_vehicles():
    d = json.load(open(VEHICLES, encoding='utf-8'))
    return d if isinstance(d, list) else d.get('vehicles', d)


def load_broken():
    """返回 {car_id: [损坏文件名]}"""
    out = {}
    for f in sorted(UPLOADS.rglob('*.jpg')):
        try:
            from PIL import Image
            im = Image.open(f)
            im.load()
            continue
        except Exception:
            pass
        try:
            cid = int(f.relative_to(UPLOADS).parts[0])
        except Exception:
            continue
        out.setdefault(cid, []).append(f.name)
    return out


def build_map():
    """imports stock_id -> vehicles.json id"""
    vehicles = load_vehicles()
    by_bmy, by_title = {}, {}
    for x in vehicles:
        by_bmy.setdefault((norm(x.get('brand')), norm(x.get('model')), str(x.get('year'))), []).append(x['id'])
        by_title.setdefault(norm(x.get('title')), []).append(x['id'])

    rows = list(csv.DictReader(open(IMPORTS / 'vehicles.csv', encoding='utf-8-sig')))
    mapping, ambiguous = {}, []
    for r in rows:
        cand = by_bmy.get((norm(r['brand']), norm(r['model']), str(r['year'])))
        if not cand or len(cand) > 1:
            cand = by_title.get(norm(r['title']), [])
        if len(cand) == 1:
            mapping[r['stock_id']] = cand[0]
        else:
            ambiguous.append((r['stock_id'], len(cand)))
    return mapping, ambiguous


def source_files(stock_id):
    d = IMPORTS / stock_id
    if not d.exists():
        return []
    return sorted(d.glob('*.jpg'))


def cmd_map():
    mapping, amb = build_map()
    print(f'可建立映射: {len(mapping)} 台')
    if amb:
        print(f'无法唯一匹配: {len(amb)} 台 -> {amb[:8]}')
    return mapping


def cmd_scan():
    broken = load_broken()
    mapping, _ = build_map()
    rev = {v: k for k, v in mapping.items()}
    total = sum(len(v) for v in broken.values())
    fixable = 0
    print(f'损坏文件 {total} 个，涉及 {len(broken)} 台车')
    print(f'{"车辆":>6} {"损坏数":>6} {"imports源":>8}  状态')
    for cid in sorted(broken):
        stock = rev.get(cid)
        srcs = source_files(stock) if stock else []
        ok = bool(srcs)
        fixable += len(broken[cid]) if ok else 0
        print(f'{cid:>6} {len(broken[cid]):>6} {len(srcs):>8}  {"可修复" if ok else "无源图"}')
    print(f'\n可修复 {fixable} / {total} 张')


def cmd_fix():
    from PIL import Image
    broken = load_broken()
    mapping, _ = build_map()
    rev = {v: k for k, v in mapping.items()}
    BACKUP.mkdir(parents=True, exist_ok=True)

    fixed = skipped = failed = 0
    log = []
    for cid in sorted(broken):
        stock = rev.get(cid)
        srcs = source_files(stock) if stock else []
        if not srcs:
            skipped += len(broken[cid])
            log.append((cid, '-', 'no_source', 0, 0))
            continue
        car_dir = UPLOADS / str(cid)
        for idx, name in enumerate(sorted(broken[cid])):
            if idx >= len(srcs):
                skipped += 1
                log.append((cid, name, 'src_short', 0, 0))
                continue
            dst = car_dir / name
            src = srcs[idx]
            try:
                orig = dst.stat().st_size
                shutil.copy2(dst, BACKUP / f'{cid}_{name}')
                im = Image.open(src).convert('RGB')
                im.save(dst, 'JPEG', quality=82, optimize=True, progressive=True)
                new = dst.stat().st_size
                im2 = Image.open(dst)
                im2.load()
                fixed += 1
                log.append((cid, name, 'ok', orig, new))
            except Exception as e:
                failed += 1
                log.append((cid, name, f'ERR {type(e).__name__}', 0, 0))

    print(f'修复成功 {fixed} 张，跳过 {skipped} 张，失败 {failed} 张')
    print(f'备份位置: {BACKUP}')
    ok = [l for l in log if l[2] == 'ok']
    if ok:
        so = sum(l[3] for l in ok)
        sn = sum(l[4] for l in ok)
        print(f'体积: {so/1048576:.1f} MB -> {sn/1048576:.1f} MB（省 {(1-sn/so)*100:.0f}%）')
    for l in log:
        if l[2] not in ('ok',):
            print(f'  未处理: car{l[0]}/{l[1]} -> {l[2]}')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'scan'
    {'map': cmd_map, 'scan': cmd_scan, 'fix': cmd_fix}[cmd]()
