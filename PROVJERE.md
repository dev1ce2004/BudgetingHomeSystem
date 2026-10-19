# Provjere prve verzije

Prošlo je 7 integracijskih testova: autorizacija, duplikati i sukobi, vidljivost i ovlasti, vlastito uređivanje/brisanje i opoziv, validacija, integritet sigurnosne kopije, postavke i izvoz.

Prošla je HTTPS provjera s validacijom lokalnog CA certifikata za HTML, JavaScript, service worker, manifest i PNG ikone. Python i JavaScript sintaksa prolaze provjere.

Automatizirana provjera sučelja nije izvedena: razvojno okruženje nema Chromium izvršnu datoteku. Windows instalacija i stvarni Android offline rad nisu potvrđeni.

Prije stvarnih podataka: instaliraj certifikate, poveži dva korisnika, unesi trošak, provjeri zajednički pregled, ugasi Wi-Fi, dodaj novi unos, zatvori i ponovno otvori aplikaciju te uključi Wi-Fi. Unos se mora pojaviti na računalu jednom. Provjeri sukob izmjena i povrat iz sigurnosne kopije na probnim podacima. Koristi jednu otvorenu karticu aplikacije po uređaju kako bi se izbjegle istodobne izmjene lokalnog reda slanja.
