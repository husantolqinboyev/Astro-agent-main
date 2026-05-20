# 1. Astro Agent: Asterisk va LLM ni qanday birlashtirdik?

## Kirish

Zamonaviy dunyoda sun'iy intellekt (AI) agentlari faqat matnli interfeys bilan cheklanib qolmasdan, tobora ko'proq real-world tizimlar bilan integratsiya qilmoqda. Ushbu maqolada biz **ASTRO V2.0** — avtonom AI tizim administratori loyihasi misolida, Katta Til Modellarini (LLM) an'anaviy telekommunikatsiya tizimi bo'lgan **Asterisk PBX** bilan qanday qilib birlashtirishni ko'rib chiqamiz.

Bu shunchaki "gaplashadigan bot" emas. Bu — telefon orqali qo'ng'iroq qilib, server holatini tekshira oladigan, ob-havoni aytib beradigan, terminal buyruqlarini bajara oladigan va mustaqil qaror qabul qiladigan haqiqiy agent.

---

## Loyihaning Umumiy Arxitekturasi

ASTRO Agent arxitekturasi uchta asosiy qatlamdan iborat:

### 1. Qabul Qilish Qatlami (Asterisk & AGI)
Tizimning kirish eshigi **Asterisk PBX** hisoblanadi. Foydalanuvchi qo'ng'iroq qilganda, Asterisk **AGI (Asterisk Gateway Interface)** protokoli orqali `bridge.py` skriptini ishga tushiradi. Bu skript Python tilida yozilgan bo'lib, ovozli signalni raqamli ma'lumotga aylantirish va teskari jarayonni boshqaradi.

**Asosiy vazifalar:**
- Qo'ng'iroqni javob berish (`ANSWER`)
- Ovozni yozib olish (`RECORD FILE`)
- Tayyor audio faylni STT dvigateliga uzatish
- TTS dan kelgan audioni abonentga eshittirish (`STREAM FILE`)

### 2. Intellektual Qatlam (LLM + LangGraph)
Ovoz matnga aylangandan so'ng, asosiy "miya" — **Google Gemini 2.0 Flash** modeli ishga tushadi. Biroq, shunchaki LLM chaqirish yetarli emas. Biz murakkab qarorlar zanjirini boshqarish uchun **LangGraph** kutubxonasidan foydalandik.

**LangGraph nima beradi?**
- **Holat boshqaruvi (State Management):** Suhbat tarixini va kontekstni saqlash.
- **Shartli o'tishlar (Conditional Edges):** Agar LLM "tool" (asbob) chaqirsa, uni bajarishga yo'naltirish; agar javob tayyor bo'lsa, suhbatni tugatish.
- **Refleksiya (Deep Think):** Agent o'z javobini mantiqan tekshirib, xatolarni oldini olish imkoniyati.

```python
# astro_agent/agents/graph.py dan parcha
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("action", ToolNode(ASTRO_TOOLS))
workflow.add_conditional_edges("agent", should_continue)
```

Ushbu graf tuzilmasi agentga chiziqli bo'lmagan, dinamik muloqot qilish imkonini beradi.

### 3. Ijro Qatlami (Tools & Memory)
Agent faqat gapirmasdan, harakat ham qilishi kerak. Buning uchun maxsus **Tools** (asboblar) to'plami yaratildi:
- `bash_terminal`: Tizim buyruqlarini bajarish (masalan, `top`, `df -h`).
- `pbx_admin`: Asteriskni boshqarish (qayta yuklash, extensionlarni tekshirish).
- `get_weather_time_and_pbx_call`: Ob-havo ma'lumotini olib, foydalanuvchiga qayta qo'ng'iroq qilish.
- `web_search`: Internetdan ma'lumot qidirish.

Shuningdek, **ChromaDB** vektorli bazasi yordamida agentga "uzoq muddatli xotira" berilgan. Bu agentga oldingi suhbatlardagi faktlarni eslab qolish va kontekstga asoslangan javoblar berish imkonini yaratadi.

---

## AI Agentning Ovozli Aloqa Tizimidagi O'rni

An'anaviy IVR (Interactive Voice Response) tizimlari ("1 ni bosing — buxoroga, 2 ni bosing — satqonga") qattiq qoidalarga asoslangan bo'lib, foydalanuvchi erkin gaplasha olmaydi. ASTRO Agent esa ushbu paradigmani tubdan o'zgartiradi:

### Farqlar Jadvali

