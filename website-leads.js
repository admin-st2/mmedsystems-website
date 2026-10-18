/* MMeD public lead form. Never put API secrets or private demo links here.
   Inactive until website-leads-config.js is explicitly enabled after backend checks. */
(() => {
  "use strict";
  const config = window.MMED_LEAD_CONFIG;
  if (!config || config.enabled !== true ||
      !/^https:\/\/[a-z0-9-]+\.supabase\.co\/functions\/v1\/website-lead$/i.test(config.endpoint || "") ||
      typeof config.turnstileSiteKey !== "string" || config.turnstileSiteKey.length < 10) {
    return; // Safe email-only fallback remains visible.
  }
  const section = document.getElementById("lead-capture");
  const form = document.getElementById("lead-intake-form");
  const status = document.getElementById("lead-intake-status");
  const button = document.getElementById("lead-intake-submit");
  const mount = document.getElementById("lead-turnstile");
  if (!section || !form || !status || !button || !mount) return;
  function message(text, isError) {
    status.textContent = text;
    status.classList.toggle("lead-status-error", Boolean(isError));
  }
  function requireChallenge() {
    return new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
      script.async = true;
      script.onload = resolve;
      script.onerror = () => reject(new Error("turnstile_loading"));
      document.head.appendChild(script);
    });
  }
  let widgetId = null;
  requireChallenge().then(() => {
    if (!window.turnstile) throw new Error("turnstile_unavailable");
    widgetId = window.turnstile.render(mount, {
      sitekey: config.turnstileSiteKey,
      action: "website_lead",
      theme: "light",
    });
    section.hidden = false;
  }).catch(() => {
    // Never show a form that cannot validate its required anti-bot challenge.
    section.hidden = true;
  });
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    if (widgetId === null || !window.turnstile) return;
    const token = window.turnstile.getResponse(widgetId);
    if (!token) {
      message("Complete the security check before submitting.", true);
      return;
    }
    const fd = new FormData(form);
    const payload = {
      full_name: fd.get("full_name"),
      work_email: fd.get("work_email"),
      organization: fd.get("organization"),
      job_title: fd.get("job_title"),
      country: fd.get("country"),
      time_zone: fd.get("time_zone"),
      facility_type: fd.get("facility_type"),
      locations: fd.get("locations"),
      timeline: fd.get("timeline"),
      message: fd.get("message") || "",
      website: fd.get("website") || "",
      interests: fd.getAll("interests"),
      privacy_notice_accepted: fd.get("privacy_notice_accepted") === "on",
      no_phi_confirmed: fd.get("no_phi_confirmed") === "on",
      turnstile_token: token,
    };
    if (!payload.privacy_notice_accepted || !payload.no_phi_confirmed) {
      message("Please confirm the privacy notice and that no patient information is included.", true);
      return;
    }
    button.disabled = true;
    message("Submitting your inquiry securely…", false);
    const abort = new AbortController();
    const timeout = setTimeout(() => abort.abort(), 15000);
    try {
      const result = await fetch(config.endpoint, {
        method: "POST",
        mode: "cors",
        credentials: "omit",
        cache: "no-store",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: abort.signal,
      });
      let body = {};
      try { body = await result.json(); } catch {}
      if (!result.ok || body.ok !== true) throw new Error("submission_failed");
      form.reset();
      message("Your business inquiry was received. Our partnerships team will review it and contact you about next steps.", false);
    } catch {
      message("The secure form could not confirm receipt. Please email partnerships@mmedsystems.com using the option below.", true);
    } finally {
      clearTimeout(timeout);
      button.disabled = false;
      window.turnstile.reset(widgetId);
    }
  });
})();
