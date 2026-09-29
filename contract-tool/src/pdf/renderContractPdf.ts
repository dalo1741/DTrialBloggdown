import fs from "node:fs";
import path from "node:path";
import PDFDocument from "pdfkit";
import type { Contract } from "../types/contract";

const OUTPUT_DIR = path.join(__dirname, "..", "..", "data", "contracts");

// Genererar en faktisk PDF fran kontraktsdata. Layouten ar medvetet enkel -
// byt ut mot en riktig mall (t.ex. HTML->PDF eller docx-mallning) nar den
// juridiska texten och grafiska profilen ar klar.
export async function renderContractPdf(contract: Contract): Promise<string> {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  const filePath = path.join(OUTPUT_DIR, `${contract.contractId}.pdf`);

  return new Promise((resolve, reject) => {
    const doc = new PDFDocument({ margin: 50 });
    const stream = fs.createWriteStream(filePath);
    doc.pipe(stream);

    doc.fontSize(18).text(`Avtal ${contract.contractId}`, { underline: true });
    doc.moveDown();

    doc.fontSize(12).text(`Leverantör: ${contract.provider.name} (${contract.provider.orgNumber})`);
    doc.text(`Beställare: ${contract.customer.name} (${contract.customer.orgNumber})`);
    doc.moveDown();

    doc.text(`Anläggning: ${contract.facility.propertyDesignation ?? "-"}, ${contract.facility.address.street}`);
    doc.text(`Avtalsperiod: ${contract.commercialTerms.startDate} – ${contract.commercialTerms.endDate ?? "tillsvidare"}`);
    doc.moveDown();

    doc.fontSize(14).text("Avgifter", { underline: true });
    doc.fontSize(12);
    for (const line of contract.lines) {
      const suffix = line.billingType === "recurring" ? "/mån" : " (engångs)";
      doc.text(`${line.description}: ${line.quantity} x ${line.unitPrice} ${contract.commercialTerms.currency}${suffix}`);
    }
    doc.moveDown();

    doc.fontSize(14).text("Signatärer", { underline: true });
    doc.fontSize(12);
    for (const s of contract.signing.signatories) {
      doc.text(`${s.role}: ${s.name} (${s.email})`);
    }

    doc.end();
    stream.on("finish", () => resolve(filePath));
    stream.on("error", reject);
  });
}
