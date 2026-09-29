import type { Contract } from "../types/contract";

export interface ESignResult {
  documentId: string;
}

// STUB - byt mot riktig integration mot e-signeringsleverantör
// (t.ex. Scrive, Oneflow, DocuSign) nar ni valt en.
// Anropet ska skicka med kontraktets falt + `signing.signatories` och
// fa tillbaka ett dokument-id att spara for uppfoljning/status-polling.
export async function sendForESignature(contract: Contract): Promise<ESignResult> {
  console.log(
    `[eSignClient] STUB: skulle skicka ${contract.contractId} till e-signering for`,
    contract.signing.signatories.map((s) => s.email).join(", ")
  );

  // TODO: ersatt med riktigt API-anrop, t.ex.:
  // const res = await fetch(`${process.env.ESIGN_BASE_URL}/documents`, {
  //   method: "POST",
  //   headers: { Authorization: `Bearer ${process.env.ESIGN_API_KEY}`, "Content-Type": "application/json" },
  //   body: JSON.stringify(buildESignPayload(contract)),
  // });
  // if (!res.ok) throw new Error(`eSign API error: ${res.status}`);
  // return await res.json();

  return { documentId: `stub-${contract.contractId}` };
}
