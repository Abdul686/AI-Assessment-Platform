window.AziroConfig = window.AziroConfig || {};

window.AziroConfig.getApiBaseUrl = function() {
  const override = window.localStorage.getItem("aziroApiBaseUrl");
  if (override) {
    return override.replace(/\/$/, "");
  }
  return `${window.location.protocol}//${window.location.hostname}:8011`;
};

window.AziroConfig.getApiBaseUrlCandidates = function() {
  const override = window.localStorage.getItem("aziroApiBaseUrl");
  const host = window.location.hostname;
  const protocol = window.location.protocol;
  const candidates = [];

  if (override) {
    candidates.push(override.replace(/\/$/, ""));
  }

  candidates.push(`${protocol}//${host}:8011`);
  candidates.push(`${protocol}//${host}:8001`);
  candidates.push(window.location.origin.replace(/\/$/, ""));

  return [...new Set(candidates)];
};

window.AziroConfig.resolveApiBaseUrl = async function() {
  if (window.AziroConfig._resolvedApiBaseUrl) {
    return window.AziroConfig._resolvedApiBaseUrl;
  }

  const candidates = window.AziroConfig.getApiBaseUrlCandidates();
  for (const candidate of candidates) {
    try {
      const response = await fetch(`${candidate}/api/health`, { method: "GET" });
      if (!response.ok) {
        continue;
      }
      const payload = await response.json();
      if (payload && payload.service === "Aziro L&D Assessment API") {
        window.AziroConfig._resolvedApiBaseUrl = candidate;
        window.localStorage.setItem("aziroApiBaseUrl", candidate);
        return candidate;
      }
    } catch (error) {
    }
  }

  const fallback = window.AziroConfig.getApiBaseUrl();
  window.AziroConfig._resolvedApiBaseUrl = fallback;
  return fallback;
};
