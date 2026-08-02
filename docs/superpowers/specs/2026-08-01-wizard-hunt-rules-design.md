# I'm Not a Wizard, Harry — zasady gry

Data: 2026-08-01
Status: zatwierdzony projekt, do wdrożenia

## Czym ta gra jest

Ośmioro ludzi przeczesuje wrak stacji w poszukiwaniu artefaktów
magiczno-technologicznych. Jeden z nich jest magiem. Mag wybija resztę
zaklęciami i musi przy tym uchodzić za łowcę.

Rdzeń to **śledztwo**, nie pościg. Gracze zbierają ślady, składają je i
przekonują siebie nawzajem. Żaden pojedynczy dowód nie nazywa maga —
każdy tylko zawęża krąg, a mag ma czym dowody zatruwać.

Rozmowa toczy się **poza grą** (Discord). Gra nie ma czatu: na telefonie
pisanie w biegu nie działa. Zamiast tego daje pingi, które obsługuje kciuk.

## Decyzje ramowe

| Decyzja | Wybór |
|---|---|
| Rdzeń | dowody i śledztwo |
| Komunikacja | głos poza grą + pingi w grze |
| Siła dowodu | zawęża, nigdy nie nazywa |
| Wyrok | trybunał odpalany pojmaniem, także przez maga |
| Skład | 5–8 graczy, jeden mag |
| Runda | do 30 minut, trzy akty |
| Martwi | idą do bazy i obsługują stację |

---

## 1. Runda

### Akty

Trzy akty po 10 minut. Wrak gaśnie z każdym aktem.

| Akt | Sekcja | Mnożnik widoczności | Artefakty |
|---|---|---|---|
| I — Rozpoznanie | pokład górny | 1.0 | 4 |
| II — Awaria | + pokład dolny | 0.75 | 4 |
| III — Ciemność | + rdzeń | 0.5 | 4 |

Akt kończy się, gdy jego artefakty są zabezpieczone albo gdy minie
`ACT_MS` (600 000). Artefakty niezabrane na czas są **stracone** na stałe.

Grodzie do sekcji kolejnego aktu otwierają się na jego starcie. Sekcje
poprzednich aktów zostają otwarte.

### Warunki zwycięstwa

* **Łowcy** — zabezpieczą 9 z 12 artefaktów, **albo** trybunał wyrzuci maga.
* **Mag** — zostaje ≤1 łowca, **albo** minie 30 minut przy nim żywym.

Przy **4 straconych artefaktach** ścieżka artefaktowa jest zamknięta —
9 z 12 przestaje być osiągalne. Łowcom zostaje wtedy wyłącznie trybunał.

To jest zegar maga. Nie musi zabijać, żeby wygrywać: wystarczy, że
zamuruje albo spali cztery artefakty. Ciemność pracuje dla niego, więc
przeciąganie rundy jest jego strategią, a nie brakiem pomysłu.

### Kontra na śnieżną kulę

Każdy zabity zasila bazę. Im więcej mag zabije, tym więcej oczu i rąk ma
przeciwnik. Ciemność go rozpędza, trupy hamują.

---

## 2. Mapa

Jedna mapa 2000×1600, piętnaście przedziałów, po pięć na sekcję aktu.
W każdym akcie cztery z pięciu przedziałów sekcji dostają artefakt.

| Sekcja | Przedziały |
|---|---|
| Pokład górny (akt I) | Mostek, Ładownia, Mesa, Kwatery, Obserwatorium |
| Pokład dolny (akt II) | Medyczny, Kaplica, Warsztat, Kriokomory, Maszynownia |
| Rdzeń (akt III) | Reaktor, Archiwum, Śluza, Serwerownia, Ładownia rdzenia |

Poza przedziałami są jeszcze **korytarze** — po jednym na każde połączenie,
osiemnaście sztuk. Tylko te strefy są podłogą; wokół nich jest kadłub i
próżnia, więc nikt nie zejdzie ze statku i żaden Podmuch nikogo tam nie
wypchnie.

