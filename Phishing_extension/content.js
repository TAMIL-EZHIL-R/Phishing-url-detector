console.log("✅ CONTENT SCRIPT LOADED");

const port = chrome.runtime.connect({ name: "phishing-check" });

let lastUrl = "";
let tooltip = null;
let cache = {};
let currentHoverUrl = null;
let debounceTimer = null;

// ==================================================
// TOOLTIP
// ==================================================
function createTooltip() {
    tooltip = document.createElement("div");

    Object.assign(tooltip.style, {
        position: "fixed",
        padding: "6px 10px",
        background: "#333",
        color: "white",
        fontSize: "12px",
        borderRadius: "6px",
        zIndex: "2147483647",
        pointerEvents: "none",
        display: "none",
        fontFamily: "Arial",
        boxShadow: "0 2px 10px rgba(0,0,0,0.3)"
    });

    document.documentElement.appendChild(tooltip);
}

function moveTooltip(x, y) {
    tooltip.style.left = (x + 15) + "px";
    tooltip.style.top = (y + 15) + "px";
}

function showTooltip(text, color) {
    tooltip.innerText = text;
    tooltip.style.background = color;
    tooltip.style.display = "block";
}

function hideTooltip() {
    tooltip.style.display = "none";
}

// ==================================================
// BACKEND RESPONSE
// ==================================================
port.onMessage.addListener((msg) => {

    cache[msg.url] = msg.prediction;

    // ❗ Only update if still hovering same URL
    if (msg.url !== currentHoverUrl) return;

    if (msg.prediction === "phishing") {
        showTooltip("🚨 Phishing", "#d9534f");
    } else {
        showTooltip("✅ Safe", "#28a745");
    }
});

// ==================================================
// FAST URL EXTRACTION
// ==================================================
function extractURL(text) {
    if (!text) return null;

    // Limit text size (🔥 performance boost)
    text = text.slice(0, 200);

    const match = text.match(/https?:\/\/[^\s]+/);
    return match ? match[0] : null;
}

// ==================================================
// MAIN HOVER LOGIC (OPTIMIZED)
// ==================================================
document.addEventListener("mousemove", function (e) {

    moveTooltip(e.clientX, e.clientY);

    clearTimeout(debounceTimer);

    debounceTimer = setTimeout(() => {

        let url = null;

        // ✅ Anchor
        const link = e.target.closest("a");
        if (link && link.href) {
            url = link.href;
        }

        // ✅ Text (lighter)
        else if (e.target.textContent) {
            url = extractURL(e.target.textContent);
        }

        if (!url) {
            currentHoverUrl = null;
            hideTooltip();
            return;
        }

        if (url === currentHoverUrl) return;

        currentHoverUrl = url;

        // ==================================================
        // INSTANT UI
        // ==================================================
        showTooltip("⏳ Checking...", "#444");

        // ==================================================
        // CACHE
        // ==================================================
        if (cache[url]) {
            const pred = cache[url];

            if (pred === "phishing") {
                showTooltip("🚨 Phishing", "#d9534f");
            } else {
                showTooltip("✅ Safe", "#28a745");
            }
            return;
        }

        // ==================================================
        // BACKEND CALL
        // ==================================================
        port.postMessage({
            type: "CHECK_URL",
            url: url
        });

    }, 150); // 🔥 debounce delay (tune 100–300)

});

// Init
createTooltip();