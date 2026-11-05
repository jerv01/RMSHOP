# **PRODUCT BACKLOG REFINADO**

## **1\. Visión y Arquetipos**

**Visión del Producto**

RM Shop es una plataforma web que centraliza el catálogo de la marca de ropa RM y permite a sus clientes del Valle del Cauca comprar y pagar en línea (tarjeta débito o Nequi), con apoyo de un chatbot de IA. Brinda a la propietaria y a los administradores un panel para gestionar productos, inventario, descuentos, pedidos y analítica. Con ello amplía el alcance de la marca de ropa RM y reduce la gestión manual de pedidos.

**Arquetipos de Usuario**

* **Visitante sin cuenta:** persona que navega el sitio y el catálogo sin registrarse; no puede agregar al carrito ni usar el chatbot.  
* **Cliente registrado:** persona con cuenta verificada que agrega productos al carrito, paga, sigue sus pedidos y usa el chatbot; no cambia estados directamente.  
* **Administrador:** una de máximo 3 personas (incluida la propietaria Libia Palacios), con permisos idénticos y cuenta separada, que gestiona productos, inventario, descuentos, pedidos y analítica.

## **2\. Backlog con Criterios de Aceptación**

**Convenciones:**

* Los IDs conservan el formato de la entrada (HU-N).  
* Los umbrales numéricos de las restricciones no funcionales que no provienen de la entrada son \[SUPUESTO\] (ver pregunta P-1).  
* Las divisiones propuestas (HU-52b, HU-53b, HU-62b) se registran en la sección 3\.

---

### **ÉPICA 1: Catálogo de Productos (CATA)**

#### **Feature 1.1: Exploración del catálogo**

**HU-1** \[SIN-IA\]

* Actor(es): Visitante sin cuenta  
* Descripción: Como Visitante sin cuenta, quiero ver el catálogo de prendas de RM sin necesidad de registrarme, para conocer los productos antes de crear una cuenta.  
* Detalles de la HU:  
  * Tareas funcionales: listar los productos publicados; permitir el acceso sin sesión.  
  * Entrada: acceso al sitio sin sesión \| Proceso: se obtienen los productos publicados \| Salida: listado con nombre, foto principal y precio vigente de cada producto.  
  * Flujo de interfaz (texto): el visitante entra a la página principal, ve la cuadrícula de productos y puede desplazarse por ella.  
  * Reglas de negocio y datos: catálogo de menos de 30 productos, exclusivamente de RM. Un producto sin variantes publicadas no se lista. \[SUPUESTO\]  
* Restricciones (requerimientos no funcionales):  
  * El listado se muestra completo en 3 segundos o menos con conexión móvil estándar.  
  * No se solicita ningún dato personal para ver el catálogo.  
  * El catálogo está disponible al menos el 99 % del tiempo mensual.  
* Criterios de aceptación:  
  * AC-HU-1-1 (Camino feliz): Dado un visitante sin sesión, cuando abre la página principal, entonces ve los productos publicados con nombre, foto y precio.  
  * AC-HU-1-2 (Alternativo/Error): Dado que no hay productos publicados, cuando el visitante abre el catálogo, entonces ve un mensaje "No hay productos disponibles por el momento" sin errores técnicos.  
  * AC-HU-1-3 (Caso límite): Dado un catálogo con 30 productos, cuando el visitante lo recorre, entonces todos se muestran sin duplicados ni omisiones.  
* Dependencias: Ninguna  
* Pre-chequeo DoR: \[1\] Calidad: Sí (clara y testeable) \| \[2\] Criterios: Sí \| \[3\] Dependencias: Sí (sin dependencias) \| \[4-6\] Se evalúan en Etapa 3

**HU-2** \[SIN-IA\]

* Actor(es): Visitante sin cuenta  
* Descripción: Como Visitante sin cuenta, quiero filtrar o navegar las prendas por categoría (Camisetas / Tops, Buzos / Sacos, Pantalones / Jeans, Conjuntos), para encontrar rápidamente lo que busco.  
* Detalles de la HU:  
  * Tareas funcionales: mostrar las 4 categorías; filtrar el listado por la categoría elegida; quitar el filtro.  
  * Entrada: categoría seleccionada \| Proceso: se filtra el listado \| Salida: solo los productos de esa categoría.  
  * Flujo de interfaz (texto): en el catálogo el visitante ve las 4 categorías, elige una y el listado se actualiza. Puede volver a ver "Todos".  
  * Reglas de negocio y datos: las 4 categorías iniciales son fijas. Cada producto pertenece a una categoría.  
* Restricciones (requerimientos no funcionales):  
  * El listado filtrado se actualiza en 2 segundos o menos.  
  * Las categorías son operables con teclado.  
* Criterios de aceptación:  
  * AC-HU-2-1 (Camino feliz): Dado el catálogo visible, cuando el visitante elige "Buzos / Sacos", entonces solo se muestran productos de esa categoría.  
  * AC-HU-2-2 (Alternativo/Error): Dada una categoría sin productos, cuando se selecciona, entonces se muestra "No hay productos en esta categoría".  
  * AC-HU-2-3 (Caso límite): Dado un filtro activo, cuando el visitante elige "Todos", entonces se muestra de nuevo el catálogo completo.  
* Dependencias: HU-1  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí \| \[3\] Dependencias: Sí (HU-1 existe) \| \[4-6\] Se evalúan en Etapa 3

**HU-3** \[SIN-IA\]

* Actor(es): Cliente registrado (ver observación en sección 3 sobre el actor)  
* Descripción: Como Cliente registrado, quiero ver el detalle de una prenda (nombre, descripción, precio, material, fotografías, diseño), para decidir si deseo comprarla.  
* Detalles de la HU:  
  * Tareas funcionales: abrir la ficha de un producto; mostrar sus atributos y fotografías.  
  * Entrada: producto seleccionado \| Proceso: se carga la ficha \| Salida: nombre, descripción, precio, material, fotografías y diseño.  
  * Flujo de interfaz (texto): desde el catálogo el cliente toca un producto y llega a su ficha, donde ve las fotos y los datos, con opciones de color y talla (HU-4).  
  * Reglas de negocio y datos: atributos: nombre, descripción, precio, material, fotografías, diseño. Un diseño es un estampado distinto de una misma prenda en un modelo/corte específico.  
* Restricciones (requerimientos no funcionales):  
  * La ficha se muestra en 3 segundos o menos con conexión móvil estándar.  
  * Todas las fotografías tienen texto alternativo.  
* Criterios de aceptación:  
  * AC-HU-3-1 (Camino feliz): Dado un cliente con sesión, cuando abre un producto, entonces ve nombre, descripción, precio, material, fotos y diseño.  
  * AC-HU-3-2 (Alternativo/Error): Dado un producto despublicado o eliminado, cuando se intenta abrir su ficha, entonces se muestra "Producto no disponible" y un enlace al catálogo.  
  * AC-HU-3-3 (Caso límite): Dado un producto con una sola fotografía o con varias, cuando se abre la ficha, entonces se muestran todas las existentes sin espacios vacíos.  
* Dependencias: HU-1  
* Pre-chequeo DoR: \[1\] Calidad: No (el actor es Cliente registrado, pero HU-1 permite a visitantes navegar; ver P-18) \| \[2\] Criterios: Sí \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-4** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero seleccionar el color y la talla de un diseño, para elegir la variante exacta que quiero comprar.  
* Detalles de la HU:  
  * Tareas funcionales: mostrar los colores y tallas del diseño; seleccionar una combinación; mostrar su disponibilidad.  
  * Entrada: color y talla elegidos \| Proceso: se valida la combinación y su stock \| Salida: variante seleccionada y su disponibilidad.  
  * Flujo de interfaz (texto): en la ficha, el cliente elige color y talla; la ficha muestra si la combinación está disponible o "Agotado" y habilita "Agregar al carrito" solo si hay stock.  
  * Reglas de negocio y datos: un diseño tiene múltiples colores y tallas. El stock se controla por combinación diseño/talla/color.  
* Restricciones (requerimientos no funcionales):  
  * La disponibilidad se actualiza en 1 segundo o menos tras elegir la variante.  
  * Los selectores son operables con teclado.  
* Criterios de aceptación:  
  * AC-HU-4-1 (Camino feliz): Dado un diseño con varias variantes, cuando el cliente elige color y talla con stock, entonces queda seleccionada la variante y se habilita "Agregar al carrito".  
  * AC-HU-4-2 (Alternativo/Error): Dada una combinación sin stock, cuando se selecciona, entonces se muestra "Agotado" y no se permite agregarla.  
  * AC-HU-4-3 (Caso límite): Dado un diseño con una sola talla y un solo color, cuando se abre la ficha, entonces esa variante aparece preseleccionada. \[SUPUESTO\]  
* Dependencias: HU-3  
* Pre-chequeo DoR: \[1\] Calidad: No (actor en conflicto, ver P-18) \| \[2\] Criterios: Sí \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-5** \[SIN-IA\]

* Actor(es): Visitante sin cuenta  
* Descripción: Como Visitante sin cuenta, quiero ver el indicador "Agotado" en las combinaciones sin stock, para saber qué variantes no están disponibles.  
* Detalles de la HU:  
  * Tareas funcionales: mostrar "Agotado" en variantes con stock 0; ocultar la acción de compra en ellas.  
  * Entrada: stock de la combinación \| Proceso: se compara contra 0 \| Salida: indicador "Agotado" visible.  
  * Flujo de interfaz (texto): en el catálogo o la ficha, la variante sin stock aparece marcada "Agotado" y deshabilitada.  
  * Reglas de negocio y datos: stock 0 equivale a "Agotado". Lo ya reservado en carritos (HU-17) no cuenta como disponible. \[SUPUESTO\]  
* Restricciones (requerimientos no funcionales):  
  * El indicador refleja el stock real con un retraso máximo de 5 segundos tras un cambio.  
  * El indicador no depende solo del color (incluye texto).  
* Criterios de aceptación:  
  * AC-HU-5-1 (Camino feliz): Dada una variante con stock 0, cuando el visitante ve el producto, entonces ve "Agotado" en esa variante.  
  * AC-HU-5-2 (Alternativo/Error): Dada una variante agotada, cuando el visitante intenta seleccionarla, entonces no se permite agregarla.  
  * AC-HU-5-3 (Caso límite): Dada una variante con stock 0 por reservas en carritos, cuando se libera la reserva, entonces el indicador desaparece y la variante vuelve a estar disponible. \[SUPUESTO\]  
* Dependencias: HU-1, HU-37  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-6** \[SIN-IA\]

* Actor(es): Visitante sin cuenta  
* Descripción: Como Visitante sin cuenta, quiero ver el precio anterior junto al precio vigente cuando una prenda tiene descuento, para identificar el ahorro.  
* Detalles de la HU:  
  * Tareas funcionales: mostrar precio anterior tachado junto al precio vigente en productos con descuento.  
  * Entrada: producto con descuento activo \| Proceso: se compara precio anterior y vigente \| Salida: ambos precios visibles.  
  * Flujo de interfaz (texto): en el listado y la ficha, el producto muestra el precio anterior tachado y el vigente.  
  * Reglas de negocio y datos: el precio anterior es un atributo del producto. Los descuentos no son acumulables. El backlog no contiene una historia que cree o gestione descuentos (ver sección 5).  
* Restricciones (requerimientos no funcionales):  
  * Ambos precios se muestran en pesos colombianos con separador de miles.  
  * El precio vigente es el mismo en listado, ficha y carrito (0 discrepancias).  
* Criterios de aceptación:  
  * AC-HU-6-1 (Camino feliz): Dado un producto con descuento activo, cuando el visitante lo ve, entonces aparecen el precio anterior tachado y el vigente.  
  * AC-HU-6-2 (Alternativo/Error): Dado un producto sin descuento, cuando se muestra, entonces solo aparece el precio vigente.  
  * AC-HU-6-3 (Caso límite): Dado un descuento cuyo período terminó, cuando se consulta el producto, entonces ya no muestra el precio anterior. \[SUPUESTO\]  
* Dependencias: HU-1; historia de gestión de descuentos (no existe en el backlog)  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: No (depende de una funcionalidad de descuentos ausente) \| \[4-6\] Se evalúan en Etapa 3

#### **Feature 1.2 se cubre arriba (HU-4 a HU-6)**

---

### **ÉPICA 2: Autenticación y Cuentas (AUTH)**

#### **Feature 2.1: Registro y verificación de clientes**

**HU-7** \[SIN-IA\]

* Actor(es): Visitante sin cuenta  
* Descripción: Como Visitante sin cuenta, quiero registrarme con mi correo y una contraseña, para poder agregar productos al carrito, comprar y usar el chatbot.  
* Detalles de la HU:  
  * Tareas funcionales: formulario de registro; validar datos; crear cuenta pendiente de verificación.  
  * Entrada: correo y contraseña \| Proceso: validación de formato y unicidad del correo; creación de la cuenta \| Salida: cuenta creada y aviso de que debe verificar el correo.  
  * Flujo de interfaz (texto): el visitante abre "Registrarse", completa el formulario y envía; ve un mensaje de confirmación e instrucciones de verificación.  
  * Reglas de negocio y datos: un correo, una cuenta. Datos: correo y contraseña. Reglas de complejidad de contraseña: no definidas (P-2).  
* Restricciones (requerimientos no funcionales):  
  * La contraseña nunca se muestra ni se envía en texto legible por correo.  
  * El registro responde en 3 segundos o menos.  
  * Los datos personales se tratan según el apartado de tratamiento de datos (HU-55).  
