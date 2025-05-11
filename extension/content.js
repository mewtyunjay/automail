(function() {
  if (window.__gmailFloatingInjected) return;
  window.__gmailFloatingInjected = true;

  const button = document.createElement('div');
  button.id = 'gmail-floating-button';
  document.body.appendChild(button);

  button.addEventListener('click', () => {
    let iframe = document.getElementById('gmail-floating-iframe');

    if (!iframe) {
      iframe = document.createElement('iframe');
      iframe.id = 'gmail-floating-iframe';
      if (window.chrome && chrome.runtime && typeof chrome.runtime.getURL === 'function') {
        iframe.src = chrome.runtime.getURL('iframe.html');
      } else if (window.chrome && chrome.extension && typeof chrome.extension.getURL === 'function') {
        iframe.src = chrome.extension.getURL('iframe.html');
      } else {
        iframe.src = 'iframe.html'; // fallback for local dev or non-extension environments
      }
      iframe.style.display = 'block';
      iframe.onload = () => {
        const info = getGmailInfo();
        iframe.contentWindow.postMessage({ type: 'gmailInfo', ...info }, '*');
      };
      document.body.appendChild(iframe);
      button.style.display = 'none';

    } else {
      if (iframe.style.display === 'none') {
        iframe.style.display = 'block';
        const info = getGmailInfo();
        iframe.contentWindow.postMessage({ type: 'gmailInfo', ...info }, '*');
        button.style.display = 'none';
      } else {
        iframe.style.display = 'none';
        button.style.display = 'block';
      }
    }
  });

  window.addEventListener('message', event => {
    if (event.data && event.data.type === 'closeIframe') {
      const iframe = document.getElementById('gmail-floating-iframe');
      if (iframe) {
        iframe.style.display = 'none';
        button.style.display = 'block';
      }
    } else if (event.data && event.data.type === 'getGmailInfo') {
      const info = getGmailInfo();
      const iframe = document.getElementById('gmail-floating-iframe');
      if (iframe) {
        iframe.contentWindow.postMessage({ type: 'gmailInfo', ...info }, '*');
      }
    }
  });

  // --- MutationObserver to auto-refresh iframe on email switch ---
  let lastInfo = null;
  function infoChanged(newInfo) {
    if (!lastInfo) return true;
    return newInfo.subject !== lastInfo.subject || newInfo.date !== lastInfo.date || newInfo.body !== lastInfo.body;
  }
  const observer = new MutationObserver(() => {
    const iframe = document.getElementById('gmail-floating-iframe');
    if (iframe && iframe.style.display !== 'none') {
      const info = getGmailInfo();
      if (infoChanged(info)) {
        iframe.contentWindow.postMessage({ type: 'gmailInfo', ...info }, '*');
        lastInfo = info;
      }
    }
  });
  observer.observe(document.body, { childList: true, subtree: true, characterData: true });


  function getGmailInfo() {
    const hash = window.location.hash || '';
    const page = hash.includes('/') ? 'singleEmail' : 'list';
    let sender = '', date = '', subject = '', body = '';
    if (page === 'singleEmail') {
      const sEl = document.querySelector('.gD');
      const dEl = document.querySelector('span.g3');
      const tEl = document.querySelector('h2.hP');
      const bEl = document.querySelector('.a3s');
      sender = sEl ? sEl.textContent.trim() : '';
      date   = dEl ? (dEl.title || dEl.textContent).trim() : '';
      subject= tEl ? tEl.textContent.trim() : '';
      body   = bEl ? (bEl.innerText || bEl.textContent || '').trim() : '';
    }
    return { page, sender, date, subject, body };
  }
})();