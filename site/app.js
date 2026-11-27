(() => {
  "use strict";
  const OWNER = "avtsye", REPO = "IvritLM", WORKFLOW = "train.yml";
  const API = "https://api.github.com";
  const $ = (id) => document.getElementById(id);
  let token = "";
  const form = $("train-form"), submit = $("submit-btn"), message = $("form-message"), runs = $("runs");
  function say(text, error = false) { message.textContent = text; message.classList.toggle("error", error); }
  function headers() { return {Accept:"application/vnd.github+json",Authorization:"Bearer "+token,"X-GitHub-Api-Version":"2022-11-28"}; }
  function validateSource(raw, kind) {
    let u; try { u = new URL(raw); } catch { throw new Error("יש להזין כתובת URL תקינה."); }
    if (u.protocol !== "https:" || u.username || u.password) throw new Error("נדרשת כתובת HTTPS ציבורית ללא פרטי התחברות.");
    if (kind === "github" || (kind === "auto" && u.hostname === "github.com")) {
      if (u.hostname !== "github.com" || !/^\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+\/?$/.test(u.pathname)) throw new Error("יש להזין כתובת מאגר GitHub בפורמט owner/repository.");
      return {url:"https://github.com"+u.pathname.replace(/\/$/,""),kind:"github"};
    }
    if (kind === "web" || kind === "auto") {
      if (u.hostname === "github.com") throw new Error("בחר בסוג מאגר GitHub עבור כתובת זו.");
      return {url:u.href,kind:"web"};
    }
    throw new Error("סוג מקור לא מוכר.");
  }
  async function request(path, options = {}) {
    const response = await fetch(API+path,{...options,headers:{...headers(),...(options.headers||{})}});
    if (!response.ok) {
      let detail=""; try { detail=(await response.json()).message||""; } catch {}
      if (response.status===401) throw new Error("האסימון אינו תקין או שפג תוקפו.");
      if (response.status===403) throw new Error("חסרה הרשאת Actions: Read and write או גישה למאגר.");
      if (response.status===404) throw new Error("ה־Workflow לא נמצא. בדוק שקובץ train.yml קיים בענף main.");
      throw new Error("שגיאת GitHub ("+response.status+"). "+detail);
    }
    return response.status===204 ? null : response.json();
  }
  function render(items) {
    runs.replaceChildren();
    if (!items.length) { const p=document.createElement("p");p.className="empty";p.textContent="לא נמצאו ריצות עדיין.";runs.append(p);return; }
    for (const item of items) {
      const row=document.createElement("div");row.className="run";
      const left=document.createElement("div"),title=document.createElement("div"),a=document.createElement("a"),meta=document.createElement("div");
      title.className="run-title";a.href=item.html_url;a.target="_blank";a.rel="noreferrer";a.textContent=item.display_title||item.name||"IvritLM workflow";title.append(a);
      meta.className="run-meta";meta.textContent="#"+item.run_number+" · "+new Date(item.created_at).toLocaleString("he-IL");left.append(title,meta);
      const state=document.createElement("span");state.className="run-state "+(item.conclusion||item.status||"queued");state.textContent=item.conclusion||item.status||"unknown";
      row.append(left,state);runs.append(row);
    }
  }
  async function loadRuns() {
    if (!token) { runs.textContent="יש להזין אסימון GitHub כדי לקרוא את היסטוריית הריצות.";runs.className="empty";return; }
    runs.textContent="טוען ריצות…";runs.className="empty";
    try { const data=await request("/repos/"+OWNER+"/"+REPO+"/actions/runs?per_page=8");runs.className="";render(data.workflow_runs||[]); }
    catch(e) { runs.textContent=e.message;runs.className="empty"; }
  }
  $("clear-token").addEventListener("click",()=>{token="";$("github-token").value="";runs.textContent="האסימון נוקה מהזיכרון.";runs.className="empty";say("האסימון נוקה.");});
  $("refresh-runs").addEventListener("click",loadRuns);
  form.addEventListener("submit",async event=>{
    event.preventDefault();say("");token=$("github-token").value.trim();
    if(!token){say("יש להזין אסימון GitHub.",true);return;}
    let source;try{source=validateSource($("source-url").value.trim(),$("source-kind").value);}catch(e){say(e.message,true);return;}
    if(!$("license-ack").checked||!$("public-ack").checked){say("יש לאשר את שתי הצהרות המקור.",true);return;}
    submit.disabled=true;submit.querySelector("span").textContent="שולח ל־GitHub…";
    try{
      await request("/repos/"+OWNER+"/"+REPO+"/actions/workflows/"+WORKFLOW+"/dispatches",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({ref:"main",inputs:{source_url:source.url,source_kind:source.kind,license_ack:"yes"}})});
      say("הבקשה התקבלה ב־GitHub. הריצה תופיע ברשימה בעוד מספר שניות.");setTimeout(loadRuns,2500);
    }catch(e){say(e.message,true);}
    finally{submit.disabled=false;submit.querySelector("span").textContent="הפעלת בדיקת מקור";}
  });
})();