import type { BrandProfile } from "../types/brandProfile";
import { PDFKIT_FONT_MAP } from "../types/brandProfile";

// Delad sidhuvud/-fot-logik for varumarkesprofilen - anvands av bade
// renderContractPdf.ts (fast Aimo Park-schema) och renderTemplatedContract.ts
// (kontraktsmallar), sa de tva renderarna alltid ser likadana ut.

export const HEADER_LOGO_BOX = 50; // pt, höjd på logga-området i sidhuvudet
export const HEADER_SPACING_AFTER = 15; // pt, luft mellan sidhuvud och innehåll

export function drawHeader(doc: PDFKit.PDFDocument, profile: BrandProfile, logoPath: string | null): void {
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

export function drawFooters(doc: PDFKit.PDFDocument, profile: BrandProfile): void {
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
