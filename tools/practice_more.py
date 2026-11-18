"""Builders for the remaining practice sets (Gemini 4, GPT 5, Gemini 5, GPT 6, Gemini 6)."""
import re
from build_practice import rd, flat, seq_blocks, opts, script_lines, keys, mc, L

NUMPAT = r'(?:^|(?<=[\s。？！”）\]】]))\s*{n}\s*[.．]\s*'

def cut(s):  # drop trailing section headers that leak into option blocks
    return re.split(r'第[一二三四]部分|[一二三]、\s*[听阅书]|HSK（|●\s*\[|○\s*第', s)[0]

def o4(s, k=4): return opts(cut(s), k)

def sec(text, a, b=None):
    t = text.split(a, 1)[1]
    return t.split(b, 1)[0] if b else t

def F(s):  # flatten whole region into one line (for Gemini docs)
    s = re.sub(r'[●○■]\s*', ' ', s)
    s = re.sub(r'\s*\n\s*', ' ', s)
    s = re.sub(r'(?<=[　-鿿，。！？；：、“”）（])\s+(?=[　-鿿，。！？；：、“”（）])', '', s)
    return re.sub(r'\s{2,}', ' ', s).strip()

def F2(s):  # join wrapped lines but keep in-line spaces (word separators)
    s = re.sub(r'[●○■]\s*', ' ', s)
    s = re.sub(r'\s*\n\s*(?=\d+\s*[.．])', ' ', s)
    return re.sub(r' {2,}', ' ', re.sub(r'\s*\n\s*', '', s)).strip()

def gscript(s):
    s = re.sub(r'(?<=[\s。？！!?…”）])\s*(?=(男|女|问)[：:])', '\n', s.strip())
    return '\n'.join(x.strip() for x in s.split('\n') if x.strip())

def wset(id_, level, label, source, minutes, L_parts, R_parts, W_parts):
    return {'id': id_, 'level': level, 'label': label, 'kind': 'practice', 'source': source,
            'title': f'HSK {level}급 실전 모의고사 {label}', 'minutes': minutes,
            'sections': [{'key': 'L', 'name': '听力', 'ko': '듣기', 'parts': L_parts},
                         {'key': 'R', 'name': '阅读', 'ko': '독해', 'parts': R_parts},
                         {'key': 'W', 'name': '书写', 'ko': '쓰기', 'parts': W_parts}]}

def P(type_, title, ko, **kw):
    d = {'type': type_, 'title': title, 'ko': ko}; d.update(kw); return d

def grp(text):
    return [(a, b, body) for a, b, body in re.findall(r'第(\d+)-(\d+)题\s*(.+?)(?=第\d+-\d+题|$)', text) if int(b) - int(a) < 8]

def picks(s, first, last, k=4):
    b = seq_blocks(F(s), first, last, NUMPAT)
    return {n: o4(b[n], k) for n in b}

