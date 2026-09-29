// Bygger nastlad JSON fran inputs med dotted names ("provider.name" -> {provider:{name}})
// och postar mot /api/contracts. Ingen ramverksberoende - byt mot React/Vue
// om formularet vaxer, men strukturen (dotted-name -> canonical model) haller.

function addLineRow() {
  const container = document.getElementById("lines");
  const idx = container.children.length;
  const row = document.createElement("div");
  row.className = "line-row";
  row.innerHTML = `
    <input placeholder="Artikelkod (t.ex. OUTLET_FEE)" name="lines.${idx}.itemCode" required />
    <input placeholder="Beskrivning" name="lines.${idx}.description" required />
    <input placeholder="Antal" type="number" step="1" name="lines.${idx}.quantity" required />
    <input placeholder="Pris" type="number" step="0.01" name="lines.${idx}.unitPrice" required />
    <select name="lines.${idx}.billingType">
      <option value="recurring">Löpande</option>
      <option value="one_time">Engångs</option>
    </select>
  `;
  container.appendChild(row);
}

function addSignatoryRow() {
  const container = document.getElementById("signatories");
  const idx = container.children.length;
  const row = document.createElement("div");
  row.className = "line-row";
  row.innerHTML = `
    <select name="signing.signatories.${idx}.role">
      <option value="provider">Leverantör</option>
      <option value="customer">Beställare</option>
    </select>
    <input placeholder="Namn" name="signing.signatories.${idx}.name" required />
    <input placeholder="E-post" type="email" name="signing.signatories.${idx}.email" required />
  `;
  container.appendChild(row);
}

function setDeep(obj, path, value) {
  const keys = path.split(".");
  let node = obj;
  for (let i = 0; i < keys.length - 1; i++) {
    const key = keys[i];
    const nextKeyIsIndex = /^\d+$/.test(keys[i + 1]);
    if (!(key in node)) node[key] = nextKeyIsIndex ? [] : {};
    node = node[key];
  }
  node[keys[keys.length - 1]] = value;
}

function collectFormData(form) {
  const data = {};
  for (const el of form.elements) {
    if (!el.name) continue;
    let value = el.value;
    if (el.type === "checkbox") value = el.checked;
    else if (el.type === "number") value = value === "" ? undefined : Number(value);
    if (value === "" || value === undefined) continue;
    setDeep(data, el.name, value);
  }
  return data;
}

document.getElementById("add-line").addEventListener("click", addLineRow);
document.getElementById("add-signatory").addEventListener("click", addSignatoryRow);
addLineRow();
addSignatoryRow();

document.getElementById("contract-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const payload = collectFormData(form);
  const resultEl = document.getElementById("result");
  resultEl.textContent = "Skickar...";

  const res = await fetch("/api/contracts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.json();
    resultEl.textContent = `Fel: ${JSON.stringify(err)}`;
    return;
  }

  const { contractId } = await res.json();
  resultEl.textContent = `Skickat, kontraktId ${contractId}. Väntar på export...`;
  pollStatus(contractId, resultEl);
});

async function pollStatus(contractId, resultEl) {
  for (let i = 0; i < 10; i++) {
    await new Promise((r) => setTimeout(r, 800));
    const res = await fetch(`/api/contracts/${contractId}`);
    if (!res.ok) continue;
    const contract = await res.json();
    resultEl.textContent =
      `Kontrakt ${contractId}\n` +
      `Dokument: ${contract.contractExport.status}\n` +
      `NetSuite: ${contract.netsuiteExport.status}`;
    if (contract.contractExport.status !== "pending" && contract.netsuiteExport.status !== "pending") {
      break;
    }
  }
}
