/**
 * HSK 방학 특강 — 구글시트 기록 + AI 피드백 백엔드
 *
 * 설치
 *  1. 새 구글시트 → 확장 프로그램 → Apps Script → 이 파일 내용을 붙여 넣고 저장
 *  2. 함수 목록에서 setup 을 한 번 실행 (권한 허용) → 시트 3개가 만들어집니다
 *  3. 프로젝트 설정(톱니바퀴) → 스크립트 속성 추가
 *       TEACHER_PIN    : 교사용 현황 화면 비밀번호 (예: 2580)
 *       GEMINI_API_KEY : (선택) https://aistudio.google.com/apikey 에서 발급한 키 → 쓰기·말하기 AI 피드백
 *       GEMINI_MODEL   : (선택) 기본값 gemini-2.5-flash
 *  4. 배포 → 새 배포 → 유형: 웹 앱 / 실행: 나 / 액세스: 모든 사용자 → 배포
 *  5. 웹 앱 URL 을 웹앱의 config.js 의 SCRIPT_URL 에 붙여 넣기
 *  ※ 코드를 고친 뒤에는 ‘배포 관리 → 수정 → 새 버전’으로 다시 배포해야 반영됩니다.
 */
const SCOPE_KO = { all: '전체', L: '듣기', R: '독해', W: '쓰기', S: '말하기' };
const SH = { sub: '제출기록', ans: '문항기록', fb: '쓰기말하기' };
const HEAD = {
  sub: ['시간', '학번', '이름', '세트', '모드', '범위', '점수', '만점', '정답률', '듣기', '독해', '쓰기', '소요(분)', '오답문항'],
  ans: ['시간', '학번', '이름', '세트', '모드', '문항', '영역', '유형', '학생답', '정답', '정오', '점수'],
  fb:  ['시간', '학번', '이름', '세트', '문항', '유형', '과제', '학생답안', '점수', 'AI 총평', 'AI 피드백(JSON)']
};

function setup() {
  const ss = SpreadsheetApp.getActive();
  Object.keys(SH).forEach(k => {
    let sh = ss.getSheetByName(SH[k]);
    if (!sh) sh = ss.insertSheet(SH[k]);
    sh.getRange(1, 1, 1, HEAD[k].length).setValues([HEAD[k]]).setFontWeight('bold').setBackground('#E1EFEA');
    sh.setFrozenRows(1);
  });
  const def = ss.getSheetByName('시트1') || ss.getSheetByName('Sheet1');
  if (def && ss.getSheets().length > 3) ss.deleteSheet(def);
}

function sheet_(k) {
  const ss = SpreadsheetApp.getActive();
  let sh = ss.getSheetByName(SH[k]);
  if (!sh) { setup(); sh = ss.getSheetByName(SH[k]); }
  return sh;
}
function out_(obj) { return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON); }
function now_() { return Utilities.formatDate(new Date(), 'Asia/Seoul', 'yyyy-MM-dd HH:mm:ss'); }
function prop_(k, d) { return PropertiesService.getScriptProperties().getProperty(k) || d; }

// ───────── GET: 오답 목록 / 교사 현황 ─────────
function doGet(e) {
  const p = e.parameter || {};
  try {
    if (p.action === 'wrong') return out_({ ok: true, wrong: wrongList_(String(p.sid || '')) });
    if (p.action === 'summary') {
      if (!p.pin || p.pin !== prop_('TEACHER_PIN', '')) return out_({ ok: false, error: 'PIN이 맞지 않습니다.' });
      return out_(summary_(String(p.set || '')));
    }
    return out_({ ok: true, msg: 'HSK backend is running', ai: !!prop_('GEMINI_API_KEY', '') });
  } catch (err) { return out_({ ok: false, error: String(err) }); }
}

function wrongList_(sid) {
  const v = sheet_('ans').getDataRange().getValues();
  const last = {}; // set -> item -> 'O'/'X'
  for (let i = 1; i < v.length; i++) {
    const r = v[i];
    if (String(r[1]) !== sid || (r[10] !== 'O' && r[10] !== 'X')) continue;
    (last[r[3]] = last[r[3]] || {})[r[5]] = r[10];
  }
  const res = {};
  Object.keys(last).forEach(set => { res[set] = Object.keys(last[set]).filter(id => last[set][id] === 'X'); });
  return res;
}

