import weakref
from rpython.rlib import rawrefcount
from rpython.rtyper.lltypesystem import lltype, llmemory

class W_Root(object):
    def __init__(self, intval=0):
        self.intval = intval

PyObjectS = lltype.Struct('PyObjectS',
                          ('ob_refcnt', lltype.Signed),
                          ('ob_pypy_link', llmemory.GCREF))
PyObject = lltype.Ptr(PyObjectS)


class TestRawRefCount:

    def setup_method(self, meth):
        del rawrefcount._p_list[:]
        del rawrefcount._o_list[:]
        del rawrefcount._s_list[:]

    def test_create_link_pypy(self):
        p = W_Root(42)
        ob = lltype.malloc(PyObjectS, flavor='raw', zero=True,
                           track_allocation=False)
        assert rawrefcount.from_obj(PyObjectS, p) == lltype.nullptr(PyObjectS)
        assert rawrefcount.to_obj(W_Root, ob) == None
        rawrefcount.create_link_pypy(p, ob)
        assert rawrefcount.from_obj(PyObjectS, p) == ob
        assert rawrefcount.to_obj(W_Root, ob) == p

    def test_create_link_pyobj(self):
        p = W_Root(42)
        ob = lltype.malloc(PyObjectS, flavor='raw', zero=True,
                           track_allocation=False)
        assert rawrefcount.from_obj(PyObjectS, p) == lltype.nullptr(PyObjectS)
        assert rawrefcount.to_obj(W_Root, ob) == None
        rawrefcount.create_link_pyobj(p, ob)
        assert rawrefcount.from_obj(PyObjectS, p) == lltype.nullptr(PyObjectS)
        assert rawrefcount.to_obj(W_Root, ob) == p

    def test_create_link_shared(self):
        p = W_Root(42)
        ob = lltype.malloc(PyObjectS, flavor='raw', zero=True,
                           track_allocation=False)
        assert rawrefcount.from_obj(PyObjectS, p) == lltype.nullptr(PyObjectS)
        assert rawrefcount.to_obj(W_Root, ob) == None
        rawrefcount.create_link_shared(p, ob)
        assert rawrefcount.from_obj(PyObjectS, p) == lltype.nullptr(PyObjectS)
        assert rawrefcount.to_obj(W_Root, ob) == p

    def test_collect_p_dies(self):
        p = W_Root(42)
        ob = lltype.malloc(PyObjectS, flavor='raw', zero=True,
                           track_allocation=False)
        rawrefcount.create_link_pypy(p, ob)
        assert rawrefcount._p_list == [ob]
        wr_ob = weakref.ref(ob)
        wr_p = weakref.ref(p)
        del ob, p
        rawrefcount._collect()
        assert rawrefcount._p_list == []
        assert wr_ob() is None
        assert wr_p() is None

    def test_collect_p_keepalive_pyobject(self):
        p = W_Root(42)
        ob = lltype.malloc(PyObjectS, flavor='raw', zero=True,
                           track_allocation=False)
        rawrefcount.create_link_pypy(p, ob)
        assert rawrefcount._p_list == [ob]
        wr_ob = weakref.ref(ob)
        wr_p = weakref.ref(p)
        ob.ob_refcnt += 1      # <=
        del ob, p
        rawrefcount._collect()
        ob = wr_ob()
        p = wr_p()
        assert ob is not None and p is not None
        assert rawrefcount._p_list == [ob]
        assert rawrefcount.to_obj(W_Root, ob) == p
        assert rawrefcount.from_obj(PyObjectS, p) == ob

    def test_collect_p_keepalive_w_root(self):
        p = W_Root(42)
        ob = lltype.malloc(PyObjectS, flavor='raw', zero=True,
                           track_allocation=False)
        rawrefcount.create_link_pypy(p, ob)
        assert rawrefcount._p_list == [ob]
        wr_ob = weakref.ref(ob)
        del ob       # p remains
        rawrefcount._collect()
        ob = wr_ob()
        assert ob is not None
        assert rawrefcount._p_list == [ob]
        assert rawrefcount.to_obj(W_Root, ob) == p
        assert rawrefcount.from_obj(PyObjectS, p) == ob

    def test_collect_o_dies(self):
        p = W_Root(42)
        ob = lltype.malloc(PyObjectS, flavor='raw', zero=True,
                           track_allocation=False)
        rawrefcount.create_link_pyobj(p, ob)
        assert rawrefcount._o_list == [ob]
        wr_ob = weakref.ref(ob)
        wr_p = weakref.ref(p)
        del ob, p
        dealloc = rawrefcount._collect()
        ob = wr_ob()
        assert ob is not None
        assert dealloc == [ob]
        assert rawrefcount._o_list == []
        assert wr_p() is None

    def test_collect_o_keepalive_pyobject(self):
        p = W_Root(42)
        ob = lltype.malloc(PyObjectS, flavor='raw', zero=True,
                           track_allocation=False)
        p.pyobj = ob
        rawrefcount.create_link_pyobj(p, ob)
        assert rawrefcount._o_list == [ob]
        wr_ob = weakref.ref(ob)
        wr_p = weakref.ref(p)
        ob.ob_refcnt += 1      # <=
        del p
        dealloc = rawrefcount._collect()
        assert dealloc == []
        p = wr_p()
        assert p is None            # was unlinked
        assert ob.ob_refcnt == 1    # != REFCNT_FROM_PYPY_OBJECT + 1
        assert rawrefcount._o_list == []
        assert rawrefcount.to_obj(W_Root, ob) == None

    def test_collect_o_keepalive_w_root(self):
        p = W_Root(42)
        ob = lltype.malloc(PyObjectS, flavor='raw', zero=True,
                           track_allocation=False)
        p.pyobj = ob
        rawrefcount.create_link_pyobj(p, ob)
        assert rawrefcount._o_list == [ob]
        wr_ob = weakref.ref(ob)
        del ob       # p remains
        dealloc = rawrefcount._collect()
        assert dealloc == []
        ob = wr_ob()
        assert ob is not None
        assert rawrefcount._o_list == [ob]
        assert rawrefcount.to_obj(W_Root, ob) == p
        assert p.pyobj == ob

    def test_collect_s_dies(self):
        p = W_Root(42)
        ob = lltype.malloc(PyObjectS, flavor='raw', zero=True,
                           track_allocation=False)
        rawrefcount.create_link_shared(p, ob)
        assert rawrefcount._s_list == [ob]
        wr_ob = weakref.ref(ob)
        wr_p = weakref.ref(p)
        del ob, p
        dealloc = rawrefcount._collect()
        ob = wr_ob()
        assert ob is not None
        assert dealloc == [ob]
        assert rawrefcount._s_list == []
        assert wr_p() is None

    def test_collect_s_keepalive_pyobject(self):
        p = W_Root(42)
        ob = lltype.malloc(PyObjectS, flavor='raw', zero=True,
                           track_allocation=False)
        p.pyobj = ob
        rawrefcount.create_link_shared(p, ob)
        assert rawrefcount._s_list == [ob]
        wr_ob = weakref.ref(ob)
        wr_p = weakref.ref(p)
        ob.ob_refcnt += 1      # <=
        del ob, p
        rawrefcount._collect()
        ob = wr_ob()
        p = wr_p()
        assert ob is not None and p is not None
        assert rawrefcount._s_list == [ob]
        assert rawrefcount.to_obj(W_Root, ob) == p

    def test_collect_s_keepalive_w_root(self):
        p = W_Root(42)
        ob = lltype.malloc(PyObjectS, flavor='raw', zero=True,
                           track_allocation=False)
        p.pyobj = ob
        rawrefcount.create_link_shared(p, ob)
        assert rawrefcount._s_list == [ob]
        wr_ob = weakref.ref(ob)
        del ob       # p remains
        dealloc = rawrefcount._collect()
        assert dealloc == []
        ob = wr_ob()
        assert ob is not None
        assert rawrefcount._s_list == [ob]
        assert rawrefcount.to_obj(W_Root, ob) == p
