(() => {
  "use strict";

  if (window.__libreboxFilesNav) {
    return;
  }
  window.__libreboxFilesNav = true;

  const MOUNT_ID = "librebox-files-nav";
  const FILES_URL = "/files/";
  const ANCHOR_SELECTOR = '[data-testid="nav-user"]';
  const ICON_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-folder h-5 w-5" aria-hidden="true"><path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/></svg>`;

  const buildButton = () => {
    const button = document.createElement("a");
    button.id = MOUNT_ID;
    button.href = FILES_URL;
    button.target = "_blank";
    button.rel = "noopener noreferrer";
    button.title = "Files";
    button.setAttribute("aria-label", "Files");
    button.className = "inline-flex items-center justify-center h-9 w-9 mb-1 rounded-lg cursor-pointer transition-colors text-text-secondary hover:bg-surface-hover hover:text-accent-foreground";
    button.innerHTML = ICON_SVG;
    return button;
  };

  const insertButton = () => {
    if (document.getElementById(MOUNT_ID)) {
      return;
    }

    const anchor = document.querySelector(ANCHOR_SELECTOR);
    if (!anchor) {
      return;
    }

    const container = anchor.closest(".mt-auto") ?? anchor.parentElement;
    if (!container) {
      return;
    }

    container.insertBefore(buildButton(), container.firstChild);
  };

  const observer = new MutationObserver(insertButton);
  observer.observe(document.body, { childList: true, subtree: true });

  insertButton();
})();