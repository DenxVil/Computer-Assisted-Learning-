import type { Metadata } from "next";
import "./globals.css";
import "./portal.css";

export const metadata: Metadata = {
  title: "Virtual Pharmacology Laboratory",
  description: "Computer assisted pharmacology practical teaching",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}

