const chartInstances = {};

function formatIndianPrice(value) {
    try {
        return new Intl.NumberFormat("en-IN", {
            style: "currency",
            currency: "INR",
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        }).format(Number(value || 0));
    } catch {
        return "₹0.00";
    }
}

function getCSRFToken() {
    const name = "csrftoken=";
    const decodedCookie = decodeURIComponent(document.cookie || "");
    const cookies = decodedCookie.split(";");
    for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.indexOf(name) === 0) {
            return cookie.substring(name.length, cookie.length);
        }
    }
    return "";
}

async function loadLineChart(ticker, period, canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    try {
        const response = await fetch(`/api/price/${ticker}/?period=${period}`);
        const data = await response.json();
        const values = data.series || [];
        if (!values.length) return;

        const ctx = canvas.getContext("2d");
        const isUp = values[values.length - 1] >= values[0];
        const lineColor = isUp ? "#00d09c" : "#eb5757";

        const gradient = ctx.createLinearGradient(0, 0, 0, 220);
        gradient.addColorStop(0, isUp ? "rgba(0,208,156,0.25)" : "rgba(235,87,87,0.25)");
        gradient.addColorStop(1, "rgba(0,0,0,0)");

        if (chartInstances[canvasId]) {
            chartInstances[canvasId].destroy();
        }

        chartInstances[canvasId] = new Chart(ctx, {
            type: "line",
            data: {
                labels: values.map((_, i) => i + 1),
                datasets: [
                    {
                        data: values,
                        borderColor: lineColor,
                        backgroundColor: gradient,
                        fill: true,
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.35,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                return formatIndianPrice(context.parsed.y);
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        display: false,
                        grid: { display: false },
                    },
                    y: {
                        ticks: {
                            color: "#8a8a8a",
                            maxTicksLimit: 4,
                            callback: (value) => formatIndianPrice(value),
                        },
                        grid: { display: false },
                    },
                },
            },
        });
    } catch (error) {
        console.error("Line chart load error", error);
    }
}

async function loadMiniSparkline(ticker, svgElement) {
    if (!svgElement) return;
    try {
        const response = await fetch(`/api/price/${ticker}/?period=1m`);
        const data = await response.json();
        const series = data.series || [];
        if (!series.length) return;
        drawSparkline(series, svgElement, series[series.length - 1] >= series[0]);
    } catch (error) {
        console.error("Sparkline load error", error);
    }
}

function drawSparkline(series, svgElement, isUp) {
    const width = 60;
    const height = 24;
    const min = Math.min(...series);
    const max = Math.max(...series);
    const range = max - min || 1;

    const points = series.map((value, index) => {
        const x = (index / (series.length - 1)) * width;
        const y = height - ((value - min) / range) * height;
        return `${x},${y}`;
    });

    svgElement.innerHTML = `<polyline fill="none" stroke="${isUp ? "#00d09c" : "#eb5757"}" stroke-width="2" points="${points.join(" ")}" />`;
}

async function loadPrediction(ticker) {
    const card = document.getElementById("predictionCard");
    if (!card) return;
    try {
        const response = await fetch(`/api/predict/${ticker}/`);
        const data = await response.json();
        const priceEl = document.getElementById("predictedPrice");
        const confidenceEl = document.getElementById("predConfidence");
        const fillEl = document.getElementById("predFill");
        const badgeEl = document.getElementById("predBadge");

        if (priceEl) priceEl.textContent = data.predicted_price_display || formatIndianPrice(data.predicted_price);
        if (confidenceEl) confidenceEl.textContent = `${data.confidence}%`;
        if (fillEl) fillEl.style.width = `${Math.min(100, Math.max(0, data.confidence || 0))}%`;
        if (badgeEl) {
            badgeEl.textContent = data.direction;
            badgeEl.className = data.direction === "BUY" ? "badge-buy" : data.direction === "SELL" ? "badge-sell" : "badge-hold";
        }
    } catch (error) {
        console.error("Prediction load error", error);
    }
}

async function addToWatchlist(ticker, exchange = "NSE") {
    try {
        const body = new URLSearchParams({ ticker, exchange });
        const response = await fetch("/watchlist/add/", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-CSRFToken": getCSRFToken(),
            },
            body,
        });
        return await response.json();
    } catch (error) {
        console.error("Add to watchlist error", error);
        return { status: "error" };
    }
}

function setupRangeTabs() {
    document.querySelectorAll(".range-tabs").forEach((tabRow) => {
        const ticker = tabRow.dataset.ticker;
        const canvasId = tabRow.dataset.canvas;
        tabRow.querySelectorAll(".tab-item").forEach((tab) => {
            tab.addEventListener("click", () => {
                tabRow.querySelectorAll(".tab-item").forEach((node) => node.classList.remove("active"));
                tab.classList.add("active");
                loadLineChart(ticker, tab.dataset.period, canvasId);
            });
        });
    });
}

function setupAutoRefresh() {
    const ticker = document.getElementById("stockChart")?.dataset?.ticker;
    if (!ticker) return;
    setInterval(() => {
        const activePeriod = document.querySelector(".range-tabs .tab-item.active")?.dataset?.period || "1d";
        loadLineChart(ticker, activePeriod, "stockChart");
        loadPrediction(ticker);
    }, 60000);
}

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".mini-line").forEach((svg) => {
        const series = (svg.dataset.series || "").split(",").map(Number).filter((n) => !isNaN(n));
        if (series.length) {
            drawSparkline(series, svg, svg.dataset.up === "1");
        }
    });
    setupRangeTabs();
    setupAutoRefresh();
});
