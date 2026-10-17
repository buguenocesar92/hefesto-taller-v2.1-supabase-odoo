import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = {title:'Hefesto Taller · Gestión de servicio técnico',description:'El control de tu taller, en un solo lugar.'};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="es"><body>{children}</body></html>}
