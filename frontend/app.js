// =====================================
// ROADSENSE AI - ROAD INTELLIGENCE
// DASHBOARD JAVASCRIPT
// =====================================


// =====================================
// CURRENT DATE - AUTOMATICALLY CHANGES
// =====================================

const currentDate = document.getElementById("currentDate");

function updateCurrentDate() {
  const today = new Date();

  currentDate.textContent = today.toLocaleDateString(
    "en-IN",
    {
      weekday: "short",
      day: "numeric",
      month: "short",
      year: "numeric"
    }
  );
}

updateCurrentDate();


// =====================================
// KPI CALCULATIONS
// =====================================

const totalRoads = roadData.length;

const averageHealth =
  roadData.reduce((sum, road) => sum + road.health, 0)
  / totalRoads;

const criticalRoads =
  roadData.filter(road =>
    road.type === "critical"
  ).length;

const maintenanceRoads =
  roadData.filter(road =>
    road.priority === "High"
  ).length;


// =====================================
// NUMBER ANIMATION
// =====================================

function animateValue(element, start, end, duration = 1000) {

  let startTime = null;

  function animation(currentTime) {

    if (!startTime) {
      startTime = currentTime;
    }

    const progress = Math.min(
      (currentTime - startTime) / duration,
      1
    );

    const value = Math.floor(
      progress * (end - start) + start
    );

    element.textContent = value;

    if (progress < 1) {
      requestAnimationFrame(animation);
    }
  }

  requestAnimationFrame(animation);
}


// DISPLAY KPI VALUES

animateValue(
  document.getElementById("roadsCount"),
  0,
  totalRoads
);

animateValue(
  document.getElementById("healthScore"),
  0,
  Math.round(averageHealth)
);

animateValue(
  document.getElementById("criticalCount"),
  0,
  criticalRoads
);

animateValue(
  document.getElementById("maintenanceCount"),
  0,
  maintenanceRoads
);


// =====================================
// LEAFLET MAP
// =====================================

const map = L.map("map").setView(
  [13.0300, 80.2300],
  12
);


// ENGLISH MAP LABELS
L.tileLayer(
  "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
  {
    maxZoom: 19,
    attribution: "© OpenStreetMap contributors"
  }
).addTo(map);


// Layer groups for roads
let roadLayers = [];


// =====================================
// GET ROAD COLOR
// =====================================

function getRoadColor(type) {

  if (type === "healthy") {
    return "#18a874"; // GREEN
  }

  if (type === "moderate") {
    return "#f59e0b"; // YELLOW
  }

  return "#ef4444"; // RED
}


// =====================================
// ROAD POPUP
// =====================================

function createRoadPopup(road) {

  return `
    <div style="
      font-family: Inter, sans-serif;
      min-width: 190px;
      padding: 4px;
    ">

      <strong style="
        font-size: 15px;
        color: #162033;
      ">
        ${road.name}
      </strong>

      <hr style="
        border: none;
        border-top: 1px solid #e8ecf3;
        margin: 10px 0;
      ">

      <p style="margin: 5px 0;">
        <b>Road ID:</b> ${road.id}
      </p>

      <p style="margin: 5px 0;">
        <b>Health Score:</b>
        ${road.health}/100
      </p>

      <p style="margin: 5px 0;">
        <b>Issue:</b> ${road.issue}
      </p>

      <p style="margin: 5px 0;">
        <b>Risk:</b> ${road.risk}
      </p>

    </div>
  `;
}


// =====================================
// RENDER COLOURED ROAD SEGMENTS
// =====================================

