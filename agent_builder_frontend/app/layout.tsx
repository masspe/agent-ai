import '../styles/globals.css';
import type { Metadata } from 'next';
export const metadata: Metadata = { title: 'Agent Builder', description: 'Agent Builder v3 Pro' };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (<html lang="it"><body>{children}</body></html>);
}
