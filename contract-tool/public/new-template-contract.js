const selectEl = document.getElementById("template-select");
const fieldsForm = document.getElementById("fields-form");
const dynamicFieldsEl = document.getElementById("dynamic-fields");
const resultEl = document.getElementById("result");

const INPUT_TYPE_MAP = { text: "text", number: "number", date: "date" };

async function loadTemplateOptions() {
  const res = await fetch("/api/templates");
  const templates = await res.json();

  if (templates.length === 0) {
    selectEl.innerHTML = '<option value="">Inga mallar finns ännu - skapa en under "Kontraktsmallar"</option>';
    return;
  }

  selectEl.innerHTML = '<option value="">Välj en mall...</option>';
  for (const template of templates) {
    const option = document.createElement("option");
    option.value = template.id;
    option.textContent = template.name;
    selectEl.appendChild(option);
  }
}

function renderFields(template) {
  dynamicFieldsEl.innerHTML = "";
  for (const field of template.fields) {
    const label = document.createElement("label");
    label.innerHTML = `${field.label} <input name="${field.key}" type="${INPUT_TYPE_MAP[field.type]}" required />`;
    dynamicFieldsEl.appendChild(label);
  }
  fieldsForm.hidden = false;
  resultEl.textContent = template.fields.length === 0 ? "Mallen har inga ifyllbara fält - klicka Generera." : "";
}

selectEl.addEventListener("change", async () => {
  const id = selectEl.value;
  if (!id) {
    fieldsForm.hidden = true;
    return;
  }
  const res = await fetch(`/api/templates/${id}`);
  const template = await res.json();
  renderFields(template);
});

fieldsForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = selectEl.value;
  const fieldValues = {};
  for (const el of fieldsForm.elements) {
    if (el.name) fieldValues[el.name] = el.value;
  }

  resultEl.textContent = "Genererar PDF...";
  const res = await fetch(`/api/templates/${id}/render`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ fieldValues }),
  });

  if (!res.ok) {
    const err = await res.json();
    resultEl.textContent = `Fel: ${JSON.stringify(err)}`;
    return;
  }

  const blob = await res.blob();
  const disposition = res.headers.get("Content-Disposition") ?? "";
  const match = disposition.match(/filename="?([^"]+)"?/);
  const fileName = match ? match[1] : "avtal.pdf";

  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = fileName;
  a.click();
  URL.revokeObjectURL(url);

  resultEl.textContent = `Klart: ${fileName}`;
});

loadTemplateOptions();
