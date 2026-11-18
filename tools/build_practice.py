"""Build practice (full-length) mock exams from the GPT / Gemini PDF text dumps.
Usage: python3 tools/build_practice.py SRC_DIR  → writes data/practice/*.js
Answer-key corrections found during review are applied in FIX_* blocks below."""
import json, re, sys, random, os
SRC = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/src2'
OUT = os.path.join(os.path.dirname(__file__), '..', 'data', 'practice')
L = 'ABCDEF'

def rd(n): return open(os.path.join(SRC, n), encoding='utf8').read().replace(chr(0x200b), '').replace(chr(0xa0), ' ').replace(chr(12), chr(10))

def flat(s):
    """join wrapped lines; drop spaces between CJK chars"""
    s = re.sub(r'\s*\n\s*', '', s.strip())
    s = re.sub(r'(?<=[　-鿿，。！？；：、“”）（])\s+(?=[　-鿿，。！？；：、“”（）])', '', s)
    return s.strip()

def seq_blocks(text, first, last, pat=r'(?:^|\n|\s)\s*{n}\s*[.．]\s*'):
    """split text into numbered blocks first..last, accepting numbers only in sequence"""
    out, pos = {}, 0
    starts = []
    for n in range(first, last + 2):
        if n == last + 1: break
        m = re.compile(pat.format(n=n)).search(text, pos)
        if not m: raise ValueError(f'block {n} not found')
        starts.append((n, m.start(), m.end())); pos = m.end()
    for i, (n, s, e) in enumerate(starts):
        end = starts[i + 1][1] if i + 1 < len(starts) else len(text)
        out[n] = text[e:end].strip()
    return out

def opts(s, k=None):
    s = re.split(r'第[一二三四]部分|[一二三]、\s*[听阅书]', s)[0]
    s = flat(s) if '\n' in s else s.strip()
    parts = re.split(r'(?:^|\s+|(?<=[一-鿿）]))([A-F])\s*(?=\S)', ' ' + s)
    o = {}
    for i in range(1, len(parts) - 1, 2):
        o[parts[i]] = parts[i + 1].strip()
    res = [o[x] for x in L if x in o]
    if k and len(res) != k: raise ValueError(f'opts {len(res)}!={k}: {s}')
    return res

def script_lines(block):
    """keep 男/女/问 lines; merge wrapped continuation lines"""
    block = re.sub(r'(?:\s+|(?<=[。？！…”]))(?=(男|女|问)[：:])', '\n', block.strip())
    out = []
    for ln in block.split('\n'):
        ln = ln.strip()
        if not ln: continue
        if re.match(r'^(男|女|问)[：:]', ln) or not out: out.append(ln.replace(':', '：', 1) if re.match(r'^(男|女|问):', ln) else ln)
        else: out[-1] += ln
    return '\n'.join(flat(x) for x in out)

def keys(text):
    return {int(n): v for n, v in re.findall(r'(\d+)\s*[.．]\s*([A-F√×]{1,5})(?![一-鿿])', text)}

def shuffle_order(it, rng):
    perm = [0, 1, 2]
    while perm == [0, 1, 2] or ''.join(L[perm.index(L.index(c))] for c in it['ans']) == 'ABC':
        rng.shuffle(perm)
    segs = it['segs']; new = [None] * 3
    for old_i, new_i in enumerate(perm): new[new_i] = segs[old_i]
    it['segs'] = new
    it['ans'] = ''.join(L[perm[L.index(c)]] for c in it['ans'])

