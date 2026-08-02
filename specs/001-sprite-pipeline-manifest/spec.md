# Feature Specification: Manifest sprite'ów i warstwa nieoświetlana

**Feature Branch**: `claude/plugin-installation-3oluvd`

**Created**: 2026-08-02

**Status**: Draft

**Input**: Przebudowa pipeline'u sprite'ów łowców w "I'm Not a Wizard, Harry" wzorowana na Space Station 14 (format RSI), zamiast arkusza indeksowanego arytmetyką. Priorytet: manifest zamiast wzoru na indeks (1) oraz warstwa emisyjna nieprzygaszana przez ciemność (2). Punkty 3–5 opisane jako dalsze etapy.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Sylwetka zawsze zgadza się z osobą (Priority: P1)

Gracz widzi na ekranie łowcę. Klasa i sprzęt, które widzi, są tymi, które
serwer o tej osobie mówi — i pozostają zgodne po każdej zmianie tabeli klas
albo listy przedmiotów. Jeżeli grafika i tabela się rozjadą, gra mówi o tym
głośno przy starcie, zamiast po cichu rysować komuś cudze ciało.

To jest ta historia, która broni całej reszty gry. Klasy są unikalne w
rundzie, więc rozpoznanie klasy z drugiego końca przedziału **jest dowodem**.
Sylwetka pokazująca nie tę osobę nie jest błędem kosmetycznym — to sfałszowany
dowód, którego nikt przy stole nie ma jak zakwestionować.

**Why this priority**: Błąd jest cichy, a jego skutkiem jest niesłuszne
skazanie na trybunale. Żaden inny punkt tej specyfikacji nie ma znaczenia,
dopóki widok nie jest wiarygodny.

**Independent Test**: Przestawić kolejność przedmiotów w jednej klasie,
zregenerować grafikę, uruchomić zestaw testów i grę. Oczekiwany wynik: gra
rysuje poprawnie, bo szuka stanu po nazwie. Usunąć jeden stan z grafiki bez
aktualizacji manifestu: testy padają z komunikatem wskazującym brakujący stan.

**Acceptance Scenarios**:

1. **Given** tabela klas z nienaruszoną kolejnością, **When** gracz patrzy na
   Chirurga ze Stabilizatorem, **Then** widzi Chirurga ze Stabilizatorem.
2. **Given** przestawiona kolejność przedmiotów Technika, **When** grafika
   zostaje zregenerowana i gra uruchomiona, **Then** każdy łowca nadal ma
   swoje ciało i swój sprzęt, bez żadnej zmiany po stronie klienta.
3. **Given** manifest opisujący stan, którego nie ma w arkuszu, **When**
   uruchamiany jest zestaw testów, **Then** test pada i nazywa brakujący stan.
4. **Given** mag pod przebraniem, **When** ktoś na niego patrzy, **Then**
   widzi klasę i sprzęt przebrania, a nie własne maga.
5. **Given** nazwa stanu, której manifest nie zna, **When** klient ma ją
   narysować, **Then** rysuje udokumentowany zastępnik i zgłasza to raz, a nie
   po cichu wybiera przypadkowy wiersz.

---

### User Story 2 - Ciemność ma punkty światła (Priority: P1)

W Akcie III wrak ciemnieje. Gracz nadal widzi, że lampka na piersi łowcy się
świeci, wizjer Strażnika jest podświetlony, a Technik niesie zapaloną lampę.
Ciemność robi się **gęstsza**, a nie po prostu bardziej szara.

**Why this priority**: Akt III to mechanika, wokół której zbudowana jest cała
końcówka rundy, a dziś lampka gaśnie razem z ciałem, które ją niesie. Przez to
najciemniejszy akt czyta się jak akt pierwszy z filtrem, zamiast jak wrak bez
prądu. Poprawka jest widoczna natychmiast i nie rusza żadnej zasady gry.

> **Sprostowanie z fazy badawczej**: pierwsza wersja tej historii mówiła, że
> to akt przygasza sylwetki. Nieprawda — akt jedynie zawęża promień widzenia,
> a wygaszenie przedziału (Zgaszenie) dotyka podłogi, nie ludzi na niej.
> Jedyne, co przygasza łowcę, to mgła, i robi to płasko: lampa na skraju
> widzenia blaknie dokładnie tak szybko jak ciało, które ją trzyma. Skutek
> opisany w tej historii zostaje bez zmian, przyczyna była nazwana błędnie.
> Szczegóły w [research.md](./research.md), R1.

**Independent Test**: Stanąć tak, by inny łowca był na skraju widzenia, i
porównać jasność jego pikseli emisyjnych z jasnością jego korpusu. Bez zmiany
mgła przygasza jedno i drugie tak samo; po zmianie korpus blaknie, a piksele
emisyjne zostają.

