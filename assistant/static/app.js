const log = document.getElementById("log");
const msgInput = document.getElementById("msg");
const settings = document.getElementById("settings");

function cfg() {
  return {
    url: localStorage.getItem("backendUrl") || window.location.origin,
    token: localStorage.getItem("token") || "",
  };
}

function add(text, cls) {
  const div = document.createElement("div");
  div.className = "bubble " + cls;
  div.textContent = text;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

function meta(text) {
  const div = document.createElement("div");
  div.className = "meta";
  div.textContent = text;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

async function sendText() {
  const text = msgInput.value.trim();
  if (!text) return;
  const { url, token } = cfg();
  if (!token) { settings.classList.remove("hidden"); return; }
  add(text, "me");
  msgInput.value = "";
  try {
    const r = await fetch(url + "/message", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": "Bearer " + token },
      body: JSON.stringify({ message: text }),
    });
    if (!r.ok) { add("Error: " + r.status, "bot"); return; }
    const data = await r.json();
    add(data.reply, "bot");
  } catch (e) {
    add("Network error.", "bot");
  }
}

let recorder = null, chunks = [];
const recBtn = document.getElementById("recBtn");

recBtn.addEventListener("click", async () => {
  if (recorder && recorder.state === "recording") {
    recorder.stop();
    return;
  }
  const { token } = cfg();
  if (!token) { settings.classList.remove("hidden"); return; }
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  recorder = new MediaRecorder(stream);
  chunks = [];
  recorder.ondataavailable = (e) => chunks.push(e.data);
  recorder.onstop = sendVoice;
  recorder.start();
  recBtn.classList.add("recording");
  recBtn.textContent = "stop";
});

async function sendVoice() {
  recBtn.classList.remove("recording");
  recBtn.textContent = "rec";
  const { url, token } = cfg();
  const blob = new Blob(chunks, { type: chunks[0] ? chunks[0].type : "audio/webm" });
  const form = new FormData();
  form.append("file", blob, "voice.webm");
  meta("transcribing...");
  try {
    const r = await fetch(url + "/voice", {
      method: "POST",
      headers: { "Authorization": "Bearer " + token },
      body: form,
    });
    if (!r.ok) { add("Error: " + r.status, "bot"); return; }
    const data = await r.json();
    add(data.transcript, "me");
    add(data.reply, "bot");
  } catch (e) {
    add("Network error.", "bot");
  }
}

document.getElementById("sendBtn").addEventListener("click", sendText);
msgInput.addEventListener("keydown", (e) => { if (e.key === "Enter") sendText(); });
document.getElementById("settingsBtn").addEventListener("click", () => settings.classList.toggle("hidden"));
document.getElementById("saveBtn").addEventListener("click", () => {
  const u = document.getElementById("urlInput").value.trim();
  const t = document.getElementById("tokenInput").value.trim();
  if (u) localStorage.setItem("backendUrl", u); else localStorage.removeItem("backendUrl");
  if (t) localStorage.setItem("token", t);
  settings.classList.add("hidden");
  meta("Settings saved.");
});

if (!cfg().token) settings.classList.remove("hidden");
if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js");
