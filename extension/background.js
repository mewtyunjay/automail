// background.js

const API_BASE_URL = 'http://localhost:8000'; // Make sure this matches your backend
console.log('Background script V3 loaded.'); // V3

// Function to update storage with status and content
function updateSummaryState(status, content) {
    console.log(`Updating summary state: Status=${status}, Content Length=${content?.length || 0}`);
    chrome.storage.local.set({ 
        summaryStatus: status, 
        emailSummary: content 
    }, () => {
        if (chrome.runtime.lastError) {
            console.error("Error setting summary state in storage:", chrome.runtime.lastError);
        } else {
            console.log("Summary state stored successfully.");
        }
    });
}


// Listen for messages from the content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('Background script received message:', request.action);
    // Original action check
    if (request.action === 'summarizeEmail') { 
        if (!request.content) { // Check for content
            console.error('Received summarizeEmail request but no content provided.');
            updateSummaryState('error', 'Error: No content provided by content script.');
            sendResponse({ status: 'error', message: 'No content provided' });
            return true; 
        }
        
        const emailContent = request.content; // Get the content
        console.log('Content received. Length:', emailContent.length);
        
        // Set initial loading state
        updateSummaryState('loading', 'Sending content to backend...'); // Updated loading message
        sendResponse({ status: 'processing', message: 'Summarization request sent to backend.'});

        // --- Call backend with Content --- 
        // Corrected backend path based on router prefix
        const backendUrl = `${API_BASE_URL}/email/summarize-content`; 
        console.log('Sending request to backend API (unsecured):', backendUrl);

        fetch(backendUrl, { // Use the corrected URL
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ content: emailContent }) // Send content in body
        })
        .then(response => {
            console.log('Received response from backend. Status:', response.status);
            if (!response.ok) {
                return response.text().then(text => {
                     const errorDetail = `Backend responded with ${response.status}. Details: ${text}`;
                     console.error(errorDetail);
                     throw new Error(errorDetail);
                 });
            }
            return response.text(); 
        })
        .then(summaryText => {
            console.log('Summary received from backend. Length:', summaryText?.length || 0);
            updateSummaryState('success', summaryText || 'Backend returned empty summary.');
        })
        .catch(error => {
            const errorMsg = `Error during backend call: ${error?.message || error}`;
            console.error('Error summarizing email:', errorMsg);
            updateSummaryState('error', `Summarization Failed: ${errorMsg}`); 
        });
        // --- END SECTION ---
        
        return true; // Indicates that the response will be sent asynchronously 
    }
});

// Optional: Log installation or update details
chrome.runtime.onInstalled.addListener(() => {
    console.log('Gmail Summarizer extension installed/updated.');
    // Clear previous state on install/update?
    // chrome.storage.local.remove(['summaryStatus', 'emailSummary']);
});