* Criterios de aceptación:  
  * AC-HU-7-1 (Camino feliz): Dado un correo válido no registrado y una contraseña válida, cuando el visitante envía el formulario, entonces se crea la cuenta y se le indica verificar su correo.  
  * AC-HU-7-2 (Alternativo/Error): Dado un correo ya registrado, cuando intenta registrarse, entonces se muestra "Este correo ya está registrado" sin crear otra cuenta.  
  * AC-HU-7-3 (Caso límite): Dado un correo con formato inválido o campos vacíos, cuando envía el formulario, entonces se marcan los campos con error y no se crea la cuenta. \[SUPUESTO sobre reglas de contraseña\]  
* Dependencias: Ninguna  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-8** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero verificar mi correo electrónico, para confirmar que mi cuenta me pertenece.  
* Detalles de la HU:  
  * Tareas funcionales: abrir el enlace de verificación; marcar la cuenta como verificada; permitir reenvío.  
  * Entrada: enlace de verificación \| Proceso: se valida el enlace y se activa la cuenta \| Salida: cuenta verificada.  
  * Flujo de interfaz (texto): el cliente abre el enlace del correo y llega a una pantalla de "Correo verificado" con acceso al inicio de sesión.  
  * Reglas de negocio y datos: sin verificación no se puede comprar ni usar el chatbot. \[SUPUESTO\] Vigencia del enlace no definida (P-3).  
* Restricciones (requerimientos no funcionales):  
  * El enlace de verificación es de un solo uso.  
  * La verificación se procesa en 3 segundos o menos.  
* Criterios de aceptación:  
  * AC-HU-8-1 (Camino feliz): Dado un enlace vigente, cuando el cliente lo abre, entonces su cuenta queda verificada.  
  * AC-HU-8-2 (Alternativo/Error): Dado un enlace vencido o inválido, cuando se abre, entonces se muestra un error y la opción de solicitar uno nuevo. \[SUPUESTO\]  
  * AC-HU-8-3 (Caso límite): Dada una cuenta ya verificada, cuando se abre de nuevo el enlace, entonces se informa que ya estaba verificada y no se produce error.  
* Dependencias: HU-7, HU-44  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

#### **Feature 2.2: Acceso y recuperación**

**HU-9** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero iniciar sesión con mi correo y contraseña, para acceder a mi carrito, pedidos y chatbot.  
* Detalles de la HU:  
  * Tareas funcionales: formulario de acceso; validar credenciales; iniciar sesión.  
  * Entrada: correo y contraseña \| Proceso: validación de credenciales y de verificación de correo \| Salida: sesión iniciada.  
  * Flujo de interfaz (texto): el cliente abre "Iniciar sesión", ingresa sus datos y es llevado a la página donde estaba o al catálogo.  
  * Reglas de negocio y datos: solo cuentas verificadas inician sesión. \[SUPUESTO\] Bloqueo por intentos fallidos no definido (P-2).  
* Restricciones (requerimientos no funcionales):  
  * El mensaje de error no revela cuál de los dos datos es incorrecto.  
  * El acceso responde en 3 segundos o menos.  
  * La sesión se cierra tras una inactividad máxima de 30 minutos. \[SUPUESTO\]  
* Criterios de aceptación:  
  * AC-HU-9-1 (Camino feliz): Dadas credenciales correctas de una cuenta verificada, cuando el cliente inicia sesión, entonces accede a su cuenta.  
  * AC-HU-9-2 (Alternativo/Error): Dadas credenciales incorrectas, cuando intenta acceder, entonces se muestra "Correo o contraseña incorrectos".  
  * AC-HU-9-3 (Caso límite): Dada una cuenta sin verificar, cuando intenta acceder, entonces se le indica verificar su correo y se ofrece reenviar el enlace. \[SUPUESTO\]  
* Dependencias: HU-7, HU-8  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-10** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero recuperar mi contraseña, para volver a acceder a mi cuenta si la olvido.  
* Detalles de la HU:  
  * Tareas funcionales: solicitar recuperación; abrir enlace; definir nueva contraseña.  
  * Entrada: correo; nueva contraseña \| Proceso: se envía un enlace y se actualiza la contraseña \| Salida: contraseña actualizada.  
  * Flujo de interfaz (texto): desde "Iniciar sesión" el cliente elige "Olvidé mi contraseña", ingresa su correo, abre el enlace recibido y define la nueva contraseña.  
  * Reglas de negocio y datos: la vigencia del enlace y las reglas de la nueva contraseña no están definidas (P-2, P-3).  
* Restricciones (requerimientos no funcionales):  
  * El enlace es de un solo uso.  
  * La respuesta de la solicitud no revela si el correo existe.  
* Criterios de aceptación:  
  * AC-HU-10-1 (Camino feliz): Dado un correo registrado, cuando el cliente solicita recuperar y define una nueva contraseña desde el enlace, entonces puede iniciar sesión con ella.  
  * AC-HU-10-2 (Alternativo/Error): Dado un enlace vencido o ya usado, cuando se abre, entonces se informa el error y se ofrece solicitar otro. \[SUPUESTO\]  
  * AC-HU-10-3 (Caso límite): Dado un correo no registrado, cuando se solicita la recuperación, entonces se muestra el mismo mensaje genérico que para uno registrado.  
* Dependencias: HU-7, HU-45  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

#### **Feature 2.3: Cuentas de administrador**

**HU-11** \[SIN-IA\]

* Actor(es): Administrador  
* Descripción: Como Administrador, quiero acceder con una cuenta de administrador separada de las cuentas de clientes, para operar el panel administrativo de forma independiente de la tienda.  
* Detalles de la HU:  
  * Tareas funcionales: acceso exclusivo al panel; separar las credenciales de administradores y clientes.  
  * Entrada: credenciales de administrador \| Proceso: validación contra las cuentas de administrador \| Salida: acceso al panel administrativo.  
  * Flujo de interfaz (texto): el administrador abre la entrada del panel, inicia sesión y ve el panel (productos, inventario, pedidos).  
  * Reglas de negocio y datos: una cuenta de cliente no accede al panel y viceversa. Los permisos de los administradores son idénticos.  
* Restricciones (requerimientos no funcionales):  
  * El acceso al panel exige credenciales válidas en el 100 % de los intentos.  
  * El panel se cierra tras 30 minutos de inactividad. \[SUPUESTO\]  
  * Los accesos de administrador quedan registrados con fecha y hora. \[SUPUESTO\]  
* Criterios de aceptación:  
  * AC-HU-11-1 (Camino feliz): Dadas credenciales de administrador válidas, cuando inicia sesión en el panel, entonces accede a las funciones administrativas.  
  * AC-HU-11-2 (Alternativo/Error): Dadas credenciales de una cuenta de cliente, cuando intenta entrar al panel, entonces se rechaza el acceso.  
  * AC-HU-11-3 (Caso límite): Dado un administrador con sesión, cuando intenta abrir directamente una pantalla del panel sin sesión válida, entonces es llevado al inicio de sesión.  
* Dependencias: Ninguna  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-12** \[SIN-IA\]

* Actor(es): Administrador  
* Descripción: Como Administrador, quiero que el sistema limite a 3 las cuentas de administrador con permisos idénticos, para mantener el control del acceso al panel.  
* Detalles de la HU:  
  * Tareas funcionales: impedir crear más de 3 cuentas de administrador; asegurar permisos idénticos.  
  * Entrada: intento de crear una cuenta de administrador \| Proceso: se cuenta las cuentas existentes \| Salida: cuenta creada o rechazo.  
  * Flujo de interfaz (texto): al agregar un administrador, si ya hay 3, se muestra "Límite de administradores alcanzado".  
  * Reglas de negocio y datos: máximo 3, incluida Libia Palacios. El mecanismo para crear o dar de baja administradores no está definido (P-4).  
* Restricciones (requerimientos no funcionales):  
  * El límite se aplica en el 100 % de los intentos, incluso simultáneos.  
  * Toda alta o baja de administrador queda registrada. \[SUPUESTO\]  
* Criterios de aceptación:  
  * AC-HU-12-1 (Camino feliz): Dadas 2 cuentas de administrador, cuando se crea una tercera, entonces se crea con los mismos permisos.  
  * AC-HU-12-2 (Alternativo/Error): Dadas 3 cuentas, cuando se intenta crear una cuarta, entonces se rechaza con un mensaje claro.  
  * AC-HU-12-3 (Caso límite): Dadas 3 cuentas y la baja de una, cuando se crea otra, entonces se permite. \[SUPUESTO\]  
* Dependencias: HU-11  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

---

### **ÉPICA 3: Carrito de Compras (CART)**

#### **Feature 3.1: Gestión del carrito**

**HU-13** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero agregar una variante de producto a mi carrito, para reunir las prendas que deseo comprar.  
* Detalles de la HU:  
  * Tareas funcionales: agregar una variante seleccionada; descontar o reservar stock (HU-17); mostrar el carrito actualizado.  
  * Entrada: variante y cantidad \| Proceso: se valida sesión y stock; se agrega al carrito \| Salida: carrito con la variante.  
  * Flujo de interfaz (texto): en la ficha, el cliente toca "Agregar al carrito" y ve confirmación y el contador del carrito.  
  * Reglas de negocio y datos: requiere sesión. Solo variantes con stock. Cantidad máxima por variante igual al stock disponible. \[SUPUESTO\] Un visitante que intenta agregar es dirigido a iniciar sesión.  
* Restricciones (requerimientos no funcionales):  
  * La acción responde en 2 segundos o menos.  
  * El carrito del cliente es visible solo para ese cliente.  
* Criterios de aceptación:  
  * AC-HU-13-1 (Camino feliz): Dado un cliente con sesión y una variante con stock, cuando pulsa "Agregar al carrito", entonces la variante aparece en su carrito.  
  * AC-HU-13-2 (Alternativo/Error): Dado un visitante sin sesión, cuando intenta agregar, entonces es dirigido al inicio de sesión o registro y no se agrega nada.  
  * AC-HU-13-3 (Caso límite): Dado que otra persona tomó el último stock justo antes, cuando el cliente intenta agregar, entonces se informa que ya no hay disponibilidad.  
* Dependencias: HU-4, HU-9, HU-37  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-14** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero eliminar productos de mi carrito, para quitar los que ya no quiero.  
* Detalles de la HU:  
  * Tareas funcionales: eliminar un ítem; liberar su stock reservado; recalcular el total.  
  * Entrada: ítem a eliminar \| Proceso: se elimina y se libera la reserva \| Salida: carrito actualizado.  
  * Flujo de interfaz (texto): en el carrito, el cliente pulsa "Eliminar" en un ítem y el ítem desaparece con el total recalculado.  
  * Reglas de negocio y datos: solo editable antes de pagar.  
* Restricciones (requerimientos no funcionales):  
  * El carrito se actualiza en 2 segundos o menos.  
  * La eliminación no afecta a otros ítems.  
* Criterios de aceptación:  
  * AC-HU-14-1 (Camino feliz): Dado un carrito con 2 ítems, cuando el cliente elimina uno, entonces queda 1 y el total se recalcula.  
  * AC-HU-14-2 (Alternativo/Error): Dado que el ítem ya expiró por reserva, cuando el cliente intenta eliminarlo, entonces no se produce error y el carrito se muestra actualizado.  
  * AC-HU-14-3 (Caso límite): Dado un carrito con un solo ítem, cuando se elimina, entonces se muestra "Tu carrito está vacío".  
* Dependencias: HU-13  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-15** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero modificar las cantidades de los productos del carrito antes de pagar, para ajustar mi compra.  
* Detalles de la HU:  
  * Tareas funcionales: aumentar o disminuir la cantidad; validar contra stock; recalcular totales.  
  * Entrada: nueva cantidad \| Proceso: validación y actualización \| Salida: carrito actualizado.  
  * Flujo de interfaz (texto): en el carrito, el cliente cambia la cantidad de un ítem y ve el subtotal y total actualizados.  
  * Reglas de negocio y datos: la cantidad no supera el stock disponible; mínimo 1\. \[SUPUESTO\] Si se pone 0 se interpreta como eliminar (a validar).  
* Restricciones (requerimientos no funcionales):  
  * El cambio se refleja en 2 segundos o menos.  
  * Los totales no tienen errores de cálculo (diferencia 0 pesos).  
* Criterios de aceptación:  
  * AC-HU-15-1 (Camino feliz): Dado un ítem con cantidad 1 y stock de 3, cuando el cliente la cambia a 2, entonces el carrito muestra 2 y el total se recalcula.  
  * AC-HU-15-2 (Alternativo/Error): Dada una cantidad mayor al stock, cuando el cliente la ingresa, entonces se rechaza con el máximo disponible.  
  * AC-HU-15-3 (Caso límite): Dada una cantidad 0 o negativa, cuando se ingresa, entonces no se acepta y se mantiene la cantidad anterior. \[SUPUESTO\]  
* Dependencias: HU-13  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-16** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero que el precio aplicado sea el vigente al momento del checkout, para pagar el valor actualizado de cada producto.  
* Detalles de la HU:  
  * Tareas funcionales: recalcular precios al iniciar el checkout; avisar si cambiaron.  
  * Entrada: carrito al iniciar el checkout \| Proceso: se compara el precio vigente con el mostrado \| Salida: total con precios vigentes.  
  * Flujo de interfaz (texto): al pasar al pago, el cliente ve el resumen con los precios vigentes y, si hubo cambios, un aviso.  
  * Reglas de negocio y datos: se aplica el precio vigente al momento del checkout, incluidos descuentos activos y no acumulables. El backlog no contiene la gestión de descuentos (sección 5).  
* Restricciones (requerimientos no funcionales):  
  * El total mostrado coincide con el monto cobrado (diferencia 0 pesos).  
  * El recálculo toma 2 segundos o menos.  
* Criterios de aceptación:  
  * AC-HU-16-1 (Camino feliz): Dado un carrito con precios sin cambios, cuando el cliente inicia el checkout, entonces el total coincide con el del carrito.  
  * AC-HU-16-2 (Alternativo/Error): Dado que el precio de un producto cambió desde que se agregó, cuando el cliente inicia el checkout, entonces se muestra el precio nuevo con un aviso.  
  * AC-HU-16-3 (Caso límite): Dado un descuento que vence durante la sesión, cuando se inicia el checkout, entonces se aplica el precio vigente en ese instante. \[SUPUESTO\]  
