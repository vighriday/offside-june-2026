import type { Metadata } from "next";
import "./globals.scss";
import "./tailwind.css";

export const metadata: Metadata = {
  title: "OFFSIDE — The Football Disagreement Engine",
  description:
    "OFFSIDE decomposes why a football moment stays contested across four diagnostic " +
    "dimensions, every reading traced to a real source and audited by IBM Granite Guardian.",
  applicationName: "OFFSIDE",
  authors: [{ name: "Hriday Vig" }],
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  // g100 is Carbon's darkest theme — the default for IBM data and analytics products.
  // Setting it on <html> means every Carbon component and token resolves to the dark
  // palette without a client boundary.
  return (
    <html lang="en" data-carbon-theme="g100">
      <body>{children}</body>
    </html>
  );
}
