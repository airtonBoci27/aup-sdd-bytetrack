"""Datos iniciales (fase de Transición) para uso local: técnicos, usuarios, repuestos y órdenes demo.

Uso: ``uv run python -m app.seed`` (idempotente: no duplica técnicos, usuarios, repuestos ni clientes).
Las contraseñas de los usuarios iniciales NO están en el código: se leen de variables de entorno o
del ``.env`` (RNF-02, principio VI); si falta alguna, la carga termina con un error que nombra la variable.
"""

from datetime import date
from decimal import Decimal
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app import config, security
from app.database import crear_tablas, obtener_fabrica_sesiones
from app.models.entities import (
    ESTADO_APROBADO,
    ESTADO_ENTREGADO,
    ESTADO_LISTO,
    ESTADO_PRESUPUESTADO,
    ESTADO_RECEPCIONADO,
    ESTADO_RECHAZADO,
    RESERVA_ACTIVA,
    RESERVA_CONSUMIDA,
    RESERVA_LIBERADA,
    Cliente,
    ComprobantePago,
    DetalleRepuesto,
    Diagnostico,
    Equipo,
    OrdenServicio,
    Repuesto,
    Tecnico,
    Usuario,
)
from app.repositories.usuario_repository import UsuarioRepository

TECNICOS_DEMO = [
    ("Luis", "Rojas", True),
    ("Carla", "Mendoza", True),
    ("Jorge", "Paredes", False),
]

REPUESTOS_DEMO = [
    ("SKU-SSD-512", "SSD NVMe M.2 512GB Kingston", 6, 1, "195.00"),
    ("SKU-RAM-16D4", "Memoria RAM 16GB DDR4 3200MHz", 5, 1, "145.00"),
    ("SKU-PAN-14FHD", "Pantalla LED 14\" Full HD IPS", 2, 1, "320.00"),
    ("SKU-BAT-T14", "Batería Interna 50Wh ThinkPad", 3, 0, "180.00"),
    ("SKU-TEC-LAT", "Teclado Retroiluminado Español LA", 4, 0, "110.00"),
    ("SKU-CAR-65W", "Cargador USB-C 65W Original", 7, 0, "95.00"),
    ("SKU-PST-THM", "Pasta Térmica Arctic MX-4 4g", 12, 0, "35.00"),
    ("SKU-FAN-CPU", "Ventilador Cooler CPU Laptop", 1, 0, "85.00"),
]


def cargar_tecnicos() -> int:
    """Crea los técnicos de demostración si la tabla está vacía; devuelve cuántos creó."""
    crear_tablas()
    with obtener_fabrica_sesiones()() as sesion:
        if sesion.scalar(select(Tecnico.id).limit(1)) is not None:
            return 0
        for nombres, apellidos, disponible in TECNICOS_DEMO:
            sesion.add(Tecnico(nombres=nombres, apellidos=apellidos, disponible=disponible, cola=0))
        sesion.commit()
        return len(TECNICOS_DEMO)


def cargar_usuarios(fabrica: sessionmaker[Session] | None = None) -> int:
    """RNF-02: crea o actualiza los usuarios iniciales desde el entorno; devuelve cuántos procesó.

    Lanza ``ConfiguracionError`` (sin crear ninguno) si falta una contraseña. Guarda solo el hash.
    """
    credenciales = config.credenciales_iniciales()  # falla antes de tocar la base
    if fabrica is None:
        crear_tablas()
        fabrica = obtener_fabrica_sesiones()
    with fabrica() as sesion:
        repositorio = UsuarioRepository(sesion)
        for nombre_usuario, clave, rol in credenciales:
            repositorio.crear_o_actualizar(nombre_usuario, security.hashear_clave(clave), rol)
        sesion.commit()
    return len(credenciales)


