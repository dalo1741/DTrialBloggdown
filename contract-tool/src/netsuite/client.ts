export interface NetsuiteCustomerPayload {
  externalId: string;
  companyName: string;
  subsidiary: { internalId: string };
  email: string;
}

export interface NetsuiteSalesOrderPayload {
  externalId: string;
  entity: { externalId: string };
  trandate: string;
  currency: string;
  memo: string;
  custbody_contract_id: string;
  custbody_facility_uid: string;
  itemList: Array<{
    item: string;
    quantity: number;
    rate: number;
    billingType: "recurring" | "one_time";
  }>;
}

export interface NetsuiteRentCalculationSetupPayload {
  recordType: "customrecord_charging_contract_terms";
  facilityUID: string;
  energyMeterId: string;
  pricePerKwh: number;
  providerRevenueSharePct: number;
  effectiveFrom: string;
  effectiveTo: string | null;
}

// STUB - byt mot riktiga anrop mot NetSuite SuiteTalk REST API.
// Anvand externalId konsekvent for idempotens (retry ska inte duplicera).
export async function upsertCustomer(payload: NetsuiteCustomerPayload): Promise<{ internalId: string }> {
  console.log("[netsuite] STUB upsertCustomer", payload);
  // TODO: PUT https://{account}.suitetalk.api.netsuite.com/services/rest/record/v1/customer/eid:{externalId}
  return { internalId: `stub-customer-${payload.externalId}` };
}

export async function createSalesOrder(payload: NetsuiteSalesOrderPayload): Promise<{ internalId: string }> {
  console.log("[netsuite] STUB createSalesOrder", payload);
  // TODO: POST https://{account}.suitetalk.api.netsuite.com/services/rest/record/v1/salesOrder
  return { internalId: `stub-so-${payload.externalId}` };
}

export async function upsertRentCalculationSetup(
  payload: NetsuiteRentCalculationSetupPayload
): Promise<{ internalId: string }> {
  console.log("[netsuite] STUB upsertRentCalculationSetup", payload);
  // TODO: PUT mot custom record-typen som den befintliga hyresmotorn laser fran,
  // matchat pa facilityUID / energyMeterId.
  return { internalId: `stub-terms-${payload.facilityUID}` };
}
