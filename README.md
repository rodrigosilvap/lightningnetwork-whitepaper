# Lightning Network Paper

This is the Bitcoin Lightning Network paper.

Paper PDF: [http://lightning.network/lightning-network-paper.pdf](http://lightning.network/lightning-network-paper.pdf)

## Translations

| Language | Source | Status |
| --- | --- | --- |
| English (original) | [paper.tex](paper.tex) | Canonical |
| Português (Brasil) | [paper.pt-BR.tex](paper.pt-BR.tex) | Draft v0.5.9.2 |

To compile a translation, run the same recipe as the English version against
the translated file (e.g. `pdflatex paper.pt-BR.tex` etc.). Figures in
`figures/` are language-neutral and shared across translations.

#Compiling/Editing

Paper is in LaTeX format. Diagrams are in dia, but may remake the diagrams in
inkscape for cleanliness.

## Updating bibliography
If you're not familiar with latex, updating bibliography requires running:
```
pdflatex new.tex
bibtex new
pdflatex new.tex
pdflatex new.tex
```

## Generating figures
requires dia

```
cd figures
python dia2pdf.py
```

## Formatting

By default, there is a text width of 80 characters unless there is an explicit
need to go longer.

If you want to do formatting of paragraphs, the vim settings are:

```
:set tw=80
```

If you want to reflow text, it's
```
<ESC>gqj
```

If you want to reflow an entire paragraph, it's
```
<ESC>gq}
```

There are a couple places where reflowing will break (primarily in figures
where it's sensitive to linebreaks).
