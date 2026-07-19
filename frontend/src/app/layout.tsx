import type { Metadata, Viewport } from "next";
import { Geist_Mono, Figtree } from "next/font/google";
import "./globals.css";
import { cn } from "@/lib/utils";

const figtree = Figtree({
  subsets: ["latin"],
  variable: "--font-sans",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Space Intelligence Platform",
  description:
    "Ask about near-Earth objects, space weather, Earth events, and more — powered by a multi-agent RAG system over live NASA data.",
};

export const viewport: Viewport = {
  themeColor: "#04050d",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={cn("h-full", "dark", "antialiased", geistMono.variable, figtree.variable, "font-sans")}
    >
      <body
        className={cn(
          "min-h-full flex flex-col",
          "bg-[#04050d] text-slate-100",
          "bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(99,102,241,0.15),transparent)]"
        )}
      >
        {children}
      </body>
    </html>
  );
}