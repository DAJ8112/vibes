// Service worker: clicking the toolbar icon toggles the on-page widget.
// The content script owns all UI/loop state; we just relay the click.
chrome.action.onClicked.addListener((tab) => {
  if (!tab.id) return;
  chrome.tabs.sendMessage(tab.id, { type: "TOGGLE_WIDGET" }).catch(() => {
    // No content script on this page (e.g. chrome:// or a non-YouTube tab).
  });
});
