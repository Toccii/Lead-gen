import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Lead-gen Dashboard",
  description: "B2B lead generation & outreach dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="it">
      <body>{children}</body>
    </html>
  );
}
