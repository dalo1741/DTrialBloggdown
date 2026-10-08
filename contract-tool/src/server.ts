import path from "node:path";
import { randomUUID } from "node:crypto";
import express from "express";
import multer from "multer";
import { contractInputSchema, type Contract } from "./types/contract";
import { saveContract, getContract } from "./storage/contractStore";
import { contractEvents, CONTRACT_SUBMITTED, emitContractSubmitted } from "./events";
import { exportContractDocument } from "./exporters/contractDocumentExporter";
import { exportToNetsuite } from "./exporters/netsuiteExporter";
import { brandProfileInputSchema } from "./types/brandProfile";
import { getBrandProfile, saveBrandProfile, saveBrandLogo, getLogoFilePath } from "./storage/brandProfileStore";

const LOGO_ALLOWED_MIME_TYPES = ["image/png", "image/jpeg", "image/svg+xml"];
const logoUpload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 2 * 1024 * 1024 },
  fileFilter: (_req, file, cb) => {
    if (!LOGO_ALLOWED_MIME_TYPES.includes(file.mimetype)) {
      cb(new Error(`Otillåten filtyp: ${file.mimetype}`));
      return;
    }
    cb(null, true);
  },
});

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

app.get("/api/brand-profile", (_req, res) => {
  res.json(getBrandProfile());
});

app.put("/api/brand-profile", (req, res) => {
  const parsed = brandProfileInputSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ error: parsed.error.flatten() });
  }
  res.json(saveBrandProfile(parsed.data));
});

app.post("/api/brand-profile/logo", (req, res) => {
  logoUpload.single("logo")(req, res, (err) => {
    if (err) return res.status(400).json({ error: err.message });
    if (!req.file) return res.status(400).json({ error: "Ingen fil mottagen" });
    const logo = saveBrandLogo(req.file.buffer, req.file.mimetype);
    res.json(logo);
  });
});

app.get("/api/brand-profile/logo", (_req, res) => {
  const filePath = getLogoFilePath();
  if (!filePath) return res.status(404).json({ error: "not_found" });
  res.sendFile(filePath);
});

const PORT = process.env.PORT ? Number(process.env.PORT) : 3000;
app.listen(PORT, () => {
  console.log(`contract-tool listening on http://localhost:${PORT}`);
});