* Dependencias: HU-13, HU-19, HU-20 (checkout)  
* Pre-chequeo DoR: \[1\] Calidad: No (depende de un paso de checkout y de descuentos no cubiertos por una HU) \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: No \| \[4-6\] Se evalúan en Etapa 3

#### **Feature 3.2: Reserva de stock**

**HU-17** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero que el stock de los productos que agrego quede reservado por 15 minutos, para no perderlos mientras decido mi compra.  
* Detalles de la HU:  
  * Tareas funcionales: reservar stock al agregar; mostrar el tiempo restante.  
  * Entrada: ítem agregado \| Proceso: se reserva la cantidad por 15 minutos \| Salida: stock reservado con cuenta regresiva.  
  * Flujo de interfaz (texto): en el carrito el cliente ve el tiempo restante de la reserva.  
  * Reglas de negocio y datos: duración 15 minutos. La reserva reduce el stock disponible para otros. Si el cronómetro se reinicia al modificar el carrito, no está definido (P-5).  
* Restricciones (requerimientos no funcionales):  
  * La reserva dura 15 minutos con tolerancia de ±5 segundos.  
  * Dos clientes no pueden reservar el mismo stock (0 sobreventas).  
* Criterios de aceptación:  
  * AC-HU-17-1 (Camino feliz): Dada una variante con stock 1, cuando el cliente A la agrega, entonces queda reservada y el cliente B la ve agotada.  
  * AC-HU-17-2 (Alternativo/Error): Dada una reserva vigente de A, cuando B intenta agregar la misma unidad, entonces se informa que no hay disponibilidad.  
  * AC-HU-17-3 (Caso límite): Dado un pedido pagado antes de los 15 minutos, cuando termina el checkout, entonces la reserva se convierte en venta y no se libera. \[SUPUESTO\]  
* Dependencias: HU-13, HU-37  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-18** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero que el stock se libere automáticamente si no avanzo al checkout, para que otros clientes puedan comprar esas prendas.  
* Detalles de la HU:  
  * Tareas funcionales: liberar el stock al vencer la reserva; actualizar el carrito del cliente.  
  * Entrada: vencimiento de reserva \| Proceso: se libera el stock y se retira o marca el ítem \| Salida: stock disponible de nuevo.  
  * Flujo de interfaz (texto): al vencer, el carrito muestra "Tu reserva expiró" y el ítem se retira o debe confirmarse de nuevo. \[SUPUESTO\]  
  * Reglas de negocio y datos: tras 15 minutos sin checkout, el stock vuelve a estar disponible.  
* Restricciones (requerimientos no funcionales):  
  * La liberación ocurre dentro de 60 segundos del vencimiento. \[SUPUESTO\]  
  * El stock liberado no puede ser liberado dos veces (0 duplicados).  
* Criterios de aceptación:  
  * AC-HU-18-1 (Camino feliz): Dada una reserva de 15 minutos sin checkout, cuando vence, entonces el stock queda disponible para otros.  
  * AC-HU-18-2 (Alternativo/Error): Dado un cliente que intenta pagar un ítem expirado, cuando avanza al checkout, entonces se le informa y se verifica de nuevo el stock.  
  * AC-HU-18-3 (Caso límite): Dado un cliente que paga justo al vencer la reserva, cuando coinciden ambos eventos, entonces prevalece uno solo y el sistema no genera sobreventa. \[SUPUESTO\]  
* Dependencias: HU-17  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

---

### **ÉPICA 4: Checkout y Pagos (PAGO)**

#### **Feature 4.1: Pago en línea**

**HU-19** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero pagar mi pedido con tarjeta débito, para completar mi compra en línea.  
* Detalles de la HU:  
  * Tareas funcionales: iniciar el pago con tarjeta débito; enviar a la pasarela; recibir su respuesta.  
  * Entrada: datos de pago ingresados en la pasarela \| Proceso: la pasarela procesa el pago \| Salida: resultado del pago.  
  * Flujo de interfaz (texto): en el resumen el cliente elige "Tarjeta débito", es llevado al formulario de pago, completa y vuelve al sitio con el resultado.  
  * Reglas de negocio y datos: solo tarjeta débito (sin crédito). Pasarela por definir (P-9). El pedido pasa a "Pendiente de Pago".  
* Restricciones (requerimientos no funcionales):  
  * Los datos de la tarjeta no se almacenan en el sitio.  
  * La comunicación del pago es cifrada.  
  * El inicio del pago responde en 5 segundos o menos. \[SUPUESTO\]  
* Criterios de aceptación:  
  * AC-HU-19-1 (Camino feliz): Dado un cliente con carrito válido, cuando paga con tarjeta débito y es aprobada, entonces el pedido queda "Pago aprobado".  
  * AC-HU-19-2 (Alternativo/Error): Dada una tarjeta de crédito o no aceptada, cuando el cliente la usa, entonces se rechaza y se informa que solo se acepta débito.  
  * AC-HU-19-3 (Caso límite): Dado un cliente que cierra la ventana de pago, cuando abandona, entonces el pedido permanece "Pendiente de Pago" según HU-21/HU-24.  
* Dependencias: HU-13, HU-25, HU-26 y una HU de creación del pedido/checkout (no existe)  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí \| \[3\] Dependencias: No (falta la HU de checkout/creación de pedido) \| \[4-6\] Se evalúan en Etapa 3

**HU-20** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero pagar mi pedido con Nequi, para completar mi compra con mi medio de pago preferido.  
* Detalles de la HU:  
  * Tareas funcionales: iniciar el pago con Nequi; recibir el resultado.  
  * Entrada: datos de pago en Nequi \| Proceso: la pasarela procesa el pago \| Salida: resultado del pago.  
  * Flujo de interfaz (texto): el cliente elige "Nequi", confirma el pago y regresa al sitio con el resultado.  
  * Reglas de negocio y datos: el pedido pasa a "Pendiente de Pago" hasta recibir respuesta. El detalle del flujo de Nequi depende de la pasarela (P-9).  
* Restricciones (requerimientos no funcionales):  
  * Los datos de pago no se almacenan en el sitio.  
  * El inicio del pago responde en 5 segundos o menos. \[SUPUESTO\]  
* Criterios de aceptación:  
  * AC-HU-20-1 (Camino feliz): Dado un carrito válido, cuando el cliente paga con Nequi y es aprobado, entonces el pedido queda "Pago aprobado".  
  * AC-HU-20-2 (Alternativo/Error): Dado un pago Nequi rechazado, cuando la pasarela responde, entonces el pedido queda "Pago rechazado" y se cancela.  
  * AC-HU-20-3 (Caso límite): Dado un cliente que no confirma en Nequi, cuando transcurren 30 minutos, entonces se aplica HU-24.  
* Dependencias: HU-13, HU-25, HU-26 y una HU de checkout (no existe)  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí \| \[3\] Dependencias: No (falta la HU de checkout) \| \[4-6\] Se evalúan en Etapa 3

**HU-21** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero ver mi pedido en estado "Pendiente de Pago" mientras se espera la respuesta de la pasarela, para saber que mi pago está en proceso.  
* Detalles de la HU:  
  * Tareas funcionales: crear el pedido al iniciar el pago; mostrar el estado "Pendiente de Pago".  
  * Entrada: inicio del pago \| Proceso: se crea el pedido en estado pendiente \| Salida: pedido visible como "Pendiente de Pago".  
  * Flujo de interfaz (texto): tras iniciar el pago, el cliente ve su pedido "Pendiente de Pago" en el detalle o la lista de pedidos.  
  * Reglas de negocio y datos: se mantiene hasta la respuesta o hasta 30 minutos (HU-24). Durante ese tiempo el stock sigue retenido.  
* Restricciones (requerimientos no funcionales):  
  * El estado aparece en 2 segundos o menos tras iniciar el pago.  
  * El estado se muestra con texto, no solo con color.  
* Criterios de aceptación:  
  * AC-HU-21-1 (Camino feliz): Dado un pago iniciado, cuando el cliente consulta su pedido, entonces ve "Pendiente de Pago".  
  * AC-HU-21-2 (Alternativo/Error): Dada una pasarela caída, cuando el cliente intenta pagar, entonces ve un error claro y el pedido no queda en un estado inconsistente. \[SUPUESTO\]  
  * AC-HU-21-3 (Caso límite): Dado un pedido pendiente, cuando el cliente intenta pagar el mismo pedido de nuevo, entonces no se genera un segundo cobro.  
* Dependencias: HU-19, HU-20  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

#### **Feature 4.2: Resultado del pago**

**HU-22** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero que mi pedido pase a "Pago aprobado" cuando la pasarela confirme el pago, para tener certeza de que mi compra fue exitosa.  
* Detalles de la HU:  
  * Tareas funcionales: recibir la confirmación; cambiar el estado; confirmar el stock como vendido.  
  * Entrada: confirmación de la pasarela \| Proceso: se actualiza el estado y se registra en el historial \| Salida: pedido en "Pago aprobado".  
  * Flujo de interfaz (texto): el cliente ve una pantalla de confirmación y el estado actualizado en su pedido.  
  * Reglas de negocio y datos: el cambio es automático (HU-42). Desde este punto el cliente ya no puede cancelar (HU-32).  
* Restricciones (requerimientos no funcionales):  
  * El estado se actualiza en 30 segundos o menos tras la confirmación. \[SUPUESTO\]  
  * Una misma confirmación no genera dos cambios (0 duplicados).  
* Criterios de aceptación:  
  * AC-HU-22-1 (Camino feliz): Dado un pedido pendiente, cuando la pasarela confirma, entonces pasa a "Pago aprobado".  
  * AC-HU-22-2 (Alternativo/Error): Dada una confirmación para un pedido ya cancelado por timeout, cuando llega, entonces no se reactiva el pedido y se registra para revisión. \[SUPUESTO\]  
  * AC-HU-22-3 (Caso límite): Dada una confirmación recibida dos veces, cuando se procesa, entonces el estado y el historial se actualizan una sola vez.  
* Dependencias: HU-21  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-23** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero que mi pedido se cancele automáticamente si el pago es rechazado, para que no quede una orden inconsistente.  
* Detalles de la HU:  
  * Tareas funcionales: detectar el rechazo; pasar el pedido a "Pago rechazado" y luego a "Cancelado"; liberar stock.  
  * Entrada: rechazo de la pasarela \| Proceso: se actualiza el estado y se libera stock \| Salida: pedido cancelado y stock disponible.  
  * Flujo de interfaz (texto): el cliente ve un mensaje de pago rechazado y el pedido como cancelado; puede intentar una nueva compra.  
  * Reglas de negocio y datos: el rechazo cancela automáticamente. Si el pedido pasa por "Pago rechazado" y luego "Cancelado", o queda solo en uno, no está definido (P-10).  
* Restricciones (requerimientos no funcionales):  
  * La cancelación se aplica en 30 segundos o menos tras el rechazo. \[SUPUESTO\]  
  * El mensaje al cliente no expone datos sensibles de la pasarela.  
* Criterios de aceptación:  
  * AC-HU-23-1 (Camino feliz): Dado un pedido pendiente, cuando la pasarela rechaza el pago, entonces el pedido queda cancelado y el stock se libera.  
  * AC-HU-23-2 (Alternativo/Error): Dado un rechazo, cuando el cliente consulta su pedido, entonces el historial muestra el rechazo y la cancelación.  
  * AC-HU-23-3 (Caso límite): Dado un rechazo, cuando el cliente reintenta, entonces debe iniciar un pedido nuevo con stock aún disponible. \[SUPUESTO\]  
* Dependencias: HU-21  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-24** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero que el pedido se cancele automáticamente si la pasarela no responde en 30 minutos, para que se reincorpore el stock y no quede pendiente indefinidamente.  
* Detalles de la HU:  
  * Tareas funcionales: contar 30 minutos desde el pago pendiente; cancelar; reincorporar stock.  
  * Entrada: pedido "Pendiente de Pago" sin respuesta \| Proceso: al vencer 30 minutos se cancela \| Salida: pedido "Cancelado" y stock disponible.  
  * Flujo de interfaz (texto): el cliente ve su pedido como "Cancelado" en su historial.  
  * Reglas de negocio y datos: 30 minutos desde el inicio del pago. Qué ocurre con un pago real tardío está sin definir (P-10).  
* Restricciones (requerimientos no funcionales):  
  * La cancelación ocurre a los 30 minutos con tolerancia de ±60 segundos. \[SUPUESTO\]  
  * El stock se reincorpora una sola vez.  
* Criterios de aceptación:  
  * AC-HU-24-1 (Camino feliz): Dado un pedido pendiente sin respuesta, cuando pasan 30 minutos, entonces se cancela y se libera el stock.  
  * AC-HU-24-2 (Alternativo/Error): Dada una respuesta de la pasarela antes de los 30 minutos, cuando llega, entonces no se cancela por timeout.  
  * AC-HU-24-3 (Caso límite): Dada una respuesta tardía de pago aprobado tras la cancelación, cuando llega, entonces queda registrada para revisión del administrador. \[SUPUESTO\]  
* Dependencias: HU-21, HU-18  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

---

### **ÉPICA 5: Envíos (ENVIO)**

#### **Feature 5.1: Cobertura y tarifa de envío**

**HU-25** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero indicar mi dirección de envío dentro de Cali, Palmira, Jamundí o Yumbo, para recibir mi pedido en mi municipio.  
* Detalles de la HU:  
  * Tareas funcionales: capturar la dirección; elegir municipio entre los 4 permitidos; guardarla en el pedido.  
  * Entrada: municipio y dirección \| Proceso: validación de campos \| Salida: dirección asociada al pedido.  
  * Flujo de interfaz (texto): en el checkout el cliente elige el municipio de una lista, escribe la dirección y continúa.  
  * Reglas de negocio y datos: municipios permitidos: Cali, Palmira, Jamundí, Yumbo. Los campos exactos de la dirección y si se guardan varias no están definidos (P-6).  
