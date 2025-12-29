/* global $ */
const eel = window.eel
const $ = window.jQuery
const SiriWave = window.SiriWave // Declare the SiriWave variable

$(document).ready(() => {
  const inputField = document.getElementById("InputField")
  const charCounter = document.getElementById("CharCount")
  const messagesDiv = document.getElementById("ChatMessages")

  initParticles()

  // Character counter - update as user types
  if (inputField && charCounter) {
    inputField.addEventListener("input", () => {
      charCounter.textContent = inputField.value.length
    })
  }

  // New Chat button - clear all messages and start fresh
  const newChatBtn = document.getElementById("NewChatBtn")
  if (newChatBtn) {
    newChatBtn.addEventListener("click", () => {
      console.log("[v0] New Chat clicked")
      messagesDiv.innerHTML = ""
      inputField.value = ""
      charCounter.textContent = "0"
      addToChatHistory("New Chat " + new Date().toLocaleTimeString())
    })
  }

  // Light Mode button - apply light theme
  const lightModeBtn = document.getElementById("LightModeBtn")
  if (lightModeBtn) {
    lightModeBtn.addEventListener("click", () => {
      console.log("[v0] Light mode clicked")
      document.body.style.background = "linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%)"
      document.body.style.color = "#333333"
      inputField.style.color = "#333333"
      inputField.style.backgroundColor = "#ffffff"
      document.querySelector(".ray-sidebar").style.backgroundColor = "rgba(220, 220, 220, 0.9)"
      document.querySelector(".ray-input-wrapper").style.background = "rgba(255, 255, 255, 0.8)"
      document.querySelector(".ray-input-wrapper").style.borderColor = "rgba(100, 100, 100, 0.3)"
      localStorage.setItem("rayTheme", "light")
    })
  }

  // Dark Mode button - apply dark theme (default)
  const darkModeBtn = document.getElementById("DarkModeBtn")
  if (darkModeBtn) {
    darkModeBtn.addEventListener("click", () => {
      console.log("[v0] Dark mode clicked")
      document.body.style.background = "linear-gradient(135deg, #000000 0%, #0a0a0a 100%)"
      document.body.style.color = "#ffffff"
      inputField.style.color = "#ffffff"
      inputField.style.backgroundColor = "transparent"
      document.querySelector(".ray-sidebar").style.backgroundColor = "rgba(20, 20, 20, 0.9)"
      document.querySelector(".ray-input-wrapper").style.background = "rgba(255, 50, 50, 0.05)"
      document.querySelector(".ray-input-wrapper").style.borderColor = "rgba(255, 50, 50, 0.5)"
      localStorage.setItem("rayTheme", "dark")
    })
  }

  // Regenerate button - regenerate the last user message
  const regenerateBtn = document.getElementById("RegenerateBtn")
  if (regenerateBtn) {
    regenerateBtn.addEventListener("click", async () => {
      console.log("[v0] Regenerate clicked")
      const lastUserMsg = Array.from(document.querySelectorAll(".ray-message-user")).pop()
      if (lastUserMsg) {
        const query = lastUserMsg.querySelector(".ray-message-text").textContent
        try {
          const messageEl = document.createElement("div")
          messageEl.className = "ray-message ray-message-ai"
          messageEl.innerHTML = `<span class="ray-message-sender">Ray:</span> <span class="ray-message-text"></span>`
          messagesDiv.appendChild(messageEl)
          messagesDiv.scrollTop = messagesDiv.scrollHeight

          await eel.respond(query)
        } catch (err) {
          console.error("[v0] Regenerate error:", err)
          addChatMessage("Ray", `Error: ${err.message}`)
        }
      } else {
        addChatMessage("Ray", "No previous question to regenerate. Ask me something first!")
      }
    })
  }

  // Attach button - file upload functionality
  const attachBtn = document.getElementById("AttachBtn")
  if (attachBtn) {
    attachBtn.addEventListener("click", () => {
      console.log("[v0] Attach button clicked")
      // Create a hidden file input
      const fileInput = document.createElement('input')
      fileInput.type = 'file'
      fileInput.accept = '.pdf,.txt,.doc,.docx,.jpg,.jpeg,.png,.gif,.mp3,.mp4,.wav'
      fileInput.style.display = 'none'

      fileInput.onchange = async function(e) {
        const file = e.target.files[0]
        if (file) {
          console.log("[v0] File selected:", file.name)
          try {
            // Show upload progress
            addChatMessage("You", `📎 Uploading ${file.name}...`)

            // Call backend to upload file (if eel.upload_file exists)
            if (typeof eel.upload_file === 'function') {
              const result = await eel.upload_file(file.name)
              addChatMessage("Ray", `✅ File "${file.name}" uploaded successfully! I can now help you with questions about this file.`)
            } else {
              // Fallback: just acknowledge the file
              addChatMessage("Ray", `✅ File "${file.name}" (${(file.size / 1024).toFixed(1)} KB) ready for processing.`)
            }
          } catch (err) {
            console.error("[v0] File upload error:", err)
            addChatMessage("Ray", `❌ Failed to upload file: ${err.message}`)
          }
        }
      }

      // Trigger file dialog
      document.body.appendChild(fileInput)
      fileInput.click()
      document.body.removeChild(fileInput)
    })
  }

  // Settings button - open settings modal/panel
  const settingsBtn = document.getElementById("SettingsBtn")
  if (settingsBtn) {
    settingsBtn.addEventListener("click", () => {
      console.log("[v0] Settings clicked")
      // Create or show settings modal
      showSettingsModal()
    })
  }

  // Top settings button
  const settingsTopBtn = document.getElementById("SettingsTopBtn")
  if (settingsTopBtn) {
    settingsTopBtn.addEventListener("click", () => {
      console.log("[v0] Top settings clicked")
      showSettingsModal()
    })
  }



  // Microphone button - activate voice input with Siri wave
  const micBtn = document.getElementById("MicBtn")
  if (micBtn) {
    micBtn.addEventListener("click", () => {
      console.log("[v0] Mic button clicked")
      document.getElementById("Oval").style.display = "none"
      document.getElementById("SiriWave").hidden = false
      eel.allCommands()
    })
  }

  // Alt + R hotkey for voice activation
  document.addEventListener("keydown", (e) => {
    if (e.key.toLowerCase() === "r" && e.altKey) {
      console.log("[v0] Alt + R detected!")
      document.getElementById("Oval").style.display = "none"
      document.getElementById("SiriWave").hidden = false
      eel.allCommands()
    }
  })

  // Chat button - send user query
  const chatBtn = document.getElementById("ChatBtn")
  if (chatBtn) {
    chatBtn.addEventListener("click", async () => {
      console.log("[v0] Chat button clicked")
      const query = inputField.value.trim()

      if (!query) {
        addChatMessage("Ray", "Please enter a question or command")
        return
      }

      try {
        addChatMessage("You", query)
        addToChatHistory(query)

        const messageEl = document.createElement("div")
        messageEl.className = "ray-message ray-message-ai"
        messageEl.innerHTML = `<span class="ray-message-sender">Ray:</span> <span class="ray-message-text"></span>`
        messagesDiv.appendChild(messageEl)
        messagesDiv.scrollTop = messagesDiv.scrollHeight

        await eel.respond(query)
        inputField.value = ""
        charCounter.textContent = "0"
      } catch (err) {
        console.error("[v0] Chat error:", err)
        addChatMessage("Ray", `Error: ${err.message}`)
      }
    })
  }

  // Enter key to send message
  inputField.addEventListener("keypress", async (e) => {
    if (e.key === "Enter") {
      e.preventDefault()
      const chatBtn = document.getElementById("ChatBtn")
      if (chatBtn) chatBtn.click()
    }
  })

  // Helper functions
  function addToChatHistory(title) {
    const historyList = document.getElementById("ChatHistory")
    if (!historyList) return

    const item = document.createElement("div")
    item.className = "ray-history-item"
    const displayTitle = title.substring(0, 30) + (title.length > 30 ? "..." : "")
    item.textContent = displayTitle
    item.title = title

    item.addEventListener("click", () => {
      console.log("[v0] Loading conversation:", title)
      messagesDiv.innerHTML = ""
      addChatMessage("Ray", `Switched to: "${title}"`)
      addChatMessage("You", title)
    })

    historyList.insertBefore(item, historyList.firstChild)

    while (historyList.children.length > 10) {
      historyList.removeChild(historyList.lastChild)
    }

    const allItems = Array.from(historyList.children).map((el) => el.title)
    localStorage.setItem("rayChatHistory", JSON.stringify(allItems))
  }

  function loadChatHistory() {
    const saved = localStorage.getItem("rayChatHistory")
    if (saved) {
      const items = JSON.parse(saved)
      items.forEach((title) => {
        const historyList = document.getElementById("ChatHistory")
        const item = document.createElement("div")
        item.className = "ray-history-item"
        const displayTitle = title.substring(0, 30) + (title.length > 30 ? "..." : "")
        item.textContent = displayTitle
        item.title = title
        item.addEventListener("click", () => {
          messagesDiv.innerHTML = ""
          addChatMessage("Ray", `Switched to: "${title}"`)
          addChatMessage("You", title)
        })
        historyList.appendChild(item)
      })
    }
  }

  function addChatMessage(sender, message) {
    if (!messagesDiv) return

    const messageEl = document.createElement("div")
    messageEl.className = `ray-message ray-message-${sender === "Ray" ? "ai" : "user"}`
    messageEl.innerHTML = `<span class="ray-message-sender">${sender}:</span> <span class="ray-message-text">${message}</span>`
    messagesDiv.appendChild(messageEl)
    messagesDiv.scrollTop = messagesDiv.scrollHeight
  }

  function StreamChunk(chunk) {
    const messagesDiv = document.getElementById("ChatMessages")
    if (!messagesDiv) return

    const lastMessages = messagesDiv.querySelectorAll(".ray-message-ai")
    if (lastMessages.length > 0) {
      const lastMessage = lastMessages[lastMessages.length - 1].querySelector(".ray-message-text")
      if (lastMessage) {
        lastMessage.textContent += chunk
        messagesDiv.scrollTop = messagesDiv.scrollHeight
      }
    }
  }

  function initParticles() {
    const canvas = document.getElementById("particleCanvas")
    if (!canvas) return

    const ctx = canvas.getContext("2d")
    canvas.width = 300
    canvas.height = 300

    const particles = []
    const particleCount = 150

    class Particle {
      constructor() {
        this.x = Math.random() * canvas.width
        this.y = Math.random() * canvas.height
        this.vx = (Math.random() - 0.5) * 2
        this.vy = (Math.random() - 0.5) * 2
        this.radius = Math.random() * 2 + 1
        this.life = Math.random() * 0.5 + 0.5
      }

      update() {
        this.x += this.vx
        this.y += this.vy
        this.life -= 0.01

        if (this.x < 0 || this.x > canvas.width) this.vx *= -1
        if (this.y < 0 || this.y > canvas.height) this.vy *= -1

        if (this.life <= 0) {
          this.x = Math.random() * canvas.width
          this.y = Math.random() * canvas.height
          this.life = Math.random() * 0.5 + 0.5
        }
      }

      draw() {
        ctx.fillStyle = `rgba(255, 50, 50, ${this.life})`
        ctx.beginPath()
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2)
        ctx.fill()
      }
    }

    for (let i = 0; i < particleCount; i++) {
      particles.push(new Particle())
    }

    function animate() {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      particles.forEach((p) => {
        p.update()
        p.draw()
      })
      requestAnimationFrame(animate)
    }

    animate()
  }

  eel.expose(StreamChunk)



  function showSettingsModal() {
    // Create settings modal
    const modal = document.createElement('div')
    modal.className = 'ray-settings-modal'
    modal.innerHTML = `
      <div class="ray-modal-overlay">
        <div class="ray-modal-content">
          <div class="ray-modal-header">
            <h3>Settings</h3>
            <button class="ray-modal-close">&times;</button>
          </div>
          <div class="ray-modal-body">
            <div class="ray-setting-item">
              <label>Theme:</label>
              <select id="themeSelect">
                <option value="dark">Dark</option>
                <option value="light">Light</option>
              </select>
            </div>
            <div class="ray-setting-item">
              <label>Voice Input:</label>
              <input type="checkbox" id="voiceEnabled" checked>
            </div>
            <div class="ray-setting-item">
              <label>Streaming Responses:</label>
              <input type="checkbox" id="streamingEnabled" checked>
            </div>
            <div class="ray-setting-item">
              <label>Model:</label>
              <span>Grok 4.1 Fast (Free)</span>
            </div>
            <div class="ray-setting-item">
              <label>API:</label>
              <span>OpenRouter</span>
            </div>
          </div>
          <div class="ray-modal-footer">
            <button class="ray-btn-secondary" id="resetSettings">Reset to Defaults</button>
            <button class="ray-btn-primary" id="saveSettings">Save</button>
          </div>
        </div>
      </div>
    `

    document.body.appendChild(modal)

    // Set current values
    const currentTheme = localStorage.getItem("rayTheme") || "dark"
    document.getElementById("themeSelect").value = currentTheme

    // Event listeners
    document.querySelector('.ray-modal-close').addEventListener('click', () => {
      document.body.removeChild(modal)
    })

    document.getElementById('saveSettings').addEventListener('click', () => {
      const selectedTheme = document.getElementById("themeSelect").value
      localStorage.setItem("rayTheme", selectedTheme)

      if (selectedTheme === "light") {
        applyLightTheme()
      } else {
        applyDarkTheme()
      }

      addChatMessage("Ray", "Settings saved successfully!")
      document.body.removeChild(modal)
    })

    document.getElementById('resetSettings').addEventListener('click', () => {
      localStorage.setItem("rayTheme", "dark")
      applyDarkTheme()
      addChatMessage("Ray", "Settings reset to defaults!")
      document.body.removeChild(modal)
    })

    // Close on overlay click
    document.querySelector('.ray-modal-overlay').addEventListener('click', (e) => {
      if (e.target === document.querySelector('.ray-modal-overlay')) {
        document.body.removeChild(modal)
      }
    })
  }

  // Load saved theme on startup
  const savedTheme = localStorage.getItem("rayTheme") || "dark"
  if (savedTheme === "light") {
    applyLightTheme()
  } else {
    applyDarkTheme()
  }

  // Load chat history on startup
  loadChatHistory()

  // Siri wave configuration
  var siriWave = new SiriWave({
    container: document.getElementById("siri-container"),
    width: 800,
    height: 200,
    style: "ios9",
    amplitude: "1",
    speed: "0.30",
    autostart: true,
    color: "#ff3232",
  })
})
