'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { getSupabaseClient } from '@/lib/supabaseClient';

type Slot = {
  id: number;
  slot_number: string;
  is_active: boolean;
};

type ActiveBooking = {
  id: number;
  customer_name: string;
  vehicle_number: string;
  status: 'reserved' | 'completed' | 'cancelled';
  created_at: string;
  parking_slots: { slot_number: string }[] | null;
};

export default function MobileBookingPage() {
  const supabase = getSupabaseClient();
  const HOURLY_RATE = 1000;
  const [slots, setSlots] = useState<Slot[]>([]);
  const [userId, setUserId] = useState<string | null>(null);
  const [activeBooking, setActiveBooking] = useState<ActiveBooking | null>(null);
  const [customerName, setCustomerName] = useState('');
  const [vehicleNumber, setVehicleNumber] = useState('');
  const [hours, setHours] = useState(1);
  const [slotId, setSlotId] = useState<number | ''>('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const refreshCustomerDashboard = async () => {
    if (!supabase) {
      return;
    }

    const { data } = await supabase.auth.getUser();
    const currentUserId = data.user?.id ?? null;
    setUserId(currentUserId);

    const { data: slotRows } = (await supabase
      .from('parking_slots')
      .select('id,slot_number,is_active')
      .eq('is_active', true)
      .order('slot_number', { ascending: true })) as { data: Slot[] | null };

    const { data: reservedRows } = (await supabase
      .from('bookings')
      .select('slot_id')
      .eq('status', 'reserved')) as { data: { slot_id: number }[] | null };

    const reservedSlotIds = new Set((reservedRows ?? []).map((row) => row.slot_id));
    const availableSlots = (slotRows ?? []).filter((slot) => !reservedSlotIds.has(slot.id));
    setSlots(availableSlots);

    if (!currentUserId) {
      setActiveBooking(null);
      return;
    }

    const { data: existingBooking } = await supabase
      .from('bookings')
      .select('id,customer_name,vehicle_number,status,created_at,parking_slots(slot_number)')
      .eq('user_id', currentUserId)
      .eq('status', 'reserved')
      .order('created_at', { ascending: false })
      .limit(1)
      .maybeSingle();

    setActiveBooking((existingBooking as ActiveBooking | null) ?? null);
  };

  useEffect(() => {
    if (!supabase) {
      return;
    }

    refreshCustomerDashboard();
  }, [supabase]);

  const selectedSlotLabel = useMemo(() => {
    const match = slots.find((item) => item.id === slotId);
    return match?.slot_number ?? '';
  }, [slotId, slots]);

  const totalAmount = useMemo(() => hours * HOURLY_RATE, [hours]);

  const onBook = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setMessage('');

    if (!slotId) {
      setMessage('اختر الموقف أولاً');
      setLoading(false);
      return;
    }

    if (!userId) {
      setMessage('يرجى تسجيل دخول الزبون أولاً من صفحة /mobile/login');
      setLoading(false);
      return;
    }

    if (activeBooking) {
      setMessage('لديك موقف محجوز حالياً. لا يمكنك حجز أكثر من موقف واحد.');
      setLoading(false);
      return;
    }

    if (!supabase) {
      setMessage('يرجى إعداد متغيرات Supabase في ملف .env.local أولاً.');
      setLoading(false);
      return;
    }

    const bookingPayload: any = {
      customer_name: customerName,
      vehicle_number: vehicleNumber,
      slot_id: slotId,
      user_id: userId,
      status: 'reserved',
    };

    const { error } = await supabase.from('bookings').insert(bookingPayload);

    if (error) {
      setMessage(error.message);
      setLoading(false);
      return;
    }

    setMessage(`تم حجز الموقف ${selectedSlotLabel} بنجاح. عدد الساعات: ${hours}، المجموع: ${totalAmount} دينار`);
    setVehicleNumber('');
    setCustomerName('');
    setHours(1);
    setSlotId('');
    await refreshCustomerDashboard();
    setLoading(false);
  };

  const onCancelBooking = async () => {
    if (!supabase || !activeBooking || !userId) {
      return;
    }

    setLoading(true);
    setMessage('');

    const { error } = await (supabase
      .from('bookings') as any)
      .update({ status: 'cancelled' })
      .eq('id', activeBooking.id)
      .eq('user_id', userId);

    if (error) {
      setMessage(error.message);
      setLoading(false);
      return;
    }

    setMessage('تم إلغاء الحجز بنجاح');
    await refreshCustomerDashboard();
    setLoading(false);
  };

  return (
    <main className="container">
      <h1>حجز موقف من الموبايل</h1>
      <div className="card" style={{ maxWidth: 560 }}>
        {!supabase && <p>يرجى إعداد NEXT_PUBLIC_SUPABASE_URL و NEXT_PUBLIC_SUPABASE_ANON_KEY.</p>}
        {!userId && supabase && (
          <p>
            يرجى تسجيل الدخول كزبون أولاً من <Link href="/mobile/login">صفحة دخول الزبون</Link>.
          </p>
        )}
        {activeBooking && (
          <p>
            لديك حجز فعّال: موقف {activeBooking.parking_slots?.[0]?.slot_number ?? '-'} للسيارة{' '}
            {activeBooking.vehicle_number}. لا يمكنك حجز أكثر من موقف واحد.
          </p>
        )}
        <form className="grid" onSubmit={onBook}>
          <input
            value={customerName}
            onChange={(e) => setCustomerName(e.target.value)}
            placeholder="اسم العميل"
            required
          />
          <input
            value={vehicleNumber}
            onChange={(e) => setVehicleNumber(e.target.value)}
            placeholder="رقم السيارة"
            required
          />
          <input
            type="number"
            min={1}
            value={hours}
            onChange={(e) => setHours(Number(e.target.value) || 1)}
            placeholder="عدد الساعات"
            required
          />
          <p>سعر الساعة: {HOURLY_RATE} دينار</p>
          <p>المجموع: {totalAmount} دينار</p>
          <select value={slotId} onChange={(e) => setSlotId(Number(e.target.value))} required>
            <option value="">اختر الموقف</option>
            {slots.map((slot) => (
              <option key={slot.id} value={slot.id}>
                {slot.slot_number}
              </option>
            ))}
          </select>
          <button type="submit" disabled={loading || Boolean(activeBooking)}>
            {loading ? 'جاري الحجز...' : 'احجز الآن'}
          </button>
        </form>
        {activeBooking && (
          <button type="button" onClick={onCancelBooking} disabled={loading} style={{ marginTop: 12 }}>
            إلغاء الحجز
          </button>
        )}
        {message && <p>{message}</p>}
      </div>
    </main>
  );
}