* Restricciones (requerimientos no funcionales):  
  * La dirección solo es visible para el cliente y los administradores.  
  * La validación responde en 2 segundos o menos.  
* Criterios de aceptación:  
  * AC-HU-25-1 (Camino feliz): Dado un checkout, cuando el cliente elige "Yumbo" y completa la dirección, entonces se asocia al pedido.  
  * AC-HU-25-2 (Alternativo/Error): Dada una dirección vacía o incompleta, cuando el cliente continúa, entonces se marca el campo con error.  
  * AC-HU-25-3 (Caso límite): Dada una dirección con caracteres especiales o muy larga, cuando se envía, entonces se acepta o se rechaza con un mensaje claro. \[SUPUESTO sobre longitud máxima\]  
* Dependencias: HU-9  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-26** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero conocer la tarifa fija de envío antes de pagar, para saber el costo total de mi compra.  
* Detalles de la HU:  
  * Tareas funcionales: mostrar la tarifa de envío; sumarla al total.  
  * Entrada: dirección dentro de cobertura \| Proceso: se aplica la tarifa fija \| Salida: total con envío.  
  * Flujo de interfaz (texto): en el resumen del pedido el cliente ve subtotal, tarifa de envío y total antes de pagar.  
  * Reglas de negocio y datos: tarifa fija; su valor no está definido (P-7) y se cobra en el checkout.  
* Restricciones (requerimientos no funcionales):  
  * Total \= subtotal \+ envío, con diferencia 0 pesos.  
  * El total mostrado es el mismo que se cobra.  
* Criterios de aceptación:  
  * AC-HU-26-1 (Camino feliz): Dado un pedido con dirección válida, cuando el cliente ve el resumen, entonces aparece la tarifa y el total la incluye.  
  * AC-HU-26-2 (Alternativo/Error): Dada una dirección fuera de cobertura, cuando se intenta calcular, entonces no se muestra tarifa y se aplica HU-28.  
  * AC-HU-26-3 (Caso límite): Dado un cambio de municipio, cuando el cliente lo modifica, entonces el total se recalcula (misma tarifa si es fija para todos). \[SUPUESTO\]  
* Dependencias: HU-25  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-27** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero conocer el tiempo estimado de entrega de 3 a 5 días, para planear la recepción de mi pedido.  
* Detalles de la HU:  
  * Tareas funcionales: mostrar el rango "3 a 5 días" en el checkout y en el pedido.  
  * Entrada: dirección dentro de cobertura \| Proceso: se muestra el rango \| Salida: texto con el tiempo estimado.  
  * Flujo de interfaz (texto): en el resumen y en el detalle del pedido aparece "Entrega estimada: 3 a 5 días".  
  * Reglas de negocio y datos: rango de 3 a 5 días. No se define si son días hábiles ni desde cuándo se cuentan (P-8).  
* Restricciones (requerimientos no funcionales):  
  * El rango es idéntico en todas las pantallas donde aparece.  
  * El texto es legible en celular sin desplazamiento horizontal.  
* Criterios de aceptación:  
  * AC-HU-27-1 (Camino feliz): Dado un checkout con dirección válida, cuando el cliente ve el resumen, entonces aparece "3 a 5 días".  
  * AC-HU-27-2 (Alternativo/Error): Dada una dirección fuera de cobertura, cuando se consulta, entonces no se muestra tiempo estimado.  
  * AC-HU-27-3 (Caso límite): Dado un pedido ya creado, cuando el cliente lo consulta, entonces ve el mismo rango. \[SUPUESTO sobre días hábiles\]  
* Dependencias: HU-25  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-28** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero que el sistema me impida comprar con direcciones fuera de la cobertura, para evitar pedidos que no se pueden entregar.  
* Detalles de la HU:  
  * Tareas funcionales: bloquear el avance con municipios no permitidos; informar la cobertura.  
  * Entrada: municipio o dirección \| Proceso: validación contra los 4 municipios \| Salida: avance permitido o bloqueado con mensaje.  
  * Flujo de interfaz (texto): si el cliente intenta usar un municipio no permitido, ve "Solo enviamos a Cali, Palmira, Jamundí y Yumbo" y no puede pagar.  
  * Reglas de negocio y datos: sin envíos fuera de los 4 municipios ni al extranjero.  
* Restricciones (requerimientos no funcionales):  
  * El bloqueo se aplica en el 100 % de los intentos.  
  * El mensaje aparece en 1 segundo o menos.  
* Criterios de aceptación:  
  * AC-HU-28-1 (Camino feliz): Dado un municipio permitido, cuando el cliente continúa, entonces el avance no se bloquea.  
  * AC-HU-28-2 (Alternativo/Error): Dado un municipio no permitido, cuando intenta continuar, entonces se bloquea con un mensaje de cobertura.  
  * AC-HU-28-3 (Caso límite): Dado un municipio escrito con mayúsculas, tildes distintas o con espacios, cuando se valida, entonces se reconoce correctamente o se rechaza con claridad. \[SUPUESTO\]  
* Dependencias: HU-25  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

---

### **ÉPICA 6: Seguimiento de Pedidos del Cliente (PEDI)**

#### **Feature 6.1: Consulta de pedidos**

**HU-29** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero ver la lista de mis pedidos, para consultar mis compras.  
* Detalles de la HU:  
  * Tareas funcionales: listar los pedidos del cliente con fecha, total y estado.  
  * Entrada: sesión del cliente \| Proceso: se consultan sus pedidos \| Salida: lista ordenada del más reciente al más antiguo. \[SUPUESTO\]  
  * Flujo de interfaz (texto): desde el menú de cuenta, el cliente abre "Mis pedidos" y toca uno para ver su detalle.  
  * Reglas de negocio y datos: el cliente solo ve sus propios pedidos.  
* Restricciones (requerimientos no funcionales):  
  * La lista carga en 3 segundos o menos.  
  * Un cliente nunca ve pedidos de otro (0 fugas).  
* Criterios de aceptación:  
  * AC-HU-29-1 (Camino feliz): Dado un cliente con pedidos, cuando abre "Mis pedidos", entonces ve la lista con fecha, total y estado.  
  * AC-HU-29-2 (Alternativo/Error): Dado un cliente sin pedidos, cuando abre la lista, entonces ve "Aún no tienes pedidos".  
  * AC-HU-29-3 (Caso límite): Dado un cliente con muchos pedidos, cuando abre la lista, entonces se muestran todos o paginados sin pérdida. \[SUPUESTO\]  
* Dependencias: HU-21  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-30** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero ver el estado actual de mi pedido (Pendiente de Pago, Pago aprobado, Pago rechazado, En preparación, Enviado, Entregado, Cancelado), para saber en qué etapa se encuentra.  
* Detalles de la HU:  
  * Tareas funcionales: mostrar el estado vigente en la lista y el detalle.  
  * Entrada: pedido seleccionado \| Proceso: se obtiene el estado vigente \| Salida: estado visible.  
  * Flujo de interfaz (texto): el cliente ve una etiqueta de estado en la lista y en el detalle.  
  * Reglas de negocio y datos: los 7 estados listados. El estado mostrado es el más reciente.  
* Restricciones (requerimientos no funcionales):  
  * El estado se muestra con texto, no solo con color.  
  * El estado mostrado coincide con el registrado (0 discrepancias).  
* Criterios de aceptación:  
  * AC-HU-30-1 (Camino feliz): Dado un pedido "Enviado", cuando el cliente lo consulta, entonces ve "Enviado".  
  * AC-HU-30-2 (Alternativo/Error): Dado un pedido que no pertenece al cliente, cuando intenta abrirlo, entonces se le deniega el acceso.  
  * AC-HU-30-3 (Caso límite): Dado un cambio de estado reciente, cuando el cliente recarga, entonces ve el nuevo estado.  
* Dependencias: HU-29  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-31** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero ver el historial completo de cambios de estado de mi pedido, para conocer todo su progreso.  
* Detalles de la HU:  
  * Tareas funcionales: mostrar la línea de tiempo con estado, fecha y hora de cada cambio.  
  * Entrada: pedido seleccionado \| Proceso: se consulta el historial \| Salida: lista cronológica de cambios.  
  * Flujo de interfaz (texto): en el detalle del pedido, el cliente ve la sección "Historial" con cada estado y su fecha.  
  * Reglas de negocio y datos: todos los cambios se registran, tanto manuales como automáticos.  
* Restricciones (requerimientos no funcionales):  
  * El historial es inalterable por el cliente.  
  * Cada registro incluye fecha y hora.  
* Criterios de aceptación:  
  * AC-HU-31-1 (Camino feliz): Dado un pedido con 3 cambios, cuando el cliente abre el historial, entonces ve los 3 con fecha y hora en orden cronológico.  
  * AC-HU-31-2 (Alternativo/Error): Dado un pedido recién creado, cuando se abre el historial, entonces muestra al menos su estado inicial.  
  * AC-HU-31-3 (Caso límite): Dados dos cambios casi simultáneos, cuando se muestran, entonces conservan un orden coherente.  
* Dependencias: HU-30, HU-42  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

#### **Feature 6.2: Cancelación previa al pago**

**HU-32** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero cancelar mi pedido mediante un botón antes de pagarlo, para desistir de la compra sin costo.  
* Detalles de la HU:  
  * Tareas funcionales: botón "Cancelar pedido" visible solo antes de pagar; liberar stock; registrar la cancelación.  
  * Entrada: acción de cancelar \| Proceso: validación del estado y cancelación \| Salida: pedido "Cancelado" y stock disponible.  
  * Flujo de interfaz (texto): en un pedido "Pendiente de Pago" aparece el botón; el cliente confirma y el pedido pasa a "Cancelado".  
  * Reglas de negocio y datos: solo antes del pago. Después de "Pago aprobado" no hay cancelación en la web (postventa externa por WhatsApp). Si un pago está en curso al cancelar, el caso no está definido (P-22).  
* Restricciones (requerimientos no funcionales):  
  * La cancelación se refleja en 3 segundos o menos.  
  * Se pide confirmación antes de cancelar.  
* Criterios de aceptación:  
  * AC-HU-32-1 (Camino feliz): Dado un pedido "Pendiente de Pago", cuando el cliente confirma la cancelación, entonces pasa a "Cancelado" y se libera el stock.  
  * AC-HU-32-2 (Alternativo/Error): Dado un pedido con pago aprobado, cuando el cliente consulta, entonces no aparece el botón de cancelar.  
  * AC-HU-32-3 (Caso límite): Dado un pago aprobado justo mientras el cliente cancela, cuando coinciden, entonces prevalece un único resultado coherente y se informa. \[SUPUESTO\]  
* Dependencias: HU-21, HU-42  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

---

### **ÉPICA 7: Gestión de Productos e Inventario (ADPRO)**

#### **Feature 7.1: Gestión de productos**

**HU-33** \[SIN-IA\] \[BACKEND LISTO\]

* Actor(es): Administrador  
* Descripción: Como Administrador, quiero crear productos con nombre, descripción, precio, precio anterior, material y categoría, para publicarlos en el catálogo.  
* Detalles de la HU:  
  * Tareas funcionales: formulario de alta; asignar categoría; publicar.  
  * Entrada: nombre, descripción, precio, precio anterior (opcional), material, categoría \| Proceso: validación y creación \| Salida: producto creado en borrador (`draft`).  
  * Flujo de interfaz (texto): el administrador abre "Nuevo producto", completa el formulario y guarda; ve confirmación.  
  * Reglas de negocio y datos: categoría entre las 4 iniciales; precio en COP; catálogo de menos de 30 productos. Resuelto P-15: se crea en borrador (`draft`); si el catálogo alcanza o supera los 30 productos, se retorna advertencia informativa sin bloquear la creación.  
* Restricciones (requerimientos no funcionales):  
  * El guardado responde en 3 segundos o menos.  
  * Solo administradores crean productos (`IsRMAdmin`).  
* Criterios de aceptación:  
  * AC-HU-33-1 (Camino feliz): Dados los datos obligatorios, cuando el administrador guarda, entonces el producto queda creado con estado borrador.  
  * AC-HU-33-2 (Alternativo/Error): Dado un precio vacío, negativo o no numérico, cuando guarda, entonces se rechaza con un mensaje de error y formato unificado.  
  * AC-HU-33-3 (Caso límite): Dado un catálogo de 30 o más productos, cuando se intenta crear otro, entonces se permite la creación y se retorna advertencia informativa en `warning`.  
* Dependencias: HU-11  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí \| \[3\] Dependencias: Sí \| \[4-6\] Backend implementado y verificado con pruebas automatizadas (Frontend pendiente)

**HU-34** \[SIN-IA\] \[BACKEND LISTO\]

* Actor(es): Administrador  
* Descripción: Como Administrador, quiero editar y eliminar productos existentes, para mantener el catálogo actualizado.  
* Detalles de la HU:  
  * Tareas funcionales: editar atributos; eliminar productos con confirmación.  
  * Entrada: producto y cambios \| Proceso: validación y actualización o eliminación \| Salida: producto actualizado o archivado (`archived`).  
  * Flujo de interfaz (texto): el administrador abre un producto, edita y guarda, o pulsa "Eliminar" y confirma.  
  * Reglas de negocio y datos: resuelto P-15: la eliminación se realiza mediante archivado lógico (`status='archived'`), manteniendo intacta la integridad referencial de pedidos y carritos existentes.  
* Restricciones (requerimientos no funcionales):  
  * Los cambios se reflejan en el catálogo en 5 segundos o menos.  
  * Se exige confirmación antes de eliminar.  
