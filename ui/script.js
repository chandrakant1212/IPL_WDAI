const PLAYER_DATA = {
    name: "Virat Kohli",
    role: "Batsman",
    battingStyle: "Right Handed Bat",
    bowlingStyle: "Right Arm Medium",
    team: "Royal Challengers Bengaluru",
    image: "../player_images/royal-challengers-bengaluru__virat-kohli.jpg",
    imageFallback: "https://static.cricbuzz.com/a/img/v1/152x152/i1/c1413/virat-kohli.jpg",
    batting: {
        Matches: "252", Innings: "245", Runs: "8304",
        Balls: "5932", Highest: "113", Average: "38.17",
        "SR": "140.00", "Not Outs": "38", "4s": "726",
        "6s": "268", Ducks: "11", "50s": "55", "100s": "8",
    },
    bowling: {
        Matches: "252", Innings: "31", Balls: "164",
        Runs: "199", Wickets: "4", Avg: "49.75",
        Econ: "7.28", SR: "41.00", BBI: "1/5",
    },
};

document.addEventListener("DOMContentLoaded", () => renderPlayer(PLAYER_DATA));

function renderPlayer(p) {
    document.getElementById("playerName").textContent = p.name;
    document.getElementById("playerRole").textContent = p.role;
    document.getElementById("teamBadge").textContent = p.team;
    document.getElementById("battingStyle").textContent = p.battingStyle;
    document.getElementById("bowlingStyle").textContent = p.bowlingStyle;

    const img = document.getElementById("playerImage");
    img.src = p.image;
    img.alt = p.name;
    img.onerror = () => {
        img.src = p.imageFallback;
        img.onerror = () => { img.style.display = "none"; };
    };

    const batHighlights = ["Runs", "Average", "SR", "100s"];
    buildGrid("battingStatsGrid", p.batting, batHighlights);

    const bowlHighlights = ["Wickets", "Econ", "BBI"];
    buildGrid("bowlingStatsGrid", p.bowling, bowlHighlights);

    if (!p.bowling || Object.keys(p.bowling).length === 0) {
        document.getElementById("bowlingStatsSection").style.display = "none";
    }
}

function buildGrid(containerId, stats, highlights) {
    const el = document.getElementById(containerId);
    if (!stats || Object.keys(stats).length === 0) {
        el.innerHTML = '<p style="color:#9ca3af;grid-column:1/-1;text-align:center">No data</p>';
        return;
    }
    el.innerHTML = Object.entries(stats)
        .map(([label, value]) => `
            <div class="stat-cell${highlights.includes(label) ? ' accent' : ''}">
                <div class="stat-num">${value || "—"}</div>
                <div class="stat-lbl">${label}</div>
            </div>`)
        .join("");
}
