import type { Metadata } from "next";
import "../styles/globals.css";

export const metadata: Metadata = {
  title: "AM הנדסה — מערכת הצעות מחיר",
  description: "מערכת אוטומטית לחישוב תמחור ויצירת הצעות מחיר לפרויקטי בנייה",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="he" dir="rtl">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body>
        <nav className="navbar">
          <a href="/" className="navbar-brand">AM הנדסה | הצעות מחיר</a>
          <ul className="navbar-nav">
            <li><a href="/">פרויקטים</a></li>
            <li><a href="/projects/new">+ חדש</a></li>
          </ul>
        </nav>
        <main>{children}</main>
      </body>
    </html>
  );
}
