window.AziroConfig = window.AziroConfig || {};

window.AziroConfig.getApiBaseUrl = function() {
  return window.location.origin.replace(/\/$/, "");
};

window.AziroConfig.getApiBaseUrlCandidates = function() {
  return [window.AziroConfig.getApiBaseUrl()];
};

window.AziroConfig.resolveApiBaseUrl = async function() {
  const baseUrl = window.AziroConfig.getApiBaseUrl();

  if (window.AziroConfig._resolvedApiBaseUrl === baseUrl) {
    return baseUrl;
  }

  try {
    const response = await fetch(`${baseUrl}/api/health`, { method: "GET" });
    if (response.ok) {
      const payload = await response.json();
      if (payload && payload.service === "Aziro L&D Assessment API") {
        window.AziroConfig._resolvedApiBaseUrl = baseUrl;
        window.localStorage.setItem("aziroApiBaseUrl", baseUrl);
        return baseUrl;
      }
    }
  } catch (error) {
  }

  window.AziroConfig._resolvedApiBaseUrl = baseUrl;
  window.localStorage.setItem("aziroApiBaseUrl", baseUrl);
  return baseUrl;
};
