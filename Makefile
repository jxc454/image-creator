
.PHONY: install
install:
	PIPENV_VERBOSITY=-1 pipenv install

.PHONY: test
test:
	pytest -s test/*

.PHONY: dist
dist:
	docker run -v $$(pwd)/dist:/dist -t $$(docker build -q --file Dockerfile.dist .) python3 setup.py sdist
