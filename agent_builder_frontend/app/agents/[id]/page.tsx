'use client';
import Nav from '../../../components/Nav';
import { useEffect, useMemo, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { apiFetch } from '../../../lib/api';

type Agent = { id:number; name:string; slug:string; description?:string; model?:string; visibility:'private'|'tenant'|'public'; timeout?:number|null; tags?:any };
type InputSet = { id:number; name:string; description?:string|null };
type Input = { id:number; key:string; label?:string|null; type:string; required:boolean; order_index:number; default_value?:string|null; };
type Variable = { id:number; key:string; value?:string|null; is_secret:boolean; as_json:boolean };
type Trigger = { id:number; kind:string; name?:string|null; description?:string|null; is_active:boolean; cron_expr?:string|null; run_at?:string|null; timezone?:string|null; event_config?:any };
type Action = { id:number; name:string; description?:string|null; kind:string; params_json?:any; order_index:number; is_enabled:boolean };
type Step = { id:number; step_index:number; name?:string|null; step_type:string; pseudocode?:string|null; params_json?:any; is_enabled:boolean };
type Advanced = { id:number; route_path?:string|null; shareable_enabled:boolean; share_token?:string|null; memory_strategy:string; memory_ttl_seconds?:number|null; cache_ttl_seconds?:number|null; tags?:any; extra?:any };

export default function AgentDetail(){
  const params = useParams<{ id:string }>(); const router = useRouter();
  const id = useMemo(()=> parseInt(String(params.id), 10), [params.id]);
  const [tab, setTab] = useState<'info'|'io'|'vars'|'triggers'|'actions'|'advanced'|'run'>('info');
  const [agent, setAgent] = useState<Agent|null>(null);
  const [error, setError] = useState<string|null>(null);
  const [saving, setSaving] = useState(false);

  // IO state
  const [sets, setSets] = useState<InputSet[]>([]);
  const [currentSet, setCurrentSet] = useState<number| null>(null);
  const [inputs, setInputs] = useState<Input[]>([]);
  // vars
  const [vars, setVars] = useState<Variable[]>([]);
  // triggers/actions/steps/advanced
  const [triggers, setTriggers] = useState<Trigger[]>([]);
  const [actions, setActions] = useState<Action[]>([]);
  const [steps, setSteps] = useState<Record<number, Step[]>>({});
  const [adv, setAdv] = useState<Advanced | null>(null);

  // run tab
  const [runSet, setRunSet] = useState<number | null>(null);
  const [runPayload, setRunPayload] = useState<string>('{\n  "inputs": {},\n  "variables": {},\n  "options": { "stream": false }\n}');
  const [runResult, setRunResult] = useState<string>('');

  // --- LOADERS ---------------------------------------------------
  useEffect(()=>{ 
    if(!id || Number.isNaN(id)) return; 
    apiFetch(`/agents/${id}`).then(setAgent).catch(e=>setError(String(e))); 
  },[id]);

  useEffect(()=>{ if(tab==='io' || tab==='run'){ refreshSets(); } },[tab]);

  useEffect(()=>{ 
    if(tab==='vars'){ 
      apiFetch(`/agent_variables?agent_id=${id}`)
        .then(setVars)
        .catch(e=>setError(String(e))); 
    } 
  },[tab, id]);

  useEffect(()=>{ 
    if(tab==='triggers'){ 
      apiFetch(`/agent_triggers?agent_id=${id}`)
        .then(setTriggers)
        .catch(e=>setError(String(e))); 
    } 
  },[tab, id]);

  useEffect(()=>{ 
    if(tab==='actions'){ 
      apiFetch(`/agent_actions?agent_id=${id}`)
        .then(setActions)
        .catch(e=>setError(String(e))); 
    } 
  },[tab, id]);

  useEffect(()=>{ 
    if(tab==='advanced'){ 
      apiFetch(`/agent_advanced?agent_id=${id}`)
        .then((rows:Advanced[])=> setAdv(rows?.[0] ?? null))
        .catch(()=>setAdv(null)); 
    } 
  },[tab, id]);

  async function refreshSets(){
    const rows:InputSet[] = await apiFetch(`/agent_input_sets?agent_id=${id}`);
    setSets(rows);
    if(rows.length && !currentSet){ setCurrentSet(rows[0].id); }
    if(rows.length && !runSet){ setRunSet(rows[0].id); }
  }

  useEffect(()=>{ 
    if(currentSet){ 
      apiFetch(`/agent_inputs?input_set_id=${currentSet}`)
        .then(setInputs)
        .catch(e=>setError(String(e))); 
    } else { 
      setInputs([]); 
    } 
  },[currentSet]);

  // --- SAVE / DELETE ---------------------------------------------
  async function saveAgent(e:React.FormEvent){
    e.preventDefault(); if(!agent) return; setSaving(true); setError(null);
    try{ 
      const payload:any={ 
        name: agent.name, slug: agent.slug, description: agent.description, 
        model: agent.model, visibility: agent.visibility, timeout: agent.timeout, tags: agent.tags 
      };
      const updated = await apiFetch(`/agents/${id}`, { method:'PUT', body: JSON.stringify(payload) }); 
      setAgent(updated);
    }catch(err:any){ 
      setError(err.message||'Errore salvataggio'); 
    } finally{ setSaving(false); }
  }

  async function deleteAgent(){ 
    if(!confirm('Confermi eliminazione?')) return; 
    try{ 
      await apiFetch(`/agents/${id}`, { method:'DELETE' }); 
      router.push('/agents'); 
    }catch(e:any){ setError(String(e)); } 
  }

  // --- IO handlers -----------------------------------------------
  async function createSet(name:string, description?:string){ 
    await apiFetch(`/agent_input_sets`, { method:'POST', body: JSON.stringify({ agent_id: id, name, description })});
    await refreshSets(); 
  }

  async function addInput(data:any){ 
    if(!currentSet) return; 
    await apiFetch(`/agent_inputs`, { method:'POST', body: JSON.stringify({ input_set_id: currentSet, ...data })});
    const rows:any = await apiFetch(`/agent_inputs?input_set_id=${currentSet}`); 
    setInputs(rows); 
  }

  // --- Vars handlers ---------------------------------------------
  async function upsertVar(key:string, value:string, is_secret:boolean, as_json:boolean){ 
    try{
      await apiFetch(`/agent_variables`, { method:'POST', body: JSON.stringify({ agent_id: id, key, value, is_secret, as_json })});
    }catch(_){
      // fallback: trova la variabile e fai PUT
      const existing:Variable[] = await apiFetch(`/agent_variables?agent_id=${id}`);
      const found = existing.find(v=>v.key===key);
      if(found){
        await apiFetch(`/agent_variables/${found.id}`, { method:'PUT', body: JSON.stringify({ value, is_secret, as_json })});
      }else{
        throw _;
      }
    }
    const rows:any = await apiFetch(`/agent_variables?agent_id=${id}`); 
    setVars(rows); 
  }

  // --- Triggers/actions ------------------------------------------
  async function addTrigger(t:any){ 
    await apiFetch(`/agent_triggers`, { method:'POST', body: JSON.stringify({ agent_id: id, ...t })});
    setTriggers(await apiFetch(`/agent_triggers?agent_id=${id}`)); 
  }

  async function delTrigger(trigger_id:number){ 
    await apiFetch(`/agent_triggers/${trigger_id}`, { method:'DELETE' }); 
    setTriggers(await apiFetch(`/agent_triggers?agent_id=${id}`)); 
  }

  async function addAction(a:any){ 
    await apiFetch(`/agent_actions`, { method:'POST', body: JSON.stringify({ agent_id: id, ...a })});
    setActions(await apiFetch(`/agent_actions?agent_id=${id}`)); 
  }

  async function loadSteps(action_id:number){ 
    const s:Step[] = await apiFetch(`/agent_action_steps?action_id=${action_id}`); 
    setSteps(prev=>({...prev, [action_id]: s})); 
  }

  async function addStep(action_id:number, s:any){ 
    await apiFetch(`/agent_action_steps`, { method:'POST', body: JSON.stringify({ action_id, ...s })});
    await loadSteps(action_id); 
  }

  // --- Advanced ---------------------------------------------------
  async function upsertAdvanced(a:any){ 
    // se esiste un record advanced, PUT su /agent_advanced/{id}, altrimenti POST su /agent_advanced
    let current:Advanced | null = adv;
    if(!current){
      const created = await apiFetch(`/agent_advanced`, { method:'POST', body: JSON.stringify({ agent_id: id, ...a })});
      setAdv(created);
      return;
    }
    const updated = await apiFetch(`/agent_advanced/${(current as any).id}`, { method:'PUT', body: JSON.stringify(a)});
    setAdv(updated); 
  }

  // --- Run --------------------------------------------------------
  async function runAgent(){
    setRunResult('');
    try{
      const body = JSON.parse(runPayload || '{}');
      let result;
      // prova endpoint per id (se disponibile nel backend)
      try{
        result = await apiFetch(`/agents/${id}/run`, { method:'POST', body: JSON.stringify({ input_set_id: runSet, ...body }) });
      }catch(_){
        // fallback a endpoint per slug se configurato
        if(agent?.slug){
          result = await apiFetch(`/v1/agents/${agent.slug}/run`, { method:'POST', body: JSON.stringify(body) });
        }else{ throw _; }
      }
      setRunResult(typeof result === 'string' ? result : JSON.stringify(result, null, 2));
    }catch(err:any){
      setRunResult(`Errore: ${err.message}`);
    }
  }

  return (<div>
    <Nav/>
    <div className="container py-6 grid gap-6">
      {!agent && !error && <div>Caricamento…</div>}
      {error && <div className="text-red-600">{error}</div>}
      {agent && (<div className="grid gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold">{agent.name}</h1>
              <div className="text-sm text-gray-600">{agent.slug} <span className="badge ml-2">{agent.visibility}</span></div>
            </div>
            <button onClick={deleteAgent} className="btn">Elimina</button>
          </div>
          <div className="mt-4 flex gap-2">
            {['info','io','vars','triggers','actions','advanced','run'].map(t=>(
              <button key={t} className={`tab ${tab===t?'tab-active':''}`} onClick={()=>setTab(t as any)}>{t}</button>
            ))}
          </div>
        </div>

        {tab==='info' && (<div className="card">
          <form onSubmit={saveAgent} className="grid gap-4">
            <div className="grid grid-cols-2 gap-4">
              <div><label className="block text-sm mb-1">Nome</label><input className="input" value={agent.name} onChange={e=>setAgent({...agent, name:e.target.value})}/></div>
              <div><label className="block text-sm mb-1">Slug</label><input className="input" value={agent.slug} onChange={e=>setAgent({...agent, slug:e.target.value})}/></div>
            </div>
            <div><label className="block text-sm mb-1">Descrizione</label><textarea className="input" rows={4} value={agent.description||''} onChange={e=>setAgent({...agent, description:e.target.value})}/></div>
            <div className="grid grid-cols-3 gap-4">
              <div><label className="block text-sm mb-1">Model</label><input className="input" value={agent.model||''} onChange={e=>setAgent({...agent, model:e.target.value})}/></div>
              <div><label className="block text-sm mb-1">Visibilità</label>
                <select className="input" value={agent.visibility} onChange={e=>setAgent({...agent, visibility: e.target.value as any})}>
                  <option value="private">private</option><option value="tenant">tenant</option><option value="public">public</option>
                </select></div>
              <div><label className="block text-sm mb-1">Timeout (s)</label><input type="number" className="input" value={agent.timeout||0} onChange={e=>setAgent({...agent, timeout: parseInt(e.target.value,10)})}/></div>
            </div>
            <div className="flex gap-2"><button className="btn" disabled={saving}>{saving?'Salvataggio…':'Salva'}</button></div>
          </form>
        </div>)}

        {tab==='io' && (<div className="card grid gap-6">
          <div>
            <h3 className="font-semibold mb-2">Input Sets</h3>
            <div className="flex gap-2 mb-3">{sets.map(s=>(<button key={s.id} className={`tab ${currentSet===s.id?'tab-active':''}`} onClick={()=>setCurrentSet(s.id)}>{s.name}</button>))}</div>
            <NewSetForm onCreate={createSet}/>
          </div>
          <div>
            <h3 className="font-semibold mb-2">Inputs {currentSet? `(#${currentSet})`: ''}</h3>
            {currentSet ? (
              <div className="grid gap-3">
                {inputs.map(i=>(
                  <div key={i.id} className="border rounded-xl p-3">
                    <div className="font-mono text-sm">{i.key} <span className="badge">{i.type}</span> {i.required && <span className="badge ml-1">required</span>}</div>
                    {i.label && <div className="text-gray-700">{i.label}</div>}
                  </div>
                ))}
                <NewInputForm onCreate={addInput}/>
              </div>
            ) : <div className="text-gray-600">Crea o seleziona un set.</div>}
          </div>
        </div>)}

        {tab==='vars' && (<div className="card grid gap-4">
          <div className="grid gap-2">{vars.map(v=>(<div key={v.id} className="border rounded-xl p-3">
            <div className="font-mono text-sm">{v.key} {v.is_secret && <span className="badge">secret</span>} {v.as_json && <span className="badge ml-1">json</span>}</div>
            {v.value && <pre className="text-xs mt-1 overflow-auto">{v.value}</pre>}
          </div>))}</div>
          <NewVarForm onCreate={upsertVar}/>
        </div>)}

        {tab==='triggers' && (<div className="card grid gap-4">
          <div className="grid gap-2">{triggers.map(t=>(<div key={t.id} className="border rounded-xl p-3">
            <div className="flex items-center justify-between">
              <div><span className="badge">{t.kind}</span> {t.name || ''} {t.is_active? <span className="badge ml-2">active</span>:<span className="badge ml-2">off</span>}</div>
              <button className="btn" onClick={()=>delTrigger(t.id)}>Elimina</button>
            </div>
            {t.cron_expr && <div className="text-sm text-gray-600">cron: {t.cron_expr}</div>}
            {t.run_at && <div className="text-sm text-gray-600">run_at: {t.run_at}</div>}
          </div>))}</div>
          <NewTriggerForm onCreate={addTrigger}/>
        </div>)}

        {tab==='actions' && (<div className="card grid gap-6">
          <div className="grid gap-2">{actions.map(a=>(<div key={a.id} className="border rounded-xl p-3">
            <div className="flex items-center justify-between"><div>
              <div className="font-semibold">{a.name} <span className="badge ml-1">{a.kind}</span></div>
              {a.description && <div className="text-gray-700">{a.description}</div>}</div>
              <button className="btn" onClick={()=>loadSteps(a.id)}>Ricarica steps</button>
            </div>
            <div className="mt-2 grid gap-2">{(steps[a.id]||[]).map(s=>(<div key={s.id} className="border rounded-xl p-2">
              <div className="text-sm">#{s.step_index} <span className="badge ml-1">{s.step_type}</span> {s.name||''}</div>
              {s.pseudocode && <pre className="text-xs mt-1 overflow-auto">{s.pseudocode}</pre>}
            </div>))}</div>
            <NewStepForm onCreate={(payload)=>addStep(a.id, payload)} />
          </div>))}</div>
          <NewActionForm onCreate={addAction}/>
        </div>)}

        {tab==='advanced' && (<div className="card">
          <AdvancedForm data={adv} onSave={upsertAdvanced} />
        </div>)}

        {tab==='run' && (<div className="card grid gap-4">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm mb-1">Input set</label>
              <select className="input" value={runSet || ''} onChange={e=>setRunSet(parseInt(e.target.value,10)||null)}>
                {sets.map(s=>(<option key={s.id} value={s.id}>{s.name}</option>))}
              </select>
            </div>
          </div>
          <div>
            <label className="block text-sm mb-1">Payload (JSON)</label>
            <textarea className="textarea" rows={10} value={runPayload} onChange={e=>setRunPayload(e.target.value)} />
          </div>
          <div className="flex gap-2"><button className="btn" onClick={runAgent}>Esegui</button></div>
          {runResult && (<div><label className="block text-sm mb-1">Risultato</label><pre className="text-xs overflow-auto">{runResult}</pre></div>)}
        </div>)}

      </div>)}
    </div>
  </div>);
}

function NewSetForm({onCreate}:{onCreate:(name:string, description?:string)=>Promise<any>}){
  const [name,setName]=useState('Default'); const [description,setDescription]=useState('');
  return (<form onSubmit={async e=>{e.preventDefault(); await onCreate(name, description||undefined);}} className="flex gap-2">
    <input className="input" placeholder="Nome set" value={name} onChange={e=>setName(e.target.value)} />
    <input className="input" placeholder="Descrizione (opz.)" value={description} onChange={e=>setDescription(e.target.value)} />
    <button className="btn">Crea set</button>
  </form>);
}

function NewInputForm({onCreate}:{onCreate:(data:any)=>Promise<any>}){
  const [key,setKey]=useState('input'); const [label,setLabel]=useState(''); const [type,setType]=useState('text');
  const [required,setRequired]=useState(false); const [order,setOrder]=useState(0);
  return (<form onSubmit={async e=>{e.preventDefault(); await onCreate({ key, label: label||undefined, type, required, order_index: order }); }} className="grid grid-cols-5 gap-2">
    <input className="input" placeholder="key" value={key} onChange={e=>setKey(e.target.value)} />
    <input className="input" placeholder="label" value={label} onChange={e=>setLabel(e.target.value)} />
    <select className="input" value={type} onChange={e=>setType(e.target.value)}>
      {['text','number','boolean','enum','json','file','apikey','document','variable'].map(t=>(<option key={t} value={t}>{t}</option>))}
    </select>
    <label className="flex items-center gap-2"><input type="checkbox" checked={required} onChange={e=>setRequired(e.target.checked)} /> required</label>
    <div className="flex gap-2"><input type="number" className="input" value={order} onChange={e=>setOrder(parseInt(e.target.value,10))} /><button className="btn">Aggiungi</button></div>
  </form>);
}

function NewVarForm({onCreate}:{onCreate:(key:string,value:string,is_secret:boolean,as_json:boolean)=>Promise<any>}){
  const [key,setKey]=useState('API_KEY'); const [value,setValue]=useState(''); const [secret,setSecret]=useState(true); const [asJson,setAsJson]=useState(false);
  return (<form onSubmit={async e=>{e.preventDefault(); await onCreate(key, value, secret, asJson);}} className="grid grid-cols-4 gap-2">
    <input className="input" placeholder="KEY" value={key} onChange={e=>setKey(e.target.value)} />
    <input className="input" placeholder="value" value={value} onChange={e=>setValue(e.target.value)} />
    <label className="flex items-center gap-2"><input type="checkbox" checked={secret} onChange={e=>setSecret(e.target.checked)} /> secret</label>
    <div className="flex items-center gap-2"><label className="flex items-center gap-2"><input type="checkbox" checked={asJson} onChange={e=>setAsJson(e.target.checked)} /> json</label><button className="btn">Salva</button></div>
  </form>);
}

function NewTriggerForm({onCreate}:{onCreate:(t:any)=>Promise<any>}){
  const [kind,setKind]=useState('manual'); const [name,setName]=useState(''); const [cron,setCron]=useState(''); const [runAt,setRunAt]=useState('');
  const [tz,setTz]=useState('Europe/Rome'); const [active,setActive]=useState(true);
  return (<form onSubmit={async e=>{e.preventDefault(); await onCreate({ kind, name: name||undefined, is_active: active, cron_expr: cron||undefined, run_at: runAt||undefined, timezone: tz||undefined }); }} className="grid grid-cols-6 gap-2">
    <select className="input" value={kind} onChange={e=>setKind(e.target.value)}>
      {['manual','schedule','one_time','webhook','email','sms','file_update','google_doc','onedrive','whatsapp'].map(k=>(<option key={k} value={k}>{k}</option>))}
    </select>
    <input className="input" placeholder="name" value={name} onChange={e=>setName(e.target.value)} />
    <input className="input" placeholder="cron (es. */5 * * * *)" value={cron} onChange={e=>setCron(e.target.value)} />
    <input className="input" placeholder="run_at (ISO)" value={runAt} onChange={e=>setRunAt(e.target.value)} />
    <input className="input" placeholder="timezone" value={tz} onChange={e=>setTz(e.target.value)} />
    <label className="flex items-center gap-2"><input type="checkbox" checked={active} onChange={e=>setActive(e.target.checked)} /> attivo</label>
    <div className="col-span-6"><button className="btn">Aggiungi trigger</button></div>
  </form>);
}

function NewActionForm({onCreate}:{onCreate:(a:any)=>Promise<any>}){
  const [name,setName]=useState('Step 1'); const [kind,setKind]=useState('custom'); const [desc,setDesc]=useState(''); const [order,setOrder]=useState(0);
  return (<form onSubmit={async e=>{e.preventDefault(); await onCreate({ name, kind, description: desc||undefined, order_index: order });}} className="grid grid-cols-4 gap-2">
    <input className="input" placeholder="name" value={name} onChange={e=>setName(e.target.value)} />
    <select className="input" value={kind} onChange={e=>setKind(e.target.value)}>
      {['tool','llm_call','webhook_call','python','rag','email_send','custom'].map(k=>(<option key={k} value={k}>{k}</option>))}
    </select>
    <input className="input" placeholder="description" value={desc} onChange={e=>setDesc(e.target.value)} />
    <div className="flex gap-2"><input type="number" className="input" value={order} onChange={e=>setOrder(parseInt(e.target.value,10)||0)} /><button className="btn">Aggiungi azione</button></div>
  </form>);
}

function AdvancedForm({data,onSave}:{data:Advanced|null,onSave:(a:any)=>Promise<any>}){
  const [route,setRoute]=useState(data?.route_path||''); const [share,setShare]=useState(!!data?.shareable_enabled); const [token,setToken]=useState(data?.share_token||'');
  const [mem,setMem]=useState(data?.memory_strategy||'none'); const [memTtl,setMemTtl]=useState<number>(data?.memory_ttl_seconds||0);
  const [cacheTtl,setCacheTtl]=useState<number>(data?.cache_ttl_seconds||0);
  useEffect(()=>{ setRoute(data?.route_path||''); setShare(!!data?.shareable_enabled); setToken(data?.share_token||''); setMem(data?.memory_strategy||'none'); setMemTtl(data?.memory_ttl_seconds||0); setCacheTtl(data?.cache_ttl_seconds||0); },[data]);
  return (<form onSubmit={async e=>{e.preventDefault(); await onSave({ route_path: route||undefined, shareable_enabled: share, share_token: token||undefined, memory_strategy: mem, memory_ttl_seconds: memTtl||undefined, cache_ttl_seconds: cacheTtl||undefined }); }} className="grid gap-4">
    <div className="grid grid-cols-3 gap-4">
      <div><label className="block text-sm mb-1">Route path</label><input className="input" value={route} onChange={e=>setRoute(e.target.value)} /></div>
      <div><label className="block text-sm mb-1">Shareable</label><label className="flex items-center gap-2 mt-2"><input type="checkbox" checked={share} onChange={e=>setShare(e.target.checked)} /> abilitato</label></div>
      <div><label className="block text-sm mb-1">Share token</label><input className="input" value={token} onChange={e=>setToken(e.target.value)} /></div>
    </div>
    <div className="grid grid-cols-3 gap-4">
      <div><label className="block text-sm mb-1">Memory</label>
        <select className="input" value={mem} onChange={e=>setMem(e.target.value)}>
          <option value="none">none</option><option value="buffer">buffer</option><option value="vector">vector</option>
        </select></div>
      <div><label className="block text-sm mb-1">Memory TTL (s)</label><input type="number" className="input" value={memTtl} onChange={e=>setMemTtl(parseInt(e.target.value,10)||0)} /></div>
      <div><label className="block text-sm mb-1">Cache TTL (s)</label><input type="number" className="input" value={cacheTtl} onChange={e=>setCacheTtl(parseInt(e.target.value,10)||0)} /></div>
    </div>
    <div><button className="btn">Salva Advanced</button></div>
  </form>);
}