* Criterios de aceptación:  
  * AC-HU-34-1 (Camino feliz): Dado un producto existente, cuando el administrador cambia el precio y guarda, entonces el catálogo muestra el nuevo precio.  
  * AC-HU-34-2 (Alternativo/Error): Dados datos inválidos, cuando guarda, entonces se rechaza con un mensaje de error y formato unificado.  
  * AC-HU-34-3 (Caso límite): Dado un producto en carritos o pedidos existentes, cuando se elimina, el sistema aplica borrado lógico (`archived`) sin dejar pedidos inconsistentes ni corromper llaves foráneas.  
* Dependencias: HU-33  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí \| \[3\] Dependencias: Sí \| \[4-6\] Backend implementado y verificado con pruebas automatizadas (Frontend pendiente)

**HU-35** \[SIN-IA\] \[BACKEND LISTO\]

* Actor(es): Administrador  
* Descripción: Como Administrador, quiero cargar fotografías de cada producto, para mostrar las prendas a los clientes.  
* Detalles de la HU:  
  * Tareas funcionales: subir, ordenar y eliminar fotografías; asociar texto alternativo.  
  * Entrada: archivos de imagen y texto alternativo \| Proceso: validación de formato y tamaño; almacenamiento \| Salida: fotos visibles en la ficha.  
  * Flujo de interfaz (texto): en el producto, el administrador pulsa "Subir fotos", elige archivos, escribe el texto alternativo y guarda.  
  * Reglas de negocio y datos: límite de 3 fotografías por producto (posiciones 1 a 3). Formatos permitidos: JPG, PNG y WebP hasta 5 MB. Conversión en memoria a WebP (máx 1600 px en lado mayor, calidad 85 con Pillow). Eliminación física del archivo en storage y recompactación secuencial de posiciones. Cada imagen requiere `alt_text` con fallback al nombre de la prenda para accesibilidad (HU-61). Endpoints REST protegidos con `IsRMAdmin` y documentados en Swagger UI (`/api/v1/docs/`).  
* Restricciones (requerimientos no funcionales):  
  * La carga de una imagen termina en 10 segundos o menos con conexión estándar. \[SUPUESTO\]  
  * Las imágenes se muestran en celular sin desbordar la pantalla.  
* Criterios de aceptación:  
  * AC-HU-35-1 (Camino feliz): Dado un archivo de imagen válido, cuando el administrador lo sube, entonces aparece en la ficha del producto (convertido a WebP).  
  * AC-HU-35-2 (Alternativo/Error): Dado un archivo que no es imagen o es demasiado pesado (\> 5 MB), cuando se sube, entonces se rechaza con un mensaje.  
  * AC-HU-35-3 (Caso límite): Dado el máximo de 3 fotos alcanzado, cuando se intenta subir otra, entonces se avisa del límite (400 Bad Request).  
* Dependencias: HU-33  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí \| \[3\] Dependencias: Sí \| \[4-6\] Backend implementado y verificado con pruebas automatizadas (Frontend pendiente)

**HU-36** \[SIN-IA\] \[BACKEND LISTO\]

* Actor(es): Administrador  
* Descripción: Como Administrador, quiero definir los colores y tallas de cada diseño, para ofrecer sus variantes.  
* Detalles de la HU:  
  * Tareas funcionales: agregar o quitar colores y tallas de un diseño; generar las combinaciones.  
  * Entrada: colores y tallas \| Proceso: se crean las combinaciones diseño/talla/color \| Salida: variantes disponibles para stock.  
  * Flujo de interfaz (texto): en el diseño, el administrador agrega colores y tallas y ve la lista de combinaciones.  
  * Reglas de negocio y datos: un diseño tiene múltiples variantes de color y talla sin duplicados (`unique(product, color, size)`). Se normalizan colores (Title Case) y tallas (Uppercase). Soporta creación individual y generación masiva (bulk). Se prohíbe eliminar variantes que posean stock (>0) o reservas activas para proteger la consistencia de inventario (AC-HU-36-3). Endpoints REST protegidos con `IsRMAdmin` y documentados en Swagger UI (`/api/v1/docs/`).  
* Restricciones (requerimientos no funcionales):  
  * No pueden existir combinaciones duplicadas.  
  * El guardado responde en 3 segundos o menos.  
* Criterios de aceptación:  
  * AC-HU-36-1 (Camino feliz): Dado un diseño, cuando el administrador agrega "Negro" y "M", entonces se crea esa combinación.  
  * AC-HU-36-2 (Alternativo/Error): Dada una combinación ya existente, cuando se intenta duplicar, entonces se rechaza con error de validación (400 Bad Request).  
  * AC-HU-36-3 (Caso límite): Dada una combinación con stock (>0) o reservas, cuando se intenta quitar, entonces se bloquea la eliminación informando al administrador (400 Bad Request).  
* Dependencias: HU-33  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí \| \[3\] Dependencias: Sí \| \[4-6\] Backend implementado y verificado con pruebas automatizadas (Frontend pendiente)

#### **Feature 7.2: Gestión de inventario**

**HU-37** \[SIN-IA\] [BACKEND LISTO]

* Actor(es): Administrador  
* Descripción: Como Administrador, quiero registrar y aumentar manualmente el stock de cada combinación de diseño, talla y color, para reflejar las existencias reales.  
* Detalles de la HU:  
  * Tareas funcionales: establecer stock inicial; aumentar stock; consultar stock por combinación.  
  * Entrada: combinación y cantidad \| Proceso: se actualiza el stock \| Salida: stock actualizado.  
  * Flujo de interfaz (texto): el administrador abre el inventario, elige una combinación e ingresa la cantidad; ve el stock resultante.  
  * Reglas de negocio y datos: stock individual por combinación. Principalmente en stock (ej.: Diseño A / Talla M / Negro \= 3 unidades). El aumento es manual.  
* Restricciones (requerimientos no funcionales):  
  * El stock actualizado se refleja en el catálogo en 5 segundos o menos.  
  * Cada cambio de stock queda registrado con fecha y administrador. \[SUPUESTO\]  
* Criterios de aceptación:  
  * AC-HU-37-1 (Camino feliz): Dada una combinación con stock 3, cuando el administrador suma 2, entonces el stock es 5\.  
  * AC-HU-37-2 (Alternativo/Error): Dada una cantidad no numérica o negativa, cuando se guarda, entonces se rechaza.  
  * AC-HU-37-3 (Caso límite): Dada una combinación agotada, cuando se aumenta el stock, entonces deja de mostrar "Agotado".  
* Dependencias: HU-36  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí \| \[3\] Dependencias: Sí \| \[4-6\] Backend implementado y verificado con 20 pruebas automatizadas en apps.inventory (Frontend pendiente)

**HU-38** \[SIN-IA\]

* Actor(es): Administrador  
* Descripción: Como Administrador, quiero que las combinaciones sin stock se muestren como "Agotado", para evitar ventas de prendas no disponibles.  
* Detalles de la HU:  
  * Tareas funcionales: marcar automáticamente "Agotado" con stock 0; impedir su compra.  
  * Entrada: stock de la combinación \| Proceso: se evalúa si es 0 \| Salida: "Agotado" y compra bloqueada.  
  * Flujo de interfaz (texto): el administrador ve las combinaciones agotadas marcadas en su inventario y en la tienda.  
  * Reglas de negocio y datos: stock 0 equivale a "Agotado" (misma regla que HU-5; ver duplicado en sección 5).  
* Restricciones (requerimientos no funcionales):  
  * El cambio a "Agotado" se refleja en 5 segundos o menos.  
  * 0 ventas de combinaciones sin stock.  
* Criterios de aceptación:  
  * AC-HU-38-1 (Camino feliz): Dado que el stock llega a 0, cuando se consulta, entonces aparece "Agotado".  
  * AC-HU-38-2 (Alternativo/Error): Dada una combinación agotada, cuando un cliente intenta comprarla, entonces la compra se bloquea.  
  * AC-HU-38-3 (Caso límite): Dado un stock de 1 con dos clientes comprando a la vez, cuando ambos intentan, entonces solo uno lo logra.  
* Dependencias: HU-37, HU-5  
* Pre-chequeo DoR: \[1\] Calidad: No (se solapa con HU-5) \| \[2\] Criterios: Sí \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

---

### **ÉPICA 8: Gestión de Pedidos del Administrador (ADPED)**

#### **Feature 8.1: Consulta de pedidos**

**HU-39** \[SIN-IA\]

* Actor(es): Administrador  
* Descripción: Como Administrador, quiero ver la lista de todos los pedidos con su estado actual, para organizar y dar seguimiento a las ventas.  
* Detalles de la HU:  
  * Tareas funcionales: listar pedidos con cliente, fecha, total y estado; filtrar por estado. \[SUPUESTO\]  
  * Entrada: acceso al panel \| Proceso: se consultan los pedidos \| Salida: lista de pedidos.  
  * Flujo de interfaz (texto): en el panel el administrador abre "Pedidos" y ve la lista; toca uno para su detalle.  
  * Reglas de negocio y datos: se incluyen los 7 estados. El filtro por estado se infiere de la necesidad de organizar.  
* Restricciones (requerimientos no funcionales):  
  * La lista carga en 3 segundos o menos.  
  * Solo administradores ven todos los pedidos.  
* Criterios de aceptación:  
  * AC-HU-39-1 (Camino feliz): Dados pedidos existentes, cuando el administrador abre "Pedidos", entonces ve la lista con estado.  
  * AC-HU-39-2 (Alternativo/Error): Dado que no hay pedidos, cuando abre la lista, entonces ve "No hay pedidos".  
  * AC-HU-39-3 (Caso límite): Dada una lista extensa, cuando se consulta, entonces se muestra completa o paginada sin pérdida. \[SUPUESTO\]  
* Dependencias: HU-11, HU-21  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-40** \[SIN-IA\]

* Actor(es): Administrador  
* Descripción: Como Administrador, quiero consultar el detalle de un pedido (productos, dirección y estado), para prepararlo y despacharlo.  
* Detalles de la HU:  
  * Tareas funcionales: mostrar productos con variante y cantidad, dirección, datos de contacto del cliente, total, estado e historial.  
  * Entrada: pedido seleccionado \| Proceso: se carga el detalle \| Salida: ficha completa del pedido.  
  * Flujo de interfaz (texto): desde la lista, el administrador abre un pedido y ve su detalle con las acciones de actualización de estado.  
  * Reglas de negocio y datos: la entrega es manual por la clienta. Los datos de contacto exactos del cliente que se muestran no están definidos (P-6).  
* Restricciones (requerimientos no funcionales):  
  * El detalle carga en 3 segundos o menos.  
  * Los datos personales solo son visibles para administradores.  
* Criterios de aceptación:  
  * AC-HU-40-1 (Camino feliz): Dado un pedido, cuando el administrador lo abre, entonces ve productos, dirección y estado.  
  * AC-HU-40-2 (Alternativo/Error): Dado un pedido inexistente, cuando se intenta abrir, entonces se muestra "Pedido no encontrado".  
  * AC-HU-40-3 (Caso límite): Dado un pedido con varias variantes del mismo diseño, cuando se abre, entonces cada una se muestra por separado con su cantidad.  
* Dependencias: HU-39  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

#### **Feature 8.2: Actualización de estados**

**HU-41** \[SIN-IA\]

* Actor(es): Administrador  
* Descripción: Como Administrador, quiero actualizar el estado de un pedido a "En preparación", "Enviado" o "Entregado", para informar al cliente del avance de su compra.  
* Detalles de la HU:  
  * Tareas funcionales: cambiar el estado manualmente; registrar el cambio; disparar la notificación (HU-48).  
  * Entrada: nuevo estado \| Proceso: validación de la transición \| Salida: estado actualizado e historial.  
  * Flujo de interfaz (texto): en el detalle, el administrador elige el nuevo estado y confirma.  
  * Reglas de negocio y datos: solo estados manuales permitidos. Orden esperado: Pago aprobado → En preparación → Enviado → Entregado. Si puede retroceder o saltar estados no está definido (P-11).  
* Restricciones (requerimientos no funcionales):  
  * El cambio se refleja al cliente en 5 segundos o menos.  
  * Cada cambio registra administrador, fecha y hora.  
* Criterios de aceptación:  
  * AC-HU-41-1 (Camino feliz): Dado un pedido con pago aprobado, cuando el administrador lo pasa a "En preparación", entonces el cliente ve ese estado.  
  * AC-HU-41-2 (Alternativo/Error): Dado un pedido pendiente o cancelado, cuando el administrador intenta pasarlo a "Enviado", entonces se rechaza.  
  * AC-HU-41-3 (Caso límite): Dado un pedido "Entregado", cuando se intenta cambiar, entonces se bloquea o requiere regla definida. \[SUPUESTO\]  
* Dependencias: HU-40, HU-22  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-42** \[SIN-IA\]

* Actor(es): Administrador (beneficiario); sistema (ejecutor)  
* Descripción: Como Administrador, quiero que los estados se actualicen automáticamente por eventos del sistema (pago aprobado, pago rechazado, cancelación), para no registrar manualmente esos cambios.  
* Detalles de la HU:  
  * Tareas funcionales: cambiar el estado ante pago aprobado, rechazado, cancelación por el cliente o timeout; registrar en el historial.  
  * Entrada: evento del sistema \| Proceso: se aplica la transición \| Salida: estado y registro de historial.  
  * Flujo de interfaz (texto): el administrador ve el estado actualizado en su lista sin intervenir.  
  * Reglas de negocio y datos: los eventos cubiertos son los de HU-22, HU-23, HU-24 y HU-32. El historial marca "Sistema" como origen. \[SUPUESTO\]  
* Restricciones (requerimientos no funcionales):  
  * Cada evento genera exactamente un cambio de estado.  
  * El cambio se aplica en 30 segundos o menos. \[SUPUESTO\]  
