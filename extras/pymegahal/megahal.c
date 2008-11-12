#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <unistd.h>
#include <getopt.h>
#include <string.h>
#include <signal.h>
#include <math.h>
#include <time.h>
#include <ctype.h>
#if defined(__mac_os)
#include <types.h>
#else
#include <sys/types.h>
#endif
#include "megahal.h"

#define MIN(a,b) ((a)<(b))?(a):(b)
#define COOKIE "MegaHALv8"
#define TIMEOUT 1
#define DEFAULT "."
#define BYTE1 unsigned char
#define BYTE2 unsigned short
#define BYTE4 unsigned long
#ifdef __mac_os
#define bool Boolean
#endif
#ifdef DOS
#define SEP "\\"
#else
#define SEP "/"
#endif

#ifdef AMIGA
#undef toupper
#define toupper(x) ToUpper(x)
#undef tolower
#define tolower(x) ToLower(x)
#undef isalpha
#define isalpha(x) IsAlpha(_AmigaLocale,x)
#undef isalnum
#define isalnum(x) IsAlNum(_AmigaLocale,x)
#undef isdigit
#define isdigit(x) IsDigit(_AmigaLocale,x)
#undef isspace
#define isspace(x) IsSpace(_AmigaLocale,x)
#endif

#ifndef __mac_os
#undef FALSE
#undef TRUE
typedef enum { FALSE, TRUE } bool;
#endif

typedef struct {
    BYTE1 length;
    char *word;
} STRING;

typedef struct {
    BYTE4 size;
    STRING *entry;
    BYTE2 *index;
} DICTIONARY;

typedef struct {
    BYTE2 size;
    STRING *from;
    STRING *to;
} SWAP;

typedef struct NODE {
    BYTE2 symbol;
    BYTE4 usage;
    BYTE2 count;
    BYTE2 branch;
    struct NODE **tree;
} TREE;

typedef struct {
    BYTE1 order;
    TREE *forward;
    TREE *backward;
    TREE **context;
    DICTIONARY *dictionary;
} MODEL;

static int order=5;
static DICTIONARY *words=NULL;
static MODEL *model=NULL;
static DICTIONARY *ban=NULL;
static DICTIONARY *aux=NULL;
static SWAP *swp=NULL;
static bool used_key;
static char *directory=NULL;
static char *last=NULL;
#ifdef AMIGA
struct Locale *_AmigaLocale;
#endif
static void add_aux(MODEL *, DICTIONARY *, STRING);
static void add_key(MODEL *, DICTIONARY *, STRING);
static void add_node(TREE *, TREE *, int);
static void add_swap(SWAP *, char *, char *);
static TREE *add_symbol(TREE *, BYTE2);
static BYTE2 add_word(DICTIONARY *, STRING);
static int babble(MODEL *, DICTIONARY *, DICTIONARY *);
static bool boundary(char *, int);
static void capitalize(char *);
static void change_personality(DICTIONARY *, unsigned int, MODEL **);
static bool dissimilar(DICTIONARY *, DICTIONARY *);
static float evaluate_reply(MODEL *, DICTIONARY *, DICTIONARY *);
static TREE *find_symbol(TREE *, int);
static TREE *find_symbol_add(TREE *, int);
static BYTE2 find_word(DICTIONARY *, STRING);
static char *generate_reply(MODEL *, DICTIONARY *);
static void learn(MODEL *, DICTIONARY *);
static void make_words(char *, DICTIONARY *);
static DICTIONARY *new_dictionary(void);
static void save_model(char *, MODEL *);
#ifdef __mac_os
static char *strdup(const char *);
#endif
static void upper(char *);
#if defined(DOS) || defined(__mac_os)
static void usleep(int);
#endif
static void free_dictionary(DICTIONARY *);
static void free_model(MODEL *);
static void free_tree(TREE *);
static void free_word(STRING);
static void free_words(DICTIONARY *);
static void initialize_context(MODEL *);
static void initialize_dictionary(DICTIONARY *);
static DICTIONARY *initialize_list(char *);
static SWAP *initialize_swap(char *);
static void load_dictionary(FILE *, DICTIONARY *);
static bool load_model(char *, MODEL *);
static void load_personality(MODEL **);
static void load_tree(FILE *, TREE *);
static void load_word(FILE *, DICTIONARY *);
static DICTIONARY *make_keywords(MODEL *, DICTIONARY *);
static char *make_output(DICTIONARY *);
static MODEL *new_model(int);
static TREE *new_node(void);
static SWAP *new_swap(void);
static DICTIONARY *reply(MODEL *, DICTIONARY *);
static void save_dictionary(FILE *, DICTIONARY *);
static void save_tree(FILE *, TREE *);
static void save_word(FILE *, STRING);
static int search_dictionary(DICTIONARY *, STRING, bool *);
static int search_node(TREE *, int, bool *);
static int seed(MODEL *, DICTIONARY *);
static void show_dictionary(DICTIONARY *);
static void train(MODEL *, char *);
static void update_context(MODEL *, int);
static void update_model(MODEL *, int);
static int wordcmp(STRING, STRING);
static bool word_exists(DICTIONARY *, STRING);
static int rnd(int);

