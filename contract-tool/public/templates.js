// Samma platshallarmonster som backend (src/types/contractTemplate.ts) -
// anvands har bara for att rita faltraderna live medan man skriver i texten.
const PLACEHOLDER_PATTERN = /\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}/g;

function extractPlaceholderKeys(bodyText) {
  const seen = new Set();
  const keys = [];
  for (const match of bodyText.matchAll(PLACEHOLDER_PATTERN)) {
    if (!seen.has(match[1])) {
      seen.add(match[1]);
      keys.push(match[1]);
    }
  }
  return keys;
}

// key -> {label, type}, bevaras aven om en platshallare tillfalligt forsvinner
// ur texten (sa man inte tappar sin etikett/typ om man rattar en stavfel).
let fieldConfigState = {};
let editingId = null;

const form = document.getElementById("template-form");
const bodyTextEl = document.getElementById("body-text");
const fieldRowsEl = document.getElementById("field-rows");
const resultEl = document.getElementById("result");
const formLegend = document.getElementById("form-legend");
const submitButton = document.getElementById("submit-button");
const cancelButton = document.getElementById("cancel-edit");

function renderFieldRows() {
  const keys = extractPlaceholderKeys(bodyTextEl.value);
  fieldRowsEl.innerHTML = "";

  if (keys.length === 0) {
    const hint = document.createElement("p");
    hint.id = "no-fields-hint";
    hint.textContent = "Inga {{...}}-platshållare hittades ännu.";
    fieldRowsEl.appendChild(hint);
    return;
  }

  for (const key of keys) {
    const config = fieldConfigState[key] ?? { label: key, type: "text" };
    fieldConfigState[key] = config;

    const row = document.createElement("div");
    row.className = "field-row";
    row.innerHTML = `
      <span><code>{{${key}}}</code></span>
      <input placeholder="Etikett" data-key="${key}" data-prop="label" value="${config.label}" />
      <select data-key="${key}" data-prop="type">
        <option value="text" ${config.type === "text" ? "selected" : ""}>Text</option>
        <option value="number" ${config.type === "number" ? "selected" : ""}>Tal</option>
        <option value="date" ${config.type === "date" ? "selected" : ""}>Datum</option>
      </select>
    `;
    fieldRowsEl.appendChild(row);
  }

  fieldRowsEl.querySelectorAll("[data-key]").forEach((el) => {
    el.addEventListener("input", () => {
      fieldConfigState[el.dataset.key][el.dataset.prop] = el.value;
    });
  });
}

bodyTextEl.addEventListener("input", renderFieldRows);

function resetForm() {
  form.reset();
  fieldConfigState = {};
  editingId = null;
  formLegend.textContent = "Ny mall";
  submitButton.textContent = "Spara mall";
  cancelButton.hidden = true;
  renderFieldRows();
}

function startEdit(template) {
  editingId = template.id;
  form.elements.name.value = template.name;
  bodyTextEl.value = template.bodyText;
  fieldConfigState = {};
  for (const field of template.fields) {
    fieldConfigState[field.key] = { label: field.label, type: field.type };
  }
  formLegend.textContent = `Redigerar: ${template.name}`;
  submitButton.textContent = "Spara ändringar";
  cancelButton.hidden = false;
  renderFieldRows();
  window.scrollTo({ top: form.offsetTop, behavior: "smooth" });
}

cancelButton.addEventListener("click", resetForm);

async function loadTemplates() {
  const listEl = document.getElementById("template-list");
  const res = await fetch("/api/templates");
  const templates = await res.json();

  if (templates.length === 0) {
    listEl.textContent = "Inga mallar ännu.";
    return;
  }

  listEl.innerHTML = "";
  for (const template of templates) {
    const row = document.createElement("div");
    row.className = "template-row";
    row.innerHTML = `
      <strong>${template.name}</strong>
      <span>${template.fields.length} fält</span>
      <button type="button" data-action="edit">Redigera</button>
      <button type="button" data-action="duplicate">Duplicera</button>
      <button type="button" data-action="delete">Ta bort</button>
    `;
    row.querySelector('[data-action="edit"]').addEventListener("click", () => startEdit(template));
    row.querySelector('[data-action="duplicate"]').addEventListener("click", async () => {
      await fetch(`/api/templates/${template.id}/duplicate`, { method: "POST" });
      loadTemplates();
    });
    row.querySelector('[data-action="delete"]').addEventListener("click", async () => {
      if (!confirm(`Ta bort mallen "${template.name}"?`)) return;
      await fetch(`/api/templates/${template.id}`, { method: "DELETE" });
      if (editingId === template.id) resetForm();
      loadTemplates();
    });
    listEl.appendChild(row);
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    name: form.elements.name.value,
    bodyText: bodyTextEl.value,
    fieldConfig: fieldConfigState,
  };

  const url = editingId ? `/api/templates/${editingId}` : "/api/templates";
  const method = editingId ? "PUT" : "POST";
  const res = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.json();
    resultEl.textContent = `Fel: ${JSON.stringify(err)}`;
    return;
  }

  resultEl.textContent = editingId ? "Mall uppdaterad." : "Mall skapad.";
  resetForm();
  loadTemplates();
});

renderFieldRows();
loadTemplates();
