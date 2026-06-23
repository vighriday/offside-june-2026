import type { Metadata } from "next";
import "./globals.scss";
import "./tailwind.css";

export const metadata: Metadata = {
  title: "OFFSIDE — The Football Disagreement Engine",
  description:
    "OFFSIDE shows why a football decision stays argued — broken into four plain reasons, " +
    "each proved against the real Laws of the Game and audited by a second IBM model.",
  applicationName: "OFFSIDE",
  authors: [{ name: "Hriday Vig" }],
  // app/icon.png and app/opengraph-image.png are auto-detected by Next; these make the
  // social card explicit for crawlers that read the tags directly.
  openGraph: {
    title: "OFFSIDE — The Football Disagreement Engine",
    description:
      "Why a billion people never agree on the same call — decomposed into four reasons, " +
      "proved against the Laws of the Game.",
    type: "website",
  },
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
