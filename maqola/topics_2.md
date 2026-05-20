# Asterisk AGI va Python: Ovozli qo'ng'iroqlarni AI orqali boshqarish

## Kirish

Telefon qo'ng'iroqlarini sun'iy intellekt orqali boshqarish — bu zamonaviy kommunikatsiya tizimlarining eng dolzarb yo'nalishlaridan biridir. An'anaviy IVR (Interactive Voice Response) tizimlari foydalanuvchilarni cheklangan menyular orqali harakatlanishga majbur qilsa, **Astro Agent** loyihasi butunlay yangi yondashuvni taklif etadi: haqiqiy suhbatlasha oladigan, kontekstni tushunadigan va mustaqil qaror qabul qiladigan AI agent.

Ushbu maqolada biz `bridge.py` fayli misolida **Asterisk Gateway Interface (AGI)** protokoli yordamida Python skriptlarini qanday bog'lash, real vaqtda ovozli qo'ng'iroqlarni boshqarish va LLM (Large Language Model) bilan integratsiya qilish jarayonini batafsil ko'rib chiqamiz.

---

## 1. AGI (Asterisk Gateway Interface) Nima?

**AGI** — bu Asterisk PBX tizimi bilan tashqi dasturlar o'rtasidagi standartlashtirilgan interfeys. U telefon qo'ng'irog'i paytida quyidagi imkoniyatlarni beradi:

- Qo'ng'iroqni javob berish (`ANSWER`)
- Ovozli xabarlarni eshittirish (`STREAM FILE`)
- Foydalanuvchi javobini yozib olish (`RECORD FILE`)
- Qo'ng'iroqni yakunlash (`HANGUP`)
- Dinamik ravishda buyruqlarni bajarish

AGI protokoli oddiy matnli buyruqlar va javoblar almashinuviga asoslangan bo'lib, uni istalgan tilda (Python, PHP, Perl va h.k.) amalga oshirish mumkin.

### AGI Ishlash Prinsipi

```
┌─────────────┐         AGI Buyruqlari        ┌──────────────┐
│   Asterisk  │ ────────────────────────────> │  Python AGI  │
│   (PBX)     │ <──────────────────────────── │  Skripti     │
│             │         Javoblar/Ma'lumot      │  (bridge.py) │
└─────────────┘                                └──────────────┘
```

1. Foydalanuvchi qo'ng'iroq qiladi
2. Asterisk `extensions.conf` da belgilangan AGI skriptini ishga tushiradi
3. AGI skripti stdin/stdout orqali Asterisk bilan muloqot qiladi
4. Barcha mantiq Python kodida bajariladi

---

## 2. bridge.py Faylining Umumiy Tuzilishi

Loyihadagi `bridge.py` fayli — bu Astro Agentning **ovozli dvigateli**. U quyidagi asosiy vazifalarni bajaradi:

```python
#!/home/user/astro-agent/venv/bin/python3
"""
ASTRO AGI Voice Engine — Asterisk Gateway Interface
Handles voice calls with AI-powered conversation in Uzbek
"""
import sys, os, time, json, subprocess, wave, signal
import requests
from datetime import datetime, timedelta
```

### Asosiy Konfiguratsiya Doimiylari

```python
CLOUD_KEY = ""  # OpenRouter API kaliti
GEMMA_URL = "https://openrouter.ai/api/v1/chat/completions"
WEATHER_API_KEY = ""

BRIDGE_FILE = "/tmp/voice_bridge.txt"  # Real vaqt transcript fayli
EDGE_TTS = "/home/user/astro-agent/venv/bin/edge-tts"
FFMPEG = "/usr/bin/ffmpeg"
MODEL_PATH = "/usr/share/asterisk/vosk-model"
OUTBOUND_MODE = ""  # Chiquvchi qo'ng'iroq rejimi
```

Bu konstantalar tizimning ishlashi uchun zarur bo'lgan manzillar, API URL'lari va sozlamalarni saqlaydi.

---

## 3. AGI Kommunikatsiyasi: stdin/stdout Protokoli

AGI skripti Asterisk bilan **standart input/output** orqali muloqot qiladi. Bu juda oddiy, lekin samarali mexanizm:

### agi_send() Funksiyasi

