import sys
import csv
import hashlib

ponzi_addr = "ponzi_addresses.csv"  # indirizzi smart ponzi
bytecodes_result = "bytecodes.csv"  # bytecode smart ponzi
ponzi_addr_hash = {} # dizionario con chiavi gli indirizzi e valori hash(bytecode) cioe' l'hash calcolato sul bytecode
ponzi_hash_bytc = []
print("Get addresses")
with open(ponzi_addr, 'r', encoding = 'utf-8-sig') as fi:  # fi: file indirizzi
    reader1 = csv.reader(fi, delimiter = ',', quotechar = '|') # reader: oggetto che itera le linee del file csv 
    for row in reader1:
        addr = row[0] # si legge per righe, il primo elemento di ogni riga viene inserito in addr
        ponzi_addr_hash[addr] = None

print("Get bytecode")
with open(bytecodes_result, 'r', encoding = 'utf-8-sig') as fb: # fb: file bytecode
    reader2 = csv.reader(fb, delimiter = ',', quotechar = '|') # reader: oggetto che itera le linee del file csv 
    for row in reader2:
        bytc = row[0] # si legge per righe, il primo elemento di ogni riga viene inserito in addr
        hash_bytc = hashlib.sha256(bytc.encode('utf-8')).hexdigest()
        ponzi_hash_bytc.append(hash_bytc) # metto hash(bytecode) nella lista

# chiavi del dizionario: ponzi_addr_hash, valori del dizionario: ponzi_hash_bytc
dictionary = dict(zip(ponzi_addr_hash, ponzi_hash_bytc)) 
flipped = {} # finding duplicate values from dictionary using flip
  
for key, value in dictionary.items():
    if value not in flipped:
        flipped[value] = [key]
    else:
        flipped[value].append(key)
  
for key, value in flipped.items():
    print(key, ':', value)
