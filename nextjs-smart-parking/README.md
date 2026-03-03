# Smart Parking (Next.js + Supabase)

واجهة ويب وموبايل مرتبطة بنفس قاعدة بيانات Supabase.

## ما تم تجهيزه
- `/mobile`: صفحة حجز موقف من الهاتف
- `/mobile/login`: دخول/إنشاء حساب الزبون من الموبايل
- `/admin`: لوحة مشرف تعرض الحجوزات مباشرة (Realtime)
- `/login`: تسجيل دخول المشرف
- مخطط قاعدة البيانات وسياسات الصلاحيات داخل `supabase/schema.sql`

## 1) إعداد Supabase
1. أنشئ مشروع Supabase جديد.
2. افتح SQL Editor ونفّذ محتوى الملف `supabase/schema.sql`.
3. أنشئ مستخدم Auth للمشرف من Authentication.
4. نفّذ SQL التالي لجعل الحساب مشرفًا:

```sql
update public.profiles
set role = 'admin'
where id = 'USER_UUID_FROM_AUTH_USERS';
```

## 2) إعداد بيئة Next.js
1. انسخ `.env.example` إلى `.env.local`.
2. ضع القيم:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`

## 3) التشغيل المحلي
```bash
npm install
npm run dev
```

ثم افتح:
- `http://localhost:3000/mobile`
- `http://localhost:3000/mobile/login`
- `http://localhost:3000/login`
- `http://localhost:3000/admin`

## 4) ربط الموبايل
بعد نشر Next.js (مثل Vercel)، ضع رابطك في:
- `android_mobile_app/MainActivity.java`
- `mobile_app/MainActivity.java`

الرابط يجب أن يكون بهذا الشكل:
`https://your-nextjs-app.vercel.app/mobile`

## 5) تشغيل فوري على Android Emulator
- تم ضبط WebView حالياً على:
   - `http://10.0.2.2:3000/mobile`
- شغّل Next.js محلياً أولاً:

```bash
npm run dev
```

## 6) ملاحظة الجهاز الحقيقي
- إذا ستختبر على هاتف فعلي، استبدل `10.0.2.2` بعنوان IP جهازك على نفس الشبكة (مثال: `http://192.168.1.10:3000/mobile`).
- بعد النشر، استبدل الرابط برابط HTTPS النهائي للتطبيق.

## 7) نشر المشروع على Vercel (الخطوات النهائية)
1. ارفع المشروع إلى GitHub.
2. من Vercel اختر **Add New Project** ثم اربط نفس المستودع.
3. في إعدادات المشروع على Vercel اضبط **Root Directory** إلى:
   - `nextjs-smart-parking`
4. أضف Environment Variables في Vercel:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
5. اضغط Deploy.
6. بعد نجاح النشر انسخ الدومين النهائي (مثال: `https://smart-parking.vercel.app`).
7. عدّل رابط الإنتاج في:
   - `android_mobile_app/MainActivity.java`
   - `mobile_app/MainActivity.java`
   واستبدل `https://YOUR_VERCEL_DOMAIN/mobile` بالرابط الحقيقي.

## 8) فحص ما بعد النشر
- افتح `https://YOUR_DEPLOYED_DOMAIN/mobile/login` وسجّل دخول/أنشئ حساب زبون.
- افتح `https://YOUR_DEPLOYED_DOMAIN/mobile` واحجز موقف.
- افتح `https://YOUR_DEPLOYED_DOMAIN/login` وسجّل دخول المشرف.
- تأكد أن الحجز يظهر فورًا في `https://YOUR_DEPLOYED_DOMAIN/admin`.

## 9) حل رسالة: "يرجى إعداد NEXT_PUBLIC_SUPABASE_URL و NEXT_PUBLIC_SUPABASE_ANON_KEY"
1. من لوحة Supabase افتح: **Project Settings > API**.
2. انسخ:
   - **Project URL** وضعه في `NEXT_PUBLIC_SUPABASE_URL`
   - **anon public key** وضعه في `NEXT_PUBLIC_SUPABASE_ANON_KEY`
3. أنشئ ملف `.env.local` داخل مجلد `nextjs-smart-parking` واكتب:

```dotenv
NEXT_PUBLIC_SUPABASE_URL=https://YOUR_PROJECT.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=YOUR_ANON_KEY
```

4. أعد تشغيل السيرفر:

```bash
npm run dev
```

## 10) إعداد المشرف والزبون (اختبار كامل)
1. أنشئ حساب مشرف من **Supabase Authentication > Users**.
2. نفّذ SQL التالي (استبدل بـ user id الحقيقي):

```sql
update public.profiles
set role = 'admin'
where id = 'USER_UUID_FROM_AUTH_USERS';
```

3. أنشئ حساب زبون من `.../mobile/login` (Sign up).
4. ادخل كمشرف من `.../login` ثم افتح `.../admin`.
5. احجز من `.../mobile` بحساب الزبون وتأكد يظهر مباشرة في لوحة المشرف باسم الزبون.