Korytarz **nie jest drzwiami ani ekranem ładowania**. To pełnoprawne
pomieszczenie: dość długie, żeby dać się w nim dopaść w połowie, dość
szerokie na kilka osób — i **nie patrzy w nie żadna kamera**. To czyni go
jedynym miejscem na statku, gdzie zabójstwo nie ma świadka poza ścianami.
Dokładnie tego potrzebuje mag, i dokładnie dlatego łowca powinien się dwa
razy zastanowić, zanim wejdzie tam w czyimś towarzystwie.

**Wejście do korytarza uzbraja oba włazy.** Dwie sekundy ostrzeżenia, potem
zatrzask na pięć. Ostrzeżenie jest sensem tego timera: masz chwilę, żeby się
wycofać, a ten, kto wchodzi za tobą, ma chwilę, żeby zdecydować, czy naprawdę
chce tam być, gdy się zamknie.

Zamknięty korytarz jest **szczelny dla wzroku w obie strony** — mgła zacieśnia
się do jego własnych ścian. Widzisz tylko tego, kto jest zamknięty razem z
tobą, a łowca stojący krok za drzwiami nie widzi nic. Bez tego pudełko było
tylko w połowie pudełkiem: widoczność jest tu promieniem, a ściany jej nie
zatrzymują, więc morderstwo dałoby się obejrzeć przez ścianę.

Korytarze są logowane jak wszystko inne, i to czyni je groźnymi w obie
strony. **„Weszło dwóch, wyszedł jeden"** to najtwardszy dowód w tej grze —
a przebranie jest jedyną rzeczą, która potrafi o tym skłamać.

Rygiel zamyka otwory strefy. Zawał grzebie pomieszczenie na stałe, ale
odmawia korytarza: przecięcie statku na pół zablokowałoby rundę.

---

## 3. Klasy

Osiem klas, **każda unikalna w rundzie** — dlatego maksimum to ośmioro
graczy. Mag też dostaje klasę i musi ją odgrywać.

| Klasa | Wzrok | Tazer | Życie | Prędkość |
|---|---|---|---|---|
| Strażnik | 210 | 62 | 2 | 0.86 |
| Zwiadowca | 330 | 58 | 1 | 1.14 |
| Strzelec | 250 | 58 | 1 | 1.00 |
| Inkwizytor | 240 | 70 | 1 | 1.00 |
| Chirurg | 230 | 58 | 1 | 0.98 |
| Runarz | 235 | 58 | 1 | 0.96 |
| Archiwista | 225 | 58 | 1 | 0.94 |
| Technik | 245 | 58 | 1 | 1.02 |

Wzrok mnoży się przez mnożnik widoczności aktu.

### Wyposażenie — jedno z trzech

Wybierane przed rundą. Zasada: **wybór musi być widoczny w grze**, żeby
deklaracja dała się sprawdzić. Kto mówi, że wziął kamizelki, powinien je
rozdawać.

