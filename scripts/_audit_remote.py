"""统计线上 main 树中的垃圾文件（n / _preview/ / .codebuddy/）"""
import sys
sys.path.insert(0, 'scripts')
import push_api as P


def walk(sha, prefix=''):
    t = P.api(f'/git/trees/{sha}')
    for e in t.get('tree', []):
        p = prefix + e['path']
        if e['type'] == 'tree':
            yield from walk(e['sha'], p + '/')
        else:
            yield p


base = P.api('/git/refs/heads/main')['object']['sha']
tree_sha = P.api(f'/git/commits/{base}')['tree']['sha']
paths = list(walk(tree_sha))
bad = [p for p in paths if p == 'n' or p.startswith('_preview/') or p.startswith('.codebuddy/')]
print('线上总文件数:', len(paths))
print('垃圾文件数:', len(bad))
for b in bad[:10]:
    print(' ', b)
if len(bad) > 10:
    print(f'  ... 其余 {len(bad)-10} 条略')
