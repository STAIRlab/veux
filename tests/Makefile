RENDER = python -m veux

all:
	 $(RENDER) --conf config.yaml --default-section hayward.txt c.json c.yaml -o out/c.html
	 $(RENDER) --conf config.yaml --default-section hayward.txt d.json c.yaml -o out/d.html
	 $(RENDER) --conf config.yaml --default-section hayward.txt e.json c.yaml -o out/e.html
	 $(RENDER) --conf config.yaml --default-section hayward.txt f.json c.yaml -o out/f.html
	 $(RENDER) --conf config.yaml --default-section hayward.txt f.json c.yaml -o out/f.html
	 $(RENDER) --conf config.yaml --vert 3 --default-section hayward.txt hayward.json -o out/h.html
	 # $(RENDER)  c.json -o c.html