# ───────────────────────── Gemini · HSK4 ─────────────────────────
def gem4():
    T = rd('G4.txt')
    A = T.split('参考答案')[1]; K = keys(A.split('三、书写')[0])
    W = dict((int(n), v) for n, v in re.findall(r'(\d+)\.\s*(\S+?[。？！])', F(A.split('86-95:')[1].split('96-100')[0])))
    W2 = dict((int(n), v) for n, v in re.findall(r'(\d+)\.\s*(\S+?[。？！])', F(A.split('(参考例句):')[1])))
    s1 = seq_blocks(F(sec(T, '[听力材料 1-10]', '[试题 1-10]')), 1, 10, NUMPAT)
    st = seq_blocks(F(sec(T, '[试题 1-10]', '第二部分')), 1, 10, NUMPAT)
    tf = [{'id': f'L{n}', 'script': s1[n], 'stem': re.sub(r'^★\s*|\(\s*\)\s*$', '', st[n]).strip(), 'ans': K[n]} for n in range(1, 11)]
    sc2 = seq_blocks(F(sec(T, '[听力材料 11-25]', '[试题 11-25]')), 11, 25, NUMPAT)
    op2 = picks(sec(T, '[试题 11-25]', '第三部分'), 11, 25)
    p2 = [mc(f'L{n}', gscript(sc2[n]), op2[n], K[n]) for n in range(11, 26)]
    L3 = F(sec(T, '[听力材料 26-45]', '[试题 26-45]'))
    sc3 = seq_blocks(L3.split('第36到37题')[0], 26, 35, NUMPAT)
    op3 = picks(sec(T, '[试题 26-45]', '二、 阅读'), 26, 45)
    p3 = [mc(f'L{n}', gscript(sc3[n]), op3[n], K[n]) for n in range(26, 36)]
    groups = []
    for a, b, body in re.findall(r'第(\d+)到(\d+)题是根据下面一段话：\s*(.+?)(?=第\d+到\d+题|$)', L3):
        a, b = int(a), int(b)
        qb = seq_blocks(body, a, b, NUMPAT); pas = body.split(f'{a}.')[0].strip()
        groups.append({'id': f'L{a}', 'script': pas, 'items': [mc(f'L{n}', None, op3[n], K[n], q=qb[n]) for n in range(a, b + 1)]})
    R = F(sec(T, '二、 阅读', '三、 书写'))
    b1t = re.search(r'第46-50题\s*(A .+?)(?=46\.)', R).group(1); b2t = re.search(r'第51-55题\s*(A .+?)(?=51\.)', R).group(1)
    b1, b2 = dict(zip(L, opts(b1t, 6))), dict(zip(L, opts(b2t, 6)))
    rb = seq_blocks(R.split('第二部分')[0], 46, 55, NUMPAT)
    def bt(t):
        t = re.split(r'●|第51-55题', t)[0].strip()
        t = re.sub(r'\(\s*\)', '（　　）', t)
        return re.sub(r'\s*B：', '\nB：', t)
    bank1 = [{'id': f'R{n}', 'text': bt(rb[n]), 'ans': K[n]} for n in range(46, 51)]
    bank2 = [{'id': f'R{n}', 'text': bt(rb[n]), 'ans': K[n]} for n in range(51, 56)]
    ob = seq_blocks(sec(R, '第二部分', '第三部分'), 56, 65, NUMPAT)
    order = []
    for n in range(56, 66):
        parts = re.split(r'\s*([ABC])[:：]\s*', ' ' + ob[n])
        segs = {parts[i]: parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}
        order.append({'id': f'R{n}', 'segs': [segs['A'], segs['B'], segs['C']], 'ans': K[n]})
    R3 = sec(R, '第三部分')
    rb3 = seq_blocks(R3.split('第80-81题')[0], 66, 79, NUMPAT)
    rmc = []
    for n in range(66, 80):
        pas, rest = rb3[n].split('★', 1); q, o = re.split(r'\s(?=A\s)', rest.strip(), 1)
        rmc.append(mc(f'R{n}', None, o4(o), K[n], passage=pas.strip(), q=q.strip()))
    rg = []
    for a, b in [(80, 81), (82, 83), (84, 85)]:
        body = R3.split(f'第{a}-{b}题')[1].split('第8')[0] if a < 84 else R3.split(f'第{a}-{b}题')[1]
        pas = body.split(f'{a}. ★')[0].strip()
        items = []
        for n in range(a, b + 1):
            m = re.search(rf'{n}\.\s*★\s*(.+?)\s(A\s.+?)(?=\s\d+\.\s*★|$)', body)
            items.append(mc(f'R{n}', None, o4(m.group(2)), K[n], q=m.group(1).strip()))
        rg.append({'id': f'R{a}', 'passage': pas, 'items': items})
    WS = F(sec(T, '三、 书写', 'HSK（四级）模拟试卷参考答案'))
    wb = seq_blocks(F2(sec(T, '三、 书写', 'HSK（四级）模拟试卷参考答案')).split('第二部分')[0], 86, 95, NUMPAT)
    arr = [{'id': f'W{n}', 'words': wb[n].split(), 'ans': [W[n]]} for n in range(86, 96)]
    SC = {96: ('👩📖', '한 여성이 도서관에서 열심히 책을 읽고 있다.'), 97: ('🏃‍♂️🏃‍♀️🌳', '두 젊은이가 공원에서 달리기를 하고 있다.'),
          98: ('👨‍🍳🍳', '요리사가 주방에서 볶음 요리를 하고 있다.'), 99: ('👦💯😄', '남자아이가 만점 시험지를 들고 아주 기쁘게 웃고 있다.'),
          100: ('❄️🏠🍵👨‍👩‍👧', '창밖에는 눈이 많이 내리고, 가족이 거실에서 차를 마시며 이야기하고 있다.')}
    pic = [{'id': f'W{n}', 'word': re.search(rf'{n}\.\s*\[.+?\]\s*词语：(\S+)', WS).group(1), 'emoji': SC[n][0], 'scene': SC[n][1], 'sample': W2[n]} for n in range(96, 101)]
    return wset('p4b', 4, '2', 'Gemini', 100,
        [P('tf', '第一部分 判断对错', '녹음을 듣고 ★ 문장이 맞으면 √, 틀리면 ×를 고르세요.', items=tf),
         P('lmc', '第二部分', '대화를 듣고 알맞은 답을 고르세요.', items=p2),
         P('lmc', '第三部分 (对话)', '대화를 듣고 알맞은 답을 고르세요.', items=p3),
         P('lgroup', '第三部分 (语段)', '단락을 듣고 이어지는 질문에 답하세요.', groups=groups)],
        [P('bank', '第一部分 选词填空 (46—50)', '빈칸에 알맞은 단어를 고르세요.', bank=b1, items=bank1),
         P('bank', '第一部分 选词填空 (51—55)', '빈칸에 알맞은 단어를 고르세요.', bank=b2, items=bank2),
         P('order', '第二部分 排列顺序', '세 문장을 올바른 순서로 배열하세요.', items=order),
         P('rmc', '第三部分', '글을 읽고 알맞은 답을 고르세요.', items=rmc),
         P('rgroup', '第三部分 (长文)', '글을 읽고 질문에 답하세요.', groups=rg)],
        [P('arrange', '第一部分 完成句子', '단어를 눌러 올바른 문장을 완성하세요.', items=arr),
         P('picture', '第二部分 看图，用词造句', '장면을 보고 제시어로 한 문장을 쓰세요.', items=pic)])

