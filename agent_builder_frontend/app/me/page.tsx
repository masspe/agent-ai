'use client';
import Nav from '../../components/Nav';
import { useEffect, useState } from 'react';
import { apiFetch } from '../../lib/api';

type Me = { id:number; email:string; role:string; tenant_id?:number };

export default function MePage(){
  const [me,setMe]=useState<Me|null>(null);
  const [err,setErr]=useState<string|null>(null);
  const [newPass,setNewPass]=useState('');
  const [saving,setSaving]=useState(false);

  useEffect(()=>{ apiFetch('/me').then(setMe).catch(e=>setErr(String(e))); },[]);

  async function changePassword(e:React.FormEvent){ e.preventDefault(); if(!me) return; setSaving(true); setErr(null);
    try{ await apiFetch(`/users/${me.id}`, { method: 'PUT', body: JSON.stringify({ password: newPass }) }); setNewPass(''); alert('Password aggiornata'); }
    catch(e:any){ setErr(String(e)); } finally{ setSaving(false); } }

  return (<div>
    <Nav/>
    <div className="container py-6 grid gap-6">
      <h1 className="text-2xl font-semibold">Profilo</h1>
      {err && <div className="text-red-600">{err}</div>}
      {me ? (
        <div className="card grid gap-2 max-w-xl">
          <div><span className="text-sm text-gray-600">Email</span><div className="font-mono">{me.email}</div></div>
          <div><span className="text-sm text-gray-600">Ruolo</span><div className="">{me.role}</div></div>
          {me.tenant_id && <div><span className="text-sm text-gray-600">Tenant</span><div className="">{me.tenant_id}</div></div>}
        </div>
      ): <div>Caricamento…</div>}
      <div className="card grid gap-3 max-w-xl">
        <h2 className="font-semibold">Cambia password</h2>
        <form onSubmit={changePassword} className="grid grid-cols-4 gap-2">
          <input className="input col-span-3" type="password" placeholder="Nuova password" value={newPass} onChange={e=>setNewPass(e.target.value)} />
          <button className="btn" disabled={saving || !newPass}>Aggiorna</button>
        </form>
        <p className="text-xs text-gray-500">
  Nota: l'endpoint usato aggiorna la password utente corrente via{" "}
  <code>PUT /users/:id</code>.
</p>
        </div>
    </div>
  </div>);
}