function renderRoads(filter = "all") {

  // Remove previous roads
  roadLayers.forEach(layer => {
    map.removeLayer(layer);
  });

  roadLayers = [];


  // Filter road data
  const filteredRoads = roadData.filter(road => {

    if (filter === "all") {
      return true;
    }

    return road.type === filter;
  });


  // Draw each road
  filteredRoads.forEach(road => {

    const color = getRoadColor(road.type);


    // MAIN ROAD LINE
    const roadLine = L.polyline(
      road.coordinates,
      {
        color: color,
        weight: 9,
        opacity: 0.9,
        lineCap: "round",
        lineJoin: "round"
      }
    ).addTo(map);


    roadLine.bindPopup(
      createRoadPopup(road)
    );


    // Add tooltip with road name
    roadLine.bindTooltip(
      road.name,
      {
        permanent: false,
        direction: "top",
        sticky: true
      }
    );


    // Add centre marker
    const centerIndex =
      Math.floor(
        road.coordinates.length / 2
      );

    const center =
      road.coordinates[centerIndex];


    const marker = L.circleMarker(
      center,
      {
        radius: 6,
        fillColor: color,
        color: "#ffffff",
        weight: 2,
        fillOpacity: 1
      }
    ).addTo(map);


    marker.bindPopup(
      createRoadPopup(road)
    );


    // Store layers
    roadLayers.push(roadLine);
    roadLayers.push(marker);

  });


  // When filtered, automatically zoom
  if (filter !== "all" && filteredRoads.length > 0) {

    const allCoordinates =
      filteredRoads.flatMap(
        road => road.coordinates
      );

    map.fitBounds(
      allCoordinates,
      {
        padding: [40, 40],
        maxZoom: 14
      }
    );
  }

}


// Initial render
renderRoads();


// =====================================
// MAP FILTER BUTTONS
// =====================================

document
  .querySelectorAll(".filter-btn")
  .forEach(button => {

    button.addEventListener("click", () => {

      // Remove active from all buttons
      document
        .querySelectorAll(".filter-btn")
        .forEach(btn => {
          btn.classList.remove("active");
        });


      // Add active to clicked button
      button.classList.add("active");


      // Get filter
      const selectedFilter =
        button.dataset.filter;


      // Render filtered roads
      renderRoads(selectedFilter);

    });

  });


// =====================================
// PRIORITY ALERTS
// =====================================

const alertsList =
  document.getElementById("alertsList");


function renderAlerts() {

  alertsList.innerHTML = "";

  alertsData.forEach(alert => {

    const icon =
      alert.level === "high"
        ? "fa-triangle-exclamation"
        : "fa-road";


    const alertHTML = `
      <div class="alert-item">

        <div class="alert-icon ${alert.level}">
          <i class="fa-solid ${icon}"></i>
        </div>

        <div class="alert-content">
          <h4>${alert.title}</h4>

          <p>${alert.description}</p>

          <div class="alert-score">
            ${alert.score}
          </div>
        </div>

      </div>
    `;

    alertsList.innerHTML += alertHTML;

  });

}

renderAlerts();


// =====================================
// ROAD HEALTH TREND CHART
// =====================================

const healthChart = new Chart(
  document.getElementById("healthChart"),
  {
    type: "line",

    data: {
      labels: healthTrendData.labels,

      datasets: [
        {
          label: "Health Score",

          data: healthTrendData.values,

          borderColor: "#246bfd",

          backgroundColor:
            "rgba(36, 107, 253, 0.08)",

          fill: true,

          tension: 0.4,

          borderWidth: 3,

          pointRadius: 4,

          pointBackgroundColor:
            "#246bfd"
        }
      ]
    },

    options: {
      responsive: true,

      plugins: {
        legend: {
          display: false
        }
      },

      scales: {
        y: {
          min: 50,
          max: 100,

          grid: {
            color: "#eef1f6"
          }
        },

        x: {
          grid: {
            display: false
          }
        }
      }
    }
  }
);


// =====================================
// ISSUE DISTRIBUTION CHART
// =====================================

const issueChart = new Chart(
  document.getElementById("issueChart"),
  {
    type: "doughnut",

    data: {
      labels: issueDistribution.labels,

      datasets: [
        {
          data:
            issueDistribution.values,

          backgroundColor: [
            "#ef4444",
            "#f59e0b",
            "#7c5cff",
            "#18a874"
          ],

          borderWidth: 0
        }
      ]
    },

    options: {
      responsive: true,

      cutout: "70%",

      plugins: {
        legend: {
          position: "bottom",

          labels: {
            boxWidth: 10,
            padding: 15
          }
        }
      }
    }
  }
);


// =====================================
// MAINTENANCE TABLE
// =====================================

const maintenanceTable =
  document.getElementById(
    "maintenanceTable"
  );


function getScoreClass(score) {

  if (score >= 80) {
    return "score-good";
  }

  if (score >= 60) {
    return "score-medium";
  }

  return "score-bad";
}


