Why Image based Epub files ? 

ISSUE 1: traditional Epub files work by converting text, which messes with LaTeX

 Normal bad way
  PDF text → try to convert to EPUB text + equations → reader destroys the math.

 Image method:
  Takes the visual appearance of each PDF page.
  Saves it as an image.
  Makes the EPUB contain only those images + tiny HTML files that say "display this image".
  The EPUB reader no longer has to understand math or layout — it just shows pictures.
  The temporary files will be automatically deleted and end product will be saved as a Epub file in the same directory as the original pdf

ISSUE 2: Old ipads and mid tier phones do not process pdf smoothly, while image based epubs are much more smoother
 
 Normal EPUBs try to use real text + math (LaTeX/MathML/SVG). Many readers (especially older iPads, Kindle, etc.) are terrible at rendering 
 complex equations, tables, fonts, or PDFs that were never meant for reflowable text. So equations break, text overlaps, fonts go missing, etc.

 This method avoids all of that because:
 There is no text in the EPUB at all (except the minimal HTML wrapper).
 Everything is a pre-rendered image. The equations, layout, fonts, diagrams — everything is "baked in" as pixels.
 EPUB readers are very good at showing images. They just decode the JPG and display it. No font rendering, no equation parsing, no layout engine struggling.
 The HTML is extremely simple so almost every reader can display it without issues.
 Pages turn fast because it's just flipping between images.

## Features
- Adjustable DPI to maintain file size and quality
- Clean and easy-to-use GUI
- Automatically cleans temporary files
- EPUB saved in the same folder as your original PDF
- Works offline

DISCLAIMER:
I hold credits only about the idea, the rest of the code was written by a local offline coding llm 
