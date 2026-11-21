import {
  Home, FilePlus2, FolderOpen, ShieldCheck, ScanSearch, Users, ClipboardList, SlidersHorizontal,
  ScrollText, BarChart3, Fingerprint, FileSearch, Map, type LucideIcon,
} from "lucide-react";

/** One icon per page, used by the menu bar and the home screen. */
export const NAV_ICONS: Record<string, LucideIcon> = {
  "/dashboard": Home,
  "/apply": FilePlus2,
  "/cases": FolderOpen,
  "/consent": ShieldCheck,
  "/scam": ScanSearch,
  "/families": Users,
  "/officer": ClipboardList,
  "/admin": SlidersHorizontal,
  "/auditor": ScrollText,
  "/eval": BarChart3,
  "/identity": Fingerprint,
  "/documents": FileSearch,
  "/scam-map": Map,
};