void megahal_setdirectory (char *dir)
{
    directory = (char *)malloc(sizeof(char)*(strlen(dir)+1));
    strcpy(directory, dir);
}

void megahal_initialize(void)
{
#ifdef AMIGA
    _AmigaLocale=OpenLocale(NULL);
#endif
    words = new_dictionary();
    change_personality(NULL, 0, &model);
}

char *megahal_do_reply(char *input, int log)
{
    char *output = NULL;
    upper(input);
    make_words(input, words);
    learn(model, words);
    output = generate_reply(model, words);
    capitalize(output);
    return output;
}

void megahal_learn_no_reply(char *input, int log)
{
    upper(input);
    make_words(input, words);
    learn(model, words);
}

void megahal_cleanup(void)
{
    save_model("megahal.brn", model);
#ifdef AMIGA
    CloseLocale(_AmigaLocale);
#endif
}

void capitalize(char *string)
{
    register unsigned int i;
    bool start=TRUE;
    for(i=0; i<strlen(string); ++i) {
        if(isalpha(string[i])) {
            if(start==TRUE) string[i]=(char)toupper((int)string[i]);
            else string[i]=(char)tolower((int)string[i]);
            start=FALSE;
        }
        if((i>2)&&(strchr("!.?", string[i-1])!=NULL)&&(isspace(string[i])))
            start=TRUE;
    }
}

void upper(char *string)
{
    register unsigned int i;
    for(i=0; i<strlen(string); ++i) string[i]=(char)toupper((int)string[i]);
}

BYTE2 add_word(DICTIONARY *dictionary, STRING word)
{
    register int i;
    int position;
    bool found;
    position=search_dictionary(dictionary, word, &found);
    if(found==TRUE) goto succeed;
    dictionary->size+=1;
    if(dictionary->index==NULL) {
        dictionary->index=(BYTE2 *)malloc(sizeof(BYTE2)*
                (dictionary->size));
    } else {
        dictionary->index=(BYTE2 *)realloc((BYTE2 *)
                (dictionary->index),sizeof(BYTE2)*(dictionary->size));
    }
    if(dictionary->index==NULL) {
        goto fail;
    }
    if(dictionary->entry==NULL) {
        dictionary->entry=(STRING *)malloc(sizeof(STRING)*(dictionary->size));
    } else {
        dictionary->entry=(STRING *)realloc((STRING *)(dictionary->entry),
                sizeof(STRING)*(dictionary->size));
    }
    if(dictionary->entry==NULL) {
        goto fail;
    }
    dictionary->entry[dictionary->size-1].length=word.length;
    dictionary->entry[dictionary->size-1].word=(char *)malloc(sizeof(char)*
            (word.length));
    if(dictionary->entry[dictionary->size-1].word==NULL) {
        goto fail;
    }
    for(i=0; i<word.length; ++i)
        dictionary->entry[dictionary->size-1].word[i]=word.word[i];
    for(i=(dictionary->size-1); i>position; --i)
        dictionary->index[i]=dictionary->index[i-1];
    dictionary->index[position]=dictionary->size-1;
succeed:
    return(dictionary->index[position]);
fail:
    return(0);
}

int search_dictionary(DICTIONARY *dictionary, STRING word, bool *find)
{
    int position;
    int min;
    int max;
    int middle;
    int compar;
    if(dictionary->size==0) {
        position=0;
        goto notfound;
    }
    min=0;
    max=dictionary->size-1;
    while(TRUE) {
        middle=(min+max)/2;
        compar=wordcmp(word, dictionary->entry[dictionary->index[middle]]);
        if(compar==0) {
            position=middle;
            goto found;
        } else if(compar>0) {
            if(max==middle) {
                position=middle+1;
                goto notfound;
            }
            min=middle+1;
        } else {
            if(min==middle) {
                position=middle;
                goto notfound;
            }
            max=middle-1;
        }
    }
found:
    *find=TRUE;
    return(position);
notfound:
    *find=FALSE;
    return(position);
}

BYTE2 find_word(DICTIONARY *dictionary, STRING word)
{
    int position;
    bool found;
    position=search_dictionary(dictionary, word, &found);
    if(found==TRUE) return(dictionary->index[position]);
    else return(0);
}

int wordcmp(STRING word1, STRING word2)
{
    register int i;
    int bound;
    bound=MIN(word1.length,word2.length);
    for(i=0; i<bound; ++i)
        if(toupper(word1.word[i])!=toupper(word2.word[i]))
            return((int)(toupper(word1.word[i])-toupper(word2.word[i])));
    if(word1.length<word2.length) return(-1);
    if(word1.length>word2.length) return(1);
    return(0);
}