```python
def agi_send(cmd):
    try:
        sys.stdout.write(cmd + "\n")
        sys.stdout.flush()
        return sys.stdin.readline().strip()
    except: return ""
```

Bu funksiya:
1. Buyruqni stdout ga yozadi (Asteriskga yuboradi)
2. Buffer'ni tozalaydi (`flush()`)
3. Asteriskdan javobni kutadi va qaytaradi

### Misol: Qo'ng'iroqni Javob Berish

```python
agi_send("ANSWER")
```

Bu buyruq qo'ng'iroqni avtomatik javob beradi va Asteriskdan quyidagiga o'xshash javob keladi:
```
200 result=0
```

Bu yerda `200` — muvaffaqiyat kodi, `result=0` — operatsiya natijasi.

---

## 4. Ovozli Muloqot Sikli

`bridge.py` dagi asosiy mantiq `main()` funksiyasida joylashgan. Keling, uni bosqichma-bosqich ko'rib chiqamiz:

### 4.1. Dastlabki Sozlash

```python
def main():
    global active_mission, full_transcript
    
    # AGI headerlarini o'qish (Asterisk yuboradi)
    while True:
        if sys.stdin.readline().strip() == "": break
    
    # Bridge faylini tayyorlash
    try:
        open(BRIDGE_FILE, "a").close()
        os.chmod(BRIDGE_FILE, 0o666)
    except: pass
    
    # Qo'ng'iroqni javob berish
    agi_send("ANSWER")
    broadcast("--- Kiruvchi/Chiquvchi Qo'ng'iroq ---", "SYSTEM")
```

Dastlabki sikl Asterisk yuboradigan AGI headerlarini (chan_id, caller_id va h.k.) o'qib chiqadi va keyingi ishlash uchun tayyorlanadi.

### 4.2. Suhbat Tarixini Shakllantirish

```python
hist = []

if OUTBOUND_MODE == "custom_call":
    # Chiquvchi qo'ng'iroq rejimi
    intro = ""
    try:
        with open("/tmp/agi_outbound_msg.txt", "r") as f: 
            intro = f.read().strip()
    except: pass
    
    if not intro: intro = "Salom!"
    
    mission_goal = ""
    try:
        with open(CONTEXT_FILE, "r") as f: 
            mission_goal = f.read().strip()
    except: pass
    
    if mission_goal:
        active_mission = True
        hist.append({
            "role": "system",
            "content": f"Siz Astro AI siz. Raqamga QO'NG'IROQ QILDINGIZ!\nMAQSAD:\n{mission_goal}\nMaqsad yakunlangach xayrlashing!"
        })
    else:
        hist.append({"role": "system", "content": BASE_PROMPT})
    
    say_uz(intro)
    broadcast(intro, "Agent")
    hist.append({"role": "assistant", "content": intro})
else:
    # Kiruvchi qo'ng'iroq rejimi
    hist.append({"role": "system", "content": BASE_PROMPT})
    say_uz("Assalomu alaykum! Men Astro yordamchisiman. Eshitaman!")
    broadcast("Assalomu alaykum! Men Astro man. Eshitaman!", "Agent")
    hist.append({"role": "assistant", "content": "Assalomu alaykum! Eshitaman!"})
```

Bu kod ikkita rejimni qo'llab-quvvatlaydi:
- **Kiruvchi qo'ng'iroq**: Foydalanuvchi Astro ga qo'ng'iroq qiladi
- **Chiquvchi qo'ng'iroq**: Astro missiya bilan foydalanuvchini chaqiradi

### 4.3. Ovoz Yozish va Tanib Olish Sikli

```python
silence_count = 0
for _ in range(25):  # Maksimal 25 ta iteratsiya
    wav_path = "/tmp/agi_voice_input.wav"
    try: os.remove(wav_path)
    except: pass
    
    # Foydalanuvchi ovozi yozib olish
    agi_status = agi_send('RECORD FILE /tmp/agi_voice_input wav "#" 10000 0 BEEP s=4')
    if not agi_status: break
    
    # Ovozni matnga aylantirish (STT)
    user_text = transcribe(wav_path).lower()
    
    # Agar sukunat bo'lsa
    if not user_text.strip():
        silence_count += 1
        if silence_count >= 2:
            say_uz("Hech kim gapirmadi, sog bo'ling.")
            broadcast("Sog bo'ling.", "Agent")
            break
        continue
    
    silence_count = 0
    broadcast(user_text, "User")
    hist.append({"role": "user", "content": user_text})
    full_transcript.append(f"Foydalanuvchi: {user_text}")
```

