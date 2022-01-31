#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>

#define ADDR_LEN 45             // lunghezza indirizzi
#define LSIZ 33000              // lunghezza massima dei bytecode 
#define NUM_SMART_PONZI 66      // numero di bytecode da analizzare

// funzione che calcola il minimo di 3 valori
int minimum(int a, int b, int c) { 
    int min = a;
    if (b < min) min = b;
    if (c < min) min = c;
    return min;
}

// funzione che calcola la distanza di levenshtein
int Levenshtein_distance(char *x, char *y) {
    int m = strlen(x);
    int n = strlen(y);
    
    register int i, j;
    int distance;
    
    int *prev = malloc((n + 1) * sizeof(int));
    int *curr = malloc((n + 1) * sizeof(int));
    int *tmp = 0;
    
    for(i = 0; i <= n; i++)
        prev[i] = i;

    for(i = 1; i <= m; i++) {
        curr[0] = i;
        for(j = 1; j <= n; j++) {
            if(x[i - 1] != y[j - 1]) {
                int k = minimum(curr[j - 1], prev[j - 1], prev[j]);
                curr[j] = k + 1;
            } else {
                curr[j] = prev[j - 1];
            }
        }

        tmp = prev;
        prev = curr;
        curr = tmp;
        
        memset((void*) curr, 0, sizeof(int) * (n + 1));
    }
    
    distance = prev[n];
    
    free(curr);
    free(prev);
    
    return distance;
}

int main(void) 
{
	char aname[20]; // nome del file contenente gli indirizzi
    char bname[20]; // nome del file contenente bytecode
    FILE *addr = NULL; 
    FILE *bytecode = NULL;
    
    printf("\n\n Read the file and store the lines into an array, in this part we are going to store the addresses of the smart contract:\n");
	printf("------------------------------------------------------\n"); 
	printf(" Input the filename to be opened : "); 

	scanf("%s", aname);	// acquisico da tastiera il nome del file
    addr = fopen(aname, "r"); // apro il file in lettura
        if(addr == NULL){
        printf("It's not possible open this file.\n");
        exit(1);
    }

    char **addresses = (char**)malloc(NUM_SMART_PONZI*sizeof(char*)); // creo l'array di stringhe che conterra' gli indirizzi
    if(addresses == NULL){
        printf("Memory allocation error.\n");
        exit(1);
    }

    for(int i=0; i<NUM_SMART_PONZI; i++){
        addresses[i] = (char*)malloc(ADDR_LEN*sizeof(char)); // alloco ADDR_LEN ad ogni entry, creo una matrice con NUM_SMART_PONZI entry e di lunghezza ADDR_LEN
        if(addresses[i] == NULL){
            printf("Memory allocation error.\n");
            exit(1);
        }
    }

    int AddressIndex = 0;

    while(fgets(addresses[AddressIndex], ADDR_LEN, addr) != NULL) // leggo dal file ed inserisco nella matrice
        AddressIndex++;

    fclose(addr); // chiudo il descrittore del file

    printf("\n\n Read the file and store the lines into an array, in this part we are going to store the bytecode of DUPLICATED smart contract:\n");
	printf("------------------------------------------------------\n"); 
	printf(" Input the filename to be opened : ");

    scanf("%s",bname);	
    bytecode = fopen(bname, "r");
    if(ponziBytecode == NULL){
        printf("It's not possible open this file.\n");
        exit(1);      
    }

    char **bytecodeSC = (char**)malloc(NUM_SMART_PONZI*sizeof(char*)); // creo l'array di stringhe che conterra' i bytecode
    if(bytecodeSC == NULL){
        printf("Memory allocation error.\n");
        exit(1);
    }

    for(int i=0; i<NUM_SMART_PONZI; i++){
        bytecodeSC[i] = (char*)malloc(LSIZ*sizeof(char)); // alloco LSIZ ad ogni entry
        if(bytecodeSC[i] == NULL){
            printf("Memory allocation error.\n");
            exit(1);
        }
    }

    int TotestIndex = 0;
    while(fgets(bytecodeSC[TotestIndex], LSIZ, bytecode) != NULL)
        TotestIndex++;

    fclose(bytecode); // chiudo il descrittore del file

    int LevDist[NUM_SMART_PONZI][NUM_SMART_PONZI]; // creo la matrice che conterra' i risultati del calcolo della Levenshtein

    for(int i=0; i<NUM_SMART_PONZI; i++)
        for(int j=0; j<NUM_SMART_PONZI; j++) // j = i+1 e posso togliere anche il controllo dell'if a riga successiva
            if(i != j) // sulla diagonale non calcolo perche' saranno i medesimi bytecode
                LevDist[i][j] = Levenshtein_distance(bytecodeSC[i], bytecodeSC[j]); // riempio la matrice per righe calcolando la Levenshtein

    int pos = -1;

    for(int i=0; i<NUM_SMART_PONZI; i++){
        int min = INT_MAX; // inizializzo il minimo al massimo intero possibile
        for(int j=0; j<NUM_SMART_PONZI; j++){
            if(i != j){ // non siamo sulla diagonale (che ricordiamo non contiene valori)
                if(LevDist[i][j] < min){
                    min = LevDist[i][j];
                    pos = j;
                }
                if(min == 0){ // abbiamo una equivalenza completa, si tratta sicuramente di un doppione
                    printf("lo smart contract %s e' una copia dello smart contract in posizione %d \n", addresses[i], pos);
                    break;
                }
            }
        } // finito il ciclo piu' interno, se min != 0, vuol dire che non abbiamo una copia perfetta, ma potremmo avere degli smart contract molto simili lo stesso
        if(min != 0){
            double normalizedLD;
            if(strlen(bytecodeSC[i]) >= strlen(bytecodeSC[pos]))
                normalizedLD = (double)min/strlen(bytecodeSC[i]);
            else
                normalizedLD = (double)min/strlen(bytecodeSC[pos]);

            if(normalizedLD < 0.05)
                printf("lo smart contract %s potrebbe essere una copia dello smart contract in posizione %d \n", addresses[i], pos);
            else
                printf("lo smart contract %s, non dovrebbe avere copie nel dataset \n", addresses[i]);
        }
    }

    // devo liberare memoria di LevDist
    for (int i=0; i<NUM_SMART_PONZI; i++) {
        for (int j=0; j<NUM_SMART_PONZI; j++) {
            free(LevDist[i][j]);
        }
        free(LevDist[i]);
    }
    free(LevDist);

    return 0;
}
