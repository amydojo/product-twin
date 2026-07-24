import type { ReactNode } from "react";
import "./globals.css";

export const metadata = {
  title: "Product Twin",
  description: "Turn a skincare product photo into a realistic, editable 3D product twin and studio render.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <header className="mast">
            <a href="/" aria-label="Product Twin home"><strong>PRODUCT TWIN</strong></a>
            <span className="eyebrow">Packaging reconstruction / v0.1</span>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
