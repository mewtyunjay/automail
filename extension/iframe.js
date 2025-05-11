window.parent.postMessage({ type: 'getGmailInfo' }, '*');

let lastEmailContent = '';
let lastPageType = '';

window.addEventListener('message', event => {
  if (event.data && event.data.type === 'gmailInfo') {
    const { page, sender, date, subject, body } = event.data;
    lastPageType = page;
    let emailContent = '';
    if (page === 'singleEmail') {
      emailContent = body || '';
    }
    lastEmailContent = emailContent;
    document.getElementById('content').innerHTML = `
      <p><b>View:</b> ${page}</p>
      <p><b>From:</b> ${sender}</p>
      <p><b>Date:</b> ${date}</p>
      <p><b>Subject:</b> ${subject}</p>
    `;
    // Hide summary result on new email
    document.getElementById('summary-result').style.display = 'none';
    document.getElementById('summary-result').innerText = '';
    // Enable/disable summarise button
    const btn = document.getElementById('summarise-btn');
    if (btn) {
      btn.disabled = !(page === 'singleEmail' && emailContent && emailContent.length > 0);
    }
  }
});

const closeBtn = document.getElementById('close-btn');
if (closeBtn) {
  closeBtn.addEventListener('click', () => {
    window.parent.postMessage({ type: 'closeIframe' }, '*');
  });
}

const summariseBtn = document.getElementById('summarise-btn');
if (summariseBtn) {
  summariseBtn.addEventListener('click', async () => {
    const summaryDiv = document.getElementById('summary-result');
    summaryDiv.style.display = 'block';
    summaryDiv.innerText = 'Summarising...';
    summariseBtn.disabled = true;
    try {
      const response = await fetch('http://localhost:8000/email/summarize-content', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content: lastEmailContent })
      });
      if (!response.ok) {
        throw new Error('Failed to summarise: ' + (await response.text()));
      }
      const summary = await response.text();
      summaryDiv.innerText = summary;
    } catch (e) {
      summaryDiv.innerText = 'Error: ' + e.message;
    }
    summariseBtn.disabled = false;
  });
}