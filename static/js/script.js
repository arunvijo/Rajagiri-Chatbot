document.addEventListener('DOMContentLoaded', function () {
  // DOM Elements
  const chatForm = document.getElementById('chatForm');
  const userInput = document.getElementById('userInput');
  const chatMessages = document.getElementById('chatMessages');
  const mobileSidebarToggle = document.getElementById('mobileSidebarToggle');
  const sidebar = document.getElementById('sidebar');
  const newChatBtn = document.getElementById('newChatBtn');
  const suggestionCards = document.querySelectorAll('.suggestion-card');

  // Sidebar toggle (mobile)
  if (mobileSidebarToggle) {
    mobileSidebarToggle.addEventListener('click', function () {
      sidebar.classList.toggle('active');
    });
  }

  // Set question from suggestion card
  suggestionCards.forEach(card => {
    card.addEventListener('click', function () {
      const question = this.querySelector('span').textContent;
      userInput.value = question;
      userInput.focus();
    });
  });

  // New chat clears messages
  if (newChatBtn) {
    newChatBtn.addEventListener('click', function () {
      chatMessages.innerHTML = '';
    });
  }

  // Form submission
  if (chatForm) {
    chatForm.addEventListener('submit', async function (e) {
      e.preventDefault();
      const question = userInput.value.trim();
      if (!question) return;

      addMessage('user', question);
      userInput.value = '';
      showLoadingIndicator();

      try {
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: question })
        });

        removeLoadingIndicator();

        if (!response.ok) throw new Error('Network error');

        const data = await response.json();
        addMessage('assistant', data.answer);
      } catch (err) {
        console.error(err);
        removeLoadingIndicator();
        addMessage('assistant', "Sorry, I encountered an error. Please try again.");
      }
    });
  }

  // Add message to chat window
  function addMessage(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;

    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    avatarDiv.innerHTML = role === 'user'
      ? '<i class="fas fa-user"></i>'
      : '<img src="/static/images/rajagiri-logo.png" alt="Rajagiri Logo">';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = content;

    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(contentDiv);

    if (role === 'assistant') {
      const actionsDiv = document.createElement('div');
      actionsDiv.className = 'message-actions';
      actionsDiv.innerHTML = `
        <button class="btn-action" onclick="rateMessage(this, 'like')"><i class="far fa-thumbs-up"></i></button>
        <button class="btn-action" onclick="rateMessage(this, 'dislike')"><i class="far fa-thumbs-down"></i></button>
      `;
      contentDiv.appendChild(actionsDiv);
    }

    chatMessages.appendChild(messageDiv);
    scrollToBottom();
  }

  // Loading indicator
  function showLoadingIndicator() {
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'loadingIndicator';
    loadingDiv.className = 'message bot-message';
    loadingDiv.innerHTML = `
      <div class="message-avatar">
        <img src="/static/images/rajagiri-logo.png" alt="Rajagiri Logo">
      </div>
      <div class="message-content">
        <div class="typing-indicator">
          <span></span><span></span><span></span>
        </div>
      </div>
    `;
    chatMessages.appendChild(loadingDiv);
    scrollToBottom();
  }

  function removeLoadingIndicator() {
    const indicator = document.getElementById('loadingIndicator');
    if (indicator) indicator.remove();
  }

  function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  // Rating buttons (like/dislike)
  window.rateMessage = function (button, action) {
    const msgEl = button.closest('.message');
    const messageIndex = [...chatMessages.children].indexOf(msgEl);
    const chatId = button.closest('.message-actions')?.dataset?.chat || "current";

    fetch('/rate-message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chatId: chatId,
        messageIndex: messageIndex,
        action: action
      })
    }).then(response => {
      if (response.ok) {
        const icon = button.querySelector('i');
        icon.classList.remove('far');
        icon.classList.add('fas');

        const sibling = action === 'like' ? button.nextElementSibling : button.previousElementSibling;
        if (sibling) {
          sibling.querySelector('i').classList.remove('fas');
          sibling.querySelector('i').classList.add('far');
        }
      }
    });
  };

  // Welcome message if no history
  if (!chatMessages.children.length) {
    const welcomeDiv = document.createElement('div');
    welcomeDiv.className = 'welcome-message';
    welcomeDiv.innerHTML = `
      <h1 class="text-center mb-4">Rajagiri College Chatbot</h1>
      <p class="text-center text-secondary">Ask about admissions, departments, scholarships, or campus life.</p>
    `;
    chatMessages.appendChild(welcomeDiv);
  }

  scrollToBottom();
});
