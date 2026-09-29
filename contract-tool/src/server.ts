import path from "node:path";
import { randomUUID } from "node:crypto";
import express from "express";
import { contractInputSchema, type Contract } from "./types/contract";
import { saveContract, getContract } from "./storage/contractStore";
import { contractEvents, CONTRACT_SUBMITTED, emitContractSubmitted } from "./events";
import { exportContractDocument } from "./exporters/contractDocumentExporter";
import { exportToNetsuite } from "./exporters/netsuiteExporter";

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, "..", "public")));

// De tva exportsporen ar helt oberoende lyssnare pa samma event -
// ett fel i den ena blockerar eller paverkar aldrig den andra.
contractEvents.on(CONTRACT_SUBMITTED, (contract: Contract) => {
  void exportContractDocument(contract);
});
contractEvents.on(CONTRACT_SUBMITTED, (contract: Contract) => {
  void exportToNetsuite(contract);
});

app.post("/api/contracts", (req, res) => {
  const parsed = contractInputSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ error: parsed.error.flatten() });
  }

  const now = new Date().toISOString();
  const contract: Contract = {
    ...parsed.data,
    contractId: `CTR-${new Date().getFullYear()}-${randomUUID().slice(0, 8).toUpperCase()}`,
    status: "submitted",
    createdBy: req.header("x-user-email") ?? "unknown",
    createdAt: now,
    contractExport: { status: "pending", provider: parsed.data.signing.method, documentId: null, lastError: null, updatedAt: null },
    netsuiteExport: { status: "pending", lastError: null, netsuiteSalesOrderId: null, updatedAt: null },
  };

  saveContract(contract);
  emitContractSubmitted(contract);

  res.status(202).json({ contractId: contract.contractId });
});

app.get("/api/contracts/:contractId", (req, res) => {
  const contract = getContract(req.params.contractId);
  if (!contract) return res.status(404).json({ error: "not_found" });
  res.json(contract);
});

const PORT = process.env.PORT ? Number(process.env.PORT) : 3000;
app.listen(PORT, () => {
  console.log(`contract-tool listening on http://localhost:${PORT}`);
});
