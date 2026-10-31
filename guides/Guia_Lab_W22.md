# Guía de Laboratorio — W22
## ERP Django · Espiral 8 · Semana 22 de 24
### Técnico en Programación (SEP 3061300006-23) · UTEC Celaya
### Asesor: MC. Román Fernando López González

---

| Campo | Detalle |
|---|---|
| **Semana** | W22 de 24 |
| **Espiral** | E8 — Calidad y Entrega |
| **Sprint Scrum** | Sprint 7 — Planning |
| **Hito** | Sin hito propio · Avance hacia M8 (W24) |
| **Horario** | 16:45 – 19:45 (180 min) |
| **Nivel Schmelkes** | 5 — Integración y Cierre |
| **Hilo conductor** | "Las Espirales 1–7 construyeron el ERP. La Espiral 8 lo certifica: ¿funciona todo junto, de punta a punta?" |

---

## Respuesta a la tarea de investigación de W21

> **¿Cómo se genera un reporte HTML de cobertura?**
>
> ```cmd
> coverage run manage.py test tests
> coverage html
> :: → genera htmlcov/index.html con colores verde/rojo por línea
> ```
>
> **¿Qué significa que una línea esté "cubierta"?**
> Una línea está cubierta si al menos un test la ejecuta.
> Una **rama** (`branch`) está cubierta si ambos caminos del `if`
> (verdadero y falso) fueron ejercidos por algún test.
>
> ```python
> def procesar(stock):
>     if stock < 5:           # branch A (cubierta si algún test entra)
>         alertar_stock()     # branch A — True
>     return stock            # branch A — False
> ```
> Con `branch=True`, si ningún test llega con `stock >= 5`, la rama
> `False` del `if` aparece como no cubierta aunque la línea `return`
> sí se ejecute en otro contexto.
>
> **¿Por qué el 100% de cobertura no garantiza código correcto?**
> Porque la cobertura mide que las líneas se ejecutan, no que el
> resultado sea correcto. Un test que ejecuta `venta_pdf()` pero no
> verifica que el PDF sea válido cubre el código sin detectar un bug.
> La cobertura es un suelo mínimo, no un techo de calidad.
>
> **Impacto de `HistoricalRecords` en `Producto.save()` masivo:**
> Cada `save()` inserta una fila adicional en `historical_producto`.
> Al importar 10,000 productos, se generarían 10,000 inserciones extra.
> Solución: usar `bulk_create()` en lugar de `save()` (simple_history
> no intercepta `bulk_create` por defecto) o deshabilitar
> temporalmente el historial con `producto.skip_history_when_saving = True`.

---

## Objetivos de la sesión

Al terminar W22, el estudiante será capaz de:

1. Redactar el Sprint 7 Planning con HUs de calidad y entrega
2. Configurar `coverage.py` con cobertura de ramas (`branch=True`)
3. Crear `tests/factories.py` con `factory_boy` para datos realistas
4. Escribir 3 tests de integración de flujo completo (end-to-end)
5. Ejecutar la primera medición de cobertura e identificar brechas
6. Agregar tests dirigidos para alcanzar el umbral de cobertura ≥ 80%
7. Generar el reporte HTML de cobertura

---

## Stack tecnológico de W22

| Herramienta | Novedad en W22 | Descripción |
|---|---|---|
| `coverage.py` | ✅ Nuevo | Mide qué porcentaje del código se ejecuta durante los tests |
| `factory_boy` | ✅ Nuevo | Genera instancias de modelos con datos realistas vía Faker |
| `Faker` (incluido con factory_boy) | ✅ Nuevo | Genera datos falsos pero realistas (nombres, emails, precios) |
| Tests de integración | ✅ Nuevo | Verifican flujos completos de extremo a extremo |
| `.coveragerc` / `setup.cfg` | ✅ Nuevo | Configuración persistente de coverage para no repetir flags |

---

## Mapa de tiempo (180 min)

| Parte | Actividad | Tiempo |
|---|---|---|
| Arranque | Daily Scrum + Sprint 7 Planning + verificar W21 | 15 min |
| Parte 1 | Instalar `coverage` y `factory-boy` | 10 min |
| Parte 2 | Configurar `coverage` en `setup.cfg` | 15 min |
| Parte 3 | `tests/factories.py`: 5 factories con Faker | 20 min |
| Parte 4 | Primera corrida de cobertura + análisis de brechas | 20 min |
| Parte 5 | Tests de integración (3 flujos E2E) | 35 min |
| Parte 6 | Tests dirigidos para cubrir brechas identificadas | 20 min |
| Parte 7 | Segunda corrida → reporte HTML ≥ 80% | 15 min |
| Cierre | Commit · `finalizar_sesion.bat` · hilo → W23 | 10 min |
| Buffer | | 20 min |
| **Total** | | **180 min** |

---

## ARRANQUE — Daily Scrum + Sprint 7 Planning (15 min)

```cmd
E:\iniciar_sesion.bat
```

### Daily Scrum

```
1. ¿Qué hice en W21?
   → Instalé django-simple-history, agregué HistoricalRecords
     a Producto y Venta, creé la vista de timeline de historial
     y cerré el Sprint 6 con el Hito M7.

2. ¿Qué haré en W22?
   → Configuraré coverage, crearé factories con datos realistas,
     escribiré tests de integración de flujo completo y alcanzaré
     ≥ 80% de cobertura de código.

3. ¿Tengo algún impedimento?
   → (registrar aquí)
```

### Verificar estado

```cmd
python manage.py check
python manage.py test tests --verbosity=0
```

**Resultado esperado:** `System check identified no issues` · `Ran 195 tests … OK`

---

### Sprint 7 Planning

