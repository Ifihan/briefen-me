// Create context menu on installation
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'shorten-url',
    title: 'Shorten with Briefen.me',
    contexts: ['page', 'link']
  });
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'shorten-url') {
    // Open popup when context menu is clicked
    chrome.action.openPopup();
  }
});