| Klasa | Przedmiot | Działanie |
|---|---|---|
| Strażnik | Tarcza szturmowa | blokuje jedno zaklęcie od przodu, 20 s stygnięcia |
| | Plecak z kamizelkami | 3 kamizelki do rozdania, każda zjada jedno trafienie |
| | Kotwica | barykada w przejściu na 20 s, 2 ładunki |
| Zwiadowca | Dron | wysyła drona, odsłania wskazany przedział na 6 s, 3 ładunki |
| | Czujnik ruchu | stawia czujnik, pinguje wejścia klasą, 2 sztuki |
| | Optyka | wzrok +70 na stałe |
| Strzelec | Karabin | ogłuszenie z 330 px, 3 ładunki |
| | Siatka | spowolnienie 60% w promieniu 90 na 8 s, 2 ładunki |
| | Znacznik | znacznik nad celem widoczny dla wszystkich 20 s, 3 ładunki |
| Inkwizytor | Kadzidło | ślad ze zwłok czytelny 3× dłużej |
| | Kajdany | wiązanie o połowę szybsze |
| | Wykrywacz | pokazuje, czy w przedziale rzucano w tym akcie |
| Chirurg | Stabilizator | podnosi jednego rannego łowcę, 1 ładunek |
| | Stymulanty | +40% prędkości i −50% ogłuszenia na 10 s, 2 ładunki |
| | Autopsja | ze zwłok czyta dokładny czas zgonu |
| Runarz | Ekstraktor | ekstrakcja 2× szybsza |
| | Pieczęć | artefakt odporny na Pożogę i Zawał; nadal wymaga ekstrakcji, 3 ładunki |
| | Zakłócacz | blokuje rzucanie w przedziale na 15 s, 2 ładunki |
| Archiwista | Czytnik | czyta rejestr przedziału bez artefaktu |
| | Kopia | zapisuje jeden rejestr tak, że przeżyje zmianę aktu, 2 ładunki |
| | Filtr | rejestr z ostatnich 60 s, ale odporny na wymazanie |
| Technik | Generator | pełne światło w przedziale na 30 s, 3 ładunki |
| | Kamera polowa | stawia kamerę widoczną dla bazy, 2 sztuki |
| | Rygiel | zamyka drzwi przedziału na 20 s, 3 ładunki |

Każdy łowca ma poza tym **tazer**: ogłuszenie 3.6 s, zasięg wg klasy,
stygnięcie 6 s.

---

## 4. Mag

### Księga

Mag wybiera **10 slotów** z księgi 24 zaklęć. Duplikaty wolno i sumują
ładunki. Po wyczerpaniu ładunków zaklęcie znika z paska do końca rundy.

Sześć szkół, każda z inną robotą:

| Szkoła | Robota |
|---|---|
| Ogień | obrażenia, pociski |
| Woda | spowolnienie, otępienie, sen |
| Powietrze | podmuch, przeskok, burza |
| Ziemia | ściany, ryglowanie, wstrząs |
| Mrok | gaszenie świateł, ukrycie, psucie śladów |
| Światło | przebranie, sobowtór, kłamstwo o tożsamości |

### Zaklęcia

Zaklęcie jest **danymi**: `{ id, szkoła, ładunki, czasRzucania, zasięg, efekt }`.
Dokładanie kolejnych to linijka w pliku, nie nowa mechanika.

| Szkoła | Zaklęcie | Ład. | Rzut | Działanie |
|---|---|---|---|---|
| Ogień | Kula ognia | 3 | 0.9 s | pocisk 7.6 px/tick, zabija przy trafieniu |
| | Pochodnia | 2 | 0.6 s | stożek 120 px, zabija |
| | Zapłon | 2 | 0.7 s | znacznik w miejscu, po 3 s wybuch zabijający w promieniu 80 |
| | Pożoga | 1 | 1.4 s | niszczy artefakt w przedziale — artefakt stracony |
| Woda | Sen | 2 | 1.0 s | cel zasypia na 4 s |
| | Topiel | 2 | 0.8 s | spowolnienie 60% w promieniu 140 na 6 s |
| | Cisza | 2 | 0.7 s | cel nie pinguje i nie kanałuje przez 8 s |
| | Zimna krew | 1 | 0.8 s | mag ignoruje najbliższe ogłuszenie tazerem |
| Powietrze | Łańcuch błyskawic | 2 | 1.0 s | ogłuszenie 2.5 s, przeskakuje do 3 celów |
| | Podmuch | 3 | 0.5 s | odrzuca cel o 200 px |
| | Pęd | 3 | 0.4 s | mag +80% prędkości na 5 s |
| | Burza | 2 | 1.1 s | ogłuszenie 3.2 s w promieniu 130 |
| Ziemia | Mur | 3 | 0.8 s | ściana w przejściu na 25 s |
| | Rygiel | 2 | 0.9 s | zamyka drzwi przedziału na 20 s |
| | Wstrząs | 2 | 1.0 s | przerywa wszystkie kanały w przedziale i przewraca na 1.5 s |
| | Zawał | 1 | 2.0 s | zamyka przedział na stałe — jego artefakt stracony |
| Mrok | Zgaszenie | 3 | 0.6 s | gasi światło w przedziale na 40 s |
| | Wymazanie | 2 | 1.2 s | kasuje własne wpisy z rejestru przedziału w tym akcie |
| | Fałszywy ślad | 3 | 0.8 s | podrzuca osad wybranej szkoły |
| | Cień | 2 | 0.5 s | mag niewidzialny 5 s — ale nadal logowany |
| Światło | Przebranie | 2 | 1.0 s | renderuje się jako inna klasa 14 s; rejestr zapisuje tę klasę |
| | Sobowtór | 2 | 0.9 s | kopia maga odchodzi w bok na 8 s |
| | Oślepienie | 3 | 0.6 s | wzrok celu spada do 25% na 6 s |
| | Fałszywa sylwetka | 2 | 1.0 s | karmi kamery bazy wybraną klasą przez 15 s |