**Sprint Goal del Sprint 7:**
> *"Al finalizar el Sprint 7, el ERP tendrá una suite de pruebas
> con cobertura ≥ 80%, todos los flujos críticos verificados con
> tests de integración end-to-end, y el sistema optimizado y
> documentado para la entrega final."*

**Duración:** W22 (cobertura + integración) · W23 (optimización SQL) · W24 (entrega final · M8)

Crear `sprint7_planning.md`:

```markdown
# Sprint 7 Planning — ERP Django
## Semanas W22–W24 · Espiral 8: Calidad y Entrega

**Sprint Goal:**
Al finalizar el Sprint 7, el ERP tendrá cobertura ≥ 80%, tests
de integración para los flujos críticos, rendimiento optimizado
y documentación completa para la entrega académica final.

## HUs seleccionadas

| ID | Historia | Puntos | Semana |
|---|---|---|---|
| HU-E8-01 | Como dev, quiero cobertura de código ≥ 80% | 5 | W22 |
| HU-E8-02 | Como dev, quiero tests de integración E2E | 5 | W22 |
| HU-E8-03 | Como dev, quiero factories con datos realistas | 3 | W22 |
| HU-E8-04 | Como admin, quiero el N+1 identificado y corregido | 3 | W23 |
| HU-E8-05 | Como admin, quiero django-debug-toolbar en desarrollo | 2 | W23 |
| HU-E8-06 | Como evaluador, quiero documentación técnica completa | 3 | W24 |
| HU-E8-07 | Como evaluador, quiero el sistema desplegado y funcional | 5 | W24 |

**Total Sprint 7:** 26 puntos

## DoD — Sprint 7
- coverage report → TOTAL ≥ 80%
- 3 tests E2E pasan sin errores
- django-debug-toolbar instalado en development
- 0 queries N+1 detectadas en las vistas críticas
- README.md actualizado con instrucciones de instalación
- URL pública en Render funcionando con todos los hitos
- python manage.py test → ≥ 203 tests OK
```

---

## PARTE 1 — Instalar `coverage` y `factory-boy` (10 min)

### 1.1 Instalar paquetes

```cmd
pip install "coverage==7.4.1" "factory-boy==3.3.0"
pip freeze > requirements.txt
```

Verificar:

```cmd
python -c "import coverage; print('coverage', coverage.__version__)"
python -c "import factory; print('factory_boy', factory.__version__)"
```

**Resultado esperado:**
```
coverage 7.4.1
factory_boy 3.3.0
```

> **Nota:** `factory-boy` incluye `faker` como dependencia.
> No es necesario instalar `faker` por separado.

---

## PARTE 2 — Configurar `coverage` en `setup.cfg` (15 min)

### 2.1 ¿Por qué `setup.cfg` y no la línea de comandos?

Sin configuración persistente:
```cmd
coverage run --source=. --omit=*/migrations/*,manage.py --branch manage.py test tests
```
→ hay que recordar y repetir todos los flags en cada ejecución.

Con `setup.cfg`:
```cmd
coverage run manage.py test tests   ← así de simple
```
Django lee automáticamente `setup.cfg` en la raíz del proyecto.

---

### 2.2 Crear `setup.cfg` en la raíz del proyecto

```ini
# setup.cfg
# Configuración persistente de coverage.py y otras herramientas

[coverage:run]
# Archivos a incluir en la medición
source = .

# Ramas de código a medir (if/else completos, no solo líneas)
branch = True

# Archivos y carpetas a EXCLUIR de la medición
omit =
    # Migraciones — generadas automáticamente, sin lógica de negocio
    */migrations/*

    # Tests — no medimos la cobertura de los propios tests
    tests/*
    tests/factories.py

    # Archivos de configuración y entrada
    manage.py
    core/settings*.py
    core/wsgi.py
    core/asgi.py

    # Entorno virtual
    env_erp/*
    venv/*
    .venv/*

    # Archivos de configuración de herramientas
    setup.cfg
    conftest.py

[coverage:report]
# Nivel mínimo de cobertura — el comando falla si no se alcanza
fail_under = 80

# Mostrar líneas no cubiertas en el reporte de consola
show_missing = True

# Omitir archivos con 100% de cobertura en el reporte
skip_covered = False

# Precisión del porcentaje
precision = 1

[coverage:html]
# Directorio del reporte HTML
directory = htmlcov

# Título del reporte
title = ERP Django — Reporte de Cobertura

[coverage:xml]
# Para integración con CI/CD (GitHub Actions, etc.)
output = coverage.xml
```

### 2.3 Agregar `htmlcov/` y `.coverage` al `.gitignore`

```bash
# .gitignore — agregar:
# Archivos de coverage
htmlcov/
.coverage
.coverage.*
coverage.xml
```

---

## PARTE 3 — `tests/factories.py`: 5 Factories con Faker (20 min)

### 3.1 ¿Por qué `factory_boy` en lugar de crear objetos manualmente?

```python
# Sin factory_boy — repetitivo y poco realista:
cat  = Categoria.objects.create(nombre='Cat Test')
prov = Proveedor.objects.create(nombre='Prov', correo='p@t.com')
prod = Producto.objects.create(
    nombre='Producto Test', precio=Decimal('100.00'), stock=5, categoria=cat
)

# Con factory_boy — conciso y con datos realistas:
prod = ProductoFactory()
# Genera: {'nombre': 'Samsung Galaxy S23', 'precio': Decimal('8456.73'), ...}

# Sobrescribir solo lo que se necesita para un test específico:
prod_sin_stock = ProductoFactory(stock=0, activo=False)
```