void free_dictionary(DICTIONARY *dictionary)
{
    if(dictionary==NULL) return;
    if(dictionary->entry!=NULL) {
        free(dictionary->entry);
        dictionary->entry=NULL;
    }
    if(dictionary->index!=NULL) {
        free(dictionary->index);
        dictionary->index=NULL;
    }
    dictionary->size=0;
}

void free_model(MODEL *model)
{
    if(model==NULL) return;
    if(model->forward!=NULL) {
        free_tree(model->forward);
    }
    if(model->backward!=NULL) {
        free_tree(model->backward);
    }
    if(model->context!=NULL) {
        free(model->context);
    }
    if(model->dictionary!=NULL) {
        free_dictionary(model->dictionary);
        free(model->dictionary);
    }
    free(model);
}

void free_tree(TREE *tree)
{
    register unsigned int i;
    if(tree==NULL) return;
    if(tree->tree!=NULL) {
        for(i=0; i<tree->branch; ++i) {
            free_tree(tree->tree[i]);
        }
        free(tree->tree);
    }
    free(tree);
}

void initialize_dictionary(DICTIONARY *dictionary)
{
    STRING word={ 7, "<ERROR>" };
    STRING end={ 5, "<FIN>" };
    (void)add_word(dictionary, word);
    (void)add_word(dictionary, end);
}

DICTIONARY *new_dictionary(void)
{
    DICTIONARY *dictionary=NULL;
    dictionary=(DICTIONARY *)malloc(sizeof(DICTIONARY));
    if(dictionary==NULL) {
        return(NULL);
    }
    dictionary->size=0;
    dictionary->index=NULL;
    dictionary->entry=NULL;
    return(dictionary);
}

void save_dictionary(FILE *file, DICTIONARY *dictionary)
{
    register unsigned int i;
    fwrite(&(dictionary->size), sizeof(BYTE4), 1, file);
    for(i=0; i<dictionary->size; ++i) {
        save_word(file, dictionary->entry[i]);
    }
}

void load_dictionary(FILE *file, DICTIONARY *dictionary)
{
    register int i;
    int size;
    fread(&size, sizeof(BYTE4), 1, file);
    for(i=0; i<size; ++i) {
        load_word(file, dictionary);
    }
}

void save_word(FILE *file, STRING word)
{
    register unsigned int i;
    fwrite(&(word.length), sizeof(BYTE1), 1, file);
    for(i=0; i<word.length; ++i)
        fwrite(&(word.word[i]), sizeof(char), 1, file);
}

void load_word(FILE *file, DICTIONARY *dictionary)
{
    register unsigned int i;
    STRING word;
    fread(&(word.length), sizeof(BYTE1), 1, file);
    word.word=(char *)malloc(sizeof(char)*word.length);
    if(word.word==NULL) {
        return;
    }
    for(i=0; i<word.length; ++i)
        fread(&(word.word[i]), sizeof(char), 1, file);
    add_word(dictionary, word);
    free(word.word);
}

TREE *new_node(void)
{
    TREE *node=NULL;
    node=(TREE *)malloc(sizeof(TREE));
    if(node==NULL) {
        goto fail;
    }
    node->symbol=0;
    node->usage=0;
    node->count=0;
    node->branch=0;
    node->tree=NULL;
    return(node);
fail:
    if(node!=NULL) free(node);
    return(NULL);
}

MODEL *new_model(int order)
{
    MODEL *model=NULL;
    model=(MODEL *)malloc(sizeof(MODEL));
    if(model==NULL) {
        goto fail;
    }
    model->order=order;
    model->forward=new_node();
    model->backward=new_node();
    model->context=(TREE **)malloc(sizeof(TREE *)*(order+2));
    if(model->context==NULL) {
        goto fail;
    }
    initialize_context(model);
    model->dictionary=new_dictionary();
    initialize_dictionary(model->dictionary);
    return(model);
fail:
    return(NULL);
}

void update_model(MODEL *model, int symbol)
{
    register unsigned int i;
    for(i=(model->order+1); i>0; --i)
        if(model->context[i-1]!=NULL)
            model->context[i]=add_symbol(model->context[i-1], (BYTE2)symbol);
    return;
}

void update_context(MODEL *model, int symbol)
{
    register unsigned int i;
    for(i=(model->order+1); i>0; --i)
        if(model->context[i-1]!=NULL)
            model->context[i]=find_symbol(model->context[i-1], symbol);
}

TREE *add_symbol(TREE *tree, BYTE2 symbol)
{
    TREE *node=NULL;
    node=find_symbol_add(tree, symbol);
    if((node->count<65535)) {
        node->count+=1;
        tree->usage+=1;
    }
    return(node);
}

TREE *find_symbol(TREE *node, int symbol)
{
    register unsigned int i;
    TREE *found=NULL;
    bool found_symbol=FALSE;
    i=search_node(node, symbol, &found_symbol);
    if(found_symbol==TRUE) found=node->tree[i];
    return(found);
}

