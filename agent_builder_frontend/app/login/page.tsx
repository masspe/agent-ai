'use client';
import { useState } from 'react'; import { API_URL, setToken } from '../../lib/api'; import { useRouter } from 'next/navigation';
export default function LoginPage(){
  const [email,setEmail]=useState('admin@example.com'); const [password,setPassword]=useState('admin123');
  const [error,setError]=useState<string|null>(null); const [loading,setLoading]=useState(false); const router=useRouter();
  async function submit(e:React.FormEvent){ e.preventDefault(); setError(null); setLoading(true);
    try{ const body=new URLSearchParams({username:email,password,grant_type:'password'});
      const res=await fetch(`${API_URL}/auth/token`,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body});
      if(!res.ok) throw new Error(await res.text()); const data=await res.json(); setToken(data.access_token); router.push('/dashboard');
    }catch(err:any){ setError(err.message||'Login failed'); }finally{ setLoading(false); } }
  return (<div className="min-h-screen grid place-items-center"><form onSubmit={submit} className="card w-[380px]">
    <h1 className="text-2xl font-semibold mb-1">Accedi</h1><p className="text-sm text-gray-600 mb-4">Usa le credenziali admin seed.</p>
    <label className="block text-sm mb-1">Email</label><input className="input mb-3" value={email} onChange={e=>setEmail(e.target.value)} />
    <label className="block text-sm mb-1">Password</label><input type="password" className="input mb-4" value={password} onChange={e=>setPassword(e.target.value)} />
    {error && <div className="text-red-600 text-sm mb-2">{error}</div>}<button className="btn w-full" disabled={loading}>{loading?'...':'Login'}</button></form></div>);
}
