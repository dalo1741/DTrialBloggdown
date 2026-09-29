import { EventEmitter } from "node:events";
import type { Contract } from "./types/contract";

// Enkel in-process event bus för scaffoldet. Bytt mot en riktig kö
// (SQS, RabbitMQ, ...) i produktion sa ett fel i en exportor inte
// kan tappa bort eventet eller blockera det andra spåret.
export const contractEvents = new EventEmitter();

export const CONTRACT_SUBMITTED = "contract.submitted";

export function emitContractSubmitted(contract: Contract): void {
  contractEvents.emit(CONTRACT_SUBMITTED, contract);
}
