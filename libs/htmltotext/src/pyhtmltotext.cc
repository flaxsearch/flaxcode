/* pyhtmltotext.cc: Python interface for htmltotext.
 *
 * Copyright (C) 2007 Lemur Consulting Ltd
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
 */

#include <config.h>
#include <Python.h>
#include "structmember.h"
#include "myhtmlparse.h"

/* Python object used to represent the results of parsing a page. */
typedef struct {
    PyObject_HEAD
    PyObject *indexing_allowed;
    PyObject *badly_encoded;
    PyObject *title;
    PyObject *sample;
    PyObject *keywords;
} ParsedPage;

static void
ParsedPage_dealloc(ParsedPage * self)
{
    Py_XDECREF(self->indexing_allowed);
    Py_XDECREF(self->badly_encoded);
    Py_XDECREF(self->title);
    Py_XDECREF(self->sample);
    Py_XDECREF(self->keywords);
    self->ob_type->tp_free((PyObject*)self);
}

static PyObject *
ParsedPage_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    ParsedPage *self;

    self = (ParsedPage *)type->tp_alloc(type, 0);
    if (self != NULL) {
	/* Initialise any fields to default values here. */
	Py_INCREF(Py_True);
	self->indexing_allowed = Py_True;

	Py_INCREF(Py_False);
	self->badly_encoded = Py_False;
    }

    return (PyObject *)self;
}

static PyMemberDef ParsedPage_members[] = {
    {"indexing_allowed", T_OBJECT_EX,
	offsetof(ParsedPage, indexing_allowed), 0,
	"Boolean flag, set to true if indexing the document is allowed\n"
	"(based on meta tags)."},
    {"badly_encoded", T_OBJECT_EX,
	offsetof(ParsedPage, badly_encoded), 0,
	"Boolean flag, set to true if badly encoded data was found in the\n"
	"page."},
    {"title", T_OBJECT_EX,
	offsetof(ParsedPage, title), 0,
	"The title of the document."},
    {"sample", T_OBJECT_EX,
	offsetof(ParsedPage, sample), 0,
	"Text from the document body."},
    {"keywords", T_OBJECT_EX,
	offsetof(ParsedPage, keywords), 0,
	"Keywords for the document (based on meta tags)."},
    {NULL}  /* Sentinel */
};

static PyObject *
ParsedPage_str(ParsedPage * parsedpage)
{
    PyObject * result = NULL;
    PyObject * args = NULL;
    PyObject * format = NULL;
    PyObject * empty = NULL;
    const char * formatstr = "ParsedPage(title=%r, sample=%r, keywords=%r)";
    
    format = PyUnicode_Decode(formatstr, strlen(formatstr), "utf-8", NULL);
    if (format == NULL) goto fail;

    args = PyTuple_New(3);
    if (args == NULL) goto fail;

    Py_UNICODE emptystring[0];
    empty = PyUnicode_FromUnicode(emptystring, 0);
    if (empty == NULL) goto fail;

    if (parsedpage->title == NULL) {
	Py_INCREF(empty);
	PyTuple_SET_ITEM(args, 0, empty);
    } else {
	Py_INCREF(parsedpage->title);
	PyTuple_SET_ITEM(args, 0, parsedpage->title);
    }

    if (parsedpage->sample == NULL) {
	Py_INCREF(empty);
	PyTuple_SET_ITEM(args, 1, empty);
    } else {
	Py_INCREF(parsedpage->sample);
	PyTuple_SET_ITEM(args, 1, parsedpage->sample);
    }

    if (parsedpage->keywords == NULL) {
	Py_INCREF(empty);
	PyTuple_SET_ITEM(args, 2, empty);
    } else {
	Py_INCREF(parsedpage->keywords);
	PyTuple_SET_ITEM(args, 2, parsedpage->keywords);
    }

    result = PyUnicode_Format(format, args);

fail:
    Py_XDECREF(format);
    Py_XDECREF(args);
    Py_XDECREF(empty);
    return result;
}

static PyTypeObject ParsedPageType = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "htmltotext.ParsedPage",   /*tp_name*/
    sizeof(ParsedPage), /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    (destructor)ParsedPage_dealloc, /*tp_dealloc*/
    0,                         /*tp_print*/
    0,                         /*tp_getattr*/
    0,                         /*tp_setattr*/
    0,                         /*tp_compare*/
    0,                         /*tp_repr*/
    0,                         /*tp_as_number*/
    0,                         /*tp_as_sequence*/
    0,                         /*tp_as_mapping*/
    0,                         /*tp_hash */
    0,                         /*tp_call*/
    (reprfunc)ParsedPage_str,  /*tp_str*/
    0,                         /*tp_getattro*/
    0,                         /*tp_setattro*/
    0,                         /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
    "A parsed page",           /* tp_doc */
    0,		               /* tp_traverse */
    0,		               /* tp_clear */
    0,		               /* tp_richcompare */
    0,		               /* tp_weaklistoffset */
    0,		               /* tp_iter */
    0,		               /* tp_iternext */
    0,                         /* tp_methods */
    ParsedPage_members,        /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    0,                         /* tp_init */
    0,                         /* tp_alloc */
    ParsedPage_new,            /* tp_new */
};

