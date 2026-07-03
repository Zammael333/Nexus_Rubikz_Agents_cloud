import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "NEXUS RUBYKZ — Edge Glow Dashboard",
  description: "Real-time system health monitoring for NEXUS-RUBYKZ",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <Sidebar />
        <main className="lg:ml-56 min-h-screen p-4 md:p-6 pt-14 lg:pt-6">{children}</main>
      </body>
    </html>
  );
}
