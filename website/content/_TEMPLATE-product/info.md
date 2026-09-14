# ============================================================================
#  HOW TO ADD A PIECE TO THE SHOP  (Como anadir una pieza a la tienda)
# ============================================================================
#
#  1. Copy this whole folder. (Copia toda esta carpeta.)
#  2. Put the copy inside  products/  and give it a short lowercase name with
#     dashes instead of spaces, for example  vestido-eva
#     (Ponla dentro de products/ con un nombre corto en minusculas y guiones.)
#  3. Upload the photos into that same folder and name them 01.jpg, 02.jpg,
#     03.jpg... The one named 01 is the big photo people see first.
#     (Sube las fotos a esa misma carpeta: 01.jpg, 02.jpg, 03.jpg...)
#  4. Edit the lines below. Delete these # notes if you like -- any line that
#     starts with # is ignored, so you can leave them.
#     (Cualquier linea que empieza con # se ignora.)
#  5. The lines with a colon are the settings. Everything from the first line
#     that is not one of them is your description, so a sentence with a colon
#     in it stays in the writing.
#     (Todo lo que no es uno de esos ajustes es ya la descripcion.)
#
#  Folders whose name starts with _ are never published, so this one is safe
#  to keep. (Las carpetas que empiezan con _ nunca se publican.)
# ============================================================================


# The name people see. This one is required. (Obligatorio.)
name: Name of the piece

# The name in Spanish. Leave it out and the English name is used for both.
# (Si lo dejas vacio se usa el nombre en ingles en los dos idiomas.)
name es: Nombre de la pieza

# The sizes you have, separated by commas. (Las tallas, separadas por comas.)
#   Write XS, S, M, L or XL and the site shows the whole row of sizes with the
#   ones you did NOT list crossed out.
#   Write anything else, like  Unique size, and only that is shown.
#   Leave it empty if sizes do not apply. (Dejalo vacio si no aplica.)
sizes: XS, S, M, L

# yes or no. "yes" replaces the sizes with a grey Sold out block.
# (si o no. "si" reemplaza las tallas por un bloque gris de Agotado.)
sold out: no

# Optional. The collection folder this piece belongs to, so the page can link
# to it. It has to match a folder name inside collections/ exactly.
# (Opcional. Tiene que coincidir con una carpeta dentro de collections/.)
collection: querido-diario

# When you added it. The newest pieces show first in the shop.
# Write it as year-month-day. (Escribela como ano-mes-dia.)
date: 2026-09-13


# Everything under the next line is the description in English.
# (Todo lo que va debajo de la siguiente linea es la descripcion en ingles.)
--- ENGLISH ---
Write the description here. Leave a blank line between paragraphs.

A second paragraph looks like this.

--- ESPANOL ---
Escribe aqui la descripcion en espanol. Deja una linea en blanco entre parrafos.

Si no escribes nada en espanol, la pagina usa el texto en ingles.
