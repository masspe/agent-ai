'use client';
import Nav from '../../components/Nav'; import Link from 'next/link';
export default function Dashboard(){ return (<div><Nav/><div className="container py-6 grid gap-6">
  <div className="card"><h2 className="text-xl font-semibold mb-2">Benvenuto 👋</h2>
  <p className="text-gray-600">Crea un Agent con il Wizard, poi gestiscilo e pubblicalo nello Store.</p>
  <div className="mt-4 flex gap-2"><Link href="/agents/wizard" className="btn">Wizard</Link><Link href="/agents" className="btn">Gestisci Agents</Link><Link href="/store" className="btn">Store</Link></div></div></div></div>); }