Zasięg domyślny to **210 px** i celuje się kursorem albo dotknięciem;
zaklęcia obszarowe podają promień w tabeli, Kula ognia leci aż trafi albo
zgaśnie po 2.4 s, a zaklęcia przedziałowe (Pożoga, Zawał, Rygiel,
Zgaszenie, Wymazanie, Fałszywy ślad, Wstrząs) działają na przedział, w
którym stoi mag.

**Wspólne stygnięcie** 3 s po każdym rzucie, żeby nie da się było zrzucić
całej księgi w jednej sekundzie.

**Maga nic nie rani.** Łowcy mają wyłącznie ogłuszenie — jedyną drogą do
niego jest tazer, wiązanie i trybunał. Dlatego Woda daje mu Zimną krew
zamiast leczenia: obrona przed ogłuszeniem jest jedyną obroną, jaka ma
dla niego sens. Z tego samego powodu przedmioty klasy przykrywkowej są
dla maga bezużyteczne mechanicznie — bierze je po to, żeby móc je odegrać.

**Telegraf.** Każde zaklęcie ma czas rzucania, w trakcie którego w miejscu
maga kwitnie efekt widoczny dla każdego z linią wzroku. Tazer w czasie
rzucania **przerywa i zjada ładunek**. Bez tego mag jest nie do pobicia;
z tym — bycie widzianym jest ryzykiem, którym zarządza.

### Drugi zestaw

Mag wybiera **także wyposażenie swojej klasy przykrywkowej** i musi umieć
je odegrać. Podał się za Chirurga ze stabilizatorem — niech kogoś
podniesie. Przykrywka jest rolą, nie etykietą.

**Wyposażenie widać na sylwetce.** Arkusz sprite'ów rysuje każdą klasę
trzy razy — po razie na przedmiot — więc to, co ktoś niesie, jest
obserwacją, nie deklaracją. Zamienia to jeden blef na ostrzejsze
pytanie: nikt nie skłamie, że wziął stabilizator, ale każdy widzi, kto
go nosi i nikogo nie podniósł. Przebranie pożycza cały wygląd razem ze
sprzętem — inaczej sylwetka przeczyłaby twarzy i wydawała maga za darmo.

### Trzy style z tych samych dziesięciu slotów

* **Rzeźnik** (ogień/woda) — zabija wprost, zostawia czytelny podpis.
* **Budowlaniec** (ziemia/powietrze) — nie musi zabijać, zamyka artefakty.
* **Oszust** (mrok/światło) — nie ma czym zabijać w ogóle, wygrywa
  wyłącznie trybunałem, wrabiając ludzi ich własnymi rękami.

Wszystkie trzy są legalne i wygrywalne.

---

## 5. Dowody

### Rejestr przedziału

Każde wejście i wyjście zapisuje **klasę i czas**, nigdy imię. Widoczny
jest tylko bieżący akt.

Czytanie: wyciągnięcie artefaktu z przedziału zrzuca jego rejestr, albo
Archiwista Czytnikiem bez artefaktu.

