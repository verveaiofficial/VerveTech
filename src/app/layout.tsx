import './globals.css';
import type { Metadata } from 'next';
import Script from 'next/script';

export const metadata: Metadata = {
  title: 'VerveTech - Premium Electronics & Tech Store',
  description: 'Effortless tech for the modern life. Discover premium gadgets, accessories, and smart devices.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="scroll-smooth">
      <body className="bg-white text-neutral-900 antialiased selection:bg-neutral-900 selection:text-white loading">
        {children}
        <Script id="remove-loading-script" strategy="afterInteractive">
          {`if (document.body) document.body.classList.remove("loading");`}
        </Script>
      </body>
    </html>
  );
}
