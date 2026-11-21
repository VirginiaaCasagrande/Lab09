from database.parco_DAO import ParcoDAO
from database.escursione_DAO import EscursioneDAO
from database.punto_interesse_DAO import PuntoInteresseDAO

class Model:
    def __init__(self):
        self.escursioni_map = {} # Mappa ID escursione -> oggetti Escursione
        self.punti_interesse_map = {} # Mappa ID punto di interesse -> oggetti PuntoInteresse

        self._pacchetto_ottimo = []
        self._valore_ottimo: int = -1
        self._costo = 0

        # TODO: Aggiungere eventuali altri attributi

        # Caricamento
        self.load_escursioni()
        self.load_punti_interesse()
        self.load_relazioni()

    @staticmethod
    def load_parchi():
        """ Restituisce tutti i parchi disponibili """
        return ParcoDAO.get_parchi()

    def load_escursioni(self):
        """ Carica tutte le escursioni in un dizionario [id, Escursione]"""
        self.escursioni_map = EscursioneDAO.get_escursioni()

    def load_punti_interesse(self):
        """ Carica tutti i punti di interesse in un dizionario [id, PuntoInteresse]"""
        self.punti_interesse_map = PuntoInteresseDAO.get_punti_interesse()

    def load_relazioni(self, punti_interesse=None):
        """
            Interroga il database per ottenere tutte le relazioni fra escursioni e punti di interesse e salvarle nelle strutture dati
            Collega escursione <-> punti di interesse.
            --> Ogni Escursione ha un set di PuntoInteresse.
            --> Ogni PuntoInteresse ha un set di Escursioni.
        """
        # Recupero tutte le relazioni N:N tramite il DAO
        relazioni = EscursioneDAO.get_escursioni_punti_interesse()

        if relazioni is None:
            return

        for relazione in relazioni:
            # Estraggo gli ID dalla relazione che sto considerando
            id_escursione = relazione['id_escursione']
            id_punto_interesse = relazione['id_punto_interesse']

            # Recupero gli oggetti dai rispettivi dizionari tramite l'ID (chiave)
            escursione = self.escursioni_map[id_escursione]
            punto_interesse=self.punti_interesse_map[id_punto_interesse]

            # Creo il collegamento tra l'escursione e il punto di interesse andando a popolare i set dei singoli oggetti
            escursione.punti_interesse.add(punto_interesse)
            punto_interesse.escursioni.add(escursione)



    def genera_pacchetto(self, id_parco: str, max_giorni: int = None, max_budget: float = None):
        """
        Calcola il pacchetto di escursioni ottimale per un parco rispettando i vincoli di durata, budget e punti di interesse unici.
        :param id_parco: id del parco
        :param max_giorni: numero massimo di giorni (può essere None --> nessun limite)
        :param max_budget: costo massimo del pacchetto (può essere None --> nessun limite)

        :return: self._pacchetto_ottimo (una lista di oggetti Escursione)
        :return: self._costo (il costo del pacchetto)
        :return: self._valore_ottimo (il voto complessivo dei visitatori per il pacchetto)
        """
        self._pacchetto_ottimo = []
        self._costo = 0
        self._valore_ottimo = -1



        escursioni_per_parco = []  #lista contenente solo le escursioni del parco selezionato

        for escursione in self.escursioni_map.values():
            #controllo se l'escursione appartiene al parco richiesto
            if escursione.id_parco == id_parco:
                escursioni_per_parco.append(escursione)

        self._ricorsione(0,[], 0, 0.0,0,set(), escursioni_per_parco, max_giorni, max_budget)


        return self._pacchetto_ottimo, self._costo, self._valore_ottimo

    def _ricorsione(self, start_index: int, pacchetto_parziale: list, durata_corrente: int, costo_corrente: float, valore_corrente: int, punti_usati: set, escursioni_per_parco,max_giorni, max_budget):
        """ Algoritmo di ricorsione che deve trovare il pacchetto che massimizza il voto complessivo dei visitatori"""

        if self._valore_ottimo == -1 or valore_corrente > self._valore_ottimo:
            self._valore_ottimo = valore_corrente
            self._pacchetto_ottimo = pacchetto_parziale.copy()
            self._costo = costo_corrente


        # Condizioni di terminazione:
        if start_index == len(escursioni_per_parco):   # Ho terminato le escursioni da valutare offerte dal singolo parco
            return

        for i in range (start_index, len(escursioni_per_parco)):
            escursione = escursioni_per_parco[i]

            nuova_durata = durata_corrente + escursione.durata_giorni
            nuovo_costo = costo_corrente + escursione.costo

            durata_valida = True
            if max_giorni is not None:
                if nuova_durata > max_giorni:
                    durata_valida = False

            costo_valido = True
            if max_budget is not None:
                if nuovo_costo > max_budget:
                    costo_valido = False

            punti_validi = True
            for punto in escursione.punti_interesse:
                if punto in punti_usati:
                    punti_validi = False

            if durata_valida and costo_valido and punti_validi:
                pacchetto_parziale.append(escursione)

                nuovi_punti_usati = punti_usati.copy()

                for punto in escursione.punti_interesse:
                    nuovi_punti_usati.add(punto)

                nuovo_valore = valore_corrente

                for punto in escursione.punti_interesse:
                    nuovo_valore+=punto.voto_visitatori

                self._ricorsione (i +1, pacchetto_parziale, nuova_durata, nuovo_costo, nuovo_valore, nuovi_punti_usati, escursioni_per_parco, max_giorni, max_budget )
                pacchetto_parziale.pop()

        # TODO: è possibile cambiare i parametri formali della funzione se ritenuto opportuno
