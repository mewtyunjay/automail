// content.js

console.log("Automail content script V3 loaded."); // V3 marker

// Selectors based on common Gmail structure for the main action toolbar
const MAIN_TOOLBAR_SELECTOR = 'div.aeH div.G-atb'; // The main container for action buttons
// Target one of the button groups within the toolbar for insertion
const TOOLBAR_INSERTION_POINT_SELECTOR = 'div.aeH div.G-atb div.G-Ni:nth-of-type(3)'; 
const EMAIL_BODY_SELECTOR = 'div.a3s.aiL'; 
const BUTTON_ID = 'automail-summarize-btn';

function getEmailContent() {
    const emailBody = document.querySelector(EMAIL_BODY_SELECTOR);
    if (emailBody) {
        console.log('getEmailContent: Found email body.');
        return emailBody.innerHTML || emailBody.textContent || '';
    }
    console.log('getEmailContent: Email body not found using selector:', EMAIL_BODY_SELECTOR);
    return '';
}

function addSummarizeButton() {
    console.log('addSummarizeButton: Attempting to add button to main toolbar...');
    
    if (document.getElementById(BUTTON_ID)) {
        console.log('addSummarizeButton: Button already exists.');
        return; 
    }

    // Find the target insertion point within the main toolbar
    const insertionPoint = document.querySelector(TOOLBAR_INSERTION_POINT_SELECTOR);
    
    if (!insertionPoint) {
        // Add a small delay and retry once, as the toolbar might still be loading
        if (!window.addSummarizeButtonRetried) {
            window.addSummarizeButtonRetried = true;
            console.log('addSummarizeButton: Toolbar insertion point not found using selector:', TOOLBAR_INSERTION_POINT_SELECTOR, '. Retrying in 500ms...');
            setTimeout(addSummarizeButton, 500);
        }
         else {
            console.log('addSummarizeButton: Toolbar insertion point not found on retry. Button not added.');
            window.addSummarizeButtonRetried = false; // Reset for next attempt
         }
        return; 
    }
    console.log('addSummarizeButton: Found toolbar insertion point:', insertionPoint);
     window.addSummarizeButtonRetried = false; // Reset retry flag on success

    console.log("addSummarizeButton: Creating Summarize button element...");

    const summarizeBtnWrapper = document.createElement('div');
    summarizeBtnWrapper.className = 'G-Ni J-J5-Ji'; // Wrap button in standard Gmail div structure

    const summarizeBtn = document.createElement('div'); // Use div like other buttons
    summarizeBtn.id = BUTTON_ID;
    summarizeBtn.className = 'T-I J-J5-Ji L3'; // Use simpler classes for text button
    summarizeBtn.setAttribute('role', 'button');
    summarizeBtn.setAttribute('tabindex', '0');
    summarizeBtn.setAttribute('aria-label', 'Summarize Email');
    summarizeBtn.setAttribute('data-tooltip', 'Summarize Email');
    summarizeBtn.style.userSelect = 'none'; // Match other buttons
    summarizeBtn.style.padding = '0 8px'; // Add padding for text
    summarizeBtn.style.height = '28px'; // Match height of some other toolbar elements
    summarizeBtn.style.lineHeight = '28px'; // Center text vertically
    summarizeBtn.style.marginLeft = '8px'; // Add some space before

    summarizeBtn.textContent = 'Summarize'; // Set button text

    summarizeBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        console.log('Summarize button clicked!');
        
        // --- Get Email Content --- 
        const emailContent = getEmailContent(); 
        // --- End Get Email Content ---

        if (emailContent) { // Check if we got content
            console.log('Sending email content to background script.');
            // Provide visual feedback
            summarizeBtn.textContent = 'Summarizing...';
            summarizeBtn.disabled = true;

            // Send content with original action name
            chrome.runtime.sendMessage({ 
                action: 'summarizeEmail', // Original action name 
                content: emailContent     // Send content
            }, (response) => {
                // Re-enable button regardless of background response for now
                // More robust error handling could be added based on response
                summarizeBtn.textContent = 'Summarize'; 
                summarizeBtn.disabled = false;
                 if (chrome.runtime.lastError) { 
                     console.error("Error sending message:", chrome.runtime.lastError.message);
                      alert('Error initiating summary. Check console.'); // Simple user feedback
                 } else {
                     console.log("Message sent to background script.", response);
                     // Maybe give a small success indication?
                 }
            });
        } else {
            // Handle case where content couldn't be retrieved
            console.log('Could not retrieve email content.');
            alert('Could not retrieve email content to summarize.');
        }
    });

    summarizeBtnWrapper.appendChild(summarizeBtn);

    // Insert the button wrapper before the target group (e.g., before 'Mark as unread')
    insertionPoint.parentNode.insertBefore(summarizeBtnWrapper, insertionPoint);
    console.log('addSummarizeButton: Summarize button added to main toolbar before:', insertionPoint);
}

// Debounce function to limit how often addSummarizeButton is called
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
};

// Simple debounce function
function debounceAddSummarizeButton(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
};

// Debounced version of the button adding function
const debouncedAddSummarizeButton = debounceAddSummarizeButton(addSummarizeButton, 500); // 500ms delay

// Callback function to execute when mutations are observed
const callback = function(mutationsList, observer) {
    // Look for mutations that indicate the email view might have changed
    // A simple check is often just to try adding the button again
    // More specific checks could be added if performance becomes an issue
    for(const mutation of mutationsList) {
        if (mutation.type === 'childList' || mutation.type === 'subtree') {
             // Check if the specific toolbar we target exists now or has changed
            const targetToolbar = document.querySelector(MAIN_TOOLBAR_SELECTOR);
            const emailBody = document.querySelector(EMAIL_BODY_SELECTOR); // Check if email body is present too
             if (targetToolbar && emailBody) { // Only try if both seem present
                 debouncedAddSummarizeButton();
                // Optimization: maybe disconnect observer temporarily if needed
                 break; // No need to check other mutations if we decided to run
             }
        }
    }
};

// Create an observer instance linked to the callback function
const observer = new MutationObserver(callback);

// Start observing the target node for configured mutations
// We observe the body, as Gmail heavily modifies its children
// More specific targets might be possible but risk missing changes
const config = { childList: true, subtree: true };

// Wait for the body to be ready before observing
if (document.readyState === 'loading') {  // Loading hasn't finished yet
  document.addEventListener('DOMContentLoaded', () => {
    observer.observe(document.body, config);
    console.log('MutationObserver started observing body after DOMContentLoaded.');
     // Initial attempt to add the button on load
     addSummarizeButton(); 
  });
} else {  // `DOMContentLoaded` has already fired
  observer.observe(document.body, config);
  console.log('MutationObserver started observing body immediately.');
   // Initial attempt to add the button on load
   addSummarizeButton(); 
}

// Initial attempt in case the DOM is ready faster than observer setup
// (Redundant if DOMContentLoaded hasn't fired, handled by addSummarizeButton calls above)
// setTimeout(addSummarizeButton, 500); 

console.log('MutationObserver setup complete.');

// Note: It might be beneficial to disconnect the observer when the script is unloaded 
// or under certain conditions to save resources, but for basic functionality,
// observing the body usually works robustly for SPAs.