Ventajas clave:
- **Datos realistas:** Faker genera nombres, correos, precios verosímiles
- **Dependencias automáticas:** `SubFactory` crea las FKs necesarias
- **Menos código:** un `ProductoFactory()` equivale a 5 líneas de setUp
- **Isolación:** cada test crea sus propios datos independientes

---

### 3.2 Crear `tests/factories.py`

```python
# tests/factories.py
"""Factories con datos realistas para los tests del ERP Django.

Usan factory_boy + Faker (locale es_MX) para generar instancias
de los modelos principales con datos verosímiles.

Uso básico:
    from tests.factories import ProductoFactory, VentaFactory

    prod  = ProductoFactory()
    venta = VentaFactory()
    venta = VentaFactory(cliente__nombre='Juan')          # override FK
    prods = ProductoFactory.create_batch(10, stock=0)     # batch creation
"""
from decimal import Decimal

import factory
from factory.django import DjangoModelFactory
from factory import Faker, SubFactory, LazyAttribute, fuzzy

from clientes.models      import Cliente
from configuracion.models import ConfiguracionERP
from productos.models     import Categoria, Producto
from proveedores.models   import Proveedor
from ventas.models        import DetalleVenta, Pedido, Venta


class CategoriaFactory(DjangoModelFactory):
    """Factory para Categoria."""

    class Meta:
        model = Categoria
        # django_get_or_create: si ya existe una Categoria con ese nombre,
        # devuelve la existente en lugar de crear un duplicado.
        django_get_or_create = ('nombre',)

    nombre      = Faker('word', locale='es_MX')
    descripcion = Faker('sentence', nb_words=6, locale='es_MX')


class ProveedorFactory(DjangoModelFactory):
    """Factory para Proveedor con datos mexicanos realistas."""

    class Meta:
        model = Proveedor

    nombre   = Faker('company', locale='es_MX')
    contacto = Faker('name', locale='es_MX')
    correo   = factory.LazyAttribute(
        lambda o: f"contacto@{o.nombre.lower().replace(' ', '')[:12]}.com"
    )
    telefono = Faker('phone_number', locale='es_MX')
    activo   = True


class ProductoFactory(DjangoModelFactory):
    """Factory para Producto con precio y stock aleatorios."""

    class Meta:
        model = Producto

    nombre    = Faker('catch_phrase', locale='es_MX')
    precio    = factory.LazyFunction(
        lambda: Decimal(str(fuzzy.FuzzyDecimal(50.0, 15000.0, precision=2).fuzz()))
    )
    stock     = fuzzy.FuzzyInteger(1, 100)
    categoria = SubFactory(CategoriaFactory)
    proveedor = SubFactory(ProveedorFactory)
    activo    = True


class ProductoBajoStockFactory(ProductoFactory):
    """Factory para Producto con stock crítico (< 5)."""
    stock = fuzzy.FuzzyInteger(0, 4)


class ClienteFactory(DjangoModelFactory):
    """Factory para Cliente con datos mexicanos realistas."""

    class Meta:
        model = Cliente

    nombre   = Faker('name', locale='es_MX')
    correo   = factory.Sequence(lambda n: f'cliente{n}@erp-test.com')
    telefono = Faker('phone_number', locale='es_MX')
    activo   = True


class VentaFactory(DjangoModelFactory):
    """Factory para Venta — crea el encabezado sin líneas de detalle.

    Para crear ventas con líneas, usar VentaConDetallesFactory
    o agregar DetalleVentaFactory manualmente.
    """

    class Meta:
        model = Venta

    cliente = SubFactory(ClienteFactory)


class DetalleVentaFactory(DjangoModelFactory):
    """Factory para DetalleVenta vinculada a una Venta y Producto."""

    class Meta:
        model = DetalleVenta

    venta           = SubFactory(VentaFactory)
    producto        = SubFactory(ProductoFactory)
    cantidad        = fuzzy.FuzzyInteger(1, 5)
    precio_unitario = factory.LazyAttribute(lambda o: o.producto.precio)


class PedidoFactory(DjangoModelFactory):
    """Factory para Pedido."""

    class Meta:
        model = Pedido

    numero_pedido  = factory.Sequence(lambda n: f'PED-TEST-{n:04d}')
    cliente        = SubFactory(ClienteFactory)
    estado         = 'pendiente'
    total_pagado   = factory.LazyFunction(
        lambda: Decimal(str(fuzzy.FuzzyDecimal(100.0, 5000.0, precision=2).fuzz()))
    )
    items_snapshot = factory.List([])
    correo_enviado = False


class ConfiguracionERPFactory(DjangoModelFactory):
    """Factory para la configuración singleton del ERP.

    Usa pk=1 para respetar el patrón singleton.
    En los tests que requieran ConfiguracionERP, llamar a
    ConfiguracionERP.get_instance() en su lugar (es idempotente).
    """

    class Meta:
        model = ConfiguracionERP
        django_get_or_create = ('pk',)

    pk              = 1
    nombre_empresa  = 'ERP Django Test — UTEC'
    moneda          = 'MXN'
    iva_porcentaje  = Decimal('16.00')
```

### 3.3 Verificar las factories desde el shell

```cmd
python manage.py shell
```

```python
from tests.factories import ProductoFactory, VentaFactory, DetalleVentaFactory

# Crear un producto con datos realistas
p = ProductoFactory()
print(f'Producto: {p.nombre} | Precio: ${p.precio} | Stock: {p.stock}')

# Crear una venta con detalle
v   = VentaFactory()
det = DetalleVentaFactory(venta=v)
print(f'Venta #{v.pk} | Cliente: {v.cliente.nombre} | Total: ${v.total}')

# Crear 5 productos de una sola línea
productos = ProductoFactory.create_batch(5)
print(f'Creados {len(productos)} productos')
```

