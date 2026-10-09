import fs from "node:fs";
import path from "node:path";
import { randomUUID } from "node:crypto";
import { type ContractTemplate, type TemplateInput, computeFields } from "../types/contractTemplate";

// Mallar ar konfiguration, precis som brand-profilen - disk-persisterade sa
// de overlever en omstart (hela poangen med fasen ar att kunna definiera nya
// avtalstyper utan att rora kod, da far de inte forsvinna nar servern startar om).
const TEMPLATES_DIR = path.join(__dirname, "..", "..", "data", "templates");

function templatePath(id: string): string {
  return path.join(TEMPLATES_DIR, `${id}.json`);
}

export function listTemplates(): ContractTemplate[] {
  if (!fs.existsSync(TEMPLATES_DIR)) return [];
  return fs
    .readdirSync(TEMPLATES_DIR)
    .filter((f) => f.endsWith(".json"))
    .map((f) => JSON.parse(fs.readFileSync(path.join(TEMPLATES_DIR, f), "utf-8")) as ContractTemplate)
    .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
}

export function getTemplate(id: string): ContractTemplate | undefined {
  try {
    return JSON.parse(fs.readFileSync(templatePath(id), "utf-8")) as ContractTemplate;
  } catch {
    return undefined;
  }
}

function writeTemplate(template: ContractTemplate): ContractTemplate {
  fs.mkdirSync(TEMPLATES_DIR, { recursive: true });
  fs.writeFileSync(templatePath(template.id), JSON.stringify(template, null, 2));
  return template;
}

export function createTemplate(input: TemplateInput): ContractTemplate {
  const now = new Date().toISOString();
  return writeTemplate({
    id: randomUUID(),
    name: input.name,
    bodyText: input.bodyText,
    fields: computeFields(input.bodyText, input.fieldConfig),
    createdAt: now,
    updatedAt: now,
  });
}

export function updateTemplate(id: string, input: TemplateInput): ContractTemplate | undefined {
  const existing = getTemplate(id);
  if (!existing) return undefined;
  return writeTemplate({
    ...existing,
    name: input.name,
    bodyText: input.bodyText,
    fields: computeFields(input.bodyText, input.fieldConfig),
    updatedAt: new Date().toISOString(),
  });
}

export function duplicateTemplate(id: string): ContractTemplate | undefined {
  const existing = getTemplate(id);
  if (!existing) return undefined;
  const now = new Date().toISOString();
  return writeTemplate({
    ...existing,
    id: randomUUID(),
    name: `${existing.name} (kopia)`,
    createdAt: now,
    updatedAt: now,
  });
}

export function deleteTemplate(id: string): boolean {
  try {
    fs.unlinkSync(templatePath(id));
    return true;
  } catch {
    return false;
  }
}
