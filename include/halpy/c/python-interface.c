/* $Id: python-interface.c,v 1.7 2004/01/13 10:59:20 lfousse Exp $ */
/* MegHAL Python interface, by David N. Welton <davidw@dedasys.com> */

#include <Python.h>
#include "megahal.h"

static PyObject *mhinitbrain(PyObject *self, PyObject *args)
{
    megahal_initialize();
    return Py_None;
}

static PyObject *mhdoreply(PyObject *self, PyObject *args)
{
    char *input;
    char *output = NULL;

    if (!PyArg_ParseTuple(args, "s", &input))
        return NULL;

    output = megahal_do_reply(input, 1);

    return PyString_FromString(output);
}

static PyObject *mhlearn(PyObject *self, PyObject *args)
{
    char *input;

    if (!PyArg_ParseTuple(args, "s", &input))
        return NULL;

    megahal_learn_no_reply(input, 1);

    return Py_None;
}

static PyObject *mhcleanup(PyObject *self, PyObject *args)
{
    megahal_cleanup();
    return Py_None;
}

static struct PyMethodDef mh_methods[] = {
    {"initbrain", mhinitbrain, METH_VARARGS, "Initialize megahal brain"},
    {"doreply", mhdoreply, METH_VARARGS, "Generate a reply"},
    {"cleanup", mhcleanup, METH_VARARGS,"Clean megahal"},
    {"learn", mhlearn, METH_VARARGS, "Learn from a sentence, don't generate a reply"},
    {NULL, NULL, 0, NULL} /* Sentinel */
};

void initmegahal()
{
    Py_InitModule("megahal", mh_methods);

    if(PyErr_Occurred())
        Py_FatalError("can't initialize module my_python");
}
