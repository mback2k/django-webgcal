all: Pipfile.lock requirements.txt dev-requirements.txt

Pipfile.lock: Pipfile
	pipenv lock --pre

requirements.txt: Pipfile Pipfile.lock
	pipenv lock --pre --requirements > requirements.txt

dev-requirements.txt: Pipfile Pipfile.lock
	pipenv lock --pre --dev --requirements > dev-requirements.txt