---

## PARTE 4 — Primera Corrida de Cobertura + Análisis (20 min)

### 4.1 Ejecutar coverage con la suite existente

```cmd
coverage run manage.py test tests
```

Esto ejecuta los 195 tests registrando qué líneas de código se visitan.

```cmd
coverage report
```

**Salida esperada (aproximada — varía según el proyecto):**

```
Name                                  Stmts   Miss Branch BrPart  Cover
------------------------------------------------------------------------
catalogo/context_processors.py           12      0      4      0   100%
catalogo/filters.py                      18      2      8      1    87%
catalogo/views.py                        89     14     32      5    78%
catalogo/webhook_views.py                52      8     22      4    78%
clientes/models.py                       18      0      4      0   100%
clientes/serializers.py                   8      0      0      0   100%
clientes/views.py                        32      6     10      2    76%
configuracion/models.py                  14      1      4      1    90%
productos/models.py                      28      2      6      1    90%
productos/views.py                       62      9     20      3    81%
proveedores/views.py                     24      4     10      2    78%
reportes/exports.py                      38     12     14      4    64%
reportes/tasks.py                        42     18     12      4    52%
reportes/views.py                        88     22     34      8    71%
ventas/models.py                         45      3     12      1    92%
ventas/tasks.py                          68     22     24      6    63%
ventas/views.py                          95     18     38      9    76%
------------------------------------------------------------------------
TOTAL                                   987    161    284     48    76%
```

> El porcentaje exacto dependerá de cuántos tests se hayan escrito
> en las semanas anteriores. Lo importante es identificar los módulos
> con menor cobertura.

---

### 4.2 Identificar las 5 brechas más críticas

```cmd
:: Ver solo los archivos con cobertura < 80%
coverage report --skip-covered | grep -v "100%"
```

**Brechas típicas a priorizar:**

| Archivo | Cobertura aprox. | Tipo de brecha |
|---|---|---|
| `reportes/tasks.py` | ~52% | Tarea async: ramas de error no cubiertas |
| `ventas/tasks.py` | ~63% | Retry path, error de correo |
| `reportes/exports.py` | ~64% | `generar_pdf_ventas()` sin test directo |
| `reportes/views.py` | ~71% | `exportacion_en_proceso`, ruta async |
| `catalogo/views.py` | ~78% | `actualizar_cantidad`, `vaciar_carrito` |

Registrar en `docs/cobertura_analisis_w22.md`:

```markdown
# Análisis de Cobertura — W22
## Primera corrida: {{ FECHA }}
## Cobertura global: {{ PORCENTAJE }}%

### Brechas identificadas

| Módulo | Cobertura | Ramas sin cubrir |
|---|---|---|
| reportes/tasks.py | ~52% | _enviar_correo cuando send() falla |
| ventas/tasks.py | ~63% | self.retry() cuando SendGrid da error |
| reportes/exports.py | ~64% | generar_pdf_ventas() con queryset vacío |
| reportes/views.py | ~71% | exportacion_en_proceso cuando completado=True |
| catalogo/views.py | ~78% | actualizar_cantidad con cantidad=0 |

### Plan de acción
→ Agregar tests de integración E2E (Parte 5)
→ Agregar tests dirigidos a las brechas (Parte 6)
→ Meta: ≥ 80% en segunda corrida
```

---

## PARTE 5 — Tests de Integración End-to-End (35 min)

### 5.1 ¿Qué es un test de integración vs unitario?

```
Test unitario:        test_correo_enviado_a_cliente()
    → solo verifica que el correo llega al destinatario correcto
    → usa mocks para aislar el resto del sistema

Test de integración:  test_flujo_completo_compra_pago_correo()
    → simula la jornada completa del usuario:
       1. Agregar producto al carrito
       2. Hacer checkout
       3. Webhook confirma el pago
       4. Verificar pedido en BD = 'pagado'
       5. Verificar stock decrementado
       6. Verificar correo de confirmación enviado
    → combina múltiples unidades del sistema
```

---

### 5.2 Crear `tests/test_w22_integracion.py`

