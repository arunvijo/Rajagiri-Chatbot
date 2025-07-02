/*  Rajagiri Chatbot – UI helpers
    ---------------------------------------------------------------
    • Sidebar toggle & mobile toggle
    • Dynamic chat‑history list (read from <div data‑attributes>)
    • “New chat” button -> /?new=true
    • Copy / Like / Dislike message actions
    • Loader + autoscroll on submit
-----------------------------------------------------------------*/

document.addEventListener('DOMContentLoaded', () => {
  /* ---------- ELEMENTS ---------- */
  const sidebar            = document.getElementById('sidebar');
  const mainContent        = document.querySelector('.main-content');
  const sidebarToggleBtns  = [document.getElementById('sidebarToggle'),
                              document.getElementById('mobileSidebarToggle')];
  const newChatBtn         = document.getElementById('newChatBtn');
  const chatHistoryHolder  = document.getElementById('chatHistory');
  const chatForm           = document.getElementById('chatForm');
  const userInput          = document.getElementById('userInput');
  const loadingIndicator   = document.getElementById('loadingIndicator');
  const chatMessages       = document.getElementById('chatMessages');
  const expandSidebarBtn   = document.getElementById('expandSidebarBtn');
  const mobileToggleBtn    = document.getElementById('mobileSidebarToggle');

  /* ---------- SIDEBAR TOGGLE ---------- */
  const toggleSidebar = () => {
    sidebar.classList.toggle('collapsed');
    mainContent.classList.toggle('expanded');
    if (sidebar.classList.contains('collapsed')) {
      expandSidebarBtn.style.display = 'block';
    } else {
      expandSidebarBtn.style.display = 'none';
    }
  };

  sidebarToggleBtns.forEach(btn => btn?.addEventListener('click', toggleSidebar));

  expandSidebarBtn?.addEventListener('click', () => {
    sidebar.classList.remove('collapsed');
    mainContent.classList.remove('expanded');
    expandSidebarBtn.style.display = 'none';
  });

  /* ---------- NEW CHAT ---------- */
  newChatBtn?.addEventListener('click', () => {
    window.location.href = '/?new=true';
  });

  /* ---------- CHAT HISTORY ---------- */
  function loadChatHistory() {
    const chatsData     = JSON.parse(chatHistoryHolder.dataset.chats || '{}');
    const currentChatId = chatHistoryHolder.dataset.current;

    chatHistoryHolder.innerHTML = '';

    Object.values(chatsData)
      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
      .forEach(chat => {
        const div = document.createElement('div');
        div.className = 'chat-history-item' + (chat.id === currentChatId ? ' active' : '');
        div.title     = chat.title;
        div.textContent = chat.title;
        div.addEventListener('click', () => {
          if (chat.id !== currentChatId) window.location.href = `/chat/${chat.id}`;
        });
        chatHistoryHolder.appendChild(div);
      });
  }
  loadChatHistory();

  /* ---------- CHAT FORM ---------- */
  chatForm?.addEventListener('submit', (e) => {
    e.preventDefault();
    const msg = userInput.value.trim();
    if (!msg) return;

    loadingIndicator.style.display = 'block';
    window.scrollTo(0, document.body.scrollHeight);
    chatForm.submit();
  });

  userInput?.focus();

  /* ---------- MESSAGE ACTIONS (copy / like / dislike) ---------- */
  chatMessages?.addEventListener('click', (e) => {
    const btn = e.target.closest('.btn-action');
    if (!btn) return;

    const action = btn.title.toLowerCase();
    const messageContent = btn.closest('.message-content')?.querySelector('p,div');
    if (!messageContent) return;

    switch (action) {
      case 'copy':
        navigator.clipboard.writeText(messageContent.textContent);
        temporarilySwapIcon(btn, 'far fa-copy', 'fas fa-check');
        break;
      case 'like':
        temporarilySwapIcon(btn, 'far fa-thumbs-up', 'fas fa-thumbs-up');
        break;
      case 'dislike':
        temporarilySwapIcon(btn, 'far fa-thumbs-down', 'fas fa-thumbs-down');
        break;
    }
  });

  function temporarilySwapIcon(button, from, to) {
    button.innerHTML = `<i class="${to}"></i>`;
    setTimeout(() => (button.innerHTML = `<i class="${from}"></i>`), 1500);
  }
});