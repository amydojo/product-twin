import Link from "next/link";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata = {
  title: "Product Twin",
  description: "Turn a skincare product photo into a realistic, editable 3D product twin and studio render.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  const fixtureMode = process.env.PRODUCT_TWIN_FIXTURE_MODE === "true";

  return (
    <html lang="en">
      <body>
        <div className="shell">
          <header className="mast">
            <Link href="/" aria-label="Product Twin home"><strong>PRODUCT TWIN</strong></Link>
            <span className="eyebrow">
              Packaging reconstruction / v0.1
              {fixtureMode ? " · Fixture preview · no live worker" : ""}
            </span>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
