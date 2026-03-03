import './globals.css';
import Link from 'next/link';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Smart Parking - Supabase',
  description: 'Mobile + Admin parking booking system using Next.js and Supabase',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ar" dir="rtl">
      <body>
        <nav>
          <div className="container">
            <Link href="/mobile">حجز من الموبايل</Link>
            <Link href="/admin">لوحة المشرف</Link>
            <Link href="/login">تسجيل الدخول</Link>
          </div>
        </nav>
        {children}
      </body>
    </html>
  );
}
