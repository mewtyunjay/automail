// popup.js

document.addEventListener('DOMContentLoaded', () => {
    const summaryContentElement = document.getElementById('summary-content');
    const statusElement = document.getElementById('status-message'); // Assuming you add a status element

    if (!summaryContentElement) {
        console.error("Element with ID 'summary-content' not found in popup.html");
        if(statusElement) statusElement.textContent = 'Error: Popup HTML is missing elements.';
        return;
    }
     if (!statusElement) {
        console.warn("Element with ID 'status-message' not found in popup.html. Status updates will be limited.");
    }

    console.log('Popup loaded. Fetching summary state from storage...');

    // Fetch the current state from storage
    chrome.storage.local.get(['summaryStatus', 'emailSummary'], (result) => {
        if (chrome.runtime.lastError) {
            console.error("Error retrieving summary state:", chrome.runtime.lastError);
            summaryContentElement.textContent = 'Error retrieving summary state.';
             if(statusElement) statusElement.textContent = 'Error';
            return;
        }

        const status = result.summaryStatus;
        const summary = result.emailSummary;

        console.log('Retrieved state:', { status, summaryLength: summary?.length });

        if (status === 'loading') {
            summaryContentElement.innerHTML = ''; // Clear previous summary
            if(statusElement) statusElement.textContent = '⏳ Loading summary...';
            else summaryContentElement.textContent = '⏳ Loading summary...';
        } else if (status === 'success') {
            // Render HTML content safely if needed, or just use textContent
             summaryContentElement.innerHTML = summary || 'Summary not available.'; // Use innerHTML if summary is HTML
            // summaryContentElement.textContent = summary || 'Summary not available.'; // Use textContent for plain text
             if(statusElement) statusElement.textContent = '✅ Summary Ready';
        } else if (status === 'error') {
            summaryContentElement.textContent = summary || 'An unknown error occurred.'; // Display the error message
             if(statusElement) statusElement.textContent = '❌ Error';
        } else {
            // Default state (e.g., before first summary attempt)
            summaryContentElement.textContent = 'Click the \"Summarize\" button on an email first.';
             if(statusElement) statusElement.textContent = 'Idle';
        }
    });

    // Optional: Listen for storage changes while the popup is open
    chrome.storage.onChanged.addListener((changes, namespace) => {
         if (namespace === 'local' && (changes.summaryStatus || changes.emailSummary)) {
            console.log('Storage changed, reloading popup content...');
             // Re-fetch and update display logic - could call the above fetching logic again
              chrome.storage.local.get(['summaryStatus', 'emailSummary'], (updatedResult) => {
                 // (Same display logic as above based on updatedResult.summaryStatus and updatedResult.emailSummary)
                 const newStatus = updatedResult.summaryStatus;
                 const newSummary = updatedResult.emailSummary;
                 console.log('Updated state:', { newStatus, newSummaryLength: newSummary?.length });
                 if (newStatus === 'loading') {
                     summaryContentElement.innerHTML = '';
                     if(statusElement) statusElement.textContent = '⏳ Loading summary...';
                      else summaryContentElement.textContent = '⏳ Loading summary...';
                 } else if (newStatus === 'success') {
                      summaryContentElement.innerHTML = newSummary || 'Summary not available.';
                      if(statusElement) statusElement.textContent = '✅ Summary Ready';
                 } else if (newStatus === 'error') {
                      summaryContentElement.textContent = newSummary || 'An unknown error occurred.';
                      if(statusElement) statusElement.textContent = '❌ Error';
                 } // Don't reset to idle state on change, keep last known state
              });
         }
    });
});
