import sys
import math
import collections
import csv
import time
import json
import requests
import certifi
import datetime, dateutil.parser
from decimal import Decimal
from datetime import datetime

def mean(dict_of_values): # media
    return sum(dict_of_values.values()) / max(len(dict_of_values), 1)

def variance(dict_of_values, mean_of_values): # varianza, necessaria per il calcolo della deviazione standard
    n = len(dict_of_values)
    deviations = [(x - mean_of_values) ** 2 for x in dict_of_values.values()]
    variance = sum(deviations) / max(n, 1)
    return variance

def sdev(dict_of_values, mean_of_values): # deviazione standard
    var = variance(dict_of_values, mean_of_values)
    std_dev = math.sqrt(var)
    return std_dev

# apertura dei file
non_ponzi_addr = "non_ponzi_addresses.csv"              # indirizzi smart contract
bytecodes_result = open("bytecodes.txt", "w+") # conterra' il bytecode degli smart contract
non_ponzi_result = open("non_ponzi_result.csv", "w+")   # conterra' le features degli smart contract
writer = csv.writer(non_ponzi_result, lineterminator = '\n') # writer per scrivere sul file
writer.writerow(['address', 'balance', 'lifetime', 'tx_in', 'tx_out', 'investment_in', 'payment_out', 'investment_to_contract/tx_in', 'payment_from_contract/tx_out', '#addresses_paying_contract', '#addresses_paid_by_contract', 'mean_v1', 'sdev_v1', 'mean_v2', 'sdev_v2', 'paid_rate', 'paid_one', 'percentage_some_tx_in', 'sdev_tx_in', 'percentage_some_tx_out', 'sdev_tx_out', 'owner_gets_eth_Wo_investing', 'owner_gets_eth_investing', 'owner_no_eth'])
non_ponzi = [] # lista che mantiene gli indirizzi degli smart contract

with open(non_ponzi_addr, 'r', encoding = 'utf-8-sig') as f: 
    reader = csv.reader(f, delimiter = ',', quotechar = '|') # reader: oggetto che itera le linee del file csv 
    for row in reader:
        addr = row[0] # si legge per righe, il primo elemento di ogni riga viene inserito in addr
        non_ponzi.append(addr)

