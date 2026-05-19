# A very basic Makefile that can build a LaTeX file + bibliography.
# Use as you see fit.
SOURCE=paper

DIA_FILES := $(wildcard figures/*.dia)

all: figures $(SOURCE).tex
	-pdflatex -interaction=nonstopmode $(SOURCE).tex < /dev/null
	-bibtex $(SOURCE).aux < /dev/null
	-pdflatex -interaction=nonstopmode $(SOURCE).tex < /dev/null
	-pdflatex -interaction=nonstopmode $(SOURCE).tex < /dev/null

pt-br: figures-pt-BR paper.pt-BR.tex
	-pdflatex -interaction=nonstopmode paper.pt-BR.tex < /dev/null
	-bibtex paper.pt-BR.aux < /dev/null
	-pdflatex -interaction=nonstopmode paper.pt-BR.tex < /dev/null
	-pdflatex -interaction=nonstopmode paper.pt-BR.tex < /dev/null

# Convert figures/*.dia to figures/*.pdf using a Debian container (Dia is no
# longer packaged for macOS). Sentinel file means we only re-run when sources
# change. Requires Docker.
figures: figures/.built

figures/.built: $(DIA_FILES) figures/dia2pdf.py
	docker run --rm -v "$(CURDIR)/figures":/figures -w /figures --platform linux/amd64 \
		debian:bookworm-slim bash -c 'set -e; \
			apt-get update -qq > /dev/null && \
			apt-get install -y -qq --no-install-recommends \
				dia ghostscript xvfb xauth python3 > /dev/null && \
			xvfb-run -a python3 dia2pdf.py'
	touch $@

# Translated figures for the pt-BR build: substitute strings using
# translations-pt-BR.json, then render to PDF in the same Debian container.
figures-pt-BR: figures-pt-BR/.built

figures-pt-BR/.built: $(DIA_FILES) figures/translations-pt-BR.json figures/translate-pt-BR.py figures/dia2pdf.py
	python3 figures/translate-pt-BR.py figures-pt-BR
	docker run --rm -v "$(CURDIR)/figures":/scripts:ro -v "$(CURDIR)/figures-pt-BR":/work -w /work --platform linux/amd64 \
		debian:bookworm-slim bash -c 'set -e; \
			apt-get update -qq > /dev/null && \
			apt-get install -y -qq --no-install-recommends \
				dia ghostscript xvfb xauth python3 > /dev/null && \
			xvfb-run -a python3 /scripts/dia2pdf.py'
	touch $@

.PHONY: all pt-br figures figures-pt-BR
