#include <ffi.h>
#include <stddef.h>

ffi_type ffi_type_void    = { 1, 1, FFI_TYPE_VOID,    NULL };
ffi_type ffi_type_uint8   = { 1, 1, FFI_TYPE_UINT8,   NULL };
ffi_type ffi_type_sint8   = { 1, 1, FFI_TYPE_SINT8,   NULL };
ffi_type ffi_type_uint16  = { 2, 2, FFI_TYPE_UINT16,  NULL };
ffi_type ffi_type_sint16  = { 2, 2, FFI_TYPE_SINT16,  NULL };
ffi_type ffi_type_uint32  = { 4, 4, FFI_TYPE_UINT32,  NULL };
ffi_type ffi_type_sint32  = { 4, 4, FFI_TYPE_SINT32,  NULL };
ffi_type ffi_type_uint64  = { 8, 8, FFI_TYPE_UINT64,  NULL };
ffi_type ffi_type_sint64  = { 8, 8, FFI_TYPE_SINT64,  NULL };
ffi_type ffi_type_float   = { 4, 4, FFI_TYPE_FLOAT,   NULL };
ffi_type ffi_type_double  = { 8, 8, FFI_TYPE_DOUBLE,  NULL };
ffi_type ffi_type_pointer = { 4, 4, FFI_TYPE_POINTER, NULL };

void *ffi_closure_alloc(size_t size, void **code) {
    (void)size; (void)code;
    return NULL;
}

void ffi_closure_free(void *closure) {
    (void)closure;
}

ffi_status ffi_prep_closure_loc(ffi_closure *closure, ffi_cif *cif,
    void (*fun)(ffi_cif*, void*, void**, void*),
    void *user_data, void *code_loc) {
    (void)closure; (void)cif; (void)fun; (void)user_data; (void)code_loc;
    return FFI_BAD_ABI;
}

ffi_status ffi_prep_cif(ffi_cif *cif, ffi_abi abi, unsigned int nargs,
    ffi_type *rtype, ffi_type **atypes) {
    (void)cif; (void)abi; (void)nargs; (void)rtype; (void)atypes;
    return FFI_OK;
}

ffi_status ffi_prep_cif_var(ffi_cif *cif, ffi_abi abi, unsigned int nfixedargs,
    unsigned int ntotalargs, ffi_type *rtype, ffi_type **atypes) {
    (void)cif; (void)abi; (void)nfixedargs; (void)ntotalargs; (void)rtype; (void)atypes;
    return FFI_OK;
}

void ffi_call(ffi_cif *cif, void (*fn)(void), void *rvalue, void **avalue) {
    (void)cif; (void)fn; (void)rvalue; (void)avalue;
}
