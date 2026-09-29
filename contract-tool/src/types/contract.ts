import { z } from "zod";

// Kanonisk kontraktsmodell - "source of truth" som formuläret skriver till
// och som de två exportörerna (kontraktsdokument, NetSuite) läser ifrån.
// Se contract-tool/README.md för bakgrund kring fälten.

const addressSchema = z.object({
  street: z.string().min(1),
  zip: z.string().min(1),
  city: z.string().min(1),
  country: z.string().default("SE"),
});

const representativeSchema = z.object({
  name: z.string().min(1),
  phone: z.string().min(1),
  email: z.string().email(),
});

const partySchema = z.object({
  name: z.string().min(1),
  orgNumber: z.string().min(1),
  address: addressSchema.optional(),
  representative: representativeSchema,
});

// En rad som alltid blir en Sales Order-rad i NetSuite, oavsett om det
// är själva tjänsten eller en tilläggstjänst (t.ex. SIM-kort).
const contractLineSchema = z.object({
  itemCode: z.string().min(1),
  description: z.string().min(1),
  quantity: z.number().positive(),
  unitPrice: z.number().nonnegative(),
  billingType: z.enum(["recurring", "one_time"]),
});

const signatorySchema = z.object({
  role: z.enum(["provider", "customer"]),
  name: z.string().min(1),
  email: z.string().email(),
});

// Underlag för motpartens/NetSuites automatiska hyres-/självfaktureringsmotor.
// Skapar ALDRIG en egen transaktion - bara konfigurationsdata kopplad till
// energyMeterId som den befintliga NetSuite-processen redan läser.
const revenueShareSchema = z.object({
  pricePerKwh: z.number().nonnegative(),
  providerRevenueSharePct: z.number().min(0).max(100),
  effectiveFrom: z.string(), // YYYY-MM-DD
  effectiveTo: z.string().optional(),
});

export const contractInputSchema = z.object({
  template: z.string().min(1),

  provider: partySchema,
  customer: partySchema.extend({
    externalId: z.string().min(1), // NetSuite-kundens externalId (idempotensnyckel)
  }),

  invoicing: z.object({
    emailInvoice: z.string().email(),
    address: addressSchema,
    invoiceMarking: z.string().optional(),
  }),

  facility: z.object({
    address: addressSchema,
    propertyDesignation: z.string().optional(),
    facilityUID: z.string().min(1),
    energyMeterId: z.string().min(1),
  }),

  commercialTerms: z.object({
    startDate: z.string(),
    endDate: z.string().optional(),
    autoRenewal: z.boolean().default(false),
    noticePeriodDays: z.number().int().nonnegative().optional(),
    currency: z.string().default("SEK"),
  }),

  lines: z.array(contractLineSchema).min(1),

  revenueShare: revenueShareSchema.optional(),

  signing: z.object({
    method: z.enum(["pdf_only", "e_sign"]),
    signatories: z.array(signatorySchema).min(1),
  }),
});

export type ContractInput = z.infer<typeof contractInputSchema>;

export type ExportStatus = "pending" | "sent" | "failed" | "confirmed";

export interface Contract extends ContractInput {
  contractId: string;
  status: "draft" | "submitted";
  createdBy: string;
  createdAt: string;
  contractExport: {
    status: ExportStatus;
    provider: string;
    documentId: string | null;
    lastError: string | null;
    updatedAt: string | null;
  };
  netsuiteExport: {
    status: ExportStatus;
    lastError: string | null;
    netsuiteSalesOrderId: string | null;
    updatedAt: string | null;
  };
}