static void
ParsedPage_ready()
{
    if (PyType_Ready(&ParsedPageType) < 0)
	return;
}

static void
ParsedPage_register(PyObject * m)
{
    Py_INCREF(&ParsedPageType);
    PyModule_AddObject(m, "ParsedPage", (PyObject *)&ParsedPageType);
}

/* Functions */

static PyObject *
decode_utf8_noting_errors(const std::string & data,
			  PyObject ** badly_encoded_ptr)
{
    PyObject * result;
    if (*badly_encoded_ptr == Py_False) {
	result = PyUnicode_Decode(data.data(), data.size(), "UTF-8", "strict");
	if (result == NULL) {
	    PyErr_Clear();
	    Py_XDECREF(*badly_encoded_ptr);
	    Py_INCREF(Py_True);
	    *badly_encoded_ptr = Py_True;
	} else {
	    return result;
	}
    }
    result = PyUnicode_Decode(data.data(), data.size(), "UTF-8", "ignore");
    return result;
}

static PyObject *
extract(PyObject *self, PyObject *args)
{
    ParsedPage * result = NULL;
    PyObject * arg1 = NULL;

    MyHtmlParser parser;

    if (!PyArg_UnpackTuple(args, "extract", 1, 1, &arg1))
	return NULL;

    if (PyUnicode_Check(arg1)) {
	/* Convert to a UTF8 string (return value needs to be DECREFed). */
	PyObject * utf8 = PyUnicode_AsUTF8String(arg1);
	if (utf8 == NULL)
	    goto fail;

	try {
	    parser.parse_html(std::string(PyString_AS_STRING(utf8),
					  PyString_GET_SIZE(utf8)),
			      std::string("UTF-8"));
	} catch(bool) {
	} catch(...) {
	    Py_DECREF(utf8);
	    throw;
	}
	Py_DECREF(utf8);
    } else {
	const char * buffer = NULL;
	int buffer_length = 0;
	if (!PyArg_ParseTuple(args, "s#", &buffer, &buffer_length))
	    goto fail;
	try {
	    parser.parse_html(std::string(buffer, buffer_length));
	} catch(bool) {
	}
    }

    result = (ParsedPage*) ParsedPage_new(&ParsedPageType, NULL, NULL);
    if (result == NULL) goto fail;
    Py_XDECREF(result->indexing_allowed);
    if (parser.indexing_allowed) {
	Py_INCREF(Py_True);
	result->indexing_allowed = Py_True;
    } else {
	Py_INCREF(Py_False);
	result->indexing_allowed = Py_False;
    }

    // Set the other members to unicode strings
    Py_XDECREF(result->title);
    result->title = decode_utf8_noting_errors(parser.title,
					      &(result->badly_encoded));
    if (result->title == NULL) goto fail;

    Py_XDECREF(result->sample);
    result->sample = PyUnicode_Decode(parser.sample.data(),
				      parser.sample.size(),
				      "UTF-8", "replace");
    if (result->sample == NULL) goto fail;

    Py_XDECREF(result->keywords);
    result->keywords = PyUnicode_Decode(parser.keywords.data(),
					parser.keywords.size(),
					"UTF-8", "replace");
    if (result->keywords == NULL) goto fail;

    return (PyObject*) result;
fail:
    Py_XDECREF(result);
    return NULL;
}

static PyMethodDef HtmlToTextMethods[] = {
    {"extract", extract, METH_VARARGS,
     "Extract text from a string containing some HTML.\n\n"
     "This takes a single argument, which should be a string type.\n"
     "The return value is a ParsedPage object.\n\n"
     "If the argument is a Unicode object, any character set information\n"
     "in the HTML string (eg, in <meta http-equiv=...> tags) will be\n"
     "ignored.  If the argument is a string object, such information will\n"
     "be used to determine the character encoding of the HTML, with a\n"
     "default of the Latin-1 (ISO-8859-1) being assumed (since this is the\n"
     "standard (but deprecated) default for HTML).  The badly_encoded\n"
     "member of the resulting ParsedPage object will be set to True if any\n"
     "invalid character encodings are found, but a best effort to ignore\n"
     "such errors and continue will be made."
    },
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
inithtmltotext(void)
{
    PyObject * m;

    ParsedPage_ready();

    m = Py_InitModule3("htmltotext", HtmlToTextMethods,
		       "Extract text from HTML documents.");

    ParsedPage_register(m);
}

