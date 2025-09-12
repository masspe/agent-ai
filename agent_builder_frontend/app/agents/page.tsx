'use client';
import Nav from '../../components/Nav'; import Link from 'next/link'; import { useEffect, useState } from 'react'; import { apiFetch } from '../../lib/api';
type Agent={id:number; name:string; slug:string; description?:string};
export default function Agents(){
  const [rows,setRows]=useState<Agent[]>([]); const [error,setError]=useState<string|null>(null);
  useEffect(()=>{ apiFetch('/agents').then(setRows).catch(e=>setError(String(e))); },[]);
  return (<div><Nav/><div className="container py-6 grid gap-6"><div className="flex items-center justify-between">
    <h1 className="text-2xl font-semibold">Agents</h1><div className="flex gap-2"><Link href="/agents/new" className="btn">Nuovo</Link><Link href="/agents/wizard" className="btn">Wizard</Link></div></div>
    {error && <div className="text-red-600">{error}</div>}
    <div className="grid gap-3">{rows.map(a=>(<Link key={a.id} href={`/agents/${a.id}`} className="card hover:shadow-md transition-shadow">
      <div className="font-semibold">{a.name}</div><div className="text-sm text-gray-600">{a.slug}</div>{a.description && <p className="mt-2 text-gray-700">{a.description}</p>}
    </Link>))}{rows.length===0&&!error&&<div className="text-gray-600">Nessun agent.</div>}</div></div></div>);
}
