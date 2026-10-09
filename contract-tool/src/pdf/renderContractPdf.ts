import fs from "node:fs";
import path from "node:path";
import PDFDocument from "pdfkit";
import type { Contract } from "../types/contract";
import { PDFKIT_BOLD_FONT_MAP, PDFKIT_FONT_MAP } from "../types/brandProfile";
import { getBrandProfile, getLogoFilePath } from "../storage/brandProfileStore";
import { drawHeader, drawFooters } from "./pdfHeader";

const OUTPUT_DIR = path.join(__dirname, "..", "..", "data", "contracts");

// Genererar en faktisk PDF fran kontraktsdata, enligt den aktiva
// varumärkesprofilen (logga, färger, typsnitt, marginaler, sidhuvud/-fot).
// Layouten ar fortfarande medvetet enkel - byt ut mot en riktig mall
// (t.ex. HTML->PDF eller docx-mallning) nar den juridiska texten ar klar.
export async function renderContractPdf(contract: Contract): Promise<string> {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  const filePath = path.join(OUTPUT_DIR, `${contract.contractId}.pdf`);

  const profile = getBrandProfile();
  const logoPath = getLogoFilePath();
  const bodyFont = PDFKIT_FONT_MAP[profile.font];
  const boldFont = PDFKIT_BOLD_FONT_MAP[profile.font];

  return new Promise((resolve, reject) => {
    const doc = new PDFDocument({ margins: profile.layout.margins, bufferPages: true });
    doc.on("pageAdded", () => drawHeader(doc, profile, logoPath));

    const stream = fs.createWriteStream(filePath);
    doc.pipe(stream);

    doc.font(bodyFont).fillColor("black");
    drawHeader(doc, profile, logoPath);

    doc
      .font(boldFont)
      .fontSize(18)
      .fillColor(profile.colors.primary)
      .text(`Avtal ${contract.contractId}`);
    doc.font(bodyFont).fillColor("black").moveDown();

    doc.fontSize(12).text(`Leverantör: ${contract.provider.name} (${contract.provider.orgNumber})`);
    doc.text(`Beställare: ${contract.customer.name} (${contract.customer.orgNumber})`);
    doc.moveDown();

    doc.text(`Anläggning: ${contract.facility.propertyDesignation ?? "-"}, ${contract.facility.address.street}`);
    doc.text(`Avtalsperiod: ${contract.commercialTerms.startDate} – ${contract.commercialTerms.endDate ?? "tillsvidare"}`);
    doc.moveDown();

    doc.font(boldFont).fontSize(14).fillColor(profile.colors.secondary).text("Avgifter");
    doc.font(bodyFont).fontSize(12).fillColor("black");
    for (const line of contract.lines) {
      const suffix = line.billingType === "recurring" ? "/mån" : " (engångs)";
      doc.text(`${line.description}: ${line.quantity} x ${line.unitPrice} ${contract.commercialTerms.currency}${suffix}`);
    }
    doc.moveDown();

    doc.font(boldFont).fontSize(14).fillColor(profile.colors.secondary).text("Signatärer");
    doc.font(bodyFont).fontSize(12).fillColor("black");
    for (const s of contract.signing.signatories) {
      doc.text(`${s.role}: ${s.name} (${s.email})`);
    }

    drawFooters(doc, profile);

    doc.end();
    stream.on("finish", () => resolve(filePath));
    stream.on("error", reject);
  });
}
