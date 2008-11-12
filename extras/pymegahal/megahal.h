#ifndef MEGAHAL_H
#define MEGAHAL_H 1
#ifdef SUNOS
extern double drand48(void);
extern void srand48(long);
#endif
void megahal_setdirectory (char *dir);
void megahal_initialize(void);
char *megahal_do_reply(char *input, int log);
void megahal_learn_no_reply(char *input, int log);
void megahal_cleanup(void);
#endif