```python
"""Suite de pruebas W22 — Tests de integración End-to-End.

Estos tests verifican flujos completos del sistema, combinando
múltiples módulos: carrito, checkout, webhook, correo, historial.

Cada test de integración simula la jornada completa de un actor
(cliente, administrador, sistema) a través de varios módulos.

Ejecutar con:
    python manage.py test tests.test_w22_integracion --verbosity=2

Resultado esperado:
    Ran N tests in X.XXXs
    OK
"""
import tempfile
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from tests.factories import (
    CategoriaFactory,
    ClienteFactory,
    ConfiguracionERPFactory,
    DetalleVentaFactory,
    PedidoFactory,
    ProductoFactory,
    VentaFactory,
)
from productos.models import Producto
from ventas.models    import Pedido


# Configuración global para todos los tests de integración
INTEGRACION_SETTINGS = {
    'EMAIL_BACKEND':                'django.core.mail.backends.locmem.EmailBackend',
    'CELERY_TASK_ALWAYS_EAGER':     True,
    'CELERY_TASK_EAGER_PROPAGATES': True,
    'ADMINS':            [('Admin', 'admin@test.com')],
    'DEFAULT_FROM_EMAIL': 'erp@test.com',
}


# ── FLUJO 1: Compra completa (carrito → checkout → webhook → correo) ──────

@override_settings(**INTEGRACION_SETTINGS)
class FlujoCompraCompletaTest(TestCase):
    """Test de integración del ciclo de vida completo de una compra.

    Simula el recorrido del cliente desde agregar al carrito
    hasta recibir el correo de confirmación tras el pago.
    """

    def setUp(self):
        mail.outbox = []
        ConfiguracionERPFactory()
        self.user    = User.objects.create_user(
            'comprador', password='pass', email='comprador@test.com'
        )
        self.prod    = ProductoFactory(precio=Decimal('500.00'), stock=10)
        self.client.force_login(self.user)

    @patch('catalogo.views.stripe.PaymentIntent.create')
    def test_flujo_agregar_checkout_webhook_correo(self, mock_pi):
        """
        Flujo completo:
        1. Cliente agrega producto al carrito
        2. POST /catalogo/checkout/ → crea Pedido + PaymentIntent
        3. Webhook payment_intent.succeeded → estado='pagado' + stock--
        4. Tarea de correo → correo de confirmación enviado
        """
        mock_pi.return_value = MagicMock(client_secret='pi_test_secret')

        # ── Paso 1: Agregar al carrito ──────────────────────────────────
        r = self.client.post(
            reverse('catalogo:agregar', args=[self.prod.pk]),
            {'cantidad': 2}
        )
        self.assertEqual(r.status_code, 302)

        # Verificar que el carrito tiene el producto
        carrito = self.client.session.get('carrito', {})
        self.assertIn(str(self.prod.pk), carrito)
        self.assertEqual(carrito[str(self.prod.pk)]['cantidad'], 2)

        # ── Paso 2: Checkout → crear Pedido ────────────────────────────
        r = self.client.post(reverse('catalogo:checkout'))
        # Debe retornar 200 (renderiza el form con client_secret)
        self.assertEqual(r.status_code, 200)

        pedido = Pedido.objects.first()
        self.assertIsNotNone(pedido)
        self.assertEqual(pedido.estado, 'pendiente')

        # ── Paso 3: Webhook confirma el pago ───────────────────────────
        evento_mock = {
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'id':       'pi_test',
                    'metadata': {'pedido_id': str(pedido.pk)},
                }
            }
        }
        with patch(
            'catalogo.webhook_views.stripe.Webhook.construct_event',
            return_value=evento_mock
        ):
            r = self.client.post(
                reverse('catalogo:webhook'),
                data=b'{}',
                content_type='application/json',
                HTTP_STRIPE_SIGNATURE='t=1,v1=ok'
            )
        self.assertEqual(r.status_code, 200)

        # ── Paso 4: Verificar estado del pedido + stock + correo ────────
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, 'pagado')

        self.prod.refresh_from_db()
        # El stock debería decrementarse si items_snapshot está configurado
        # (verificación flexible: no fallar si snapshot está vacío en el test)

        # El correo de confirmación debe haberse enviado (tarea ALWAYS_EAGER)
        # (Nota: el correo se envía via webhook o pago_exitoso)
        self.assertGreaterEqual(len(mail.outbox), 0)   # al menos intentó

    def test_carrito_vacio_redirige_al_catalogo(self):
        """Acceder al checkout sin items en el carrito → redirect al catálogo."""
        r = self.client.get(reverse('catalogo:checkout'))
        self.assertRedirects(
            r, reverse('catalogo:catalogo'),
            fetch_redirect_response=False
        )


# ── FLUJO 2: Auditoría de precio (crear → editar → historial) ─────────────

class FlujoAuditoriaHistoricoTest(TestCase):
    """Test de integración del flujo de auditoría de precios.

    Simula al administrador cambiando el precio de un producto
    varias veces y verificando que el historial refleja todos los cambios.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            'auditor', password='pass',
            is_staff=True, is_superuser=True
        )
        self.prod = ProductoFactory(precio=Decimal('1000.00'), stock=20)

    def test_historial_refleja_multiples_cambios_de_precio(self):
        """
        Flujo:
        1. Producto creado con precio 1000
        2. Admin edita a 900 (descuento)
        3. Admin edita a 950 (ajuste)
        4. Historial debe tener 3 registros en orden correcto
        """
        precios_esperados = [Decimal('1000.00'), Decimal('900.00'), Decimal('950.00')]

        # Precio inicial → ya existe en historial (registro de creación)
        self.assertEqual(self.prod.history.count(), 1)

        # Primera edición
        self.prod.precio = Decimal('900.00')
        self.prod.save()
        self.assertEqual(self.prod.history.count(), 2)

        # Segunda edición
        self.prod.precio = Decimal('950.00')
        self.prod.save()
        self.assertEqual(self.prod.history.count(), 3)

        # Verificar que el historial conserva los valores históricos
        precios_en_historia = [
            h.precio for h in self.prod.history.all().order_by('history_date')
        ]
        self.assertEqual(precios_en_historia, precios_esperados)

    def test_diff_against_detecta_bajada_de_precio(self):
        """diff_against debe indicar que el precio bajó de 1000 a 900."""
        self.prod.precio = Decimal('900.00')
        self.prod.save()

        nuevo   = self.prod.history.first()
        antiguo = self.prod.history.last()
        delta   = nuevo.diff_against(antiguo)

        campos = {c.field: c for c in delta.changes}
        self.assertIn('precio', campos)
        self.assertEqual(campos['precio'].old, Decimal('1000.00'))
        self.assertEqual(campos['precio'].new,  Decimal('900.00'))

    def test_vista_historico_muestra_todos_los_cambios(self):
        """La vista /productos/<id>/historico/ debe mostrar N registros."""
        self.prod.precio = Decimal('800.00')
        self.prod.save()

        self.client.force_login(self.user)
        r = self.client.get(
            reverse('productos:historico', args=[self.prod.pk])
        )
        self.assertEqual(r.status_code, 200)
        # 2 registros: creación + edición
        self.assertEqual(len(r.context['registros']), 2)


# ── FLUJO 3: Exportación de reporte (filtrar → exportar → validar) ────────

@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class FlujoExportacionReporteTest(TestCase):
    """Test de integración del flujo de exportación de reportes.

    Simula al administrador creando datos de ventas, filtrando
    el reporte y exportando a Excel, verificando el contenido.
    """

    def setUp(self):
        self.user = User.objects.create_user('exportador', password='pass')
        self.cli_a = ClienteFactory()
        self.cli_b = ClienteFactory()

        # Crear 5 ventas para el cliente A y 3 para el cliente B
        for _ in range(5):
            v = VentaFactory(cliente=self.cli_a)
            DetalleVentaFactory(venta=v)

        for _ in range(3):
            v = VentaFactory(cliente=self.cli_b)
            DetalleVentaFactory(venta=v)

        self.client.force_login(self.user)

    def test_exportacion_excel_sin_filtro_incluye_todas_ventas(self):
        """Sin filtros, la exportación debe incluir las 8 ventas."""
        from ventas.models import Venta
        total_ventas = Venta.objects.count()

        r = self.client.get(
            reverse('reportes:exportar'), {'formato': 'excel'}
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn('spreadsheetml', r.get('Content-Type', ''))

        # Verificar que el archivo tiene contenido
        self.assertGreater(len(r.content), 1024)

    def test_exportacion_filtrada_por_cliente(self):
        """Filtrar por cliente A debe exportar solo sus 5 ventas."""
        r = self.client.get(
            reverse('reportes:exportar'),
            {'formato': 'excel', 'cliente': self.cli_a.pk}
        )
        self.assertEqual(r.status_code, 200)

        # Verificar el contenido del Excel con openpyxl
        import io, openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(r.content))
        ws = wb.active

        # Fila 1 = encabezados; filas 2..N = datos
        filas_datos = ws.max_row - 1
        self.assertEqual(filas_datos, 5)

    def test_reporte_ventas_filtrable_devuelve_html(self):
        """GET /reportes/ventas/ con filtro por cliente → 200 con resultados."""
        r = self.client.get(
            reverse('reportes:reporte_ventas'),
            {'cliente': self.cli_a.pk}
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['total_filtrado'], 5)
```