**Acceptance Scenarios**:

1. **Given** łowca na skraju promienia widzenia, **When** jest rysowany,
   **Then** jego elementy emisyjne mają pełną jasność, a reszta sylwetki jest
   przygaszona przez mgłę.
2. **Given** przedział w pełnym świetle, **When** rysowany jest ten sam
   łowca, **Then** wygląda tak jak dotychczas — zmiana nie może być widoczna
   przy pełnym świetle.
3. **Given** mag pod zaklęciem Cień, **When** patrzy na własne ciało,
   **Then** elementy emisyjne są przezroczyste dokładnie tak jak reszta
   sylwetki i nie zdradzają jego pozycji.
4. **Given** zwłoki w ciemnym przedziale, **When** ktoś je widzi, **Then**
   ich elementy emisyjne są zgaszone — martwy sprzęt nie świeci.

---

### User Story 3 - Kolor mówi najpierw o dziale (Priority: P2)

Gracz rozpoznaje najpierw grupę — bojowi, technicy, wsparcie — a dopiero
potem konkretną osobę. Osiem osobnych barw to osiem rzeczy do zapamiętania;
trzy pasma dają szybszy pierwszy odczyt, nie odbierając sylwetkom
unikalności.

**Why this priority**: Realna poprawa czytelności na telefonie, ale gra jest
grywalna bez niej. Zależy od tego, żeby zmiana koloru nie wymagała
regenerowania grafiki, więc naturalnie idzie po etapie pierwszym.

**Independent Test**: Zmienić przypisanie klasy do pasma w jednym miejscu
konfiguracji, odświeżyć grę bez regenerowania grafiki i zobaczyć nowy kolor
płaszcza.

**Acceptance Scenarios**:

1. **Given** zmienione przypisanie barwy klasy, **When** gra jest odświeżona
   bez uruchamiania generatora, **Then** płaszcz ma nowy kolor.
2. **Given** trzy pasma barw, **When** gracz widzi dwóch łowców z tego samego
   pasma, **Then** nadal rozróżnia ich po sylwetce i nakryciu głowy.

---

### User Story 4 - Widać, czy ktoś niesie, czy używa (Priority: P2)

Gracz odróżnia sprzęt schowany przy pasie od sprzętu trzymanego w dłoni.
"Niesie stabilizator" i "właśnie używa stabilizatora" to dwie różne
obserwacje, i obie są dowodem innego rodzaju.

**Why this priority**: Dokłada nową informację do gry dowodowej, ale wymaga
rozbicia przedmiotu na osobne grafiki, więc jest droższa niż etapy
wcześniejsze.

**Independent Test**: Użyć przedmiotu i sprawdzić, że sylwetka na czas
użycia pokazuje go w dłoni, a poza tym czasem przy pasie.

**Acceptance Scenarios**:

1. **Given** łowca z przedmiotem aktywnym, **When** nie używa go, **Then**
   przedmiot widnieje przy pasie.
2. **Given** ten sam łowca, **When** trwa użycie albo kanałowanie,
   **Then** przedmiot jest w dłoni.

---

### User Story 5 - Leżący wygląda na leżącego (Priority: P3)

Gracz rozpoznaje powalonego albo ogłuszonego łowcę po samej sylwetce, z
drugiego końca przedziału, bez czytania ikony nad głową.

**Why this priority**: Czysty zysk czytelności, zerowy koszt grafiki — obrót
istniejącej klatki. Najniższy priorytet, bo dzisiejsza ikona działa, tylko
wymaga przeczytania.

**Independent Test**: Powalić bota i sprawdzić, że jego sylwetka jest
pozioma, zanim jakikolwiek tekst zostanie przeczytany.

**Acceptance Scenarios**:

1. **Given** powalony łowca, **When** ktoś go widzi, **Then** sylwetka jest
   obrócona do poziomu.
2. **Given** łowca podniesiony Stabilizatorem, **When** wstaje, **Then**
   sylwetka wraca do pionu.

### Edge Cases

- **Manifest i grafika rozjechane w drugą stronę**: arkusz zawiera stan,
  którego manifest nie opisuje. To zmarnowane piksele, nie błąd renderowania,
  ale zestaw testów ma to zgłosić — najczęściej znaczy, że ktoś zapomniał
  zregenerować manifest.
- **Serwer podaje klasę spoza manifestu**: musi istnieć jeden udokumentowany
  zastępnik i jedno zgłoszenie, nie ciche wybranie wiersza zero za każdą
  klatkę.
- **Przebranie**: nazwa stanu składa się z klasy pozornej i przedmiotu
  pozornego; prawdziwa klasa maga nie może wyciec do nazwy stanu.
