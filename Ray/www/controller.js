// Import jQuery and Eel
const $ = window.$
const eel = window.eel

$(document).ready(() => {
  // Expose the DisplayMessage function to Python (eel)
  eel.expose(DisplayMessage)
  function DisplayMessage(message) {
    console.log("[v0] DisplayMessage called:", message)
    const siriMessage = document.querySelector(".ray-siri-message")
    if (siriMessage) {
      siriMessage.textContent = message
    }
    addChatMessage("Ray", message)
  }

  // Expose the ShowHood function to Python (eel)
  eel.expose(ShowHood)
  function ShowHood() {
    console.log("[v0] ShowHood called")
    $("#Oval").css("display", "flex")
    $("#SiriWave").attr("hidden", true)
  }

  // Expose addChatMessage globally
  window.addChatMessage = addChatMessage

  function addChatMessage(sender, message) {
    const messagesDiv = document.getElementById("ChatMessages")
    if (!messagesDiv) return

    const messageEl = document.createElement("div")
    messageEl.className = `ray-message ray-message-${sender === "Ray" ? "ai" : "user"}`
    messageEl.innerHTML = `<span class="ray-message-sender">${sender}:</span> <span class="ray-message-text">${message}</span>`
    messagesDiv.appendChild(messageEl)
    messagesDiv.scrollTop = messagesDiv.scrollHeight
  }
})