def cargar_datos_demo() -> int:
    """Carga repuestos, clientes, equipos y órdenes en todos los estados del ciclo AUP (idempotente)."""
    crear_tablas()
    with obtener_fabrica_sesiones()() as sesion:
        # Vincular el usuario Técnico al primer técnico disponible para RN-03.
        tecnicos_disp = list(
            sesion.scalars(
                select(Tecnico).where(Tecnico.disponible.is_(True)).order_by(Tecnico.id)
            )
        )
        if tecnicos_disp:
            usuario_tec = sesion.scalar(
                select(Usuario).where(Usuario.rol == config.ROL_TECNICO).limit(1)
            )
            if usuario_tec is not None and usuario_tec.tecnico_id is None:
                usuario_tec.tecnico_id = tecnicos_disp[0].id

        # Catálogo de repuestos (CU-07).
        if sesion.scalar(select(Repuesto.id).limit(1)) is None:
            for sku, nombre, disp, resv, precio in REPUESTOS_DEMO:
                sesion.add(
                    Repuesto(
                        sku=sku,
                        nombre=nombre,
                        stock_disponible=disp,
                        stock_reservado=resv,
                        precio_unitario=Decimal(precio),
                    )
                )
            sesion.flush()

        if sesion.scalar(select(Cliente.id).limit(1)) is not None:
            sesion.commit()
            return 0

        rep_ssd = sesion.scalar(select(Repuesto).where(Repuesto.sku == "SKU-SSD-512"))
        rep_ram = sesion.scalar(select(Repuesto).where(Repuesto.sku == "SKU-RAM-16D4"))
        rep_pan = sesion.scalar(select(Repuesto).where(Repuesto.sku == "SKU-PAN-14FHD"))

        c1 = Cliente(dni="45678912", nombres="María", apellidos="Torres Quispe", telefono="987654321", correo="maria.torres@gmail.com")
        c2 = Cliente(dni="72345678", nombres="Carlos", apellidos="Mendoza Vega", telefono="945112233", correo="cmendoza@outlook.com")
        c3 = Cliente(dni="10293847", nombres="Lucía", apellidos="Paredes Silva", telefono="912334455", correo=None)
        c4 = Cliente(dni="48112233", nombres="Diego", apellidos="Ramírez Soto", telefono="998877665", correo="dramirez@usil.pe")
        c5 = Cliente(dni="70998877", nombres="Valeria", apellidos="Chávez León", telefono="966554433", correo="vchavez@gmail.com")
        sesion.add_all([c1, c2, c3, c4, c5])
        sesion.flush()

        e1 = Equipo(cliente_id=c1.id, tipo="Laptop", marca="Lenovo", modelo="ThinkPad T14", numero_serie="SN-LEN-2026-01")
        e2 = Equipo(cliente_id=c1.id, tipo="Laptop", marca="Dell", modelo="XPS 13", numero_serie="SN-DEL-2026-02")
        e3 = Equipo(cliente_id=c2.id, tipo="Laptop", marca="Apple", modelo="MacBook Air M2", numero_serie="SN-APL-2026-03")
        e4 = Equipo(cliente_id=c2.id, tipo="PC Escritorio", marca="ASUS", modelo="ROG Strix", numero_serie="SN-ASU-2026-04")
        e5 = Equipo(cliente_id=c4.id, tipo="Laptop", marca="HP", modelo="Victus 15", numero_serie="SN-HPV-2026-05")
        e6 = Equipo(cliente_id=c5.id, tipo="Laptop", marca="Acer", modelo="Swift 3", numero_serie="SN-ACR-2026-06")
        e7 = Equipo(cliente_id=c4.id, tipo="Laptop", marca="MSI", modelo="Modern 14", numero_serie="SN-MSI-2026-07")
        sesion.add_all([e1, e2, e3, e4, e5, e6, e7])
        sesion.flush()

        if tecnicos_disp:
            tec1 = tecnicos_disp[0]
            tec2 = tecnicos_disp[1] if len(tecnicos_disp) > 1 else tec1
            anio = date.today().year
            costo = config.costo_revision_inicial()

            # 1. RECEPCIONADO (para probar E01 en GUI-01 y CU-02 en GUI-03 con tecnico)
            o1 = OrdenServicio(
                codigo=f"OS-{anio}-0001", equipo_id=e1.id, tecnico_id=tec1.id,
                estado=ESTADO_RECEPCIONADO, accesorios="Cargador original",
                estado_fisico="Tapa con leves rayones, bisagras firmes",
                falla_reportada="No enciende al presionar el botón de encendido",
                costo_revision=costo, id_op="OP-DEMO-0001",
            )
            # 2. PRESUPUESTADO (para probar CU-03 en GUI-04)
            o2 = OrdenServicio(
                codigo=f"OS-{anio}-0002", equipo_id=e3.id, tecnico_id=tec1.id,
                estado=ESTADO_PRESUPUESTADO, accesorios="Cargador original, Funda / maletín",
                estado_fisico="Carcasa limpia sin golpes",
                falla_reportada="Pantalla con líneas verticales tras caída",
                costo_revision=costo, id_op="OP-DEMO-0002",
            )
            # 3. APROBADO (para probar CU-08 en GUI-05 con tecnico)
            o3 = OrdenServicio(
                codigo=f"OS-{anio}-0003", equipo_id=e4.id, tecnico_id=tec1.id,
                estado=ESTADO_APROBADO, accesorios=None,
                estado_fisico="Gabinete completo",
                falla_reportada="Lentitud extrema y pantallazos azules",
                costo_revision=costo, id_op="OP-DEMO-0003",
                decision_canal="WHATSAPP", decision_fecha=f"{anio}-11-24T15:20:00+00:00",
                decision_evidencia="Cliente aprobó por WhatsApp el cambio de SSD y RAM.",
            )
            # 4. LISTO (para probar CU-04 en GUI-06 con recepcion)
            o4 = OrdenServicio(
                codigo=f"OS-{anio}-0004", equipo_id=e5.id, tecnico_id=tec2.id,
                estado=ESTADO_LISTO, accesorios="Cargador original",
                estado_fisico="Buen estado general",
                falla_reportada="Sobrecalentamiento y apagado repentino",
                costo_revision=costo, id_op="OP-DEMO-0004",
                decision_canal="LLAMADA", decision_fecha=f"{anio}-11-23T11:10:00+00:00",
                decision_evidencia="Aprobado por llamada telefónica.",
                trabajo_realizado="Limpieza interna y cambio de pasta térmica.",
                prueba_conforme=True, resultado_prueba="Temperatura estable bajo carga de 65°C.",
            )
            # 5. ENTREGADO (permite nueva orden para SN-DEL-2026-02 y muestra CP-AAAA-NNNN)
            o5 = OrdenServicio(
                codigo=f"OS-{anio}-0005", equipo_id=e2.id, tecnico_id=tec2.id,
                estado=ESTADO_ENTREGADO, accesorios="Cargador original",
                estado_fisico="Excelente estado",
                falla_reportada="Mantenimiento preventivo anual",
                costo_revision=costo, id_op="OP-DEMO-0005",
                trabajo_realizado="Mantenimiento preventivo completo.",
                prueba_conforme=True, resultado_prueba="Equipo operando al 100%.",
            )
            # 6. RECHAZADO (reserva liberada)
            o6 = OrdenServicio(
                codigo=f"OS-{anio}-0006", equipo_id=e6.id, tecnico_id=tec2.id,
                estado=ESTADO_RECHAZADO, accesorios="Funda / maletín",
                estado_fisico="Esquina inferior golpeada",
                falla_reportada="No carga batería",
                costo_revision=costo, id_op="OP-DEMO-0006",
                decision_canal="PRESENCIAL", decision_fecha=f"{anio}-11-22T17:40:00+00:00",
                decision_evidencia="Cliente decidió no proceder por costo del repuesto.",
            )
            # 7. RECEPCIONADO adicional (para que la tabla paginada tenga 2 páginas reales)
            o7 = OrdenServicio(
                codigo=f"OS-{anio}-0007", equipo_id=e7.id, tecnico_id=tec1.id,
                estado=ESTADO_RECEPCIONADO, accesorios="Cargador original",
                estado_fisico="Teclado con teclas desgastadas",
                falla_reportada="No reconoce puertos USB laterales",
                costo_revision=costo, id_op="OP-DEMO-0007",
            )
            sesion.add_all([o1, o2, o3, o4, o5, o6, o7])
            sesion.flush()

            # Diagnósticos de o2 (PRESUPUESTADO), o3 (APROBADO), o4 (LISTO), o5 (ENTREGADO) y o6 (RECHAZADO)
            if rep_pan is not None:
                sesion.add(
                    Diagnostico(
                        orden_id=o2.id,
                        informe_tecnico="Panel LCD fisurado internamente; requiere reemplazo de pantalla.",
                        costo_mano_obra=Decimal("90.00"),
                        subtotal_repuestos=Decimal("320.00"),
                        total_presupuesto=Decimal("410.00"),
                        detalles=[
                            DetalleRepuesto(
                                repuesto_id=rep_pan.id, cantidad=1,
                                precio_cotizado=Decimal("320.00"), subtotal=Decimal("320.00"),
                                estado_reserva=RESERVA_ACTIVA,
                            )
                        ],
                    )
                )
            if rep_ssd is not None and rep_ram is not None:
                sesion.add(
                    Diagnostico(
                        orden_id=o3.id,
                        informe_tecnico="Disco con sectores dañados y módulo de RAM defectuoso.",
                        costo_mano_obra=Decimal("100.00"),
                        subtotal_repuestos=Decimal("340.00"),
                        total_presupuesto=Decimal("440.00"),
                        detalles=[
                            DetalleRepuesto(
                                repuesto_id=rep_ssd.id, cantidad=1,
                                precio_cotizado=Decimal("195.00"), subtotal=Decimal("195.00"),
                                estado_reserva=RESERVA_ACTIVA,
                            ),
                            DetalleRepuesto(
                                repuesto_id=rep_ram.id, cantidad=1,
                                precio_cotizado=Decimal("145.00"), subtotal=Decimal("145.00"),
                                estado_reserva=RESERVA_ACTIVA,
                            ),
                        ],
                    )
                )
            sesion.add(
                Diagnostico(
                    orden_id=o4.id,
                    informe_tecnico="Sistema de disipación obstruido y pasta térmica reseca.",
                    costo_mano_obra=Decimal("120.00"),
                    subtotal_repuestos=Decimal("0.00"),
                    total_presupuesto=Decimal("120.00"),
                    detalles=[],
                )
            )
            sesion.add(
                Diagnostico(
                    orden_id=o5.id,
                    informe_tecnico="Mantenimiento preventivo general sin cambio de piezas.",
                    costo_mano_obra=Decimal("80.00"),
                    subtotal_repuestos=Decimal("0.00"),
                    total_presupuesto=Decimal("80.00"),
                    detalles=[],
                )
            )
            if rep_ssd is not None:
                sesion.add(
                    Diagnostico(
                        orden_id=o6.id,
                        informe_tecnico="Falla en circuito de carga y almacenamiento degradado.",
                        costo_mano_obra=Decimal("70.00"),
                        subtotal_repuestos=Decimal("195.00"),
                        total_presupuesto=Decimal("265.00"),
                        detalles=[
                            DetalleRepuesto(
                                repuesto_id=rep_ssd.id, cantidad=1,
                                precio_cotizado=Decimal("195.00"), subtotal=Decimal("195.00"),
                                estado_reserva=RESERVA_LIBERADA,
                            )
                        ],
                    )
                )
            sesion.add(
                ComprobantePago(
                    numero=f"CP-{anio}-0001",
                    orden_id=o5.id,
                    metodo_pago="TARJETA",
                    monto_total=Decimal("80.00"),
                    conformidad_entrega=True,
                )
            )
            tec1.cola = 3  # o1, o3, o7 activas en laboratorio
            tec2.cola = 1

        sesion.commit()
        return 5


def main() -> int:
    config.cargar_entorno()
    try:
        usuarios = cargar_usuarios()
    except config.ConfiguracionError as error:
        print(f"Error de configuración: {error}", file=sys.stderr)
        return 1
    tecnicos = cargar_tecnicos()
    clientes_demo = cargar_datos_demo()
    print(f"Usuarios cargados o actualizados: {usuarios}")
    print(f"Técnicos de demostración creados: {tecnicos}")
    print(f"Clientes de demostración creados: {clientes_demo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
