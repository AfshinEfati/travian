document.addEventListener("DOMContentLoaded", () => {
    document.getElementById('startScript').addEventListener('click', () => {
        const my_x = parseInt(document.getElementById('my_x').value);
        const my_y = parseInt(document.getElementById('my_y').value);
        const min_distance = parseInt(document.getElementById('min_distance').value);
        const max_distance = parseInt(document.getElementById('max_distance').value);
        const min_population = parseInt(document.getElementById('min_population').value);
        const max_population = parseInt(document.getElementById('max_population').value);

        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs[0].url.includes("speedtra.com")) {
                chrome.tabs.sendMessage(tabs[0].id, {
                    action: "runScript",
                    params: { my_x, my_y, min_distance, max_distance, min_population, max_population }
                }, (response) => {
                    if (chrome.runtime.lastError) {
                        console.error("Error sending message:", chrome.runtime.lastError);
                        alert("Error: Unable to connect to the content script. Please make sure you're on a supported page.");
                    } else {
                        console.log("Script started:", response.status);
                    }
                });
            } else {
                alert("Please open this extension on a supported speedtra.com page.");
            }
        });
    });
});
