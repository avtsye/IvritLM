(() => {
  "use strict";
  const OWNER = "avtsye", REPO = "IvritLM";
  const SOURCE_WORKFLOW = "train.yml", PRETRAIN_WORKFLOW = "pretrain.yml";
  const API = "/api";
  const $ = (id) => document.getElementById(id);
  let adminKey = "";
  $("corpus-approved").checked = false;
  $("chat-data-approved").checked = false;
  const form = $("train-form"), submit = $("submit-btn"), message = $("form-message"), runs = $("runs");
  const pretrainForm = $("pretrain-form"), pretrainButton = $("pretrain-btn"), pretrainMessage = $("pretrain-message");

  function say(text, error = false) {
    message.textContent = text;
    message.classList.toggle("error", error);
  }
  function sayPretrain(text, error = false) {
    pretrainMessage.textContent = text;
    pretrainMessage.classList.toggle("error", error);
  }
  function headers() {
    return {"Content-Type":"application/json","X-Admin-Key":adminKey};
  }
  function validateSource(raw, kind) {
    let u;
    try { u = new URL(raw); } catch { throw new Error("יש להזין כתובת URL תקינה."); }
    if (u.protocol !== "https:" || u.username || u.password) throw new Error("נדרשת כתובת HTTPS ציבורית ללא פרטי התחברות.");
    if (kind === "github" || (kind === "auto" && u.hostname === "github.com")) {
      if (u.hostname !== "github.com" || !/^\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+\/?$/.test(u.pathname)) {
        throw new Error("יש להזין כתובת מאגר GitHub בפורמט owner/repository.");
      }
      return {url:"https://github.com"+u.pathname.replace(/\/$/, ""),kind:"github"};
    }
    if (kind === "web" || kind === "auto") {
      if (u.hostname === "github.com") throw new Error("בחר בסוג מאגר GitHub עבור כתובת זו.");
      return {url:u.href,kind:"web"};
    }
    throw new Error("סוג מקור לא מוכר.");
  }
  async function request(path, options = {}) {
    const response = await fetch(API+path,{...options,headers:{...headers(),...(options.headers||{})}});
    let data = {};
    try { data = await response.json(); } catch {}
    if (!response.ok) {
      if (response.status === 401) throw new Error("סיסמת הניהול שגויה או שפג תוקפה.");
      throw new Error(data.error || "שגיאת שרת ("+response.status+").");
    }
    return data;
  }
  async function dispatchWorkflow(workflow, inputs) {
    return request("/dispatch", {method:"POST",body:JSON.stringify({workflow,inputs})});
  }
  function render(items) {
    runs.replaceChildren();
    if (!items.length) {
      const p = document.createElement("p");
      p.className = "empty";
      p.textContent = "לא נמצאו ריצות עדיין.";
      runs.append(p);
      return;
    }
    for (const item of items) {
      const row = document.createElement("div");
      row.className = "run";
      const left = document.createElement("div"), title = document.createElement("div"), a = document.createElement("a"), meta = document.createElement("div");
      title.className = "run-title";
      a.href = item.html_url;
      a.target = "_blank";
      a.rel = "noreferrer";
      a.textContent = item.display_title || item.name || "IvritLM workflow";
      title.append(a);
      meta.className = "run-meta";
      meta.textContent = "#"+item.run_number+" · "+new Date(item.created_at).toLocaleString("he-IL");
      left.append(title,meta);
      const state = document.createElement("span");
      state.className = "run-state "+(item.conclusion || item.status || "queued");
      state.textContent = item.conclusion || item.status || "unknown";
      row.append(left,state);
      runs.append(row);
    }
  }
  async function loadRuns() {
    adminKey = $("admin-key").value;
    if (!adminKey) {
      runs.textContent = "יש להזין סיסמת ניהול כדי לקרוא את היסטוריית הריצות.";
      runs.className = "empty";
      return;
    }
    runs.textContent = "טוען ריצות…";
    runs.className = "empty";
    try {
      const data = await request("/runs");
      runs.className = "";
      render(data.workflow_runs || []);
    } catch (e) {
      runs.textContent = e.message;
      runs.className = "empty";
    }
  }

  $("clear-key").addEventListener("click", () => {
    adminKey = "";
    $("admin-key").value = "";
    runs.textContent = "סיסמת הניהול נוקתה מהזיכרון.";
    runs.className = "empty";
    say("החיבור נותק.");
    sayPretrain("החיבור נותק.");
  });
  $("refresh-runs").addEventListener("click", loadRuns);

  const textForm = $("text-form");
  const textArea = $("training-text");
  const textFile = $("text-file");
  const textButton = $("text-submit-btn");
  const textMessage = $("text-message");
  function sayText(value, error = false) {
    textMessage.textContent = value;
    textMessage.classList.toggle("error", error);
  }
  textFile.addEventListener("change", async () => {
    const file = textFile.files && textFile.files[0];
    if (!file) return;
    if (!/\.txt$/i.test(file.name) && file.type !== "text/plain") {
      sayText("יש לבחור קובץ TXT בלבד.", true); textFile.value = ""; return;
    }
    if (file.size > 5 * 1024 * 1024) {
      sayText("הקובץ גדול מ־5 MiB. יש לבחור קובץ קטן יותר.", true); textFile.value = ""; return;
    }
    try {
      const content = await file.text();
      if (content.length > 40000) {
        textArea.value = content.slice(0, 40000);
        sayText("הקובץ נטען חלקית: מגבלת ההזנה הישירה היא 40,000 תווים.", true);
      } else {
        textArea.value = content;
        sayText("הקובץ נטען. אפשר לבדוק את הטקסט ולשמור אותו במאגר.");
      }
    } catch {
      sayText("לא ניתן לקרוא את הקובץ. יש לוודא שהוא קובץ טקסט UTF-8.", true);
    }
  });
  textForm.addEventListener("submit", async event => {
    event.preventDefault();
    sayText("");
    adminKey = $("admin-key").value;
    if (!adminKey) { sayText("יש להזין תחילה סיסמת ניהול.", true); return; }
    const content = textArea.value.trim();
    if (content.length < 100) { sayText("יש להזין לפחות 100 תווים.", true); return; }
    if (content.length > 40000) { sayText("מגבלת ההזנה היא 40,000 תווים לריצה.", true); return; }
    if (!$("text-license-ack").checked) {
      sayText("יש לאשר שיש לך הרשאה להשתמש בטקסט לאימון.", true); return;
    }
    $("corpus-approved").checked = false;
    textButton.disabled = true;
    textButton.querySelector("span").textContent = "שומר ב־Google Drive…";
    try {
      await dispatchWorkflow("ingest-text.yml", {text_content:content, license_ack:"yes"});
      sayText("הטקסט התקבל. המערכת בונה קורפוס עברי ושומרת אותו ב־Google Drive. לאחר מכן אפשר להפעיל אימון.");
      textArea.value = "";
      textFile.value = "";
      $("text-license-ack").checked = false;
      setTimeout(loadRuns, 2500);
    } catch (e) { sayText(e.message, true); }
    finally {
      textButton.disabled = false;
      textButton.querySelector("span").textContent = "שמירת הטקסט במאגר האימון";
    }
  });

  form.addEventListener("submit", async event => {
    event.preventDefault();
    say("");
    adminKey = $("admin-key").value;
    if (!adminKey) { say("יש להזין סיסמת ניהול.", true); return; }
    let source;
    try { source = validateSource($("source-url").value.trim(), $("source-kind").value); }
    catch (e) { say(e.message, true); return; }
    if (!$("license-ack").checked || !$("public-ack").checked) {
      say("יש לאשר את שתי הצהרות המקור.", true);
      return;
    }
    $("corpus-approved").checked = false;
    submit.disabled = true;
    submit.querySelector("span").textContent = "שולח ל־GitHub…";
    try {
      await dispatchWorkflow(SOURCE_WORKFLOW, {source_url:source.url,source_kind:source.kind,license_ack:"yes"});
      say("הסריקה התקבלה. הקורפוס יישמר ב־Google Drive כמועמד לאימון. יש לבדוק את זכויות המקור ואת התוכן לפני הפעלת אימון ידנית.");
      setTimeout(loadRuns, 2500);
    } catch (e) { say(e.message, true); }
    finally {
      submit.disabled = false;
      submit.querySelector("span").textContent = "סריקה ושמירת קורפוס לבדיקה";
    }
  });


  const chatForm = $("chat-form");
  const chatButton = $("chat-submit-btn");
  const chatMessage = $("chat-message");
  function sayChat(value, error = false) {
    chatMessage.textContent = value;
    chatMessage.classList.toggle("error", error);
  }
  chatForm.addEventListener("submit", async event => {
    event.preventDefault();
    sayChat("");
    adminKey = $("admin-key").value;
    if (!adminKey) { sayChat("יש להזין תחילה סיסמת ניהול.", true); return; }
    const raw = $("chat-jsonl").value.trim();
    if (!$("chat-data-approved").checked) { sayChat("יש לאשר שיש לך הרשאה להשתמש בדוגמאות השיחה לאימון.", true); return; }
    if (!raw || raw.length > 60000) { sayChat("יש להזין נתוני JSONL עד 60,000 תווים.", true); return; }
    const rows = raw.split(/\r?\n/).filter(line => line.trim());
    try {
      if (!rows.length) throw new Error("לא נמצאו שיחות.");
      for (let i = 0; i < rows.length; i++) {
        const item = JSON.parse(rows[i]);
        if (!item || !Array.isArray(item.messages) || item.messages.length < 2) throw new Error("שורה " + (i + 1) + ": נדרש messages עם לפחות שתי הודעות.");
        let last = "";
        for (const message of item.messages) {
          if (!message || !["system","user","assistant"].includes(message.role) || typeof message.content !== "string" || !message.content.trim()) throw new Error("שורה " + (i + 1) + ": הודעה לא תקינה.");
          if (last === message.role && message.role !== "system") throw new Error("שורה " + (i + 1) + ": יש להחליף בין user ל-assistant.");
          last = message.role;
        }
        if (last !== "assistant") throw new Error("שורה " + (i + 1) + ": כל שיחה חייבת להסתיים בתשובת assistant.");
      }
    } catch (e) { sayChat("בדיקת הנתונים נכשלה: " + e.message, true); return; }
    const steps = Number($("chat-steps").value), batch = Number($("chat-batch").value);
    if (!Number.isInteger(steps) || steps < 1 || steps > 1000 || !Number.isInteger(batch) || batch < 1 || batch > 16) {
      sayChat("צעדי האימון חייבים להיות 1–1,000 ו-Batch size חייב להיות 1–16.", true); return;
    }
    $("chat-data-approved").checked = false;
    chatButton.disabled = true;
    chatButton.querySelector("span").textContent = "מפעיל אימון שיחות…";
    try {
      await dispatchWorkflow("chat-tuning.yml", {chat_jsonl:raw,steps:String(steps),batch_size:String(batch),data_approved:"yes"});
      sayChat("אימון השיחות התקבל. המערכת תמשיך מה-checkpoint האחרון, תשמור גרסה מעודכנת ותנסה ליצור ולהעלות GGUF. אפשר לעקוב באזור הריצות.");
      setTimeout(loadRuns, 2500);
    } catch (e) { sayChat(e.message, true); }
    finally {
      chatButton.disabled = false;
      chatButton.querySelector("span").textContent = "אימון שיחות ויצירת GGUF";
    }
  });

  pretrainForm.addEventListener("submit", async event => {
    event.preventDefault();
    sayPretrain("");
    adminKey = $("admin-key").value;
    if (!adminKey) { sayPretrain("יש להזין תחילה סיסמת ניהול.", true); return; }
    const corpusPath = $("corpus-path").value.trim();
    if (!$("corpus-approved").checked) {
      sayPretrain("יש לאשר שבדקת את זכויות המקור ואת תוכן הקורפוס.", true); return;
    }
    const steps = Number($("training-steps").value);
    const batchSize = Number($("batch-size").value);
    if (corpusPath && (!/^[A-Za-z0-9._/-]+\.txt$/.test(corpusPath) || corpusPath.startsWith("/") || corpusPath.split("/").includes(".."))) {
      sayPretrain("אם מציינים נתיב, יש להזין נתיב יחסי לקובץ TXT ללא '..'. אפשר להשאיר ריק לשימוש בקורפוס האחרון ב-Drive.", true);
      return;
    }
    if (!Number.isInteger(steps) || steps < 1 || steps > 1000) {
      sayPretrain("מספר צעדי האימון חייב להיות בין 1 ל־1,000.", true);
      return;
    }
    if (!Number.isInteger(batchSize) || batchSize < 1 || batchSize > 16) {
      sayPretrain("Batch size חייב להיות בין 1 ל־16.", true);
      return;
    }
    pretrainButton.disabled = true;
    pretrainButton.querySelector("span").textContent = "מפעיל אימון…";
    try {
      await dispatchWorkflow(PRETRAIN_WORKFLOW, {
        corpus_path:corpusPath,
        data_approved:"yes",
        steps:String(steps),
        batch_size:String(batchSize)
      });
      sayPretrain("בקשת האימון התקבלה. אם הנתיב הושאר ריק, המערכת תשתמש בקורפוס האחרון ב-Drive.");
      $("corpus-approved").checked = false;
      setTimeout(loadRuns, 3000);
    } catch (e) { sayPretrain(e.message, true); }
    finally {
      pretrainButton.disabled = false;
      pretrainButton.querySelector("span").textContent = "הפעלת אימון והפקת GGUF";
    }
  });
})();