Bu sikl quyidagi amallarni bajaradi:
1. `RECORD FILE` buyrug'i bilan foydalanuvchi ovozi yozib olinadi (# tugmasi yoki 10 soniya davomida)
2. `transcribe()` funksiyasi yordamida ovoz matnga aylantiriladi (Vosk STT)
3. Agar 2 marta ketma-ket sukunat aniqlansa, qo'ng'iroq yakunlanadi
4. Foydalanuvchi matni tarixga qo'shiladi

### 4.4. Xayrlashish So'zlarini Aniqlash

```python
hangup_words = ["hayr", "xayr", "rahmat", "sog", "stop", "tugat", "qoy"]
if any(w in user_text for w in hangup_words) and len(user_text.split()) < 4:
    say_uz("Sog bo'ling!")
    broadcast("Sog bo'ling!", "Agent")
    full_transcript.append("Agent: Sog bo'ling!")
    break
```

Bu oddiy, lekin samarali usul foydalanuvchi xayrlashish so'zlarini aytsa, qo'ng'iroqni darhol yakunlaydi.

---

## 5. LLM Integratsiyasi va Tool Calls

Eng qiziqarli qism — bu AI model bilan muloqot va tashqi vositalardan foydalanish:

### 5.1. OpenRouter API Chaqiruvi

```python
for __ in range(2):  # Maksimal 2 ta urinish
    try:
        r = requests.post(
            GEMMA_URL, 
            headers={"Authorization": "Bearer " + CLOUD_KEY},
            json={
                "model": "google/gemini-2.0-flash-lite-001",
                "messages": hist,
                "max_tokens": 512,
                "temperature": 0.2,
                "tools": TOOLS
            }, 
            timeout=30
        ).json()
        
        if "choices" not in r: break
        m = r["choices"][0]["message"]
```

Bu kod:
- Suhbat tarixini (`hist`) LLM ga yuboradi
- `tools` parametri orqali modelga tashqi funksiyalarni bajarish huquqini beradi
- Google Gemini 2.0 Flash Lite modelidan foydalanadi (tez va arzon)

### 5.2. Tool Call'larni Bajarish

Agar LLM tashqi funksiya chaqirishga qaror qilsa:

```python
if m.get("tool_calls"):
    hist.append(m)
    for tc in m["tool_calls"]:
        fn = tc["function"]["name"]
        args = json.loads(tc["function"]["arguments"])
        broadcast(f"[⚙️ {fn}]", "SYSTEM")
        
        if fn == "run_terminal":
            res = run_cmd(args.get("command", ""))
        elif fn == "get_weather_and_time":
            res = get_weather_and_time(
                args.get("location", "Tashkent"), 
                args.get("iana_timezone", "Asia/Tashkent")
            )
        elif fn == "save_user_name":
            res = save_name_to_file(args.get("user_name", ""))
        else:
            res = "OK"
        
        hist.append({
            "role": "tool",
            "tool_call_id": tc["id"],
            "name": fn,
            "content": str(res)[:1000]
        })
    continue  # Natija bilan qayta so'rov yuborish
```

Bu mexanizm AI ga quyidagi imkoniyatlarni beradi:
- **Terminal buyruqlarini bajarish** (`run_terminal`)
- **Ob-havo va vaqtni aniqlash** (`get_weather_and_time`)
- **Foydalanuvchi ismini eslab qolish** (`save_user_name`)

### 5.3. Javobni Ovozga Aylantirish

```python
ans = m.get("content", "")
if ans:
    hist.append({"role": "assistant", "content": ans})
    broadcast(ans, "Agent")
    say_uz(ans)
    full_transcript.append(f"Agent: {ans}")
```

AI javobi:
1. Tarixga qo'shiladi
2. `broadcast()` orqali transcript fayliga yoziladi
3. `say_uz()` orqali ovozga aylantiriladi va eshittiriladi

---

## 6. Ovoz Bilan Ishlash: TTS va STT

### 6.1. Text-to-Speech (say_uz)

