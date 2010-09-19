#include <Python.h>
#include "megahal.h"

static PyObject *mhinitbrain(PyObject *self, PyObject *args)
{
    char *dir;
    if (!PyArg_ParseTuple(args, "s", &dir))
        return NULL;
    megahal_setdirectory(dir);
    megahal_initialize();
    Py_INCREF(Py_None);
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
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *mhcleanup(PyObject *self, PyObject *args)
{
    megahal_cleanup();
    Py_INCREF(Py_None);
    return Py_None;
}

static struct PyMethodDef mh_methods[] = {
    {"init", mhinitbrain, METH_VARARGS, "Initialize megahal brain"},
    {"process", mhdoreply, METH_VARARGS, "Generate a reply"},
    {"save", mhcleanup, METH_VARARGS,"Save database"},
    {"learn", mhlearn, METH_VARARGS, "Learn from a sentence"},
    {NULL, NULL, 0, NULL}
};

void initcmegahal()
{
    Py_InitModule("cmegahal", mh_methods);
    if(PyErr_Occurred())
        Py_FatalError("can't initialize module megahal");
}
