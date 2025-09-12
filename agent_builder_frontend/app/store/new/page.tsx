'use client';
import Nav from '../../../components/Nav'; import { useRouter } from 'next/navigation'; import { useEffect, useState } from 'react'; import { apiFetch } from '../../../lib/api';
type Agent={id:number; name:string; slug:string};
export default function NewListing(){
  const router=useRouter(); const [agents,setAgents]=useState<Agent[]>([]); const [title,setTitle]=useState(''); const [slug,setSlug]=useState(''); const [price,setPrice]=useState(0);
  useEffect(()=>{ apiFetch('/agents').then(setAgents).catch(()=>{}); },[]);
  async function submit(e:React.FormEvent){ e.preventDefault(); const created=await apiFetch('/store_listings',{method:'POST',body:JSON.stringify({ agent_id: agents[0]?.id, title, slug, price_cents: Math.round(price*100), currency:'EUR', visibility:'public' })}); router.push(`/store/${created.id}`); }
  return (<div><Nav/><div className="container py-6"><div className="card grid gap-3 max-w-2xl"><h1 className="text-2xl font-semibold">Nuova Scheda Store</h1>
    <input className="input" placeholder="Titolo" value={title} onChange={e=>setTitle(e.target.value)} />
    <input className="input" placeholder="Slug" value={slug} onChange={e=>setSlug(e.target.value)} />
    <input className="input" type="number" placeholder="Prezzo" value={price} onChange={e=>setPrice(parseFloat(e.target.value)||0)} />
    <button className="btn" onClick={submit as any}>Crea</button>
  </div></div></div>);
}
