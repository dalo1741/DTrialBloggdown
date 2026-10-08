import { z } from "zod";

// Varumärkesprofil - en global uppsättning branding-inställningar som
// tillämpas på alla exporterade kontrakts-PDF:er (logga, färger, typsnitt,
// layout). Loggan själv hanteras separat via en egen upload-endpoint, inte
// som en del av detta schema.

const hexColorSchema = z
  .string()
  .regex(/^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/, "Måste vara en hex-färg, t.ex. #1a73e8");

// Begränsad till pdfkits inbyggda standardtypsnitt - inga uppladdade
// custom-fonter i den här fasen (undviker licens-/embedding-hantering).
export const FONT_OPTIONS = ["helvetica", "helvetica-bold", "times", "courier"] as const;
export type BrandFont = (typeof FONT_OPTIONS)[number];

export const PDFKIT_FONT_MAP: Record<BrandFont, string> = {
  helvetica: "Helvetica",
  "helvetica-bold": "Helvetica-Bold",
  times: "Times-Roman",
  courier: "Courier",
};

// Fetstil i samma familj, för rubriker oavsett vilket body-typsnitt som valts.
export const PDFKIT_BOLD_FONT_MAP: Record<BrandFont, string> = {
  helvetica: "Helvetica-Bold",
  "helvetica-bold": "Helvetica-Bold",
  times: "Times-Bold",
  courier: "Courier-Bold",
};

export const LOGO_POSITIONS = ["left", "center", "right"] as const;
export type LogoPosition = (typeof LOGO_POSITIONS)[number];

export const brandProfileInputSchema = z.object({
  colors: z.object({
    primary: hexColorSchema,
    secondary: hexColorSchema,
  }),
  font: z.enum(FONT_OPTIONS),
  layout: z.object({
    margins: z.object({
      top: z.number().min(0).max(200),
      right: z.number().min(0).max(200),
      bottom: z.number().min(0).max(200),
      left: z.number().min(0).max(200),
    }),
    header: z.object({
      enabled: z.boolean(),
      text: z.string().max(200).optional().default(""),
    }),
    footer: z.object({
      enabled: z.boolean(),
      text: z.string().max(200).optional().default(""),
    }),
    logoPosition: z.enum(LOGO_POSITIONS),
  }),
});

export type BrandProfileInput = z.infer<typeof brandProfileInputSchema>;

export interface BrandLogo {
  fileName: string;
  mimeType: string;
  updatedAt: string;
}

export interface BrandProfile extends BrandProfileInput {
  logo: BrandLogo | null;
  updatedAt: string;
}

export const DEFAULT_BRAND_PROFILE: BrandProfile = {
  colors: { primary: "#1a1a1a", secondary: "#666666" },
  font: "helvetica",
  layout: {
    margins: { top: 50, right: 50, bottom: 50, left: 50 },
    header: { enabled: false, text: "" },
    footer: { enabled: false, text: "" },
    logoPosition: "left",
  },
  logo: null,
  updatedAt: new Date(0).toISOString(),
};
