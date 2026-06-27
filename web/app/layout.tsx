import type { Metadata } from "next";
import "./globals.scss";
import "./tailwind.css";

// Absolute base for resolving the Open Graph / Twitter card image. Without it, Next
// resolves the relative /og-card.png against http://localhost:3000 in the built HTML,
// so a shared link (Slack, X, LinkedIn) shows a broken preview. On Vercel the production
// URL is injected; the literal fallback covers local builds and any non-Vercel host.
const SITE_URL = process.env.VERCEL_PROJECT_PRODUCTION_URL
  ? `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}`
  : "https://offside-june-2026.vercel.app";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: "OFFSIDE — The Football Disagreement Engine",
  description:
    "OFFSIDE shows why a football decision stays argued — broken into four plain reasons, " +
    "each proved against the real Laws of the Game and audited by a second IBM model.",
  applicationName: "OFFSIDE",
  authors: [{ name: "Hriday Vig" }],
  // Reference the favicon and social card from /public directly rather than the
  // app/icon.png + app/opengraph-image.png file conventions: the webpack metadata-image
  // loader fails on those binaries in the Vercel/Linux build ("unsupported file type"),
  // and pointing metadata at static /public assets sidesteps that loader entirely.
  icons: { icon: "/favicon.png", apple: "/favicon.png" },
  openGraph: {
    title: "OFFSIDE — The Football Disagreement Engine",
    description:
      "Why a billion people never agree on the same call — decomposed into four reasons, " +
      "proved against the Laws of the Game.",
    type: "website",
    images: [{ url: "/og-card.png", width: 1536, height: 1024, alt: "OFFSIDE" }],
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