Klasy są unikalne, więc wpis wskazuje konkretnego człowieka — ale
wskazuje go jako **obecnego, nie winnego**. Obecność to nie sprawstwo.
Żeby zamknąć sprawę, trzeba złożyć rejestr ze śladem na zwłokach, z
osadem i z tym, co ludzie mówią o sobie.

Mag psuje rejestr dwoma zaklęciami: **Przebranie** wpisuje cudzą klasę,
**Wymazanie** kasuje jego wpisy. Rejestr nie jest prawdą o rundzie —
jest zeznaniem, które ktoś mógł podrobić.

### Ślad na zwłokach

Zwłoki niosą **szkołę** zaklęcia i przybliżony czas zgonu (±30 s).
Czytelne przez 120 s, z Kadzidłem 360 s. Autopsja daje dokładny czas.

Mag ma tylko dziesięć slotów, więc jego zestaw **zostawia podpis**. Trzeci
trup ze śladem ognia mówi, kogo ścigacie — a on nie może zmienić stylu,
bo wziął, co wziął.

### Osad w przedziale

Rzucanie zostawia ślad szkoły, blednący przez 90 s. Mówi „tu rzucano
ogniem", nie mówi kto. Wykrywacz Inkwizytora czyta osad z całego aktu.

Mrok kasuje osad i podrzuca fałszywy.

---

## 6. Trybunał

Odpala się, gdy komuś uda się **związać ogłuszonego** (kanał 1.8 s, z
Kajdanami 0.9 s). Świat staje.

Ekran pokazuje **oskarżonego i tego, kto go związał**. Nic więcej. Gra nie
wykłada dowodów — dowody są w tym, co ludzie mówią na Discordzie. Inaczej
trybunał zrobiłby się automatem do liczenia zamiast rozmową.

* 60 s na dyskusję i głos.
* Do wyroku trzeba **większości żywych** na „tak".
* Remis, wstrzymania i brak większości → wypuszczony.
* Głosy **jawne po rozstrzygnięciu** — kto jak głosował, jest dowodem.
* Mag głosuje razem ze wszystkimi i może odpalić trybunał sam.

Wyrok: do bazy, na stałe. Jeśli to był mag, runda kończy się natychmiast.

Blokady: **120 s** przerwy między trybunałami, **60 s** nietykalności dla
wypuszczonego.

Konsekwencja zostawiona celowo: przy dwóch łowcach i magu wystarczy, że
mag zagłosuje z jednym łowcą przeciw drugiemu — i wygrywa. Im mniej was
zostaje, tym bardziej oskarżanie jest samobójstwem.

Wyniku nie da się ukryć: wyrzucenie maga kończy rundę, więc brak końca
rundy jest natychmiastowym komunikatem „pomyliliście się". Nie ma tu
pokrętła do kręcenia.

---

## 7. Baza

Zabici i wyrzuceni idą do bazy i **dostają robotę**.

Widzą schemat stacji i **dwa podglądy kamer naraz — każdy z osobna,
z jednego wspólnego zestawu kamer**. Na
kamerach są **sylwetki klas, nigdy imiona** — przebranie i Fałszywa
sylwetka oszukują bazę tak samo jak żywych.

Czasowniki:

| Czynność | Koszt |
|---|---|
| przełączenie kamery | za darmo |
| otwarcie/zamknięcie drzwi | z puli aktu |
| awaryjne światło w przedziale na 20 s | z puli aktu |

Pula jest **wspólna dla całej bazy** i wynosi 6 użyć na akt, nie na głowę.
Inaczej piąty trup zrobiłby z bazy wieżę kontroli lotów.

W akcie III połowa kamer pada. Baza rośnie w ludzi, ale traci oczy.

**Nikt w bazie nigdy nie dowiaduje się, kto jest magiem.** Nawet zabity
widzi tylko klasę rzucającego, a ta mogła być fałszywa. Dlatego mogą
rozmawiać na Discordzie do woli — to nie jest łamanie zasad, tylko ich
rola. Rozwiązuje to problem, którego inaczej nie da się wyegzekwować:
przy głosie poza grą martwi i tak by gadali.

---

## 8. Pingi

