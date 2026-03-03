'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getSupabaseClient } from '@/lib/supabaseClient';

type Booking = {
  id: number;
  customer_name: string;
  vehicle_number: string;
  status: 'reserved' | 'completed' | 'cancelled';
  created_at: string;
  parking_slots: { slot_number: string }[] | null;
};

export default function AdminPage() {
  const supabase = getSupabaseClient();
  const router = useRouter();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState('');

  const loadBookings = async () => {
    if (!supabase) {
      return;
    }

    const { data, error } = await supabase
      .from('bookings')
      .select('id,customer_name,vehicle_number,status,created_at,parking_slots(slot_number)')
      .order('created_at', { ascending: false });

    if (!error && data) {
      setBookings(data as Booking[]);
    }
  };

  useEffect(() => {
    if (!supabase) {
      setAuthError('يرجى إعداد متغيرات Supabase في ملف .env.local أولاً.');
      setLoading(false);
      return;
    }

    let isMounted = true;
    let channel: ReturnType<typeof supabase.channel> | null = null;

    const init = async () => {
      const { data: authData } = await supabase.auth.getUser();
      const user = authData.user;

      if (!user) {
        if (isMounted) {
          setAuthError('هذه الصفحة للمشرف فقط. يرجى تسجيل الدخول.');
          setLoading(false);
        }
        return;
      }

      const { data: profile } = (await supabase
        .from('profiles')
        .select('role')
        .eq('id', user.id)
        .single()) as { data: { role: string } | null };

      if (!profile || profile.role !== 'admin') {
        if (isMounted) {
          setAuthError('ليس لديك صلاحية مشرف.');
          setLoading(false);
        }
        return;
      }

      await loadBookings();
      if (isMounted) {
        setLoading(false);
      }

      channel = supabase
        .channel('bookings-realtime')
        .on('postgres_changes', { event: '*', schema: 'public', table: 'bookings' }, async () => {
          await loadBookings();
        })
        .subscribe();
    };

    init();

    return () => {
      isMounted = false;
      if (channel) {
        supabase.removeChannel(channel);
      }
    };
  }, [supabase]);

  const stats = useMemo(() => {
    const reserved = bookings.filter((b) => b.status === 'reserved').length;
    const completed = bookings.filter((b) => b.status === 'completed').length;
    return { total: bookings.length, reserved, completed };
  }, [bookings]);

  const signOut = async () => {
    if (!supabase) {
      return;
    }

    await supabase.auth.signOut();
    router.push('/login');
  };

  if (loading) {
    return (
      <main className="container">
        <p>جاري تحميل بيانات المشرف...</p>
      </main>
    );
  }

  if (authError) {
    return (
      <main className="container">
        <div className="card" style={{ maxWidth: 560 }}>
          <h1>وصول مرفوض</h1>
          <p>{authError}</p>
        </div>
      </main>
    );
  }

  return (
    <main className="container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>لوحة المشرف - الحجوزات</h1>
        <button onClick={signOut} style={{ width: 'auto', paddingInline: 16 }}>
          تسجيل خروج
        </button>
      </div>

      <section className="grid grid-2" style={{ marginBottom: 12 }}>
        <div className="card">
          <h3>إجمالي الحجوزات</h3>
          <p>{stats.total}</p>
        </div>
        <div className="card">
          <h3>حجوزات محجوزة الآن</h3>
          <p>{stats.reserved}</p>
        </div>
        <div className="card">
          <h3>حجوزات مكتملة</h3>
          <p>{stats.completed}</p>
        </div>
      </section>

      <div className="card">
        <table className="table">
          <thead>
            <tr>
              <th>الوقت</th>
              <th>العميل</th>
              <th>السيارة</th>
              <th>الموقف</th>
              <th>الحالة</th>
            </tr>
          </thead>
          <tbody>
            {bookings.map((booking) => (
              <tr key={booking.id}>
                <td>{new Date(booking.created_at).toLocaleString('ar-EG')}</td>
                <td>{booking.customer_name}</td>
                <td>{booking.vehicle_number}</td>
                <td>{booking.parking_slots?.[0]?.slot_number ?? '-'}</td>
                <td>
                  <span className={`badge ${booking.status}`}>{booking.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}
