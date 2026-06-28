// Simple frontend to talk to /api/chat
const form = document.getElementById("input-form");
const input = document.getElementById("message-input");
const messages = document.getElementById("messages");

function appendMessage(text, who="tucker"){
  const d = document.createElement("div");
  d.className = "msg " + (who === "user" ? "user" : "tucker");
  d.textContent = text;
  messages.appendChild(d);
  messages.scrollTop = messages.scrollHeight;
}

async function sendMessage(text){
  appendMessage(text, "user");
  try{
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({message: text})
    });
    if(!res.ok) throw new Error("Network error");
    const j = await res.json();
    appendMessage(j.reply || "(no reply)");
  }catch(e){
    appendMessage("Error: " + e.message);
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
appendMessage("Hi — I'm Tucker. Try 'hello', 'joke', '2+2', or 'remember favorite color is blue'.");
