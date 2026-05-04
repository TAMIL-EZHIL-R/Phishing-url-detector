console.log("🔥 BACKGROUND STARTED");

chrome.runtime.onInstalled.addListener(() => {
    console.log("✅ Extension Installed");
});

// 🔥 handle persistent connection
chrome.runtime.onConnect.addListener((port) => {

    console.log("🔌 PORT CONNECTED");

    let lastChecked = "";

    port.onMessage.addListener((message) => {

        console.log("🔥 RECEIVED:", message);

        if(message.type === "CHECK_URL"){

            // avoid duplicate API calls
            if(message.url === lastChecked) return;
            lastChecked = message.url;

            fetch("http://127.0.0.1:5000/api/check", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ url: message.url })
            })
            .then(res => res.json())
            .then(data => {

                console.log("✅ RESULT:", message.url, "→", data.prediction);

                // 🔥 send back to content script
                port.postMessage({
                    url: message.url,
                    prediction: data.prediction
                });

                // optional (for popup)
                chrome.storage.local.set({
                    lastUrl: message.url,
                    prediction: data.prediction
                });

            })
            .catch(err => {
                console.log("❌ FETCH ERROR:", err);
            });

        }

    });

});