'use client';
import Nav from '../../../components/Nav'; import { useParams, useRouter } from 'next/navigation'; import { useEffect, useMemo, useState } from 'react'; import { apiFetch } from '../../../lib/api';
type Listing={id:number; title:string; slug:string; price_cents:number; currency:string; visibility:string; is_published:boolean; short_subtitle?:string|null; description_md?:string|null;};
export default function StoreEdit(){
  const params = useParams<{id:string}>(); const router=useRouter(); const id = useMemo(()=>parseInt(String(params.id),10),[params.id]);
  const [data,setData]=useState<Listing|null>(null); const [err,setErr]=useState<string|null>(null); const [saving,setSaving]=useState(false);
  useEffect(()=>{ if(!id) return; apiFetch(`/store_listings/${id}`).then(setData).catch(e=>setErr(String(e))); },[id]);
  async function save(e:React.FormEvent){ e.preventDefault(); if(!data) return; setSaving(true);
    try{ const updated = await apiFetch(`/store_listings/${id}`, { method:'PUT', body: JSON.stringify(data) }); setData(updated); }
    catch(e:any){ setErr(String(e)); } finally{ setSaving(false); } }
  async function del(){ if(!confirm('Eliminare la scheda?')) return; try{ await apiFetch(`/store_listings/${id}`, { method:'DELETE' }); router.push('/store'); }catch(e:any){ setErr(String(e)); } }
  return (<div><Nav/><div className="container py-6">{!data && !err && <div>Caricamento…</div>}{err && <div className="text-red-600">{err}</div>}{data && (
    <div className="card grid gap-3"><h1 className="text-2xl font-semibold">Modifica Scheda</h1>
      <form onSubmit={save} className="grid gap-3">
        <input className="input" value={data.title} onChange={e=>setData({...data, title:e.target.value})} />
        <input className="input" value={data.slug||''} onChange={e=>setData({...data, slug:e.target.value})} />
        <textarea className="textarea" rows={6} value={data.description_md||''} onChange={e=>setData({...data, description_md:e.target.value})} />
        <label className="flex items-center gap-2"><input type="checkbox" checked={data.is_published} onChange={e=>setData({...data, is_published:e.target.checked})} /> pubblicato</label>
        <div className="flex gap-2"><button className="btn" disabled={saving}>{saving?'Salvataggio…':'Salva'}</button><button type="button" onClick={del} className="btn">Elimina</button></div>
      </form>
    </div>
  )}</div></div>);
}
