import type { Contract } from "../types/contract";
import { updateContractExport } from "../storage/contractStore";
import { renderContractPdf } from "../pdf/renderContractPdf";
import { sendForESignature } from "./eSignClient";

// Ett av de tva oberoende exportsporen som triggas av CONTRACT_SUBMITTED.
// Fel har ska aldrig paverka NetSuite-exporten och tvartom.
export async function exportContractDocument(contract: Contract): Promise<void> {
  try {
    if (contract.signing.method === "pdf_only") {
      const filePath = await renderContractPdf(contract);
      updateContractExport(contract.contractId, {
        status: "confirmed",
        provider: "pdf",
        documentId: filePath,
        lastError: null,
        updatedAt: new Date().toISOString(),
      });
    } else {
      const result = await sendForESignature(contract);
      updateContractExport(contract.contractId, {
        status: "sent",
        provider: "e_sign",
        documentId: result.documentId,
        lastError: null,
        updatedAt: new Date().toISOString(),
      });
    }
  } catch (err) {
    updateContractExport(contract.contractId, {
      status: "failed",
      lastError: err instanceof Error ? err.message : String(err),
      updatedAt: new Date().toISOString(),
    });
  }
}
