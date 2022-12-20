# Compile C files and dump their .data section to binary

CROSS := mips-linux-gnu-

CC := $(CROSS)gcc
OBJCOPY := $(CROSS)objcopy
NM := $(CROSS)nm

C_FILES := f3dex2.c
BIN_FILES := $(C_FILES:.c=.bin)

all: $(BIN_FILES)
	./test.py

.PHONY: all

%.bin: %.o
	$(OBJCOPY) -O binary -j .data $< $@
	$(NM) -f sysv $< > $(@:.bin=.txt)

%.o: %.c
	$(CC) -c -o $@ $^
