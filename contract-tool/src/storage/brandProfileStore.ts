import fs from "node:fs";
import path from "node:path";
import {
  type BrandLogo,
  type BrandProfile,
  type BrandProfileInput,
  DEFAULT_BRAND_PROFILE,
} from "../types/brandProfile";

// Varumärkesprofilen är global (en enda profil, inget flerkunds-stöd ännu)
// och, till skillnad från contractStore, disk-persisterad - det är en
// engångskonfiguration som inte ska försvinna vid omstart. Byt mot en
// riktig databas när övrig lagring migreras dit (se README).
const BRAND_DIR = path.join(__dirname, "..", "..", "data", "brand");
const PROFILE_PATH = path.join(BRAND_DIR, "profile.json");

const MIME_TO_EXT: Record<string, string> = {
  "image/png": "png",
  "image/jpeg": "jpg",
  "image/svg+xml": "svg",
};

function readProfileFile(): BrandProfile {
  try {
    const raw = fs.readFileSync(PROFILE_PATH, "utf-8");
    return JSON.parse(raw) as BrandProfile;
  } catch {
    return DEFAULT_BRAND_PROFILE;
  }
}

function writeProfileFile(profile: BrandProfile): void {
  fs.mkdirSync(BRAND_DIR, { recursive: true });
  fs.writeFileSync(PROFILE_PATH, JSON.stringify(profile, null, 2));
}

export function getBrandProfile(): BrandProfile {
  return readProfileFile();
}

export function saveBrandProfile(input: BrandProfileInput): BrandProfile {
  const current = readProfileFile();
  const profile: BrandProfile = {
    ...input,
    logo: current.logo,
    updatedAt: new Date().toISOString(),
  };
  writeProfileFile(profile);
  return profile;
}

export function saveBrandLogo(buffer: Buffer, mimeType: string): BrandLogo {
  const ext = MIME_TO_EXT[mimeType];
  if (!ext) {
    throw new Error(`Okänd logotyp-filtyp: ${mimeType}`);
  }

  fs.mkdirSync(BRAND_DIR, { recursive: true });

  // Rensa bort en tidigare logga med annan filändelse så vi inte samlar skräp.
  for (const existingExt of Object.values(MIME_TO_EXT)) {
    const existingPath = path.join(BRAND_DIR, `logo.${existingExt}`);
    if (existingExt !== ext && fs.existsSync(existingPath)) {
      fs.unlinkSync(existingPath);
    }
  }

  const fileName = `logo.${ext}`;
  fs.writeFileSync(path.join(BRAND_DIR, fileName), buffer);

  const logo: BrandLogo = { fileName, mimeType, updatedAt: new Date().toISOString() };
  const current = readProfileFile();
  writeProfileFile({ ...current, logo, updatedAt: new Date().toISOString() });
  return logo;
}

export function getLogoFilePath(): string | null {
  const profile = readProfileFile();
  if (!profile.logo) return null;
  const filePath = path.join(BRAND_DIR, profile.logo.fileName);
  return fs.existsSync(filePath) ? filePath : null;
}
