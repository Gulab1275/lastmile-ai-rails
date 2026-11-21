import type { Metadata, Viewport } from "next";
import { Inter, Noto_Nastaliq_Urdu } from "next/font/google";
import "./globals.css";
import SwRegister from "@/components/SwRegister";
import PrototypeBanner from "@/components/PrototypeBanner";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

const urdu = Noto_Nastaliq_Urdu({
  subsets: ["arabic"],
  weight: ["400", "700"],
  variable: "--font-urdu",
});

export const metadata: Metadata = {
  title: "Rahbar | رہبر",
  description: "Relief support made simple",
  manifest: "/manifest.json",
  icons: { icon: "/icon-192.png", apple: "/icon-192.png" },
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
        className={`${inter.variable} ${urdu.variable} font-sans antialiased`}
        style={{ lineHeight: 1.9 }}
      >
        <SwRegister />
        <PrototypeBanner />
        {children}
      </body>
    </html>
  );
}