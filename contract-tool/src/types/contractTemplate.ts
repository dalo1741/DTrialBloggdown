import { z } from "zod";

// Kontraktsmall - fast text med {{platshallare}} som ersatts med ifyllda
// falt nar ett konkret avtal genereras fran mallen. Faltlistan harleds
// automatiskt ur bodyText (ingen separat faltdeklaration att halla i synk) -
// se extractPlaceholderKeys/computeFields.

export const FIELD_TYPES = ["text", "number", "date"] as const;
export type TemplateFieldType = (typeof FIELD_TYPES)[number];

export interface TemplateField {
  key: string;
  label: string;
  type: TemplateFieldType;
}

const PLACEHOLDER_PATTERN = /\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}/g;

export function extractPlaceholderKeys(bodyText: string): string[] {
  const seen = new Set<string>();
  const keys: string[] = [];
  for (const match of bodyText.matchAll(PLACEHOLDER_PATTERN)) {
    const key = match[1];
    if (!seen.has(key)) {
      seen.add(key);
      keys.push(key);
    }
  }
  return keys;
}

const fieldConfigEntrySchema = z.object({
  label: z.string().min(1).max(100),
  type: z.enum(FIELD_TYPES),
});

export const templateInputSchema = z.object({
  name: z.string().min(1).max(200),
  bodyText: z.string().min(1),
  // Per-falt-overrides (etikett/typ), nycklade pa platshallarnamnet. Vilka
  // falt som faktiskt finns pa mallen bestams av bodyText, inte av den har
  // listan - en override for en nyckel som inte langre forekommer i texten
  // ignoreras bara.
  fieldConfig: z.record(fieldConfigEntrySchema).default({}),
});
export type TemplateInput = z.infer<typeof templateInputSchema>;

export interface ContractTemplate {
  id: string;
  name: string;
  bodyText: string;
  fields: TemplateField[];
  createdAt: string;
  updatedAt: string;
}

export function computeFields(bodyText: string, fieldConfig: TemplateInput["fieldConfig"]): TemplateField[] {
  return extractPlaceholderKeys(bodyText).map((key) => ({
    key,
    label: fieldConfig[key]?.label ?? key,
    type: fieldConfig[key]?.type ?? "text",
  }));
}

// Bygger ett zod-schema for ifyllda faltvarden dynamiskt fran mallens
// faltlista - motsvarigheten till de statiska scheman under src/types/ for
// de har genererade, per-mall-unika formen.
export function buildFieldValuesSchema(fields: TemplateField[]) {
  const shape: Record<string, z.ZodTypeAny> = {};
  for (const field of fields) {
    if (field.type === "number") {
      // Tomt falt ska underkannas, inte tolkas som 0 - darfor min(1) innan
      // coercion (Number("") ar 0, inte NaN, och skulle annars slinka igenom).
      shape[field.key] = z
        .string()
        .trim()
        .min(1, "Obligatoriskt fält")
        .pipe(z.coerce.number({ invalid_type_error: "Måste vara ett tal" }));
    } else if (field.type === "date") {
      shape[field.key] = z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Måste vara ett datum (ÅÅÅÅ-MM-DD)");
    } else {
      shape[field.key] = z.string().min(1, "Obligatoriskt fält");
    }
  }
  return z.object(shape);
}