TREE *find_symbol_add(TREE *node, int symbol)
{
    register unsigned int i;
    TREE *found=NULL;
    bool found_symbol=FALSE;
    i=search_node(node, symbol, &found_symbol);
    if(found_symbol==TRUE) {
        found=node->tree[i];
    } else {
        found=new_node();
        found->symbol=symbol;
        add_node(node, found, i);
    }
    return(found);
}

void add_node(TREE *tree, TREE *node, int position)
{
    register int i;
    if(tree->tree==NULL) {
        tree->tree=(TREE **)malloc(sizeof(TREE *)*(tree->branch+1));
    } else {
        tree->tree=(TREE **)realloc((TREE **)(tree->tree),sizeof(TREE *)*
                (tree->branch+1));
    }
    if(tree->tree==NULL) {
        return;
    }
    for(i=tree->branch; i>position; --i)
        tree->tree[i]=tree->tree[i-1];
    tree->tree[position]=node;
    tree->branch+=1;
}

int search_node(TREE *node, int symbol, bool *found_symbol)
{
    register unsigned int position;
    int min;
    int max;
    int middle;
    int compar;
    if(node->branch==0) {
        position=0;
        goto notfound;
    }
    min=0;
    max=node->branch-1;
    while(TRUE) {
        middle=(min+max)/2;
        compar=symbol-node->tree[middle]->symbol;
        if(compar==0) {
            position=middle;
            goto found;
        } else if(compar>0) {
            if(max==middle) {
                position=middle+1;
                goto notfound;
            }
            min=middle+1;
        } else {
            if(min==middle) {
                position=middle;
                goto notfound;
            }
            max=middle-1;
        }
    }
found:
    *found_symbol=TRUE;
    return(position);
notfound:
    *found_symbol=FALSE;
    return(position);
}

void initialize_context(MODEL *model)
{
    register unsigned int i;
    for(i=0; i<=model->order; ++i) model->context[i]=NULL;
}

void learn(MODEL *model, DICTIONARY *words)
{
    register unsigned int i;
    register int j;
    BYTE2 symbol;
    if(words->size<=(model->order)) return;
    initialize_context(model);
    model->context[0]=model->forward;
    for(i=0; i<words->size; ++i) {
        symbol=add_word(model->dictionary, words->entry[i]);
        update_model(model, symbol);
    }
    update_model(model, 1);
    initialize_context(model);
    model->context[0]=model->backward;
    for(j=words->size-1; j>=0; --j) {
        symbol=find_word(model->dictionary, words->entry[j]);
        update_model(model, symbol);
    }
    update_model(model, 1);
    return;
}

void train(MODEL *model, char *filename)
{
    FILE *file;
    char buffer[1024];
    DICTIONARY *words=NULL;
    int length;
    if(filename==NULL) return;
    file=fopen(filename, "r");
    if(file==NULL) {
        printf("Unable to find the personality %s\n", filename);
        return;
    }
    fseek(file, 0, 2);
    length=ftell(file);
    rewind(file);
    words=new_dictionary();
    while(!feof(file)) {
        if(fgets(buffer, 1024, file)==NULL) break;
        if(buffer[0]=='#') continue;
        buffer[strlen(buffer)-1]='\0';
        upper(buffer);
        make_words(buffer, words);
        learn(model, words);
    }
    free_dictionary(words);
    fclose(file);
}

void show_dictionary(DICTIONARY *dictionary)
{
    register unsigned int i;
    register unsigned int j;
    FILE *file;
    file=fopen("megahal.dic", "w");
    if(file==NULL) {
        return;
    }
    for(i=0; i<dictionary->size; ++i) {
        for(j=0; j<dictionary->entry[i].length; ++j)
            fprintf(file, "%c", dictionary->entry[i].word[j]);
        fprintf(file, "\n");
    }
    fclose(file);
}

void save_model(char *modelname, MODEL *model)
{
    FILE *file;
    static char *filename=NULL;
    if(filename==NULL) filename=(char *)malloc(sizeof(char)*1);
    filename=(char *)realloc(filename,
            sizeof(char)*(strlen(directory)+strlen(SEP)+12));
    show_dictionary(model->dictionary);
    if(filename==NULL) return;
    sprintf(filename, "%s%smegahal.brn", directory, SEP);
    file=fopen(filename, "wb");
    if(file==NULL) {
        return;
    }
    fwrite(COOKIE, sizeof(char), strlen(COOKIE), file);
    fwrite(&(model->order), sizeof(BYTE1), 1, file);
    save_tree(file, model->forward);
    save_tree(file, model->backward);
    save_dictionary(file, model->dictionary);
    fclose(file);
}

void save_tree(FILE *file, TREE *node)
{
    register unsigned int i;
    fwrite(&(node->symbol), sizeof(BYTE2), 1, file);
    fwrite(&(node->usage), sizeof(BYTE4), 1, file);
    fwrite(&(node->count), sizeof(BYTE2), 1, file);
    fwrite(&(node->branch), sizeof(BYTE2), 1, file);
    for(i=0; i<node->branch; ++i) {
        save_tree(file, node->tree[i]);
    }
}

