// Simple frontend to talk to /api/chat and show timestamps + avatars
const form = document.getElementById("input-form");
const input = document.getElementById("message-input");
const messages = document.getElementById("messages");

function _formatTimestamp(iso){
  try{
    const d = new Date(iso);
    return d.toLocaleTimeString();
  }catch(e){
    return "";
  }
}

function appendMessage(text, who="tucker", ts=null){
  const row = document.createElement("div");
  row.className = "msg-row";

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = who === "user" ? "U" : "T";

  const bubble = document.createElement("div");
  bubble.className = "msg " + (who === "user" ? "user" : "tucker");
  bubble.textContent = text;

  const time = document.createElement("div");
  time.className = "timestamp";
  time.textContent = ts ? _formatTimestamp(ts) : "";

  if(who === "user"){
    row.appendChild(time);
    row.appendChild(bubble);
    row.appendChild(avatar);
  }else{
    row.appendChild(avatar);
    row.appendChild(bubble);
    row.appendChild(time);
  }

  messages.appendChild(row);
  messages.scrollTop = messages.scrollHeight;
}

async function sendMessage(text){
  const clientTs = new Date().toISOString();
  appendMessage(text, "user", clientTs);
  try{
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({message: text})
    });
    if(!res.ok) throw new Error("Network error");
    const j = await res.json();
    appendMessage(j.reply || "(no reply)", "tucker", j.timestamp || new Date().toISOString());
  }catch(e){
    appendMessage("Error: " + e.message, "tucker", new Date().toISOString());
  }
}

form.addEventListener("submit", (ev) => {
  ev.preventDefault();
  const v = input.value.trim();
  if(!v) return;
  input.value = "";
  sendMessage(v);
});

// welcome message
appendMessage("Hi — I'm Tucker. Try 'hello', 'joke', '2+2', or 'remember favorite color is blue'.", "tucker", new Date().toISOString());
