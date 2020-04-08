
PYTHON := nice -19 python3
DATA_DIR := /mnt/hinoki/share/covid19
INPUT_DIR := /mnt/hinoki/share/covid19/run
OUTPUT_DIR := /mnt/hinoki/murawaki/covid19
OUTPUT := $(OUTPUT_DIR)/output.jsonl

DAILY_INPUTS = $(wildcard $(INPUT_DIR)/new-xml-files-*.txt)
BASE_NAMES = $(subst new-xml-files-,,$(basename $(notdir $(DAILY_INPUTS))))

# $(1): BASE_NAME
define each_task
$(OUTPUT_DIR)/$(1).target.txt : $(INPUT_DIR)/new-xml-files-$(1).txt
	cat $$< | perl -nle '$$$$d="$(DATA_DIR)"; s/^\Q$$$$d\E/./;print;' > $$@ 2>> $(OUTPUT_DIR)/$(1).log

$(OUTPUT_DIR)/$(1).metadata.jsonl : $(OUTPUT_DIR)/$(1).target.txt
	$(PYTHON) metadata.py -d $(DATA_DIR) $$< $$@ 2>> $(OUTPUT_DIR)/$(1).log

$(OUTPUT_DIR)/$(1).output.jsonl: $(OUTPUT_DIR)/$(1).metadata.jsonl keywords.txt
	$(PYTHON) classifier.py -d $(DATA_DIR) $$< keywords.txt $$@ 2>> $(OUTPUT_DIR)/$(1).log

OUTPUTS += $(OUTPUT_DIR)/$(1).output.jsonl
endef

$(foreach base_name,$(BASE_NAMES), \
  $(eval $(call each_task,$(base_name))))

$(OUTPUT) : $(OUTPUTS)
	echo $(OUTPUTS) | tr ' ' '\n' | sort | xargs cat > $@

all : $(OUTPUT)

clean:
	rm -f $(OUTPUT_DIR)/*.log
	rm -f $(OUTPUT_DIR)/*.target.txt
	rm -f $(OUTPUT_DIR)/*.metadata.jsonl
	rm -f $(OUTPUT_DIR)/*.output.jsonl
	rm -f $(OUTPUT)

