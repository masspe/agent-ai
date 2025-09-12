import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
export function middleware(req: NextRequest) {
  const url = req.nextUrl;
  const isAuth = url.pathname.startsWith('/login');
  const isApp = url.pathname === '/' || url.pathname.startsWith('/dashboard') || url.pathname.startsWith('/agents') || url.pathname.startsWith('/store') || url.pathname.startsWith('/users') || url.pathname.startsWith('/me');
  const token = req.cookies.get('token')?.value;
  if (isApp && !isAuth && !token) { url.pathname = '/login'; return NextResponse.redirect(url); }
  return NextResponse.next();
}
export const config = { matcher: ['/', '/dashboard/:path*', '/agents/:path*', '/store/:path*', '/users/:path*', '/me/:path*'] };