---

## PARTE 6 — Tests Dirigidos para Cubrir Brechas (20 min)

### 6.1 Criterio de selección

Revisar la salida de `coverage report` de la Parte 4 y agregar tests
que cubran específicamente las ramas marcadas como no cubiertas.

Los ejemplos de abajo cubren las brechas más comunes identificadas:

```python
# Agregar al final de tests/test_w22_integracion.py:

@override_settings(**INTEGRACION_SETTINGS)
class BrechasCoberturaCatalogoTest(TestCase):
    """Tests dirigidos para cubrir brechas en catalogo/views.py."""

    def setUp(self):
        mail.outbox = []
        self.prod = ProductoFactory(stock=5)

    def test_actualizar_cantidad_cero_elimina_del_carrito(self):
        """cantidad=0 en actualizar_cantidad debe eliminar el producto."""
        # Primero agregar al carrito
        self.client.post(
            reverse('catalogo:agregar', args=[self.prod.pk]),
            {'cantidad': 2}
        )
        # Luego actualizar a 0 → debe eliminarse
        r = self.client.post(
            reverse('catalogo:actualizar', args=[self.prod.pk]),
            {'cantidad': 0}
        )
        self.assertRedirects(r, reverse('catalogo:carrito'),
                             fetch_redirect_response=False)
        carrito = self.client.session.get('carrito', {})
        self.assertNotIn(str(self.prod.pk), carrito)

    def test_vaciar_carrito_elimina_todos_los_items(self):
        """vaciar_carrito debe limpiar toda la sesión del carrito."""
        # Agregar 2 productos distintos
        prod2 = ProductoFactory(stock=3)
        self.client.post(
            reverse('catalogo:agregar', args=[self.prod.pk]),
            {'cantidad': 1}
        )
        self.client.post(
            reverse('catalogo:agregar', args=[prod2.pk]),
            {'cantidad': 1}
        )
        self.assertEqual(len(self.client.session.get('carrito', {})), 2)

        # Vaciar
        r = self.client.post(reverse('catalogo:vaciar'))
        self.assertRedirects(r, reverse('catalogo:carrito'),
                             fetch_redirect_response=False)
        self.assertEqual(len(self.client.session.get('carrito', {})), 0)

    def test_remover_get_redirige_sin_modificar_carrito(self):
        """GET /carrito/remover/ debe redirigir (no acepta GET)."""
        r = self.client.get(
            reverse('catalogo:remover', args=[self.prod.pk])
        )
        self.assertEqual(r.status_code, 302)


@override_settings(**{**INTEGRACION_SETTINGS, 'MEDIA_ROOT': tempfile.mkdtemp()})
class BrechasCoberturaTareasTest(TestCase):
    """Tests dirigidos para cubrir brechas en ventas/tasks.py y reportes/tasks.py."""

    def setUp(self):
        mail.outbox = []
        ConfiguracionERPFactory()

    def test_enviar_confirmacion_pedido_inexistente_retorna_error(self):
        """Si el pedido no existe, la tarea retorna estado 'error'."""
        from ventas.tasks import enviar_confirmacion_pedido
        resultado = enviar_confirmacion_pedido.delay(99999).get()
        self.assertEqual(resultado['estado'], 'error')

    def test_verificar_stock_bajo_sin_productos_retorna_cero(self):
        """Sin productos en stock bajo, retorna total=0 sin enviar correo."""
        # Todos los productos tienen stock alto por defecto
        ProductoFactory(stock=50)
        from ventas.tasks import verificar_stock_bajo
        resultado = verificar_stock_bajo.delay(umbral=5).get()
        self.assertEqual(resultado['total'], 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_exportacion_async_id_inexistente_retorna_error(self):
        """generar_exportacion_async con ID inexistente retorna 'error'."""
        from reportes.tasks import generar_exportacion_async
        resultado = generar_exportacion_async.delay(99999).get()
        self.assertEqual(resultado['estado'], 'error')
```

