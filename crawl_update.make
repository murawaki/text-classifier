
PYTHON := nice -19 python3
DATA_DIR := /mnt/hinoki/share/covid19
INPUT_DIR := /mnt/hinoki/share/covid19/run/new-xml-files
OUTPUT_DIR := /mnt/hinoki/share/covid19/topics_bert
BLACKLIST := $(DATA_DIR)/url_black_list.txt
SOURCEINFO := $(DATA_DIR)/source_info.tsv
OUTPUT := $(OUTPUT_DIR)/output.jsonl

CLASSES_FILE = classifiers/classes.txt  # list of classes
BERT_DIR := data/bert
BERT_MODEL := $(BERT_DIR)/Japanese_L-12_H-768_A-12_E-30_BPE_transformers
BERTSIMPLE_MODEL = $(BERT_DIR)/classifier.pth

DAILY_INPUTS = $(wildcard $(INPUT_DIR)/new-xml-files-202*.txt)
BASE_NAMES = $(subst new-xml-files-,,$(basename $(notdir $(DAILY_INPUTS))))

GPUID := -1

# $(1): BASE_NAME
define each_task
$(OUTPUT_DIR)/$(1).target.txt : $(INPUT_DIR)/new-xml-files-$(1).txt
	cat $$< | perl -nle '$$$$d="$(DATA_DIR)"; s/^\Q$$$$d\E/./;print;' > $$@ 2>> $(OUTPUT_DIR)/$(1).log

$(OUTPUT_DIR)/$(1).metadata.jsonl : $(SOURCEINFO) $(OUTPUT_DIR)/$(1).target.txt
	$(PYTHON) -mpreprocess.metadata -d $(DATA_DIR) -s $(SOURCEINFO) $(OUTPUT_DIR)/$(1).target.txt $(OUTPUT_DIR)/$(1).metadata.jsonl.tmp 2>> $(OUTPUT_DIR)/$(1).log && \
	$(PYTHON) preprocess/extracttext.py -d $(DATA_DIR) $(OUTPUT_DIR)/$(1).metadata.jsonl.tmp $(OUTPUT_DIR)/$(1).metadata.jsonl 2>> $(OUTPUT_DIR)/$(1).log

$(OUTPUT_DIR)/$(1).metadata2.jsonl: $(OUTPUT_DIR)/$(1).metadata.jsonl classifiers/keywords.txt
	$(PYTHON) -mcovid-19-annotation-cleanup.classifier -d $(DATA_DIR) $$< classifiers/keywords.txt $$@ 2>> $(OUTPUT_DIR)/$(1).log

METAS += $(OUTPUT_DIR)/$(1).metadata2.jsonl

$(OUTPUT_DIR)/$(1).bertclass.jsonl: $(OUTPUT_DIR)/$(1).metadata2.jsonl
	$(PYTHON) classifiers/bertsimple.py test --gpu=$(GPUID) --batch 256 --bert-model $(BERT_MODEL) --text-file $(OUTPUT_DIR)/$(1).metadata2.jsonl --model-path $(BERTSIMPLE_MODEL) --output-file $(OUTPUT_DIR)/$(1).bertclass.jsonl --classes-file $(CLASSES_FILE) 2>> $(OUTPUT_DIR)/$(1).log

$(OUTPUT_DIR)/$(1).output.jsonl : $(OUTPUT_DIR)/$(1).metadata2.jsonl $(OUTPUT_DIR)/$(1).bertclass.jsonl
	$(PYTHON) merge-classification.py $(OUTPUT_DIR)/$(1).metadata2.jsonl $(OUTPUT_DIR)/$(1).bertclass.jsonl > $(OUTPUT_DIR)/$(1).output.jsonl

OUTPUTS += $(OUTPUT_DIR)/$(1).output.jsonl
endef

$(foreach base_name,$(BASE_NAMES), \
  $(eval $(call each_task,$(base_name))))

$(OUTPUT) : $(OUTPUTS) $(BLACKLIST)
	$(PYTHON) merge.py -k -b $(BLACKLIST) -o $(OUTPUT) $(OUTPUTS)

metas : $(METAS)

all : $(OUTPUT)

clean:
	rm -f $(OUTPUT_DIR)/*.log
	rm -f $(OUTPUT_DIR)/*.target.txt
	rm -f $(OUTPUT_DIR)/*.*.jsonl
	rm -f $(OUTPUT)