* Criterios de aceptación:  
  * AC-HU-42-1 (Camino feliz): Dado un pago aprobado, cuando llega el evento, entonces el pedido cambia a "Pago aprobado" sin intervención.  
  * AC-HU-42-2 (Alternativo/Error): Dado un evento duplicado, cuando llega, entonces no se duplica el cambio.  
  * AC-HU-42-3 (Caso límite): Dado un evento que contradice el estado vigente, cuando llega, entonces no se aplica y se registra. \[SUPUESTO\]  
* Dependencias: HU-22, HU-23, HU-24, HU-32  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

---

### **ÉPICA 9: Notificaciones por Correo (NOTI)**

#### **Feature 9.1: Correos de cuenta**

**HU-43** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero recibir un correo al registrarme, para confirmar que mi cuenta fue creada.  
* Detalles de la HU:  
  * Tareas funcionales: enviar el correo de bienvenida tras el registro.  
  * Entrada: registro exitoso \| Proceso: se envía el correo \| Salida: correo recibido.  
  * Flujo de interfaz (texto): sin interfaz propia; el cliente lo recibe en su bandeja.  
  * Reglas de negocio y datos: se solapa con HU-44; si son dos correos distintos o uno solo no está definido (P-16).  
* Restricciones (requerimientos no funcionales):  
  * El correo se envía en 2 minutos o menos tras el registro. \[SUPUESTO\]  
  * Está en español y no contiene la contraseña.  
* Criterios de aceptación:  
  * AC-HU-43-1 (Camino feliz): Dado un registro exitoso, cuando se crea la cuenta, entonces el cliente recibe un correo de confirmación.  
  * AC-HU-43-2 (Alternativo/Error): Dado un fallo de envío, cuando ocurre, entonces el registro no se pierde y el envío se reintenta. \[SUPUESTO\]  
  * AC-HU-43-3 (Caso límite): Dado un correo con dominio inexistente, cuando se envía, entonces el sistema registra el fallo sin afectar a otros clientes.  
* Dependencias: HU-7  
* Pre-chequeo DoR: \[1\] Calidad: No (se solapa con HU-44) \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-44** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero recibir un correo de verificación, para validar mi dirección de correo.  
* Detalles de la HU:  
  * Tareas funcionales: enviar el correo con el enlace de verificación; permitir reenviarlo.  
  * Entrada: registro o solicitud de reenvío \| Proceso: se genera y envía el enlace \| Salida: correo con enlace.  
  * Flujo de interfaz (texto): el cliente recibe el correo y abre el enlace (HU-8).  
  * Reglas de negocio y datos: el enlace es personal y de un solo uso. Vigencia no definida (P-3).  
* Restricciones (requerimientos no funcionales):  
  * El correo llega en 2 minutos o menos. \[SUPUESTO\]  
  * El enlace no es adivinable.  
* Criterios de aceptación:  
  * AC-HU-44-1 (Camino feliz): Dado un registro, cuando se crea la cuenta, entonces llega un correo con un enlace válido.  
  * AC-HU-44-2 (Alternativo/Error): Dado que el correo no llegó, cuando el cliente solicita reenvío, entonces se envía uno nuevo.  
  * AC-HU-44-3 (Caso límite): Dadas varias solicitudes de reenvío seguidas, cuando se hacen, entonces solo el último enlace es válido. \[SUPUESTO\]  
* Dependencias: HU-7  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-45** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero recibir un correo para recuperar mi contraseña, para restablecer mi acceso.  
* Detalles de la HU:  
  * Tareas funcionales: enviar el correo con el enlace de recuperación.  
  * Entrada: solicitud de recuperación \| Proceso: se genera y envía el enlace \| Salida: correo con enlace.  
  * Flujo de interfaz (texto): el cliente recibe el correo y abre el enlace (HU-10).  
  * Reglas de negocio y datos: se envía solo si el correo está registrado, sin revelarlo al solicitante.  
* Restricciones (requerimientos no funcionales):  
  * El correo llega en 2 minutos o menos. \[SUPUESTO\]  
  * El enlace es de un solo uso.  
* Criterios de aceptación:  
  * AC-HU-45-1 (Camino feliz): Dado un correo registrado, cuando solicita recuperar, entonces recibe el enlace.  
  * AC-HU-45-2 (Alternativo/Error): Dado un correo no registrado, cuando solicita recuperar, entonces no se envía correo y la pantalla muestra el mensaje genérico.  
  * AC-HU-45-3 (Caso límite): Dadas varias solicitudes seguidas, cuando se hacen, entonces solo el último enlace es válido. \[SUPUESTO\]  
* Dependencias: HU-10  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

#### **Feature 9.2: Correos de pedido**

**HU-46** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero recibir un correo cuando mi pedido sea creado, para tener constancia de mi compra.  
* Detalles de la HU:  
  * Tareas funcionales: enviar el correo al crearse el pedido con su resumen.  
  * Entrada: pedido creado \| Proceso: se compone y envía el correo \| Salida: correo con número de pedido, productos, total y estado.  
  * Flujo de interfaz (texto): sin interfaz propia; el cliente lo recibe en su bandeja.  
  * Reglas de negocio y datos: se dispara en la creación (estado "Pendiente de Pago"). Contenido exacto no definido (P-16).  
* Restricciones (requerimientos no funcionales):  
  * El correo se envía en 2 minutos o menos. \[SUPUESTO\]  
  * No incluye datos de pago.  
* Criterios de aceptación:  
  * AC-HU-46-1 (Camino feliz): Dado un pedido creado, cuando se registra, entonces el cliente recibe el correo con su resumen.  
  * AC-HU-46-2 (Alternativo/Error): Dado un fallo de envío, cuando ocurre, entonces el pedido no se afecta y se reintenta. \[SUPUESTO\]  
  * AC-HU-46-3 (Caso límite): Dado un pedido con varios productos, cuando se envía el correo, entonces todos aparecen listados.  
* Dependencias: HU-21  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-47** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero recibir un correo cuando mi pago sea aprobado o rechazado, para conocer el resultado del pago.  
* Detalles de la HU:  
  * Tareas funcionales: enviar un correo diferenciado según el resultado.  
  * Entrada: resultado del pago \| Proceso: se elige la plantilla según el resultado \| Salida: correo de pago aprobado o rechazado.  
  * Flujo de interfaz (texto): sin interfaz propia.  
  * Reglas de negocio y datos: ante rechazo, el correo informa que el pedido fue cancelado.  
* Restricciones (requerimientos no funcionales):  
  * El correo se envía en 2 minutos o menos tras el resultado. \[SUPUESTO\]  
  * No incluye datos de la tarjeta.  
* Criterios de aceptación:  
  * AC-HU-47-1 (Camino feliz): Dado un pago aprobado, cuando se confirma, entonces el cliente recibe el correo de aprobación.  
  * AC-HU-47-2 (Alternativo/Error): Dado un pago rechazado, cuando se registra, entonces recibe el correo de rechazo y cancelación.  
  * AC-HU-47-3 (Caso límite): Dado un resultado repetido, cuando se procesa dos veces, entonces se envía un solo correo.  
* Dependencias: HU-22, HU-23  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-48** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero recibir un correo cuando mi pedido esté en preparación, enviado o entregado, para seguir su avance sin entrar a la plataforma.  
* Detalles de la HU:  
  * Tareas funcionales: enviar un correo ante cada uno de los tres estados.  
  * Entrada: cambio manual de estado \| Proceso: se envía el correo del estado \| Salida: correo recibido.  
  * Flujo de interfaz (texto): sin interfaz propia.  
  * Reglas de negocio y datos: se solapa con HU-49 (ver sección 5).  
* Restricciones (requerimientos no funcionales):  
  * El correo se envía en 2 minutos o menos. \[SUPUESTO\]  
  * El correo indica el número de pedido y el nuevo estado.  
* Criterios de aceptación:  
  * AC-HU-48-1 (Camino feliz): Dado un pedido que pasa a "Enviado", cuando el administrador lo actualiza, entonces el cliente recibe el correo.  
  * AC-HU-48-2 (Alternativo/Error): Dado un fallo de envío, cuando ocurre, entonces el estado se mantiene y se reintenta. \[SUPUESTO\]  
  * AC-HU-48-3 (Caso límite): Dados dos cambios rápidos de estado, cuando ocurren, entonces se envía un correo por cada uno en orden.  
* Dependencias: HU-41  
* Pre-chequeo DoR: \[1\] Calidad: No (se solapa con HU-49) \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-49** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero recibir un correo ante cualquier cambio de estado de mi pedido, para estar siempre informado.  
* Detalles de la HU:  
  * Tareas funcionales: enviar un correo ante cualquier transición, incluidas las automáticas.  
  * Entrada: cambio de estado \| Proceso: se compone y envía \| Salida: correo con el nuevo estado.  
  * Flujo de interfaz (texto): sin interfaz propia.  
  * Reglas de negocio y datos: se solapa con HU-46, 47 y 48\. No se define si un solo cambio genera uno o varios correos (P-16).  
* Restricciones (requerimientos no funcionales):  
  * Un cambio de estado genera como máximo 1 correo. \[SUPUESTO\]  
  * El correo se envía en 2 minutos o menos. \[SUPUESTO\]  
* Criterios de aceptación:  
  * AC-HU-49-1 (Camino feliz): Dado un cambio de estado cualquiera, cuando ocurre, entonces el cliente recibe un correo con el nuevo estado.  
  * AC-HU-49-2 (Alternativo/Error): Dado un cambio que ya notifica otra HU, cuando ocurre, entonces no se envía un correo duplicado. \[SUPUESTO\]  
  * AC-HU-49-3 (Caso límite): Dado un cambio automático por timeout, cuando ocurre, entonces el cliente recibe el correo de cancelación.  
* Dependencias: HU-42, HU-41  
* Pre-chequeo DoR: \[1\] Calidad: No (duplica HU-46/47/48) \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

---

### **ÉPICA 10: Chatbot con IA (CHAT)**

#### **Feature 10.1: Acceso al chatbot**

