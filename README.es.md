# 5 Tintas — tu página web

Tu página está aquí:

### https://5tintas.com

La dirección anterior, https://camilarestrepop.github.io, lleva al mismo sitio.

Esta guía te dice cómo cambiarla. Todo se hace en github.com, desde el navegador. No necesitas
instalar nada en tu computador, y no puedes romper nada: cada cambio se guarda como una versión
nueva, así que todo se puede devolver.

English: [README.md](README.md)

Los botones de GitHub están en inglés, así que los nombro en inglés y te explico al lado qué son.

<!-- Jack: aquí podrían ir capturas de pantalla, una debajo de cada paso. -->

---

## La única regla

Cada cambio que haces vuelve a construir la página sola. Tarda más o menos un minuto. Después
recargas la página en el navegador y ahí está tu cambio.

Si sigues viendo la página vieja, es la copia que guardó tu navegador. Mantén pulsada la tecla Shift
y haz clic en recargar, o espera unos minutos y vuelve a intentarlo.

Si algo en un archivo la confunde, **no** publica una página rota: te dice qué está mal, en palabras
sencillas, y nombra el archivo. Mira [¿Funcionó?](#funcionó) más abajo.

---

## Añadir una pieza a la tienda — la manera fácil

1. Entra a https://github.com/camilarestrepop/camilarestrepop.github.io
2. Haz clic en la pestaña **Issues** (arriba).
3. Haz clic en el botón verde **New issue** (formulario nuevo).
4. Al lado de **Add a product**, haz clic en **Get started**.
5. Llena el formulario:
   - **Name of the piece** (nombre de la pieza) — es lo que ve la gente. Este sí es obligatorio.
   - **Sizes** (tallas) — separadas por comas, como `XS, S, M`. Déjalo vacío si no aplica.
   - **Sold out** (agotado) — `No` o `Yes`.
   - **Collection** (colección) — elige una, o déjalo en `(none)`.
   - **Description in English** y **Descripción en español** — deja una línea en blanco entre
     párrafos. Si dejas el español vacío, se usa el texto en inglés en los dos idiomas.
   - **Photos** (fotos) — arrastra las fotos a la caja y espera a que cada una termine de subir. La
     primera que pongas es la foto grande que la gente ve primero. Esta también es obligatoria.
6. Haz clic en **Create**.

Eso es todo. En un par de minutos aparece una respuesta en lo que acabas de crear, con un enlace
directo a la página nueva, y la pieza ya está en la tienda.

Si alguna foto no se pudo guardar, la respuesta te lo dice y te da un enlace para arrastrarla a mano.
Tus palabras y la página ya están guardadas, así que no se pierde nada.

No le quites el título cuando llenes el formulario: ya empieza por `Add product:`, y en parte así es
como la página reconoce lo que estás pidiendo. Si no aparece ninguna respuesta después de cinco
minutos, dile a Jack.

---

## Añadir una pieza a la tienda — la otra manera

Úsala si prefieres no usar el formulario, o si quieres ver los archivos.

**Primero la carpeta y las palabras:**

1. Entra a https://github.com/camilarestrepop/camilarestrepop.github.io
2. Haz clic en **website**, luego en **content**, luego en **products**.
3. Haz clic en **Add file** (arriba a la derecha) y elige **Create new file**.
4. En la casilla del nombre escribe el nombre de la carpeta, una barra, y `info.md`. Por ejemplo:
   `vestido-eva/info.md`
   Usa minúsculas, números y guiones en vez de espacios. GitHub crea la carpeta sola en cuanto
   escribes la barra.
5. En la caja grande de abajo escribe los datos de la pieza. Abajo, en
   [La chuleta de info.md](#la-chuleta-de-infomd), hay una versión para copiar y pegar.
6. Haz clic en el botón verde **Commit changes...** y luego en **Commit changes** en la ventanita.

**Después las fotos:**

7. Ya estás dentro de tu carpeta nueva. Haz clic en **Add file** y elige **Upload files**.
8. En tu computador nombra las fotos `01.jpg`, `02.jpg`, `03.jpg`… La que se llama `01` es la foto
   grande que la gente ve primero.
9. Arrástralas a la página y haz clic en **Commit changes**.

---

## La chuleta de info.md

Cada pieza tiene un archivo `info.md`. Esto es todo lo que lleva:

```
name: Vestido Eva
sizes: XS, S, M, L
sold out: no
collection: eva-mitocondrial
date: 2026-09-13

--- ENGLISH ---
Hand-dyed denim dress, made to order.

Un segundo párrafo se ve así.

--- ESPANOL ---
Vestido de denim teñido a mano, hecho por encargo.
```

Qué significa cada línea:

| Línea | Qué hace |
| --- | --- |
| `name:` | Lo que ve la gente. Es la única línea de verdad obligatoria. |
| `name es:` | El nombre en español, si es distinto. Si la quitas se usa el nombre en inglés. |
| `sizes:` | Separadas por comas. Si escribes `XS, S, M, L` o `XL`, la página muestra toda la fila de tallas y tacha las que no pusiste. Si escribes otra cosa, como `Talla única`, solo se muestra eso. Déjalo vacío si no hay tallas. |
| `sold out:` | `no` o `yes`. Con `yes` las tallas se reemplazan por un bloque gris de **Agotado**. |
| `collection:` | A qué colección pertenece. Tiene que coincidir exactamente con el nombre de una carpeta dentro de `website/content/collections/`. Quita la línea si no pertenece a ninguna. |
| `date:` | Escrita como año-mes-día. Las piezas más nuevas se muestran primero en la tienda. |

Las líneas con dos puntos de arriba son los ajustes, y pueden ir en cualquier orden. Todo lo que va
desde la primera línea que no es uno de ellos es tu descripción: una frase con dos puntos, como
`Inspiración: el mar`, se queda en el texto tal como la escribiste.

Todo lo que va debajo de `--- ENGLISH ---` es la descripción en inglés, y todo lo que va debajo de
`--- ESPANOL ---` es la descripción en español. Deja una línea en blanco entre párrafos.

Una línea que empieza por `#` es una nota para ti. Nunca sale en la página.

Hay un ejemplo listo para copiar en `website/content/_TEMPLATE-product/info.md`. Las carpetas cuyo
nombre empieza por `_` nunca se publican, por eso esa no aparece en la tienda.

---

## Cambiar una descripción o un nombre

1. Ve al archivo: **website** → **content** → **products** → la carpeta → `info.md`
2. Haz clic en el lápiz, arriba a la derecha del archivo.
3. Cambia las palabras.
4. Haz clic en **Commit changes...** y luego en **Commit changes**.

Lo mismo funciona con cualquier otro archivo de palabras de la página.

---

## Cambiar el orden de las fotos

La foto que se llama `01` siempre va primero. Las demás siguen en orden de número.

Para reordenarlas, renómbralas en tu computador (`01.jpg`, `02.jpg`, `03.jpg`…) y súbelas otra vez
todas a la misma carpeta: **Add file** → **Upload files** → arrastrar → **Commit changes**. Una foto
con el mismo nombre que una que ya está simplemente la reemplaza.

Para quitar una foto: ábrela en la carpeta, haz clic en el botón **...** de arriba a la derecha,
elige **Delete file** y luego **Commit changes**.

---

## Quitar una pieza de la tienda

Tres maneras, de la más suave a la más definitiva:

1. **Marcarla agotada.** Edita su `info.md` y escribe `sold out: yes`. La página se queda, con un
   bloque gris de **Agotado** en lugar de las tallas.
2. **Quitarla.** Abre su carpeta, haz clic en el botón **...** de arriba a la derecha de la lista de
   archivos y elige **Delete directory**, luego **Commit changes**. Desaparece de la página, pero
   queda en el historial, así que siempre se puede recuperar.
3. **Esconderla sin quitarla.** Las carpetas cuyo nombre empieza por `_` nunca se publican. Abre el
   `info.md` de la pieza, haz clic en el lápiz, y en la casilla del nombre del archivo, arriba,
   ponle un `_` delante al nombre de la carpeta: `vestido-eva/info.md` pasa a ser
   `_vestido-eva/info.md`. Luego **Commit changes**. La pieza desaparece de la tienda, y quitando el
   `_` vuelve enseguida.

   Las fotos se pueden quedar donde están. La página menciona esa carpeta entre sus notas, igual que
   con cualquier pieza que todavía estés preparando, y todo sigue funcionando. Si la quieres dejar
   ordenada, mueve también las fotos a la carpeta con `_`.

---

## Cambiar tu Instagram, tu WhatsApp o tu correo

Están en un solo archivo, y toda la página lo lee.

1. Haz clic en **website** → **content** → `site.md`
2. Haz clic en el lápiz.
3. Cambia las líneas que quieras:
   ```
   instagram: https://instagram.com/5.tintas
   whatsapp: +1 347 362 2979
   email: camilarestrepo.fashionlab@gmail.com
   ```
4. Haz clic en **Commit changes...** y luego en **Commit changes**.

En ese mismo archivo están tu frase, la foto grande de la página principal, y cuántas piezas nuevas
muestra la página principal.

---

## Tu dirección web

La gente llega a tu página por **5tintas.com**. Esa dirección está escrita en el mismo archivo
`site.md`, en esta línea:

```
domain: 5tintas.com
```

Deja esa línea como está. Añadir una pieza, cambiar una foto o editar tus textos nunca la toca. Solo
importa si algún día cambia la dirección web, y entonces hay que cambiarla en dos sitios: esta línea
y **Settings** → **Pages** en github.com. Pídele a Jack que haga las dos cosas a la vez.

Tiene que quedarse ahí. Cada cambio que haces vuelve a publicar la página, y es esta línea la que le
dice a cada publicación que conserve tu dirección. Si se borrara la línea no se rompería nada: la
página volvería a responder en https://camilarestrepop.github.io.

Para GitHub, `www.5tintas.com` y `5tintas.com` no son la misma dirección, así que la que esté en esa
línea es la que hay que poner también en **Settings** → **Pages**.

---

## Colecciones y pasarelas

Funcionan igual que las piezas, cada una en su carpeta:

- Colecciones: **website** → **content** → **collections** → la carpeta → `info.md`
- Pasarelas: **website** → **content** → **runways** → la carpeta → `info.md`

Las fotos van en la misma carpeta que el `info.md`, nombradas `01.jpg`, `02.jpg`, `03.jpg`…

**Rayito de Sol**, **Añoranza** y las tres pasarelas dicen *muy pronto* por ahora, porque todavía no
tienen fotos. Sube fotos a sus carpetas y el *muy pronto* desaparece solo: no hay que cambiar nada
más.

La línea `order:` decide en qué lugar de la lista va cada colección. El `1` va de primero.

Si creas una colección **nueva**, falta una cosa más: la lista **Collection** del formulario "Add a
product" es fija, así que una colección nueva no aparece ahí hasta que se añada. La lista está en
`.github/ISSUE_TEMPLATE/add-product.yml` y Jack puede añadirle una línea en un minuto. Mientras
tanto, escribe a mano la línea `collection:` en el `info.md` de la pieza.

---

## Añadir un video a una pasarela o a una colección

El video va debajo de las fotos, con un botón de play. Hay dos maneras, y usas la que le convenga al
video que tengas. Una pasarela que no tenga ninguna de las dos dice **Video coming soon** (video muy
pronto) hasta que añadas uno.

### Manera 1: subir el archivo del video a la carpeta

1. En tu computador nombra el archivo `video.mp4`. También sirven `video.mov` y `video.webm`.
2. Entra a la carpeta de esa pasarela o colección: **website** → **content** → **runways** → la
   carpeta.
3. Haz clic en **Add file** y elige **Upload files**.
4. Arrastra el video y haz clic en **Commit changes**.

Eso es todo. El reproductor aparece solo debajo de las fotos.

**Lo único que hay que tener en cuenta:** github.com no acepta desde el navegador un archivo de más
de **25 MB**. Un video sacado directamente del celular casi siempre pesa mucho más, así que hay que
hacerlo más liviano primero, o usar la Manera 2. Si lo intentas igual, GitHub te dice que el archivo
es demasiado grande y no sube nada, así que no se rompe nada.

Para hacerlo más liviano, en iPhone lo más fácil es recortarlo y enviártelo a ti misma con menos
calidad, o pedirle a Jack que lo comprima una vez. Ten en cuenta también que un video pesado hace que
la página abra lento en el celular, así que más liviano es de verdad mejor.

### Manera 2: usar un enlace al video

Úsala para cualquier video largo o pesado. Sube el video a YouTube, Vimeo o Instagram y después:

1. Copia su enlace de la barra de direcciones del navegador.
2. Abre el `info.md` de esa carpeta y haz clic en el lápiz.
3. Añade una línea así:
   ```
   video: https://www.youtube.com/watch?v=XXXXXXXXXXX
   ```
4. Haz clic en **Commit changes...** y luego en **Commit changes**.

Así no hay límite de tamaño, y la página sigue abriendo rápido, porque el video se reproduce desde
YouTube, Vimeo o Instagram y no desde tu página.

Si una carpeta tiene las dos cosas, el archivo de la carpeta es el que se muestra.

---

## ¿Funcionó?

Cada cambio vuelve a publicar la página. Para verlo:

1. Entra a https://github.com/camilarestrepop/camilarestrepop.github.io
2. Haz clic en la pestaña **Actions** (arriba).
3. La primera línea de la lista es tu cambio.
   - Un **punto naranja** quiere decir que todavía está trabajando. Espera un minuto.
   - Un **chulo verde** quiere decir que ya está publicado. Recarga la página.
   - Una **equis roja** quiere decir que algo en los archivos la confundió. No se publicó nada, y la
     página que ve la gente sigue igual que antes.
4. Si es una equis roja, haz clic en esa primera línea, luego en el nombre del trabajo, y lee las
   últimas líneas del mensaje. Ahí dice qué archivo es y qué hacer, en palabras sencillas. Arregla
   ese archivo y la página se publica sola otra vez.

---

## Si te quedas atascada

Escríbele a Jack. Mándale:

- qué estabas tratando de hacer,
- el enlace de la página o del archivo en el que estabas.

Nada de lo que hagas aquí puede romper la página para siempre. Todas las versiones quedan guardadas.
