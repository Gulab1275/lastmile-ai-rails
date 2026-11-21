import type { Metadata } from "next";
import { Noto_Nastaliq_Urdu } from "next/font/google";
import "./globals.css";

const urdu = Noto_Nastaliq_Urdu({
  subsets: ["arabic"],
  weight: ["400", "700"],
  variable: "--font-urdu",
});

export const metadata: Metadata = {
  title: "Rahbar | رہبر",
  description: "Relief support made simple",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ur" dir="rtl">
      <body
        className={`${urdu.variable} antialiased`}
        style={{ fontFamily: "var(--font-urdu), sans-serif" }}
      >
        {children}
      </body>
    </html>
  );
}