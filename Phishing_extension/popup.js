document.addEventListener("DOMContentLoaded", function(){

    chrome.storage.local.get(["lastUrl", "prediction"], function(data){

        const urlEl = document.getElementById("url");
        const resultBox = document.getElementById("resultBox");

        urlEl.innerText = data.lastUrl || "No URL";

        if(data.prediction === "phishing"){
            resultBox.innerText = "🚨 Phishing";
            resultBox.style.background = "#ffe5e5";
            resultBox.style.color = "#d9534f";
        }
        else if(data.prediction === "legitimate"){
            resultBox.innerText = "✅ Safe";
            resultBox.style.background = "#e6ffed";
            resultBox.style.color = "#28a745";
        }
        else{
            resultBox.innerText = "Hover a link";
            resultBox.style.background = "#eee";
            resultBox.style.color = "#333";
        }

    });

});