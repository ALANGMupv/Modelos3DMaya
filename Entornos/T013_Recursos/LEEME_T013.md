# T013 · Entorno carretera

Escena: `../T013_Entorno_Carretera.mb`. Es una copia de trabajo independiente de `../EntornoEntrada.mb`.

## Organización

La casa original conserva sus grupos (`CASA`, `TEJADO`, `CERRAMIENTOS_TEJADO`, `TECHOS_INTERIORES`, `PUERTA_EXTERIOR` y el respaldo oculto). El entorno añadido está bajo `T013_Entorno_Carretera`:

- `Terreno`: parcela y suelo de bosque.
- `Carretera`: calzada secundaria, arcenes y marcas desgastadas.
- `Acceso_Casa`: camino desde la calzada hasta la puerta, vallado con apertura y faroles.
- `Arboles_y_Vegetacion`: árboles, arbustos y hierbas instanciados.
- `Detalles_Carretera`: charcos, piedras, hojas, señal y cableado.
- `Iluminacion_Exterior`: ambiente frío y luces cálidas del acceso.
- `Camaras_T013`: vista de carretera, entrada y panorámica aérea.
- `Prototipos_Instancias_OCULTOS`: geometría maestra de árboles y elementos repetidos; conservar oculta.

Hay 81 árboles de tres especies visuales, 52 arbustos, 167 matas de hierba y 105 rocas. Los ejemplares son instancias de prototipos editables. El recuento aproximado de mallas visibles expandidas es 805.371 triángulos: 587.773 correspondientes a la casa y 217.598 al entorno nuevo. El recuento de Maya puede variar ligeramente según qué nodos y objetos ocultos se muestren.

Las texturas nuevas de asfalto, terreno, grava y corteza son [CC0 de Poly Haven](https://polyhaven.com/license). El follaje usa dos mapas procedurales propios. Se han reparado las rutas existentes de 72 texturas importadas de la casa para esta copia, sin cambiar sus materiales ni geometría. Esas rutas siguen apuntando al proyecto Unity del equipo.

La escena se guardó y se reabrió para comprobar que las 197 mallas originales conservan recuento de vértices, triángulos y límites espaciales, y que no quedan rutas de textura sin localizar.