# ───────────────────────── GPT · HSK5 ─────────────────────────
def gpt5():
    T = rd('P5_a.txt')
    stu, tea = T.split('教师用：听力材料')
    tl, ta = tea.split('教师用：参考答案')
    K = keys(ta.split('书写 第一部分')[0])
    W = dict((int(n), v.strip()) for n, v in re.findall(r'(\d+)．\s*(\S.+?[。？！])', ta.split('书写 第一部分（参考答案）')[1].split('书写 第二部分')[0]))
    S99 = flat(ta.split('99．')[1].split('100．')[0]); S100 = flat(ta.split('100．')[1].split('评分提醒')[0])
    NP = r'(?:^|\n)\s*{n}\s*[.．]\s*'
    so = seq_blocks(sec(stu, '一、听 力', '二、阅 读'), 1, 45, NP)
    O = {n: o4(re.sub(r'请选择正确答案。', '', so[n])) for n in so}
    O[22] = ['6 楼 1203 室', '12 号楼 603 室', '6 号楼 1203 室', '6 号楼 603 室']  # FIX: B and D were identical
    sc = seq_blocks(tl.split('第 31—32 题')[0], 1, 30, NP)
    p1 = [mc(f'L{n}', script_lines(cut(sc[n])), O[n], K[n]) for n in range(1, 21)]
    p2 = [mc(f'L{n}', script_lines(cut(sc[n])), O[n], K[n]) for n in range(21, 31)]
    groups = []
    for a, b, body in re.findall(r'第 (\d+)—(\d+) 题根据下面一段对话或短文：\s*(.+?)(?=第 \d+—\d+ 题|\Z)', tl, re.S):
        a, b = int(a), int(b)
        pas = body.split(f'{a}．')[0]
        qb = seq_blocks(body, a, b, NP)
        pas = script_lines(pas) if re.search(r'(男|女)：', pas) else flat(pas)
        groups.append({'id': f'L{a}', 'script': pas, 'items': [mc(f'L{n}', None, O[n], K[n], q=flat(qb[n]).replace('问：', '')) for n in range(a, b + 1)]})
    R = sec(stu, '二、阅 读', '三、书 写')
    R1 = sec(R, '请根据上下文，选出填入空白处最恰当的一项。', '第二部分')
    rb = seq_blocks(R1, 46, 60, r'\n\s*{n}．\s*\n')
    head = R1.split('\n46．')[0].strip()
    cl_groups, cur = [], {'passage': head, 'items': []}
    for n in range(46, 61):
        blk = rb[n].strip()
        m = re.match(r'(A.+?)(?:\n\s*\n|$)(.*)', blk, re.S)
        cur['items'].append(mc(f'R{n}', None, o4(m.group(1)), K[n]))
        rest = m.group(2).strip()
        if rest or n == 60:
            cl_groups.append(cur); cur = {'passage': rest, 'items': []}
    for g in cl_groups:
        g['passage'] = re.sub(r'（(\d+)）', r'（R\1）', flat(g['passage']))
        g['id'] = g['items'][0]['id']
    R2 = seq_blocks(sec(R, '请选出与试题内容一致的一项。', '第三部分'), 61, 70, NP)
    p62 = []
    for n in range(61, 71):
        pas, o = re.split(r'\n\s*A\s', R2[n], 1)
        p62.append(mc(f'R{n}', None, o4('A ' + o), K[n], passage=flat(pas), q=''))
    R3 = sec(R, '请阅读短文，选出正确答案。')
    rg = []
    for m in re.finditer(r'【(.+?)】(.+?)(?=【|\Z)', R3, re.S):
        title, body = m.group(1), m.group(2)
        first = int(re.search(r'\n\s*(\d+)．', body).group(1))
        nums = [int(x) for x in re.findall(r'\n\s*(\d+)．', body)]
        pas = body.split(f'\n{first}．')[0]
        qb = seq_blocks(body, first, nums[-1], NP)
        items = []
        for n in range(first, nums[-1] + 1):
            q, o = re.split(r'\n\s*A\s', qb[n], 1)
            items.append(mc(f'R{n}', None, o4('A ' + o), K[n], q=flat(q)))
        rg.append({'id': f'R{first}', 'passage': f'【{title}】\n' + flat(pas), 'items': items})
    WS = sec(stu, '三、书 写')
    wb = seq_blocks(WS.split('第二部分')[0], 91, 98, NP)
    arr = [{'id': f'W{n}', 'words': [w.strip() for w in wb[n].split('\n')[0].split('/')], 'ans': [W[n]]} for n in range(91, 99)]
    words99 = [w.strip() for w in re.search(r'99．.+?\n\s*\n\s*(.+?)\n', WS, re.S).group(1).split('、')]
    return wset('p5a', 5, '1', 'GPT', 120,
        [P('lmc', '第一部分', '대화를 듣고 알맞은 답을 고르세요.', items=p1),
         P('lmc', '第二部分 (对话)', '대화를 듣고 알맞은 답을 고르세요.', items=p2),
         P('lgroup', '第二部分 (对话·短文)', '대화나 단문을 듣고 질문에 답하세요.', groups=groups)],
        [P('cloze', '第一部分', '빈칸에 들어갈 가장 알맞은 것을 고르세요.', groups=cl_groups),
         P('rmc', '第二部分 选出一致的一项', '글의 내용과 일치하는 것을 고르세요.', items=p62),
         P('rgroup', '第三部分', '글을 읽고 질문에 답하세요.', groups=rg)],
        [P('arrange', '第一部分 完成句子', '단어를 눌러 올바른 문장을 완성하세요.', items=arr),
         P('essay', '第二部分 写短文 (99)', '제시된 단어를 모두 사용하여 80자 내외의 글을 쓰세요.', items=[{'id': 'W99', 'words': words99, 'min': 70, 'max': 110, 'sample': S99}]),
         P('essay', '第二部分 写短文 (100)', '장면을 보고 80자 내외의 글을 쓰세요.', items=[{'id': 'W100', 'img': 'img/p5a-W100.png', 'emoji': '🧤🗑️🌳🙋', 'scene': '주말에 자원봉사자들이 장갑을 끼고 공원에서 쓰레기와 플라스틱병을 줍고 있다.', 'min': 70, 'max': 110, 'sample': S100}])])