void load_tree(FILE *file, TREE *node)
{
    register unsigned int i;
    fread(&(node->symbol), sizeof(BYTE2), 1, file);
    fread(&(node->usage), sizeof(BYTE4), 1, file);
    fread(&(node->count), sizeof(BYTE2), 1, file);
    fread(&(node->branch), sizeof(BYTE2), 1, file);
    if(node->branch==0) return;
    node->tree=(TREE **)malloc(sizeof(TREE *)*(node->branch));
    if(node->tree==NULL) {
        return;
    }
    for(i=0; i<node->branch; ++i) {
        node->tree[i]=new_node();
        load_tree(file, node->tree[i]);
    }
}

bool load_model(char *filename, MODEL *model)
{
    FILE *file;
    char cookie[16];
    if(filename==NULL) return(FALSE);
    file=fopen(filename, "rb");
    if(file==NULL) {
        return(FALSE);
    }
    fread(cookie, sizeof(char), strlen(COOKIE), file);
    if(strncmp(cookie, COOKIE, strlen(COOKIE))!=0) {
        goto fail;
    }
    fread(&(model->order), sizeof(BYTE1), 1, file);
    load_tree(file, model->forward);
    load_tree(file, model->backward);
    load_dictionary(file, model->dictionary);
    return(TRUE);
fail:
    fclose(file);
    return(FALSE);
}

void make_words(char *input, DICTIONARY *words)
{
    int offset=0;
    free_dictionary(words);
    if(strlen(input)==0) return;
    while(1) {
        if(boundary(input, offset)) {
            if(words->entry==NULL)
                words->entry=(STRING *)malloc((words->size+1)*sizeof(STRING));
            else
                words->entry=(STRING *)realloc(words->entry, (words->size+1)*sizeof(STRING));
            if(words->entry==NULL) {
                return;
            }
            words->entry[words->size].length=offset;
            words->entry[words->size].word=input;
            words->size+=1;
            if(offset==(int)strlen(input)) break;
            input+=offset;
            offset=0;
        } else {
            ++offset;
        }
    }
    if(isalnum(words->entry[words->size-1].word[0])) {
        if(words->entry==NULL)
            words->entry=(STRING *)malloc((words->size+1)*sizeof(STRING));
        else
            words->entry=(STRING *)realloc(words->entry, (words->size+1)*sizeof(STRING));
        if(words->entry==NULL) {
            return;
        }
        words->entry[words->size].length=1;
        words->entry[words->size].word=".";
        ++words->size;
    }
    else if(strchr("!.?", words->entry[words->size-1].word[words->entry[words->size-1].length-1])==NULL) {
        words->entry[words->size-1].length=1;
        words->entry[words->size-1].word=".";
    }
    return;
}

bool boundary(char *string, int position)
{
    if(position==0)
        return(FALSE);
    if(position==(int)strlen(string))
        return(TRUE);
    if(
            (string[position]=='\'')&&
            (isalpha(string[position-1])!=0)&&
            (isalpha(string[position+1])!=0)
      )
        return(FALSE);
    if(
            (position>1)&&
            (string[position-1]=='\'')&&
            (isalpha(string[position-2])!=0)&&
            (isalpha(string[position])!=0)
      )
        return(FALSE);
    if(
            (isalpha(string[position])!=0)&&
            (isalpha(string[position-1])==0)
      )
        return(TRUE);
    if(
            (isalpha(string[position])==0)&&
            (isalpha(string[position-1])!=0)
      )
        return(TRUE);
    if(isdigit(string[position])!=isdigit(string[position-1]))
        return(TRUE);
    return(FALSE);
}

char *generate_reply(MODEL *model, DICTIONARY *words)
{
    static DICTIONARY *dummy=NULL;
    DICTIONARY *replywords;
    DICTIONARY *keywords;
    float surprise;
    float max_surprise;
    char *output;
    static char *output_none=NULL;
    int count;
    int basetime;
    int timeout = TIMEOUT;
    keywords=make_keywords(model, words);
    if(output_none==NULL) {
        output_none=malloc(40);
        if(output_none!=NULL)
            strcpy(output_none, "I don't know enough to answer you yet!");
    }
    output=output_none;
    if(dummy == NULL) dummy = new_dictionary();
    replywords = reply(model, dummy);
    if(dissimilar(words, replywords) == TRUE) output = make_output(replywords);
    max_surprise=(float)-1.0;
    count=0;
    basetime=time(NULL);
    do {
        replywords=reply(model, keywords);
        surprise=evaluate_reply(model, keywords, replywords);
        ++count;
        if((surprise>max_surprise)&&(dissimilar(words, replywords)==TRUE)) {
            max_surprise=surprise;
            output=make_output(replywords);
        }
    } while((time(NULL)-basetime)<timeout);
    return(output);
}

bool dissimilar(DICTIONARY *words1, DICTIONARY *words2)
{
    register unsigned int i;
    if(words1->size!=words2->size) return(TRUE);
    for(i=0; i<words1->size; ++i)
        if(wordcmp(words1->entry[i], words2->entry[i])!=0) return(TRUE);
    return(FALSE);
}

