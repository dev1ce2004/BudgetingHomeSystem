# Kućni budžet — BudgetingHomeSystem

Prva lokalna verzija: Windows hub i Android PWA, zajednički pregled, prihodi/troškovi/prijenosi, kategorije, računi, mjesečni limit, korisnici, opoziv pristupa, lokalna offline evidencija, sinkronizacija s verzijama, izvoz i sigurnosne kopije. Baza je na Windows računalu. Ne koristi vanjski server. Android aplikacija nije zasebni APK; instalira se iz preglednika nakon postavljanja certifikata.

## 1. Windows instalacija

1. Raspakiraj cijeli paket u stalnu mapu, npr. `C:\BudgetingHomeSystem`. Nemoj pokretati iz ZIP-a.
2. Potreban je Python 3.10 ili noviji s python.org i naredba `py`. Pokreni `Instaliraj.bat`. Internet je potreban za instalaciju ovisnosti, ne za korištenje.
3. Pokreni `Pokreni.bat`. Ostavi prozor otvoren. Ispisat će kućnu HTTPS adresu. Ako je IP pogrešan (VPN, više adaptera), provjeri IPv4 kućne mreže naredbom `ipconfig` i pokreni `Pokreni.bat --ip 192.168.1.123`, sa svojom adresom.
4. U Windows firewallu dopusti Python samo na privatnoj mreži. Ako je potrebno, ručno dodaj dolazno TCP pravilo za 8443, profil Private i udaljene adrese Local subnet. Ne otvaraj port na routeru.
5. Instaliraj `data\BudgetingHomeSystem-CA.crt` u certifikate **Current User → Trusted Root Certification Authorities**. Provjeri da je to certifikat koji je ova instalacija upravo generirala.
6. Pokreni `Otvori-hub.bat`. Prvi administrator već postoji. Tajna poveznica je u `data\admin-access.txt`; nemoj je dijeliti članovima.

Računalo mora biti uključeno i budno za sinkronizaciju. Preporučuje se rezervirati njegov IP u DHCP postavkama routera, kako se adresa ne bi mijenjala. Pristupni ključevi daju pristup financijskim podacima — čuvaj ih kao lozinke.

## 2. Android povezivanje

1. Na desktopu otvori **Postavke → Članovi kućanstva**, upiši ime i dodaj člana. Dobivaš njegovu osobnu poveznicu. Pošalji je tom članu ručno.
2. Prenesi samo javni `BudgetingHomeSystem-CA.crt` na mobitel. Nikad ne prenosi `server-key.pem`, bazu ni administratorsku poveznicu.
3. U postavkama Androida instaliraj certifikat kao **CA certifikat**. Naziv izbornika ovisi o proizvođaču (Sigurnost → Šifriranje i vjerodajnice → Instaliraj certifikat). Android će tražiti potvrdu jer dodaješ lokalni izvor povjerenja.
4. Poveži mobitel na isti kućni Wi-Fi i otvori člansku poveznicu u Chromeu. Adresa mora biti ona s IP-om računala, ne localhost. Certifikat mora biti prihvaćen bez upozorenja. Samo zaobilaženje upozorenja ne jamči offline rad.
5. U izborniku preglednika odaberi **Instaliraj aplikaciju / Dodaj na početni zaslon**, ako preglednik to ponudi. PWA radi i u običnoj kartici. Prvo otvaranje i preuzimanje zajedničkih podataka mora biti dok je računalo dostupno.
6. Za offline provjeru pričekaj prvu uspješnu sinkronizaciju, zatvori aplikaciju, isključi Wi-Fi i ponovno je otvori. Dodaj trošak; mora pisati da čeka sinkronizaciju. Vrati Wi-Fi i otvori aplikaciju: unos se treba pojaviti na desktopu točno jednom.

Svi vide sve transakcije. Član uređuje svoje, administrator sve. Sinkronizacija radi pri otvaranju, povratku u aplikaciju, nakon unosa te svakih 30 sekundi dok je aplikacija aktivna. Nije implementirana sinkronizacija dok je Android aplikacija potpuno zatvorena.

## 3. Sukobi i neposlani unosi

Ponavljanje istog slanja ne stvara duplikate. Ako je transakcija već promijenjena na drugom uređaju, sinkronizacija je ne prepisuje. Otvori **Uredi** na konfliktnom unosu: prikazuje se verzija računala; prihvati je ili pregledaj i ponovno spremi svoju. Ostali unosi iza sukoba čekaju njegovo rješavanje.

Ne briši podatke preglednika, ne deinstaliraj PWA i ne mijenjaj adresu dok ima neposlanih unosa. Podaci preglednika su vezani za adresu. Izvoz JSON sadrži i neposlane unose; u prvoj verziji nema automatskog uvoza tog izvoza.

## 4. Sigurnosne kopije i vraćanje

Baza je `data\budget.sqlite3`. Kopija nastaje pri pokretanju i svaki sat, u `data\backups\YYYY-MM-DD.sqlite3`; jedna dnevna kopija osvježava se tijekom dana. Gumb u postavkama radi dodatnu kopiju tog dana.

Kopiraj cijelu mapu `data` na drugi disk, osobito bazu i certifikat. Kopije baze sadrže pristupne ključeve; zaštiti ih. Za vraćanje: zaustavi servis, sačuvaj trenutnu bazu, kopiraj odabranu kopiju preko `data\budget.sqlite3` i pokreni servis. Nakon vraćanja stare kopije provjeri sve uređaje: stanje njihovih lokalnih pregleda i potvrđenih unosa može biti novije od vraćene baze. Napravi izvoz s uređaja prije usklađivanja.

## 5. Automatsko pokretanje

Nakon uspješnog ručnog rada pokreni PowerShell i izvrši `powershell -ExecutionPolicy Bypass -File .\Autopokretanje.ps1` iz mape projekta. Pokreće se nakon prijave u Windows, ne prije prijave. Prozor nije otvoren. Nemoj istovremeno pokretati drugu instancu. Uklanjanje: Win+R → `shell:startup` → izbriši BudgetingHomeSystem prečac. Za zaustavljanje pozadinske instance koristi Task Manager i identificiraj pythonw proces ovog projekta.

## 6. Ograničenja prve verzije

- Certifikat servera traje godinu dana. Za obnovu, uz zaustavljen servis, izbriši `data\cert-ip.txt` i ponovno pokreni servis. Stvara se novi CA; treba zamijeniti stari certifikat na svim uređajima. Isto vrijedi nakon promjene IP-a.
- Lokalni cache na mobitelu nije šifriran ovom aplikacijom; oslanja se na zaštitu uređaja. Opoziv pristupa zaustavlja daljnju sinkronizaciju, ali ne briše podatke već preuzete na uređaj.
- Jedan pristupni ključ po članu; opoziv vrijedi za sve uređaje tog člana. Za novi pristup dodaj novog člana. QR uparivanje nije uključeno.
- Nema zasebnog APK-a/EXE instalera, bankovne integracije, fotografija računa, ponavljajućih računa, budžeta po kategoriji ni evidencije početnih stanja računa. Računi služe razvrstavanju transakcija, mjesečna razlika nije ukupno stanje imovine.
- Prva verzija je testirana u razvojnom okruženju; instalacija, Android certifikati i offline rad moraju se dodatno provjeriti na tvojim stvarnim uređajima.

## Razvoj i testovi

`python -m unittest discover -s tests -v`
Za testiranje samo na istom računalu možeš koristiti `python server.py --http --port 8443`; taj način sluša isključivo localhost i ne omogućuje Android PWA preko mreže.
