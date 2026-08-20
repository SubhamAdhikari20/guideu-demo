import { MountainSnow, ShieldCheck } from 'lucide-react';
import { redirect } from 'next/navigation';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { currentAdmin } from '@/lib/auth';
import { loginAction } from './actions';

export const dynamic = 'force-dynamic';

export default async function LoginPage({ searchParams }: { searchParams: Promise<{ error?: string }> }) {
  if (await currentAdmin()) redirect('/dashboard');
  const { error } = await searchParams;
  return (
    <main className="from-primary/10 via-background to-amber-500/10 flex min-h-screen items-center justify-center bg-gradient-to-br p-6">
      <Card className="w-full max-w-md shadow-xl">
        <CardHeader className="text-center">
          <div className="bg-primary text-primary-foreground mx-auto mb-3 flex size-12 items-center justify-center rounded-xl"><MountainSnow /></div>
          <CardTitle className="text-2xl">GuideU Administration</CardTitle>
          <CardDescription>Sign in with an administrator account to manage the tourism platform.</CardDescription>
        </CardHeader>
        <CardContent>
          {error && <p role="alert" className="bg-destructive/10 text-destructive mb-4 rounded-md p-3 text-sm">{error}</p>}
          <form action={loginAction} className="space-y-4">
            <div className="space-y-2"><Label htmlFor="email">Email</Label><Input id="email" name="email" type="email" autoComplete="username" required /></div>
            <div className="space-y-2"><Label htmlFor="password">Password</Label><Input id="password" name="password" type="password" autoComplete="current-password" required /></div>
            <Button type="submit" className="w-full"><ShieldCheck className="size-4" /> Secure sign in</Button>
          </form>
          <p className="text-muted-foreground mt-5 text-center text-xs">Tourist and guide accounts are rejected at the server boundary.</p>
        </CardContent>
      </Card>
    </main>
  );
}
