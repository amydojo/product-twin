import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: "standalone",
  transpilePackages: ["@product-twin/packaging-schema"],
  allowedDevOrigins: ["127.0.0.1"],
};

export default nextConfig;