NUM = re.compile(r'[0-9一二三四五六七八九十百千万两半]')
def rebalance(set_, rng):
    items = []
    for sec in set_['sections']:
        for p in sec['parts']:
            if p['type'] in ('lmc', 'lgroup', 'rmc', 'rgroup', 'cloze', 'error', 'multi'):
                for it in (p.get('items') or [i for g in p['groups'] for i in g['items']]):
                    if len(it.get('opts', [])) == 4: items.append(it)
    fixed = [it for it in items if all(NUM.search(o) and len(o) <= 6 for o in it['opts'])]
    movable = [it for it in items if it not in fixed]
    per = len(items) / 4
    targets = []
    for x in L[:4]: targets += [x] * max(0, round(per - sum(1 for it in fixed if it['ans'] == x)))
    while len(targets) < len(movable): targets.append(rng.choice(L[:4]))
    targets = targets[:len(movable)]; rng.shuffle(targets)
    for it, t in zip(movable, targets):
        ci = L.index(it['ans']); c = it['opts'][ci]; others = it['opts'][:ci] + it['opts'][ci + 1:]
        ti = L.index(t); it['opts'] = others[:ti] + [c] + others[ti:]; it['ans'] = t

def untangle_tf(set_, rng):
    for sec in set_['sections']:
        for p in sec['parts']:
            if p['type'] != 'tf': continue
            its = p['items']; pat = ''.join(i['ans'] for i in its)
            if re.search(r'(√×){3}|(×√){3}', pat):
                while True:
                    rng.shuffle(its); pat = ''.join(i['ans'] for i in its)
                    if not re.search(r'(√×){3}|(×√){3}|√{4}|×{4}', pat): break
                for k, it in enumerate(its): it['id'] = f'L{k + 1}'

def finish(set_):
    rng = random.Random(set_['id'])
    untangle_tf(set_, rng)
    rebalance(set_, rng)
    for sec in set_['sections']:
        for p in sec['parts']:
            for it in (p.get('items') or []):
                if p['type'] == 'order': shuffle_order(it, rng)
    lv = set_['level']
    set_.pop('kind', None)
    set_['corner'] = 'exam'
    set_['minutes'] = {4: {'L': 30, 'R': 35, 'W': 25}, 5: {'L': 30, 'R': 40, 'W': 40}, 6: {'L': 35, 'R': 45, 'W': 45}}[lv]
    set_['label'] = set_['label'] + '회'
    set_['title'] = f"HSK {lv}급 실전 모의고사 {set_['label']}"
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, set_['id'] + '.js'), 'w', encoding='utf8') as f:
        f.write('window.HSK_SETS = window.HSK_SETS || [];\nHSK_SETS.push(')
        f.write(json.dumps(set_, ensure_ascii=False, indent=0))
        f.write(');\n')
    n = sum(len(g['items']) for s in set_['sections'] for p in s['parts'] for g in (p.get('groups') or [])) + \
        sum(len(p.get('items') or []) for s in set_['sections'] for p in s['parts'])
    print(set_['id'], 'items', n)

def mc(id_, script, o, a, **kw):
    d = {'id': id_, 'opts': o, 'ans': a}
    if script is not None: d['script'] = script
    d.update(kw); return d

