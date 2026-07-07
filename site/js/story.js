/* fair play, over fair pay? — scroll story (riso-collage edition)
   All charts read the JSON exported by the analysis pipeline (site/data/),
   so the page can never drift from the paper.
   The two reader polls store nothing and send nothing — in-browser only. */

(function () {
  "use strict";

  const C = {
    ink: "#2E2839", ink70: "rgba(46,40,57,0.72)", paper: "#F6F0E4",
    orange: "#E25A2C", purple: "#7A5BC0", grey: "#9A93A8",
  };
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const DUR = reduceMotion ? 0 : 600;

  const tooltip = document.getElementById("tooltip");
  function showTip(html, ev) {
    tooltip.innerHTML = html;
    tooltip.classList.add("show");
    const pad = 14;
    let x = ev.clientX + pad, y = ev.clientY + pad;
    const r = tooltip.getBoundingClientRect();
    if (x + r.width > window.innerWidth - 8) x = ev.clientX - r.width - pad;
    if (y + r.height > window.innerHeight - 8) y = ev.clientY - r.height - pad;
    tooltip.style.left = x + "px";
    tooltip.style.top = y + "px";
  }
  function hideTip() { tooltip.classList.remove("show"); }

  const fmt2 = d3.format(".2f");

  // ----------------------------------------------------------------
  // Load everything, then build.
  // ----------------------------------------------------------------
  Promise.all([
    d3.json("data/births.json"),
    d3.json("data/cohort_dist.json"),
    d3.json("data/coefficients.json"),
    d3.json("data/extras.json"),
  ]).then(([births, cohorts, coefs, extras]) => {
    birthsChart(births);
    const cohortApi = cohortChart(cohorts, extras);
    zeroChart(extras);
    const coefApi = coefChart(coefs.main);
    const strataApi = strataChart(coefs.strata);
    const gradientApi = gradientChart(extras.gradient);
    wireScrolly("#scrolly-cohort", cohortApi);
    wireScrolly("#scrolly-coef", coefApi);
    wireScrolly("#scrolly-strata", strataApi);
    pollIdeal(cohorts, extras);
    pollFair(extras);
    closingQuestions();

    function pollFair(extras) {
      const resp = document.getElementById("poll-fair-resp");
      const overall = 1.59;
      document.querySelectorAll("#poll-fair .poll-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
          document.querySelectorAll("#poll-fair .poll-btn").forEach((b) => b.classList.remove("sel"));
          btn.classList.add("sel");
          const lvl = +btn.dataset.val;
          const row = extras.gradient.find((d) => d.level === lvl);
          const dir = row.mean > overall ? "above" : "below";
          resp.innerHTML = `In this survey, the <strong>${row.n.toLocaleString()}</strong> people who answered
            like you wanted <strong>${fmt2(row.mean)}</strong> children on average —
            ${dir} the overall 1.59. That’s you on the chart below ↓`;
          gradientApi.highlight(lvl);
        });
      });
    }
  });

  // ----------------------------------------------------------------
  // Poll A — reader's ideal number, compared against both cohorts
  // ----------------------------------------------------------------
  function pollIdeal(cohorts, extras) {
    const resp = document.getElementById("poll-ideal-resp");
    const zeroYou = document.getElementById("zero-you");
    const share = (dist, k) => {
      let s = 0;
      for (const [key, v] of Object.entries(dist)) {
        const n = +key;
        if (k === 3 ? n >= 3 : n === k) s += v;
      }
      return (s * 100).toFixed(1);
    };
    document.querySelectorAll("#poll-ideal .poll-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll("#poll-ideal .poll-btn").forEach((b) => b.classList.remove("sel"));
        btn.classList.add("sel");
        const k = +btn.dataset.val;
        const gz = share(cohorts["Gen Z"].dist, k);
        const ml = share(cohorts["Millennials"].dist, k);
        const tail = k === 0
          ? "The fastest-growing answer in China."
          : k === 2
          ? "Still the most common answer — but shrinking."
          : k === 3
          ? "A rare answer among both generations."
          : "An increasingly common middle ground.";
        resp.innerHTML = `You answered like <strong>${gz}% of Gen Z</strong> and
          <strong>${ml}% of Millennials</strong> — ${tail} Keep your answer in mind as you scroll.`;
        zeroYou.textContent = k === 0 ? " — including you" : "";
      });
    });
  }

  // ----------------------------------------------------------------
  // Closing — pick the question that stays with you
  // ----------------------------------------------------------------
  function closingQuestions() {
    const responses = [
      "So are we — the same survey infrastructure exists in Korea and Japan. Same questions, waiting to be asked.",
      "Harder than any subsidy: exam integrity, transparent hiring, visible consequences when connections beat merit.",
      "Childcare that exists, paternity leave that men actually take, hiring that doesn’t quietly punish mothers.",
      "The data hints no — beliefs track lived experience, not slogans. But it stays an open question.",
    ];
    const resp = document.getElementById("q-resp");
    document.querySelectorAll(".q-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".q-btn").forEach((b) => b.classList.remove("sel"));
        btn.classList.add("sel");
        resp.textContent = "↳ " + responses[+btn.dataset.q];
      });
    });
  }

  function wireScrolly(sel, api) {
    const scroller = scrollama();
    scroller
      .setup({ step: `${sel} .step`, offset: 0.55 })
      .onStepEnter((r) => {
        d3.selectAll(`${sel} .step`).classed("is-active", (d, i, n) => n[i] === r.element);
        api.setStep(r.element.dataset.step);
      });
    window.addEventListener("resize", scroller.resize);
  }

  // ----------------------------------------------------------------
  // 1 · Births line, 2015–2023, policy annotations
  // ----------------------------------------------------------------
  function birthsChart(data) {
    const W = 800, H = 420, m = { t: 28, r: 24, b: 40, l: 48 };
    const svg = d3.select("#births-chart").append("svg").attr("viewBox", `0 0 ${W} ${H}`);
    const x = d3.scaleLinear().domain([2015, 2023]).range([m.l, W - m.r]);
    const y = d3.scaleLinear().domain([0, 19]).range([H - m.b, m.t]);

    svg.append("g").attr("class", "axis")
      .attr("transform", `translate(0,${H - m.b})`)
      .call(d3.axisBottom(x).ticks(9).tickFormat(d3.format("d")).tickSize(0).tickPadding(10))
      .call((g) => g.select(".domain").remove());
    svg.append("g").attr("class", "axis")
      .attr("transform", `translate(${m.l},0)`)
      .call(d3.axisLeft(y).ticks(5).tickSize(-(W - m.l - m.r)).tickPadding(8))
      .call((g) => g.select(".domain").remove())
      .call((g) => g.selectAll("line").attr("class", "gridline"));

    // policy annotation lines (2021 label anchored left so it fits the frame)
    for (const d of data.filter((d) => d.note)) {
      const late = d.year > 2019;
      svg.append("line").attr("x1", x(d.year)).attr("x2", x(d.year))
        .attr("y1", y(0)).attr("y2", y(18)).attr("stroke", C.ink)
        .attr("stroke-dasharray", "4 4").attr("stroke-width", 1.1).attr("opacity", 0.55);
      svg.append("text").attr("class", "anno")
        .attr("x", x(d.year) + (late ? -6 : 6)).attr("y", m.t + 4)
        .attr("text-anchor", late ? "end" : "start")
        .text(d.note);
    }

    const line = d3.line().x((d) => x(d.year)).y((d) => y(d.births_m)).curve(d3.curveMonotoneX);
    const path = svg.append("path").datum(data)
      .attr("fill", "none").attr("stroke", C.orange).attr("stroke-width", 3).attr("d", line);

    if (!reduceMotion) {
      const len = path.node().getTotalLength();
      path.attr("stroke-dasharray", `${len} ${len}`).attr("stroke-dashoffset", len);
      const io = new IntersectionObserver((es) => {
        if (es[0].isIntersecting) {
          path.transition().duration(1800).ease(d3.easeCubicOut).attr("stroke-dashoffset", 0);
          io.disconnect();
        }
      }, { threshold: 0.4 });
      io.observe(document.getElementById("births-chart"));
    }

    svg.selectAll("circle.pt").data(data).join("circle")
      .attr("class", "pt")
      .attr("cx", (d) => x(d.year)).attr("cy", (d) => y(d.births_m))
      .attr("r", 4.5).attr("fill", C.orange).attr("stroke", C.paper).attr("stroke-width", 2)
      .on("mousemove", (ev, d) => showTip(`<b>${d.year}</b><br>${d.births_m.toFixed(2)} million births`, ev))
      .on("mouseleave", hideTip);

    const first = data[1], last = data[data.length - 1];
    svg.append("text").attr("class", "direct-label").attr("fill", C.orange)
      .attr("x", x(first.year) - 10).attr("y", y(first.births_m) - 10).attr("text-anchor", "end")
      .text("17.9M");
    svg.append("text").attr("class", "direct-label").attr("fill", C.orange)
      .attr("x", x(last.year) - 2).attr("y", y(last.births_m) - 14).attr("text-anchor", "end")
      .text("9.0M — nearly half");
  }

  // ----------------------------------------------------------------
  // 2 · Cohort distribution (scrolly): grouped bars, % by ideal number
  // ----------------------------------------------------------------
  function cohortChart(cohorts, extras) {
    const W = 800, H = 460, m = { t: 20, r: 24, b: 44, l: 48 };
    const svg = d3.select("#cohort-chart").append("svg").attr("viewBox", `0 0 ${W} ${H}`);
    const cats = [0, 1, 2, 3, 4, 5];
    const val = (dist, k) => (dist[String(k)] || 0) * 100;

    const x = d3.scaleBand().domain(cats).range([m.l, W - m.r]).paddingInner(0.32).paddingOuter(0.12);
    const xi = d3.scaleBand().domain(["mill", "genz"]).range([0, x.bandwidth()]).paddingInner(0.14);
    const y = d3.scaleLinear().domain([0, 65]).range([H - m.b, m.t]);

    svg.append("g").attr("class", "axis")
      .attr("transform", `translate(0,${H - m.b})`)
      .call(d3.axisBottom(x).tickSize(0).tickPadding(10).tickFormat((d) => (d === 5 ? "5+" : d)))
      .call((g) => g.select(".domain").remove());
    svg.append("text").attr("class", "anno")
      .attr("x", (m.l + W - m.r) / 2).attr("y", H - 6).attr("text-anchor", "middle")
      .text("Ideal number of children");
    svg.append("g").attr("class", "axis")
      .attr("transform", `translate(${m.l},0)`)
      .call(d3.axisLeft(y).ticks(5).tickFormat((d) => d + "%").tickSize(-(W - m.l - m.r)).tickPadding(8))
      .call((g) => g.select(".domain").remove())
      .call((g) => g.selectAll("line").attr("class", "gridline"));

    const series = [
      { key: "mill", label: "Millennials (born 1980–94)", color: C.grey, dist: cohorts["Millennials"].dist },
      { key: "genz", label: "Gen Z (born 1995+)", color: C.orange, dist: cohorts["Gen Z"].dist },
    ];

    const bars = {};
    for (const s of series) {
      bars[s.key] = svg.selectAll(`rect.${s.key}`).data(cats).join("rect")
        .attr("class", s.key)
        .attr("x", (d) => x(d) + xi(s.key)).attr("width", xi.bandwidth())
        .attr("y", y(0)).attr("height", 0)
        .attr("fill", s.color)
        .on("mousemove", (ev, d) => showTip(
          `<b>${s.label}</b><br>${d === 5 ? "5+" : d} children: ${val(s.dist, d).toFixed(1)}%`, ev))
        .on("mouseleave", hideTip);
    }

    const legend = svg.append("g").attr("transform", `translate(${W - m.r - 260}, ${m.t + 2})`);
    series.forEach((s, i) => {
      const g = legend.append("g").attr("transform", `translate(0, ${i * 20})`)
        .attr("opacity", s.key === "genz" ? 0 : 1).attr("class", `leg-${s.key}`);
      g.append("rect").attr("x", -6).attr("y", -10).attr("width", 12).attr("height", 12).attr("fill", s.color);
      g.append("text").attr("class", "anno").attr("x", 11).text(s.label);
    });

    const zeroRing = svg.append("rect")
      .attr("x", x(0) - 5).attr("width", x.bandwidth() + 10)
      .attr("y", y(0)).attr("height", 0)
      .attr("fill", "none").attr("stroke", C.ink).attr("stroke-width", 1.8)
      .attr("stroke-dasharray", "5 4").attr("opacity", 0);
    const zeroLabel = svg.append("text").attr("class", "anno-strong")
      .attr("x", x(0) + x.bandwidth() / 2 + 4).attr("y", 0).attr("text-anchor", "start").attr("opacity", 0);

    function grow(key, on) {
      const s = series.find((d) => d.key === key);
      bars[key].transition().duration(DUR)
        .attr("y", (d) => (on ? y(val(s.dist, d)) : y(0)))
        .attr("height", (d) => (on ? y(0) - y(val(s.dist, d)) : 0));
      svg.select(`.leg-${key}`).transition().duration(DUR).attr("opacity", on ? 1 : 0);
    }

    function setStep(step) {
      if (step === "mill") {
        grow("mill", true); grow("genz", false);
        zeroRing.attr("opacity", 0); zeroLabel.attr("opacity", 0);
        bars.mill.attr("opacity", 1);
      } else if (step === "genz") {
        grow("mill", true); grow("genz", true);
        zeroRing.attr("opacity", 0); zeroLabel.attr("opacity", 0);
        bars.mill.attr("opacity", 1); bars.genz.attr("opacity", 1);
      } else if (step === "zero") {
        grow("mill", true); grow("genz", true);
        bars.mill.attr("opacity", (d) => (d === 0 ? 1 : 0.3));
        bars.genz.attr("opacity", (d) => (d === 0 ? 1 : 0.3));
        const top = y(Math.max(val(series[0].dist, 0), val(series[1].dist, 0)));
        zeroRing.attr("y", top - 8).attr("height", y(0) - top + 8).transition().duration(DUR).attr("opacity", 1);
        zeroLabel.attr("y", top - 16)
          .text(`${extras.zero_pref.genz.pct}% of Gen Z say zero`)
          .transition().duration(DUR).attr("opacity", 1);
      }
    }
    setStep("mill");
    return { setStep };
  }

  // ----------------------------------------------------------------
  // 3 · Who says zero — horizontal bars (highlight = orange, context = grey)
  // ----------------------------------------------------------------
  function zeroChart(extras) {
    const rows = [
      { l: "Gen Z", v: extras.zero_pref.genz, c: C.orange },
      { l: "Millennials", v: extras.zero_pref.millennial, c: C.grey },
      { l: "Women", v: extras.zero_pref.female, c: C.orange },
      { l: "Men", v: extras.zero_pref.male, c: C.grey },
      { l: "Urban", v: extras.zero_pref.urban, c: C.orange },
      { l: "Rural", v: extras.zero_pref.rural, c: C.grey },
    ];
    const W = 800, rowH = 44, m = { t: 8, r: 92, b: 8, l: 118 };
    const H = m.t + rows.length * rowH + m.b;
    const svg = d3.select("#zero-chart").append("svg").attr("viewBox", `0 0 ${W} ${H}`);
    const x = d3.scaleLinear().domain([0, 30]).range([m.l, W - m.r]);

    const g = svg.selectAll("g.row").data(rows).join("g")
      .attr("transform", (d, i) => `translate(0, ${m.t + i * rowH})`);
    g.append("text").attr("class", "anno-strong")
      .attr("x", m.l - 12).attr("y", rowH / 2 + 5).attr("text-anchor", "end")
      .text((d) => d.l);
    g.append("rect")
      .attr("x", x(0)).attr("y", rowH / 2 - 10).attr("height", 20)
      .attr("width", (d) => x(d.v.pct) - x(0)).attr("fill", (d) => d.c)
      .on("mousemove", (ev, d) => showTip(`<b>${d.l}</b><br>${d.v.pct}% want zero children<br>of ${d.v.n.toLocaleString()} valid answers`, ev))
      .on("mouseleave", hideTip);
    g.append("text").attr("class", "direct-label")
      .attr("x", (d) => x(d.v.pct) + 8).attr("y", rowH / 2 + 5)
      .attr("fill", (d) => (d.c === C.grey ? C.ink70 : d.c))
      .text((d) => d.v.pct + "%");
  }

  // ----------------------------------------------------------------
  // 4 · Hero coefficient chart (scrolly)
  // ----------------------------------------------------------------
  function coefChart(main) {
    const W = 800, H = 420, m = { t: 30, r: 40, b: 46, l: 190 };
    const svg = d3.select("#coef-chart").append("svg").attr("viewBox", `0 0 ${W} ${H}`);
    const vars = ["general_fairness", "meritocracy_index", "income_fairness"];
    const rows = vars.map((v) => main.find((d) => d.variable === v));
    const nice = {
      general_fairness: "“Society is fair”",
      meritocracy_index: "“Effort decides success”",
      income_fairness: "“The income gap is fair”",
    };

    const x = d3.scaleLinear().domain([-0.16, 0.26]).range([m.l, W - m.r]);
    const y = d3.scalePoint().domain(vars).range([m.t + 40, H - m.b - 30]).padding(0.4);

    svg.append("g").attr("class", "axis")
      .attr("transform", `translate(0,${H - m.b})`)
      .call(d3.axisBottom(x).tickValues([-0.1, 0, 0.1, 0.2]).tickSize(0).tickPadding(10).tickFormat(d3.format("+.1f")))
      .call((g) => g.select(".domain").remove());
    svg.append("text").attr("class", "anno")
      .attr("x", (m.l + W - m.r) / 2).attr("y", H - 8).attr("text-anchor", "middle")
      .text("Change in ideal number of children per one-point increase in belief");

    svg.append("line").attr("class", "zeroline")
      .attr("x1", x(0)).attr("x2", x(0)).attr("y1", m.t).attr("y2", H - m.b);
    svg.append("text").attr("class", "anno")
      .attr("x", x(0)).attr("y", m.t - 8).attr("text-anchor", "middle")
      .text("No relationship");

    const groups = {};
    for (const d of rows) {
      const g = svg.append("g").attr("opacity", 0);
      const col = d.significant ? C.orange : C.grey;
      g.append("text").attr("class", "anno-strong")
        .attr("x", m.l - 14).attr("y", y(d.variable) + 5).attr("text-anchor", "end")
        .text(nice[d.variable]);
      g.append("line")
        .attr("x1", x(d.ci_lower)).attr("x2", x(d.ci_upper))
        .attr("y1", y(d.variable)).attr("y2", y(d.variable))
        .attr("stroke", col).attr("stroke-width", d.significant ? 5 : 3)
        .attr("stroke-linecap", "round").attr("opacity", d.significant ? 0.85 : 0.55);
      g.append("circle")
        .attr("cx", x(d.coef)).attr("cy", y(d.variable))
        .attr("r", d.significant ? 11 : 8.5)
        .attr("fill", d.significant ? col : C.paper)
        .attr("stroke", d.significant ? C.paper : col).attr("stroke-width", 2.5)
        .on("mousemove", (ev) => showTip(
          `<b>${d.label}</b><br>β = ${d.coef >= 0 ? "+" : ""}${fmt2(d.coef)} · 95% CI [${fmt2(d.ci_lower)}, ${fmt2(d.ci_upper)}]<br>${d.significant ? "p < 0.05" : "not significant"}`, ev))
        .on("mouseleave", hideTip);
      g.append("text").attr("class", "direct-label")
        .attr("x", x(Math.max(d.ci_upper, d.coef)) + 10).attr("y", y(d.variable) + 5)
        .attr("fill", d.significant ? col : C.ink70)
        .text(`${d.coef >= 0 ? "+" : ""}${fmt2(d.coef)}${d.significant ? "" : " (ns)"}`);
      groups[d.variable] = g;
    }

    const order = { intro: [], gf: ["general_fairness"], merit: ["general_fairness", "meritocracy_index"],
      income: ["general_fairness", "meritocracy_index", "income_fairness"], all: vars };
    function setStep(step) {
      const on = new Set(order[step] || vars);
      for (const v of vars) {
        groups[v].transition().duration(DUR)
          .attr("opacity", on.has(v) ? (step === "income" && v !== "income_fairness" ? 0.35 : 1) : 0);
      }
    }
    setStep("intro");
    return { setStep };
  }

  // ----------------------------------------------------------------
  // 5 · Two Chinas + gender (scrolly, paired panels)
  // ----------------------------------------------------------------
  function strataChart(strata) {
    const W = 800, H = 430;
    const svg = d3.select("#strata-chart").append("svg").attr("viewBox", `0 0 ${W} ${H}`);
    const vars = ["general_fairness", "meritocracy_index", "income_fairness"];
    const nice = { general_fairness: "Society fair", meritocracy_index: "Effort decides", income_fairness: "Income gap fair" };
    const panelW = W / 2;
    const m = { t: 58, r: 42, b: 46, l: 118 };
    const x = d3.scaleLinear().domain([-0.25, 0.42]);
    const y = d3.scalePoint().domain(vars).range([m.t + 24, H - m.b - 16]).padding(0.35);

    const panels = [
      svg.append("g").attr("class", "panel0"),
      svg.append("g").attr("class", "panel1").attr("transform", `translate(${panelW},0)`),
    ];
    const titleEl = document.getElementById("strata-title");

    function drawPanel(g, data, color, title, n, dim) {
      g.selectAll("*").remove();
      const xr = x.copy().range([m.l, panelW - m.r]);
      g.attr("opacity", dim ? 0.32 : 1);
      g.append("text").attr("class", "anno-strong").attr("fill", color)
        .attr("x", (m.l + panelW - m.r) / 2).attr("y", 24).attr("text-anchor", "middle")
        .style("font-size", "15px")
        .text(title);
      g.append("text").attr("class", "anno")
        .attr("x", (m.l + panelW - m.r) / 2).attr("y", 40).attr("text-anchor", "middle")
        .text(`N = ${n.toLocaleString()}`);
      g.append("g").attr("class", "axis")
        .attr("transform", `translate(0,${H - m.b})`)
        .call(d3.axisBottom(xr).ticks(4).tickSize(0).tickPadding(9).tickFormat(d3.format("+.1f")))
        .call((s) => s.select(".domain").remove());
      g.append("line").attr("class", "zeroline")
        .attr("x1", xr(0)).attr("x2", xr(0)).attr("y1", m.t).attr("y2", H - m.b);
      for (const v of vars) {
        const d = data.coefficients.find((c) => c.variable === v);
        const col = d.significant ? color : C.grey;
        g.append("text").attr("class", "anno")
          .attr("x", m.l - 10).attr("y", y(v) + 4).attr("text-anchor", "end")
          .text(nice[v]);
        g.append("line")
          .attr("x1", xr(d.ci_lower)).attr("x2", xr(d.ci_upper))
          .attr("y1", y(v)).attr("y2", y(v))
          .attr("stroke", col).attr("stroke-width", d.significant ? 5 : 2.5)
          .attr("stroke-linecap", "round").attr("opacity", d.significant ? 0.85 : 0.5);
        g.append("circle")
          .attr("cx", xr(d.coef)).attr("cy", y(v))
          .attr("r", d.significant ? 10 : 7)
          .attr("fill", d.significant ? col : C.paper)
          .attr("stroke", d.significant ? C.paper : col).attr("stroke-width", 2.5)
          .on("mousemove", (ev) => showTip(
            `<b>${title} · ${d.label}</b><br>β = ${d.coef >= 0 ? "+" : ""}${fmt2(d.coef)} [${fmt2(d.ci_lower)}, ${fmt2(d.ci_upper)}]<br>${d.significant ? "p < 0.05" : "not significant"}`, ev))
          .on("mouseleave", hideTip);
        if (d.significant) {
          g.append("text").attr("class", "direct-label")
            .attr("x", xr(Math.max(d.ci_upper, d.coef)) + 8).attr("y", y(v) + 4)
            .attr("fill", col)
            .text(`+${fmt2(d.coef)}`);
        }
      }
    }

    function render(mode, focus) {
      if (mode === "residence") {
        titleEl.textContent = "Urban and rural China read fairness differently";
        drawPanel(panels[0], strata.urban, C.purple, "Urban", strata.urban.n, focus === "rural");
        drawPanel(panels[1], strata.rural, C.orange, "Rural", strata.rural.n, focus === "urban");
      } else {
        titleEl.textContent = "The same beliefs move men more than women";
        drawPanel(panels[0], strata.male, C.purple, "Men", strata.male.n, focus === "female");
        drawPanel(panels[1], strata.female, C.orange, "Women", strata.female.n, focus === "male");
      }
    }

    function setStep(step) {
      if (step === "urban") render("residence", "urban");
      else if (step === "rural") render("residence", "rural");
      else if (step === "paradox") render("residence", null);
      else if (step === "gender") render("gender", null);
      else if (step === "gender2") render("gender", "female");
    }
    render("residence", null);
    return { setStep };
  }

  // ----------------------------------------------------------------
  // 6 · Raw gradient mini-chart (+ "you are here" from poll B)
  // ----------------------------------------------------------------
  function gradientChart(gradient) {
    const W = 800, H = 310, m = { t: 30, r: 40, b: 52, l: 52 };
    const svg = d3.select("#gradient-chart").append("svg").attr("viewBox", `0 0 ${W} ${H}`);
    const labels = ["Very unfair", "Unfair", "In between", "Fair", "Very fair"];
    const x = d3.scalePoint().domain(gradient.map((d) => d.level)).range([m.l, W - m.r]).padding(0.4);
    const y = d3.scaleLinear().domain([1.3, 2.0]).range([H - m.b, m.t]);

    svg.append("g").attr("class", "axis")
      .attr("transform", `translate(0,${H - m.b})`)
      .call(d3.axisBottom(x).tickSize(0).tickPadding(10).tickFormat((d, i) => labels[i]))
      .call((g) => g.select(".domain").remove());
    svg.append("g").attr("class", "axis")
      .attr("transform", `translate(${m.l},0)`)
      .call(d3.axisLeft(y).ticks(4).tickFormat(d3.format(".1f")).tickSize(-(W - m.l - m.r)).tickPadding(8))
      .call((g) => g.select(".domain").remove())
      .call((g) => g.selectAll("line").attr("class", "gridline"));
    svg.append("text").attr("class", "anno")
      .attr("x", (m.l + W - m.r) / 2).attr("y", H - 10).attr("text-anchor", "middle")
      .text("“Overall, is today’s society fair?”");

    svg.append("path").datum(gradient)
      .attr("fill", "none").attr("stroke", C.orange).attr("stroke-width", 2)
      .attr("stroke-dasharray", "1 6").attr("stroke-linecap", "round")
      .attr("d", d3.line().x((d) => x(d.level)).y((d) => y(d.mean)));

    svg.selectAll("circle.g").data(gradient).join("circle").attr("class", "g")
      .attr("cx", (d) => x(d.level)).attr("cy", (d) => y(d.mean))
      .attr("r", (d) => Math.max(6, Math.sqrt(d.n) / 3.4))
      .attr("fill", C.orange).attr("fill-opacity", 0.9)
      .attr("stroke", C.paper).attr("stroke-width", 2)
      .on("mousemove", (ev, d) => showTip(`<b>“${labels[d.level - 1]}”</b><br>mean ideal children: ${d.mean}<br>n = ${d.n.toLocaleString()}`, ev))
      .on("mouseleave", hideTip);

    svg.selectAll("text.val").data(gradient).join("text")
      .attr("class", "direct-label").attr("fill", C.orange)
      .attr("x", (d) => x(d.level)).attr("y", (d) => y(d.mean) - 18).attr("text-anchor", "middle")
      .text((d) => fmt2(d.mean));

    // "you are here" marker, driven by poll B
    const youRing = svg.append("circle")
      .attr("fill", "none").attr("stroke", C.ink).attr("stroke-width", 2.2)
      .attr("stroke-dasharray", "5 4").attr("opacity", 0);
    const youLabel = svg.append("text").attr("class", "anno-strong")
      .attr("text-anchor", "middle").attr("opacity", 0).text("You ↑");

    function highlight(level) {
      const d = gradient.find((g) => g.level === level);
      const r = Math.max(6, Math.sqrt(d.n) / 3.4) + 7;
      youRing.attr("cx", x(level)).attr("cy", y(d.mean)).attr("r", r)
        .transition().duration(DUR).attr("opacity", 1);
      youLabel.attr("x", x(level)).attr("y", y(d.mean) + r + 18)
        .transition().duration(DUR).attr("opacity", 1);
    }
    return { highlight };
  }
})();
