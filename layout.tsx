import './globals.css';

export const metadata = {
  title: 'Articles Builder',
  description: 'AI-assisted article ideation and writing, tuned to your topics and tone.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="aurora-field" aria-hidden="true">
          <div className="aurora-blob b1" />
          <div className="aurora-blob b2" />
          <div className="aurora-blob b3" />
        </div>
        <div style={{ position: 'relative', zIndex: 1 }}>{children}</div>
      </body>
    </html>
  );
}