# ───────────────────────── GPT · HSK4 ─────────────────────────
def gpt4():
    S, T = rd('P4_student.txt'), rd('P4_teacher.txt')
    K = keys(T.split('二、答案')[1].split('书写第一部分')[0])
    W1 = dict((int(n), v.strip()) for n, v in re.findall(r'(\d+)\.\s*(\S.+?。|\S.+?？)', T.split('书写第一部分')[1].split('书写第二部分')[0]))
    W2 = dict((int(n), v.strip()) for n, v in re.findall(r'(\d+)\.\s*(\S.+?[。？！])', T.split('书写第二部分')[1].split('评分提示')[0]))
    W1[93] = '中文他说得很流利。'  # FIX: original key repeats 说, impossible with given words
    tl = seq_blocks(T.split('第一部分（1—10 题）')[1].split('第二部分')[0], 1, 10, r'(?:^|\n)\s*{n}\.\s*')
    tf = []
    for n in range(1, 11):
        b = tl[n]; sc, st = b.split('★')
        tf.append({'id': f'L{n}', 'script': flat(sc), 'stem': flat(st), 'ans': K[n]})
    ts = seq_blocks(T.split('第二部分（11—25 题）')[1].split('第三部分（26—45 题）')[0], 11, 25, r'(?:^|\n)\s*{n}\.\s*')
    ts.update(seq_blocks(T.split('第三部分（26—45 题）')[1].split('36—37 题材料')[0], 26, 35, r'(?:^|\n)\s*{n}\.\s*'))
    so = seq_blocks(S.split('第二部分（11—25 题）')[1].split('二、阅读')[0], 11, 45, r'(?:^|\n)\s*{n}\.\s*')
    p2 = [mc(f'L{n}', script_lines(ts[n]), opts(so[n], 4), K[n]) for n in range(11, 26)]
    p3 = [mc(f'L{n}', script_lines(ts[n]), opts(so[n], 4), K[n]) for n in range(26, 36)]
    groups = []
    gtxt = T.split('第三部分（26—45 题）')[1].split('二、答案')[0]
    for a, b, body in re.findall(r'(\d+)—(\d+) 题材料：(.+?)(?=\n\s*\d+—\d+ 题材料|\n\s*二、答案|\Z)', gtxt + '\n二、答案', re.S):
        a, b = int(a), int(b)
        pas, qs = body.split(f'\n{a}.', 1)
        qb = seq_blocks(f'{a}.' + qs, a, b, r'(?:^|\n)\s*{n}\.\s*')
        groups.append({'id': f'L{a}', 'script': flat(pas), 'items': [mc(f'L{n}', None, opts(so[n], 4), K[n], q=flat(qb[n])) for n in range(a, b + 1)]})
    R = S.split('二、阅读')[1].split('三、书写')[0]
    banks = re.findall(r'(\d+)—(\d+) 题选项：(.+)', R)
    b1 = dict(zip(L, opts(banks[0][2], 6))); b2 = dict(zip(L, opts(banks[1][2], 6)))
    rb = seq_blocks(R.split('第一部分')[1].split('第二部分')[0], 46, 55, r'(?:^|\n)\s*{n}\.\s*')
    def btext(t):
        t = re.sub(r'\d+—\d+ 题选项：.*', '', t).strip()
        t = '\n'.join(flat(x) for x in re.split(r'\n(?=B：)', t))
        return re.sub(r'（\s*）', '（　　）', t)
    bank1 = [{'id': f'R{n}', 'text': btext(rb[n]), 'ans': K[n]} for n in range(46, 51)]
    bank2 = [{'id': f'R{n}', 'text': btext(rb[n]), 'ans': K[n]} for n in range(51, 56)]
    ob = seq_blocks(R.split('第二部分（56—65 题）')[1].split('第三部分')[0], 56, 65, r'(?:^|\n)\s*{n}\.\s*')
    order = []
    for n in range(56, 66):
        segs = re.findall(r'(?m)^\s*([ABC])\s+(.+)$', ob[n].split('顺序')[0]) or re.findall(r'([ABC])\s+(\S+)', ob[n])
        order.append({'id': f'R{n}', 'segs': [s for _, s in sorted(segs)][:3], 'ans': K[n]})
    R3 = R.split('第三部分（66—85 题）')[1]
    rb3 = seq_blocks(R3.split('80—81.')[0], 66, 79, r'(?:^|\n)\s*{n}\.\s*')
    rmc = []
    for n in range(66, 80):
        pas, rest = rb3[n].split('★', 1)
        q, o = rest.split('\nA ', 1)
        rmc.append(mc(f'R{n}', None, opts('A ' + o, 4), K[n], passage=flat(pas), q=flat(q)))
    rg = []
    for a, b in [(80, 81), (82, 83), (84, 85)]:
        seg = R3.split(f'{a}—{b}.')[1]
        pas = seg.split(f'\n{a}. ★')[0]
        if f'\n{a}.' not in seg.split('★')[0] and f'{a}. ★' in seg: pas = seg.split(f'{a}. ★')[0]
        items = []
        for n in range(a, b + 1):
            m = re.search(rf'{n}\.\s*★\s*(.+?)\n\s*(A .+?)(?=\n\s*\n|\n\s*\d|\Z)', seg, re.S)
            items.append(mc(f'R{n}', None, opts(m.group(2), 4), K[n], q=flat(m.group(1))))
        rg.append({'id': f'R{a}', 'passage': flat(pas), 'items': items})
    WS = S.split('三、书写')[1]
    wb = seq_blocks(WS.split('第一部分')[1].split('第二部分')[0], 86, 95, r'(?:^|\n)\s*{n}\.\s*')
    arr = [{'id': f'W{n}', 'words': [w.strip() for w in wb[n].split('\n')[0].split('/')], 'ans': [W1[n]]} for n in range(86, 96)]
    SCENES = {96: ('📚🤫', '한 학생이 도서관에서 조용히 책을 읽고 있다.'), 97: ('🚏☂️', '한 사람이 우산을 들고 정류장에 서 있다.'),
              98: ('👩‍🍳🍎🔪', '엄마가 부엌에서 과일을 자르고 있다.'), 99: ('⛰️📸👫', '두 친구가 산 정상에서 사진을 찍고 있다.'),
              100: ('🧳💪😓', '남학생이 아주 무거운 여행 가방을 들고 있다.')}
    pic = []
    for n in range(96, 101):
        word = re.search(rf'{n}\..*?指定词：(\S+)', WS, re.S).group(1)
        pic.append({'id': f'W{n}', 'word': word, 'emoji': SCENES[n][0], 'scene': SCENES[n][1], 'sample': W2[n]})
    return {'id': 'p4a', 'level': 4, 'label': '1', 'kind': 'practice', 'source': 'GPT', 'title': 'HSK 4급 실전 모의고사 1', 'minutes': 100,
            'sections': [
                {'key': 'L', 'name': '听力', 'ko': '듣기', 'parts': [
                    {'type': 'tf', 'title': '第一部分 判断对错', 'ko': '녹음을 듣고 ★ 문장이 맞으면 √, 틀리면 ×를 고르세요.', 'items': tf},
                    {'type': 'lmc', 'title': '第二部分', 'ko': '대화를 듣고 알맞은 답을 고르세요.', 'items': p2},
                    {'type': 'lmc', 'title': '第三部分 (对话)', 'ko': '대화를 듣고 알맞은 답을 고르세요.', 'items': p3},
                    {'type': 'lgroup', 'title': '第三部分 (语段)', 'ko': '단락을 듣고 이어지는 질문에 답하세요.', 'groups': groups}]},
                {'key': 'R', 'name': '阅读', 'ko': '독해', 'parts': [
                    {'type': 'bank', 'title': '第一部分 选词填空 (46—50)', 'ko': '빈칸에 알맞은 단어를 고르세요.', 'bank': b1, 'items': bank1},
                    {'type': 'bank', 'title': '第一部分 选词填空 (51—55)', 'ko': '빈칸에 알맞은 단어를 고르세요.', 'bank': b2, 'items': bank2},
                    {'type': 'order', 'title': '第二部分 排列顺序', 'ko': '세 문장을 올바른 순서로 배열하세요.', 'items': order},
                    {'type': 'rmc', 'title': '第三部分', 'ko': '글을 읽고 알맞은 답을 고르세요.', 'items': rmc},
                    {'type': 'rgroup', 'title': '第三部分 (长文)', 'ko': '글을 읽고 질문에 답하세요.', 'groups': rg}]},
                {'key': 'W', 'name': '书写', 'ko': '쓰기', 'parts': [
                    {'type': 'arrange', 'title': '第一部分 完成句子', 'ko': '단어를 눌러 올바른 문장을 완성하세요.', 'items': arr},
                    {'type': 'picture', 'title': '第二部分 看图，用词造句', 'ko': '장면을 보고 제시어로 한 문장을 쓰세요.', 'items': pic}]}]}

if __name__ == '__main__':
    import practice_more  # noqa: F401  (remaining builders live there)
    for fn in [gpt4] + practice_more.BUILDERS:
        finish(fn())
