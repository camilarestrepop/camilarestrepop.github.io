# 5 Tintas — your website

Your website is live here:

### https://5tintas.com

The older address, https://camilarestrepop.github.io, brings people to the same place.

This page tells you how to change it. You do everything on github.com, in the browser. You never
need a program on your computer, and you cannot break anything: every change is saved as a new
version, so anything can be put back.

Español: [README.es.md](README.es.md)

<!-- Jack: screenshots of each GitHub screen could go here, one under each numbered step. -->

---

## The one rule

Every change you make starts the website building itself again. It takes about a minute. Then you
refresh the page in your browser and your change is there.

If you still see the old page, your browser is showing you the copy it saved. Hold Shift and click
refresh, or wait a few minutes and try again.

If something in a file confuses the website, it does **not** publish a broken page. It tells you
what is wrong instead, in plain words, naming the file. See [Did it work?](#did-it-work) below.

---

## Add a piece to the shop — the easy way

1. Go to https://github.com/camilarestrepop/camilarestrepop.github.io
2. Click the **Issues** tab at the top.
3. Click the green **New issue** button.
4. Next to **Add a product**, click **Get started**.
5. Fill in the form:
   - **Name of the piece** — what people see. This one is needed.
   - **Sizes** — separated by commas, like `XS, S, M`. Leave it empty if sizes do not apply.
   - **Sold out** — `No` or `Yes`.
   - **Collection** — pick one, or leave it on `(none)`.
   - **Description in English** and **Descripción en español** — leave a blank line between
     paragraphs. If you leave the Spanish one empty, the English text is used in both languages.
   - **Photos** — drag your photos into the box and wait for each one to finish uploading. The
     first one you add is the big photo people see first. This one is needed.
6. Click **Create**.

That is all. Within a couple of minutes a reply appears on what you just created, with a link
straight to the new page, and the piece is on the shop.

If any photo did not come through, the reply tells you and gives you a link to drag those photos in
by hand. Your words and the page are already saved, so nothing is lost.

Leave the title alone when you fill the form in: it already starts with `Add product:`, and that is
partly how the website recognises what you are asking for. If no reply appears at all after five
minutes, tell Jack.

---

## Add a piece to the shop — the other way

Use this if you would rather not use the form, or if you want to look at the files.

**First the folder and its words:**

1. Go to https://github.com/camilarestrepop/camilarestrepop.github.io
2. Click **website**, then **content**, then **products**.
3. Click **Add file** (top right) and choose **Create new file**.
4. In the box for the name, type the name of the folder, then a slash, then `info.md`. For example:
   `vestido-eva/info.md`
   Use lowercase letters, numbers and dashes instead of spaces. GitHub makes the folder for you as
   soon as you type the slash.
5. In the big box underneath, type the details of the piece. There is a copy-and-paste version in
   [The info.md cheat sheet](#the-infomd-cheat-sheet) below.
6. Click the green **Commit changes...** button, then **Commit changes** in the little window.

**Then the photos:**

7. You are now looking at your new folder. Click **Add file** and choose **Upload files**.
8. Name the photos on your computer `01.jpg`, `02.jpg`, `03.jpg`… The one called `01` is the big
   photo people see first.
9. Drag them into the page and click **Commit changes**.

---

## The info.md cheat sheet

Every piece has one `info.md` file. This is all it is:

```
name: Vestido Eva
sizes: XS, S, M, L
sold out: no
collection: eva-mitocondrial
date: 2026-09-13

--- ENGLISH ---
Hand-dyed denim dress, made to order.

A second paragraph looks like this.

--- ESPANOL ---
Vestido de denim teñido a mano, hecho por encargo.
```

What each line means:

| Line | What it does |
| --- | --- |
| `name:` | What people see. The only line you really need. |
| `name es:` | The name in Spanish, if it is different. Leave it out and the English name is used. |
| `sizes:` | Separated by commas. Write `XS, S, M, L` or `XL` and the site shows the whole row with the ones you did not list crossed out. Write something else, like `Unique size`, and only that is shown. Leave it empty for no sizes at all. |
| `sold out:` | `no` or `yes`. `yes` replaces the sizes with a grey **Sold out** block. |
| `collection:` | Which collection it belongs to. It has to match a folder name inside `website/content/collections/` exactly. Leave the line out if it belongs to none. |
| `date:` | Written as year-month-day. The newest pieces show first in the shop. |

The lines with a colon at the top are the settings, and they can be in any order. Everything from
the first line that is not one of them is your description — so a sentence with a colon in it, like
`Inspiracion: el mar`, stays in the writing exactly as you typed it.

Anything under `--- ENGLISH ---` is the description in English, and anything under
`--- ESPANOL ---` is the description in Spanish. Leave a blank line between paragraphs.

A line starting with `#` is a note to yourself. It never shows up on the website.

There is a ready-made example to copy in `website/content/_TEMPLATE-product/info.md`. A folder whose
name starts with `_` is never published, which is why that one is not in the shop.

---

## Change a description or a name

1. Click your way to the file: **website** → **content** → **products** → the folder → `info.md`
2. Click the pencil icon at the top right of the file.
3. Change the words.
4. Click **Commit changes...**, then **Commit changes**.

The same works for any other file of words on the site.

---

## Change the order of the photos

The photo called `01` is always the first one. The rest follow in number order.

To reorder them, rename them on your computer (`01.jpg`, `02.jpg`, `03.jpg`…) and upload them all
again into the same folder: **Add file** → **Upload files** → drag → **Commit changes**. A photo
with the same name as one already there simply replaces it.

To remove a photo: open it in the folder, click the **...** button at its top right, choose
**Delete file**, then **Commit changes**.

---

## Take a piece off the shop

Three ways, from gentlest to most final:

1. **Mark it sold out.** Edit its `info.md` and write `sold out: yes`. The page stays, with a grey
   **Sold out** block instead of the sizes.
2. **Remove it.** Open its folder, click the **...** button at the top right of the file list and
   choose **Delete directory**, then **Commit changes**. It is gone from the site, but it stays in
   the history, so it can always come back.
3. **Hide it without removing it.** A folder whose name starts with `_` is never published. Open the
   piece's `info.md`, click the pencil, and in the box with the file name at the top put a `_` at the
   front of the folder name, so `vestido-eva/info.md` becomes `_vestido-eva/info.md`. Then **Commit
   changes**. The piece disappears from the shop, and putting the `_` back brings it straight back.

   The photos can stay where they are. The website mentions the folder they are in among its notes,
   the way it does for any piece still being worked on, and everything keeps working. Move them into
   the `_` folder too if you want it tidy.

---

## Change your Instagram, WhatsApp or email

They live in one file, and the whole site reads it.

1. Click **website** → **content** → `site.md`
2. Click the pencil icon.
3. Change the lines you want:
   ```
   instagram: https://instagram.com/5.tintas
   whatsapp: +1 347 362 2979
   email: camilarestrepo.fashionlab@gmail.com
   ```
4. Click **Commit changes...**, then **Commit changes**.

The same file holds your tagline, the big photo at the top of the home page, and how many of the
newest pieces the home page shows.

---

## Your web address

People reach your website at **5tintas.com**. That address is written in the same `site.md` file, on
this line:

```
domain: 5tintas.com
```

Leave that line alone. Adding a piece, changing a photo or editing your words never touches it. It
only matters if the web address itself ever changes, and then it has to change in two places: this
line, and **Settings** → **Pages** on github.com. Ask Jack to do both together.

It has to stay there. Every change you make publishes the website again, and it is this line that
tells each publish to keep your address. If the line were deleted, nothing would break: the website
would simply go back to answering at https://camilarestrepop.github.io instead.

`www.5tintas.com` and `5tintas.com` are not the same address to GitHub, so whichever one is on that
line is the one to put in **Settings** → **Pages** as well.

---

## Collections and runway shows

They work exactly like products, in their own folders:

- Collections: **website** → **content** → **collections** → the folder → `info.md`
- Runway shows: **website** → **content** → **runways** → the folder → `info.md`

Photos go in the same folder as the `info.md`, named `01.jpg`, `02.jpg`, `03.jpg`…

**Rayito de Sol**, **Añoranza** and the three runway shows say *coming soon* at the moment, because
they have no photos yet. Upload photos into their folders and the *coming soon* disappears by
itself — you do not have to change anything else.

The `order:` line decides where a collection sits in the lists. `1` comes first.

If you make a **new** collection, one more thing needs doing: the **Collection** dropdown on the
"Add a product" form is a fixed list, so a new collection is not in it until it is added. The list is
in `.github/ISSUE_TEMPLATE/add-product.yml`, and Jack can add a line to it in a minute. Until then,
write the `collection:` line in the piece's `info.md` by hand instead.

---

## Add a video to a runway show or a collection

The video goes underneath the photos, with a play button. There are two ways, and you can use
whichever suits the video you have. A runway show with neither says **Video coming soon** until you
add one.

### Way 1: put the video file in the folder

1. Name the file `video.mp4` on your computer. `video.mov` and `video.webm` work too.
2. Go to the folder of that runway show or collection: **website** → **content** → **runways** →
   the folder.
3. Click **Add file** and choose **Upload files**.
4. Drag the video in and click **Commit changes**.

That is all. The player appears under the photos by itself.

**The one thing to watch:** github.com will not accept a single file bigger than **25 MB** through
the browser. A video straight off a phone is usually much bigger than that, so it has to be made
smaller first, or you use Way 2 instead. If you try anyway, GitHub says the file is too large and
nothing is uploaded, so nothing breaks.

To make it smaller, on an iPhone the simplest way is to trim it and send it to yourself at a lower
quality, or ask Jack to compress it once for you. Keep in mind that a heavy video also makes the page
slow to open on a phone, so smaller is genuinely better.

### Way 2: use a link to the video

Use this for anything long or heavy. Put the video on YouTube, Vimeo or Instagram first, then:

1. Copy its link from the address bar of the browser.
2. Open that folder's `info.md` and click the pencil icon.
3. Add one line, like this:
   ```
   video: https://www.youtube.com/watch?v=XXXXXXXXXXX
   ```
4. Click **Commit changes...**, then **Commit changes**.

There is no size limit this way, and the page stays quick to open, because the video is played from
YouTube, Vimeo or Instagram rather than from your website.

If a folder has both a video file and a `video:` line, the file in the folder is the one shown.

---

## Did it work?

Every change publishes the site again. To watch it happen:

1. Go to https://github.com/camilarestrepop/camilarestrepop.github.io
2. Click the **Actions** tab at the top.
3. The top line in the list is your change.
   - An **orange dot** means it is still working. Wait a minute.
   - A **green tick** means it is live. Refresh the website.
   - A **red cross** means something in the files confused it. Nothing was published, and the
     website that people see is untouched.
4. If it is a red cross, click that top line, then click the job name, and read the last lines of
   the message. It names the file and says what to do about it, in plain words. Fix that file and
   the site publishes itself again.

---

## If you get stuck

Write to Jack. Send him:

- what you were trying to do,
- the link to the page or the file you were on.

Nothing you do here can break the website permanently. Every version is kept.