DICTIONARY *make_keywords(MODEL *model, DICTIONARY *words)
{
    static DICTIONARY *keys=NULL;
    register unsigned int i;
    register unsigned int j;
    int c;
    if(keys==NULL) keys=new_dictionary();
    for(i=0; i<keys->size; ++i) free(keys->entry[i].word);
    free_dictionary(keys);
    for(i=0; i<words->size; ++i) {
        c=0;
        for(j=0; j<swp->size; ++j)
            if(wordcmp(swp->from[j], words->entry[i])==0) {
                add_key(model, keys, swp->to[j]);
                ++c;
            }
        if(c==0) add_key(model, keys, words->entry[i]);
    }
    if(keys->size>0) for(i=0; i<words->size; ++i) {
        c=0;
        for(j=0; j<swp->size; ++j)
            if(wordcmp(swp->from[j], words->entry[i])==0) {
                add_aux(model, keys, swp->to[j]);
                ++c;
            }
        if(c==0) add_aux(model, keys, words->entry[i]);
    }
    return(keys);
}

void add_key(MODEL *model, DICTIONARY *keys, STRING word)
{
    int symbol;
    symbol=find_word(model->dictionary, word);
    if(symbol==0) return;
    if(isalnum(word.word[0])==0) return;
    symbol=find_word(ban, word);
    if(symbol!=0) return;
    symbol=find_word(aux, word);
    if(symbol!=0) return;
    add_word(keys, word);
}

void add_aux(MODEL *model, DICTIONARY *keys, STRING word)
{
    int symbol;
    symbol=find_word(model->dictionary, word);
    if(symbol==0) return;
    if(isalnum(word.word[0])==0) return;
    symbol=find_word(aux, word);
    if(symbol==0) return;
    add_word(keys, word);
}

DICTIONARY *reply(MODEL *model, DICTIONARY *keys)
{
    static DICTIONARY *replies=NULL;
    register int i;
    int symbol;
    bool start=TRUE;
    if(replies==NULL) replies=new_dictionary();
    free_dictionary(replies);
    initialize_context(model);
    model->context[0]=model->forward;
    used_key=FALSE;
    while(TRUE) {
        if(start==TRUE) symbol=seed(model, keys);
        else symbol=babble(model, keys, replies);
        if((symbol==0)||(symbol==1)) break;
        start=FALSE;
        if(replies->entry==NULL)
            replies->entry=(STRING *)malloc((replies->size+1)*sizeof(STRING));
        else
            replies->entry=(STRING *)realloc(replies->entry, (replies->size+1)*sizeof(STRING));
        if(replies->entry==NULL) {
            return(NULL);
        }
        replies->entry[replies->size].length=
            model->dictionary->entry[symbol].length;
        replies->entry[replies->size].word=
            model->dictionary->entry[symbol].word;
        replies->size+=1;
        update_context(model, symbol);
    }
    initialize_context(model);
    model->context[0]=model->backward;
    if(replies->size>0) for(i=MIN(replies->size-1, model->order); i>=0; --i) {
        symbol=find_word(model->dictionary, replies->entry[i]);
        update_context(model, symbol);
    }
    while(TRUE) {
        symbol=babble(model, keys, replies);
        if((symbol==0)||(symbol==1)) break;
        if(replies->entry==NULL)
            replies->entry=(STRING *)malloc((replies->size+1)*sizeof(STRING));
        else
            replies->entry=(STRING *)realloc(replies->entry, (replies->size+1)*sizeof(STRING));
        if(replies->entry==NULL) {
            return(NULL);
        }
        for(i=replies->size; i>0; --i) {
            replies->entry[i].length=replies->entry[i-1].length;
            replies->entry[i].word=replies->entry[i-1].word;
        }
        replies->entry[0].length=model->dictionary->entry[symbol].length;
        replies->entry[0].word=model->dictionary->entry[symbol].word;
        replies->size+=1;
        update_context(model, symbol);
    }
    return(replies);
}

float evaluate_reply(MODEL *model, DICTIONARY *keys, DICTIONARY *words)
{
    register unsigned int i;
    register int j;
    register int k;
    int symbol;
    float probability;
    int count;
    float entropy=(float)0.0;
    TREE *node;
    int num=0;
    if(words->size<=0) return((float)0.0);
    initialize_context(model);
    model->context[0]=model->forward;
    for(i=0; i<words->size; ++i) {
        symbol=find_word(model->dictionary, words->entry[i]);
        if(find_word(keys, words->entry[i])!=0) {
            probability=(float)0.0;
            count=0;
            ++num;
            for(j=0; j<model->order; ++j) if(model->context[j]!=NULL) {
                node=find_symbol(model->context[j], symbol);
                probability+=(float)(node->count)/
                    (float)(model->context[j]->usage);
                ++count;
            }
            if(count>0.0) entropy-=(float)log(probability/(float)count);
        }
        update_context(model, symbol);
    }
    initialize_context(model);
    model->context[0]=model->backward;
    for(k=words->size-1; k>=0; --k) {
        symbol=find_word(model->dictionary, words->entry[k]);
        if(find_word(keys, words->entry[k])!=0) {
            probability=(float)0.0;
            count=0;
            ++num;
            for(j=0; j<model->order; ++j) if(model->context[j]!=NULL) {
                node=find_symbol(model->context[j], symbol);
                probability+=(float)(node->count)/
                    (float)(model->context[j]->usage);
                ++count;
            }
            if(count>0.0) entropy-=(float)log(probability/(float)count);
        }
        update_context(model, symbol);
    }
    if(num>=8) entropy/=(float)sqrt(num-1);
    if(num>=16) entropy/=(float)num;
    return(entropy);
}