Przytrzymanie palcem. Na graczu: **podejrzany** — znacznik nad nim na
20 s. Na przedziale: **czysto**, **byłem tu**, **zwłoki**.

Każdy ping jest **podpisany** — widać, kto go postawił. To cała jego siła
i całe ryzyko. Mag pinguje tak samo i kłamie pingiem; to przewidziane.

Jeden ping na 8 s na gracza.

---

## 9. Wybór przed rundą

Ekran wyboru: klasa (przydzielana losowo z unikalnych), wyposażenie
klasy, a dla maga dodatkowo dziesięć slotów księgi.

**Timer 90 s i losowy fallback.** Przy ośmiu graczach jeden niezdecydowany
nie może blokować wszystkich.

Dziesięć slotów z 24 zaklęć w 90 sekund na telefonie to za dużo klikania,
więc księga ma **gotowe zestawy** — Rzeźnik, Budowlaniec, Oszust — jednym
dotknięciem, do dowolnej przeróbki. Fallback losuje jeden z nich.

Przy pięciu graczach używanych jest pięć z ośmiu klas, losowo. Reszta nie
występuje w rundzie i nie może paść w rejestrze — co samo w sobie jest
informacją, i tak ma być.

Mag przechodzi ten sam ekran co łowcy plus zakładkę księgi, więc czas
spędzony na ekranie niczego o nim nie zdradza.

---

## 10. Architektura

Obecny `server.js` ma 601 linii i trzyma wszystko. Ten projekt tego nie
udźwignie — rozbijam na moduły o jednej odpowiedzialności każdy:

```
wizard-hunt-online/
  server.js          # http + websocket, nic więcej
  src/
    rules.js         # stałe i strojenie
    classes.js       # 8 klas + 24 przedmioty
    spells.js        # 24 zaklęcia jako dane
    room.js          # stan pokoju, gracze, cykl życia
    round.js         # akty, artefakty, warunki zwycięstwa
    evidence.js      # rejestry, ślady, osady
    tribunal.js      # pojmanie → głosowanie → wyrok
    base.js          # martwi: kamery, drzwi, światła
    snapshot.js      # cięcie widoczności per gracz + serializacja
  public/
    index.html, client.js, loadout.js, assets/
```

Zasada, która nie może paść: **serwer jest autorytatywny, łącznie z
mgłą**. Widoczność jest cięta per gracz **przed** serializacją migawki,
więc zdjęcie nakładki po stronie klienta nie odsłania niczego. Rejestry,
ślady i podglądy bazy idą tą samą drogą — klient dostaje to, co gracz ma
prawo wiedzieć, i nic więcej.

## 11. Testy

Skryptowane boty na WebSockecie, tak jak przy poprzedniej wersji.

Pokrycie:

* przejścia między aktami, w tym po czasie i po zabraniu artefaktów
* tracenie artefaktów na czas, Pożogą i Zawałem
* zamknięcie ścieżki artefaktowej przy czwartym straconym
* trybunał: większość, remis, wstrzymania, wyrzucenie maga, wyrzucenie
  niewinnego, blokady czasowe
* rejestr: poprawność wpisów, Przebranie wpisujące cudzą klasę,
  Wymazanie, Filtr odporny na wymazanie
* ładunki: wyczerpanie zaklęcia, przerwanie rzutu tazerem zjadające ładunek
* migawka: żaden gracz ani baza nie dostaje danych spoza swojego zasięgu
  ani tożsamości maga

Do tego poligon dla jednego gracza na wyczucie zasięgów i ciemności
aktu III.

## 12. Czego tu nie ma

* Dźwięku.
* Trwałych lobby i powrotu po rozłączeniu — przy 30-minutowej rundzie i
  sieci komórkowej to będzie potrzebne, ale nie w pierwszym podejściu.
* Więcej niż jednego maga. Przy 8 graczach niepotrzebne; przy 12 byłoby.
* Interakcji między szkołami (woda przewodzi piorun, powietrze podsyca
  ogień). Kuszące, ale to warstwa na później.
