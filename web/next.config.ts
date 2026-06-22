import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
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
