# 이 웹앱을 다른 시험(예: 학부 레벨테스트)으로 바꾸는 안내

다른 AI(Gemini 등)에게 이 파일과 `index.html`, `data/practice/p4a.js`를 함께 주고 "이 구조 그대로 ○○ 시험을 만들어 줘"라고 하면 됩니다.

## 1. 전체 구조
| 파일 | 역할 | 바꿀 필요 |
|---|---|---|
| `index.html` | 화면·채점·로그인·오답노트·재강의 전부 (한 파일, 순수 JS) | 제목/문구 정도만 |
| `config.js` | Apps Script 웹 앱 주소(`SCRIPT_URL`), 반 이름 등 | 새 시트를 쓰면 주소 교체 |
| `data/*.js` | **문제 데이터**. 세트 하나 = 파일 하나 | **여기만 새로 만들면 됨** |
| `index.html`의 `<script src="data/...">` 목록 | 어떤 세트 파일을 불러올지 | 새 파일명으로 교체 |
| `apps-script/Code.gs` | 구글시트 저장·로그인·오답·AI 해설 서버 | 그대로 재사용 가능 |
| `audio/<세트id>/<문항id>.mp3` | 듣기 음성 | 듣기 문항이 있으면 새로 생성 |
| `tools/` | PDF→데이터 변환, 검사, 음성 생성 스크립트 | 선택 |

## 2. 세트 파일 형식
```js
window.HSK_SETS = window.HSK_SETS || [];
HSK_SETS.push({
  id: 'lt1',            // 세트 고유 ID (오디오 폴더 이름과 같아야 함)
  level: 4,             // 숫자. 레벨테스트면 1, 2... 아무 숫자나 가능
  label: '1회', source: 'CUFS', title: '학부 레벨테스트 1회',
  corner: 'exam',       // 'exam'이면 실전 모의고사 코너, 빼면 수업용 요약본 코너
  minutes: { L: 20, R: 30, W: 20 },   // 영역별 제한 시간(표시용)
  sections: [
    { key: 'L', name: '听力', ko: '듣기', parts: [ /* 아래 유형들 */ ] },
    { key: 'R', name: '阅读', ko: '독해', parts: [] },
    { key: 'W', name: '书写', ko: '쓰기', parts: [] },
    { key: 'S', name: '口语', ko: '말하기', parts: [] }
  ]
});
```
규칙: 문항 `id` 첫 글자 = 영역(L/R/W/S), 한 세트 안에서 중복 금지. 객관식 정답은 `'A'~'F'` 글자.

## 3. 문항 유형 (part.type) 예시
```js
// 듣기 O/X
{type:'tf', title:'第一部分', ko:'안내문', items:[{id:'L1', script:'녹음 원문', stem:'★ 문장', ans:'√'}]}
// 듣기 객관식
{type:'lmc', title:'', ko:'', items:[{id:'L11', script:'男：…\n女：…\n问：…', opts:['','','',''], ans:'B', exp:'해설(선택)'}]}
// 듣기 지문 하나에 여러 문제
{type:'lgroup', groups:[{id:'L36', script:'지문', items:[{id:'L36', q:'질문', opts:[...], ans:'B'}, {id:'L37', ...}]}]}
// 독해 단어 고르기(보기 은행)
{type:'bank', bank:{A:'适合',B:'终于',C:'负责',D:'习惯',E:'邀请',F:'认真'}, items:[{id:'R46', text:'…（　　）…', ans:'A'}]}
// 문장 순서
{type:'order', items:[{id:'R56', segs:['문장A','문장B','문장C'], ans:'CAB'}]}
// 독해 객관식
{type:'rmc', items:[{id:'R66', passage:'지문', q:'질문', opts:[...], ans:'A'}]}
// 독해 지문 하나에 여러 문제
{type:'rgroup', groups:[{id:'R80', passage:'지문', items:[{id:'R80', q:'', opts:[], ans:'A'}]}]}
// 빈칸 채우기(지문 속 (R1) 자리)
{type:'cloze', groups:[{id:'R1', passage:'…（R1）…（R2）…', items:[{id:'R1', opts:[], ans:'D', exp:''}]}]}
// 틀린 문장 고르기
{type:'error', items:[{id:'R51', opts:['문장1','문장2','문장3','문장4'], ans:'A'}]}
// 빈칸 여러 개 조합
{type:'multi', items:[{id:'R61', text:'…＿＿＿…＿＿＿…', opts:['a　b','c　d','e　f','g　h'], ans:'D'}]}
// 문장 고르기(보기 은행, 지문)
{type:'sentfill', groups:[{id:'R71', passage:'…（R71）…', bank:{A:'',B:'',C:'',D:'',E:''}, items:[{id:'R71', ans:'C'}]}]}
// 쓰기: 단어 배열 (정답 여러 개 가능)
{type:'arrange', items:[{id:'W86', words:['已经','我','这本小说','看完','了'], ans:['我已经看完这本小说了。']}]}
// 쓰기: 그림(장면) 보고 문장
{type:'picture', items:[{id:'W96', word:'安静', emoji:'📚🤫', scene:'장면 설명(한국어)', sample:'모범 답안'}]}
// 쓰기: 단어로 짧은 글
{type:'essay', items:[{id:'W5', words:['毕业','紧张'], min:70, max:110, sample:'모범 답안'}]}
// 쓰기: 읽고 요약
{type:'summary', items:[{id:'W101', read:600, min:350, max:500, text:'원문'}]}
// 말하기: 따라 말하기 / 장면 보고 말하기
{type:'repeat', items:[{id:'S1', text:'문장'}]}
{type:'speak', items:[{id:'S2', emoji:'', prompt:'请…', ko:'장면 설명', sec:60, sample:'모범 답안'}]}
```
(이 밖에 `read`, `retell` 유형도 있습니다. `index.html`에서 `case 'retell'` 등을 검색하면 형식이 보입니다.)

## 4. 새 시험으로 바꾸는 순서
1. `data/` 안에 새 세트 파일(예: `data/lt1.js`)을 위 형식대로 만든다.
2. `index.html` 아래쪽 `<script src="data/...">` 줄을 새 파일로 바꾼다.
3. 화면 제목: `index.html`에서 "HSK 방학 특강" 문구, 급수 표기(4·5·6급) 문구를 검색해 바꾼다.
4. 검사: `node tools/check_data.js`, `node tools/check_practice.js` (정답 범위·ID 중복 확인).
5. 듣기가 있으면 `python3 tools/make_audio.py` 로 음성 생성 (README 5장).
6. 기록을 따로 받으려면 새 구글시트 → 확장 프로그램 → Apps Script에 `apps-script/Code.gs` 붙여넣기 → `setup` 실행 → 스크립트 속성(TEACHER_PIN, GEMINI_API_KEY) → 웹 앱 배포 → 주소를 `config.js`에 넣기 (README 2장).
7. GitHub에 새 저장소로 올리고 Pages 켜기 (README 1장).

## 5. 주의
- 데이터 파일은 반드시 `HSK_SETS.push({...})` 형태 유지 (이름을 바꾸면 화면에 안 나옴).
- 세트 `id`를 바꾸면 이전 기록과 연결이 끊김. 운영 중에는 바꾸지 말 것.
- 정답이 하나만 맞도록, 보기 중복이 없도록 꼭 다시 확인할 것.