- **Cień a warstwa emisyjna**: przezroczystość postaci obowiązuje również
  warstwę emisyjną. Warstwa, która ignoruje ciemność, nie może ignorować
  niewidzialności, bo zaklęcie przestaje działać dokładnie tam, gdzie jest
  potrzebne.
- **Podgląd bazy**: kamery rysują te same sylwetki. Muszą korzystać z tego
  samego manifestu i tej samej reguły emisyjnej, inaczej baza i pole widzą
  dwie różne gry.
- **Tryb artefaktu**: manifest musi dać się wbudować w pojedynczy plik HTML
  razem z grafiką, bo tam nie wolno niczego pobrać.
- **Brak manifestu**: gra nie może wystartować i pokazywać przypadkowych
  ciał; brak manifestu to błąd startu z czytelnym komunikatem.
- **Zwłoki i fałszywa sylwetka**: obie rysowane są z tego samego arkusza i
  muszą mieć poprawną nazwę stanu, łącznie ze sfałszowanym sprzętem.

## Requirements *(mandatory)*

### Functional Requirements

**Etap 1 — manifest (P1)**

- **FR-001**: Generator grafiki MUSI wytwarzać obok arkusza opis
  maszynowo-czytelny, wymieniający każdy rysowalny stan po nazwie wraz z jego
  położeniem, liczbą kierunków, liczbą klatek i rozmiarem klatki.
- **FR-002**: Nazwa stanu MUSI składać się z nazwy klasy i identyfikatora
  przedmiotu, czyli z wartości, które i tak krążą między serwerem a klientem —
  nigdy z pozycji w tabeli.
- **FR-003**: Klient MUSI rozwiązywać sprite po nazwie stanu. Żadne miejsce w
  kodzie nie może liczyć wiersza z pozycji klasy ani przedmiotu.
- **FR-004**: Stan, o który klient prosi, a którego opis nie zna, MUSI zostać
  narysowany udokumentowanym zastępnikiem i zgłoszony dokładnie raz na sesję.
- **FR-005**: Zestaw testów MUSI wykrywać niezgodność opisu z arkuszem w obie
  strony: stan opisany, ale nieobecny w grafice, oraz obszar grafiki, którego
  opis nie wymienia.
- **FR-006**: Przestawienie kolejności klas albo przedmiotów w tabeli MUSI
  pozostawać bez wpływu na to, co widzi gracz, po samej regeneracji grafiki i
  bez żadnej zmiany w kliencie.
- **FR-007**: Opis MUSI dawać się wbudować w jednoplikową wersję gry razem z
  grafiką, bez pobierania czegokolwiek w czasie działania.
- **FR-008**: Brak opisu albo opis nieczytelny MUSI zatrzymać start gry z
  komunikatem nazywającym problem, zamiast rysować cokolwiek.
- **FR-009**: Dotychczasowy test czytający nagłówek pliku graficznego MUSI
  zostać zastąpiony testem zgodności opisu z arkuszem, który wykrywa również
  zmianę kolejności, a nie tylko zmianę rozmiaru.

**Etap 2 — warstwa emisyjna (P1)**

- **FR-010**: Generator MUSI wydzielać piksele świecące własnym światłem jako
  osobną warstwę, odrębną od korpusu sylwetki.
- **FR-011**: Warstwa emisyjna MUSI być rysowana po mgle, zachowując pełną
  jasność niezależnie od odległości od patrzącego i od aktu.
- **FR-011a**: *Poza zakresem, zapisane, żeby nie zginęło.* Wygaszony
  przedział nie przygasza dziś stojących w nim ludzi — pokój ciemnieje wokół
  w pełni oświetlonych łowców. To osobna usterka, znaleziona przy okazji, i
  wymaga własnej decyzji: żeby ją naprawić, trzeba przygaszać sylwetki
  światłem przedziału, czego renderer w ogóle jeszcze nie robi.
- **FR-012**: Warstwa emisyjna MUSI podlegać przezroczystości postaci, tak by
  niewidzialność pozostała pełna.
- **FR-013**: Zwłoki MUSZĄ być rysowane bez warstwy emisyjnej.
- **FR-014**: Przy pełnym oświetleniu wygląd postaci MUSI pozostać
  nieodróżnialny od dzisiejszego.
- **FR-015**: Podgląd bazy MUSI stosować tę samą regułę emisyjną co widok
  pola.

**Etap 3 — barwa w czasie działania (P2)**

- **FR-016**: Barwa płaszcza MUSI dać się zmienić bez regenerowania grafiki.
- **FR-017**: Klasy MUSZĄ dać się przypisać do wspólnych pasm barw, przy
  zachowaniu unikalnych sylwetek.

