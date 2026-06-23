import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // The Next image optimization endpoint (/_next/image) was returning 400 on the deployment,
  // so every <Image> (the logo, the incident schematics, the lineage thumbnails) rendered as
  // a broken image while the raw /public PNGs served fine (200). These assets are
  // hand-authored and already correctly sized — disable optimization and serve them directly.
  images: { unoptimized: true },
  // Carbon ships untranspiled ESM/SCSS; transpile its packages through Next's compiler.
  transpilePackages: ["@carbon/react", "@carbon/styles", "@carbon/icons-react"],
  sassOptions: {
    // Carbon's SCSS uses bare `@use 'scss/...'` paths that resolve from node_modules;
    // both keys are set so the rule works under classic sass-loader and modern Sass.
    includePaths: ["node_modules"],
    loadPaths: ["node_modules"],
    // Silence the deprecation warnings Carbon's Sass emits on Dart Sass; they are
    // upstream and not actionable from this app.
    quietDeps: true,
    silenceDeprecations: ["mixed-decls", "global-builtin", "import"],
  },
};

export default nextConfig;