# ───────────────────────── Gemini · HSK5 ─────────────────────────
def gem5():
    T = rd('G56.txt').split('新汉语水平考试 HSK（六级）')[0]
    A = T.split('HSK（五级）模拟试卷参考答案')[1]; K = keys(A.split('三、书写')[0])
    W = dict((int(n), v) for n, v in re.findall(r'(\d+)\.\s*(\S+?[。？！])', F(A.split('91-98:')[1].split('99-100')[0])))
    S99 = F(A.split('99:')[1].split('100:')[0]); S100 = F(A.split('100:')[1])
    sc1 = seq_blocks(F(sec(T, '[听力材料 1-20]', '[试题 1-20]')), 1, 20, NUMPAT)
    op1 = picks(sec(T, '[试题 1-20]', '第二部分'), 1, 20)
    op1[11] = ['他们迟到了', '观众非常多', '音乐会取消了', '他们来得太早了']  # FIX: original D (门票很难买到) was also true
    p1 = [mc(f'L{n}', gscript(sc1[n]), op1[n], K[n]) for n in range(1, 21)]
    L2 = F(sec(T, '[听力材料 21-45]', '[试题 21-45]'))
    sc2 = seq_blocks(L2.split('第31到32题')[0], 21, 30, NUMPAT)
    op2 = picks(sec(T, '[试题 21-45]', '二、 阅读'), 21, 45)
    p2 = [mc(f'L{n}', gscript(sc2[n]), op2[n], K[n]) for n in range(21, 31)]
    groups = []
    for a, b, body in re.findall(r'第(\d+)到(\d+)题是根据下面一段(?:对话|话)：\s*(.+?)(?=第\d+到\d+题|$)', L2):
        a, b = int(a), int(b)
        pas = body.split(f' {a}. ')[0] if f' {a}. ' in body else body.split(f'{a}.')[0]
        qb = seq_blocks(body[len(pas):], a, b, NUMPAT)
        pas = gscript(pas) if re.search(r'(男|女)：', pas) else pas.strip()
        groups.append({'id': f'L{a}', 'script': pas, 'items': [mc(f'L{n}', None, op2[n], K[n], q=qb[n]) for n in range(a, b + 1)]})
    R = F(sec(T, '二、 阅读', '三、 书写'))
    R1 = sec(R, '第一部分', '第二部分')
    cl = []
    for a, b, body in grp(R1):
        a, b = int(a), int(b)
        pas = body.split(f'{a}. A')[0]
        for n in range(a, b + 1):
            pas = re.sub(rf'(?<=[\s，。])\s*{n}\s*(?=[\s，。；]|$)', f'（R{n}）', pas, 1)
        qb = seq_blocks(body[len(body.split(f'{a}. A')[0]):], a, b, NUMPAT)
        cl.append({'id': f'R{a}', 'passage': pas.strip(), 'items': [mc(f'R{n}', None, o4(qb[n]), K[n]) for n in range(a, b + 1)]})
    rb2 = seq_blocks(sec(R, '第二部分', '第三部分'), 61, 70, NUMPAT)
    p62 = []
    for n in range(61, 71):
        pas, o = re.split(r'\s(?=A\s)', rb2[n], 1)
        p62.append(mc(f'R{n}', None, o4(o), K[n], passage=pas.strip(), q=''))
    rg = []
    R3 = sec(R, '第三部分')
    for a, b, body in grp(R3):
        a, b = int(a), int(b)
        pas = body.split(f' {a}. ')[0]
        qb = seq_blocks(body[len(pas):], a, b, NUMPAT)
        items = []
        for n in range(a, b + 1):
            q, o = re.split(r'\s(?=A\s)', qb[n], 1)
            items.append(mc(f'R{n}', None, o4(o), K[n], q=q.strip()))
        rg.append({'id': f'R{a}', 'passage': pas.strip(), 'items': items})
    WS = F(sec(T, '三、 书写', 'HSK（五级）模拟试卷参考答案'))
    wb = seq_blocks(F2(sec(T, '三、 书写', 'HSK（五级）模拟试卷参考答案')).split('第二部分')[0], 91, 98, NUMPAT)
    arr = [{'id': f'W{n}', 'words': wb[n].split(), 'ans': [W[n]]} for n in range(91, 99)]
    arr[7]['ans'].append('务必签署前仔细阅读合同。')
    words99 = re.search(r'短文。\s*(\S+)', WS.split('99.')[1]).group(1).split('、')
    return wset('p5b', 5, '2', 'Gemini', 120,
        [P('lmc', '第一部分', '대화를 듣고 알맞은 답을 고르세요.', items=p1),
         P('lmc', '第二部分 (对话)', '대화를 듣고 알맞은 답을 고르세요.', items=p2),
         P('lgroup', '第二部分 (对话·短文)', '대화나 단문을 듣고 질문에 답하세요.', groups=groups)],
        [P('cloze', '第一部分', '빈칸에 들어갈 가장 알맞은 것을 고르세요.', groups=cl),
         P('rmc', '第二部分 选出一致的一项', '글의 내용과 일치하는 것을 고르세요.', items=p62),
         P('rgroup', '第三部分', '글을 읽고 질문에 답하세요.', groups=rg)],
        [P('arrange', '第一部分 完成句子', '단어를 눌러 올바른 문장을 완성하세요.', items=arr),
         P('essay', '第二部分 写短文 (99)', '제시된 단어를 모두 사용하여 80자 내외의 글을 쓰세요.', items=[{'id': 'W99', 'words': words99, 'min': 70, 'max': 110, 'sample': S99}]),
         P('essay', '第二部分 写短文 (100)', '장면을 보고 80자 내외의 글을 쓰세요.', items=[{'id': 'W100', 'emoji': '📚🪜🙂', 'scene': '도서관에서 한 젊은이가 높은 책장의 책을 꺼내려고 발끝을 들고 있고, 옆에서 사서가 웃으며 사다리를 건네주고 있다.', 'min': 70, 'max': 110, 'sample': S100}])])

