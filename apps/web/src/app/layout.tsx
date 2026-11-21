import type { Metadata, Viewport } from "next";
import { Noto_Nastaliq_Urdu } from "next/font/google";
import "./globals.css";
import SwRegister from "@/components/SwRegister";
const urdu = Noto_Nastaliq_Urdu({
  subsets: ["arabic"],
  weight: ["400", "700"],
  variable: "--font-urdu",
});

export const metadata: Metadata = {
  title: "Rahbar | رہبر",
  description: "Relief support made simple",
  manifest: "/manifest.json",
};

export const viewport: Viewport = {
  themeColor: "#047857",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ur" dir="rtl">
      <body
        className={`${urdu.variable} antialiased`}
        style={{ fontFamily: "var(--font-urdu), sans-serif", lineHeight: 2 }}
      >
        <SwRegister />
        {children}
      </body>
    </html>
  );
}