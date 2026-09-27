APP := fpga_console
PYTHON := .venv/bin/python
PYINSTALLER := .venv/bin/pyinstaller
SOURCE := source/fpga_console.py
DIST := dist/$(APP)
INSTALL_DIR := /usr/local/bin

.PHONY: build install run clean

build:
	$(PYINSTALLER) --onefile --windowed $(SOURCE)

install: build
	sudo cp $(DIST) $(INSTALL_DIR)/$(APP)

run:
	$(PYTHON) $(SOURCE)

clean:
	rm -rf build dist *.spec