| Xususiyat | An'anaviy IVR | ASTRO AI Agent |
|-----------|---------------|----------------|
| **Boshqaruv** | Tugmalar (DTMF) | Erkin nutq (Voice) |
| **Moslashuvchanlik** | Qattiq ssenariy | Dinamik, LLM asosida |
| **Kontekst** | Yo'q | To'liq suhbat tarixi saqlanadi |
| **Harakat** | Faqat ma'lumot berish | Terminal buyruqlari, qo'ng'iroqlar |
| **Til** | Oldindan yozilgan frazalar | Tabiiy, generatsiya qilingan nutq |

### Real Hayotdagi Ssenariy

Tasavvur qiling, siz ofisdasiz va serveringiz sekin ishlayapti. Oddiy holatda siz SSH orqali ulanib, buyruqlarni kiritishingiz kerak edi. ASTRO bilan esa jarayon quyidagicha kechadi:

1. **Siz:** "Astro, serverning disk holatini tekshirib ber."
2. **Asterisk:** Ovozni yozib oladi va `bridge.py` ga uzatadi.
3. **Vosk STT:** Ovozni matnga aylantiradi: *"serverning disk holatini tekshirib ber"*.
4. **LangGraph Agenti:** Matnni tahlil qiladi va `bash_terminal` asbobini tanlaydi.
5. **Ijro:** `df -h` buyrug'i bajariladi, natija LLM ga qaytadi.
6. **Javob:** LLM natijani tahlil qilib, odamiy tilda javob yozadi: *"Diskning 80% band, /var papkasi to'lib qolgan"*.
7. **Edge-TTS:** Javob ovozga aylantiriladi va sizga eshittiriladi.

Barcha jarayon 3-5 soniya ichida amalga oshadi.

---

## Texnik Yechimlar va Integratsiya Jarayoni

### 1. Ovozni Matnga Aylantirish (STT)
Biz bulutli yechimlar o'rniga **Vosk** offline dvigatelini tanladik. Sabablari:
- **Maxfiylik:** Audio hech qachon serverdan chiqib ketmaydi.
- **Tezlik:** Tarmoq kechikishlari yo'q.
- **O'zbek tili:** Model o'zbek tili uchun moslashtirilgan.

```python
# agi/bridge.py dan parcha
def transcribe(wav_path):
    model = Model(MODEL_PATH)
    wf = wave.open(wav_path, "rb")
    rec = KaldiRecognizer(model, wf.getframerate())
    # ... audio oqimini qayta ishlash
    return json.loads(rec.FinalResult()).get("text", "")
```

### 2. Matnni Ovozga Aylantirish (TTS)
Tabiiy va jarangdor ovoz uchun **Microsoft Edge TTS** ishlatilgan. Bu yechim bepul va yuqori sifatli neyron tarmoq ovozlarini taqdim etadi. Ammo Asterisk telefoniya standartlari (8kHz, Mono) talablariga moslashish uchun **FFmpeg** dan foydalanamiz:

```bash
ffmpeg -i input.mp3 -ar 8000 -ac 1 -acodec pcm_s16le output.wav
```

Bu konversiya jarayoni sifat va tezlik o'rtasidagi optimal balansni ta'minlaydi.

### 3. Xavfsizlik va Ruxsatlar
Agentga tizimni boshqarish huquqini berish xavfli bo'lishi mumkin. Shu sababli:
- **Fernet Shifrlash:** Sudo parollarini xavfsiz saqlash uchun AES-128 shifrlash qo'llaniladi.
- **Log Yuritish:** Har bir bajarilgan buyruq SQLite bazasida qayd etiladi.
- **Cheklovlar:** Agent faqat ruxsat berilgan buyruqlarni bajara oladi.

---

## Xulosa

ASTRO Agent loyihasi shuni ko'rsatadiki, zamonaviy LLM lar va an'anaviy telekommunikatsiya tizimlarini birlashtirish orqali g'oyat kuchli va foydali avtonom agentlar yaratish mumkin. 

**Erishilgan natijalar:**
✅ To'liq ovozli boshqaruv (Voice-First).
✅ Murakkab ko'p bosqichli vazifalarni bajarish (LangGraph).
✅ Offline STT va yuqori sifatli TTS.
✅ Tizim administratsiyasi uchun real qurol.

Keyingi maqolalarda biz **Asterisk AGI va Python** integratsiyasini chuqurroq ko'rib chiqamiz, `bridge.py` skriptining ishlash prinsiplarini tahlil qilamiz va ovozli kanalda ma'lumot almashishning nozik jihatlarini o'rganamiz.

---

*Muallif: Husan | Loyiha: ASTRO V2.0 | Sana: 2024*