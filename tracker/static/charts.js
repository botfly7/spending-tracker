/*
 * Dashboard charts (Chart.js 4).
 *
 * Reads the JSON the server embeds in <script id="chart-data"> and draws two charts:
 *   - spending by category: ranked horizontal bars, one color
 *   - spending by month: columns, with the selected month highlighted and the rest grey
 *
 * Colors come from the CSS variables in style.css, so the charts follow light/dark mode.
 * If the data or Chart.js is missing (for example offline), nothing happens: the chart
 * cards stay hidden and the tables on the page carry the same figures.
 */
(function () {
  "use strict";

  var dataElement = document.getElementById("chart-data");
  if (!dataElement || typeof Chart === "undefined") {
    return;
  }

  var data = JSON.parse(dataElement.textContent);
  var currency = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var colorScheme = window.matchMedia("(prefers-color-scheme: dark)");
  var charts = [];

  function dollars(cents) {
    return cents / 100;
  }

  // Axis ticks: whole dollars under 10,000, compact (10K) above it.
  function formatTick(value) {
    if (!Number.isInteger(value)) {
      return currency.format(value);
    }
    if (value >= 10000) {
      return "$" + value / 1000 + "K";
    }
    return "$" + value.toLocaleString("en-US");
  }

  function readTheme() {
    var root = getComputedStyle(document.documentElement);
    function read(name) {
      return root.getPropertyValue(name).trim();
    }
    return {
      text: read("--text"),
      muted: read("--muted"),
      grid: read("--border"),
      accent: read("--accent"),
      context: read("--chart-context"),
      font: getComputedStyle(document.body).fontFamily,
    };
  }

  // Reveal the card around a canvas (cards are hidden until Chart.js is known to be here).
  function reveal(canvas) {
    var card = canvas.closest(".chart-card");
    if (card) {
      card.hidden = false;
    }
  }

  function categoryChart(colors) {
    var canvas = document.getElementById("category-chart");
    var categories = data.categories;
    if (!canvas || !categories || !categories.labels.length) {
      return null;
    }
    reveal(canvas);
    // Room for every row plus the axis, so the axis labels are never cut off.
    canvas.parentNode.style.height = Math.max(180, categories.labels.length * 36 + 56) + "px";

    var options = {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      // Hovering anywhere along a row shows its tooltip, not just over the thin bar.
      interaction: { mode: "index", axis: "y", intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function (item) {
              return currency.format(item.parsed.x);
            },
          },
        },
      },
      scales: {
        x: {
          beginAtZero: true,
          grid: { color: colors.grid },
          border: { display: false },
          ticks: { callback: formatTick },
        },
        y: {
          grid: { display: false },
          border: { color: colors.grid },
          ticks: { color: colors.text },
        },
      },
    };
    if (reduceMotion) {
      options.animation = false;
    }

    return new Chart(canvas, {
      type: "bar",
      data: {
        labels: categories.labels,
        datasets: [
          {
            data: categories.cents.map(dollars),
            backgroundColor: colors.accent,
            maxBarThickness: 24,
            // Rounded at the data end, square where the bars meet the baseline.
            borderRadius: { topRight: 4, bottomRight: 4 },
          },
        ],
      },
      options: options,
    });
  }

  function trendChart(colors) {
    var canvas = document.getElementById("trend-chart");
    var months = data.months;
    if (!canvas || !months) {
      return null;
    }
    reveal(canvas);
    var selected = months.selected;

    var options = {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", axis: "x", intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function (item) {
              return currency.format(item.parsed.y);
            },
          },
        },
      },
      scales: {
        x: {
          grid: { display: false },
          border: { color: colors.grid },
          ticks: {
            // The selected month is also bold, so it never depends on color alone.
            color: function (context) {
              return context.index === selected ? colors.text : colors.muted;
            },
            font: function (context) {
              return { weight: context.index === selected ? "700" : "400" };
            },
          },
        },
        y: {
          beginAtZero: true,
          grid: { color: colors.grid },
          border: { display: false },
          ticks: { callback: formatTick },
        },
      },
    };
    if (reduceMotion) {
      options.animation = false;
    }

    return new Chart(canvas, {
      type: "bar",
      data: {
        labels: months.labels,
        datasets: [
          {
            data: months.cents.map(dollars),
            backgroundColor: months.cents.map(function (_, index) {
              return index === selected ? colors.accent : colors.context;
            }),
            maxBarThickness: 24,
            borderRadius: { topLeft: 4, topRight: 4 },
          },
        ],
      },
      options: options,
    });
  }

  function render() {
    charts.forEach(function (chart) {
      chart.destroy();
    });
    var colors = readTheme();
    Chart.defaults.color = colors.muted;
    Chart.defaults.borderColor = colors.grid;
    Chart.defaults.font.family = colors.font;
    charts = [categoryChart(colors), trendChart(colors)].filter(Boolean);
  }

  render();

  // Redraw with the other palette when the system switches between light and dark.
  if (colorScheme.addEventListener) {
    colorScheme.addEventListener("change", render);
  } else if (colorScheme.addListener) {
    colorScheme.addListener(render);
  }
})();
