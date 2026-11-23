# Discusión de Trade-offs

La decisión de arquitectura para el acortador de URLs depende directamente de las necesidades operacionales de la universidad. A continuación se muestran las ventajas y desventajas de ambas arquitecturas:

### Arquitectura 1: Observabilidad y Analítica
Por un lado, la **Arquitectura 1** prioriza la recopilación de información estadística sobre el uso de las URLs acortadas. Al utilizar redirecciones temporales (**HTTP 302**), el navegador no guarda la redirección en su caché y vuelve a contactar al servicio cada vez que se visita una URL corta, permitiendo registrar cada evento de visita (`url hit`) mediante **gRPC** hacia el servicio de logs.

* **Beneficios:** Alta observabilidad del sistema, permitiendo analizar el tráfico de los enlaces para conocer el interés real de los usuarios, horarios punta y alcance de las distintas campañas que dispone la universidad. Además, si la URL de destino cambia en la base de datos, el cambio se refleja de inmediato para todos los usuarios.
* **Costos (Trade-offs):** Mayor carga de red, consumo de CPU y escrituras en disco por cada visita, sumado a una arquitectura más compleja de mantener al requerir dos procesos activos (`LiteStar` y servidor `gRPC`) y dos bases de datos independientes.

### Arquitectura 2: Rendimiento y Disponibilidad
Por otro lado, la **Arquitectura 2** prioriza el rendimiento, la disponibilidad y la eficiencia en el uso de recursos. Mediante redirecciones permanentes (**HTTP 301**), los navegadores almacenan el destino en su caché local y evitan realizar solicitudes posteriores al servidor. Adicionalmente, el *caching* en memoria de LiteStar (`ResponseCacheConfig`) permite reutilizar respuestas previamente generadas sin consultar la base de datos, mientras que el *Rate Limiting* controla la tasa de arribo de solicitudes para proteger el servicio ante tráfico excesivo o ataques.

* **Beneficios:** Latencia mínima para el usuario final, reducción drástica en la carga del servidor y despliegue simplificado en un único servicio.
* **Costos (Trade-offs):** Se produce una "ceguera" analítica respecto a la cantidad exacta de visitas que recibe un enlace después del primer clic de cada usuario. Además, al usar HTTP 301, si la universidad necesita modificar la URL de destino asociada a un *hash* ya publicado, los usuarios que lo visitaron previamente seguirán siendo redirigidos a la dirección antigua hasta que expiren o limpien la caché de sus navegadores.

---

### Conclusión y Recomendación para la USM

Para el contexto presentado, ambos *trade-offs* son beneficiosos y hacen que ninguna arquitectura sea ideal por sí sola para todos los servicios universitarios:
* Si el objetivo principal es analizar el comportamiento de los usuarios y obtener métricas de impacto, la **Arquitectura 1** resulta más conveniente.
* Si se busca ofrecer un servicio de alta disponibilidad, reducir la carga del servidor y soportar ráfagas masivas de tráfico, la **Arquitectura 2** representa una mejor alternativa.

Aprovechando la actual división de subdominios que presenta la USM (`usm.cl`, `siga.usm.cl`, `aula.usm.cl`, `casino.usm.cl`), la solución óptima es adoptar un **enfoque híbrido**:
1. **Usar Arquitectura 1 (HTTP 302 + gRPC)** para campañas de difusión y comunicaciones (Admisión, Postgrado, eventos culturales o noticias), donde medir el alcance y horarios de visita es clave para la toma de decisiones.
2. **Usar Arquitectura 2 (HTTP 301 + Caché + Rate Limit)** para enlaces institucionales estáticos de alta demanda (principalmente `SIGA` en semanas de inscripción de asignaturas, y en menor medida `Aula` y `Casino USM`).
---

## Bonus: Unicidad de Identificadores en un Ambiente Distribuido

En una arquitectura distribuida con múltiples instancias del acortador recibiendo peticiones `POST` en paralelo, depender de un contador local autoincremental en SQLite provocaría colisiones (dos nodos asignarían el mismo ID entero y generarían el mismo *hash* en base62 para URLs distintas). Para garantizar identificadores únicos sin colisiones manteniendo la codificación en **base62**, se puede aplicar la siguiente estrategia:

**Asignación de Rangos Disjuntos:** Un coordinador central asigna bloques exclusivos de IDs enteros a cada servidor al iniciar (por ejemplo, Nodo 1 usa el rango `[100, 199]` y Nodo 2 usa `[200, 299]` y así sucesivamente). Cada instancia incrementa su contador en memoria dentro de su bloque asignado y solicita un nuevo rango solo cuando lo agota, conservando hashes cortos y secuenciales.
