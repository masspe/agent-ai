'use client';
import Nav from '../../../components/Nav'; import { useState } from 'react'; import { useRouter } from 'next/navigation'; import { apiFetch } from '../../../lib/api';
export default function Wizard(){
  const router=useRouter();
  const [name,setName]=useState(''); const [model,setModel]=useState('gpt-4o-mini'); const [vis,setVis]=useState<'private'|'tenant'|'public'>('private');
  const [inputs,setInputs]=useState<any[]>([{key:'input',type:'text',required:false,label:''}]);
  async function create(){ const agent=await apiFetch('/agents',{method:'POST',body:JSON.stringify({name,model,visibility:vis})});
    const setrow=await apiFetch(`/agents/${agent.id}/agent_input_sets`,{method:'POST',body:JSON.stringify({name:'Default'})});
    for(let i=0;i<inputs.length;i++){await apiFetch(`/agents/agent_input_sets/${setrow.id}/inputs`,{method:'POST',body:JSON.stringify({...inputs[i],order_index:i})});}
    router.push(`/agents/${agent.id}`); }
  return (<div><Nav/><div className="container py-6 grid gap-3">
    <div className="card grid gap-3"><h1 className="text-2xl font-semibold">Wizard rapido</h1>
      <input className="input" placeholder="Nome agent" value={name} onChange={e=>setName(e.target.value)} />
      <input className="input" placeholder="Model" value={model} onChange={e=>setModel(e.target.value)} />
      <select className="input" value={vis} onChange={e=>setVis(e.target.value as any)}><option value="private">private</option><option value="tenant">tenant</option><option value="public">public</option></select>
      <div className="grid gap-2">{inputs.map((i,idx)=>(<div key={idx} className="border rounded-xl p-2 grid grid-cols-4 gap-2">
        <input className="input" placeholder="key" value={i.key} onChange={e=>{const a=[...inputs];a[idx].key=e.target.value;setInputs(a);}} />
        <input className="input" placeholder="label" value={i.label} onChange={e=>{const a=[...inputs];a[idx].label=e.target.value;setInputs(a);}} />
        <select className="input" value={i.type} onChange={e=>{const a=[...inputs];a[idx].type=e.target.value;setInputs(a);}}>
          {['text','number','boolean','enum','json','file','apikey','document','variable'].map(t=>(<option key={t} value={t}>{t}</option>))}
        </select>
        <label className="flex items-center gap-2"><input type="checkbox" checked={i.required} onChange={e=>{const a=[...inputs];a[idx].required=e.target.checked;setInputs(a);}}/> required</label>
      </div>))}</div>
      <button className="btn" onClick={()=>setInputs([...inputs,{key:'field',type:'text',required:false,label:''}])}>Aggiungi input</button>
      <div><button className="btn" onClick={create}>Crea</button></div>
    </div></div></div>);
}
