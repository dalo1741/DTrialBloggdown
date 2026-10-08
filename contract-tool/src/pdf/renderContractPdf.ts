import fs from "node:fs";
import path from "node:path";
import PDFDocument from "pdfkit";
import type { Contract } from "../types/contract";
import { type BrandProfile, PDFKIT_BOLD_FONT_MAP, PDFKIT_FONT_MAP } from "../types/brandProfile";
import { getBrandProfile, getLogoFilePath } from "../storage/brandProfileStore";

const OUTPUT_DIR = path.join(__dirname, "..", "..", "data", "contracts");

const HEADER_LOGO_BOX = 50; // pt, höjd på logga-området i sidhuvudet
const HEADER_SPACING_AFTER = 15; // pt, luft mellan sidhuvud och innehåll

function drawHeader(doc: PDFKit.PDFDocument, profile: BrandProfile, logoPath: string | null): void {
  const { margins, header, logoPosition } = profile.layout;
  const startY = margins.top;
  const contentWidth = doc.page.width - margins.left - margins.right;
  let bottom = startY;

  if (logoPath) {
    const logoWidth = 90;
    const x =
      logoPosition === "left"
        ? margins.left
        : logoPosition === "right"
          ? doc.page.width - margins.right - logoWidth
          : margins.left + (contentWidth - logoWidth) / 2;
    doc.image(logoPath, x, startY, { fit: [logoWidth, HEADER_LOGO_BOX] });
    bottom = startY + HEADER_LOGO_BOX;
  }

  if (header.enabled && header.text) {
    doc
      .font(PDFKIT_FONT_MAP[profile.font])
      .fontSize(9)
      .fillColor(profile.colors.secondary)
      .text(header.text, margins.left, bottom + 5, { width: contentWidth, align: "center" });
    bottom += 5 + doc.heightOfString(header.text, { width: contentWidth });
  }

  if (logoPath || (header.enabled && header.text)) {
    const ruleY = bottom + 8;
    doc
      .strokeColor(profile.colors.primary)
      .lineWidth(1.5)
      .moveTo(margins.left, ruleY)
      .lineTo(doc.page.width - margins.right, ruleY)
      .stroke();
    bottom = ruleY;
  }

  doc.y = bottom + HEADER_SPACING_AFTER;
  doc.fillColor("black");
}

function drawFooters(doc: PDFKit.PDFDocument, profile: BrandProfile): void {
  const { margins, footer } = profile.layout;
  const range = doc.bufferedPageRange();
  for (let i = range.start; i < range.start + range.count; i++) {
    doc.switchToPage(i);
    const y = doc.page.height - margins.bottom + 10;
    const contentWidth = doc.page.width - margins.left - margins.right;

    // doc.text() annars lägger automatiskt till en ny sida så fort y + text
    // skulle hamna under bottenmarginalen - vi ritar medvetet där, så
    // marginalkontrollen stängs tillfälligt av för det här anropet.
    const originalBottomMargin = doc.page.margins.bottom;
    doc.page.margins.bottom = 0;

    doc.font(PDFKIT_FONT_MAP[profile.font]).fontSize(8).fillColor(profile.colors.secondary);
    if (footer.enabled && footer.text) {
      doc.text(footer.text, margins.left, y, { width: contentWidth * 0.7, align: "left", lineBreak: false });
    }
    doc.text(`Sida ${i - range.start + 1} av ${range.count}`, margins.left, y, {
      width: contentWidth,
      align: "right",
      lineBreak: false,
    });
    doc.fillColor("black");

    doc.page.margins.bottom = originalBottomMargin;
  }
}

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
