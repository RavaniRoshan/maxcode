import { Geist } from 'next/font/google';
import type { Metadata } from 'next';
import { Provider } from '@/components/provider';
import './global.css';

const geist = Geist({
  subsets: ['latin'],
});

export const metadata: Metadata = {
  metadataBase: new URL('https://ravaniroshan.github.io/maxcode'),
};

export default function Layout({ children }: LayoutProps<'/'>) {
  return (
    <html lang="en" className={geist.className} suppressHydrationWarning>
      <body className="flex flex-col min-h-screen">
        <Provider>{children}</Provider>
      </body>
    </html>
  );
}
