SHELL=/usr/bin/bash


# <pattern> : <patterns>... 
# 	command
# 	command
# 	...
# 	command


%.tex: %.md Makefile
	pandoc $< \
		-f markdown+markdown_in_html_blocks \
		-t markdown+markdown_in_html_blocks \
		-V geometry:margin=0.75in \
		--filter pandoc-eqnos \
		--metadata-file=<(sed '/^\.\.\./q' $<) \
		-f markdown-raw_tex+tex_math_single_backslash+markdown_in_html_blocks \
		-t latex \
 		--template ./style/truesdell.tex  \
		-o $@

%.pdf: %.tex Makefile
	mkdir -p out
	lualatex -output-directory=out $< -o $@
	# rm *.aux *.log


%.html: %.md Makefile
	pandoc $< \
		--filter pandoc-eqnos \
		--metadata-file=<(sed '/^\.\.\./q' %<.md) \
		-f markdown+markdown_in_html_blocks \
		-t markdown+markdown_in_html_blocks \
		| pandoc --toc -s \
		-f markdown-raw_tex+tex_math_single_backslash+markdown_in_html_blocks \
		--mathjax \
		-t html \
		-o $@

	#--filter pygmentize 


