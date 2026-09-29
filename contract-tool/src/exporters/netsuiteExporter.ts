import type { Contract } from "../types/contract";
import { updateNetsuiteExport } from "../storage/contractStore";
import {
  upsertCustomer,
  createSalesOrder,
  upsertRentCalculationSetup,
} from "../netsuite/client";

// Det andra av de tva oberoende exportsporen. Bygger NetSuite-payload fran
// samma kontraktspost och gor tre anrop: kund, sales order (alla rader -
// bade tjansten och tillagg som SIM-kort), och - om avtalet har
// omsattningsbaserad ersattning - konfiguration for den befintliga
// automatiska hyres-/sjalvfaktureringsmotorn.
export async function exportToNetsuite(contract: Contract): Promise<void> {
  try {
    await upsertCustomer({
      externalId: contract.customer.externalId,
      companyName: contract.customer.name,
      subsidiary: { internalId: "1" }, // TODO: mappa fran contract.provider vid flera subsidiaries
      email: contract.invoicing.emailInvoice,
    });

    const salesOrder = await createSalesOrder({
      externalId: contract.contractId,
      entity: { externalId: contract.customer.externalId },
      trandate: contract.commercialTerms.startDate,
      currency: contract.commercialTerms.currency,
      memo: `Avtal ${contract.contractId}`,
      custbody_contract_id: contract.contractId,
      custbody_facility_uid: contract.facility.facilityUID,
      itemList: contract.lines.map((line) => ({
        item: line.itemCode,
        quantity: line.quantity,
        rate: line.unitPrice,
        billingType: line.billingType,
      })),
    });

    if (contract.revenueShare) {
      await upsertRentCalculationSetup({
        recordType: "customrecord_charging_contract_terms",
        facilityUID: contract.facility.facilityUID,
        energyMeterId: contract.facility.energyMeterId,
        pricePerKwh: contract.revenueShare.pricePerKwh,
        providerRevenueSharePct: contract.revenueShare.providerRevenueSharePct,
        effectiveFrom: contract.revenueShare.effectiveFrom,
        effectiveTo: contract.revenueShare.effectiveTo ?? null,
      });
    }

    updateNetsuiteExport(contract.contractId, {
      status: "confirmed",
      lastError: null,
      netsuiteSalesOrderId: salesOrder.internalId,
      updatedAt: new Date().toISOString(),
    });
  } catch (err) {
    updateNetsuiteExport(contract.contractId, {
      status: "failed",
      lastError: err instanceof Error ? err.message : String(err),
      updatedAt: new Date().toISOString(),
    });
  }
}
