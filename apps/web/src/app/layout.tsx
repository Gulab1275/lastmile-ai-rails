import type { Metadata, Viewport } from "next";
import { Inter, Noto_Nastaliq_Urdu, Noto_Naskh_Arabic } from "next/font/google";
import "./globals.css";
import SwRegister from "@/components/SwRegister";
import PrototypeBanner from "@/components/PrototypeBanner";
import { UIProvider } from "@/lib/uiContext";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });

const nastaliq = Noto_Nastaliq_Urdu({
  subsets: ["arabic"],
  weight: ["400", "700"],
  variable: "--font-nastaliq",
  display: "swap",
});

const naskh = Noto_Naskh_Arabic({
  subsets: ["arabic"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-naskh",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Rahbar · رہبر | Digital Relief on Public Rails",
  description: "DPI-powered relief assistance platform designed for non-readers and weak connectivity",
  manifest: "/manifest.json",
  icons: { icon: "/icon-192.png", apple: "/icon-192.png" },
};

export const viewport: Viewport = {
  themeColor: "#0B4F43",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ur" dir="rtl" className="h-full">
      <body
        className={`${inter.variable} ${nastaliq.variable} ${naskh.variable} font-sans antialiased min-h-screen text-[#17302B] bg-[#F7F4EE]`}
        style={{ lineHeight: 1.8 }}
      >
        <UIProvider>
          <SwRegister />
          <PrototypeBanner />
          {children}
        </UIProvider>
      </body>
    </html>
  );
}
