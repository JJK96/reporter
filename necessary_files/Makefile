PROJNAME=report

.PHONY: $(PROJNAME).pdf all clean

all: $(PROJNAME).pdf

$(PROJNAME).pdf: $(PROJNAME).tex
	latexmk -pdflatex=lualatex -pdf $<

clean:
	latexmk -c
