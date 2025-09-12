'use client';
import Link from 'next/link'; import { usePathname, useRouter } from 'next/navigation';
export default function Nav(){
  const pathname = usePathname(); const router = useRouter();
  const logout = ()=>{ localStorage.removeItem('token'); document.cookie='token=; Max-Age=0; path=/'; router.push('/login'); };
  const link = (href:string, text:string)=>(<Link href={href} className={`px-3 py-2 rounded-xl ${pathname?.startsWith(href)?'bg-gray-200':''}`}>{text}</Link>);
  return (<div className="w-full border-b bg-white sticky top-0 z-20"><div className="container flex items-center gap-4 h-14">
    <Link href="/dashboard" className="font-semibold">Agent Builder</Link>
    <div className="flex gap-2 ml-4">{link('/dashboard','Dashboard')}{link('/agents','Agents')}{link('/agents/wizard','Wizard')}{link('/store','Store')}{link('/users','Utenti')}{link('/me','Profilo')}</div>
    <div className="ml-auto"><button onClick={logout} className="btn">Logout</button></div></div></div>);
}
