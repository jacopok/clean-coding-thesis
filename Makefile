all: run_pandoc combine_pdfs

run_pandoc:
	pandoc -f markdown-implicit_figures --citeproc --pdf-engine=xelatex --listings galileian_thesis.md --toc --template=default.latex -o galileian_thesis_pandoc_only.pdf

combine_pdfs:
	gs -dBATCH -dNOPAUSE -q -sDEVICE=pdfwrite -dAutoRotatePages=/None -sOutputFile=galileian_thesis.pdf  frontespizio/frontespizio.pdf galileian_thesis_pandoc_only.pdf