function getPriorityClass(priority) {

  if (priority === "High") {
    return "priority-high";
  }

  if (priority === "Medium") {
    return "priority-medium";
  }

  return "score-good";
}


function renderMaintenanceTable() {

  maintenanceTable.innerHTML = "";


  roadData.forEach(road => {

    const row =
      document.createElement("tr");


    row.innerHTML = `

      <td class="road-id">
        ${road.id}
      </td>

      <td>
        <strong>${road.name}</strong>
        <br>

        <span style="
          color:#73809a;
          font-size:10px;
        ">
          ${road.location}
        </span>
      </td>

      <td>
        <span class="
          score-badge
          ${getScoreClass(road.health)}
        ">
          ${road.health}/100
        </span>
      </td>

      <td>
        ${road.issue}
      </td>

      <td>
        <span class="risk-badge">
          ${road.risk}
        </span>
      </td>

      <td>
        <span class="
          priority-badge
          ${getPriorityClass(road.priority)}
        ">
          ${road.priority}
        </span>
      </td>

      <td>
        <button
          class="view-btn"
          onclick="focusRoad('${road.id}')"
        >
          View on Map
        </button>
      </td>

    `;

    maintenanceTable.appendChild(row);

  });

}


renderMaintenanceTable();


// =====================================
// FOCUS SELECTED ROAD ON MAP
// =====================================

function focusRoad(roadId) {

  const road =
    roadData.find(
      item => item.id === roadId
    );


  if (!road) {
    return;
  }


  // Scroll to map
  document
    .getElementById("map-section")
    .scrollIntoView({
      behavior: "smooth",
      block: "start"
    });


  // Wait for scroll then zoom map
  setTimeout(() => {

    // Show all roads first
    document
      .querySelectorAll(".filter-btn")
      .forEach(btn => {

        btn.classList.remove("active");

        if (
          btn.dataset.filter === "all"
        ) {
          btn.classList.add("active");
        }

      });


    renderRoads("all");


    // Zoom to selected road
    const selectedRoadLine =
      roadLayers.find(layer => {

        return (
          layer instanceof L.Polyline &&
          !(layer instanceof L.CircleMarker) &&
          layer.getLatLngs().length > 0 &&
          JSON.stringify(
            layer.getLatLngs().map(point => [
              Number(point.lat.toFixed(4)),
              Number(point.lng.toFixed(4))
            ])
          ) ===
          JSON.stringify(
            road.coordinates.map(point => [
              Number(point[0].toFixed(4)),
              Number(point[1].toFixed(4))
            ])
          )
        );

      });


    if (selectedRoadLine) {

      map.fitBounds(
        selectedRoadLine.getBounds(),
        {
          padding: [60, 60],
          maxZoom: 16
        }
      );


      setTimeout(() => {
        selectedRoadLine.openPopup();
      }, 500);

    }

  }, 700);

}


// =====================================
// REFRESH BUTTON
// =====================================

document
  .getElementById("refreshBtn")
  .addEventListener("click", function () {

    const icon =
      this.querySelector("i");

    icon.classList.add("fa-spin");


    setTimeout(() => {

      icon.classList.remove("fa-spin");

      updateCurrentDate();

      renderRoads("all");

      alert(
        "Dashboard refreshed successfully!"
      );

    }, 700);

  });


// =====================================
// DOWNLOAD REPORT
// =====================================

document
  .getElementById("downloadReportBtn")
  .addEventListener("click", () => {

    const report = `
ROADSENSE AI - ROAD INTELLIGENCE REPORT
=======================================

Total Roads Monitored: ${totalRoads}
Average Health Score: ${Math.round(averageHealth)}/100
Critical Roads: ${criticalRoads}
High Maintenance Priority: ${maintenanceRoads}

ROAD DETAILS
=======================================

${roadData.map(road => `
Road ID: ${road.id}
Road: ${road.name}
Health Score: ${road.health}/100
Issue: ${road.issue}
Risk Level: ${road.risk}
Priority: ${road.priority}
`).join("\n")}

Generated: ${new Date().toLocaleString()}
    `;


    const blob = new Blob(
      [report],
      {
        type: "text/plain"
      }
    );


    const url =
      URL.createObjectURL(blob);


    const link =
      document.createElement("a");


    link.href = url;

    link.download =
      "RoadSense-AI-Report.txt";


    link.click();

    URL.revokeObjectURL(url);

  });