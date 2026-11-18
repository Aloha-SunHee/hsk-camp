"""Rebalance correct-answer positions of 4-option items so A/B/C/D appear evenly.
Options that are ordered numbers/times are left as they are."""
import re, random, sys, glob, collections
NUM = re.compile(r'[0-9一二三四五六七八九十百千万两半]')
for path in sorted(glob.glob('data/*.js')):
    src = open(path, encoding='utf8').read().split('\n')
    cand = []
    for i, line in enumerate(src):
        m = re.search(r"opts:\[(.*?)\], ans:'([A-D])'", line)
        if not m: continue
        opts = re.findall(r"'((?:[^'\\]|\\.)*)'", m.group(1))
        if len(opts) != 4: continue
        ordinal = all(NUM.search(o) and len(o) <= 6 for o in opts)
        cand.append((i, m, opts, ordinal))
    movable = [c for c in cand if not c[3]]
    rng = random.Random(path)
    fixed = collections.Counter(c[1].group(2) for c in cand if c[3])
    n = len(cand); per = n / 4
    targets = []
    for L in 'ABCD': targets += [L] * max(0, round(per - fixed[L]))
    while len(targets) < len(movable): targets.append(rng.choice('ABCD'))
    targets = targets[:len(movable)]; rng.shuffle(targets)
    # avoid 3 identical in a row
    for k in range(2, len(targets)):
        if targets[k] == targets[k-1] == targets[k-2]:
            for j in range(len(targets)):
                if targets[j] != targets[k] and (j < 2 or targets[j-1] != targets[k]):
                    targets[k], targets[j] = targets[j], targets[k]; break
    for (i, m, opts, _), T in zip(movable, targets):
        ci = 'ABCD'.index(m.group(2)); correct = opts[ci]
        others = [o for k, o in enumerate(opts) if k != ci]
        ti = 'ABCD'.index(T); new = others[:ti] + [correct] + others[ti:]
        rep = "opts:[" + ",".join("'" + o + "'" for o in new) + "], ans:'" + T + "'"
        src[i] = src[i][:m.start()] + rep + src[i][m.end():]
    open(path, 'w', encoding='utf8').write('\n'.join(src))
    print(path, 'moved', len(movable), 'kept', n - len(movable))
