'use client';

import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getSupabaseClient } from '@/lib/supabaseClient';

export default function MobileLoginPage() {
  const router = useRouter();
  const supabase = getSupabaseClient();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const onLogin = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setMessage('');

    if (!supabase) {
      setMessage('يرجى إعداد متغيرات Supabase أولاً.');
      setLoading(false);
      return;
    }

    const { error } = await supabase.auth.signInWithPassword({ email, password });

    if (error) {
      setMessage(error.message);
      setLoading(false);
      return;
    }

    setMessage('تم تسجيل دخول الزبون بنجاح');
    setLoading(false);
    router.push('/mobile');
    router.refresh();
  };

  const onSignup = async () => {
    setLoading(true);
    setMessage('');

    if (!supabase) {
      setMessage('يرجى إعداد متغيرات Supabase أولاً.');
      setLoading(false);
      return;
    }

    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          full_name: fullName,
        },
      },
    });

    if (error) {
      setMessage(error.message);
      setLoading(false);
      return;
    }

    setMessage('تم إنشاء حساب الزبون. إذا طلب تأكيد بريد، أكمل التأكيد ثم سجّل الدخول.');
    setLoading(false);
  };

  return (
    <main className="container">
      <h1>دخول الزبون (الموبايل)</h1>
      <div className="card" style={{ maxWidth: 520 }}>
        <form className="grid" onSubmit={onLogin}>
          <input
            type="text"
            placeholder="الاسم الكامل (لإنشاء حساب جديد)"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />
          <input
            type="email"
            placeholder="البريد الإلكتروني"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="كلمة المرور"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button type="submit" disabled={loading}>
            {loading ? 'جاري المعالجة...' : 'دخول كزبون'}
          </button>
        </form>

        <button type="button" onClick={onSignup} disabled={loading} style={{ marginTop: 12 }}>
          إنشاء حساب زبون جديد
        </button>

        {message && <p style={{ marginTop: 12 }}>{message}</p>}
      </div>
    </main>
  );
}