char *make_output(DICTIONARY *words)
{
    static char *output=NULL;
    register unsigned int i;
    register int j;
    int length;
    static char *output_none=NULL;
    if(output_none==NULL) output_none=malloc(40);
    if(output==NULL) {
        output=(char *)malloc(sizeof(char));
        if(output==NULL) {
            return(output_none);
        }
    }
    if(words->size==0) {
        if(output_none!=NULL)
            strcpy(output_none, "I am utterly speechless!");
        return(output_none);
    }
    length=1;
    for(i=0; i<words->size; ++i) length+=words->entry[i].length;
    output=(char *)realloc(output, sizeof(char)*length);
    if(output==NULL) {
        if(output_none!=NULL)
            strcpy(output_none, "I forgot what I was going to say!");
        return(output_none);
    }
    length=0;
    for(i=0; i<words->size; ++i)
        for(j=0; j<words->entry[i].length; ++j)
            output[length++]=words->entry[i].word[j];
    output[length]='\0';
    return(output);
}

int babble(MODEL *model, DICTIONARY *keys, DICTIONARY *words)
{
    TREE *node;
    register int i;
    int count;
    int symbol = 0;
    node = NULL;
    for(i=0; i<=model->order; ++i)
        if(model->context[i]!=NULL)
            node=model->context[i];
    if(node->branch==0) return(0);
    i=rnd(node->branch);
    count=rnd(node->usage);
    while(count>=0) {
        symbol=node->tree[i]->symbol;
        if(
                (find_word(keys, model->dictionary->entry[symbol])!=0)&&
                ((used_key==TRUE)||
                 (find_word(aux, model->dictionary->entry[symbol])==0))&&
                (word_exists(words, model->dictionary->entry[symbol])==FALSE)
          ) {
            used_key=TRUE;
            break;
        }
        count-=node->tree[i]->count;
        i=(i>=(node->branch-1))?0:i+1;
    }
    return(symbol);
}

bool word_exists(DICTIONARY *dictionary, STRING word)
{
    register unsigned int i;
    for(i=0; i<dictionary->size; ++i)
        if(wordcmp(dictionary->entry[i], word)==0)
            return(TRUE);
    return(FALSE);
}

int seed(MODEL *model, DICTIONARY *keys)
{
    register unsigned int i;
    int symbol;
    unsigned int stop;
    if(model->context[0]->branch==0) symbol=0;
    else symbol=model->context[0]->tree[rnd(model->context[0]->branch)]->symbol;
    if(keys->size>0) {
        i=rnd(keys->size);
        stop=i;
        while(TRUE) {
            if(
                    (find_word(model->dictionary, keys->entry[i])!=0)&&
                    (find_word(aux, keys->entry[i])==0)
              ) {
                symbol=find_word(model->dictionary, keys->entry[i]);
                return(symbol);
            }
            ++i;
            if(i==keys->size) i=0;
            if(i==stop) return(symbol);
        }
    }
    return(symbol);
}

SWAP *new_swap(void)
{
    SWAP *list;
    list=(SWAP *)malloc(sizeof(SWAP));
    if(list==NULL) {
        return(NULL);
    }
    list->size=0;
    list->from=NULL;
    list->to=NULL;
    return(list);
}

void add_swap(SWAP *list, char *s, char *d)
{
    list->size+=1;
    if(list->from==NULL) {
        list->from=(STRING *)malloc(sizeof(STRING));
        if(list->from==NULL) {
            return;
        }
    }
    if(list->to==NULL) {
        list->to=(STRING *)malloc(sizeof(STRING));
        if(list->to==NULL) {
            return;
        }
    }
    list->from=(STRING *)realloc(list->from, sizeof(STRING)*(list->size));
    if(list->from==NULL) {
        return;
    }
    list->to=(STRING *)realloc(list->to, sizeof(STRING)*(list->size));
    if(list->to==NULL) {
        return;
    }
    list->from[list->size-1].length=strlen(s);
    list->from[list->size-1].word=strdup(s);
    list->to[list->size-1].length=strlen(d);
    list->to[list->size-1].word=strdup(d);
}