# ───────────────────────── GPT · HSK6 ─────────────────────────
GPT6_Q = {16: '嘉宾为什么选择改造旧厂房？', 17: '改造中最大的困难是什么？', 18: '新的用途是怎么决定的？', 19: '改造后最让嘉宾意外的是什么？', 20: '嘉宾认为未来的城市更新应该怎样？',
          21: '嘉宾为什么开始做科普？', 22: '解释复杂概念时最重要的是什么？', 23: '嘉宾怎么看比喻？', 24: '面对质疑，嘉宾通常怎么做？', 25: '嘉宾希望听众最后获得什么？',
          26: '嘉宾什么时候正式开始学习陶艺？', 27: '年轻学徒最难掌握的是什么？', 28: '嘉宾怎么看机器与手工？', 29: '嘉宾为什么开设体验课程？', 30: '嘉宾最担心什么？'}
def gpt6():
    S, T = rd('P6_student.txt'), rd('P6_teacher.txt')
    K = keys(T.split('二、参考答案')[1].split('三、书写题')[0])
    NP = r'(?:^|\n)\s*{n}\s*[.．]\s*'
    so = seq_blocks(sec(S, '第一部分（1—15）', '二、阅读'), 1, 50, NP)
    def ol(b):  # options on separate lines
        b = re.sub(r'^.*?(?=\n\s*A\s)', '', '\n' + b, flags=re.S)
        return [flat(x) for x in re.findall(r'\n\s*[A-F]\s+(.+?)(?=\n\s*[A-F]\s|\Z)', cut(b), re.S)]
    O = {n: ol(so[n]) for n in so}
    tl = sec(T, '第一部分（1—15）', '第二部分（16—30）')
    s1 = seq_blocks(tl, 1, 15, NP)
    p1 = [mc(f'L{n}', flat(s1[n]), O[n], K[n]) for n in range(1, 16)]
    iv = sec(T, '第二部分（16—30）', '第三部分（31—50）')
    groups2 = []
    for gi, (a, b, body) in enumerate(re.findall(r'采访 \d：.+?（(\d+)—(\d+)）\s*(.+?)(?=采访 \d：|\Z)', iv, re.S)):
        a, b = int(a), int(b)
        host, guest = ('女', '男') if gi != 1 else ('男', '女')
        body = re.sub(r'\s*嘉宾：', '\n嘉宾：', body)
        lines = []
        for ln in re.split(r'\n(?=主持人：|嘉宾：)', body.strip()):
            ln = flat(ln); lines.append(ln.replace('主持人：', host + '：').replace('嘉宾：', guest + '：'))
        groups2.append({'id': f'L{a}', 'script': '\n'.join(lines),
                        'items': [mc(f'L{n}', None, O[n], K[n], q=GPT6_Q[n].replace('嘉宾', '女的' if guest == '女' else '男的')) for n in range(a, b + 1)]})
    p3t = sec(T, '第三部分（31—50）', '二、参考答案')
    groups3 = []
    for a, b, title, body in re.findall(r'(\d+)—(\d+)：(\S+)\s*\n(.+?)(?=\n\s*\d+—\d+：|\Z)', p3t, re.S):
        a, b = int(a), int(b)
        pas = body.split(f'\n{a}．')[0]
        qb = seq_blocks(body, a, b, NP)
        groups3.append({'id': f'L{a}', 'script': flat(pas), 'items': [mc(f'L{n}', None, O[n], K[n], q=flat(qb[n])) for n in range(a, b + 1)]})
    R = sec(S, '二、阅读', '三、书写')
    eb = seq_blocks(sec(R, '请选出有语病的一项。', '第二部分'), 51, 60, NP)
    err = [mc(f'R{n}', None, ol(eb[n]), K[n]) for n in range(51, 61)]
    err[2]['opts'][2] = '听了这场讲座，我的知识水平和视野都扩大了很多。'  # FIX: clearer error (搭配不当: 水平…扩大)
    err[2]['exp'] = '“水平”은 “扩大”와 호응하지 않음 (水平提高 / 视野扩大).'
    mb = seq_blocks(sec(R, '选词填空。', '第三部分'), 61, 70, NP)
    multi = []
    for n in range(61, 71):
        t, o = re.split(r'\n\s*A\s', mb[n], 1)
        multi.append(mc(f'R{n}', None, [x.replace('／', '　') for x in ol('\n A ' + o)], K[n], text=flat(t).replace('____', '＿＿＿')))
    sf = sec(R, '请从 A—E 中选择合适的句子。', '第四部分')
    sgroups = []
    for title, body in re.findall(r'\n(\S{4,10})\n(.+?)(?=\n\S{4,10}\n|\Z)', '\n' + sf.strip(), re.S):
        pas, bank = re.split(r'\n\s*A\s', body, 1)
        bank = dict(zip('ABCDE', ol('\n A ' + bank)))
        nums = [int(x) for x in re.findall(r'（(\d+)）', pas)]
        pas = re.sub(r'（(\d+)）____', r'（R\1）', flat(pas))
        sgroups.append({'id': f'R{nums[0]}', 'passage': f'【{title}】\n' + pas, 'bank': bank, 'items': [{'id': f'R{n}', 'ans': K[n]} for n in nums]})
    TITLES = ['沉默的价值', '修复一条河', '数字时代的记忆', '一位修鞋师傅', '科学中的偶然']
    R4 = sec(R, '请阅读文章并选出正确答案。')
    chunks = re.split(r'\n\s*(?:默的价|修一河|字代的|一位修鞋师傅|科中的偶然)\s*\n', '\n' + R4)
    chunks = [c for c in chunks if c.strip()]
    rg = []
    for title, body in zip(TITLES, chunks):
        nums = [int(x) for x in re.findall(r'\n\s*(\d+)．', '\n' + body)]
        first, last = nums[0], nums[-1]
        pas = ('\n' + body).split(f'\n{first}．')[0]
        qb = seq_blocks('\n' + body, first, last, NP)
        items = []
        for n in range(first, last + 1):
            q, o = re.split(r'\n\s*A\s', qb[n], 1)
            items.append(mc(f'R{n}', None, ol('\n A ' + o), K[n], q=flat(q)))
        rg.append({'id': f'R{first}', 'passage': f'【{title}】\n' + flat(pas), 'items': items})
    text101 = '\n'.join(flat(p) for p in re.split(r'\n\s*\n', sec(S, '（3）标题自拟，只复述文章内容，不加入个人观点。', '作答区').strip()) if p.strip())
    sample = '面包店的坚持\n' + flat(sec(T, '参考缩写如下（非唯一答案）：', '评分建议'))
    return wset('p6a', 6, '1', 'GPT', 135,
        [P('lmc', '第一部分', '녹음을 듣고 내용과 일치하는 것을 고르세요.', items=p1),
         P('lgroup', '第二部分 采访', '인터뷰를 듣고 질문에 답하세요.', groups=groups2),
         P('lgroup', '第三部分 语段', '단락을 듣고 질문에 답하세요.', groups=groups3)],
        [P('error', '第一部分 请选出有语病的一项', '문법적으로 틀린 문장을 고르세요.', items=err),
         P('multi', '第二部分 选词填空', '빈칸에 순서대로 들어갈 단어 조합을 고르세요.', items=multi),
         P('sentfill', '第三部分 选句填空', '빈칸에 알맞은 문장을 A~E에서 고르세요.', groups=sgroups),
         P('rgroup', '第四部分', '글을 읽고 질문에 답하세요.', groups=rg)],
        [P('summary', '缩写', '글을 10분 동안 읽은 뒤 글이 사라지면 400자 내외로 요약하세요. 제목은 직접 붙이고 자신의 의견은 넣지 마세요.',
           items=[{'id': 'W101', 'read': 600, 'min': 350, 'max': 500, 'text': text101, 'sample': sample}])])

