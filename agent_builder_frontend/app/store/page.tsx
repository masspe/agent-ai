'use client';
import Nav from '../../components/Nav'; import Link from 'next/link'; import { useEffect, useState } from 'react'; import { apiFetch } from '../../lib/api';
type Listing={id:number; title:string; slug:string; price_cents:number; currency:string; visibility:string; short_subtitle?:string|null;};
export default function Store(){
  const [rows,setRows]=useState<Listing[]>([]); const [err,setErr]=useState<string|null>(null);
  useEffect(()=>{ apiFetch('/store_listings').then(setRows).catch(e=>setErr(String(e))); },[]);
  return (<div><Nav/><div className="container py-6 grid gap-6"><div className="flex items-center justify-between">
    <h1 className="text-2xl font-semibold">Store</h1><Link href="/store/new" className="btn">Nuova Scheda</Link></div>{err&&<div className="text-red-600">{err}</div>}
    <div className="grid gap-3">{rows.map(x=>(<Link key={x.id} href={`/store/${x.id}`} className="card">
      <div className="font-semibold">{x.title}</div><div className="text-sm text-gray-600">{x.slug} — {x.currency} {(x.price_cents/100).toFixed(2)}</div>
    </Link>))}</div></div></div>);
}
