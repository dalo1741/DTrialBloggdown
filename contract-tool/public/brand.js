// Samma dotted-name-mönster som form.js: input-namn med punkter mappar
// mot nästlade fält i BrandProfileInput (se src/types/brandProfile.ts).

function setDeep(obj, path, value) {
  const keys = path.split(".");
  let node = obj;
  for (let i = 0; i < keys.length - 1; i++) {
    const key = keys[i];
    if (!(key in node)) node[key] = {};
    node = node[key];
  }
  node[keys[keys.length - 1]] = value;
}

function getDeep(obj, path) {
  return path.split(".").reduce((node, key) => (node == null ? undefined : node[key]), obj);
}

function collectFormData(form) {
  const data = {};
  for (const el of form.elements) {
    if (!el.name) continue;
    let value = el.value;
    if (el.type === "checkbox") value = el.checked;
    else if (el.type === "number") value = value === "" ? undefined : Number(value);
    if (value === undefined) continue;
    setDeep(data, el.name, value);
  }
  return data;
}

function fillForm(form, profile) {
  for (const el of form.elements) {
    if (!el.name) continue;
    const value = getDeep(profile, el.name);
    if (value === undefined) continue;
    if (el.type === "checkbox") el.checked = Boolean(value);
    else el.value = value;
  }
}

function refreshLogoPreview() {
  const img = document.getElementById("logo-preview");
  img.src = `/api/brand-profile/logo?t=${Date.now()}`;
  img.onerror = () => {
    img.removeAttribute("src");
  };
}

async function loadProfile() {
  const form = document.getElementById("brand-form");
  const res = await fetch("/api/brand-profile");
  const profile = await res.json();
  fillForm(form, profile);
  if (profile.logo) refreshLogoPreview();
}

document.getElementById("logo-file").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const statusEl = document.getElementById("logo-status");
  statusEl.textContent = "Laddar upp...";

  const body = new FormData();
  body.append("logo", file);
  const res = await fetch("/api/brand-profile/logo", { method: "POST", body });

  if (!res.ok) {
    const err = await res.json();
    statusEl.textContent = `Fel: ${err.error ?? JSON.stringify(err)}`;
    return;
  }

  statusEl.textContent = "Logga uppladdad.";
  refreshLogoPreview();
});

document.getElementById("brand-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const payload = collectFormData(form);
  const resultEl = document.getElementById("result");
  resultEl.textContent = "Sparar...";

  const res = await fetch("/api/brand-profile", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.json();
    resultEl.textContent = `Fel: ${JSON.stringify(err)}`;
    return;
  }

  resultEl.textContent = "Profil sparad.";
});

loadProfile();
