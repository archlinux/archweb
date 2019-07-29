PYTHON>=python
PYTEST?=pytest
PYTEST_OPTIONS+=
PYTEST_INPUT?=.
PYTEST_COVERAGE_OPTIONS+=--cov-report=term-missing --cov-report=html:htmlcov --cov=.
PYTEST_PDB?=0
PYTEST_PDB_OPTIONS?=--pdb --pdbcls=IPython.terminal.debugger:TerminalPdb


ifeq (${PYTEST_PDB},1)
PYTEST_OPTIONS+= ${PYTEST_PDB_OPTIONS}
else
test-pdb: PYTEST_OPTIONS+= ${PYTEST_PDB_OPTIONS}
endif
test-pdb: test


.PHONY: test lint

lint:
	pylint devel main mirrors news packages releng templates todolists visualize *.py

collecstatic:
	python manage.py collecstatic --noinput

test: test-py

test-py coverage:
	${PYTEST} ${PYTEST_INPUT} ${PYTEST_OPTIONS} ${PYTEST_COVERAGE_OPTIONS}

open-coverage: coverage
	${BROWSER} htmlcov/index.html