**Etap 4 — sprzęt w dłoni (P2)**

- **FR-018**: Przedmiot MUSI mieć rozróżnione przedstawienie schowane i
  trzymane w dłoni.
- **FR-019**: Przedstawienie w dłoni MUSI pojawiać się na czas użycia albo
  kanałowania przedmiotu.

**Etap 5 — postawa (P3)**

- **FR-020**: Powalony albo ogłuszony łowca MUSI być pokazany poziomą
  sylwetką, bez dodatkowej grafiki.

### Key Entities

- **Opis arkusza (manifest)**: spis wszystkich rysowalnych stanów. Zna
  rozmiar klatki, wersję formatu i listę stanów. Jest jedynym źródłem prawdy o
  tym, gdzie w grafice co leży.
- **Stan**: jedna nazwana pozycja w opisie — klasa plus przedmiot. Ma
  kierunki i klatki animacji. Nazwa jest kluczem; położenie jest szczegółem
  wewnętrznym.
- **Warstwa**: część sylwetki rysowana osobno, bo rządzi się inną regułą.
  Dziś dwie: korpus, który ciemnieje razem z przedziałem, i emisyjna, która
  nie. W etapie trzecim dochodzi warstwa barwiona.
- **Klasa pozorna i przedmiot pozorny**: to, co widzi obserwator. Pod
  przebraniem różnią się od prawdziwych i tylko one mogą trafić do nazwy
  stanu.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Przestawienie kolejności klas albo przedmiotów w tabeli i
  zregenerowanie grafiki nie wymaga **ani jednej** zmiany w kodzie klienta, a
  gracz nadal widzi właściwe ciała i sprzęt.
- **SC-002**: Niezgodność opisu z grafiką jest wychwytywana przez zestaw
  testów przed uruchomieniem gry, w obu kierunkach niezgodności, i komunikat
  nazywa konkretny stan.
- **SC-003**: Dodanie czwartego przedmiotu do dowolnej klasy wymaga zmiany w
  jednej tabeli i uruchomienia generatora — zero zmian w kliencie i zero
  zmian w liczbach gdziekolwiek indziej.
- **SC-004**: Na skraju promienia widzenia element świecący na sylwetce jest
  co najmniej trzykrotnie jaśniejszy od sąsiadującego z nim korpusu tej samej
  postaci.
- **SC-005**: Postać pod zaklęciem niewidzialności nie ma na sobie ani
  jednego piksela jaśniejszego niż reszta jej sylwetki.
- **SC-006**: Przy pełnym oświetleniu porównanie klatek sprzed i po zmianie
  nie wykazuje różnicy.
- **SC-007**: Jednoplikowa wersja gry nadal działa bez sieci i nie rośnie o
  więcej niż 5 KB względem dzisiejszej.
- **SC-008**: Cały zestaw testów wykonuje się w czasie nie dłuższym niż dziś,
  liczonym z dokładnością do sekundy.

## Assumptions

- Wzorem jest **format danych** Space Station 14 (RSI: opis obok grafiki,
  stany nazwane, kierunki i klatki zadeklarowane), nie jego silnik. Nie
  przenosimy architektury encji ani shaderów.
- Klient pozostaje rysowaniem na płótnie 2D w czystym JS, serwer to Node z
  gniazdami. Bez kroku budowania i bez nowych zależności zewnętrznych.
- Grafika nadal powstaje proceduralnie w Pythonie z Pillow. Generator jest
  jedynym miejscem, które wie, gdzie co narysował, więc to on wypisuje opis —
  opis pisany ręcznie byłby tą samą pułapką co dziś, tylko w innym pliku.
- Zostaje dzisiejszy podział na cztery kierunki i dwie klatki chodu. Format
  ma to deklarować, a nie zakładać, żeby ósmy kierunek albo trzecia klatka
  nie wymagały ruszania klienta.
- Etap trzeci nie zmienia poświaty przypisanej klasom, używanej dziś w
  interfejsie i na podglądzie bazy — pasma barw dotyczą wyłącznie dużej
  powierzchni płaszcza. Dzięki temu zmiana jest odwracalna i nie rusza
  czytelności elementów interfejsu.
- Zmiana jest w całości wizualna i formatowa. **Żadna zasada gry nie ulega
  zmianie**: widoczność sprzętu, przebranie, mgła i dowody działają dokładnie
  tak jak dziś. Jedyna nowa informacja dla gracza w etapach 1–2 to fakt, że
  świecące elementy przestają gasnąć razem z otoczeniem.
- Etapy 3–5 są opisane, ale nie wchodzą do pierwszego wydania tej zmiany.
  Etapy 1 i 2 są niezależne od siebie i dają się wydać osobno.
