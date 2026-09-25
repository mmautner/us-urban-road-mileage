.PHONY: all data charts clean

all: data charts

data/raw/hm71_2023.pdf:
	python scripts/fetch_hm71.py

data: data/raw/hm71_2023.pdf
	python scripts/parse_hm71.py data/raw/hm71_2023.pdf
	python scripts/build_metrics.py

charts:
	python scripts/render_charts.py

clean:
	rm -f data/raw/hm71_2023.pdf charts/_*.png charts/*.html
