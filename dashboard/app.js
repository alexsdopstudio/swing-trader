"use strict";

const byId = (id) => document.getElementById(id);

function humanize(value) {
  return String(value ?? "")
    .replaceAll("_", " ")
    .replaceAll("-", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(`${value}T00:00:00Z`);
  if (Number.isNaN(date.valueOf())) return value;
  return new Intl.DateTimeFormat("en", {
    year: "numeric",
    month: "short",
    day: "2-digit",
    timeZone: "UTC",
  }).format(date);
}

function repositoryUrl(repository) {
  return `https://github.com/${repository}`;
}

function renderCanonical(project) {
  const repoUrl = repositoryUrl(project.repository);
  for (const id of ["repository-link", "footer-repository-link"]) {
    const link = byId(id);
    link.href = repoUrl;
    link.rel = "noopener noreferrer";
  }

  byId("validation-label").textContent = project.strategy.validation_label;
  byId("strategy-version").textContent = project.strategy.version;
  byId("strategy-status").textContent = humanize(project.strategy.status);
  byId("deployment-status").textContent = humanize(project.strategy.deployment_status);

  const holdout = project.prospective_holdout;
  byId("holdout-status").textContent = humanize(holdout.status);
  byId("holdout-start").textContent = formatDate(holdout.evaluation_start);
  byId("holdout-end").textContent = formatDate(holdout.minimum_observation_end);
  byId("minimum-trades").textContent = String(holdout.minimum_closed_trades);

  const research = project.research;
  byId("experiment-count").textContent = String(research.historical_experiment_count);
  const experimentGrid = byId("experiment-grid");
  const experimentTemplate = byId("experiment-template");
  experimentGrid.replaceChildren();
  for (const experiment of research.historical_experiments) {
    const fragment = experimentTemplate.content.cloneNode(true);
    fragment.querySelector(".experiment-card__id").textContent = experiment.id;
    fragment.querySelector(".experiment-card__stage").textContent = humanize(
      experiment.research_stage,
    );
    fragment.querySelector(".experiment-card__name").textContent = humanize(experiment.name);
    fragment.querySelector(".experiment-card__decision").textContent =
      experiment.decision || "No machine-recorded decision; see reviewed experiment notes.";
    const link = fragment.querySelector(".experiment-card__link");
    link.href = `${repoUrl}/tree/main/${experiment.directory}`;
    link.rel = "noopener noreferrer";
    experimentGrid.append(fragment);
  }

  const knowledge = project.knowledge;
  byId("source-count").textContent = String(knowledge.source_count);
  byId("note-count").textContent = String(knowledge.note_count);
  byId("news-count").textContent = String(knowledge.news_observation_count);
  const topicCloud = byId("topic-cloud");
  topicCloud.replaceChildren();
  const topics = Object.entries(knowledge.source_topic_counts).sort(
    ([nameA, countA], [nameB, countB]) => countB - countA || nameA.localeCompare(nameB),
  );
  for (const [topic, count] of topics) {
    const chip = document.createElement("span");
    chip.className = "topic-chip";
    const label = document.createElement("span");
    label.textContent = humanize(topic);
    const number = document.createElement("b");
    number.textContent = String(count);
    chip.append(label, number);
    topicCloud.append(chip);
  }

  const universe = project.universe;
  byId("asset-count").textContent = String(universe.asset_count);
  byId("benchmark-equities").textContent = universe.benchmark_equities;
  byId("benchmark-crypto").textContent = universe.benchmark_crypto;
  const assetGrid = byId("asset-grid");
  const assetTemplate = byId("asset-template");
  assetGrid.replaceChildren();
  for (const asset of universe.assets) {
    const fragment = assetTemplate.content.cloneNode(true);
    fragment.querySelector(".asset-chip__symbol").textContent = asset.symbol;
    fragment.querySelector(".asset-chip__class").textContent = asset.asset_class;
    assetGrid.append(fragment);
  }

  const boundaryList = byId("boundary-list");
  boundaryList.replaceChildren();
  for (const boundary of project.evidence_boundaries) {
    const item = document.createElement("li");
    item.textContent = boundary;
    boundaryList.append(item);
  }
}

async function githubRequest(repository, suffix) {
  const response = await fetch(`https://api.github.com/repos/${repository}${suffix}`, {
    headers: {
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
    },
  });
  if (response.status === 404) return null;
  if (!response.ok) {
    const error = new Error(`GitHub API ${response.status}`);
    error.status = response.status;
    throw error;
  }
  return response.json();
}

async function releaseArchiveStats(repository, tag, prefix) {
  const release = await githubRequest(repository, `/releases/tags/${encodeURIComponent(tag)}`);
  if (!release) return { count: 0, latest: null };

  const dates = [];
  let page = 1;
  while (page <= 10) {
    const assets = await githubRequest(
      repository,
      `/releases/${release.id}/assets?per_page=100&page=${page}`,
    );
    if (!Array.isArray(assets)) break;
    for (const asset of assets) {
      if (typeof asset.name !== "string" || !asset.name.startsWith(prefix)) continue;
      const suffix = asset.name.slice(prefix.length);
      const match = suffix.match(/^(\d{4}-\d{2}-\d{2})-[0-9a-f]{64}\.zip$/);
      if (match) dates.push(match[1]);
    }
    if (assets.length < 100) break;
    page += 1;
  }

  dates.sort();
  return { count: dates.length, latest: dates.at(-1) ?? null };
}

function setLiveUnavailable(reason) {
  byId("live-pulse").dataset.state = "unavailable";
  byId("live-summary").textContent = "Live GitHub status unavailable";
  byId("live-detail").textContent = reason;
}

async function loadLiveStatus(project) {
  const repository = project.repository;
  const year = new Date().getUTCFullYear();
  const live = project.live_github;
  const tasks = {
    repository: githubRequest(repository, ""),
    pulls: githubRequest(repository, "/pulls?state=open&per_page=100"),
    workflows: githubRequest(repository, "/actions/runs?branch=main&per_page=20"),
    scans: releaseArchiveStats(
      repository,
      `${live.daily_scan_release_tag_prefix}${year}`,
      live.daily_scan_asset_prefix,
    ),
    holdout: releaseArchiveStats(
      repository,
      `${live.prospective_release_tag_prefix}${year}`,
      live.prospective_asset_prefix,
    ),
  };

  const entries = Object.entries(tasks);
  const settled = await Promise.allSettled(entries.map(([, promise]) => promise));
  const values = {};
  let successes = 0;
  settled.forEach((result, index) => {
    const key = entries[index][0];
    if (result.status === "fulfilled") {
      values[key] = result.value;
      successes += 1;
    } else {
      values[key] = undefined;
    }
  });

  if (Array.isArray(values.pulls)) {
    byId("open-prs").textContent = String(values.pulls.length);
  } else {
    byId("open-prs").textContent = "Unavailable";
  }

  const runs = values.workflows?.workflow_runs;
  if (Array.isArray(runs) && runs.length > 0) {
    const latest = runs[0];
    const outcome = latest.status === "completed" ? latest.conclusion : latest.status;
    byId("workflow-status").textContent = `${latest.name}: ${humanize(outcome)}`;
  } else if (Array.isArray(runs)) {
    byId("workflow-status").textContent = "No recent runs";
  } else {
    byId("workflow-status").textContent = "Unavailable";
  }

  if (values.scans) {
    byId("scan-latest").textContent = values.scans.latest
      ? formatDate(values.scans.latest)
      : "None published yet";
    byId("scan-archive-count").textContent = `${values.scans.count} canonical archive${
      values.scans.count === 1 ? "" : "s"
    } in ${year}`;
  } else {
    byId("scan-latest").textContent = "Unavailable";
    byId("scan-archive-count").textContent = "Unavailable";
  }

  if (values.holdout) {
    byId("holdout-latest").textContent = values.holdout.latest
      ? formatDate(values.holdout.latest)
      : "None published yet";
    byId("holdout-archive-count").textContent = `${values.holdout.count} canonical archive${
      values.holdout.count === 1 ? "" : "s"
    } in ${year}`;
  } else {
    byId("holdout-latest").textContent = "Unavailable";
    byId("holdout-archive-count").textContent = "Live release lookup unavailable";
  }

  if (successes === 0) {
    setLiveUnavailable("Canonical project data remains available; only live GitHub enrichment failed.");
    return;
  }

  byId("live-pulse").dataset.state = "ok";
  byId("live-summary").textContent =
    successes === entries.length ? "Live GitHub status connected" : "Live GitHub status partially available";
  const repositoryState = values.repository?.default_branch
    ? `${values.repository.default_branch} · public repository`
    : "repository metadata unavailable";
  byId("live-detail").textContent = `${repositoryState}. Live data is presentation-only.`;
}

function showCanonicalError(error) {
  const main = byId("main-content");
  const panel = document.createElement("div");
  panel.className = "error-panel";
  panel.textContent = `Dashboard snapshot could not be loaded: ${error.message}`;
  main.prepend(panel);
  setLiveUnavailable("Live enrichment was skipped because the canonical dashboard snapshot failed.");
}

async function start() {
  try {
    const response = await fetch("./project.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`project.json returned HTTP ${response.status}`);
    const project = await response.json();
    renderCanonical(project);
    await loadLiveStatus(project);
  } catch (error) {
    showCanonicalError(error instanceof Error ? error : new Error(String(error)));
  }
}

start();
