const roadData = [
  {
    id: "TN-CHN-1042",
    name: "Anna Salai",
    location: "Teynampet, Chennai",
    health: 42,
    issue: "Multiple Potholes",
    risk: "High",
    priority: "High",
    type: "critical",

    coordinates: [
      [13.0435, 80.2465],
      [13.0410, 80.2480],
      [13.0385, 80.2500],
      [13.0360, 80.2520]
    ]
  },

  {
    id: "TN-CHN-2087",
    name: "OMR Road",
    location: "Sholinganallur, Chennai",
    health: 71,
    issue: "Surface Wear",
    risk: "Medium",
    priority: "Medium",
    type: "moderate",

    coordinates: [
      [12.9040, 80.2290],
      [12.9015, 80.2270],
      [12.8990, 80.2250],
      [12.8965, 80.2230]
    ]
  },

  {
    id: "TN-CHN-3156",
    name: "ECR Road",
    location: "Thiruvanmiyur, Chennai",
    health: 88,
    issue: "No Major Issues",
    risk: "Low",
    priority: "Low",
    type: "healthy",

    coordinates: [
      [12.9870, 80.2590],
      [12.9845, 80.2620],
      [12.9820, 80.2650],
      [12.9795, 80.2680]
    ]
  },

  {
    id: "TN-CHN-4120",
    name: "GST Road",
    location: "Guindy, Chennai",
    health: 55,
    issue: "Road Damage",
    risk: "High",
    priority: "High",
    type: "critical",

    coordinates: [
      [13.0120, 80.2180],
      [13.0090, 80.2200],
      [13.0060, 80.2220],
      [13.0030, 80.2240]
    ]
  },

  {
    id: "TN-CHN-5021",
    name: "Poonamallee High Road",
    location: "Koyambedu, Chennai",
    health: 76,
    issue: "Minor Cracks",
    risk: "Medium",
    priority: "Medium",
    type: "moderate",

    coordinates: [
      [13.0710, 80.1950],
      [13.0690, 80.1910],
      [13.0670, 80.1870],
      [13.0650, 80.1830]
    ]
  },

  {
    id: "TN-CHN-6210",
    name: "Velachery Main Road",
    location: "Velachery, Chennai",
    health: 91,
    issue: "Healthy Surface",
    risk: "Low",
    priority: "Low",
    type: "healthy",

    coordinates: [
      [12.9850, 80.2210],
      [12.9815, 80.2190],
      [12.9780, 80.2170],
      [12.9745, 80.2150]
    ]
  }
];


const alertsData = [
  {
    title: "Critical Pothole Detected",
    description: "Multiple potholes detected on Anna Salai.",
    score: "Confidence: 96%",
    level: "high"
  },
  {
    title: "High Accident Risk",
    description: "GST Road shows increased accident-risk indicators.",
    score: "Risk Level: High",
    level: "high"
  },
  {
    title: "Surface Deterioration",
    description: "OMR Road requires maintenance inspection.",
    score: "Health Score: 71/100",
    level: "medium"
  }
];


const healthTrendData = {
  labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
  values: [78, 77, 76, 78, 75, 74, 75]
};


const issueDistribution = {
  labels: ["Potholes", "Cracks", "Surface Wear", "Healthy"],
  values: [18, 12, 25, 45]
};