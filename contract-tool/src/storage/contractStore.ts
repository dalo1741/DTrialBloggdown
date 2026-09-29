import type { Contract } from "../types/contract";

// In-memory store for scaffoldet. Byt mot en riktig databas (Postgres m.m.)
// innan produktion - status per exportspar maste overleva en omstart.
const contracts = new Map<string, Contract>();

export function saveContract(contract: Contract): void {
  contracts.set(contract.contractId, contract);
}

export function getContract(contractId: string): Contract | undefined {
  return contracts.get(contractId);
}

export function updateContractExport(
  contractId: string,
  patch: Partial<Contract["contractExport"]>
): void {
  const contract = contracts.get(contractId);
  if (!contract) return;
  contract.contractExport = { ...contract.contractExport, ...patch };
}

export function updateNetsuiteExport(
  contractId: string,
  patch: Partial<Contract["netsuiteExport"]>
): void {
  const contract = contracts.get(contractId);
  if (!contract) return;
  contract.netsuiteExport = { ...contract.netsuiteExport, ...patch };
}