```python
def say_uz(text):
    tmp_mp3 = "/tmp/agi_tts.mp3"
    tmp_wav = "/tmp/agi_tts.wav"
    voice = get_voice()
    
    try:
        # Edge-TTS orqali MP3 generatsiya
        subprocess.run([
            EDGE_TTS, "--voice", voice, "--rate", "+35%", 
            "--volume", "+100%", "--text", text, 
            "--write-media", tmp_mp3
        ], check=True, timeout=20, capture_output=True)
        
        # FFmpeg orqali Asterisk formatiga o'tkazish (8kHz, Mono)
        subprocess.run([
            FFMPEG, "-y", "-i", tmp_mp3, "-ar", "8000", "-ac", "1",
            "-acodec", "pcm_s16le", tmp_wav
        ], check=True, stderr=subprocess.DEVNULL, 
           stdout=subprocess.DEVNULL, timeout=10)
        
        # Asteriskga audio faylni eshittirish
        agi_send('STREAM FILE /tmp/agi_tts ""')
    except Exception as e:
        broadcast(f"TTS xato: {e}", "SYSTEM")
```

Bu funksiya:
1. Microsoft Edge-TTS dan foydalanib, matnni MP3 formatida generatsiya qiladi
2. FFmpeg yordamida Asterisk talab qiladigan formatga (8kHz, mono, PCM) o'tkazadi
3. `STREAM FILE` buyrug'i orqali faylni qo'ng'iroq qiluvchiga eshittiradi

### 6.2. Speech-to-Text (transcribe)

```python
_global_vosk_model = None

def transcribe(wav_path):
    global _global_vosk_model
    from vosk import Model, KaldiRecognizer, SetLogLevel
    SetLogLevel(-1)
    
    if not os.path.exists(MODEL_PATH) or not os.path.exists(wav_path): 
        return ""
    
    try:
        if os.path.getsize(wav_path) < 1000: 
            return ""
        
        # Modelni bir marta yuklash (performance optimizatsiya)
        if _global_vosk_model is None:
            _global_vosk_model = Model(MODEL_PATH)
        
        wf = wave.open(wav_path, "rb")
        rec = KaldiRecognizer(_global_vosk_model, wf.getframerate())
        rec.SetWords(True)
        
        while True:
            data = wf.readframes(4000)
            if len(data) == 0: break
            rec.AcceptWaveform(data)
        
        wf.close()
        return json.loads(rec.FinalResult()).get("text", "")
    except Exception as e:
        broadcast(f"STT Error: {e}", "SYSTEM")
        return ""
```

Bu funksiya:
1. Vosk modelini bir marta yuklaydi (xotirada saqlaydi)
2. WAV faylni ochib, kadrlar bo'yicha o'qiydi
3. KaldiRecognizer yordamida nutqni matnga aylantiradi
4. JSON formatidagi natijadan matnni ajratib oladi

---

## 7. Ma'lumotlar Bazasiga Saqlash

Har bir qo'ng'iroq tarixi SQLite bazasiga saqlanadi:

```python
def save_to_db(transcript_lines):
    import sqlite3
    try:
        db_dir = "/home/user/astro-agent/db"
        os.makedirs(db_dir, exist_ok=True)
        
        conn = sqlite3.connect(f"{db_dir}/astro_calls.db")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS calls 
            (id INTEGER PRIMARY KEY, ts DATETIME, transcript TEXT)
        """)
        conn.execute(
            "INSERT INTO calls (ts, transcript) VALUES (datetime('now'), ?)", 
            ("\\n".join(transcript_lines),)
        )
        conn.commit()
    except Exception as e:
        broadcast(f"DB Xato: {e}", "SYSTEM")
```

Bu yechim:
- Barcha qo'ng'iroqlar tarixini saqlaydi
- Vaqt stampi bilan birga to'liq transkriptni yozadi
- Keyingi tahlillar va ML o'qitish uchun ma'lumot bazasi yaratadi

---

## 8. Real Hayotdagi Ishlatish Ssenariysi

Keling, real qo'ng'iroq ssenariysini ko'rib chiqamiz:

### Ssenariy: Ob-havo So'rash

**1-qadam:** Foydalanuvchi qo'ng'iroq qiladi
```
Asterisk -> AGI: ANSWER
AGI -> Asterisk: 200 result=0
```