for addr in non_ponzi: # ciclo su tutti gli indirizzi presenti nella lista
    print("Retrieving transactions of contract ", addr)
    sys.stdout.flush() # si ripulisce lo stream di output

    count_in, count_out = 0, 0   # contatore delle transazioni interne ed esterne del contratto, si considerano solo quelle con valore > 0
    eth_in, eth_out = 0, 0       # eth in entrata ed in uscita, servira' per calcolare il bilancio
    date_first_tx = 0            # la data della prima transazione vale 0, considero intero poiche' su timestamp
    date_last_tx = ''            # e' una stringa, la recupero dalle liste txs_list_in e txs_list_out che contengono stringhe
    txs_list_in = []             # lista che conterra' le date delle transazioni in ingresso in formato y-m-d, in stringhe
    txs_list_out = []            # lista che conterra' le date delle trans in uscita, le date sono sotto forma di stringhe
    dict_addr_tx_out = {}        # dizionario, <indirizzo: #pagamenti fatti dal contratto verso l'indirizzo>
    dict_addr_tx_in = {}         # dizionario, <indirizzo: #pagamenti inviati al contratto dall'indirizzo>
    dict_addr_eth_in = {}        # dizionario, <indirizzo: amount inviati al contratto dall'indirizzo>
    dict_addr_eth_out = {}       # dizionario, <indirizzo: amount ricevuti dall'indirizzo>
    bytcd = ''                  # in questa stringa ci mettero' il bytecode del contratto
    creator_addr = ''            # mantiene l'indirizzo di chi crea il contratto
    creator_get_eth_wo_investing = 0   # 1 se il creatore ha ottenuto eth senza investire
    creator_get_eth_investing = 0      # 1 se il creatore ha ottenuto eth investendo
    creator_get_no_eth = 0             # 1 se il creatore del contratto non ha ottenuto eth 
    
    print("Get normal transaction of contract ", addr)
    normal_tx_url = "https://api.etherscan.io/api?module=account&action=txlist&address=" + addr + \
                   "&startblock=0&endblock=99999999&page=1&offset=10000&sort=asc&apikey=Q9C796N54G4G4S6JP91ERNQTM9VWC463BP"
    response_normal = requests.get(normal_tx_url, verify = certifi.where()) # la get restituisce un Response obj
    address_content_normal = response_normal.json() # la risposta e' in formato json, si ottiene un dizionario python
    result_normal = address_content_normal.get('result') # facendo la get e si ottiene tutto cio' che sta dopo result, si ottiene una lista

    for t in result_normal: # transazioni in ingresso nel contratto
        if (t['isError'] == '0'): # assenza di errori nella transazione
            if (date_first_tx == 0): 
                date_first_tx = int(t['timeStamp']) # assegno la prima che trovo
                creator_addr = t['from'] # assegno anche il creatore del contratto
            if not bytcd: # disponendo le transazione in ordine asc, la prima che si incontra manterra' il bytecode dello smart contract
                bytcd = t['input']
                to_print_in_file = bytcd[2:]
                to_print_in_file += "\n" # inserico il new line altrimenti non va accapo
                bytecodes_result.write(to_print_in_file)
            # si trasforma il timestamp in una stringa e lo inserisco in txs_list_in
            obj_datetime = datetime.fromtimestamp(int(t['timeStamp'])) 
            txs_list_in.append(obj_datetime.strftime('%Y-%m-%d')) # inserisco in coda la data
            eth_val = int(t['value'])
            if (eth_val > 0): # se il valore della transazione e' > 0 allora...
                if t['from'] in dict_addr_tx_in: # se l'indirizzo e' gia' presente, cioe' il mittente della transazione aveva gia' pagato il contratto
                    dict_addr_tx_in[t['from']] += 1 # incremento il valore associato alla chiave, che indica il numero di transazioni
                    dict_addr_eth_in[t['from']] += round(Decimal(eth_val)/Decimal('1000000000000000000'), 6) # incremento il valore associato alla chiave, che indica quanto eth ha inviato
                else:
                    dict_addr_tx_in[t['from']] = 1 # se non era ancora presente allora e' la prima volta che invia soldi al contratto
                    dict_addr_eth_in[t['from']] = round(Decimal(eth_val)/Decimal('1000000000000000000'), 6)
                eth_in += eth_val # incremento la variabile che contiene l'ETH ricevuto
                count_in += 1

    print("Get internal transaction of contract ", addr)
    internal_tx_url = "https://api.etherscan.io/api?module=account&action=txlistinternal&address=" + addr + \
                       "&startblock=0&endblock=99999999&page=1&offset=10000&sort=asc&apikey=Q9C796N54G4G4S6JP91ERNQTM9VWC463BP"
    response_internal = requests.get(internal_tx_url, verify = certifi.where())
    address_content_internal = response_internal.json()
    result_internal = address_content_internal.get("result")

    for t in result_internal:
        if (t['isError'] != '0'): continue # siamo in presenza di errore
        obj_datetime = datetime.fromtimestamp(int(t['timeStamp']))
        eth_val = int(t['value'])
        if (t['from'].lower() == addr.lower()):  # internal transaction from contract to t['to'] aka addr, flusso di ETH uscente            
            txs_list_out.append(obj_datetime.strftime('%Y-%m-%d')) # inserisco in coda la data            
            if (eth_val > 0):
                if t['to'] in dict_addr_tx_out:
                    dict_addr_tx_out[t['to']] += 1
                    dict_addr_eth_out[t['to']] += round(Decimal(eth_val)/Decimal('1000000000000000000'), 6)
                else:
                    dict_addr_tx_out[t['to']] = 1 # se non era ancora presente allora e' il primo pagamento che ha ricevuto
                    dict_addr_eth_out[t['to']] = round(Decimal(eth_val)/Decimal('1000000000000000000'), 6)
                eth_out += eth_val
                count_out +=1
        else:  # internal transaction from t['from'] to contract, flusso di ETH entrante
            txs_list_in.append(obj_datetime.strftime('%Y-%m-%d')) # inserisco in coda la data
            if (eth_val > 0): # se il valore della transazione e' >0 allora...
                if t['from'] in dict_addr_tx_in: # se l'indirizzo e' gia' presente, cioe' il mittente della transazione aveva gia' pagato il contratto
                    dict_addr_tx_in[t['from']] += 1 # incremento il valore associato alla chiave, che indica il numero di transazioni
                    dict_addr_eth_in[t['from']] += round(Decimal(eth_val)/Decimal('1000000000000000000'), 6) # incremento il valore associato alla chiave, che indica quanto eth ha inviato
                else:
                    dict_addr_tx_in[t['from']] = 1 # se non era ancora presente allora e' la prima volta che invia soldi al contratto
                    dict_addr_eth_in[t['from']] = round(Decimal(eth_val)/Decimal('1000000000000000000'), 6)
                eth_in += eth_val # incremento la variabile che contiene l'ETH ricevuto
                count_in += 1

    # creo due dizionari <data (string): occorenza (intero)>, per occorrenza si intende il numero di volte che la data compare
    dict_date_tx_in = dict(collections.Counter(txs_list_in))
    dict_date_tx_out = dict(collections.Counter(txs_list_out))
    tx_in = len(txs_list_in)
    tx_out = len(txs_list_out)

    sorted_txs_list_in = sorted(txs_list_in, key=lambda x: datetime.strptime(x, '%Y-%m-%d'))
    string_fisrt_date = sorted_txs_list_in[0] # Return a string representing the date in fmt y-m-d, questa la prendo da txs_list_in perche' la prima proviene sempre da lista di tx in ingresso
    date_zero = datetime.strptime(string_fisrt_date, '%Y-%m-%d') # ottengo adesso un oggetto date che indica la data di inizio
    date_last_in_tx = datetime.strptime(sorted_txs_list_in[-1], '%Y-%m-%d') # questa ce' per forza perche' una transazione entrante serve per creare il contratto

    if len(txs_list_out) == 0: # se non ha transazioni uscenti allora la lifetime sara' la differenza delle tx entranti
        df = date_last_in_tx - date_zero
        lifetime = df.days
    else: # prendo la data della prima transazione e dell'ultima, ne faccio la differenza ed ottengo la lifetime del contratto
        date_last_out_tx = datetime.strptime(txs_list_out[-1], '%Y-%m-%d') # ultima data delle transazioni interne
        if date_last_in_tx > date_last_out_tx:
            date_last_tx = date_last_in_tx
        else:
            date_last_tx = date_last_out_tx
        df = date_last_tx - date_zero
        lifetime = df.days # la differenza deve essere espressa in giorni
    
    # calcolo le statistiche
    balance = round(Decimal(eth_in - eth_out)/Decimal('1000000000000000000'),6)                  # bilancio del contratto
    percentage_count_tx_in = round(count_in/max(tx_in, 1), 4)
    percentage_count_tx_out = round(count_out/max(tx_out, 1), 4)
    paying_addresses = len(dict_addr_tx_in)     # numero di indirizzi diversi che hanno inviato ETH al contratto
    paid_addresses = len(dict_addr_tx_out)      # numero di indirizzi diversi che hanno ricevuto ETH dal contratto
    
    v1 = {key: dict_addr_tx_out[key] - dict_addr_tx_in.get(key, 0) for key in dict_addr_tx_out} # creo un dizionario che ha tutte le chiavi di dict_addr_tx_in e come valori la differenza fra i valori dei due dizionari per chiavi uguali 
    for k in dict_addr_tx_in:
        if k not in dict_addr_tx_out:
	        v1[k] = - dict_addr_tx_in[k] # aggiungo le chiavi che sono presenti in dict_addr_tx_out ma che non sono state inserite in v1
    
    v2 = {key: dict_addr_eth_out[key] - dict_addr_eth_in.get(key, 0) for key in dict_addr_eth_out}
    for k in dict_addr_eth_in:
        if k not in dict_addr_eth_out:
	        v2[k] = - dict_addr_eth_in[k]
    
    mean_v1 = round(Decimal(mean(v1)), 6)   # media del vettore differenza fra dict_addr_tx_in (contiene il numero di volte che un indirizzo ha inviato ETH al contratto) e dict_addr_tx_out (contiene il numero di volte che un indirizzo ha ricevuto ETH dal contratto) per ogni indirizzo
    sdev_v1 = round(sdev(v1, mean_v1), 6)   # sdev del vettore differenza dict_addr_tx_in e dict_addr_tx_out
    mean_v2 = round(Decimal(mean(v2)), 6)   # media del vettore differenza fra dict_addr_eth_in (contiene l'ammontare di ETH inviato al contratto da un indirizzo) e dict_addr_eth_out (contiene l'ammontare di ETH ricevuto dal contratto e inviato ad un indirizzo) per ogni indirizzo
    sdev_v2 = round(sdev(v2, mean_v2), 6)   # sdev del vettore differenza dict_addr_eth_in e dict_addr_eth_out
    paid_rate = round(Decimal(count_out)/Decimal(max(count_in, 1)), 4) # rapporto fra le transazioni in uscita dal contratto e quelle in ingresso nel contratto: tx_out/tx_in

    # conto le chiavi presenti sia in dict_addr_tx_out che in dict_addr_tx_in, in questo modo ho il numero di quanti investitori sono stati pagati
    count_paid_investors = 0
    for k in dict_addr_tx_out:
        if k in dict_addr_tx_in:
            count_paid_investors += 1 # non posso usare la variabile paid_addresses poiche' qui ci possono essere messi anche non investitori es: creatore del contratto che non ha investito ma ha ricevuto soldi
    
    paid_one = round(Decimal(count_paid_investors)/Decimal(max(paying_addresses, 1)), 4)   # perche' faccio count/... anzi che len(dict_addr_tx_out)/... perche' ci potrebbe essere qualche indirizzo (i.e. il proprietario) che pur non investendo nulla nel contratto potrebbe ricevere ETH, noi qui non vogliamo considerarlo

    if(creator_addr in dict_addr_tx_out and creator_addr not in dict_addr_tx_in): # creatore del contratto ha ricevuto ETH senza investire
        creator_get_eth_wo_investing = 1
    if(creator_addr in dict_addr_tx_out and creator_addr in dict_addr_tx_in): # creatore del contratto ha ricevuto ETH investendo
        creator_get_eth_investing = 1
    if(creator_addr not in dict_addr_tx_out): # creatore del contratto non ha ricevuto ETH
        creator_get_no_eth = 1

    percentage_some_tx_in = round(Decimal(len(dict_date_tx_in))/Decimal(max(lifetime, 1)), 4) # percentuale che esprime i giorni di attivita' di un contratto (in cui ce' stata almeno una transazione in ingresso, non necessariamente con ETH) rispetto alla sua lifetime
    sdev_tx_in = round(sdev(dict_date_tx_in, mean(dict_date_tx_in)), 6)  # sdev delle transazioni, ci dice se ci sono dei giorni con picchi rispetto ad altri, piu' e' alta la sdev e piu' e' eterogeneo il numero delle tx in ingresso
    percentage_some_tx_out = round(Decimal(len(dict_date_tx_out))/Decimal(max(lifetime,1)), 4)
    sdev_tx_out = round(sdev(dict_date_tx_out, mean(dict_date_tx_out)), 6)

    writer.writerow([addr, str(balance), str(lifetime), str(tx_in), str(tx_out), str(count_in), str(count_out), str(percentage_count_tx_in), str(percentage_count_tx_out), str(paying_addresses), str(paid_addresses), str(mean_v1), str(sdev_v1), str(mean_v2), str(sdev_v2), str(paid_rate), str(paid_one), str(percentage_some_tx_in), str(sdev_tx_in), str(percentage_some_tx_out), str(sdev_tx_out), str(creator_get_eth_wo_investing), str(creator_get_eth_investing), str(creator_get_no_eth)]) 
    time.sleep(0.2)

non_ponzi_result.close()
bytecodes_result.close()
print("end of the journey!")