SWAP *initialize_swap(char *filename)
{
    SWAP *list;
    FILE *file=NULL;
    char buffer[1024];
    char *from;
    char *to;
    list=new_swap();
    if(filename==NULL) return(list);
    file=fopen(filename, "r");
    if(file==NULL) return(list);
    while(!feof(file)) {
        if(fgets(buffer, 1024, file)==NULL) break;
        if(buffer[0]=='#') continue;
        from=strtok(buffer, "\t ");
        to=strtok(NULL, "\t \n#");
        add_swap(list, from, to);
    }
    fclose(file);
    return(list);
}

void free_swap(SWAP *swap)
{
    register int i;
    if(swap==NULL) return;
    for(i=0; i<swap->size; ++i) {
        free_word(swap->from[i]);
        free_word(swap->to[i]);
    }
    free(swap->from);
    free(swap->to);
    free(swap);
}

DICTIONARY *initialize_list(char *filename)
{
    DICTIONARY *list;
    FILE *file=NULL;
    STRING word;
    char *string;
    char buffer[1024];
    list=new_dictionary();
    if(filename==NULL) return(list);
    file=fopen(filename, "r");
    if(file==NULL) return(list);
    while(!feof(file)) {
        if(fgets(buffer, 1024, file)==NULL) break;
        if(buffer[0]=='#') continue;
        string=strtok(buffer, "\t \n#");
        if((string!=NULL)&&(strlen(string)>0)) {
            word.length=strlen(string);
            word.word=strdup(buffer);
            add_word(list, word);
        }
    }
    fclose(file);
    return(list);
}

int rnd(int range)
{
    static bool flag=FALSE;
    if(flag==FALSE) {
#if defined(__mac_os) || defined(DOS)
        srand(time(NULL));
#else
        srand48(time(NULL));
#endif
    }
    flag=TRUE;
#if defined(__mac_os) || defined(DOS)
    return(rand()%range);
#else
    return(floor(drand48()*(double)(range)));
#endif
}

#if defined(DOS) || defined(__mac_os)
void usleep(int period)
{
    clock_t goal;
    goal=(clock_t)(period*CLOCKS_PER_SEC)/(clock_t)1000000+clock();
    while(goal>clock());
}
#endif

#ifdef __mac_os
char *strdup(const char *str)
{
    char *rval=(char *)malloc(strlen(str)+1);
    if(rval!=NULL) strcpy(rval, str);
    return(rval);
}
#endif

void load_personality(MODEL **model)
{
    FILE *file;
    static char *filename=NULL;
    if(filename==NULL) filename=(char *)malloc(sizeof(char)*1);
    filename=(char *)realloc(filename,
            sizeof(char)*(strlen(directory)+strlen(SEP)+12));
    if(strcmp(directory, last)!=0) {
        sprintf(filename, "%s%smegahal.brn", directory, SEP);
        file=fopen(filename, "r");
        if(file==NULL) {
            sprintf(filename, "%s%smegahal.trn", directory, SEP);
            file=fopen(filename, "r");
            if(file==NULL) {
                fprintf(stdout, "Unable to change MegaHAL personality to \"%s\".\n"
                        "Reverting to MegaHAL personality \"%s\".\n", directory, last);
                free(directory);
                directory=strdup(last);
                return;
            }
        }
        fclose(file);
        fprintf(stdout, "Changing to MegaHAL personality \"%s\".\n", directory);
    }
    free_model(*model);
    free_words(ban);
    free_dictionary(ban);
    free_words(aux);
    free_dictionary(aux);
    free_swap(swp);
    *model=new_model(order);
    sprintf(filename, "%s%smegahal.brn", directory, SEP);
    if(load_model(filename, *model)==FALSE) {
        sprintf(filename, "%s%smegahal.trn", directory, SEP);
        train(*model, filename);
    }
    sprintf(filename, "%s%smegahal.ban", directory, SEP);
    ban=initialize_list(filename);
    sprintf(filename, "%s%smegahal.aux", directory, SEP);
    aux=initialize_list(filename);
    sprintf(filename, "%s%smegahal.swp", directory, SEP);
    swp=initialize_swap(filename);
}

void change_personality(DICTIONARY *command, unsigned int position, MODEL **model)
{
    if(directory == NULL) {
        directory = (char *)malloc(sizeof(char)*(strlen(DEFAULT)+1));
        strcpy(directory, DEFAULT);
    }
    if(last == NULL) {
        last = strdup(directory);
    }
    if((command == NULL)||((position+2)>=command->size)) {
    } else {
        directory=(char *)realloc(directory,
                sizeof(char)*(command->entry[position+2].length+1));
        strncpy(directory, command->entry[position+2].word,
                command->entry[position+2].length);
        directory[command->entry[position+2].length]='\0';
    }
    load_personality(model);
}

void free_words(DICTIONARY *words)
{
    register unsigned int i;
    if(words == NULL) return;
    if(words->entry != NULL)
        for(i=0; i<words->size; ++i) free_word(words->entry[i]);
}

void free_word(STRING word)
{
    free(word.word);
}