function summary_(set) {
  const sv = sheet_('sub').getDataRange().getValues();
  const latest = {};
  for (let i = 1; i < sv.length; i++) {
    const r = sv[i]; if (r[3] !== set) continue;
    const prev = latest[r[1]];
    if (r[4] === 'retry') { if (prev) prev.retry = (prev.retry || 0) + 1; else latest[r[1]] = { sid: String(r[1]), name: r[2], mode: '오답만', score: r[6], total: r[7], time: String(r[0]).slice(5, 16), retry: 1 }; continue; }
    latest[r[1]] = { sid: String(r[1]), name: r[2], mode: SCOPE_KO[r[5]] || r[5], score: r[6], total: r[7], L: r[9], R: r[10], W: r[11], time: String(r[0]).slice(5, 16), retry: prev ? prev.retry || 0 : 0 };
  }
  // 문항 통계: 학생별 ‘처음 푼(test 모드) 마지막 응답’ 기준
  const av = sheet_('ans').getDataRange().getValues();
  const seen = {};
  for (let i = 1; i < av.length; i++) {
    const r = av[i]; if (r[3] !== set || r[4] !== 'test' || (r[10] !== 'O' && r[10] !== 'X')) continue;
    seen[r[1] + '|' + r[5]] = { id: r[5], ok: r[10] === 'O' };
  }
  const items = {};
  Object.keys(seen).forEach(k => { const s = seen[k]; const it = items[s.id] = items[s.id] || { n: 0, wrong: 0 }; it.n++; if (!s.ok) it.wrong++; });
  const students = Object.keys(latest).map(k => latest[k]).sort((a, b) => a.sid < b.sid ? -1 : 1);
  return { ok: true, students: students, items: items };
}

// ───────── POST: 제출 / 피드백 ─────────
function doPost(e) {
  let p;
  try { p = JSON.parse(e.postData.contents); } catch (err) { return out_({ ok: false, error: 'bad json' }); }
  try {
    if (p.action === 'submit') return out_(submit_(p));
    if (p.action === 'feedback') return out_(feedback_(p));
    return out_({ ok: false, error: 'unknown action' });
  } catch (err) { return out_({ ok: false, error: String(err) }); }
}

function submit_(p) {
  const lock = LockService.getScriptLock(); lock.waitLock(20000);
  try {
    const t = now_(), per = p.per || {};
    const f = k => per[k] ? per[k].c + '/' + per[k].t : '';
    const wrong = (p.answers || []).filter(a => a.ok === false).map(a => a.id).join(' ');
    sheet_('sub').appendRow([t, p.sid, p.name, p.setId, p.mode, p.scope, p.score, p.total, p.total ? Math.round(p.score / p.total * 100) / 100 : '', f('L'), f('R'), f('W'), Math.round((p.durationSec || 0) / 6) / 10, wrong]);
    const rows = (p.answers || []).map(a => [t, p.sid, p.name, p.setId, p.mode, a.id, a.sec, a.part, String(a.resp).slice(0, 2000), a.key, a.ok === true ? 'O' : a.ok === false ? 'X' : '', a.score == null ? '' : a.score]);
    if (rows.length) { const sh = sheet_('ans'); sh.getRange(sh.getLastRow() + 1, 1, rows.length, rows[0].length).setValues(rows); }
    sheet_('sub').getRange(sheet_('sub').getLastRow(), 9).setNumberFormat('0%');
  } finally { lock.releaseLock(); }
  return { ok: true };
}

function feedback_(p) {
  let fb = null, err = '';
  if (p.ai) {
    try { fb = gemini_(p); } catch (e) { err = String(e); }
  }
  const lock = LockService.getScriptLock(); lock.waitLock(20000);
  try {
    sheet_('fb').appendRow([now_(), p.sid, p.name, p.setId, p.itemId, p.kind, String(p.task || '').slice(0, 200), String(p.response || '').slice(0, 5000),
      fb ? fb.score : (p.score === '' ? '' : p.score), fb ? fb.summary : (err ? 'AI 오류: ' + err.slice(0, 200) : ''), fb ? JSON.stringify(fb) : '']);
  } finally { lock.releaseLock(); }
  return { ok: true, feedback: fb, error: err };
}

