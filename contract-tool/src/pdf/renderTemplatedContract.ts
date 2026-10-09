import fs from "node:fs";
import path from "node:path";
import { randomUUID } from "node:crypto";
import PDFDocument from "pdfkit";
import type { ContractTemplate } from "../types/contractTemplate";
import { PDFKIT_BOLD_FONT_MAP, PDFKIT_FONT_MAP } from "../types/brandProfile";
import { getBrandProfile, getLogoFilePath } from "../storage/brandProfileStore";
import { drawHeader, drawFooters } from "./pdfHeader";

const OUTPUT_DIR = path.join(__dirname, "..", "..", "data", "contracts");

const PLACEHOLDER_PATTERN = /\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}/g;

function substitutePlaceholders(bodyText: string, fieldValues: Record<string, string>): string {
  return bodyText.replace(PLACEHOLDER_PATTERN, (_match, key: string) =>
    key in fieldValues ? fieldValues[key] : `{{${key}}}`
  );
}

// Genererar en PDF fran en kontraktsmall: ersatter {{falt}}-platshallare i
// bodyText med ifyllda varden och floder texten som stycken genom pdfkit,
// med samma varumarkesprofil (logga/farger/typsnitt/marginaler/sidhuvud/-fot)
// som renderContractPdf.ts - se pdfHeader.ts for den delade header/footer-logiken.
export async function renderTemplatedContract(
  template: ContractTemplate,
  fieldValues: Record<string, string>
): Promise<{ contractId: string; filePath: string }> {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  const contractId = `TC-${randomUUID().slice(0, 8).toUpperCase()}`;
  const filePath = path.join(OUTPUT_DIR, `${contractId}.pdf`);

  const profile = getBrandProfile();
  const logoPath = getLogoFilePath();
  const bodyFont = PDFKIT_FONT_MAP[profile.font];
  const boldFont = PDFKIT_BOLD_FONT_MAP[profile.font];
  const renderedText = substitutePlaceholders(template.bodyText, fieldValues);

  return new Promise((resolve, reject) => {
    const doc = new PDFDocument({ margins: profile.layout.margins, bufferPages: true });
    doc.on("pageAdded", () => drawHeader(doc, profile, logoPath));

    const stream = fs.createWriteStream(filePath);
    doc.pipe(stream);

    doc.font(bodyFont).fillColor("black");
    drawHeader(doc, profile, logoPath);

    doc.font(boldFont).fontSize(18).fillColor(profile.colors.primary).text(template.name);
    doc.font(bodyFont).fontSize(12).fillColor("black").moveDown();

    const contentWidth = doc.page.width - profile.layout.margins.left - profile.layout.margins.right;
    for (const paragraph of renderedText.split(/\n\s*\n/)) {
      if (!paragraph.trim()) continue;
      doc.text(paragraph.trim(), { width: contentWidth });
      doc.moveDown();
    }

    drawFooters(doc, profile);

    doc.end();
    stream.on("finish", () => resolve({ contractId, filePath }));
    stream.on("error", reject);
  });
}
