document.addEventListener('DOMContentLoaded', function() {
  // Debugging helper
  function debugLog(message) {
    console.log(`[DEBUG] ${message}`);
  }

  // Sidebar elements
  const sidebar = document.getElementById('sidebar');
  const sidebarToggle = document.getElementById('sidebarToggle');
  const mobileSidebarToggle = document.getElementById('mobileSidebarToggle');
  
  // Toggle sidebar function with debugging
  function toggleSidebar() {
    debugLog(`Toggling sidebar. Current state: ${sidebar.classList}`);
    sidebar.classList.toggle('collapsed');
    
    if (window.innerWidth <= 768) {
      sidebar.classList.toggle('visible');
      debugLog(`Mobile view - sidebar visible: ${sidebar.classList.contains('visible')}`);
    }
  }
  
  // Sidebar toggle event listeners
  [sidebarToggle, mobileSidebarToggle].forEach(btn => {
    btn.addEventListener('click', function(e) {
      e.stopPropagation();
      toggleSidebar();
    });
  });
  
  // Close sidebar when clicking outside on mobile
  document.addEventListener('click', function(e) {
    if (window.innerWidth <= 768 && 
        !sidebar.contains(e.target) && 
        !mobileSidebarToggle.contains(e.target) &&
        sidebar.classList.contains('visible')) {
      debugLog('Click outside detected - closing sidebar');
      toggleSidebar();
    }
  });

  // Enhanced chat deletion with error handling
  document.querySelectorAll('.btn-delete-chat').forEach(btn => {
    btn.addEventListener('click', async function(e) {
      e.stopPropagation();
      const chatItem = this.closest('.chat-history-item');
      const chatId = chatItem?.dataset?.chatId;
      
      if (!chatId) {
        console.error('Delete failed: No chat ID found');
        return;
      }

      debugLog(`Attempting to delete chat: ${chatId}`);
      
      if (confirm('Are you sure you want to delete this chat?')) {
        try {
          const response = await fetch(`/delete-chat/${chatId}`, {
            method: 'DELETE'
          });
          
          if (response.ok) {
            debugLog(`Successfully deleted chat: ${chatId}`);
            chatItem.remove();
            
            // If no chats left, create a new one
            if (document.querySelectorAll('.chat-history-item').length === 0) {
              debugLog('No chats left - creating new one');
              const newChatResponse = await fetch('/new-chat', { method: 'POST' });
              const data = await newChatResponse.json();
              window.location.href = data.redirect;
            }
          } else {
            console.error('Delete failed:', await response.text());
          }
        } catch (error) {
          console.error('Delete error:', error);
        }
      }
    });
  });

  // Enhanced chat renaming with error handling
  document.querySelectorAll('.btn-edit-chat').forEach(btn => {
    btn.addEventListener('click', function(e) {
      e.stopPropagation();
      const chatItem = this.closest('.chat-history-item');
      const chatId = chatItem?.dataset?.chatId;
      
      if (!chatId) {
        console.error('Rename failed: No chat ID found');
        return;
      }

      const titleSpan = chatItem.querySelector('.chat-title');
      const titleInput = chatItem.querySelector('.chat-title-edit');
      
      titleSpan.style.display = 'none';
      titleInput.style.display = 'block';
      titleInput.value = titleSpan.textContent;
      titleInput.focus();
      
      const saveTitle = async () => {
        const newTitle = titleInput.value.trim();
        if (newTitle && newTitle !== titleSpan.textContent) {
          debugLog(`Attempting to rename chat ${chatId} to: ${newTitle}`);
          
          try {
            const response = await fetch(`/rename-chat/${chatId}`, {
              method: 'PUT',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ title: newTitle })
            });
            
            if (response.ok) {
              debugLog(`Successfully renamed chat to: ${newTitle}`);
              titleSpan.textContent = newTitle;
            } else {
              console.error('Rename failed:', await response.text());
            }
          } catch (error) {
            console.error('Rename error:', error);
          }
        }
        
        titleSpan.style.display = 'block';
        titleInput.style.display = 'none';
      };
      
      titleInput.addEventListener('blur', saveTitle);
      titleInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') saveTitle();
      });
    });
  });

  // New chat button with error handling
  document.getElementById('newChatBtn').addEventListener('click', async function() {
    debugLog('Creating new chat');
    try {
      const response = await fetch('/new-chat', { method: 'POST' });
      const data = await response.json();
      window.location.href = data.redirect;
    } catch (error) {
      console.error('New chat error:', error);
    }
  });

  // Responsive adjustments
  function handleResize() {
    debugLog(`Window resized to: ${window.innerWidth}px`);
    if (window.innerWidth > 768) {
      sidebar.classList.remove('visible');
    }
  }
  
  window.addEventListener('resize', handleResize);
  handleResize(); // Initial call

  // Debug initial state
  debugLog('DOM fully loaded and parsed');
  debugLog(`Initial sidebar state: ${sidebar.classList}`);
  debugLog(`Found ${document.querySelectorAll('.chat-history-item').length} chat items`);
});