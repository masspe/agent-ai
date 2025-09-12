'use client';
import Nav from '../../components/Nav';
import { useEffect, useState } from 'react';
import { apiFetch } from '../../lib/api';

type User = { id:number; email:string; role:string; is_active:boolean; tenant_id?:number };

export default function UsersPage(){
  const [rows,setRows]=useState<User[]>([]);
  const [error,setError]=useState<string|null>(null);
  const [loading,setLoading]=useState(true);
  // create
  const [email,setEmail]=useState(''); const [password,setPassword]=useState(''); const [role,setRole]=useState('admin'); const [active,setActive]=useState(true);

  async function load(){ setLoading(true); setError(null);
    try{ const data = await apiFetch('/users'); setRows(data); } catch(e:any){ setError(String(e)); } finally{ setLoading(false); } }
  useEffect(()=>{ load(); },[]);

  async function create(e:React.FormEvent){ e.preventDefault(); setError(null);
    try{ await apiFetch('/users', { method:'POST', body: JSON.stringify({ email, password, role, is_active: active })}); setEmail(''); setPassword(''); setRole('admin'); setActive(true); await load(); }
    catch(e:any){ setError(String(e)); } }

  async function toggleActive(u:User){ try{ await apiFetch(`/users/${u.id}`, { method:'PUT', body: JSON.stringify({ is_active: !u.is_active })}); await load(); } catch(e:any){ setError(String(e)); } }
  async function changeRole(u:User, newRole:string){ try{ await apiFetch(`/users/${u.id}`, { method:'PUT', body: JSON.stringify({ role: newRole })}); await load(); } catch(e:any){ setError(String(e)); } }
  async function del(u:User){ if(!confirm(`Eliminare ${u.email}?`)) return; try{ await apiFetch(`/users/${u.id}`, { method:'DELETE' }); await load(); } catch(e:any){ setError(String(e)); } }

  return (<div>
    <Nav/>
    <div className="container py-6 grid gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Utenti</h1>
      </div>
      {error && <div className="text-red-600">{error}</div>}
      <div className="card grid gap-3">
        <h2 className="font-semibold">Crea nuovo</h2>
        <form onSubmit={create} className="grid grid-cols-5 gap-2">
          <input className="input" placeholder="email" value={email} onChange={e=>setEmail(e.target.value)} />
          <input type="password" className="input" placeholder="password" value={password} onChange={e=>setPassword(e.target.value)} />
          <select className="input" value={role} onChange={e=>setRole(e.target.value)}>
            <option value="admin">admin</option>
            <option value="user">user</option>
          </select>
          <label className="flex items-center gap-2"><input type="checkbox" checked={active} onChange={e=>setActive(e.target.checked)} /> attivo</label>
          <button className="btn">Crea</button>
        </form>
      </div>
      <div className="card">
        <h2 className="font-semibold mb-2">Elenco</h2>
        {loading? <div>Caricamento…</div> : (
          <div className="grid gap-2">
            {rows.map(u=>(
              <div key={u.id} className="border rounded-xl p-3 flex items-center justify-between">
                <div>
                  <div className="font-mono">{u.email}</div>
                  <div className="text-sm text-gray-600">role: {u.role} {u.is_active? '• active':'• disabled'}</div>
                </div>
                <div className="flex gap-2">
                  <select className="input" value={u.role} onChange={e=>changeRole(u, e.target.value)}>
                    <option value="admin">admin</option>
                    <option value="user">user</option>
                  </select>
                  <button className="btn" onClick={()=>toggleActive(u)}>{u.is_active? 'Disattiva':'Attiva'}</button>
                  <button className="btn" onClick={()=>del(u)}>Elimina</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  </div>);
}