**2-qadam:** Astro salom beradi
```python
say_uz("Assalomu alaykum! Men Astro yordamchisiman. Eshitaman!")
```

**3-qadam:** Foydalanuvchi savol beradi
```
Foydalanuvchi: "Toshkentda ob-havo qanday?"
```

**4-qadam:** STT orqali matn olinadi va LLM ga yuboriladi

**5-qadam:** LLM tool call yaratadi
```json
{
  "name": "get_weather_and_time",
  "arguments": {"location": "Toshkent", "iana_timezone": "Asia/Tashkent"}
}
```

**6-qadam:** Python funksiyasi bajariladi
```python
res = get_weather_and_time("Toshkent", "Asia/Tashkent")
# Natija: "Toshkent: 2026-yil 17-aprel, soat 16:13. Ob-havo: harorat 22°C, ochiq."
```

**7-qadam:** Natija LLM ga qaytariladi va javob shakllantiriladi

**8-qadam:** Javob ovozga aylantiriladi va eshittiriladi
```
Astro: "Toshkentda hozir 22 daraja issiq, ob-havo ochiq."
```

---

## 9. Xavfsizlik va Optimizatsiya

### 9.1. Signal Handling

```python
try: 
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
except: pass
```

Bu kod AGI skriptini `SIGHUP` signaliga e'tibor bermaslikka o'rgatadi, bu Asterisk qayta yuklanganda skript to'xtab qolmasligini ta'minlaydi.

### 9.2. API Kalitlarni Xavfsiz Saqlash

```python
try:
    import pathlib
    cfg_path = pathlib.Path("/home/user/.astro/config.json")
    if cfg_path.exists():
        _cfg = json.loads(cfg_path.read_text())
        _prov = _cfg.get("providers", {}).get(_cfg.get("provider", "openrouter"), {})
        CLOUD_KEY = _prov.get("key", CLOUD_KEY)
        GEMMA_URL = _prov.get("url", GEMMA_URL)
        WEATHER_API_KEY = _cfg.get("weather_api_key", WEATHER_API_KEY)
except: pass
```

API kalitlar konfiguratsiya faylidan o'qiladi va kodda ochiq holda saqlanmaydi.

### 9.3. Performance Optimizatsiyalari

- **Global model**: Vosk modeli bir marta yuklanadi va xotirada saqlanadi
- **Timeout'lar**: Barcha tashqi chaqiruvlarda timeout belgilangan
- **Silence detection**: Sukunatni aniqlash orqali keraksiz iteratsiyalar oldini olish

---

## 10. Xulosa

`bridge.py` fayli orqali biz quyidagi ko'nikmalarni o'rgandik:

1. **AGI protokoli** — Asterisk bilan oddiy matnli buyruqlar orqali muloqot qilish
2. **Real vaqt boshqaruvi** — Qo'ng'iroq jarayonini dinamik boshqarish
3. **STT/TTS integratsiyasi** — Ovozni matnga va matnni ovozga aylantirish
4. **LLM Tool Calling** — AI ga tashqi funksiyalarni bajarish huquqini berish
5. **Ma'lumotlarni saqlash** — Qo'ng'iroq tarixini bazaga yozish

Ushbu yechim an'anaviy IVR tizimlaridan tubdan farq qiladi:
- **Statik menyu** o'rniga — **dinamik suhbat**
- **Cheklangan ssenariy** o'rniga — **moslashuvchan AI**
- **Quruq javoblar** o'rniga — **kontekstli muloqot**

Keyingi maqolada biz **Vosk STT** texnologiyasini chuqurroq ko'rib chiqamiz va o'zbek tilidagi nutqni internetisiz qanday tanib olish mumkinligini o'rganamiz.

---

## Qo'shimcha Manbalar

- [Asterisk AGI Dokumentatsiyasi](https://wiki.asterisk.org/wiki/display/AST/Asterisk+11+Application_AGI)
- [Vosk STT](https://alphacephei.com/vosk/)
- [Edge-TTS](https://github.com/rany2/edge-tts)
- [OpenRouter API](https://openrouter.ai/docs)
- [LangGraph](https://langchain-ai.github.io/langgraph/)

---

*Muallif: Astro Agent Development Team*  
*Sana: 2026-yil*  
*Versiya: 2.0*