const KIND_DESC = {
  picture: '그림(장면)을 보고 제시어를 사용해 한 문장 쓰기 (HSK 4급 쓰기 제2부분)',
  essay: '80자 내외의 짧은 글쓰기 (HSK 5급 쓰기 제2부분)',
  summary: '약 1000자 원문을 읽고 400자 내외로 축약하기(缩写, HSK 6급 쓰기). 원문 내용의 충실한 재현이 가장 중요하며, 제목이 있어야 하고, 자신의 의견을 넣으면 안 된다.',
  speak: '질문 또는 그림에 대해 구술로 답하기 (HSKK 스타일 말하기)',
  retell: '들은 이야기를 자신의 말로 다시 말하기(复述). 원문 내용을 빠짐없이 순서대로 전달했는지가 중요하다.'
};

function gemini_(p) {
  const key = prop_('GEMINI_API_KEY', '');
  if (!key) return null;
  const model = prop_('GEMINI_MODEL', 'gemini-2.5-flash');
  const spoken = p.kind === 'speak' || p.kind === 'retell';
  const lines = [
    '너는 한국 대학생(사이버한국외대 중국어 전공)에게 HSK ' + p.level + '급을 가르치는 친절하고 정확한 중국어 교사다.',
    '학생 답안을 평가하고, 설명은 한국어로, 예문과 수정문은 간체 중국어로 써라.',
    '과제 유형: ' + (KIND_DESC[p.kind] || p.kind),
    p.task ? '과제/질문: ' + p.task : '',
    p.word ? '제시어: ' + p.word : '',
    (p.words && p.words.length) ? '제시어(모두 사용해야 함): ' + p.words.join('、') : '',
    (p.min || p.max) ? '권장 분량: ' + p.min + '~' + p.max + '자' : '',
    p.source ? '원문:\n"""' + String(p.source).slice(0, 2500) + '"""' : '',
    p.sample ? '참고용 모범 답안(그대로 강요하지 말 것):\n"""' + p.sample + '"""' : '',
    '학생 답안:\n"""' + p.response + '"""',
    spoken ? '주의: 이 답안은 브라우저 음성 인식으로 받아 적은 텍스트다. 동음이의어 오인식이나 문장부호 누락은 감점하지 말고, 문법·어휘·내용·논리 구성을 평가하라.' : '',
    '평가 기준: HSK ' + p.level + '급 수준에 맞는 ① 문법 정확성 ② 어휘의 적절성과 다양성 ③ 과제 충족(제시어·분량·내용) ④ 구성과 연결 표현.',
    '반드시 아래 JSON만 출력하라.',
    '{"score": 0~100 정수, "level": "HSK ' + p.level + '급 기준 한 줄 평가", "summary": "총평 2문장", "strengths": ["잘한 점"], "corrections": [{"wrong": "학생 원문 일부", "right": "수정한 중국어", "reason": "한국어 설명"}], "improved": "학생 답안의 내용을 살려 자연스럽게 다듬은 중국어 전체", "tips": ["다음에 연습할 점 1~2개"]}',
    'corrections는 실제 오류만 최대 5개. 오류가 없으면 빈 배열.'
  ].filter(Boolean).join('\n\n');
  const res = UrlFetchApp.fetch('https://generativelanguage.googleapis.com/v1beta/models/' + model + ':generateContent?key=' + encodeURIComponent(key), {
    method: 'post', contentType: 'application/json', muteHttpExceptions: true,
    payload: JSON.stringify({ contents: [{ role: 'user', parts: [{ text: lines }] }], generationConfig: { temperature: 0.3, responseMimeType: 'application/json' } })
  });
  if (res.getResponseCode() !== 200) throw new Error('Gemini ' + res.getResponseCode() + ': ' + res.getContentText().slice(0, 300));
  const j = JSON.parse(res.getContentText());
  const txt = j.candidates[0].content.parts.map(x => x.text || '').join('');
  const fb = JSON.parse(txt.replace(/^```json\s*|```$/g, ''));
  fb.score = Math.max(0, Math.min(100, parseInt(fb.score, 10) || 0));
  return fb;
}

/** 시트에서 바로 확인용: 실행하면 Gemini 연결을 테스트합니다. */
function testGemini() {
  Logger.log(JSON.stringify(gemini_({ level: 4, kind: 'picture', word: '帮助', task: '学生帮老奶奶拿东西', response: '他帮助老奶奶拿东西了很重。', sample: '' }), null, 2));
}
