"""Etiquetas de Swagger: cada operación declara su caso de uso y su pantalla (principio I)."""

CU05_GUI01 = "CU-05 · GUI-01"
CU06_GUI02 = "CU-06 · GUI-02"
CU01_GUI01 = "CU-01 · GUI-01"
CU01_ACCESO = "CU-01 · Acceso (RNF-02)"
CU07_GUI03 = "CU-07 · GUI-03"
CU02_GUI03 = "CU-02 · GUI-03"
CU03_GUI04 = "CU-03 · GUI-04"
CU08_GUI05 = "CU-08 · GUI-05"
CU04_GUI06 = "CU-04 · GUI-06"

METADATOS_ETIQUETAS = [
    {"name": CU05_GUI01, "description": "CU-05 Buscar cliente (pantalla GUI-01 Recepción)."},
    {"name": CU06_GUI02, "description": "CU-06 Registrar nuevo cliente (modal GUI-02)."},
    {
        "name": CU01_GUI01,
        "description": "CU-01 Registrar orden de servicio y seguimiento del taller (GUI-01).",
    },
    {
        "name": CU01_ACCESO,
        "description": "Inicio y cierre de sesión; precondición de CU-01 («sesión iniciada») y RNF-02.",
    },
    {
        "name": CU07_GUI03,
        "description": "CU-07 Consultar stock libre de repuestos (pantalla GUI-03 Laboratorio).",
    },
    {
        "name": CU02_GUI03,
        "description": "CU-02 Emitir diagnóstico y presupuesto con reserva atómica (GUI-03).",
    },
    {
        "name": CU03_GUI04,
        "description": "CU-03 Registrar decisión de presupuesto del cliente (GUI-04).",
    },
    {
        "name": CU08_GUI05,
        "description": "CU-08 Finalizar reparación y consumir repuestos reservados (GUI-05).",
    },
    {
        "name": CU04_GUI06,
        "description": "CU-04 Liquidar orden, emitir CP-AAAA-NNNN y entregar equipo (GUI-06).",
    },
]
