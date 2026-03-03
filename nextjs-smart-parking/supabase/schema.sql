create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text,
  role text not null default 'customer' check (role in ('admin', 'customer')),
  created_at timestamptz not null default now()
);

create table if not exists public.parking_slots (
  id bigserial primary key,
  slot_number text not null unique,
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists public.bookings (
  id bigserial primary key,
  customer_name text not null,
  vehicle_number text not null,
  slot_id bigint not null references public.parking_slots(id) on delete restrict,
  user_id uuid references auth.users(id) on delete set null,
  status text not null default 'reserved' check (status in ('reserved', 'completed', 'cancelled')),
  created_at timestamptz not null default now()
);

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, full_name, role)
  values (new.id, coalesce(new.raw_user_meta_data->>'full_name', ''), 'customer')
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute procedure public.handle_new_user();

create or replace function public.is_admin()
returns boolean
language sql
stable
as $$
  select exists (
    select 1
    from public.profiles
    where id = auth.uid() and role = 'admin'
  );
$$;

alter table public.profiles enable row level security;
alter table public.parking_slots enable row level security;
alter table public.bookings enable row level security;

drop policy if exists "profiles_select_own" on public.profiles;
create policy "profiles_select_own" on public.profiles
for select
using (id = auth.uid() or public.is_admin());

drop policy if exists "slots_read_all" on public.parking_slots;
create policy "slots_read_all" on public.parking_slots
for select
using (true);

drop policy if exists "bookings_insert_authenticated" on public.bookings;
drop policy if exists "bookings_insert_public" on public.bookings;
create policy "bookings_insert_public" on public.bookings
for insert
with check (true);

drop policy if exists "bookings_select_owner_or_admin" on public.bookings;
create policy "bookings_select_owner_or_admin" on public.bookings
for select
using (public.is_admin() or user_id = auth.uid());

drop policy if exists "bookings_admin_update" on public.bookings;
create policy "bookings_admin_update" on public.bookings
for update
using (public.is_admin())
with check (public.is_admin());

drop policy if exists "bookings_owner_cancel" on public.bookings;
create policy "bookings_owner_cancel" on public.bookings
for update
using (user_id = auth.uid() and status = 'reserved')
with check (user_id = auth.uid() and status in ('reserved', 'cancelled'));

insert into public.parking_slots (slot_number)
values ('A1'), ('A2'), ('A3'), ('B1'), ('B2'), ('B3')
on conflict (slot_number) do nothing;
