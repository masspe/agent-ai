'use client';
import Nav from '../../../components/Nav'; import { useRouter } from 'next/navigation'; import { useState } from 'react'; import { apiFetch } from '../../../lib/api';
export default function NewAgentPage(){
  const router=useRouter(); const [name,setName]=useState(''); const [slug,setSlug]=useState(''); const [description,setDescription]=useState('');
  const [model,setModel]=useState('gpt-4o-mini'); const [visibility,setVisibility]=useState<'private'|'tenant'|'public'>('private');
  const [loading,setLoading]=useState(false); const [error,setError]=useState<string|null>(null);
  async function submit(e:React.FormEvent){ e.preventDefault(); setError(null); if(!name.trim()){setError('Nome obbligatorio'); return;} setLoading(true);
    try{ const payload:any={name,visibility,model}; if(description) payload.description=description; if(slug.trim()) payload.slug=slug.trim();
      const created=await apiFetch('/agents',{method:'POST',body:JSON.stringify(payload)}); router.push(`/agents/${created.id}`);
    }catch(err:any){ setError(err.message||'Errore creazione agent'); }finally{ setLoading(false); } }
  return (<div><Nav/><div className="container py-6"><div className="card max-w-2xl"><h1 className="text-2xl font-semibold mb-4">Nuovo Agent</h1>
    <form onSubmit={submit} className="grid gap-4">
      <div><label className="block text-sm mb-1">Nome *</label><input className="input" value={name} onChange={e=>setName(e.target.value)} /></div>
      <div><label className="block text-sm mb-1">Slug (opz.)</label><input className="input" value={slug} onChange={e=>setSlug(e.target.value)} /></div>
      <div><label className="block text-sm mb-1">Descrizione</label><textarea className="input" rows={4} value={description} onChange={e=>setDescription(e.target.value)} /></div>
      <div className="grid grid-cols-2 gap-4">
        <div><label className="block text-sm mb-1">Model</label><input className="input" value={model} onChange={e=>setModel(e.target.value)} /></div>
        <div><label className="block text-sm mb-1">Visibilità</label><select className="input" value={visibility} onChange={e=>setVisibility(e.target.value as any)}>
          <option value="private">private</option><option value="tenant">tenant</option><option value="public">public</option></select></div></div>
      {error && <div className="text-red-600 text-sm">{error}</div>}
      <div className="flex gap-2"><button className="btn" disabled={loading}>{loading?'Creazione…':'Crea agent'}</button></div>
    </form></div></div></div>);
}