# ───────────────────────── Gemini · HSK6 ─────────────────────────
def gem6():
    T = '新汉语水平考试 HSK（六级）' + rd('G56.txt').split('新汉语水平考试 HSK（六级）')[1]
    A = T.split('HSK（六级）模拟试卷参考答案')[1]
    K = keys(F(A.split('51-60')[0]))
    K.update(keys(F(A.split('61-70:')[1].split('三、书写')[0])))
    for n, l in re.findall(r'(5\d|60)\.\s*([A-D])\s*\(', F(A)): K[int(n)] = l
    EXP = {int(n): e for n, e in re.findall(r'(5\d|60)\.\s*[A-D]\s*\((.+?)\)(?=\s*■|\s*○|\s*\d\d\.|$)', F(A.split('61-70:')[0]))}
    sc1 = seq_blocks(F(sec(T, '[听力材料 1-15]', '[试题 1-15]')), 1, 15, NUMPAT)
    op1 = picks(sec(T, '[试题 1-15]', '第二部分'), 1, 15)
    p1 = [mc(f'L{n}', sc1[n], op1[n], K[n]) for n in range(1, 16)]
    L2 = F(sec(T, '[听力材料 16-30]', '[试题 16-30]'))
    op2 = picks(sec(T, '[试题 16-30]', '第三部分'), 16, 30)
    groups2 = []
    for a, b, body in re.findall(r'第(\d+)到(\d+)题是根据下面一段采访：\s*(.+?)(?=第\d+到\d+题|$)', L2):
        a, b = int(a), int(b)
        if a == 16:  # FIX: drop the drafting notes left inside the first interview
            body = '女：观众朋友们大家好。' + body.split('(调整为男受访者)女：观众朋友们大家好。', 1)[1]
        pas = body.split(f' {a}. ')[0]
        qb = seq_blocks(body[len(pas):], a, b, NUMPAT)
        groups2.append({'id': f'L{a}', 'script': gscript(pas), 'items': [mc(f'L{n}', None, op2[n], K[n], q=qb[n]) for n in range(a, b + 1)]})
    L3 = F(sec(T, '[听力材料 31-50]', '[试题 31-50]'))
    op3 = picks(sec(T, '[试题 31-50]', '二、 阅读'), 31, 50)
    groups3 = []
    for a, b, body in re.findall(r'第(\d+)到(\d+)题是根据下面一段话：\s*(.+?)(?=第\d+到\d+题|$)', L3):
        a, b = int(a), int(b)
        pas = body.split(f' {a}. ')[0]
        qb = seq_blocks(body[len(pas):], a, b, NUMPAT)
        groups3.append({'id': f'L{a}', 'script': pas.strip(), 'items': [mc(f'L{n}', None, op3[n], K[n], q=qb[n]) for n in range(a, b + 1)]})
    R = F(sec(T, '二、 阅读', '三、 书写'))
    eb = seq_blocks(sec(R, '第一部分', '第二部分'), 51, 60, NUMPAT)
    err = [mc(f'R{n}', None, o4(eb[n]), K[n], exp=EXP.get(n, '')) for n in range(51, 61)]
    # FIX 52: none of the four sentences was wrong → make C a real error (语义重复: 目的是为了)
    err[1]['opts'][2] = '博物馆近期推出了一系列互动体验活动，目的是为了吸引更多青少年走进博物馆。'
    err[1]['ans'] = 'C'; err[1]['exp'] = '“目的是”와 “为了”가 의미 중복(语义重复). “目的是吸引…” 또는 “为了吸引…”로 써야 합니다.'
    # FIX 57: the intended error was too weak → classic 两面对一面
    err[6]['opts'][0] = '真正的友谊能否经得起时间的考验，关键在于彼此真诚相待。'
    err[6]['ans'] = 'A'; err[6]['exp'] = '앞은 “能否”(양면), 뒤는 “真诚相待”(한 면)라 호응하지 않음(两面对一面).'
    mb = seq_blocks(F2(sec(sec(T, '二、 阅读', '三、 书写'), '第二部分', '第三部分')), 61, 70, NUMPAT)
    multi = []
    for n in range(61, 71):
        t, o = re.split(r'\s(?=A\s)', mb[n], 1)
        t = F(t)
        parts = re.split(r'(?:^|\s)([A-D])\s*(?=[\u4e00-\u9fff])', ' ' + o)
        op = [re.sub(r'\s+', '　', parts[i + 1].strip()) for i in range(1, len(parts) - 1, 2)]
        multi.append(mc(f'R{n}', None, op, K[n], text=re.sub(r'\(\s*\)', '＿＿＿', t).strip()))
    multi[5]['opts'][0] = '传播　平静　判决'
    multi[9]['opts'][3] = '体现　做法　映射'  # line-wrap lost the separator  # FIX 66: original A (蔓延 平息 判断) was also acceptable
    sf = sec(R, '第三部分', '第四部分')
    sgroups = []
    for a, b, body in grp(sf):
        a, b = int(a), int(b)
        pas, bank = re.split(r'(?<=[\s。])(?=A\s)', body, 1)
        bank = dict(zip('ABCDE', opts(bank, 5)))
        pas = re.sub(r'\((\d+)\)\s*_+', r'（R\1）', pas).strip()
        sgroups.append({'id': f'R{a}', 'passage': pas, 'bank': bank, 'items': [{'id': f'R{n}', 'ans': K[n]} for n in range(a, b + 1)]})
    R4 = sec(R, '第四部分')
    rg = []
    for a, b, body in grp(R4):
        a, b = int(a), int(b)
        pas = body.split(f' {a}. ')[0]
        qb = seq_blocks(body[len(pas):], a, b, NUMPAT)
        items = []
        for n in range(a, b + 1):
            q, o = re.split(r'\s(?=A\s)', qb[n], 1)
            items.append(mc(f'R{n}', None, o4(o), K[n], q=q.strip()))
        rg.append({'id': f'R{a}', 'passage': pas.strip(), 'items': items})
    ws = sec(T, '(阅读材料)', 'HSK（六级）模拟试卷参考答案')
    text101 = flat(ws)
    text101 = re.sub(r'(?<=[。”])\s*(?=(于是，无|住院期间|陈总听完|陈总微笑|出院后|起初，))', '\n', text101)
    sample = F(A.split('参考范文，约400字)')[1]).replace(' ', '\n', 1)
    return wset('p6b', 6, '2', 'Gemini', 135,
        [P('lmc', '第一部分', '녹음을 듣고 내용과 일치하는 것을 고르세요.', items=p1),
         P('lgroup', '第二部分 采访', '인터뷰를 듣고 질문에 답하세요.', groups=groups2),
         P('lgroup', '第三部分 语段', '단락을 듣고 질문에 답하세요.', groups=groups3)],
        [P('error', '第一部分 请选出有语病的一项', '문법적으로 틀린 문장을 고르세요.', items=err),
         P('multi', '第二部分 选词填空', '빈칸에 순서대로 들어갈 단어 조합을 고르세요.', items=multi),
         P('sentfill', '第三部分 选句填空', '빈칸에 알맞은 문장을 A~E에서 고르세요.', groups=sgroups),
         P('rgroup', '第四部分', '글을 읽고 질문에 답하세요.', groups=rg)],
        [P('summary', '缩写', '글을 10분 동안 읽은 뒤 글이 사라지면 400자 내외로 요약하세요. 제목은 직접 붙이고 자신의 의견은 넣지 마세요.',
           items=[{'id': 'W101', 'read': 600, 'min': 350, 'max': 500, 'text': text101, 'sample': sample}])])

BUILDERS = [gem4, gpt5, gem5, gpt6, gem6]