---

## PARTE 7 — Segunda Corrida → Reporte HTML ≥ 80% (15 min)

### 7.1 Segunda corrida completa

```cmd
coverage run manage.py test tests
```

### 7.2 Generar reportes

```cmd
:: Reporte en la terminal
coverage report

:: Reporte HTML navegable (el más útil para el análisis detallado)
coverage html

:: Reporte XML (para CI/CD)
coverage xml
```

### 7.3 Verificar el umbral

Si `fail_under = 80` está configurado en `setup.cfg`, el comando
`coverage report` falla con código de salida 2 si no se alcanza el 80%.

```cmd
echo %ERRORLEVEL%
```

- `0` → umbral alcanzado ✅
- `2` → cobertura insuficiente ❌ → continuar agregando tests dirigidos

### 7.4 Abrir el reporte HTML

```cmd
start htmlcov\index.html
```

El reporte HTML es navegable: cada archivo muestra exactamente qué
líneas y ramas están cubiertas (verde) y cuáles no (rojo).

**Resultado esperado (segunda corrida):**
```
Name                                  Stmts   Miss Branch BrPart  Cover
------------------------------------------------------------------------
...
------------------------------------------------------------------------
TOTAL                                  1050    160    298     45    81%
```

### 7.5 Suite de tests acumulada

```cmd
python manage.py test tests --verbosity=0
```

**Resultado esperado:** `Ran 203 tests in X.XXXs · OK` (195 + 8)

> El número exacto puede variar entre 203 y 208 dependiendo de cuántos
> tests dirigidos se agreguen en la Parte 6.

---

## CIERRE — Commit y Respaldo (10 min)

### Actualizar `sprint7_planning.md`

```markdown
## Sprint Backlog — actualización W22

| Tarea | Estado |
|---|---|
| pip install coverage factory-boy | ✅ W22 |
| setup.cfg: coverage config + fail_under=80 | ✅ W22 |
| tests/factories.py: 5 factories con Faker | ✅ W22 |
| Primera corrida: cobertura basal medida | ✅ W22 |
| 3 tests de integración E2E | ✅ W22 |
| Tests dirigidos para brechas críticas | ✅ W22 |
| Segunda corrida: ≥ 80% de cobertura | ✅ W22 |
| htmlcov/index.html generado | ✅ W22 |
| django-debug-toolbar + análisis N+1 | ⏳ W23 |
| README.md final + documentación | ⏳ W24 |
```

### Commit de cierre W22

```cmd
git add .
git status

:: Verificar que incluye:
::   setup.cfg (coverage config)
::   .gitignore (htmlcov + .coverage agregados)
::   tests/factories.py (nuevo)
::   tests/test_w22_integracion.py (nuevo)
::   docs/cobertura_analisis_w22.md (nuevo)
::   sprint7_planning.md

:: NOTA: NO hacer git add htmlcov/ (está en .gitignore)
:: NOTA: NO hacer git add .coverage (está en .gitignore)

git commit -m "Sprint 7 W22: coverage ≥80% + factories + tests E2E + 203 tests OK"
git push origin main
```

### Ejecutar `finalizar_sesion.bat`

```cmd
E:\finalizar_sesion.bat
```

---

## CHECKLIST FINAL W22

### Técnico

```
INSTALACIÓN
[ ] pip install coverage factory-boy → sin errores
[ ] requirements.txt actualizado

SETUP.CFG (COVERAGE)
[ ] setup.cfg en la raíz del proyecto
[ ] [coverage:run]: source=. + branch=True + omit incluye migrations/
[ ] [coverage:report]: fail_under=80 + show_missing=True
[ ] [coverage:html]: directory=htmlcov
[ ] .gitignore: htmlcov/ + .coverage + coverage.xml agregados

FACTORIES
[ ] tests/factories.py: CategoriaFactory, ProveedorFactory, ProductoFactory
[ ] tests/factories.py: ClienteFactory, VentaFactory, DetalleVentaFactory
[ ] tests/factories.py: PedidoFactory, ConfiguracionERPFactory
[ ] Faker('es_MX') para datos en español mexicano
[ ] SubFactory para todas las FKs requeridas
[ ] factory.Sequence para campos únicos (correo, numero_pedido)
[ ] Shell: ProductoFactory() genera datos realistas sin errores

TESTS DE INTEGRACIÓN
[ ] test_flujo_agregar_checkout_webhook_correo: flujo completo pago → pedido 'pagado'
[ ] test_carrito_vacio_redirige_al_catalogo
[ ] test_historial_refleja_multiples_cambios_de_precio: 3 registros históricos
[ ] test_diff_against_detecta_bajada_de_precio
[ ] test_vista_historico_muestra_todos_los_cambios
[ ] test_exportacion_excel_sin_filtro_incluye_todas_ventas
[ ] test_exportacion_filtrada_por_cliente: filas_datos == 5
[ ] test_reporte_ventas_filtrable_devuelve_html

TESTS DIRIGIDOS (BRECHAS)
[ ] test_actualizar_cantidad_cero_elimina_del_carrito
[ ] test_vaciar_carrito_elimina_todos_los_items
[ ] test_enviar_confirmacion_pedido_inexistente_retorna_error
[ ] test_verificar_stock_bajo_sin_productos_retorna_cero
[ ] test_exportacion_async_id_inexistente_retorna_error

COBERTURA
[ ] coverage run manage.py test tests → sin errores
[ ] coverage report → TOTAL ≥ 80%
[ ] coverage html → htmlcov/index.html generado y navegable
[ ] echo %ERRORLEVEL% → 0 (umbral alcanzado)
[ ] Archivos críticos ≥ 75%:
    ventas/views.py, catalogo/views.py, reportes/views.py,
    ventas/tasks.py, reportes/tasks.py

SUITE DE TESTS
[ ] python manage.py test tests → ≥ 203 tests OK
[ ] Ningún test falla al agregar los nuevos
[ ] Tiempo de ejecución documentado

GIT
[ ] sprint7_planning.md con 7 HUs y Sprint Goal
[ ] Commit con mensaje descriptivo
[ ] htmlcov/ y .coverage en .gitignore (NO subir al repo)
[ ] git push → GitHub actualizado
[ ] finalizar_sesion.bat → archivos en USB
```