**HU-50** \[IA-TEXTO\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero usar el chatbot solo con sesión iniciada, para conversar con el agente desde mi cuenta.  
* Detalles de la HU:  
  * Tareas funcionales: habilitar el chatbot solo con sesión; dirigir a los visitantes al inicio de sesión.  
  * Entrada: sesión activa y mensajes de texto \| Proceso: se valida la sesión y se abre la conversación \| Salida: conversación disponible.  
  * Flujo de interfaz (texto): el cliente abre el chatbot, escribe y ve la respuesta en la ventana de chat. El visitante ve una invitación a iniciar sesión.  
  * Reglas de negocio y datos: sin sesión no hay chatbot. El chatbot trabaja solo con texto.  
* Restricciones (requerimientos no funcionales):  
  * Un visitante no puede usar el chatbot en el 100 % de los intentos.  
  * La respuesta del chatbot llega en 10 segundos o menos. \[SUPUESTO\]  
  * Los mensajes del cliente no se comparten con otros clientes.  
* Criterios de aceptación:  
  * AC-HU-50-1 (Camino feliz): Dado un cliente con sesión, cuando abre el chatbot y escribe, entonces recibe respuesta.  
  * AC-HU-50-2 (Alternativo/Error): Dado un visitante sin sesión, cuando intenta abrir el chatbot, entonces se le dirige a iniciar sesión.  
  * AC-HU-50-3 (Caso límite): Dada una sesión que expira durante la conversación, cuando envía un mensaje, entonces se le pide iniciar sesión sin perder el carrito.  
  * AC-HU-50-4 (IA — respuesta incorrecta/vacía/fuera de contexto): Dada una respuesta vacía, con error o fuera del tema de RM Shop, cuando ocurre, entonces el chatbot informa que no puede responder y sugiere navegar el catálogo. \[SUPUESTO sobre el texto exacto\]  
  * AC-HU-50-5 (IA — privacidad): Dada una conversación, cuando termina, entonces no queda almacenada ni visible para otros y se informa al cliente. \[SUPUESTO; ver P-13\]  
* Dependencias: HU-9  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-51** \[IA-TEXTO\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero que el uso del chatbot tenga un límite por cliente, para que el servicio se mantenga sostenible.  
* Detalles de la HU:  
  * Tareas funcionales: contar el uso por cliente; bloquear al llegar al límite; informar el límite.  
  * Entrada: mensajes del cliente \| Proceso: se acumula el uso y se compara con el límite \| Salida: servicio permitido o bloqueado con aviso.  
  * Flujo de interfaz (texto): al alcanzar el límite el chatbot muestra "Has alcanzado tu límite de uso" y deshabilita el envío.  
  * Reglas de negocio y datos: existe un límite por cliente, pero su valor y su período de reinicio no están definidos (P-13).  
* Restricciones (requerimientos no funcionales):  
  * El límite se aplica en el 100 % de los casos.  
  * El cliente ve su uso restante o el aviso en 1 segundo o menos. \[SUPUESTO\]  
  * Un cliente no puede evadir el límite abriendo varias conversaciones.  
* Criterios de aceptación:  
  * AC-HU-51-1 (Camino feliz): Dado un cliente bajo el límite, cuando usa el chatbot, entonces recibe respuestas normales.  
  * AC-HU-51-2 (Alternativo/Error): Dado un cliente que alcanzó el límite, cuando envía otro mensaje, entonces no recibe respuesta de IA y ve el aviso.  
  * AC-HU-51-3 (Caso límite): Dado un cliente en el último mensaje permitido, cuando lo envía, entonces se responde y luego se bloquea. \[SUPUESTO\]  
  * AC-HU-51-4 (IA — respuesta incorrecta/vacía/fuera de contexto): Dada una respuesta vacía o con error, cuando ocurre, entonces no se descuenta del límite del cliente. \[SUPUESTO\]  
  * AC-HU-51-5 (IA — privacidad): Dado el conteo de uso, cuando se registra, entonces solo se guarda la cantidad de uso y no el contenido de los mensajes. \[SUPUESTO\]  
* Dependencias: HU-50  
* Pre-chequeo DoR: \[1\] Calidad: No (el valor y la unidad del límite no están definidos; afecta la testeabilidad) \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

#### **Feature 10.2: Asistencia de compra**

**HU-52** \[IA-TEXTO\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero consultar productos según tallas, colores y stock, para resolver mis dudas de disponibilidad de forma inmediata. *(Primera parte de la división de la HU original; ver sección 3.)*  
* Detalles de la HU:  
  * Tareas funcionales: responder preguntas sobre disponibilidad de una prenda, talla o color.  
  * Entrada: pregunta en texto \| Proceso: el chatbot consulta el catálogo y el stock reales \| Salida: respuesta con disponibilidad.  
  * Flujo de interfaz (texto): el cliente escribe "¿Hay buzo negro talla M?" y recibe la disponibilidad, con la opción de agregarlo.  
  * Reglas de negocio y datos: solo informa sobre productos de RM y sus datos reales; no inventa productos ni stock.  
* Restricciones (requerimientos no funcionales):  
  * La respuesta coincide con el stock real (0 discrepancias).  
  * La respuesta llega en 10 segundos o menos. \[SUPUESTO\]  
  * Solo usa datos del catálogo, no datos personales del cliente.  
* Criterios de aceptación:  
  * AC-HU-52-1 (Camino feliz): Dada una variante con stock, cuando el cliente pregunta por ella, entonces el chatbot confirma su disponibilidad.  
  * AC-HU-52-2 (Alternativo/Error): Dada una variante agotada, cuando se pregunta, entonces el chatbot informa que está agotada.  
  * AC-HU-52-3 (Caso límite): Dada una pregunta por un producto que no existe, cuando se hace, entonces el chatbot dice que no lo encuentra y no inventa información.  
  * AC-HU-52-4 (IA — respuesta incorrecta/vacía/fuera de contexto): Dada una pregunta ajena a RM Shop o una respuesta vacía, cuando ocurre, entonces el chatbot informa que no puede responder y sugiere el catálogo. \[SUPUESTO\]  
  * AC-HU-52-5 (IA — privacidad): Dada la consulta, cuando se procesa, entonces no se envían datos personales del cliente (correo, dirección) al procesamiento de IA. \[SUPUESTO\]  
* Dependencias: HU-50, HU-37  
* Pre-chequeo DoR: \[1\] Calidad: Sí (tras la división) \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-52b** \[IA-TEXTO\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero recibir recomendaciones de productos según tallas, colores y stock, para encontrar prendas adecuadas sin buscar manualmente. *(Segunda parte de la división de HU-52.)*  
* Detalles de la HU:  
  * Tareas funcionales: sugerir productos disponibles según lo que el cliente pida.  
  * Entrada: descripción de lo que busca \| Proceso: se filtran productos con stock que coincidan \| Salida: lista breve de sugerencias.  
  * Flujo de interfaz (texto): el cliente escribe "busco algo para el frío en talla S" y recibe sugerencias con su enlace al producto.  
  * Reglas de negocio y datos: solo recomienda productos con stock. El criterio de recomendación no está definido (P-14).  
* Restricciones (requerimientos no funcionales):  
  * Todas las recomendaciones están en el catálogo real y con stock (0 productos inexistentes).  
  * La respuesta llega en 10 segundos o menos. \[SUPUESTO\]  
* Criterios de aceptación:  
  * AC-HU-52b-1 (Camino feliz): Dada una petición clara, cuando el cliente la envía, entonces recibe sugerencias reales con stock.  
  * AC-HU-52b-2 (Alternativo/Error): Dada una petición sin coincidencias, cuando se envía, entonces el chatbot informa que no hay opciones y sugiere el catálogo.  
  * AC-HU-52b-3 (Caso límite): Dada una petición muy vaga, cuando se envía, entonces el chatbot pide aclarar o sugiere navegar el catálogo. \[SUPUESTO\]  
  * AC-HU-52b-4 (IA — respuesta incorrecta/vacía/fuera de contexto): Dada una respuesta que menciona un producto inexistente o vacía, cuando ocurre, entonces no se muestra al cliente y se responde con el mensaje de "no puedo responder". \[SUPUESTO\]  
  * AC-HU-52b-5 (IA — privacidad): Dada la recomendación, cuando se genera, entonces no usa ni conserva el historial de compras del cliente. \[SUPUESTO\]  
* Dependencias: HU-52  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-53** \[IA-TEXTO\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero que el chatbot agregue productos a mi carrito, para armar mi compra desde la conversación. *(Primera parte de la división de la HU original; ver sección 3.)*  
* Detalles de la HU:  
  * Tareas funcionales: agregar una variante al carrito a petición del cliente; confirmar la acción.  
  * Entrada: petición de agregar una variante y cantidad \| Proceso: se valida stock y se agrega (misma regla que HU-13) \| Salida: carrito actualizado y confirmación.  
  * Flujo de interfaz (texto): el cliente escribe "agrega el buzo negro M" y el chatbot confirma; el carrito muestra el ítem.  
  * Reglas de negocio y datos: aplican las reglas de reserva de stock de 15 minutos. Si pide confirmación antes de agregar, no está definido (P-14).  
* Restricciones (requerimientos no funcionales):  
  * Cada petición agrega como máximo lo solicitado (0 ítems no pedidos).  
  * La acción se refleja en el carrito en 5 segundos o menos. \[SUPUESTO\]  
* Criterios de aceptación:  
  * AC-HU-53-1 (Camino feliz): Dada una variante con stock, cuando el cliente pide agregarla, entonces aparece en su carrito y el chatbot lo confirma.  
  * AC-HU-53-2 (Alternativo/Error): Dada una variante agotada, cuando se pide, entonces no se agrega y el chatbot lo informa.  
  * AC-HU-53-3 (Caso límite): Dada una petición ambigua (sin talla o color), cuando se envía, entonces el chatbot pregunta lo que falta antes de agregar. \[SUPUESTO\]  
  * AC-HU-53-4 (IA — respuesta incorrecta/vacía/fuera de contexto): Dada una interpretación incorrecta o respuesta vacía, cuando ocurre, entonces no se modifica el carrito y se informa al cliente.  
  * AC-HU-53-5 (IA — privacidad): Dada la acción, cuando se ejecuta, entonces solo afecta el carrito del cliente con sesión. \[SUPUESTO\]  
* Dependencias: HU-52, HU-13  
* Pre-chequeo DoR: \[1\] Calidad: Sí (tras la división) \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-53b** \[IA-TEXTO\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero que el chatbot modifique o quite productos de mi carrito, para ajustar mi compra desde la conversación. *(Segunda parte de la división de HU-53.)*  
* Detalles de la HU:  
  * Tareas funcionales: cambiar cantidades o eliminar ítems por petición.  
  * Entrada: petición de modificar o quitar \| Proceso: se valida y se aplica (misma regla que HU-14 y HU-15) \| Salida: carrito actualizado y confirmación.  
  * Flujo de interfaz (texto): el cliente escribe "quita el buzo" o "pon 2 camisetas" y el chatbot confirma.  
  * Reglas de negocio y datos: la cantidad no supera el stock. Aplican las reglas del carrito.  
* Restricciones (requerimientos no funcionales):  
  * No se modifican ítems distintos del pedido (0 cambios no solicitados).  
  * La acción se refleja en 5 segundos o menos. \[SUPUESTO\]  
* Criterios de aceptación:  
  * AC-HU-53b-1 (Camino feliz): Dado un ítem en el carrito, cuando el cliente pide cambiar la cantidad, entonces se actualiza y se confirma.  
  * AC-HU-53b-2 (Alternativo/Error): Dada una cantidad mayor al stock, cuando se pide, entonces no se aplica y se informa el máximo.  
  * AC-HU-53b-3 (Caso límite): Dado un carrito con varios ítems similares, cuando la petición es ambigua, entonces el chatbot pregunta cuál. \[SUPUESTO\]  
  * AC-HU-53b-4 (IA — respuesta incorrecta/vacía/fuera de contexto): Dada una interpretación incorrecta o vacía, cuando ocurre, entonces el carrito no cambia y se informa.  
  * AC-HU-53b-5 (IA — privacidad): Dada la acción, cuando se ejecuta, entonces solo afecta el carrito del cliente con sesión. \[SUPUESTO\]  
* Dependencias: HU-53, HU-14, HU-15  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-54** \[IA-TEXTO\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero que el chatbot deje mi carrito preparado para el checkout sin procesar el pago, para completar yo mismo el pago en la pasarela.  
* Detalles de la HU:  
  * Tareas funcionales: dejar el carrito listo; llevar al cliente al checkout; no procesar pagos.  
  * Entrada: petición de pagar \| Proceso: se valida el carrito y se redirige al checkout \| Salida: acceso al checkout con el carrito listo.  
  * Flujo de interfaz (texto): el cliente escribe "quiero pagar" y el chatbot muestra un botón "Ir al pago" que abre el resumen; el pago lo hace el cliente.  
  * Reglas de negocio y datos: el chatbot no procesa pagos ni recibe datos de tarjeta.  
* Restricciones (requerimientos no funcionales):  
  * El chatbot nunca solicita ni procesa datos de pago (0 casos).  
  * El acceso al checkout ocurre en 3 segundos o menos. \[SUPUESTO\]  
* Criterios de aceptación:  
  * AC-HU-54-1 (Camino feliz): Dado un carrito con ítems, cuando el cliente pide pagar, entonces el chatbot lo lleva al checkout sin cobrar.  
  * AC-HU-54-2 (Alternativo/Error): Dado un carrito vacío, cuando pide pagar, entonces el chatbot informa que no hay productos.  
  * AC-HU-54-3 (Caso límite): Dada una reserva expirada, cuando pide pagar, entonces el chatbot avisa y verifica el stock de nuevo.  
  * AC-HU-54-4 (IA — respuesta incorrecta/vacía/fuera de contexto): Dada una petición de pagar dentro del chat o una respuesta vacía, cuando ocurre, entonces el chatbot rechaza procesar el pago y dirige al checkout.  
  * AC-HU-54-5 (IA — privacidad): Dado el cliente, cuando comparte datos de tarjeta en el chat, entonces el chatbot no los usa ni los almacena y le recomienda no compartirlos. \[SUPUESTO\]  
* Dependencias: HU-53, HU-19, HU-20  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: No (depende de una HU de checkout inexistente) \| \[4-6\] Se evalúan en Etapa 3

---

### **ÉPICA 11: Legal y Postventa (LEGAL)**

#### **Feature 11.1: Políticas legales**

**HU-55** \[SIN-IA\]

* Actor(es): Visitante sin cuenta  
* Descripción: Como Visitante sin cuenta, quiero consultar el apartado de tratamiento de datos personales y de pago, para saber cómo se manejará mi información.  
* Detalles de la HU:  
  * Tareas funcionales: mostrar la política; enlazarla desde el pie de página y el registro.  
  * Entrada: acceso a la página \| Proceso: se muestra el texto vigente \| Salida: política legible.  
  * Flujo de interfaz (texto): el visitante abre el enlace "Tratamiento de datos" y lee la política.  
  * Reglas de negocio y datos: redactada por el equipo de desarrollo; debe cumplir la normativa aplicable (no especificada, P-17).  
* Restricciones (requerimientos no funcionales):  
  * Es accesible sin sesión, desde cualquier página, a 1 clic.  
  * El texto es legible en celular sin desplazamiento horizontal.  
* Criterios de aceptación:  
  * AC-HU-55-1 (Camino feliz): Dado un visitante, cuando abre el enlace, entonces lee la política completa.  
  * AC-HU-55-2 (Alternativo/Error): Dada una falla al cargar, cuando ocurre, entonces se muestra un mensaje de error con opción de reintentar.  
  * AC-HU-55-3 (Caso límite): Dado un registro, cuando el visitante lo completa, entonces tiene acceso a la política desde el formulario. \[SUPUESTO\]  
* Dependencias: Ninguna  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-56** \[SIN-IA\]

* Actor(es): Visitante sin cuenta  
* Descripción: Como Visitante sin cuenta, quiero consultar los términos y condiciones, para conocer las reglas de uso y compra de la plataforma.  
* Detalles de la HU:  
  * Tareas funcionales: mostrar los términos; enlazarlos desde el pie de página y el checkout.  
  * Entrada: acceso a la página \| Proceso: se muestra el texto vigente \| Salida: términos legibles.  
  * Flujo de interfaz (texto): el visitante abre "Términos y condiciones" y los lee.  
  * Reglas de negocio y datos: redactados por el equipo; contienen el enlace de WhatsApp (HU-58). Si deben aceptarse expresamente al registrarse o comprar, no está definido (P-17).  
* Restricciones (requerimientos no funcionales):  
  * Accesible sin sesión a 1 clic desde cualquier página.  
  * Legible en celular sin desplazamiento horizontal.  
* Criterios de aceptación:  
  * AC-HU-56-1 (Camino feliz): Dado un visitante, cuando abre el enlace, entonces lee los términos.  
  * AC-HU-56-2 (Alternativo/Error): Dada una falla al cargar, cuando ocurre, entonces ve un mensaje de error con opción de reintentar.  
  * AC-HU-56-3 (Caso límite): Dado un cliente en el checkout, cuando busca los términos, entonces tiene acceso desde ese paso. \[SUPUESTO\]  
* Dependencias: Ninguna  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-57** \[SIN-IA\]

* Actor(es): Visitante sin cuenta  
* Descripción: Como Visitante sin cuenta, quiero consultar la política de garantías, para conocer las condiciones de postventa.  
* Detalles de la HU:  
  * Tareas funcionales: mostrar la política de garantías.  
  * Entrada: acceso a la página \| Proceso: se muestra el texto vigente \| Salida: política legible.  
  * Flujo de interfaz (texto): el visitante abre "Política de garantías" y la lee.  
  * Reglas de negocio y datos: los cambios, garantías y devoluciones se gestionan fuera de la web. El contenido de la política no está definido (P-17).  
* Restricciones (requerimientos no funcionales):  
  * Accesible sin sesión a 1 clic desde cualquier página.  
  * Legible en celular sin desplazamiento horizontal.  
* Criterios de aceptación:  
  * AC-HU-57-1 (Camino feliz): Dado un visitante, cuando abre el enlace, entonces lee la política.  
  * AC-HU-57-2 (Alternativo/Error): Dada una falla al cargar, cuando ocurre, entonces ve un mensaje de error con opción de reintentar.  
  * AC-HU-57-3 (Caso límite): Dado un cambio de política, cuando se publica, entonces el visitante ve la versión vigente con su fecha. \[SUPUESTO\]  
* Dependencias: Ninguna  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

#### **Feature 11.2: Contacto de postventa**

**HU-58** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero encontrar el enlace o número de WhatsApp únicamente dentro de la sección de Términos, Condiciones y Políticas de Garantía, para gestionar cambios, garantías y devoluciones directamente con la marca.  
* Detalles de la HU:  
  * Tareas funcionales: incluir el enlace o número de WhatsApp en esa sección y en ningún otro lugar.  
  * Entrada: acceso a la sección \| Proceso: se muestra el contacto \| Salida: enlace o número visible.  
  * Flujo de interfaz (texto): el cliente abre Términos y Garantías y toca el enlace de WhatsApp, que abre la conversación externa.  
  * Reglas de negocio y datos: la gestión de cambios, garantías, devoluciones y reembolsos ocurre por WhatsApp, fuera de la web. El número no está definido (P-17).  
* Restricciones (requerimientos no funcionales):  
  * El contacto aparece solo en la sección indicada (0 apariciones en otras pantallas).  
  * El enlace abre WhatsApp en 1 clic.  
* Criterios de aceptación:  
  * AC-HU-58-1 (Camino feliz): Dado un cliente en la sección de Términos y Garantías, cuando la abre, entonces ve el enlace de WhatsApp.  
  * AC-HU-58-2 (Alternativo/Error): Dado que el cliente no tiene WhatsApp instalado, cuando toca el enlace, entonces ve el número para contactar de otra forma. \[SUPUESTO\]  
  * AC-HU-58-3 (Caso límite): Dado cualquier otra pantalla (catálogo, pedidos, chatbot), cuando se revisa, entonces no muestra el contacto de WhatsApp.  
* Dependencias: HU-56, HU-57  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

---

### **ÉPICA 12: Experiencia de Usuario y Marca (EXPER)**

#### **Feature 12.1: Diseño adaptable y tema**

**HU-59** \[SIN-IA\]

* Actor(es): Visitante sin cuenta  
* Descripción: Como Visitante sin cuenta, quiero usar la plataforma de forma adaptada a celular, tablet y computador, para navegar cómodamente desde cualquier dispositivo.  
* Detalles de la HU:  
  * Tareas funcionales: adaptar la interfaz a los tres tipos de pantalla.  
  * Entrada: dispositivo del usuario \| Proceso: la interfaz se ajusta al ancho \| Salida: página usable.  
  * Flujo de interfaz (texto): el usuario abre el sitio en cualquier dispositivo y todas las pantallas se ajustan sin desplazamiento horizontal.  
  * Reglas de negocio y datos: aplica a pantallas de clientes y del panel. Anchos y navegadores mínimos sin definir (P-20).  
* Restricciones (requerimientos no funcionales):  
  * Ninguna pantalla requiere desplazamiento horizontal en anchos desde 360 píxeles. \[SUPUESTO\]  
  * Los botones tienen área táctil de al menos 44×44 píxeles. \[SUPUESTO\]  
  * Funciona en las versiones actuales de los navegadores principales.  
* Criterios de aceptación:  
  * AC-HU-59-1 (Camino feliz): Dado un celular de 360 píxeles de ancho, cuando se abre el catálogo, entonces se ve completo sin desplazamiento horizontal.  
  * AC-HU-59-2 (Alternativo/Error): Dada una pantalla con tabla de pedidos, cuando se ve en celular, entonces el contenido sigue legible y operable.  
  * AC-HU-59-3 (Caso límite): Dado un cambio de orientación, cuando el usuario gira el dispositivo, entonces la interfaz se reajusta sin perder lo ingresado.  
* Dependencias: Ninguna  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-60** \[SIN-IA\]

* Actor(es): Visitante sin cuenta  
* Descripción: Como Visitante sin cuenta, quiero ver toda la plataforma en español, para entender claramente su contenido.  
* Detalles de la HU:  
  * Tareas funcionales: textos, mensajes de error y correos en español.  
  * Entrada: acceso a cualquier pantalla \| Proceso: se muestran textos en español \| Salida: interfaz en español.  
  * Flujo de interfaz (texto): todas las pantallas, mensajes y notificaciones aparecen en español.  
  * Reglas de negocio y datos: solo español. Moneda en COP.  
* Restricciones (requerimientos no funcionales):  
  * El 100 % de los textos visibles está en español.  
  * Los formatos de fecha y moneda siguen la convención colombiana. \[SUPUESTO\]  
* Criterios de aceptación:  
  * AC-HU-60-1 (Camino feliz): Dada cualquier pantalla, cuando se revisa, entonces todos los textos están en español.  
  * AC-HU-60-2 (Alternativo/Error): Dado un error del sistema, cuando se muestra, entonces el mensaje está en español.  
  * AC-HU-60-3 (Caso límite): Dado un navegador configurado en otro idioma, cuando se abre el sitio, entonces sigue mostrándose en español.  
* Dependencias: Ninguna  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

#### **Feature 12.2: Accesibilidad básica**

**HU-61** \[SIN-IA\]

* Actor(es): Visitante sin cuenta  
* Descripción: Como Visitante sin cuenta, quiero que cada imagen tenga texto alternativo, para acceder a su contenido con lectores de pantalla.  
* Detalles de la HU:  
  * Tareas funcionales: asegurar el texto alternativo en toda imagen informativa.  
  * Entrada: imágenes del sitio \| Proceso: se asocia el texto alternativo \| Salida: imágenes con descripción.  
  * Flujo de interfaz (texto): el lector de pantalla lee la descripción de cada imagen del catálogo.  
  * Reglas de negocio y datos: el texto alternativo de productos lo ingresa el administrador (HU-35).  
* Restricciones (requerimientos no funcionales):  
  * El 100 % de las imágenes informativas tiene texto alternativo.  
  * El texto alternativo describe la prenda.  
* Criterios de aceptación:  
  * AC-HU-61-1 (Camino feliz): Dada una imagen de producto, cuando la lee un lector de pantalla, entonces anuncia su descripción.  
  * AC-HU-61-2 (Alternativo/Error): Dada una imagen sin texto alternativo ingresado, cuando se muestra, entonces usa uno por defecto (nombre del producto). \[SUPUESTO\]  
  * AC-HU-61-3 (Caso límite): Dada una imagen meramente decorativa, cuando se muestra, entonces se omite para lectores de pantalla. \[SUPUESTO\]  
* Dependencias: HU-35  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-62** \[SIN-IA\]

* Actor(es): Visitante sin cuenta  
* Descripción: Como Visitante sin cuenta, quiero un contraste adecuado y texto legible, para ver el contenido de la plataforma con buena legibilidad. *(Primera parte de la división de la HU original; ver sección 3.)*  
* Detalles de la HU:  
  * Tareas funcionales: garantizar contraste y tamaño de texto legibles en todas las pantallas.  
  * Entrada: pantallas del sitio \| Proceso: se aplican colores y tamaños \| Salida: texto legible.  
  * Flujo de interfaz (texto): el usuario lee el texto en todas las pantallas sin esfuerzo.  
  * Reglas de negocio y datos: se usa la paleta y tipografía de la marca (entregadas por la clienta). El nivel de accesibilidad exigido no está definido (P-20).  
* Restricciones (requerimientos no funcionales):  
  * La relación de contraste del texto es al menos 4.5:1. \[SUPUESTO\]  
  * El texto principal mide al menos 16 píxeles. \[SUPUESTO\]  
* Criterios de aceptación:  
  * AC-HU-62-1 (Camino feliz): Dado un texto principal sobre su fondo, cuando se mide el contraste, entonces es de 4.5:1 o más. \[SUPUESTO\]  
  * AC-HU-62-2 (Alternativo/Error): Dada una combinación de colores de marca con bajo contraste, cuando se detecta, entonces se ajusta para cumplir el umbral. \[SUPUESTO\]  
  * AC-HU-62-3 (Caso límite): Dado el texto ampliado al 200 % en el navegador, cuando se ve la página, entonces el contenido sigue legible y sin superposiciones. \[SUPUESTO\]  
* Dependencias: Ninguna  
* Pre-chequeo DoR: \[1\] Calidad: Sí (tras la división) \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-62b** \[SIN-IA\]

* Actor(es): Visitante sin cuenta  
* Descripción: Como Visitante sin cuenta, quiero navegar por teclado con foco visual, para usar la plataforma sin depender del mouse. *(Segunda parte de la división de HU-62.)*  
* Detalles de la HU:  
  * Tareas funcionales: permitir acceder y operar todos los controles con teclado; resaltar el elemento con foco.  
  * Entrada: teclas de navegación \| Proceso: el foco recorre los elementos en orden lógico \| Salida: operación completa por teclado.  
  * Flujo de interfaz (texto): el usuario usa Tab para recorrer enlaces, botones y formularios, y ve siempre cuál tiene el foco.  
  * Reglas de negocio y datos: aplica a la tienda y al panel.  
* Restricciones (requerimientos no funcionales):  
  * El 100 % de los controles es operable con teclado.  
  * El elemento con foco es visible en todo momento.  
  * No hay trampas de foco (se puede salir de cualquier componente con teclado).  
* Criterios de aceptación:  
  * AC-HU-62b-1 (Camino feliz): Dada la página de catálogo, cuando el usuario recorre con Tab, entonces cada elemento interactivo recibe foco visible en orden lógico.  
  * AC-HU-62b-2 (Alternativo/Error): Dado un diálogo o menú abierto, cuando el usuario pulsa Escape, entonces se cierra y el foco vuelve al elemento que lo abrió.  
  * AC-HU-62b-3 (Caso límite): Dado el flujo completo de compra, cuando se completa solo con teclado, entonces es posible sin usar el mouse.  
* Dependencias: Ninguna  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

**HU-63** \[SIN-IA\]

* Actor(es): Cliente registrado  
* Descripción: Como Cliente registrado, quiero ver mensajes de error claros en los formularios, para corregir mis datos fácilmente.  
* Detalles de la HU:  
  * Tareas funcionales: validar campos; mostrar mensajes junto al campo con error.  
  * Entrada: datos del formulario \| Proceso: validación \| Salida: mensajes específicos por campo.  
  * Flujo de interfaz (texto): al enviar un formulario con errores, cada campo inválido se marca con un mensaje que indica qué corregir.  
  * Reglas de negocio y datos: aplica a registro, inicio de sesión, recuperación de contraseña y dirección de envío. \[SUPUESTO\]  
* Restricciones (requerimientos no funcionales):  
  * El error aparece junto al campo en 1 segundo o menos.  
  * El mensaje se anuncia a lectores de pantalla.  
  * Los datos válidos ya ingresados no se pierden.  
* Criterios de aceptación:  
  * AC-HU-63-1 (Camino feliz): Dado un campo inválido, cuando el cliente envía el formulario, entonces ve un mensaje que explica la corrección.  
  * AC-HU-63-2 (Alternativo/Error): Dados varios campos inválidos, cuando se envía, entonces todos se marcan a la vez.  
  * AC-HU-63-3 (Caso límite): Dado un error de servidor, cuando ocurre, entonces el mensaje es comprensible y no muestra detalles técnicos.  
* Dependencias: HU-7  
* Pre-chequeo DoR: \[1\] Calidad: No (el término "claros" requiere definir los formularios cubiertos, ver P-19) \| \[2\] Criterios: Sí (con \[SUPUESTO\]) \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3

#### **Feature 12.3: Presencia de marca**

**HU-64** \[SIN-IA\]

* Actor(es): Visitante sin cuenta  
* Descripción: Como Visitante sin cuenta, quiero acceder a un enlace al Instagram de RM desde la plataforma, para conocer más de la marca en su red principal.  
* Detalles de la HU:  
  * Tareas funcionales: mostrar un enlace visible a Instagram; abrirlo en una pestaña nueva.  
  * Entrada: clic en el enlace \| Proceso: se abre el perfil de Instagram de RM \| Salida: perfil visible.  
  * Flujo de interfaz (texto): el visitante ve el ícono o enlace de Instagram en el pie de página y lo toca.  
  * Reglas de negocio y datos: solo Instagram; no hay otras redes. La dirección del perfil la debe entregar la clienta.  
* Restricciones (requerimientos no funcionales):  
  * El enlace es visible en todas las páginas.  
  * El enlace abre el perfil correcto en el 100 % de los casos.  
* Criterios de aceptación:  
  * AC-HU-64-1 (Camino feliz): Dado el sitio, cuando el visitante toca el enlace, entonces se abre el perfil de Instagram de RM.  
  * AC-HU-64-2 (Alternativo/Error): Dado que Instagram no carga, cuando el visitante vuelve al sitio, entonces la tienda sigue funcionando.  
  * AC-HU-64-3 (Caso límite): Dado un lector de pantalla, cuando se lee el enlace, entonces anuncia "Instagram de RM".  
* Dependencias: Ninguna  
* Pre-chequeo DoR: \[1\] Calidad: Sí \| \[2\] Criterios: Sí \| \[3\] Dependencias: Sí \| \[4-6\] Se evalúan en Etapa 3