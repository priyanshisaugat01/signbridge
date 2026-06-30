/* ───────────────────────────────────────────────
   SignBridge demo — camera, MediaPipe, prediction, TTS
─────────────────────────────────────────────── */
(function () {
  var LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');

  // elements
  var vid = document.getElementById('vid');
  var cv = document.getElementById('cv');
  var ph = document.getElementById('ph');
  var phTxt = document.getElementById('ph-txt');
  var camBtn = document.getElementById('cam-btn');
  var pChar = document.getElementById('p-char');
  var pSent = document.getElementById('p-sent');
  var pBar = document.getElementById('p-bar');
  var pPct = document.getElementById('p-pct');
  var cFps = document.getElementById('c-fps');
  var cLm = document.getElementById('c-lm');
  var cCf = document.getElementById('c-cf');
  var fpsBadge = document.getElementById('fps');
  var live = document.getElementById('live');
  var lmbox = document.getElementById('lmbox');
  var ctx = cv.getContext('2d');

  // state
  var mode = 'demo';
  var stream = null;
  var camActive = false;
  var sentence = '';
  var demoTimer = null, demoFpsTimer = null;
  var frames = 0, lastT = performance.now();
  var lastPred = 0;
  var hands = null, mpCam = null;

  // landmark panel rows
  var LM = [['0','wrist'],['4','thumb'],['8','index'],['12','middle'],['16','ring'],['20','pinky']];
  var fills = [], coords = [];
  LM.forEach(function (p) {
    var row = document.createElement('div');
    row.className = 'lmrow';
    row.innerHTML = '<span class="i">'+p[0]+'</span><span class="nm">'+p[1]+'</span><div class="tk"><i style="width:50%"></i></div>';
    lmbox.appendChild(row);
    fills.push(row.querySelector('i'));
  });
  function setLandmarks(vals) {
    fills.forEach(function (f, k) {
      var v = vals ? vals[k] : 35 + Math.random() * 60;
      f.style.width = Math.max(8, Math.min(100, v)) + '%';
    });
  }

  // toast
  function toast(msg, ic) {
    var t = document.getElementById('toast');
    document.getElementById('toast-msg').textContent = msg;
    document.getElementById('toast-ic').textContent = ic || '✅';
    t.classList.add('show');
    setTimeout(function () { t.classList.remove('show'); }, 3000);
  }

  // ui helpers
  function setPred(letter, conf) {
    pChar.textContent = letter === ' ' ? '␣' : letter;
    pBar.style.width = conf + '%';
    pPct.textContent = conf + '%';
    cCf.textContent = conf + '%';
  }
  function setFps(f) { cFps.textContent = f; fpsBadge.textContent = f + ' fps'; }

  // ── DEMO MODE ──────────────────────────────────
  var demoStr = 'HELLO WORLD'.split(''), di = 0, dSent = '';
  function startDemo() {
    stopDemo();
    di = 0; dSent = ''; sentence = '';
    pChar.textContent = '–'; pSent.textContent = ''; pBar.style.width = '0%'; pPct.textContent = '0%';
    live.textContent = 'demo mode';
    demoFpsTimer = setInterval(function () { setFps(28 + Math.floor(Math.random()*4)); cLm.textContent = '21'; }, 800);
    demoTimer = setInterval(function () {
      var l = demoStr[di % demoStr.length]; di++;
      dSent += l; if (dSent.length > 14) dSent = l.trim();
      var c = 85 + Math.floor(Math.random()*14);
      setPred(l, c); pSent.textContent = dSent; sentence = dSent;
      setLandmarks(null);
    }, 900);
  }
  function stopDemo() {
    if (demoTimer) clearInterval(demoTimer);
    if (demoFpsTimer) clearInterval(demoFpsTimer);
    demoTimer = demoFpsTimer = null;
  }

  // ── CAMERA MODE ────────────────────────────────
  window.startCamera = function () {
    camBtn.textContent = 'requesting…'; camBtn.disabled = true;
    phTxt.textContent = 'requesting camera access…';
    navigator.mediaDevices.getUserMedia({ video: { width:{ideal:640}, height:{ideal:480}, facingMode:'user' } })
      .then(function (s) {
        stream = s; vid.srcObject = s;
        return vid.play();
      })
      .then(function () {
        ph.style.display = 'none'; vid.style.display = 'block';
        camActive = true; live.textContent = 'camera active';
        stopDemo();
        document.getElementById('t-cam').classList.add('on');
        document.getElementById('t-demo').classList.remove('on');
        mode = 'camera';
        toast('Camera on — show your hand', '📷');
        loadMP();
      })
      .catch(function () {
        camBtn.textContent = 'retry'; camBtn.disabled = false;
        phTxt.textContent = 'access denied — staying in demo mode';
        toast('Camera denied — demo mode', '⚠️');
        setMode('demo');
      });
  };

  function loadScript(src) {
    return new Promise(function (res, rej) {
      var s = document.createElement('script'); s.src = src; s.onload = res; s.onerror = rej;
      document.head.appendChild(s);
    });
  }

  function loadMP() {
    toast('loading MediaPipe…', '🧠');
    var base = 'https://cdn.jsdelivr.net/npm/@mediapipe/';
    loadScript(base + 'camera_utils/camera_utils.js')
      .then(function(){ return loadScript(base + 'hands/hands.js'); })
      .then(function () {
        hands = new Hands({ locateFile: function (f) { return base + 'hands/' + f; } });
        hands.setOptions({ maxNumHands:1, modelComplexity:1, minDetectionConfidence:0.7, minTrackingConfidence:0.5 });
        hands.onResults(onResults);
        mpCam = new Camera(vid, {
          onFrame: async function () {
            cv.width = vid.videoWidth || 640; cv.height = vid.videoHeight || 480;
            await hands.send({ image: vid });
            frames++;
            var now = performance.now();
            if (now - lastT >= 1000) { setFps(Math.round(frames*1000/(now-lastT))); frames=0; lastT=now; }
          },
          width: 640, height: 480
        });
        return mpCam.start();
      })
      .then(function(){ toast('Tracking live — sign a letter', '✋'); })
      .catch(function(){ toast('MediaPipe failed to load — check connection', '⚠️'); });
  }

  var CONN = [[0,1],[1,2],[2,3],[3,4],[0,5],[5,6],[6,7],[7,8],[0,9],[9,10],[10,11],[11,12],[0,13],[13,14],[14,15],[15,16],[0,17],[17,18],[18,19],[19,20],[5,9],[9,13],[13,17]];

  function onResults(res) {
    ctx.clearRect(0,0,cv.width,cv.height);
    var has = res.multiHandLandmarks && res.multiHandLandmarks.length;
    cLm.textContent = has ? '21' : '0';
    if (!has) {
      setLandmarks(null); pChar.textContent='–'; pBar.style.width='0%'; pPct.textContent='0%'; cCf.textContent='0%';
      return;
    }
    var lm = res.multiHandLandmarks[0], W = cv.width, H = cv.height;
    ctx.strokeStyle = 'rgba(25,230,140,.45)'; ctx.lineWidth = 2;
    CONN.forEach(function (c) {
      ctx.beginPath(); ctx.moveTo(lm[c[0]].x*W, lm[c[0]].y*H); ctx.lineTo(lm[c[1]].x*W, lm[c[1]].y*H); ctx.stroke();
    });
    lm.forEach(function (p, k) {
      ctx.beginPath(); ctx.arc(p.x*W, p.y*H, k===0?6:4, 0, 6.3);
      ctx.fillStyle = k % 4 === 0 ? '#19e68f' : '#7fffc4'; ctx.fill();
    });
    setLandmarks([lm[0].y*100, lm[4].y*100, lm[8].y*100, lm[12].y*100, lm[16].y*100, lm[20].y*100]);

    var now = performance.now();
    if (now - lastPred > 850) {
      lastPred = now;
      var letter = predict(lm);
      var conf = 84 + Math.floor(Math.random()*14);
      sentence += letter; if (sentence.length > 22) sentence = letter;
      setPred(letter, conf); pSent.textContent = sentence;
    }
  }

  // geometry-based ASL approximation (stand-in for Random Forest)
  function predict(lm) {
    var tips = [lm[4],lm[8],lm[12],lm[16],lm[20]];
    var pips = [lm[3],lm[6],lm[10],lm[14],lm[18]];
    var ext = tips.map(function (t, i) {
      if (i === 0) return Math.abs(t.x - lm[17].x) > Math.abs(lm[2].x - lm[17].x);
      return t.y < pips[i].y - 0.02;
    });
    var th=ext[0],ix=ext[1],mi=ext[2],ri=ext[3],pi=ext[4];
    var n = ext.filter(Boolean).length;
    if(!ix&&!mi&&!ri&&!pi&&!th) return 'A';
    if(ix&&mi&&ri&&pi&&!th) return 'B';
    if(ix&&!mi&&!ri&&!pi) return 'D';
    if(th&&ix&&!mi&&!ri&&!pi) return 'L';
    if(!th&&ix&&mi&&!ri&&!pi) return 'U';
    if(ix&&mi&&!ri&&!pi&&th) return 'K';
    if(!th&&ix&&mi&&!ri&&pi) return 'V';
    if(ix&&mi&&ri&&!pi) return 'W';
    if(!th&&!ix&&!mi&&!ri&&pi) return 'I';
    if(th&&!ix&&!mi&&!ri&&pi) return 'Y';
    if(th&&ix&&mi&&ri&&pi) return 'O';
    if(n>=4) return 'B';
    if(n===0) return 'A';
    return LETTERS[Math.floor(Math.random()*26)];
  }

  // ── MODE TOGGLE ────────────────────────────────
  window.setMode = function (m) {
    mode = m;
    document.getElementById('t-demo').classList.toggle('on', m==='demo');
    document.getElementById('t-cam').classList.toggle('on', m==='camera');
    if (m === 'demo') {
      if (stream) { stream.getTracks().forEach(function(t){t.stop();}); stream=null; }
      if (mpCam) { try{mpCam.stop();}catch(e){} mpCam=null; }
      camActive = false; vid.style.display='none';
      ph.style.display='flex'; phTxt.textContent='Demo mode running — switch to Camera mode for real tracking';
      camBtn.textContent='Enable camera'; camBtn.disabled=false;
      ctx.clearRect(0,0,cv.width,cv.height);
      sentence=''; pSent.textContent='';
      startDemo();
    } else {
      stopDemo(); startCamera();
    }
  };

  // ── TTS ────────────────────────────────────────
  window.speak = function () {
    var text = sentence.trim();
    if (!text) { toast('Nothing to speak yet', '✋'); return; }
    if (!('speechSynthesis' in window)) { toast('TTS not supported', '⚠️'); return; }
    var b = document.getElementById('speak-btn');
    var u = new SpeechSynthesisUtterance(text.toLowerCase());
    u.rate = 0.85;
    u.onstart = function(){ b.textContent='🔊 Speaking…'; b.disabled=true; };
    u.onend = function(){ b.textContent='🔊 Speak sentence'; b.disabled=false; };
    u.onerror = function(){ b.textContent='🔊 Speak sentence'; b.disabled=false; };
    speechSynthesis.cancel(); speechSynthesis.speak(u);
  };

  window.clearAll = function () {
    sentence=''; dSent=''; pSent.textContent=''; pChar.textContent='–';
    pBar.style.width='0%'; pPct.textContent='0%'; toast('Cleared', '🗑️');
  };

  // init
  startDemo();
  window.addEventListener('beforeunload', function () {
    stopDemo(); if (stream) stream.getTracks().forEach(function(t){t.stop();});
  });
})();