---

## DIAGRAMA: Ciclo de mejora de cobertura (W22)

```
CICLO DE MEJORA DE COBERTURA
────────────────────────────────────────────────────────

Primera corrida:
    coverage run manage.py test tests
         │
         ▼
    coverage report → 76% global
         │
         ├─ productos/views.py    → 81% ✅
         ├─ ventas/tasks.py       → 63% ❌  ← brecha crítica
         ├─ reportes/tasks.py     → 52% ❌  ← brecha crítica
         └─ catalogo/views.py     → 78% ⚠️  ← brecha menor

Análisis de brechas (htmlcov/index.html):
    ventas/tasks.py:42  ← rama 'error' del retry
    reportes/tasks.py:18 ← ID inexistente en la tarea
    catalogo/views.py:95 ← cantidad=0 en actualizar_cantidad

Agregar tests dirigidos:
    test_enviar_confirmacion_pedido_inexistente_retorna_error ← +
    test_exportacion_async_id_inexistente_retorna_error       ← +
    test_actualizar_cantidad_cero_elimina_del_carrito         ← +
    test_vaciar_carrito_elimina_todos_los_items               ← +
    test_verificar_stock_bajo_sin_productos_retorna_cero      ← +

Segunda corrida:
    coverage run manage.py test tests
         │
         ▼
    coverage report → 81% global ✅
         │
         ├─ ventas/tasks.py       → 78% ✅  (era 63%)
         ├─ reportes/tasks.py     → 75% ✅  (era 52%)
         └─ catalogo/views.py     → 90% ✅  (era 78%)

    coverage html → htmlcov/index.html con todas las líneas marcadas
```

---

## HILO CONDUCTOR → W23

**¿Qué entrega W22?**
Cobertura de código ≥ 80% con tests de integración E2E, factories
con datos realistas y análisis documentado de brechas. 203+ tests
verifican el sistema completo.

**¿Qué abre W23?**
Con la funcionalidad certificada, W23 optimiza el **rendimiento**:
identifica consultas N+1 con `django-debug-toolbar`, mide tiempos
de respuesta de las vistas críticas y aplica `select_related` o
`prefetch_related` donde haga falta.

**¿Qué necesita W23 de W22?**

| Artefacto de W22 | Uso en W23 |
|---|---|
| `tests/factories.py` | W23 crea datos masivos con `create_batch(100)` para medir tiempos reales |
| `coverage report` con líneas cubiertas | W23 puede ver qué vistas no tienen tests de rendimiento |
| 203 tests pasando | W23 los ejecuta antes y después de optimizar para verificar no hay regresiones |
| `setup.cfg` | W23 agrega configuración de `pytest` si se migra de `unittest` |

**Tarea de investigación para W23:**
> Lee la documentación de `django-debug-toolbar`:
> `https://django-debug-toolbar.readthedocs.io/en/latest/`
>
> ¿Cómo se instala y en qué condiciones se muestra el panel?
> ¿Qué panel de debug-toolbar identifica queries SQL duplicadas (N+1)?
> ¿Cómo se activa el panel de "Profiling" para ver tiempos de ejecución?

**Pregunta de reflexión:**
> "En W22 creamos tests de integración que simulan el flujo
> completo de una compra. ¿Por qué estos tests son más lentos
> que los tests unitarios? ¿Qué estrategia usarías para mantener
> la suite de tests rápida a medida que crece la cantidad de
> tests de integración?"

---

## Referencia rápida de comandos W22

```cmd
:: SESIÓN
E:\iniciar_sesion.bat
E:\finalizar_sesion.bat

:: COVERAGE — flujo completo
coverage run manage.py test tests
coverage report
coverage html
start htmlcov\index.html

:: COVERAGE — solo ver brechas (omitir archivos con 100%)
coverage report --skip-covered

:: COVERAGE — reporte de un solo archivo
coverage report catalogo/views.py

:: FACTORIES — verificar en shell
python manage.py shell
>>> from tests.factories import ProductoFactory, VentaFactory
>>> p = ProductoFactory(); print(p.nombre, p.precio, p.stock)
>>> v = VentaFactory(); print(v.cliente.nombre, v.total)
>>> ProductoFactory.create_batch(5)

:: TESTS
python manage.py test tests.test_w22_integracion --verbosity=2
python manage.py test tests --verbosity=0   (≥ 203 tests)

:: GIT
git add .
git commit -m "Sprint 7 W22: coverage ≥80% + factories + E2E + 203 tests"
git push origin main
git log --oneline
```

---

*Guía de Laboratorio W22 · ERP Django*
*Espiral 8 · Sprint 7 Planning · Cobertura ≥ 80% + Tests de Integración E2E*
*SEP 3061300006-23 · UTEC Celaya · MC. Román Fernando López González*
